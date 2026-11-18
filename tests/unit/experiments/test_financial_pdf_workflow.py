import json
import tempfile
import unittest
from pathlib import Path
from delta_t1.experiments.financial_pdf_workflow import checked_result,status
from delta_t1.ingestion.cafef_financial import encoded,digest


class WorkflowTests(unittest.TestCase):
    def test_status_counts_reviewed_cases_instead_of_terminal_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def put(path,body):
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body);return digest(body)
            def js(path,v):return put(path,encoded(v))
            targets=[dict(registry_id='R'+str(i),symbol='A'+str(i),year=2018) for i in range(10)]
            js('acq.json',dict(output_root='acq',targets=targets))
            for t in targets:js('acq/targets/'+t['symbol']+'.json',dict(target=t,status='SEMANTIC_REVIEW_REQUIRED'))
            manifest={'summary.json':js('dataset/summary.json',dict(rows_after=11840,full10_after=464,new_rows=1)),
                      'recovered-rows.csv':put('dataset/recovered-rows.csv',b'registry_id,year\nR0,2018\n')}
            sha=js('dataset/manifest.json',manifest);js('ref.json',dict(path='dataset',manifest_sha256=sha))
            result=status(root,dict(acquisition_config='acq.json',dataset_result_ref='ref.json'))
            self.assertEqual(result['targets_visited'],10)
            self.assertEqual(result['reference_progress_percent'],10.0)
            self.assertEqual(result['current_full10'],464)
            self.assertFalse(result['next50_allowed'])
            self.assertFalse(result['strict_pit_ready'])

    def test_modified_dataset_fails_even_with_unchanged_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();(root/'data/summary.json').write_bytes(b'{}')
            raw=encoded({'summary.json':digest(b'{}')});(root/'data/manifest.json').write_bytes(raw)
            ref=dict(path='data',manifest_sha256=digest(raw));checked_result(root,ref)
            (root/'data/summary.json').write_bytes(b'{"changed":true}')
            with self.assertRaisesRegex(ValueError,'dataset file changed'):checked_result(root,ref)
