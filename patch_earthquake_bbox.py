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

# Default earthquake feed to Kenya-wide bbox (same box VIIRS/FIRMS already uses),
# so /api/earthquake/live matches every other engine's Kenya scope by default,
# with no frontend changes required.

patch(
    "backend/disaster/earthquake_engine.py",
    '    def analyse(\n'
    '        self,\n'
    '        period: str = "day",\n'
    '        min_magnitude: float | None = 4.0,\n'
    '        bbox: tuple[float, float, float, float] | None = None,\n'
    '    ) -> list[dict[str, Any]]:',

    '    KENYA_BBOX = (33.5, -5.0, 42.0, 5.5)  # west, south, east, north -- same box used by VIIRS/FIRMS\n'
    '\n'
    '    def analyse(\n'
    '        self,\n'
    '        period: str = "day",\n'
    '        min_magnitude: float | None = 4.0,\n'
    '        bbox: tuple[float, float, float, float] | None = None,\n'
    '    ) -> list[dict[str, Any]]:\n'
    '\n'
    '        if bbox is None:\n'
    '            bbox = self.KENYA_BBOX',
    "earthquake_engine.py (default Kenya bbox)",
)

print()
print("BBOX SCOPING APPLIED -- restart uvicorn and re-test.")
