import io
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from delta_t1.experiments import financial_pdf_pipeline as flow


class StubTransport:
    def __init__(self, body=b'%PDF-1.7'):
        self.state = dict(requests={})
        self.b = dict(max_response_bytes=25_000_000, timeout_seconds=25)
        self.calls = 0
        self.body = body
    def get(self, url):
        self.calls += 1
        return self.body, 200


class PipelineTests(unittest.TestCase):
    def test_source_boundary_unapproved_host_and_prior_request_never_call_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); out = root/'run'; out.mkdir()
            transport = StubTransport(); c = dict(approved_hosts=['allowed.org'])
            contract = dict(blocked_hosts=['blocked.org'])
            for host in ['blocked.org', 'unapproved.org']:
                result = flow.request(root, out, c, contract, transport, 'https://'+host+'/a.pdf', 'pdf', 'AAA', 2018)
                self.assertNotEqual(result['status'], 'ACQUIRED')
            transport.state['requests']['previous'] = dict(url='https://allowed.org/a.pdf')
            result = flow.request(root, out, c, contract, transport, 'https://allowed.org/a.pdf', 'pdf', 'AAA', 2018)
            self.assertEqual(result['status'], 'PRIOR_REQUEST_WITHOUT_PIPELINE_RECEIPT_REVIEW_REQUIRED')
            self.assertEqual(transport.calls, 0)

    def test_failed_mime_is_terminal_and_never_retried_on_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); out = root/'run'; out.mkdir()
            t = StubTransport(b'<html>not PDF</html>')
            c, contract = dict(approved_hosts=['x.org']), dict(blocked_hosts=[])
            args = root, out, c, contract, t, 'https://x.org/a.pdf', 'pdf', 'AAA', 2018
            self.assertEqual(flow.request(*args)['status'], 'FAILED_OR_STOPPED')
            self.assertEqual(flow.request(*args)['status'], 'FAILED_OR_STOPPED')
            self.assertEqual(t.calls, 1)
            self.assertEqual(t.b['max_response_bytes'], 25_000_000)

    def test_changed_cached_bytes_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); out = root/'run'; out.mkdir()
            t = StubTransport(); c, contract = dict(approved_hosts=['x.org']), dict(blocked_hosts=[])
            args = root, out, c, contract, t, 'https://x.org/a.pdf', 'pdf', 'AAA', 2018
            r = flow.request(*args)
            (root/r['path']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'cache changed'):
                flow.request(*args)
            self.assertEqual(t.calls, 1)

    def test_new_batch_deadline_does_not_reset_campaign_anchor(self):
        t = object.__new__(flow.PipelineTransport)
        t.state = dict(created_at=100)
        t.b = dict(max_wall_seconds=90*86400)
        t.utc = lambda: 1000
        t.batch_deadline, t.campaign_deadline = 1200, 1500
        self.assertEqual(t.remaining_seconds(), 200)
        t.batch_deadline = 2000
        self.assertEqual(t.remaining_seconds(), 500)
        t.utc = lambda: 1501
        self.assertEqual(t.remaining_seconds(), 0)

    def test_anonymous_pdf_resolved_by_source_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root/'task'; p.mkdir()
            body = b'%PDF-1.7'; (p/'raw.pdf').write_bytes(body)
            (p/'result.json').write_bytes(flow.encoded(dict(request=dict(url='https://x.org/doc.pdf'), payload=dict(path='task/raw.pdf', sha256=flow.digest(body)))))
            (root/'inventory.csv').write_text('path,sha256\ntask/raw.pdf,'+flow.digest(body)+'\n')
            result = flow.index_cache(root, 'inventory.csv')
            self.assertEqual(result['unknown_metadata'], [])
            self.assertEqual(result['by_url']['https://x.org/doc.pdf'][0]['path'], 'task/raw.pdf')

    def test_real_text_worker_and_resume_on_ten_targets(self):
        from pypdf import PdfWriter
        writer = PdfWriter(); writer.add_blank_page(width=400, height=400)
        stream = io.BytesIO(); writer.write(stream); pdf = stream.getvalue()
        html = b'<a href="report.pdf">BCTC hop nhat 2018</a>'
        calls = []
        class Response(io.BytesIO):
            status = 200
            def read1(self, count): return self.read(count)
        class Opener:
            def open(self, request, timeout):
                calls.append(request.full_url)
                return Response(pdf if request.full_url.endswith('.pdf') else html)
        class Transport(flow.PipelineTransport):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs, opener=Opener(), sleep=lambda n: None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); out = root/'run'; out.mkdir()
            (root/'scripts').mkdir()
            shutil.copyfile(Path(__file__).resolve().parents[3]/'scripts/financial_pdf_pipeline.py', root/'scripts/financial_pdf_pipeline.py')
            flow.put(out/'contract.json', {})
            (root/'inventory.csv').write_text('path,sha256\n')
            now = time.time()
            c = dict(targets=[dict(symbol='A'+str(i), year=2018, catalogues=['https://x.org/list'] if i==0 else [], source_scope_filter='CONSOLIDATED') for i in range(10)],
                pdf_inventory='inventory.csv', approved_hosts=['x.org'], batch_deadline=now+1000, campaign_deadline=now+2000,
                max_text_pages_per_pdf=160, max_text_pages_batch=1600, cache_epoch='test',
                budgets=dict(max_wall_seconds=86400, max_logical_requests=10, max_transport_attempts=20, max_pdf_download_attempts=20, max_response_bytes=25_000_000, max_total_downloaded_bytes=100_000_000, max_attempts_per_request=2, timeout_seconds=25, min_seconds_between_transport_attempts=2))
            seed = dict(created_at=now, logical_requests=0, transport_attempts=0, downloaded_bytes=0, reserved_bytes=0, pdf_download_attempts=0, text_pages=0, reserved_text_pages=0, requests={}, cache={}, boundary=False, budget_stop=False, stop_reason=None)
            contract = dict(seed=seed, blocked_hosts=[])
            with patch.object(flow, 'PipelineTransport', Transport):
                flow.execute(root, c, out, contract, True)
                first = flow.snapshot(root, c, out)['summary']
                self.assertEqual(first['terminal_task_states'], 10)
                self.assertEqual(first['pdfs_acquired'], 1)
                self.assertEqual(first['new_feature_rows'], 0)
                self.assertTrue((out/'ocr-review/A0-2018.json').exists())
                flow.execute(root, c, out, contract, True)
            self.assertEqual(len(calls), 2)
            flow.snapshot(root, c, out)
            self.assertEqual(flow.snapshot(root, c, out, True)['summary'], first)

    def test_403_latches_and_never_retries(self):
        class Opener:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                raise HTTPError(request.full_url, 403, 'Forbidden', {}, None)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); opener=Opener(); now=time.time()
            c=dict(approved_hosts=['x.org'],cache_epoch='test',budgets=dict(max_wall_seconds=86400,max_logical_requests=4,max_transport_attempts=8,max_pdf_download_attempts=8,max_response_bytes=100000,max_total_downloaded_bytes=1000000,max_attempts_per_request=2,timeout_seconds=25,min_seconds_between_transport_attempts=2))
            seed=dict(created_at=now,logical_requests=0,transport_attempts=0,downloaded_bytes=0,reserved_bytes=0,pdf_download_attempts=0,text_pages=0,reserved_text_pages=0,requests={},cache={},boundary=False,budget_stop=False,stop_reason=None)
            t=flow.PipelineTransport(root,root/'network',c,seed,batch_deadline=now+1000,campaign_deadline=now+2000,opener=opener,sleep=lambda n:None)
            t.context=dict(kind='pdf')
            with self.assertRaises(Exception): t.get('https://x.org/a.pdf')
            with self.assertRaises(Exception): t.get('https://x.org/b.pdf')
            self.assertTrue(t.state['boundary'])
            self.assertEqual(opener.calls,1)
