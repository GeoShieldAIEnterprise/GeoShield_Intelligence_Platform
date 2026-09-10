from pathlib import Path

path = Path("backend/api/sentinel2_map_layer.py")
src = path.read_text(encoding="utf-8-sig")
original = src

old = '''@router.get("/tile-layer", response_model=TileLayerConfig)
async def get_tile_layer() -> TileLayerConfig:
    now = datetime.now(timezone.utc).isoformat()

    try:
        token = _auth_manager.get_token()
    except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as e:
        print(f"[sentinel2_map_layer] Copernicus auth failed: {type(e).__name__}: {e}")
        token = None'''

new = '''@router.get("/tile-layer", response_model=TileLayerConfig)
async def get_tile_layer() -> TileLayerConfig:
    import time as _time
    _t0 = _time.time()
    print(f"[sentinel2_map_layer] handler ENTERED at {_t0}", flush=True)

    now = datetime.now(timezone.utc).isoformat()

    try:
        print(f"[sentinel2_map_layer] calling get_token()...", flush=True)
        token = _auth_manager.get_token()
        print(f"[sentinel2_map_layer] get_token() returned after {_time.time() - _t0:.2f}s", flush=True)
    except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as e:
        print(f"[sentinel2_map_layer] Copernicus auth failed after {_time.time() - _t0:.2f}s: {type(e).__name__}: {e}", flush=True)
        token = None'''

if old not in src:
    raise SystemExit("ERROR: handler block not found -- printing file:\n" + src)
src = src.replace(old, new)
path.write_text(src, encoding="utf-8", newline="\n")
print("sentinel2_map_layer.py patched -- diagnostic timing prints added.")
