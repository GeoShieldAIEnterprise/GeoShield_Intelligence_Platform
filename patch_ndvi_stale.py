import re
import shutil

path = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py"
backup = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py.bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# --- 1. Add logging import ---
if "import logging" not in content:
    content = content.replace(
        "from typing import Any\n",
        "from typing import Any\nimport logging\n",
        1,
    )
    content = content.replace(
        'STATISTICS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"',
        'logger = logging.getLogger(__name__)\n\nSTATISTICS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"',
        1,
    )

# --- 2. Patch __init__ to add last-known-good stores ---
init_pattern = re.compile(
    r"    def __init__\(self, config: ConnectorConfig\) -> None:.*?\n(?=    @property)",
    re.DOTALL,
)
new_init = '''    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._auth = CopernicusAuthManager()
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0
        # Stale-while-revalidate: NDVI changes slowly, so a county that fails
        # to fetch this cycle should keep showing its last successful reading
        # rather than going blank. These never expire on their own -- only a
        # fresh successful fetch overwrites them.
        self._last_good: dict[str, float] = {}
        self._last_good_time: dict[str, float] = {}

'''

init_matches = init_pattern.findall(content)
if len(init_matches) != 1:
    print(f"ABORTED at __init__ -- expected 1 match, found {len(init_matches)}. No changes made.")
    raise SystemExit(1)

content = init_pattern.sub(new_init, content, count=1)

# --- 3. Patch search() for stale-fallback behavior ---
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

        try:
            token = self._auth.get_token()

        except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as exc:
            if self._last_good:
                logger.warning(
                    "Sentinel2-NDVI auth failed (%s); serving last-known-good NDVI for all counties.", exc
                )
                return ConnectorResult.ok(
                    provider=self.provider_name,
                    operation="search",
                    data=dict(self._last_good),
                    metadata={
                        "cached": True,
                        "stale_fallback": True,
                        "stale_counties": sorted(self._last_good.keys()),
                        "reason": str(exc),
                    },
                )
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=str(exc),
            )

        date_to = datetime.now(timezone.utc)
        date_from = date_to - timedelta(days=LOOKBACK_DAYS)
        date_to_str = date_to.strftime("%Y-%m-%dT%H:%M:%SZ")
        date_from_str = date_from.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            counties = self._county_geometries()

        except Exception as exc:
            if self._last_good:
                logger.warning(
                    "Failed to load county boundaries (%s); serving last-known-good NDVI.", exc
                )
                return ConnectorResult.ok(
                    provider=self.provider_name,
                    operation="search",
                    data=dict(self._last_good),
                    metadata={
                        "cached": True,
                        "stale_fallback": True,
                        "stale_counties": sorted(self._last_good.keys()),
                        "reason": str(exc),
                    },
                )
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Failed to load county boundaries: {exc}",
            )

        results: dict[str, float | None] = {}
        stale_counties: list[str] = []

        for name, geometry in counties:
            fresh = self._query_county_ndvi(token, geometry, date_from_str, date_to_str)

            if fresh is not None:
                results[name] = fresh
                self._last_good[name] = fresh
                self._last_good_time[name] = now
            elif name in self._last_good:
                results[name] = self._last_good[name]
                stale_counties.append(name)
                age_min = (now - self._last_good_time.get(name, now)) / 60
                logger.warning(
                    "NDVI fetch failed for %s this cycle; serving last-known-good value from %.0f min ago.",
                    name, age_min,
                )
            else:
                results[name] = None
                logger.warning("NDVI fetch failed for %s and no prior value exists; returning null.", name)

        self._cache = results
        self._cache_time = now

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=results,
            metadata={
                "cached": False,
                "lookback_days": LOOKBACK_DAYS,
                "stale_counties": stale_counties,
            },
        )

'''

search_matches = search_pattern.findall(content)
if len(search_matches) != 1:
    print(f"ABORTED at search() -- expected 1 match, found {len(search_matches)}. No changes made.")
    raise SystemExit(1)

content = search_pattern.sub(new_search, content, count=1)

shutil.copyfile(path, backup)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Patched successfully. Backup saved at {backup}")
