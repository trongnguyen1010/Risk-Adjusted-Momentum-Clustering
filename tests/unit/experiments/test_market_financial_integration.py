import tempfile
import unittest
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from delta_t1.experiments.market_financial_integration import inside, sha, check_hashes, keyed, publish

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from import_market_bundle import import_bundle


class IntegrationContractTests(unittest.TestCase):
    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                inside(td, '../outside')

    def test_exact_hash_rejects_newline_changes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'model.json'
            p.write_bytes(b'{}\n')
            expected = sha(p)
            self.assertEqual(1, check_hashes(td, {'model.json': expected}))
            p.write_bytes(b'{}\r\n')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                check_hashes(td, {'model.json': expected})

    def test_duplicate_keys_are_not_silently_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'duplicate key'):
            keyed([{'id': 'x'}, {'id': 'x'}], ('id',))

    def test_versioned_output_is_idempotent_but_cannot_change(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'M2/artifacts/m2-final-handoff-v1'
            source.mkdir(parents=True)
            (source / 'm2_cluster_labels_for_m3.csv').write_bytes(b'labels\n')
            data = dict(version='fixture', model_pins={})
            first = publish(td, data)
            self.assertEqual(first, publish(td, data))
            with self.assertRaisesRegex(ValueError, 'existing output differs'):
                publish(td, dict(data, changed=True))
            (first / 'manifest.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'existing output differs'):
                publish(td, data)

    def test_bundle_import_rejects_tampering_and_preserves_existing_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'repo'
            root.mkdir()
            bundle = Path(td) / 'bundle.zip'
            prefix = 'artifacts/fixture/'
            payload = b'original\n'
            manifest = json.dumps({'outputs': {'data.txt': hashlib.sha256(payload).hexdigest()}}).encode()
            with zipfile.ZipFile(bundle, 'w') as archive:
                archive.writestr(prefix + 'manifest.json', manifest)
                archive.writestr(prefix + 'data.txt', payload)
            cfg = dict(market_root=prefix[:-1], bundle_sha256=sha(bundle),
                       market_manifest_sha256=hashlib.sha256(manifest).hexdigest())
            self.assertEqual(2, import_bundle(root, bundle, cfg))
            self.assertEqual(2, import_bundle(root, bundle, cfg))
            (root / prefix / 'data.txt').write_bytes(b'local evidence')
            with self.assertRaisesRegex(ValueError, 'existing different evidence'):
                import_bundle(root, bundle, cfg)
            self.assertEqual(b'local evidence', (root / prefix / 'data.txt').read_bytes())
            with self.assertRaisesRegex(ValueError, 'bundle checksum mismatch'):
                import_bundle(root, bundle, dict(cfg, bundle_sha256='0'*64))
