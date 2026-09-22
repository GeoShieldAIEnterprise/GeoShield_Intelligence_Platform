import os

files_to_remove = [
    r"backend\routes\debug_seed_era5.py",
    r"backend\routes\debug_seed_era5.py.bom_bak",
]

for f in files_to_remove:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed: {f}")
    else:
        print(f"Not found (already gone): {f}")
