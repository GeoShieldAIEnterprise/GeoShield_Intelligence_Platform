import pathlib
p = pathlib.Path('frontend/templates/index.html')
data = p.read_bytes()
lines = data.split(b'\n')
fixed_lines = []
count = 0
for line in lines:
    if b'\xc3\xb0' in line:
        try:
            fixed = line.decode('utf-8').encode('latin-1').decode('utf-8').encode('utf-8')
            fixed_lines.append(fixed)
            count += 1
        except Exception:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)
result = b'\n'.join(fixed_lines)
p.write_bytes(result)
print('Fixed', count, 'more lines')

