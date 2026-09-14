from pathlib import Path
import glob

backups = sorted(glob.glob("frontend/static/style.css.bak_*"))
if not backups:
    raise SystemExit("ERROR: no backup file found matching style.css.bak_*")

backup_path = Path(backups[-1])
backup_content = backup_path.read_text(encoding="utf-8-sig")

marker = "GEOSHIELD COLLAPSIBLE WORKSPACE"
idx = backup_content.find(marker)

if idx == -1:
    raise SystemExit(f"ERROR: marker not found in {backup_path} -- cannot safely split. Printing first 2000 chars:\n" + backup_content[:2000])

# Walk back to the start of the comment block that contains the marker,
# so we don't cut off mid-comment.
comment_start = backup_content.rfind("/*", 0, idx)
original_head = backup_content[:comment_start].rstrip() + "\n\n"

current = Path("frontend/static/style.css").read_text(encoding="utf-8-sig")

merged = original_head + current

Path("frontend/static/style.css").write_text(merged, encoding="utf-8", newline="\n")
print(f"Merged {len(original_head)} bytes of recovered base styles (from {backup_path.name}) with the consolidated layout rules.")
print(f"New style.css size: {len(merged)} bytes")
