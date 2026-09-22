import re

with open("core/engines/main_engine.py", "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r'    def get_era5_weather\(self.*?\n(?=    def )', content, re.DOTALL)
if match:
    print(match.group(0))
else:
    print("get_era5_weather not found by that exact signature -- searching loosely...")
    idx = content.find("era5_weather")
    print(content[max(0, idx-100):idx+2500])
