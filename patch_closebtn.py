path = r"frontend\templates\index.html"
backup = r"frontend\templates\index.html.closebtn_bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

targets = [
    ('id="liveMapCloseBtn" class="livemap-close-btn" title="Return to Main Map">?</button>',
     'id="liveMapCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>'),
    ('id="floodCloseBtn" class="livemap-close-btn" title="Return to Main Map">?</button>',
     'id="floodCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>'),
    ('id="fireCloseBtn" class="livemap-close-btn" title="Return to Main Map">?</button>',
     'id="fireCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>'),
    ('id="earthquakeCloseBtn" class="livemap-close-btn" title="Return to Main Map">?</button>',
     'id="earthquakeCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>'),
    ('id="droughtCloseBtn" class="livemap-close-btn" title="Return to Main Map">?</button>',
     'id="droughtCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>'),
]

import shutil
shutil.copyfile(path, backup)

for old, new in targets:
    count = content.count(old)
    if count != 1:
        print(f"ABORTED -- expected 1 match, found {count}, for pattern containing: {old[:60]}...")
        raise SystemExit(1)
    content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Patched successfully. Backup saved at {backup}")
