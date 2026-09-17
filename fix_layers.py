import pathlib, shutil
p = pathlib.Path('frontend/templates/index.html')
shutil.copy(p, str(p) + '.bak3')
data = p.read_bytes()
lines = data.split(b'\n')
out = []
for i, line in enumerate(lines, 1):
    if b'\xc3\xb0' not in line:
        out.append(line); continue
    solved = None
    for cycles in (1, 2, 3):
        for enc in ('cp1252', 'latin-1'):
            try:
                cur = line
                for _ in range(cycles):
                    s = cur.decode('utf-8')
                    cur = s.encode(enc)
                final_text = cur.decode('utf-8')
                if 0x1F300 <= ord(next(c for c in final_text if ord(c) > 0x2000), 0) or True:
                    solved = cur
                    print('LINE', i, 'solved with cycles=', cycles, 'enc=', enc)
                    break
            except Exception:
                continue
        if solved:
            break
    out.append(solved if solved else line)
    if not solved:
        print('LINE', i, 'UNSOLVED')
p.write_bytes(b'\n'.join(out))
print('done')

