"""Reproduce the local CPU OCR dependency bundle; no system installation."""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def setup(network):
    config=json.loads((ROOT/'configs/data/financial_ocr_runtime_v1.json').read_bytes())
    if sys.version_info[:2]!=(3,12):raise ValueError('pinned wheel requires Python3.12 x64')
    out=ROOT/config['runtime_folder'];out.mkdir(parents=True,exist_ok=True)
    for item in config['assets']:
        target=ROOT/item['path']
        if not target.exists():
            if not network:raise ValueError('Missing dependency; use setup --network explicitly: '+item['path'])
            time.sleep(2)
            with urllib.request.urlopen(urllib.request.Request(item['source_url'],headers={'User-Agent':'DeltaT1Research dependency setup'}),timeout=config['timeout_seconds']) as response:
                if response.status!=200:raise ValueError('dependency download stopped')
                raw=response.read(config['max_download_bytes']+1)
            if len(raw)>config['max_download_bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
                raise ValueError('dependency size/hash mismatch')
            target.write_bytes(raw)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('cached dependency hash mismatch')
    wheel=next(ROOT/a['path'] for a in config['assets'] if a['path'].endswith('.whl'))
    runtime=out/'runtime';runtime.mkdir(exist_ok=True)
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if not (runtime/name).resolve().is_relative_to(runtime.resolve()):raise ValueError('archive path escape')
        archive.extractall(runtime)
    downloads=out/'downloads.json'
    if not downloads.exists():downloads.write_text(json.dumps(config['assets'],indent=2)+'\n',encoding='utf-8')
    lock_raw=(ROOT/config['expected_lock']).read_bytes();lock=json.loads(lock_raw)
    for relative,sha in lock['files'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=sha:
            raise ValueError('reproduced runtime differs: '+relative)
    target=out/'runtime-lock.json'
    if target.exists() and target.read_bytes()!=lock_raw:raise ValueError('runtime lock differs; no overwrite')
    if not target.exists():target.write_bytes(lock_raw)
    sys.path.insert(0,str(runtime))
    import tesserocr
    with tesserocr.PyTessBaseAPI(path=str(out),lang='vie+eng') as api:
        languages=api.GetLoadedLanguages()
    return dict(status='PASS',engine=tesserocr.tesseract_version(),languages=languages,system_install=False,
                runtime_lock=config['expected_lock'],actual_python=sys.version)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--network',action='store_true');a=p.parse_args()
    try:print(json.dumps(setup(a.network),ensure_ascii=False,indent=2))
    except Exception as e:print(json.dumps(dict(status='FAIL_CLOSED',reason=str(e))));raise SystemExit(2)
