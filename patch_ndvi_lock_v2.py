import re
import shutil

path = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py"
backup = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py.bak3"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(
    r"    def search\(self, \*\*filters: Any\) -> ConnectorResult:.*?\n(?=    def download)",
    re.DOTALL,
)

new_method = """    def search(self, **filters: Any) -> ConnectorResult:
        with _search_lock:
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
                fresh = None
                for attempt in range(MAX_RETRIES_ON_RATE_LIMIT + 1):
                    fresh = self._query_county_ndvi(token, geometry, date_from_str, date_to_str)
                    if fresh is not None:
                        break
                    if attempt < MAX_RETRIES_ON_RATE_LIMIT:
                        logger.warning(
                            "NDVI fetch for %s failed (attempt %d/%d) -- backing off %ds before retry.",
                            name, attempt + 1, MAX_RETRIES_ON_RATE_LIMIT, RETRY_BACKOFF_SECONDS,
                        )
                        time.sleep(RETRY_BACKOFF_SECONDS)

                time.sleep(REQUEST_DELAY_SECONDS)

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

"""

matches = pattern.findall(content)
if len(matches) != 1:
    print(f"ABORTED -- expected 1 match for search(), found {len(matches)}. No changes made.")
else:
    shutil.copyfile(path, backup)
    content = pattern.sub(new_method, content, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched successfully. Backup saved at {backup}")
