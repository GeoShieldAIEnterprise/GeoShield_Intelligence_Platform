import pathlib, shutil
p = pathlib.Path('frontend/templates/index.html')
shutil.copy(p, str(p) + '.bak2')
data = p.read_bytes()
lines = data.split(b'\n')
out = []
fixed_count = 0
for i, line in enumerate(lines, 1):
    if b'\xc3\xb0' in line:
        try:
            fixed = line.decode('utf-8').encode('cp1252').decode('utf-8').encode('utf-8')
            out.append(fixed); fixed_count += 1; continue
        except Exception:
            pass
        try:
            fixed = line.decode('utf-8').encode('latin-1').decode('utf-8').encode('utf-8')
            out.append(fixed); fixed_count += 1; continue
        except Exception as e:
            print('LINE', i, 'STILL FAILING:', type(e).__name__)
            out.append(line); continue
    out.append(line)
p.write_bytes(b'\n'.join(out))
print('Total fixed this pass:', fixed_count)

