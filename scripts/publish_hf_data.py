"""Publish the verified DELTA presentation data to a public Hugging Face Dataset repo.

Render (backend host) tải các file này lúc build Docker image. Script không sinh dữ liệu mới:
chỉ upload bundle đã export và các nguồn indicator và supplements đã pin hash, fail-closed nếu thiếu/sai hash.
Token lấy từ HF_TOKEN hoặc cache của `huggingface_hub.login()`; không truyền token qua tham số.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Served bundle (owner switched to v4 on 25/10/2026; v1–v3 stay local, unchanged).
BUNDLE = ROOT / 'data/web/delta-intelligence-v4'
INDICATOR_CONFIG = ROOT / 'configs/product/indicator_reference_v1.json'
DATA_FILES_LIST = ROOT / 'deploy/render/data-files.txt'


def sha256(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def collect():
    """Return {path_in_repo: local_path} (repo-relative paths), failing closed on hash mismatch."""
    files = {}
    manifest = json.loads((BUNDLE / 'manifest.json').read_bytes())
    database = BUNDLE / 'terminal.sqlite'
    if not database.is_file() or sha256(database) != manifest.get('database_sha256'):
        raise SystemExit('Presentation database missing or checksum mismatch. Re-export first.')
    for path in (BUNDLE / 'manifest.json', database):
        files[path.relative_to(ROOT).as_posix()] = path
    for source in json.loads(INDICATOR_CONFIG.read_bytes())['sources']:
        for key in ('manifest', 'file'):
            local = ROOT / source[key]
            if not local.is_file() or sha256(local) != source[f'{key}_sha256']:
                raise SystemExit(f'Indicator source missing or checksum mismatch: {source[key]}')
            files[source[key]] = local
        for item in source.get('supplements',[]):
            local=ROOT/item['file']
            if not local.is_file() or sha256(local)!=item['sha256']:
                raise SystemExit('Indicator supplementary evidence missing or checksum mismatch: '+item['file'])
            files[item['file']]=local
    indicators=ROOT/'configs/product/indicators_v1.json'
    if indicators.is_file():
        pointer=json.loads(indicators.read_bytes())
        for key in ('manifest','file'):
            local=ROOT/pointer[key]
            if not local.is_file() or sha256(local)!=pointer[key+'_sha256']:raise SystemExit('Indicators v1 source missing or checksum mismatch: '+pointer[key])
            files[pointer[key]]=local
    preview=ROOT/'configs/product/model_previews_v1.json'
    if preview.is_file():
        pointer=json.loads(preview.read_bytes())
        seal=json.loads((ROOT/pointer['manifest']).read_bytes())
        if seal.get('database_sha256')!=manifest.get('database_sha256'):
            # R1 previews are pinned to another bundle; the API serves without them.
            return files
        for key in ('manifest','file'):
            local=ROOT/pointer[key]
            if not local.is_file() or sha256(local)!=pointer[key+'_sha256']:raise SystemExit('Research preview source missing or checksum mismatch: '+pointer[key])
            files[pointer[key]]=local
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='delta-intelligence-data', help='Dataset name or <owner>/<name>.')
    parser.add_argument('--dry-run', action='store_true', help='Only list and verify files.')
    args = parser.parse_args()
    files = collect()
    for target, local in files.items():
        print(f'{local.stat().st_size / 1048576:9.1f} MB  {target}')
    # Keep the Docker download list in sync with what is published.
    DATA_FILES_LIST.write_text(''.join(f'{t}\n' for t in files), encoding='utf-8', newline='\n')
    if args.dry_run:
        return
    from huggingface_hub import CommitOperationAdd, HfApi
    api = HfApi()
    repo_id = args.repo if '/' in args.repo else f"{api.whoami()['name']}/{args.repo}"
    api.create_repo(repo_id, repo_type='dataset', private=False, exist_ok=True)
    api.create_commit(repo_id, repo_type='dataset',
                      operations=[CommitOperationAdd(path_in_repo=t, path_or_fileobj=str(p)) for t, p in files.items()],
                      commit_message='Publish verified DELTA presentation bundle and reviewed indicator packages')
    print(f'Dataset: https://huggingface.co/datasets/{repo_id}')
    print(f'Render build arg DATA_BASE_URL=https://huggingface.co/datasets/{repo_id}/resolve/main')


if __name__ == '__main__':
    main()
