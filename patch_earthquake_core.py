from pathlib import Path

def patch(path_str, anchor, addition, label):
    path = Path(path_str)
    src = path.read_text(encoding="utf-8-sig")
    original = src

    if anchor not in src:
        raise SystemExit(f"ERROR: anchor not found for {label} in {path_str} -- printing file:\n" + src)

    src = src.replace(anchor, addition, 1)

    if src == original:
        print(f"{label}: no changes were necessary (already patched?).")
    else:
        path.write_text(src, encoding="utf-8", newline="\n")
        print(f"{label}: patched successfully.")


# ------------------------------------------------------------
# 1. core/config.py -- add worldpop_api_key setting
# ------------------------------------------------------------

config_anchor = '''    gpm_pps_email: str = os.getenv(
        "GPM_PPS_EMAIL",
        "",
    )'''

config_addition = config_anchor + '''

    # ---------------------------------------------------------
    # WorldPop (population exposure)
    # ---------------------------------------------------------

    worldpop_api_key: str = os.getenv(
        "WORLDPOP_API_KEY",
        "",
    )'''

patch("core/config.py", config_anchor, config_addition, "core/config.py (worldpop_api_key)")


# ------------------------------------------------------------
# 2. core/engines/main_engine.py -- imports
# ------------------------------------------------------------

me_import_anchor = "from core.connectors.era5_connector import build_era5_connector"
me_import_addition = (
    me_import_anchor
    + "\nfrom core.connectors.earthquake_connector import build_earthquake_connector"
    + "\nfrom core.connectors.population_connector import build_population_connector"
)
patch("core/engines/main_engine.py", me_import_anchor, me_import_addition, "main_engine.py (imports)")


# ------------------------------------------------------------
# 3. core/engines/main_engine.py -- registry registration
# ------------------------------------------------------------

me_registry_anchor = '''    registry.register(build_firms_connector())
    registry.register(build_gpm_connector())
    registry.register(build_era5_connector())
    return registry'''

me_registry_addition = '''    registry.register(build_firms_connector())
    registry.register(build_gpm_connector())
    registry.register(build_era5_connector())
    registry.register(build_earthquake_connector())
    registry.register(build_population_connector())
    return registry'''

patch("core/engines/main_engine.py", me_registry_anchor, me_registry_addition, "main_engine.py (registry)")


# ------------------------------------------------------------
# 4. core/engines/main_engine.py -- new methods
# ------------------------------------------------------------

me_methods_anchor = "    def get_satellite_live_status(self, satellite_id: str) -> dict[str, Any] | None:"

me_methods_addition = '''    def get_earthquakes(self, period: str = "day", min_magnitude: float | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        connector = self.connectors.get("USGS-Earthquake")

        if connector is None or not connector.is_enabled():
            result = {"mode": "mock", "provider": "USGS-Earthquake", "events": [], "count": 0, "checked_at": now}
            self._last_status["earthquake"] = result
            return result

        result_obj = connector.search(period=period, min_magnitude=min_magnitude)

        if not result_obj.success:
            print(f"[MainEngine] USGS search failed: {result_obj.error}")
            result = {
                "mode": "mock", "provider": "USGS-Earthquake", "events": [], "count": 0,
                "error": result_obj.error, "checked_at": now,
            }
            self._last_status["earthquake"] = result
            return result

        result = {
            "mode": "live",
            "provider": "USGS-Earthquake",
            "events": result_obj.data,
            "count": result_obj.metadata.get("count", len(result_obj.data)),
            "checked_at": now,
        }
        self._last_status["earthquake"] = result
        return result

    def get_population_exposure(self, latitude: float, longitude: float, radius_km: float = 50.0) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        connector = self.connectors.get("WorldPop")

        if connector is None or not connector.is_enabled():
            result = {"mode": "mock", "provider": "WorldPop", "population": None, "checked_at": now}
            self._last_status["population"] = result
            return result

        result_obj = connector.search(latitude=latitude, longitude=longitude, radius_km=radius_km)

        if not result_obj.success:
            print(f"[MainEngine] WorldPop search failed: {result_obj.error}")
            result = {"mode": "mock", "provider": "WorldPop", "population": None, "error": result_obj.error, "checked_at": now}
            self._last_status["population"] = result
            return result

        result = {
            "mode": "live",
            "provider": "WorldPop",
            **result_obj.data,
            "cached": result_obj.metadata.get("cached", False),
            "checked_at": now,
        }
        self._last_status["population"] = result
        return result

    def get_satellite_live_status(self, satellite_id: str) -> dict[str, Any] | None:'''

patch("core/engines/main_engine.py", me_methods_anchor, me_methods_addition, "main_engine.py (new methods)")


# ------------------------------------------------------------
# 5. core/risk_engine.py -- calculate_earthquake_risk
# ------------------------------------------------------------

risk_anchor = '''        return {

            "risk_score": score,

            "severity": severity

        }'''

risk_addition = risk_anchor + '''

    def calculate_earthquake_risk(self, event):

        magnitude = event.get("magnitude") or 0
        depth_km = event.get("depth_km")
        population = event.get("population_exposed")

        score = 0

        # Magnitude
        if magnitude >= 7.0:
            score += 40
        elif magnitude >= 6.0:
            score += 32
        elif magnitude >= 5.0:
            score += 22
        elif magnitude >= 4.0:
            score += 12
        else:
            score += 5

        # Depth -- shallower quakes cause more surface damage
        if depth_km is not None:
            if depth_km <= 10:
                score += 30
            elif depth_km <= 35:
                score += 20
            elif depth_km <= 70:
                score += 10
            else:
                score += 5
        else:
            score += 10

        # Population exposure within the search radius
        if population is not None:
            if population >= 1_000_000:
                score += 30
            elif population >= 250_000:
                score += 22
            elif population >= 50_000:
                score += 14
            elif population >= 5_000:
                score += 7
            else:
                score += 2
        else:
            score += 5

        if score >= 90:
            severity = "Extreme"
        elif score >= 70:
            severity = "High"
        elif score >= 50:
            severity = "Moderate"
        else:
            severity = "Low"

        return {
            "risk_score": score,
            "severity": severity,
        }'''

patch("core/risk_engine.py", risk_anchor, risk_addition, "risk_engine.py (calculate_earthquake_risk)")


# ------------------------------------------------------------
# 6. core/decision_engine.py -- recommend_earthquake
# ------------------------------------------------------------

decision_anchor = '''        return {

            "recommended_actions": actions

        }'''

decision_addition = decision_anchor + '''

    def recommend_earthquake(self, event):

        severity = event["severity"]

        if severity == "Low":
            actions = ["Log event", "Monitor for aftershocks"]

        elif severity == "Moderate":
            actions = [
                "Notify County Disaster Office",
                "Alert nearby emergency services",
                "Monitor for aftershocks",
            ]

        elif severity == "High":
            actions = [
                "Notify National Disaster Operations Centre",
                "Dispatch damage assessment teams",
                "Alert hospitals in the affected county",
                "Prepare emergency shelters",
            ]

        elif severity == "Extreme":
            actions = [
                "Activate National Disaster Response",
                "Deploy Search and Rescue Teams",
                "Alert all hospitals and emergency services",
                "Issue Public Warning",
                "Prepare mass evacuation and shelter",
                "Request international assistance if needed",
            ]

        else:
            actions = ["Monitor situation"]

        return {"recommended_actions": actions}'''

patch("core/decision_engine.py", decision_anchor, decision_addition, "decision_engine.py (recommend_earthquake)")

print()
print("ALL PATCHES APPLIED SUCCESSFULLY.")
