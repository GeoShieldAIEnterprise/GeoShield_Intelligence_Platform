import shutil, pathlib
p = pathlib.Path('frontend/templates/index.html')
shutil.copy(p, str(p) + '.bak')
text = p.read_text(encoding='utf-8')

def fix(line):
    try:
        return line.encode('cp1252').decode('utf-8')
    except Exception:
        return line

fixed = ''.join(fix(l) for l in text.splitlines(keepends=True))
p.write_text(fixed, encoding='utf-8')
print('Fixed. Backup saved as', str(p) + '.bak')

