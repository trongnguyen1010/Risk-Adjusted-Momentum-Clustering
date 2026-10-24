"""Build-time download of the published DELTA data files (list in data-files.txt) into /app."""
import os
import pathlib
import shutil
import sys
import urllib.request

base = os.environ['DATA_BASE_URL'].rstrip('/')
root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else '/app')
for rel in pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig').split():
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f'{base}/{rel}', timeout=120) as response, open(target, 'wb') as out:
        shutil.copyfileobj(response, out, 1 << 20)
    print(f'{target.stat().st_size:>12}  {rel}', flush=True)
