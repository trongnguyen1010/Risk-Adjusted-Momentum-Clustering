import contextlib
import io
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from delta_t1.experiments.financial_crawl import USER_VERSION, doctor, prepare, run, verify
from delta_t1.ingestion.cafef_financial import encoded, digest
from delta_t1.ingestion.financial_batch_evidence import Checkpoints
from delta_t1.ingestion.financial_crawl_candidates import candidates, structured_request, summarize
from delta_t1.ingestion.financial_crawl_pdf import extract
from delta_t1.ingestion.sources.base import AccessControlError, RateLimitError


def config(**changes):
    c = dict(version=USER_VERSION, cache_epoch='test-epoch', symbols=['AAA'], years=[2025],
        company_types={'AAA':'Regular'}, periods=['year'], pdf_discovery=False, documents=[],
        pdf_extract=False, budgets={'max_ocr_pages':0})
    c.update(changes)
    return c


def payload(report, quarter=0):
    codes = {'CDKT':{2996:100, 2997:40, 2998:60, 3000:None},
             'KQKD':{2216:100, 2212:20, 2215:5000}, 'LCTT':{2234:25}}
    return dict(Head=[dict(YearPeriod=2025, TermCode='N' if not quarter else 'Q'+str(quarter),
        United='HN', PeriodBegin='202501', PeriodEnd='202512', BusinessType=1),
        dict(YearPeriod=2024, TermCode='N', United='HN')],
        Content={'section':[dict(ReportNormID=k, NameEn='test', Value1=v) for k,v in codes[report].items()]})


class Client:
    def __init__(self, responses=None):
        self.responses, self.calls = responses or {}, []
    def get(self, url):
        self.calls.append(url)
        r = self.responses[url]
        if isinstance(r, Exception):
            raise r
        return r, 200


class CrawlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'configs').mkdir()
        self.path = self.root/'configs/user.json'
        self.path.write_bytes(encoded(config()))
    def execute(self, output, client, resume=(), cfg=None):
        if cfg:
            self.path.write_bytes(encoded(cfg))
        with contextlib.redirect_stdout(io.StringIO()):
            return run(self.root, 'configs/user.json', 'data/'+output, resume_runs=resume, network=True, client=client)
    def client(self):
        return Client({structured_request('AAA',r,'year')['url']:encoded(payload(r)) for r in ['CDKT','KQKD','LCTT']})

    def test_user_entrypoint_no_pilot_dependency_and_replay_latest_is_transitive(self):
        first = self.execute('first', self.client())
        self.assertEqual(first['engineering_status'], 'COMPLETE')
        self.assertEqual(first['summary']['wire_cells'], 8)  # no Value2 manufactured from Head
        self.assertEqual(first['summary']['accounting_qa'][0]['status'], 'CANDIDATE_ARITHMETIC_PASS')
        forbidden = Client()
        self.execute('second', forbidden, ['data/first'])
        third = self.execute('third', forbidden, ['data/second'])
        self.assertEqual(third['metrics']['logical_requests'], 0)
        self.assertEqual(third['metrics']['new_checkpoints'], 0)
        self.assertEqual(forbidden.calls, [])
        for name in ['candidates.jsonl', 'candidates.csv', 'coverage.csv', 'review-queue.json']:
            self.assertEqual((self.root/'data/first'/name).read_bytes(), (self.root/'data/third'/name).read_bytes())
        verify(self.root, 'data/third')
        rows = [json.loads(line) for line in (self.root/'data/first/candidates.jsonl').read_text(encoding='utf8').splitlines()]
        self.assertTrue(all(r['published_at'] is None for r in rows))
        self.assertTrue(any(r['raw_value'] is None for r in rows))
        self.assertFalse(third['financial_features_allowed'])

    def test_offline_without_cache_is_partial_with_explicit_queue(self):
        client = Client()
        with contextlib.redirect_stdout(io.StringIO()):
            r = run(self.root, 'configs/user.json', 'data/offline', client=client)
        self.assertEqual(r['engineering_status'], 'PARTIAL')
        self.assertEqual(r['summary']['wire_cells'], 0)
        self.assertEqual(client.calls, [])
        self.assertTrue(all(x['acquisition']['status']=='DEFERRED_OFFLINE_CACHE_MISS' for x in r['structured']))

    def test_401_403_429_batch_stop_persists_over_multiple_resume_runs(self):
        for exc in [AccessControlError('401'), AccessControlError('403'), RateLimitError('429')]:
            with self.subTest(error=str(exc)):
                tag = str(exc)
                client = Client({structured_request('AAA','CDKT','year')['url']:exc})
                a = self.execute(tag+'a', client)
                self.assertEqual(a['engineering_status'], 'HARD_STOP')
                b = self.execute(tag+'b', client, ['data/'+tag+'a'])
                d = self.execute(tag+'c', client, ['data/'+tag+'b'])
                self.assertEqual(b['engineering_status'], 'HARD_STOP')
                self.assertEqual(d['engineering_status'], 'HARD_STOP')
                self.assertEqual(len(client.calls), 1)

    def test_tampered_dependency_and_candidate_raw_fail_verification(self):
        r = self.execute('base', self.client())
        raw = self.root/r['structured'][0]['acquisition']['payload']['path']
        raw.write_bytes(b'bad')
        client = Client()
        with self.assertRaises(ValueError):
            self.execute('bad', client, ['data/base'])
        self.assertEqual(client.calls, [])
        self.assertFalse((self.root/'data/bad').exists())
        with self.assertRaises(ValueError):
            verify(self.root, 'data/base')

    def test_budget_page2_overlap_keeps_conflicts_no_source_priority(self):
        client = self.client()
        c = config(structured_pages=[1,2], budgets={'max_logical_requests':4,'max_ocr_pages':0})
        p = payload('CDKT')
        p['Content']['section'][0]['Value1'] = 101
        client.responses[structured_request('AAA','CDKT','year',2)['url']] = encoded(p)
        r = self.execute('budget', client, cfg=c)
        self.assertEqual(r['metrics']['logical_requests'], 4)
        self.assertEqual(r['engineering_status'], 'PARTIAL')
        self.assertEqual(len(r['summary']['conflicts']), 1)
        self.assertEqual(len(client.calls), 4)

    def test_invalid_or_empty_json_is_not_success(self):
        for name, body in [('bad', b'<html>error</html>'), ('empty', encoded(dict(Head=[], Content={}))),
                           ('nonfinite', b'{"Head":[],"Content":{},"bad":NaN}')]:
            client = self.client()
            client.responses[structured_request('AAA','CDKT','year')['url']] = body
            r = self.execute(name, client)
            self.assertEqual(r['engineering_status'], 'PARTIAL')
            self.assertNotEqual(r['structured'][0]['status'], 'PARSED_CANDIDATES')

    def test_config_rejects_large_batches_gate_promotion_and_template_without_exact_hash(self):
        for c in [config(financial_features_allowed=True), config(symbols=['AAA']*11),
                  config(company_types={}), config(structured_pages=[4]),
                  config(documents=[dict(symbol='AAA',year=2025,quarter=0,url='https://cafefnew.mediacdn.vn/test.pdf',
                        ocr_pages=[1], cell_templates=[dict(pdf_page=1,year=2025,row_code='100')])])]:
            with self.subTest(config=c), self.assertRaises((ValueError, TypeError)):
                prepare(c)

    def test_scope_and_sector_mapping_and_quarter_coverage_remain_unverified(self):
        request = dict(structured_request('AAA','CDKT','quarter'), path='raw.json', sha256='hash')
        p = payload('CDKT',quarter=2)
        p['Content']['section'].append(dict(ReportNormID=2212, NameEn='profit in wrong report', Value1=99))
        rows = candidates(p, request, [2025], 'Regular')
        self.assertEqual(rows[-1]['status'], 'REPORT_TEMPLATE_REVIEW_REQUIRED')
        bank = candidates(p, request, [2025], 'Bank')
        self.assertTrue(all(r['field'] is None and r['value'] is None for r in bank))
        coverage = summarize(rows, config(periods=['quarter']))['coverage']
        self.assertEqual(len(coverage),12)
        self.assertEqual([x['quarter'] for x in coverage if x['fields_with_candidates']], [2])

    def test_duplicate_period_headers_never_inflate_quarter_coverage(self):
        p=payload('CDKT',quarter=4)
        p['Head'][1]=dict(p['Head'][0], ID=2)
        for row in p['Content']['section']:
            row['Value2']=row['Value1']
        request=dict(structured_request('AAA','CDKT','quarter'),path='raw.json',sha256='hash')
        rows=candidates(p,request,[2025],'Regular')
        self.assertTrue(all(r['value'] is None and not r['in_target'] for r in rows))
        self.assertTrue(all(r['header_status']=='AMBIGUOUS_DUPLICATED_PERIOD_COLUMNS' for r in rows))
        result=summarize(rows,config(periods=['quarter']))
        self.assertTrue(all(not x['fields_with_candidates'] for x in result['coverage']))

    def test_no_cross_response_accounting_bridge_and_conflicting_numbers_fail(self):
        req = dict(structured_request('AAA','CDKT','year'), path='raw.json', sha256='one')
        rows = candidates(payload('CDKT'), req, [2025], 'Regular')
        rows[1]['source_sha256'] = 'two'
        self.assertTrue(all(r['status']=='MISSING_OR_AMBIGUOUS_INPUT' for r in summarize(rows,config())['accounting_qa']))
        rows = candidates(payload('CDKT'), req, [2025], 'Regular')
        rows[0]['value'] = '110000'
        self.assertEqual(summarize(rows,config())['accounting_qa'][0]['status'],'CANDIDATE_ARITHMETIC_CONFLICT')

    def test_ocr_selected_notes_after_prefix_and_partial_budget_remains_retryable(self):
        c = prepare(config(pdf_extract=True, budgets={'max_ocr_pages':0}))
        cp = Checkpoints(self.root,self.root/'data/pdf',c)
        doc = dict(symbol='AAA',year=2025,quarter=0,url='https://cafefnew.mediacdn.vn/test.pdf',ocr_pages=[19])
        doc['acquisition'] = cp.acquire(dict(symbol='AAA',year=2025,quarter=0,url=doc['url'],kind='pdf'),Client({doc['url']:b'%PDF-scan'}),True)
        script = self.root/'ocr.ps1'
        script.write_text('stub')
        fake = types.SimpleNamespace(__version__='test', errors=types.SimpleNamespace(PyPdfError=ValueError),
            PdfReader=lambda p:types.SimpleNamespace(is_encrypted=False, pages=[types.SimpleNamespace(extract_text=lambda:'') for _ in range(20)]))
        with patch.dict('sys.modules', {'pypdf':fake}):
            r = extract(cp,doc,script)
        self.assertEqual(r['status'],'PARTIAL_OCR_DEFERRED')
        self.assertEqual(r['payload']['deferred_ocr_pages'],[19])
        self.assertEqual(len(r['payload']['low_text_pages']),20)
        with patch.dict('sys.modules', {'pypdf':fake}):
            resumed = Checkpoints(self.root,self.root/'data/resume',c,['data/pdf'])
        self.assertEqual(len(resumed.cached),1)  # partial extraction not cached as complete

    def test_ocr_page_outside_pdf_and_wrong_document_hash_are_errors(self):
        c = prepare(config())
        cp = Checkpoints(self.root,self.root/'data/pdf',c)
        doc = dict(symbol='AAA',year=2025,quarter=0,url='https://cafefnew.mediacdn.vn/test.pdf',ocr_pages=[19])
        doc['acquisition'] = cp.acquire(dict(symbol='AAA',year=2025,quarter=0,url=doc['url'],kind='pdf'),Client({doc['url']:b'%PDF-scan'}),True)
        script=self.root/'ocr.ps1';script.write_text('stub')
        fake=types.SimpleNamespace(__version__='test',errors=types.SimpleNamespace(PyPdfError=ValueError),
            PdfReader=lambda p:types.SimpleNamespace(is_encrypted=False,pages=[types.SimpleNamespace(extract_text=lambda:'')]))
        with patch.dict('sys.modules', {'pypdf':fake}):
            r=extract(cp,doc,script)
        self.assertEqual(r['status'],'FAILED_PDF_EXTRACTION')
        self.assertIn('exceeds actual PDF',r['error'])

    def test_discovery_preserves_all_vintages_and_pdf_404_is_partial(self):
        c=config(pdf_discovery=True)
        client=self.client()
        listing='https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol=aaa&Type=1&Year=2025'
        client.responses[listing]=encoded(dict(Success=True,Data=[
            dict(Year=2025,Quarter=5,id=str(i),Name='Báo cáo hợp nhất',Link=f'https://cafefnew.mediacdn.vn/{i}.pdf') for i in [1,2]]))
        client.responses['https://cafefnew.mediacdn.vn/1.pdf']=b'%PDF-first'
        client.responses['https://cafefnew.mediacdn.vn/2.pdf']=ValueError('HTTP 404')
        r=self.execute('discovery',client,cfg=c)
        self.assertEqual(r['engineering_status'],'PARTIAL')
        self.assertEqual(len(r['documents']),2)
        self.assertEqual({x['provider_report_id'] for x in r['documents']},{'1','2'})
        queue=json.loads((self.root/'data/discovery/review-queue.json').read_bytes())
        self.assertTrue(any(x.get('acquisition_error')=='HTTP 404' for x in queue))

    def test_selected_ocr_cells_match_reference_and_no_acceptance_is_granted(self):
        c=prepare(config(budgets={'max_ocr_pages':1}))
        cp=Checkpoints(self.root,self.root/'data/pdf',c)
        doc=dict(symbol='AAA',year=2025,quarter=0,url='https://cafefnew.mediacdn.vn/test.pdf',ocr_pages=[2],
                 cell_templates=[dict(pdf_page=2,year=2025,field='test',box=[0,0,1,1],unit='VND',reference_value=1234)])
        doc['acquisition']=cp.acquire(dict(symbol='AAA',year=2025,quarter=0,url=doc['url'],kind='pdf'),Client({doc['url']:b'%PDF-scan'}),True)
        script=self.root/'ocr.ps1';script.write_text('stub')
        renderer=self.root/'renderer.exe';renderer.write_bytes(b'renderer test')
        fake=types.SimpleNamespace(__version__='test',errors=types.SimpleNamespace(PyPdfError=ValueError),
            PdfReader=lambda p:types.SimpleNamespace(is_encrypted=False,pages=[types.SimpleNamespace(extract_text=lambda:'') for _ in range(2)]))
        def command(args,**kwargs):
            if args[0]==str(renderer):
                Path(args[-1]+'-2.png').write_bytes(b'test image')
            else:
                folder=Path(args[-1]);image=next(folder.glob('*.png'))
                image.with_suffix('.ocr.json').write_bytes(encoded(dict(width=100,height=100,
                    image_sha256=digest(image.read_bytes()),lines=[dict(words=[dict(text='1.234',x=10,y=10,width=20,height=5)])])))
        with patch.dict('sys.modules',{'pypdf':fake}), patch('delta_t1.ingestion.financial_crawl_pdf.shutil.which',return_value=str(renderer)):
            r=extract(cp,doc,script,command=command)
        self.assertEqual(r['status'],'COMPLETE')
        self.assertEqual(r['payload']['ocr_pages'][0]['pdf_page'],2)
        cell=r['payload']['cell_candidates'][0]
        self.assertTrue(cell['reference_qa']['passed'])
        self.assertFalse(cell['candidate']['financial_features_allowed'])


if __name__ == '__main__':
    unittest.main()
