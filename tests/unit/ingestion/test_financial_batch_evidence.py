import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_batch_evidence import (
    VERSION, GATES, Checkpoints, collect, extract_pdf, seal, validate,
)
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.sources.base import AccessControlError, RateLimitError


def config(**changes):
    c = dict(version=VERSION, symbols=['AAA', 'BBB'], years=[2025], cache_epoch='test-frozen',
        approved_hosts=['cafef.vn', 'cafefnew.mediacdn.vn'], max_logical_requests=4,
        max_pdf_downloads=2, max_documents=4, max_bytes=10000, max_total_bytes=20000,
        max_pdf_pages=20, max_text_pages=40, max_ocr_pages=0, ocr_first_pages=0, max_seconds=60,
        discovery=[], documents=[], cache_records=[], **GATES)
    c.update(changes)
    return c


class Client:
    def __init__(self, responses): self.responses, self.calls = responses, []
    def get(self, url):
        self.calls.append(url)
        r = self.responses[url]
        if isinstance(r, Exception): raise r
        return r, 200


class BatchEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.doc = dict(symbol='AAA', year=2025, quarter=0, url='https://cafefnew.mediacdn.vn/aaa.pdf')
        self.request = dict(self.doc, kind='pdf')
    def cp(self, name='first', c=None, resume=()):
        return Checkpoints(self.root, self.root/'data'/name, c or config(), resume)

    def test_interrupted_parent_reuses_only_sealed_success_and_zero_network(self):
        cp = self.cp()
        cli = Client({self.doc['url']:b'%PDF-source'})
        first = cp.acquire(self.request, cli, True)
        (self.root/'data/first/tasks/unsealed').mkdir(parents=True)
        (self.root/'data/first/tasks/unsealed/result.json').write_text('bad unfinished bytes')
        resumed = self.cp('second', resume=['data/first'])
        forbidden = Client({})
        second = resumed.acquire(self.request, forbidden, True)
        self.assertEqual(first['payload']['sha256'], second['payload']['sha256'])
        self.assertTrue(second['reused'])
        self.assertEqual(forbidden.calls, [])
        self.assertEqual(resumed.metrics['logical_requests'], 0)

    def test_corrupt_sealed_checkpoint_fails_before_transport(self):
        cp = self.cp(); r=cp.acquire(self.request, Client({self.doc['url']:b'%PDF'}), True)
        (self.root/r['payload']['path']).write_bytes(b'corrupt')
        with self.assertRaises(ValueError): self.cp('resume', resume=['data/first'])

    def test_403_429_stops_entire_batch_and_resume_does_not_retry_boundary(self):
        for exc in [AccessControlError('403'), RateLimitError('429')]:
            with self.subTest(exc=type(exc).__name__):
                name = type(exc).__name__
                cp=self.cp(name)
                cli=Client({self.doc['url']:exc})
                a=cp.acquire(self.request, cli, True)
                other=dict(self.request, url='https://cafefnew.mediacdn.vn/other.pdf')
                b=cp.acquire(other, cli, True)
                self.assertEqual(a['status'], 'HARD_STOP')
                self.assertEqual(b['status'], 'DEFERRED_BOUNDARY_REVIEW')
                retry=self.cp(name+'resume', resume=['data/'+name])
                self.assertEqual(retry.acquire(self.request, cli, True)['status'], 'DEFERRED_BOUNDARY_REVIEW')
                third=self.cp(name+'third',resume=['data/'+name+'resume'])
                self.assertEqual(third.acquire(self.request,cli,True)['status'],'DEFERRED_BOUNDARY_REVIEW')
                self.assertEqual(len(cli.calls), 1)

    def test_budget_and_offline_misses_are_explicit_without_calls(self):
        cli=Client({})
        self.assertEqual(self.cp('offline').acquire(self.request, cli, False)['status'], 'DEFERRED_OFFLINE_CACHE_MISS')
        self.assertEqual(self.cp('cap', config(max_pdf_downloads=0)).acquire(self.request, cli, True)['status'], 'DEFERRED_BUDGET')
        self.assertEqual(cli.calls, [])

    def test_all_annual_vintages_preserved_no_silent_latest_selection(self):
        url='https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol=aaa&Type=1&Year=2025'
        body=encoded(dict(Success=True, Data=[dict(Year=2025, Quarter=5, id=str(i), Name='Báo cáo hợp nhất',
                      Link=f'https://cafefnew.mediacdn.vn/{i}.pdf') for i in [1,2]]))
        cli=Client({url:body, 'https://cafefnew.mediacdn.vn/1.pdf':b'%PDF1', 'https://cafefnew.mediacdn.vn/2.pdf':b'%PDF2'})
        cp=self.cp(c=config(discovery=[dict(symbol='AAA', year=2025)]))
        r=collect(cp, True, cli)
        self.assertEqual(len(r['documents']), 2)
        self.assertEqual({d['provider_report_id'] for d in r['documents']}, {'1','2'})
        self.assertTrue(all(d['publication_date'] is None and d['actual_document_identity']=='UNVERIFIED' for d in r['documents']))

    def test_false_envelope_wrong_pdf_and_unapproved_host_are_not_success(self):
        cp=self.cp(); cli=Client({self.doc['url']:b'login HTML'})
        self.assertEqual(cp.acquire(self.request, cli, True)['status'], 'FAILED')
        with self.assertRaises(ValueError): cp.acquire(dict(self.request, url='https://evil.test/a.pdf'), cli, True)
        self.assertEqual(len(cli.calls), 1)

    def test_seed_requires_manifest_file_and_exact_url_association(self):
        seed=self.root/'data/seed'; seed.mkdir(parents=True)
        pdf=seed/'raw.pdf'; pdf.write_bytes(b'%PDFcached')
        immutable_write(seed/'inventory.json', encoded(dict(requests=[dict(url=self.doc['url'], sha256=digest(pdf.read_bytes()))])))
        seal(seed)
        entry=dict(url=self.doc['url'], kind='pdf', run='data/seed', path='data/seed/raw.pdf',
                   sha256=digest(pdf.read_bytes()), manifest_sha256=digest((seed/'manifest.json').read_bytes()))
        cp=self.cp(c=config(cache_records=[entry]))
        r=cp.acquire(self.request, Client({}), False)
        self.assertEqual(r['status'], 'COMPLETE')
        self.assertEqual(r['payload']['origin'], 'PINNED_EXISTING_RAW')
        with self.assertRaises(ValueError): self.cp('bad', config(cache_records=[dict(entry,url='https://cafefnew.mediacdn.vn/wrong.pdf')]))

    def test_cache_epoch_refresh_does_not_reuse_old_listing(self):
        cp=self.cp(); cp.acquire(self.request, Client({self.doc['url']:b'%PDFold'}), True)
        newer=self.cp('new', config(cache_epoch='new-epoch'), ['data/first'])
        self.assertEqual(newer.acquire(self.request, Client({}), False)['status'], 'DEFERRED_OFFLINE_CACHE_MISS')

    def test_scan_ocr_page_budget_missing_is_not_zero_and_not_cached_as_complete(self):
        cp=self.cp(c=config(ocr_first_pages=2, max_ocr_pages=0))
        a=cp.acquire(self.request, Client({self.doc['url']:b'%PDF-scan'}), True)
        script=self.root/'ocr.ps1'; script.write_text('test stub')
        fake=types.SimpleNamespace(__version__='test', PdfReader=lambda p:types.SimpleNamespace(is_encrypted=False,
              pages=[types.SimpleNamespace(extract_text=lambda:'') for _ in range(2)]))
        with patch.dict(sys.modules, {'pypdf':fake}):
            r=extract_pdf(cp, dict(self.doc,acquisition=a), script)
        self.assertEqual(r['status'], 'PARTIAL_OCR_BUDGET')
        self.assertEqual(r['payload']['deferred_ocr_pages'], [1,2])
        self.assertEqual([p['text_characters'] for p in r['payload']['pages']], [0,0])
        self.assertTrue(all(p['low_text'] for p in r['payload']['pages']))
        verify_inventory(self.root/r['checkpoint_path'])
        resume=self.cp('resume', cp.c, ['data/first'])
        self.assertEqual(len(resume.cached), 1)  # raw only, partial OCR will be retried

    def test_contract_rejects_promotion_and_large_batches(self):
        for changes in [dict(financial_features_allowed=True), dict(max_logical_requests=61), dict(max_ocr_pages=49), dict(symbols=['AAA']*2)]:
            with self.assertRaises(ValueError): validate(config(**changes))


if __name__=='__main__': unittest.main()
