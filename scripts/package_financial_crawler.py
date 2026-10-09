"""Create source-only handoff zip; never include local raw data or credentials."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package(output):
    out = (ROOT/output).resolve()
    if not out.is_relative_to(ROOT/'artifacts') or out.exists():
        raise ValueError('new output under artifacts required')
    files = [(p,p.relative_to(ROOT).as_posix()) for p in sorted((ROOT/'src').rglob('*'))
             if p.is_file() and p.suffix in ['.py','.json'] and '__pycache__' not in p.parts]
    names = ['scripts/crawl_financial.py','scripts/crawl_financial.ps1','scripts/ocr_financial_pages.ps1',
        'configs/data/financial_crawl_user.example.json','configs/data/financial_crawl_requirements.txt',
        'tests/__init__.py','tests/unit/__init__.py','tests/unit/experiments/__init__.py',
        'tests/unit/experiments/test_financial_crawl.py']
    files += [(ROOT/name,name) for name in names]
    files.append((ROOT/'docs/crawl/FINANCIAL_CRAWLER_USER_GUIDE.md','README.md'))
    manifest = dict(version='financial-crawler-source-handoff-v1', raw_data_included=False,
        files={name:hashlib.sha256(path.read_bytes()).hexdigest() for path,name in files})
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('xb') as stream, zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path,name in files:
            archive.writestr(name,path.read_bytes())
        archive.writestr('handoff-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return dict(path=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
                bytes=out.stat().st_size,files=len(files),raw_data_included=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    print(json.dumps(package(parser.parse_args().output),indent=2))
