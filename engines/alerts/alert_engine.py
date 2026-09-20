"""
engines/alerts/alert_engine.py — GeoShield Alerts Engine orchestrator

Polls each registered hazard engine's OWN cache (agriculture, fire, flood,
drought), compares current per-county severity against the last-seen
severity, and raises a VISIBLE alert only when severity is new-or-worsened
AND is Moderate or above (Low is tracked internally so later escalation is
still detected, but never surfaces as an alert on its own).

Two separate views are maintained:
  - ACTIVE ALERTS (_active_alerts): only (hazard, county) pairs CURRENTLY
    at Moderate+. The moment a county drops back to Low -- including a
    fire hotspot simply no longer appearing in that day's VIIRS feed --
    it is removed from this dict and a "resolved" entry is appended to
    history so the recovery itself is on record.
  - HISTORICAL ALERTS (main_engine.risk_alert_engine.alert_history): a
    permanent, append-only log of every alert ever raised, including
    resolutions. Can be cleared on demand via clear_alert_history()
    without touching the live active state.

Of the alerts that surface, only High/Extreme trigger an actual SMS
dispatch attempt via main_engine.dispatch_alert_notification(). Moderate
alerts are recorded in history/active state but never reach the
notification engine. Resolution ("recovery") entries never notify.

Each raised alert also carries a best-effort human-readable "reason"
string built from whatever raw factor fields the matching RiskEngine
calculator already computed.

NOT YET DONE (intentionally): DRY_RUN defaults True. Watch a few poll
cycles of logged output before ever flipping this — and even then,
notification_engine.send_sms still requires
GEOSHIELD_NOTIFICATIONS_ENABLED=true and real Africa's Talking creds in
.env before anything actually leaves the building.

Also not yet done: _last_seen and _active_alerts are in-memory only. A
server restart clears both, so the first poll cycle after a restart will
re-raise alerts for anything already elevated (same as before this
change) and Active Alerts will rebuild itself from that first cycle.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Tuple

from core.engines.main_engine import main_engine
from engines.risk_alert_engine import RiskAlertEngine

logger = logging.getLogger("geoshield.alerts.orchestrator")

DRY_RUN = True
POLL_INTERVAL_SECONDS = 60

SEVERITY_RANK = {"Low": 0, "Moderate": 1, "High": 2, "Extreme": 3}
HAZARDS = ("agriculture", "fire", "flood", "drought")

# Severities that are ever shown as a visible/active alert.
ALERT_SEVERITIES = {"Moderate", "High", "Extreme"}

# Of the alert severities above, only these attempt SMS dispatch.
NOTIFY_SEVERITIES = {"High", "Extreme"}

# (hazard, county) -> last-seen severity. Tracks EVERYTHING, including Low,
# so a later re-worsening (including a rise out of Low) is always caught.
_last_seen: Dict[Tuple[str, str], str] = {}

# (hazard, county) -> the alert dict currently representing that pair's
# active elevated state. Removed the moment severity drops back to Low
# (or, for fire, the county stops appearing in the hotspot feed at all).
_active_alerts: Dict[Tuple[str, str], dict] = {}

_lock = threading.Lock()


def _get_hazard_records(hazard: str) -> dict[str, dict]:
    """Read current per-county records for one hazard via that engine's
    own .analyse(). Does NOT force a fresh live fetch.

    Fire returns one record per VIIRS hotspot EVENT, not one per county,
    so multiple records can share a county -- we keep the record with the
    worst severity per county. A county with NO hotspots today simply
    will not appear in this dict at all (handled as a recovery by the
    caller, not here).
    """
    engine = main_engine.registered_engines.get(hazard)
    if engine is None:
        logger.warning("orchestrator: hazard '%s' not registered on main_engine", hazard)
        return {}
    try:
        records = engine.analyse()
    except Exception:
        logger.exception("orchestrator: %s.analyse() raised", hazard)
        return {}

    worst: dict[str, dict] = {}
    for r in records:
        county = r.get("county")
        severity = r.get("severity")
        if not county or not severity:
            continue
        current = worst.get(county)
        if (
            current is None
            or SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(current.get("severity"), 0)
        ):
            worst[county] = r
    return worst


def _build_reason(hazard: str, record: dict) -> str:
    """Best-effort human-readable explanation for an alert's severity,
    built from raw factors the matching RiskEngine already computed.
    Never raises -- falls back to a generic line if fields are missing."""
    try:
        if hazard == "fire":
            brightness = record.get("brightness")
            frp = record.get("frp")
            confidence = record.get("confidence")
            parts = []
            if brightness is not None:
                parts.append(f"brightness {brightness:.0f}K")
            if frp is not None:
                parts.append(f"FRP {frp:.1f}MW")
            if confidence is not None:
                parts.append(f"confidence '{confidence}'")
            if parts:
                return "Active VIIRS hotspot (" + ", ".join(parts) + ")."
            return "Active VIIRS fire hotspot detected."

        if hazard in ("drought", "agriculture"):
            rainfall = record.get("rainfall_mm")
            temperature = record.get("temperature_c")
            humidity = record.get("humidity_pct")
            ndvi = record.get("ndvi")
            reasons = []
            if rainfall is not None and rainfall < 5:
                reasons.append(f"very low rainfall ({rainfall:.1f}mm)")
            if temperature is not None and temperature >= 30:
                reasons.append(f"high temperature ({temperature:.1f}\u00b0C)")
            if humidity is not None and humidity < 30:
                reasons.append(f"low humidity ({humidity:.0f}%)")
            if ndvi is not None and ndvi < 0.3:
                reasons.append(f"degraded vegetation (NDVI {ndvi:.2f})")
            label = "Drought conditions" if hazard == "drought" else "Agricultural stress"
            if reasons:
                return label + " driven by " + ", ".join(reasons) + "."
            return label + " based on current weather/vegetation conditions."

        if hazard == "flood":
            rainfall = record.get("rainfall_mm")
            upland_skm = record.get("upland_skm")
            discharge = record.get("reference_discharge_cms")
            reasons = []
            if rainfall is not None and rainfall >= 800:
                reasons.append(f"heavy rainfall ({rainfall:.0f}mm)")
            if upland_skm is not None and upland_skm >= 30000:
                reasons.append(f"large upstream catchment ({upland_skm:.0f} sq km)")
            if discharge is not None and discharge > 0:
                reasons.append(f"elevated reference river discharge ({discharge:.1f} m\u00b3/s)")
            if reasons:
                return "Flood risk driven by " + ", ".join(reasons) + "."
            return "Elevated flood risk based on current rainfall and catchment conditions."

    except Exception:
        logger.exception("orchestrator: failed to build reason for %s", hazard)

    return f"{hazard.title()} severity elevated to current level."


def _raise_alert(hazard: str, county: str, previous: str | None, severity: str, record: dict) -> dict:
    message = RiskAlertEngine.build_message(hazard, severity)
    action = RiskAlertEngine.build_action(severity)
    reason = _build_reason(hazard, record)

    alert = {
        "alert_id": f"GS-{hazard.upper()}-ORCH-{int(time.time() * 1000)}",
        "hazard": hazard,
        "county": county,
        "severity": severity,
        "previous_severity": previous,
        "reason": reason,
        "message": message,
        "recommended_action": action,
        "source": "AlertOrchestrator",
        "timestamp": time.time(),
        "resolved": False,
    }

    main_engine.risk_alert_engine.alert_history.append(alert)
    main_engine.event_bus.publish(alert)

    if severity in NOTIFY_SEVERITIES:
        sms_result = main_engine.dispatch_alert_notification(alert, dry_run=DRY_RUN)
    else:
        sms_result = {"status": "skipped_below_notify_threshold", "sent": False}

    logger.info(
        "orchestrator alert %s (%s -> %s, %s/%s) | sms_status=%s",
        alert["alert_id"], previous, severity, hazard, county,
        sms_result.get("status"),
    )
    print(
        f"[Alert Orchestrator] {alert['alert_id']} {hazard}/{county}: "
        f"{previous} -> {severity} | sms_status={sms_result.get('status')}"
    )
    return alert


def _log_recovery(hazard: str, county: str, previous: str | None, new_severity: str) -> None:
    """Log that a previously-active (hazard, county) pair has dropped
    back below Moderate. Recorded in history but never notifies and is
    never added to _active_alerts."""
    alert = {
        "alert_id": f"GS-{hazard.upper()}-RESOLVED-{int(time.time() * 1000)}",
        "hazard": hazard,
        "county": county,
        "severity": new_severity,
        "previous_severity": previous,
        "reason": "Conditions have returned to normal.",
        "message": f"{hazard.title()} risk in {county} has returned to {new_severity}.",
        "recommended_action": "ROUTINE_MONITORING",
        "source": "AlertOrchestrator",
        "timestamp": time.time(),
        "resolved": True,
    }
    main_engine.risk_alert_engine.alert_history.append(alert)
    main_engine.event_bus.publish(alert)
    logger.info("orchestrator recovery %s/%s: %s -> %s", hazard, county, previous, new_severity)
    print(f"[Alert Orchestrator] RECOVERED {hazard}/{county}: {previous} -> {new_severity}")


def run_poll_cycle() -> int:
    """One pass over every registered hazard's cached counties. Returns
    the number of NEW/WORSENED visible alerts raised this cycle
    (recoveries are logged but not counted in this return value)."""
    raised = 0
    with _lock:
        for hazard in HAZARDS:
            records = _get_hazard_records(hazard)
            seen_this_hazard = set(records.keys())

            for county, record in records.items():
                severity = record.get("severity")
                if not severity:
                    continue
                key = (hazard, county)
                previous = _last_seen.get(key)
                worsened = (
                    previous is None
                    or SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(previous, 0)
                )
                _last_seen[key] = severity

                if severity in ALERT_SEVERITIES:
                    if worsened:
                        alert = _raise_alert(hazard, county, previous, severity, record)
                        _active_alerts[key] = alert
                        raised += 1
                    elif key not in _active_alerts:
                        # Defensive: severity is elevated but somehow not
                        # tracked as active yet (e.g. state drift) --
                        # backfill without re-raising a duplicate alert.
                        _active_alerts[key] = {
                            "alert_id": f"GS-{hazard.upper()}-ACTIVE-{int(time.time() * 1000)}",
                            "hazard": hazard, "county": county, "severity": severity,
                            "previous_severity": previous,
                            "reason": _build_reason(hazard, record),
                            "message": RiskAlertEngine.build_message(hazard, severity),
                            "recommended_action": RiskAlertEngine.build_action(severity),
                            "source": "AlertOrchestrator", "timestamp": time.time(),
                            "resolved": False,
                        }
                else:
                    if key in _active_alerts:
                        _log_recovery(hazard, county, previous, severity)
                        del _active_alerts[key]

            # A county that used to report for this hazard but no longer
            # appears at all this cycle (e.g. a fire hotspot cleared) is
            # also a recovery -- "no current record" means nothing
            # elevated is being reported for it anymore.
            missing_now = [
                key for key in list(_active_alerts.keys())
                if key[0] == hazard and key[1] not in seen_this_hazard
            ]
            for key in missing_now:
                h, c = key
                previous = _last_seen.get(key)
                _log_recovery(h, c, previous, "Low")
                _last_seen[key] = "Low"
                del _active_alerts[key]
    return raised


def get_active_alerts() -> list[dict]:
    """Current live alert state -- only Moderate+ (hazard, county) pairs
    right now. Goes back down as conditions improve."""
    with _lock:
        return sorted(
            _active_alerts.values(),
            key=lambda a: SEVERITY_RANK.get(a.get("severity"), 0),
            reverse=True,
        )


def get_active_alert_count() -> int:
    """Count of currently-active (Moderate+) (hazard, county) pairs.
    Used by the dashboard's 'Active Alerts' tile."""
    with _lock:
        return len(_active_alerts)


