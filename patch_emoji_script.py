from pathlib import Path

path = Path("frontend/templates/index.html")
src = path.read_text(encoding="utf-8")
script_tag = '<script src="/static/emoji-lock.js"></script>'
if script_tag not in src:
    if "</head>" in src:
        src = src.replace("</head>", f"    {script_tag}\n</head>")
    else:
        src += f"\n{script_tag}"
    path.write_text(src, encoding="utf-8")
    print("index.html successfully updated with emoji-lock.js")
else:
    print("emoji-lock.js is already included in index.html.")
