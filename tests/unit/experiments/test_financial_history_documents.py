import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from delta_t1.experiments.financial_history_documents import DocumentTransport, acquire, put, read, report
from delta_t1.ingestion.financial_compact_trial import read_compact


class DocumentSupplementTests(unittest.TestCase):
    def config(self):
        return dict(cache_epoch='test',approved_hosts=['issuer.example'], jobs=[dict(id='test', url='https://issuer.example/report.pdf',symbol='GMD',year=2015)],
            budgets=dict(max_logical_requests=5,max_transport_attempts=6,max_pdf_download_attempts=2,
                         max_response_bytes=1000,max_total_downloaded_bytes=10000,max_wall_seconds=1000,
                         max_attempts_per_request=2,timeout_seconds=25,min_seconds_between_transport_attempts=2))

    def seed(self):
        return dict(created_at=1,logical_requests=3,transport_attempts=3,pdf_download_attempts=0,
                    downloaded_bytes=300,reserved_bytes=0,text_pages=0,reserved_text_pages=0,
                    requests={str(i):dict(url='https://old.example/'+str(i),attempts=1) for i in range(3)},
                    boundary=False,budget_stop=False,stop_reason=None)

    def test_parent_counters_and_deadline_survive_document_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=self.config();seed=self.seed()
            a=DocumentTransport(root,root/'network',config,seed,utc=lambda:10)
            self.assertEqual(a.state['logical_requests'],3)
            a.state['downloaded_bytes']+=7;a.event('TEST_CHECKPOINT')
            b=DocumentTransport(root,root/'network',config,seed,utc=lambda:20)
            self.assertEqual(b.state['created_at'],1)
            self.assertEqual(b.state['downloaded_bytes'],307)
            self.assertEqual(read_compact(root/'network')['state']['transport_attempts'],3)

    def test_imported_source_boundary_prevents_transport_construction(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch('delta_t1.experiments.financial_history_documents.DocumentTransport',side_effect=AssertionError('network')):
                acquire(root,self.config(),root,dict(boundaries=dict(blocked_hosts=['issuer.example'])))
            self.assertEqual(read(root/'receipts/test.json')['status'],'IMPORTED_SOURCE_BOUNDARY')

    def test_terminal_failed_receipt_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);put(root/'receipts/test.json',dict(status='FAILED_OR_STOPPED'))
            with patch('delta_t1.experiments.financial_history_documents.DocumentTransport',side_effect=AssertionError('network')):
                acquire(root,self.config(),root,dict(boundaries=dict(blocked_hosts=[])))

    def test_torn_journal_does_not_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=DocumentTransport(root,root/'network',self.config(),self.seed(),utc=lambda:10)
            with (root/'network/transport.jsonl').open('ab') as stream:stream.write(b'{')
            with self.assertRaisesRegex(ValueError,'torn journal'):
                DocumentTransport(root,root/'network',self.config(),self.seed(),utc=lambda:20)

    def test_modified_acquired_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);put(root/'raw.pdf',b'%PDF-changed')
            put(root/'receipts/test.json',dict(status='ACQUIRED',path='raw.pdf',sha256='0'*64))
            with self.assertRaisesRegex(ValueError,'PDF hash mismatch'):
                report(root,self.config(),root,'verify')

    def test_real_get_path_uses_epoch_and_increments_inherited_counters(self):
        class Response:
            status=200
            def __init__(self):self.body=b'%PDF-test'
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,count):body,self.body=self.body[:count],self.body[count:];return body
        class Opener:
            def open(self,*args,**kwargs):return Response()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);t=DocumentTransport(root,root/'network',self.config(),self.seed(),utc=lambda:10,sleep=lambda _:None,opener=Opener())
            t.context=dict(kind='pdf')
            body,status=t.get('https://issuer.example/report.pdf')
            self.assertEqual(body,b'%PDF-test');self.assertEqual(status,200)
            self.assertEqual(t.state['logical_requests'],4)
            self.assertEqual(t.state['transport_attempts'],4)
            self.assertEqual(t.state['pdf_download_attempts'],1)