def clear_alert_history() -> int:
    """Empty the permanent historical alert log. Active alert state is
    completely untouched -- this only clears the history for space.
    Returns the number of entries that were cleared."""
    with _lock:
        history = main_engine.risk_alert_engine.alert_history
        count = len(history)
        history.clear()
        return count


def _loop(stop_event: threading.Event) -> None:
    logger.info(
        "Alert orchestrator starting (dry_run=%s, poll_interval=%ss)",
        DRY_RUN, POLL_INTERVAL_SECONDS,
    )
    print(f"[Alert Orchestrator] starting (dry_run={DRY_RUN}, poll_interval={POLL_INTERVAL_SECONDS}s)")
    while not stop_event.is_set():
        try:
            raised = run_poll_cycle()
            if raised:
                logger.info("poll cycle raised %d alert(s)", raised)
                print(f"[Alert Orchestrator] poll cycle raised {raised} alert(s)")
        except Exception:
            logger.exception("alert orchestrator poll cycle failed")
        stop_event.wait(POLL_INTERVAL_SECONDS)
    logger.info("Alert orchestrator stopped")
    print("[Alert Orchestrator] stopped")


def start_alert_orchestrator() -> threading.Event:
    stop_event = threading.Event()
    threading.Thread(
        target=_loop,
        args=(stop_event,),
        daemon=True,
        name="geoshield-alert-orchestrator",
    ).start()
    return stop_event
