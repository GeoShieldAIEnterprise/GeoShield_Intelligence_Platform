import pathlib, shutil
p = pathlib.Path('frontend/templates/index.html')
shutil.copy(p, str(p) + '.bak5')
cp1252_map = {i: bytes([i]).decode('cp1252') for i in range(0x80, 0xA0) if i not in (0x81, 0x8D, 0x8F, 0x90, 0x9D)}
for gap in (0x81, 0x8D, 0x8F, 0x90, 0x9D):
    cp1252_map[gap] = chr(gap)
reverse_map = {v: k for k, v in cp1252_map.items()}
data = p.read_bytes()
lines = data.split(b'\n')
out = []
for i, line in enumerate(lines, 1):
    if b'\xc3\xb0' not in line:
        out.append(line); continue
    try:
        s = line.decode('utf-8')
        rebuilt = bytearray()
        for ch in s:
            cp = ord(ch)
            if ch in reverse_map:
                rebuilt.append(reverse_map[ch])
            elif cp < 0x80 or 0xA0 <= cp <= 0xFF:
                rebuilt.append(cp)
            else:
                raise ValueError('unmappable char U+%04X' % cp)
        fixed = bytes(rebuilt).decode('utf-8').encode('utf-8')
        out.append(fixed)
        print('LINE', i, 'FIXED')
    except Exception as e:
        print('LINE', i, 'FAILED:', e)
        out.append(line)
p.write_bytes(b'\n'.join(out))

