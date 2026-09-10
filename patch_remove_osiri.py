import re
from pathlib import Path

path = Path("frontend/templates/index.html")
src = path.read_text(encoding="utf-8-sig")
original = src

# Remove the OSIRI product section inside Satellite Intelligence page
pattern1 = re.compile(
    r'\s*<!-- OSIRI REAL-TIME.*?</section>\s*',
    re.DOTALL
)
src, count1 = pattern1.subn('\n', src, count=1)

# Remove the fullscreen OSIRI Live Map workspace page (appears twice as a comment marker + the real section)
pattern2 = re.compile(
    r'\s*<!-- OSIRI LIVE MAP FULLSCREEN WORKSPACE PAGE -->\s*',
    re.DOTALL
)
src = pattern2.sub('\n', src)

pattern3 = re.compile(
    r'\s*<section id="osiriLiveMapPage".*?</section>\s*',
    re.DOTALL
)
src, count3 = pattern3.subn('\n', src, count=1)

# Remove the osiri-live-map.js script include
src = src.replace('<script src="/static/osiri-live-map.js"></script>\n', '')
src = src.replace('<script src="/static/osiri-live-map.js"></script>', '')

# Remove the dead, unused satelliteHub div
src = src.replace('<div id="satelliteHub"></div>\n            ', '')
src = src.replace('<div id="satelliteHub"></div>', '')

if src == original:
    print("No changes were necessary (already removed?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print(f"index.html patched -- OSIRI removed completely (product section: {count1}, fullscreen page: {count3}).")
