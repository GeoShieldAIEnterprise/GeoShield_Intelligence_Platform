from pathlib import Path

path = Path("frontend/templates/index.html")
src = path.read_text(encoding="utf-8-sig")
original = src

head_start = src.lower().find("<head")
if head_start == -1:
    raise SystemExit("ERROR: <head> tag not found -- printing first 3000 chars:\n" + src[:3000])

tag_end = src.find(">", head_start)
if tag_end == -1:
    raise SystemExit("ERROR: could not find end of <head> tag -- printing first 3000 chars:\n" + src[:3000])

nearby = src[tag_end:tag_end + 500].lower()

if "charset" in nearby:
    print("A charset declaration already appears right after <head> -- not auto-inserting a duplicate.")
    print("Nearby content for inspection:")
    print(src[head_start:tag_end + 500])
else:
    insertion_point = tag_end + 1
    src = src[:insertion_point] + '\n    <meta charset="UTF-8">' + src[insertion_point:]
    path.write_text(src, encoding="utf-8", newline="\n")
    print('index.html: <meta charset="UTF-8"> inserted as the first element inside <head>.')
