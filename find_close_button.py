import re

with open("frontend/templates/index.html", "rb") as f:
    content = f.read().decode("utf-8")

# Find any close/exit button markup -- typically a button/span with a
# title like "close" or "exit", or a small standalone symbol near panel headers
pattern = re.compile(r'.{40}[?\u2715\u00d7\u2716].{0,60}(close|exit|dismiss)', re.IGNORECASE)
matches = pattern.findall(content)

pattern2 = re.compile(r'<[^>]*(?:close|exit)[^>]*>.{0,10}')
matches2 = pattern2.findall(content)

print("=== Pattern 1 (symbol near close/exit keyword) ===")
for m in pattern.finditer(content):
    print(repr(m.group(0)))
    print()

print("=== Pattern 2 (close/exit in tag attributes) ===")
for m in pattern2.finditer(content):
    print(repr(m.group(0)))
    print()
