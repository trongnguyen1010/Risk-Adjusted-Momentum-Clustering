"""Import the pinned C8 V2 ZIP without overwriting different existing evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.market_financial_integration import inside, sha, check_hashes


def import_bundle(root, bundle, config):
    if sha(bundle) != config['bundle_sha256']:
        raise ValueError('bundle checksum mismatch')
    prefix = config['market_root'] + '/'
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate ZIP entry')
        manifest_data = archive.read(prefix + 'manifest.json')
        if hashlib.sha256(manifest_data).hexdigest() != config['market_manifest_sha256']:
            raise ValueError('manifest checksum mismatch')
        manifest = json.loads(manifest_data)
        expected = {prefix + p: h for p, h in manifest['outputs'].items()}
        expected[prefix + 'manifest.json'] = config['market_manifest_sha256']
        if set(names) != set(expected):
            raise ValueError('unexpected ZIP inventory')
        # Validate every destination before writing any file.
        for name in names:
            target = inside(root, name)
            if target.exists() and sha(target) != expected[name]:
                raise ValueError('existing different evidence: ' + name)
        for name in names:
            target = inside(root, name)
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.importing')
            if temporary.exists():
                raise ValueError('incomplete prior import requires review: ' + str(temporary))
            try:
                with archive.open(name) as source, temporary.open('xb') as stream:
                    shutil.copyfileobj(source, stream, 4 * 1024 * 1024)
                if sha(temporary) != expected[name]:
                    raise ValueError('extracted checksum mismatch: ' + name)
                temporary.rename(target)
            finally:
                if temporary.exists():
                    temporary.unlink()
    return check_hashes(root, expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    args = parser.parse_args()
    cfg = json.loads((ROOT / 'configs/data/market_financial_integration_v1.json').read_text(encoding='utf-8'))
    print('Verified imported files:', import_bundle(ROOT, args.bundle, cfg))
