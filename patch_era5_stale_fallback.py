import re
import shutil

path = r"core\connectors\era5_connector.py"
backup = r"core\connectors\era5_connector.py.bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# --- 1. Bump cache window, add logging import ---
content = content.replace("CACHE_MINUTES = 30", "CACHE_MINUTES = 240  # lengthened -- Open-Meteo free tier has a DAILY quota, not just a burst limit", 1)
if "import logging" not in content:
    content = content.replace("import time\n", "import logging\nimport time\n", 1)
    content = content.replace(
        'OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"',
        'logger = logging.getLogger(__name__)\n\nOPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"',
        1,
    )

# --- 2. Add last-known-good store in __init__ ---
init_pattern = re.compile(
    r"    def __init__\(self, config: ConnectorConfig\) -> None:.*?\n(?=    @property)",
    re.DOTALL,
)
new_init = '''    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0
        # Stale-while-revalidate: Open-Meteo's free tier has a DAILY request
        # quota, so a quota-exhausted day should not blank out weather for
        # all 47 counties -- fall back to the last successful batch instead.
        self._last_good: dict[str, dict[str, Any]] | None = None
        self._last_good_time: float = 0.0

'''
if len(init_pattern.findall(content)) != 1:
    print("ABORTED at __init__ -- pattern not found as expected. No changes made.")
    raise SystemExit(1)
content = init_pattern.sub(new_init, content, count=1)

# --- 3. Replace search() entirely with error-aware + stale-fallback version ---
search_pattern = re.compile(
    r"    def search\(self, \*\*filters: Any\) -> ConnectorResult:.*?\n(?=    def download)",
    re.DOTALL,
)

new_search = '''    def search(self, **filters: Any) -> ConnectorResult:
        now = time.time()

        if self._cache is not None and (now - self._cache_time) < (CACHE_MINUTES * 60):
            return ConnectorResult.ok(
                provider=self.provider_name,
                operation="search",
                data=self._cache,
                metadata={"cached": True, "cache_age_seconds": round(now - self._cache_time)},
            )

        def _stale_fallback(reason: str) -> ConnectorResult | None:
            if self._last_good:
                age_min = (now - self._last_good_time) / 60
                logger.warning(
                    "ERA5/Open-Meteo fetch failed (%s); serving last-known-good weather from %.0f min ago.",
                    reason, age_min,
                )
                return ConnectorResult.ok(
                    provider=self.provider_name,
                    operation="search",
                    data=dict(self._last_good),
                    metadata={"cached": True, "stale_fallback": True, "reason": reason},
                )
            return None

        try:
            counties = gpd.read_file(COUNTIES_GEOJSON)

        except Exception as exc:
            fallback = _stale_fallback(f"Failed to load county boundaries: {exc}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Failed to load county boundaries: {exc}",
            )

        names: list[str] = []
        lats: list[str] = []
        lons: list[str] = []

        for _, row in counties.iterrows():
            name = row.get("COUNTY") or row.get("NAME") or row.get("name")

            if not name:
                continue

            centroid = row.geometry.centroid
            names.append(name)
            lats.append(str(round(centroid.y, 4)))
            lons.append(str(round(centroid.x, 4)))

        lat_param = ",".join(lats)
        lon_param = ",".join(lons)

        url = (
            f"{OPEN_METEO_URL}?latitude={lat_param}&longitude={lon_param}"
            "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure"
            "&timezone=auto"
        )

        ok, text = _curl_get(url, min(self.config.timeout, 30))

        if not ok:
            fallback = _stale_fallback(f"Unable to reach Open-Meteo: {text}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Unable to reach Open-Meteo: {text}",
            )

        try:
            data = json.loads(text)

        except ValueError as exc:
            fallback = _stale_fallback(f"Open-Meteo returned an invalid response: {exc}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Open-Meteo returned an invalid response: {exc}",
            )

        # Open-Meteo signals errors (rate limits, bad requests, etc.) as a
        # single JSON object with "error": true -- this must be checked
        # BEFORE the isinstance(data, list) wrap below, or the error body
        # gets silently misread as "1 valid county's worth of data".
        if isinstance(data, dict) and data.get("error"):
            reason = data.get("reason", "Unknown Open-Meteo error")
            fallback = _stale_fallback(f"Open-Meteo error: {reason}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Open-Meteo error: {reason}",
            )

        if not isinstance(data, list):
            data = [data]

        if len(data) != len(names):
            fallback = _stale_fallback(
                f"Mismatch: {len(names)} counties requested, {len(data)} results returned."
            )
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Mismatch: {len(names)} counties requested, {len(data)} results returned.",
            )

        results: dict[str, dict[str, Any]] = {}

        for name, entry in zip(names, data):
            current = entry.get("current", {})
            results[name] = {
                "temperature_c": current.get("temperature_2m"),
                "humidity_pct": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "pressure_hpa": current.get("surface_pressure"),
            }

        self._cache = results
        self._cache_time = now
        self._last_good = dict(results)
        self._last_good_time = now

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=results,
            metadata={"cached": False, "county_count": len(results)},
        )

'''

matches = search_pattern.findall(content)
if len(matches) != 1:
    print(f"ABORTED at search() -- expected 1 match, found {len(matches)}. No changes made.")
    raise SystemExit(1)

content = search_pattern.sub(new_search, content, count=1)

shutil.copyfile(path, backup)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Patched successfully. Backup saved at {backup}")
