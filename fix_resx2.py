import pathlib
p = pathlib.Path('core/connectors/sentinel2/sentinel2_ndvi_connector.py')
c = p.read_text(encoding='utf-8')
c = c.replace('"resx": 0.05,', '"resx": 0.01,')
c = c.replace('"resy": 0.05,', '"resy": 0.01,')
p.write_text(c, encoding='utf-8')
print("done")
