from pathlib import Path
import tempfile
import unittest

from delta_t1.ingestion.corporate_actions.layout import inside, make_plan


class LayoutTests(unittest.TestCase):
    def fixture(self, root):
        for name in ['scripts', 'src/delta_t1/ingestion', 'configs/data', 'src/delta_t1/schemas', 'tests/unit/ingestion', 'tmp']:
            (root / name).mkdir(parents=True, exist_ok=True)
        (root / 'scripts/collect_corporate_actions_v1.py').write_text('preserved bytes', encoding='utf-8')
        (root / 'scripts/run_m2_global_k.py').write_text('outside scope', encoding='utf-8')
        (root / 'tmp/ca_saved_artifact').mkdir()
        (root / 'tmp/ca_saved_artifact/manifest.json').write_text('{}', encoding='utf-8')

    def test_existing_artifacts_are_exposed_by_new_alias_not_relocated(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd() / 'tmp') as tmp:
            root = Path(tmp); self.fixture(root)
            plan = make_plan(root)
            self.assertEqual(2, len(plan['entries']))
            artifact = next(e for e in plan['entries'] if e['old'].startswith('tmp/'))
            self.assertEqual('NEW_DIRECTORY_JUNCTION', artifact['kind'])
            self.assertEqual('data/corporate_actions/work/legacy_tmp/ca_saved_artifact', artifact['new'])
            self.assertTrue((root / artifact['old']).is_dir())
            self.assertFalse((root / artifact['new']).exists())

    def test_code_preservation_includes_hash_and_excludes_m2(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd() / 'tmp') as tmp:
            root = Path(tmp); self.fixture(root)
            files = [e for e in make_plan(root)['entries'] if e['kind'] == 'MOVE_FILE_KEEP_HARDLINK']
            self.assertEqual(['scripts/collect_corporate_actions_v1.py'], [e['old'] for e in files])
            self.assertEqual(64, len(files[0]['sha256']))

    def test_existing_target_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd() / 'tmp') as tmp:
            root = Path(tmp); self.fixture(root)
            target = root / 'scripts/corporate_actions/legacy_sources/collect_corporate_actions_v1.py'
            target.parent.mkdir(parents=True); target.write_text('existing')
            with self.assertRaises(FileExistsError): make_plan(root)

    def test_path_traversal_and_absolute_paths_are_rejected(self):
        for name in ['../outside', 'C:/outside', '/outside', 'a/../../outside']:
            with self.assertRaises(ValueError): inside(Path.cwd(), name)


if __name__ == '__main__': unittest.main()
