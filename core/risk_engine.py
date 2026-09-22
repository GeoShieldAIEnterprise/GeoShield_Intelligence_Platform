class RiskEngine:

    def calculate_fire_risk(self, fire):

        score = 0

        # Brightness
        if fire["brightness"] >= 360:
            score += 40
        elif fire["brightness"] >= 340:
            score += 30
        else:
            score += 20

        # Fire Radiative Power
        if fire["frp"] >= 10:
            score += 30
        elif fire["frp"] >= 5:
            score += 20
        else:
            score += 10

        # Confidence
        confidence = fire["confidence"].lower()

        if confidence == "h":
            score += 30
        elif confidence == "n":
            score += 20
        else:
            score += 10

        # Severity Classification
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

            "severity": severity

        }

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
        }
    def calculate_agriculture_risk(self, record):

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
        }


    def calculate_drought_risk(self, record):

        rainfall_mm = record.get("rainfall_mm")
        temperature_c = record.get("temperature_c")
        humidity_pct = record.get("humidity_pct")
        ndvi = record.get("ndvi")

        score = 0

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
        }

    def calculate_flood_risk(self, record):

        rainfall_mm = record.get("rainfall_mm")
        temperature_c = record.get("temperature_c")
        humidity_pct = record.get("humidity_pct")
        ndvi = record.get("ndvi")
        elevation_range_m = record.get("elevation_range_m")
        upland_skm = record.get("upland_skm")
        reference_discharge_cms = record.get("reference_discharge_cms")

        score = 0
        static_hydrology_used = []

        if rainfall_mm is None:
            score += 5
        elif rainfall_mm >= 1200:
            score += 30
        elif rainfall_mm >= 800:
            score += 20
        elif rainfall_mm >= 400:
            score += 9
        else:
            score += 3

        if upland_skm is None:
            score += 6
        elif upland_skm >= 80000:
            score += 18
        elif upland_skm >= 30000:
            score += 12
        elif upland_skm >= 10000:
            score += 7
        else:
            score += 2
        if upland_skm is not None:
            static_hydrology_used.append("upland_skm")

        if reference_discharge_cms is None:
            score += 2
        elif reference_discharge_cms >= 500:
            score += 7
        elif reference_discharge_cms >= 100:
            score += 4
        elif reference_discharge_cms >= 20:
            score += 2
        else:
            score += 1
        if reference_discharge_cms is not None:
            static_hydrology_used.append("reference_discharge_cms")

        if elevation_range_m is None:
            score += 5
        elif elevation_range_m < 50:
            score += 15
        elif elevation_range_m < 150:
            score += 10
        elif elevation_range_m < 400:
            score += 6
        else:
            score += 2

        if ndvi is None:
            score += 4
        elif ndvi < 0.15:
            score += 10
        elif ndvi < 0.25:
            score += 7
        elif ndvi < 0.35:
            score += 4
        else:
            score += 1

        if temperature_c is None:
            score += 3
        elif temperature_c >= 32:
            score += 10
        elif temperature_c >= 28:
            score += 6
        else:
            score += 3

        if humidity_pct is None:
            score += 3
        elif humidity_pct >= 70:
            score += 10
        elif humidity_pct >= 50:
            score += 7
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
            "static_hydrology_factors_used": static_hydrology_used,
        }

