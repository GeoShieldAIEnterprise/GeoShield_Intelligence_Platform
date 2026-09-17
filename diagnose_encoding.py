import pathlib
data = pathlib.Path('frontend/templates/index.html').read_bytes()
lines = data.split(b'\n')
for i, line in enumerate(lines, 1):
    if b'\xc3\xb0' in line:
        try:
            fixed = line.decode('utf-8').encode('cp1252').decode('utf-8')
            print(i, 'OK', fixed[:70])
        except Exception as e:
            print(i, 'FAIL', type(e).__name__, str(e))

