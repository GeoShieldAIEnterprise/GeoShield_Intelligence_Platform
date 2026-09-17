import pathlib
p = pathlib.Path('core/connectors/sentinel2/sentinel2_ndvi_connector.py')
c = p.read_text(encoding='utf-8')
broken = '"resx": 0.05,`n                "resy": 0.05,'
fixed = '"resx": 0.05,\n                "resy": 0.05,'
if broken in c:
    c = c.replace(broken, fixed)
    p.write_text(c, encoding='utf-8')
    print("FIXED")
else:
    print("PATTERN NOT FOUND - printing context instead")
    idx = c.find('"resx"')
    print(repr(c[idx-20:idx+80]))
