from pathlib import Path

def patch(path_str, anchor, addition, label):
    path = Path(path_str)
    src = path.read_text(encoding="utf-8-sig")
    original = src
    if anchor not in src:
        raise SystemExit(f"ERROR: anchor not found for {label} in {path_str} -- printing file:\n" + src)
    src = src.replace(anchor, addition, 1)
    if src == original:
        print(f"{label}: no changes were necessary.")
    else:
        path.write_text(src, encoding="utf-8", newline="\n")
        print(f"{label}: patched successfully.")


# ------------------------------------------------------------
# 1. core/risk_engine.py -- rebalanced calculate_agriculture_risk with NDVI
# ------------------------------------------------------------

risk_anchor = '''    def calculate_agriculture_risk(self, record):

        rainfall_mm = record.get("rainfall_mm")
        temperature_c = record.get("temperature_c")
        humidity_pct = record.get("humidity_pct")

        score = 0

        if rainfall_mm is None:
            score += 15
        elif rainfall_mm < 1:
            score += 40
        elif rainfall_mm < 5:
            score += 30
        elif rainfall_mm < 15:
            score += 15
        else:
            score += 5

        if temperature_c is None:
            score += 10
        elif temperature_c >= 35:
            score += 30
        elif temperature_c >= 30:
            score += 20
        elif temperature_c >= 25:
            score += 10
        else:
            score += 5

        if humidity_pct is None:
            score += 10
        elif humidity_pct < 30:
            score += 30
        elif humidity_pct < 50:
            score += 20
        elif humidity_pct < 70:
            score += 10
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

risk_replacement = '''    def calculate_agriculture_risk(self, record):

        rainfall_mm = record.get("rainfall_mm")
        temperature_c = record.get("temperature_c")
        humidity_pct = record.get("humidity_pct")
        ndvi = record.get("ndvi")

        score = 0

        # Rainfall
        if rainfall_mm is None:
            score += 10
        elif rainfall_mm < 1:
            score += 25
        elif rainfall_mm < 5:
            score += 18
        elif rainfall_mm < 15:
            score += 10
        else:
            score += 3

        # Temperature
        if temperature_c is None:
            score += 8
        elif temperature_c >= 35:
            score += 25
        elif temperature_c >= 30:
            score += 17
        elif temperature_c >= 25:
            score += 8
        else:
            score += 3

        # Humidity
        if humidity_pct is None:
            score += 8
        elif humidity_pct < 30:
            score += 25
        elif humidity_pct < 50:
            score += 17
        elif humidity_pct < 70:
            score += 8
        else:
            score += 3

        # NDVI (vegetation health) -- low NDVI means sparse/stressed vegetation
        if ndvi is None:
            score += 10
        elif ndvi < 0.15:
            score += 25
        elif ndvi < 0.25:
            score += 17
        elif ndvi < 0.35:
            score += 8
        else:
            score += 3

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

patch("core/risk_engine.py", risk_anchor, risk_replacement, "risk_engine.py (calculate_agriculture_risk + NDVI)")


# ------------------------------------------------------------
# 2. backend/disaster/agriculture_engine.py -- pull and merge NDVI per county
# ------------------------------------------------------------

analyse_anchor = '''    def analyse(self) -> list[dict[str, Any]]:
        rainfall = main_engine.get_gpm_rainfall()
        weather = main_engine.get_era5_weather()

        rainfall_counties = rainfall.get("counties", {})
        weather_counties = weather.get("counties", {})

        all_counties = set(rainfall_counties.keys()) | set(weather_counties.keys())

        enriched: list[dict[str, Any]] = []

        for county in sorted(all_counties):
            weather_data = weather_counties.get(county, {})

            record = {
                "county": county,
                "rainfall_mm": rainfall_counties.get(county),
                "temperature_c": weather_data.get("temperature_c"),
                "humidity_pct": weather_data.get("humidity_pct"),
                "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
                "rainfall_mode": rainfall.get("mode"),
                "weather_mode": weather.get("mode"),
            }

            risk = self.risk.calculate_agriculture_risk(record)
            decision = self.decision.recommend_agriculture(risk)

            enriched.append({
                **record,
                **risk,
                **decision,
            })

        return enriched'''

analyse_replacement = '''    def analyse(self) -> list[dict[str, Any]]:
        rainfall = main_engine.get_gpm_rainfall()
        weather = main_engine.get_era5_weather()
        ndvi = main_engine.get_sentinel2_ndvi()

        rainfall_counties = rainfall.get("counties", {})
        weather_counties = weather.get("counties", {})
        ndvi_counties = ndvi.get("counties", {})

        all_counties = set(rainfall_counties.keys()) | set(weather_counties.keys()) | set(ndvi_counties.keys())

        enriched: list[dict[str, Any]] = []

        for county in sorted(all_counties):
            weather_data = weather_counties.get(county, {})

            record = {
                "county": county,
                "rainfall_mm": rainfall_counties.get(county),
                "temperature_c": weather_data.get("temperature_c"),
                "humidity_pct": weather_data.get("humidity_pct"),
                "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
                "ndvi": ndvi_counties.get(county),
                "rainfall_mode": rainfall.get("mode"),
                "weather_mode": weather.get("mode"),
                "ndvi_mode": ndvi.get("mode"),
            }

            risk = self.risk.calculate_agriculture_risk(record)
            decision = self.decision.recommend_agriculture(risk)

            enriched.append({
                **record,
                **risk,
                **decision,
            })

        return enriched'''

patch("backend/disaster/agriculture_engine.py", analyse_anchor, analyse_replacement, "agriculture_engine.py (analyse + NDVI)")

satellites_anchor = '            "satellites": ["GPM-IMERG", "ERA5-OpenMeteo"],'
satellites_replacement = '            "satellites": ["GPM-IMERG", "ERA5-OpenMeteo", "Sentinel2-NDVI"],'
patch("backend/disaster/agriculture_engine.py", satellites_anchor, satellites_replacement, "agriculture_engine.py (satellites list)")


# ------------------------------------------------------------
# 3. backend/main.py -- background NDVI cache warm-up
# ------------------------------------------------------------

import_anchor = "from core.engines.main_engine import main_engine"
import_replacement = "import threading\nimport time\nfrom core.engines.main_engine import main_engine"
patch("backend/main.py", import_anchor, import_replacement, "main.py (threading/time imports)")

startup_anchor = 'main_engine.register_engine("earthquake", earthquake_engine)'
startup_replacement = '''main_engine.register_engine("earthquake", earthquake_engine)

NDVI_WARMUP_INTERVAL_SECONDS = 170 * 60  # refresh just under the connector's 180-minute cache window

def _ndvi_warmup_loop():
    while True:
        try:
            print("[NDVI Warmup] Refreshing Sentinel-2 NDVI cache...")
            result = main_engine.get_sentinel2_ndvi()
            print(f"[NDVI Warmup] Done -- mode={result.get('mode')}, counties={len(result.get('counties', {}))}")
        except Exception as exc:
            print(f"[NDVI Warmup] Failed: {exc!r}")
        time.sleep(NDVI_WARMUP_INTERVAL_SECONDS)

@app.on_event("startup")
def _start_ndvi_warmup():
    threading.Thread(target=_ndvi_warmup_loop, daemon=True).start()'''

patch("backend/main.py", startup_anchor, startup_replacement, "main.py (NDVI warmup thread)")

print()
print("ALL NDVI WIRING PATCHES APPLIED.")
