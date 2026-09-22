import shutil

path = r"core\connectors\era5_connector.py"
backup = r"core\connectors\era5_connector.py.persist_bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

shutil.copyfile(path, backup)

def apply(content, old, new, label):
    count = content.count(old)
    if count != 1:
        print(f"ABORTED at {label} -- expected 1 match, found {count}")
        raise SystemExit(1)
    return content.replace(old, new, 1)

# 1. Add os import
content = apply(
    content,
    "import json\nimport subprocess\nimport logging\nimport time\n",
    "import json\nimport os\nimport subprocess\nimport logging\nimport time\n",
    "os import",
)

# 2. Add on-disk cache file constant
content = apply(
    content,
    'CACHE_MINUTES = 240  # lengthened -- Open-Meteo free tier has a DAILY quota, not just a burst limit\n',
    'CACHE_MINUTES = 240  # lengthened -- Open-Meteo free tier has a DAILY quota, not just a burst limit\n'
    'LAST_GOOD_CACHE_FILE = Path(settings.data_dir) / "era5_last_good.json"  # on-disk backup so a server restart does not lose last-known-good weather\n',
    "cache file constant",
)

# 3. Call disk-load at end of __init__ (note the space before "| None" -- matches actual file)
content = apply(
    content,
    "        self._last_good: dict[str, dict[str, Any]] | None = None\n"
    "        self._last_good_time: float = 0.0\n",
    "        self._last_good: dict[str, dict[str, Any]] | None = None\n"
    "        self._last_good_time: float = 0.0\n"
    "        self._load_last_good_from_disk()\n",
    "__init__ disk-load call",
)

# 4. Insert new load/persist methods before the provider_name property
new_methods = '''
    def _load_last_good_from_disk(self) -> None:
        """On startup, load the last-known-good weather snapshot from disk
        (if one exists) so a server restart does not present a fresh blank
        slate before the first live fetch of this session succeeds."""
        try:
            if not LAST_GOOD_CACHE_FILE.exists():
                return
            with open(LAST_GOOD_CACHE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            data = payload.get("data")
            timestamp = payload.get("timestamp")
            if isinstance(data, dict) and isinstance(timestamp, (int, float)):
                self._last_good = data
                self._last_good_time = timestamp
                logger.info(
                    "ERA5/Open-Meteo: loaded last-known-good weather from disk (%d counties, saved at %s).",
                    len(data), timestamp,
                )
        except Exception as exc:
            # Defensive: a missing/corrupt cache file must never prevent
            # startup or be treated as a hard error -- just start cold,
            # same as if no prior data had ever been fetched.
            logger.warning("ERA5/Open-Meteo: could not load on-disk last-good cache: %s", exc)

    def _persist_last_good_to_disk(self) -> None:
        """Write the current last-known-good snapshot to disk so it survives
        a server restart. Writes to a temp file then renames, so a crash
        mid-write can never leave a corrupt cache file behind."""
        try:
            LAST_GOOD_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = LAST_GOOD_CACHE_FILE.with_suffix(".json.tmp")
            payload = {"timestamp": self._last_good_time, "data": self._last_good}
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp_path, LAST_GOOD_CACHE_FILE)
        except Exception as exc:
            # Defensive: failing to persist to disk must never break the
            # live request in progress -- the in-memory fallback still works.
            logger.warning("ERA5/Open-Meteo: could not persist last-good cache to disk: %s", exc)

'''

content = apply(
    content,
    "    @property\n    def provider_name(self) -> str:",
    new_methods + "    @property\n    def provider_name(self) -> str:",
    "new methods insertion",
)

# 5. Persist to disk right after a successful live fetch updates _last_good
content = apply(
    content,
    "        self._cache = results\n"
    "        self._cache_time = now\n"
    "        self._last_good = dict(results)\n"
    "        self._last_good_time = now\n\n"
    "        return ConnectorResult.ok(",
    "        self._cache = results\n"
    "        self._cache_time = now\n"
    "        self._last_good = dict(results)\n"
    "        self._last_good_time = now\n"
    "        self._persist_last_good_to_disk()\n\n"
    "        return ConnectorResult.ok(",
    "persist call after success",
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Patched successfully. Backup saved at {backup}")
