import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from delta_t1.experiments.financial_batch_flow import run, verify_flow
from delta_t1.ingestion.cafef_financial import encoded
from delta_t1.ingestion.financial_documents import verify_inventory
from unit.ingestion.test_financial_batch_evidence import config, Client


class BatchFlowTests(unittest.TestCase):
    def test_stop_resume_real_task_boundary_and_fail_closed_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'scripts').mkdir(); (root/'scripts/ocr_financial_pages.ps1').write_text('stub')
            (root/'src/delta_t1/ingestion').mkdir(parents=True)
            (root/'src/delta_t1/ingestion/financial_batch_evidence.py').write_text('snapshot stub')
            doc=dict(symbol='AAA', year=2025, quarter=0,url='https://cafefnew.mediacdn.vn/a.pdf')
            (root/'config.json').write_bytes(encoded(config(documents=[doc])))
            a=run(root,'config.json','data/a',network=True,stop_after='acquire',client=Client({doc['url']:b'%PDF'}))
            self.assertEqual(a['engineering_status'], 'STOPPED_AFTER_ACQUIRE')
            fake=dict(status='COMPLETE',payload=dict(pages=[],ocr_pages=[],total_pdf_pages=0))
            with patch('delta_t1.experiments.financial_batch_flow.extract_pdf',return_value=fake):
                b=run(root,'config.json','data/b',resume_runs=['data/a'],network=True,client=Client({}))
            self.assertEqual(b['engineering_status'], 'COMPLETE')
            self.assertEqual(b['metrics']['logical_requests'], 0)
            self.assertFalse(b['financial_features_allowed'])
            self.assertEqual(b['financial_cluster_eligible_rows'], 0)
            self.assertEqual(b['acceptance_status'], 'PARTIAL_REFERENCE_ONLY')
            self.assertTrue(b['review_queue_items'] > 0)
            verify_inventory(root/'data/a'); verify_inventory(root/'data/b')
            self.assertEqual(verify_flow(root,'data/b')['status'],'PASS')
            # B has no acquisition task of its own: newest-run-only resume must follow B -> A.
            with patch('delta_t1.experiments.financial_batch_flow.extract_pdf',return_value=fake):
                newest=run(root,'config.json','data/c',resume_runs=['data/b'],network=True,client=Client({}))
            self.assertEqual(newest['metrics']['logical_requests'],0)
            self.assertEqual(newest['engineering_status'],'COMPLETE')
            for line in (root/'data/b/work-log.jsonl').read_text().splitlines(): json.loads(line)
            with self.assertRaises(ValueError): run(root,'config.json','data/b')
            # The outer B manifest stays valid, but its reused raw in A has changed.
            (root/b['documents'][0]['acquisition']['payload']['path']).write_bytes(b'corrupt external raw')
            verify_inventory(root/'data/b')
            with self.assertRaises(ValueError): verify_flow(root,'data/b')

    def test_code_or_source_drift_rejected_before_output_or_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'source').write_text('changed')
            (root/'c.json').write_bytes(encoded(config(code_sha256={'source':'0'*64})))
            with self.assertRaises(ValueError): run(root,'c.json','data/new',network=True,client=Client({}))
            self.assertFalse((root/'data/new').exists())

    def test_empty_offline_batch_cannot_claim_engineering_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'src/delta_t1/ingestion').mkdir(parents=True)
            (root/'src/delta_t1/ingestion/financial_batch_evidence.py').write_text('snapshot')
            (root/'c.json').write_bytes(encoded(config(discovery=[dict(symbol='AAA',year=2025)])))
            r=run(root,'c.json','data/new')
            self.assertEqual(r['engineering_status'], 'PARTIAL')
            self.assertEqual(r['metrics']['logical_requests'],0)


if __name__=='__main__': unittest.main()
