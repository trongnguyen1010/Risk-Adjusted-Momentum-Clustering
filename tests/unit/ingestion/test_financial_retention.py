import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from delta_t1.ingestion.financial_retention import archive_root,checked_member,financial_refs,inventory,restore,safe_root,verify_archive,verify_before_prune


class RetentionTests(unittest.TestCase):
    def test_offline_integration_and_its_parent_stay_active(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'configs/data').mkdir(parents=True)
            (root/'configs/data/financial_execution_plan_v9.json').write_text('{}')
            (root/'configs/data/financial_active_integration_v1.json').write_text(
                json.dumps(dict(run='data/financial/integration_v1/results.json')))
            for name in ['integration_v1','candidate_parent']:
                (root/'data/financial'/name).mkdir(parents=True)
            (root/'data/financial/integration_v1/results.json').write_text(
                json.dumps(dict(trial='data/financial/candidate_parent')))
            result=inventory(root)
            self.assertTrue(all(r['action']=='KEEP_ACTIVE_DEPENDENCY' for r in result['items']))

    def test_windows_escaped_dependency_paths_are_detected(self):
        text=json.dumps({'a':r'C:\Projects\Intern\SourceCode-CafeF\data\financial\fpt_interim_ocr_v1\index.json','b':'data/financial/other_v1/facts.json'})
        self.assertEqual(financial_refs(text),{'fpt_interim_ocr_v1','other_v1'})

    def test_outside_and_traversal_targets_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ['..','../market','C:\\outside','x/y','x:y']:
                with self.assertRaises(ValueError):safe_root(root,name)
            for name in ['../x','/x','a/../x','C:/x','a\\x']:
                with self.assertRaises(ValueError):checked_member(name)

    def test_active_closure_preserves_windows_dependencies_and_closed_archive_pointer(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'configs/data').mkdir(parents=True)
            (root/'configs/data/financial_execution_plan_v9.json').write_text(json.dumps(dict(latest='data/financial/active_v1/results.json')))
            for name in ['active_v1','evidence_v1','trial-epochs','old_v1']:
                (root/'data/financial'/name).mkdir(parents=True)
            (root/'data/financial/active_v1/results.json').write_text(json.dumps(dict(source=r'data\financial\evidence_v1\facts.json')))
            (root/'data/financial/trial-epochs/closed.json').write_text(json.dumps(dict(run='data/financial/crawl_50_live_20261007_v1/results.json')))
            result=inventory(root)
            actions={r['name']:r['action'] for r in result['items']}
            self.assertEqual(actions['active_v1'],'KEEP_ACTIVE_DEPENDENCY')
            self.assertEqual(actions['evidence_v1'],'KEEP_ACTIVE_DEPENDENCY')
            self.assertEqual(actions['trial-epochs'],'KEEP_ACTIVE_DEPENDENCY')
            self.assertEqual(actions['old_v1'],'ARCHIVE_INACTIVE')

    def test_archive_checksum_source_change_and_restore_are_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'data/financial/example_v1';source.mkdir(parents=True)
            original=b'original bytes\r\n';(source/'evidence.json').write_bytes(original)
            destination=root/'artifacts/archives/test'
            record=archive_root(root,'example_v1',destination)
            self.assertTrue(record['verified'])
            self.assertEqual(verify_before_prune(root,record)['status'],'PRUNE_READY')
            (source/'evidence.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'source changed'):verify_before_prune(root,record)
            # A test-created leaf is removed, never recursively deleting computed paths.
            (source/'evidence.json').unlink();source.rmdir()
            restored=restore(root,destination/'example_v1.zip')
            self.assertEqual(restored['files'],1)
            self.assertEqual((source/'evidence.json').read_bytes(),original)
            with self.assertRaises(FileExistsError):restore(root,destination/'example_v1.zip')

    def test_archive_extra_member_and_tampered_pin_stop_pruning(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'data/financial/example_v1';source.mkdir(parents=True)
            (source/'manifest.json').write_text('{}')
            record=archive_root(root,'example_v1',root/'artifacts/archives/test')
            archive=root/record['archive']
            with zipfile.ZipFile(archive,'a') as pack:pack.writestr('files/../unsafe',b'x')
            with self.assertRaisesRegex(ValueError,'pin changed'):restore(root,archive,record['archive_sha256'])
            with self.assertRaisesRegex(ValueError,'inventory'):verify_archive(archive)
            with self.assertRaisesRegex(ValueError,'pin changed'):verify_before_prune(root,record)
