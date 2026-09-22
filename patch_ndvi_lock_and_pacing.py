import re
import shutil

path = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py"
backup = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py.bak2"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# --- 1. Add threading import + a module-level lock ---
if "import threading" not in content:
    content = content.replace(
        "import time\n",
        "import threading\nimport time\n",
        1,
    )
    content = content.replace(
        "logger = logging.getLogger(__name__)",
        "logger = logging.getLogger(__name__)\n_search_lock = threading.Lock()",
        1,
    )

# --- 2. Add a per-request delay constant ---
content = content.replace(
    "CACHE_MINUTES = 180",
    "CACHE_MINUTES = 180\nREQUEST_DELAY_SECONDS = 0.8  # pacing between per-county calls to avoid 429s\nMAX_RETRIES_ON_RATE_LIMIT = 3\nRETRY_BACKOFF_SECONDS = 5",
    1,
)

# --- 3. Wrap search() body with the lock, and add pacing + retry in the county loop ---
old_loop = '''        results: dict[str, float | None] = {}
        stale_counties: list[str] = []

        for name, geometry in counties:
            fresh = self._query_county_ndvi(token, geometry, date_from_str, date_to_str)

            if fresh is not None:'''

new_loop = '''        results: dict[str, float | None] = {}
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

            time.sleep(REQUEST_DELAY_SECONDS)  # pace every county call, success or not

            if fresh is not None:'''

if old_loop not in content:
    print("ABORTED at loop patch -- pattern not found. No changes made.")
    raise SystemExit(1)
content = content.replace(old_loop, new_loop, 1)

# --- 4. Wrap the whole search() method body in the lock ---
search_sig = "    def search(self, **filters: Any) -> ConnectorResult:\n"
if search_sig not in content:
    print("ABORTED -- search() signature not found. No changes made.")
    raise SystemExit(1)

idx = content.index(search_sig)
head = content[:idx + len(search_sig)]
rest = content[idx + len(search_sig):]

# Indent the entire rest of the method body by 4 spaces and wrap in `with _search_lock:`
end_marker = "\n    def download(self, product_id: str)"
if end_marker not in rest:
    print("ABORTED -- could not find end of search() method. No changes made.")
    raise SystemExit(1)

body, tail = rest.split(end_marker, 1)
indented_body = "\n".join(
    ("    " + line if line.strip() else line) for line in body.split("\n")
)
new_method = head + "        with _search_lock:\n" + indented_body + end_marker + tail

content = content[:idx] + new_method[len(head):] if False else content  # placeholder, real assembly below
content_final = head + "        with _search_lock:\n" + indented_body + end_marker + tail
content = content[:idx] + content_final[idx:] if False else (content[:idx] + new_method[idx:] if False else content)

# Simplify: rebuild content directly
content = content[:idx] + "        with _search_lock:\n" + indented_body + end_marker + tail

shutil.copyfile(path, backup)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Patched successfully. Backup saved at {backup}")
