import contextlib
import io
import json
import tempfile
import subprocess
import types
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from delta_t1.experiments.financial_crawl_trial import CAPS, prepare, run, verify, feedback, document_sample
from delta_t1.ingestion.cafef_financial import encoded, digest
from delta_t1.ingestion.financial_batch_evidence import Checkpoints, seal
from delta_t1.ingestion.financial_crawl_pdf import extract
from delta_t1.ingestion.financial_trial_transport import TrialTransport, TrialBudgetError, read_ledger
from delta_t1.ingestion.sources.base import AccessControlError, RateLimitError


class Response(io.BytesIO):
    status=200


class Opener:
    def __init__(self, handler=None):
        self.calls=[]
        self.handler=handler or self.provider
    def open(self,request,timeout):
        self.calls.append(request.full_url)
        result=self.handler(request.full_url,len(self.calls))
        if isinstance(result,BaseException):
            raise result
        return Response(result)
    @staticmethod
    def provider(url,number):
        q=parse_qs(urlsplit(url).query)
        report=q['type'][0]
        quarter=q['termtype']==['2']
        codes={'CDKT':{2996:100,2997:40,2998:60},'KQKD':{2216:100,2212:20},'LCTT':{2234:25}}[report]
        heads=[dict(YearPeriod=y,TermCode='Q'+str(n) if quarter else 'N',United='HN',BusinessType=1)
               for y in ([2025,2024] if quarter else [2025,2024,2023,2022,2021])
               for n in ([1,2,3,4] if quarter else [0])]
        return encoded(dict(Head=heads,Content={'s':[dict(ReportNormID=k,NameEn='synthetic',
            **{'Value'+str(i):v for i in range(1,len(heads)+1)}) for k,v in codes.items()]}))


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'configs').mkdir()
        (self.root/'artifacts').mkdir()
    def config(self,count=20,**changes):
        symbols=['T'+str(i).zfill(3) for i in range(count)]
        csv='security_id,ticker,market_feature_ready_v2\n'+''.join(f'KBS:HOSE:{s},{s},True\n' for s in symbols)
        market=self.root/'artifacts/market.csv'
        market.write_text(csv,encoding='utf8')
        plan=dict(version='financial-crawl-50-plan-v1',executable=False,
            universe_source=dict(path='artifacts/market.csv',sha256=digest(market.read_bytes())),
            members=[dict(ticker=s,security_id='KBS:HOSE:'+s,proposed_company_type='Regular') for s in symbols],
            waves=[dict(id=i//10+1,symbols=symbols[i:i+10]) for i in range(0,count,10)])
        p=self.root/'configs/plan.json'
        p.write_bytes(encoded(plan))
        cfg=dict(version='financial-crawl-trial-v1',plan_path='configs/plan.json',plan_sha256=digest(p.read_bytes()),
            cache_epoch='test',approved_hosts=['kbbuddywts.kbsec.com.vn'],budgets=CAPS|{'min_seconds_between_transport_attempts':2},
            annual_years=[2021,2022,2023,2024,2025],quarter_years=[2024,2025],score_years=[2023,2024,2025],
            history_requests=0,document_requests=0,document_symbols=0,documents_enabled=False,explicit_documents=[])
        cfg.update(changes)
        (self.root/'configs/user.json').write_bytes(encoded(cfg))
        return cfg
    def factory(self,opener):
        def create(root,out,c,state):
            t=TrialTransport(root,out,c,state,opener=opener,sleep=lambda _:None)
            t.mode='SYNTHETIC_OFFLINE_TEST'
            return t
        return create
    def execute(self,name,opener,parent=(),network=True):
        with contextlib.redirect_stdout(io.StringIO()):
            return run(self.root,'configs/user.json','data/'+name,parent,network,
                       transport_factory=self.factory(opener))
    def test_fifty_symbol_pipeline_resume_and_feedback(self):
        self.config(50)
        opener=Opener()
        first=self.execute('first',opener)
        self.assertEqual(first['engineering_status'],'COMPLETE')
        self.assertEqual(first['base_success'],{'annual':150,'quarter':150})
        self.assertEqual(len(opener.calls),300)
        self.assertEqual(first['attempted_symbols'],50)
        self.assertFalse(first['financial_cluster_allowed'])
        self.assertFalse(first['next_100_allowed'])
        forbidden=Opener(lambda *_:AssertionError('unexpected transport'))
        second=self.execute('second',forbidden,['data/first'])
        third=self.execute('third',forbidden,['data/second'])
        self.assertEqual(forbidden.calls,[])
        self.assertEqual(third['trial_totals']['transport_attempts'],300)
        self.assertEqual(third['metrics']['logical_requests'],0)
        self.assertEqual(third['metrics']['new_checkpoints'],0)
        for name in ['candidates.jsonl','coverage.csv','period-coverage.csv','feature-readiness.csv','review-queue.json']:
            self.assertEqual((self.root/'data/first'/name).read_bytes(),(self.root/'data/third'/name).read_bytes())
        verify(self.root,'data/third')
        f=feedback(self.root,'data/third','artifacts/feedback.zip')
        self.assertFalse(f['includes_raw'])
        self.assertTrue(Path(f['path']).exists())
    def test_hard_stop_latched_across_waves_and_resumes_and_fresh_run_rejected(self):
        for code in [401,403,429]:
            with self.subTest(code=code):
                self.config(20,cache_epoch=str(code))
                def response(url,n):
                    return HTTPError(url,code,'blocked',None,None) if n==31 else Opener.provider(url,n)
                opener=Opener(response)
                first=self.execute(str(code)+'a',opener)
                self.assertEqual(first['engineering_status'],'HARD_STOP')
                self.assertEqual(len(opener.calls),31)
                second=self.execute(str(code)+'b',opener,['data/'+str(code)+'a'])
                self.assertEqual(second['engineering_status'],'HARD_STOP')
                self.assertEqual(len(opener.calls),31)
                with self.assertRaisesRegex(ValueError,'epoch already started'):
                    self.execute(str(code)+'new',opener)
    def test_global_attempt_and_byte_caps_survive_resume(self):
        cfg=self.config(20)
        cfg['budgets']['max_transport_attempts']=5
        (self.root/'configs/user.json').write_bytes(encoded(cfg))
        opener=Opener()
        first=self.execute('cap',opener)
        self.assertEqual(first['engineering_status'],'BUDGET_STOP')
        second=self.execute('cap2',opener,['data/cap'])
        self.assertEqual(second['trial_totals']['transport_attempts'],5)
        self.assertEqual(len(opener.calls),5)
        self.config(1,cache_epoch='bytes')
        cfg=json.loads((self.root/'configs/user.json').read_bytes())
        cfg['budgets']['max_total_downloaded_bytes']=12
        (self.root/'configs/user.json').write_bytes(encoded(cfg))
        first=self.execute('bytes',Opener(lambda *_:b'123456789012345'))
        self.assertEqual(first['trial_totals']['downloaded_bytes'],12)
        self.assertEqual(first['engineering_status'],'BUDGET_STOP')
    def test_logical_request_cap_stops_current_run_instead_of_quality_gate(self):
        cfg=self.config(20)
        cfg['budgets']['max_logical_requests']=5
        (self.root/'configs/user.json').write_bytes(encoded(cfg))
        opener=Opener()
        r=self.execute('logical',opener)
        self.assertEqual(r['engineering_status'],'BUDGET_STOP')
        self.assertEqual(r['trial_totals']['logical_requests'],5)
        self.assertEqual(len(opener.calls),5)
    def test_invalid_payload_stops_next_wave_with_all_symbol_gap_rows(self):
        self.config(20)
        opener=Opener(lambda url,n:b'not json' if n<=4 else Opener.provider(url,n))
        first=self.execute('badpayload',opener)
        self.assertEqual(first['engineering_status'],'QUALITY_STOP')
        self.assertEqual(len(opener.calls),30)
        self.assertEqual(first['attempted_symbols'],10)
        self.assertEqual(len({r['symbol'] for r in first['summary']['coverage']}),20)
    def test_overflow_numeric_payload_is_reported_without_export_crash(self):
        self.config(1)
        def response(url,n):
            raw=Opener.provider(url,n)
            return raw.replace(b'100,',b'1e309,') if n==1 else raw
        result=self.execute('overflow',Opener(response))
        self.assertEqual(result['engineering_status'],'QUALITY_STOP')
        self.assertEqual(result['structured'][0]['status'],'INVALID_PROVIDER_PAYLOAD')
        verify(self.root,'data/overflow')
    def test_interrupted_parent_resumes_sealed_tasks_and_reservations(self):
        self.config(2)
        def response(url,n):
            if n==2:
                raise KeyboardInterrupt()
            return Opener.provider(url,n)
        opener=Opener(response)
        with self.assertRaises(KeyboardInterrupt):
            self.execute('interrupted',opener)
        self.assertFalse((self.root/'data/interrupted/manifest.json').exists())
        state=read_ledger(self.root/'data/interrupted/ledger')[-1]['state']
        self.assertEqual(state['transport_attempts'],2)
        resumed=self.execute('resumed',Opener(),['data/interrupted'])
        self.assertEqual(resumed['engineering_status'],'COMPLETE')
        self.assertEqual(resumed['trial_totals']['transport_attempts'],13)
        self.assertGreater(resumed['metrics']['cache_hits'],0)
        verify(self.root,'data/resumed')
    def test_tampered_resume_and_plan_are_rejected_before_transport(self):
        self.config(1)
        self.execute('base',Opener())
        raw=next((self.root/'data/base/raw').glob('*.json'))
        raw.write_bytes(b'bad')
        opener=Opener()
        with self.assertRaises(ValueError):
            self.execute('bad',opener,['data/base'])
        self.assertEqual(opener.calls,[])
        self.assertFalse((self.root/'data/bad').exists())
        cfg=json.loads((self.root/'configs/user.json').read_bytes())
        cfg['budgets']['max_logical_requests']=451
        with self.assertRaises(ValueError):
            prepare(self.root,cfg)
        cfg['budgets']['max_logical_requests']=450
        cfg['financial_cluster_allowed']=True
        with self.assertRaises(ValueError):
            prepare(self.root,cfg)
    def test_missing_business_type_and_duplicate_quarter_headers_are_quarantined(self):
        self.config(1)
        def response(url,n):
            p=json.loads(Opener.provider(url,n))
            if 'termtype=2' in url:
                p['Head'][1]=dict(p['Head'][0])
            else:
                for h in p['Head']:
                    h.pop('BusinessType')
            return encoded(p)
        result=self.execute('headers',Opener(response))
        rows=[json.loads(line) for line in (self.root/'data/headers/candidates.jsonl').read_text(encoding='utf8').splitlines()]
        self.assertTrue(all(r['field'] is None for r in rows if r['quarter']==0))
        self.assertTrue(all(not r['in_target'] for r in rows if r['header_status']=='AMBIGUOUS_DUPLICATED_PERIOD_COLUMNS'))
    def test_pdf_worker_text_resume_and_global_reservation_after_timeout(self):
        import pypdf
        self.config(1,cache_epoch='pdf',approved_hosts=['example.test','kbbuddywts.kbsec.com.vn'],
            documents_enabled=True,document_requests=3,document_symbols=1,
            explicit_documents=[dict(symbol='T000',year=2025,quarter=0,url='https://example.test/doc.pdf')])
        (self.root/'scripts').mkdir()
        (self.root/'scripts/ocr_financial_pages.ps1').write_text('# unused',encoding='utf8')
        writer=pypdf.PdfWriter()
        writer.add_blank_page(width=100,height=100)
        writer.add_blank_page(width=100,height=100)
        stream=io.BytesIO(); writer.write(stream)
        opener=Opener(lambda url,n:stream.getvalue() if url.endswith('.pdf') else Opener.provider(url,n))
        def worker(args,**kwargs):
            self.assertGreater(kwargs['timeout'],0)
            self.assertLessEqual(kwargs['timeout'],14400)
            job=json.loads((self.root/args[-1]).read_bytes())
            out=self.root/args[args.index('--output')+1]
            cp=Checkpoints(self.root,out,job['config'],job['resume_runs'])
            receipt=extract(cp,job['document'],self.root/'scripts/ocr_financial_pages.ps1')
            return types.SimpleNamespace(stdout=encoded(dict(receipt=receipt,metrics=cp.metrics)))
        def execute(name,parent=(),command=worker):
            with contextlib.redirect_stdout(io.StringIO()):
                return run(self.root,'configs/user.json','data/'+name,parent,True,
                    transport_factory=self.factory(opener),pdf_command=command)
        first=execute('pdf')
        self.assertEqual(first['documents'][0]['extraction']['status'],'COMPLETE')
        self.assertEqual(first['trial_totals']['text_pages'],2)
        self.assertEqual(first['trial_totals']['reserved_text_pages'],0)
        second=execute('pdf_replay',['data/pdf'],command=lambda *_a,**_k: (_ for _ in ()).throw(AssertionError('cached extraction must not launch worker')))
        self.assertEqual(second['trial_totals']['text_pages'],2)
        self.assertEqual(second['metrics']['text_pages'],0)
        self.assertEqual(len(opener.calls),7)
        self.config(1,cache_epoch='timeout',approved_hosts=['example.test','kbbuddywts.kbsec.com.vn'],
            documents_enabled=True,document_requests=3,document_symbols=1,
            explicit_documents=[dict(symbol='T000',year=2025,quarter=0,url='https://example.test/doc.pdf')])
        def timeout(args,**kwargs): raise subprocess.TimeoutExpired(args,kwargs['timeout'])
        partial=execute('timeout',command=timeout)
        self.assertEqual(partial['engineering_status'],'PARTIAL')
        self.assertEqual(partial['trial_totals']['reserved_text_pages'],250)
        done=execute('timeout_resumed',['data/timeout'])
        self.assertEqual(done['trial_totals']['reserved_text_pages'],250)
        self.assertEqual(done['trial_totals']['text_pages'],2)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config=dict(budgets=CAPS|{'min_seconds_between_transport_attempts':2},
            cache_epoch='transport',approved_hosts=['example.test'])
    def test_retries_and_spacing_are_bounded_and_persist(self):
        clock=[0]
        def sleep(seconds): clock[0]+=seconds
        opener=Opener(lambda *_:URLError('timeout'))
        t=TrialTransport(self.root,self.root/'data/one',self.config,opener=opener,sleep=sleep,clock=lambda:clock[0])
        with self.assertRaises(ValueError): t.get('https://example.test/a')
        self.assertEqual(len(opener.calls),2)
        self.assertGreaterEqual(clock[0],4)
        reserved=next(e for e in t.journal if e['action']=='REQUEST_RESERVED')
        self.assertEqual(reserved['detail']['request_snapshot']['attempts'],0)
        attempts=[e['detail']['request_snapshot']['attempts'] for e in t.journal if e['action']=='ATTEMPT_START']
        self.assertEqual(attempts,[1,2])
        state=read_ledger(self.root/'data/one/ledger')[-1]['state']
        t2=TrialTransport(self.root,self.root/'data/two',self.config,state,opener=opener,sleep=sleep)
        with self.assertRaises(ValueError): t2.get('https://example.test/a')
        self.assertEqual(len(opener.calls),2)
    def test_document_selection_retains_sector_diversity_despite_financial_mapping_gaps(self):
        from collections import Counter
        symbols=['R'+str(i) for i in range(10)]+['B'+str(i) for i in range(6)]+['S0','S1','I0']
        types={s:'Regular' if s.startswith('R') else 'Bank' if s.startswith('B') else 'Securities' if s.startswith('S') else 'Insurance' for s in symbols}
        gaps=Counter({s:1000 if types[s]!='Regular' else 10 for s in symbols})
        selected=document_sample(symbols,types,[dict(symbol='R0')],gaps,12)
        self.assertEqual(len(selected),len(set(selected)))
        self.assertIn('R0',selected)
        self.assertEqual({types[s] for s in selected},{'Regular','Bank','Securities','Insurance'})
        self.assertGreater(sum(types[s]=='Regular' for s in selected),sum(types[s]=='Bank' for s in selected))
    def test_challenge_wall_clock_and_unconfirmed_read_reservation(self):
        t=TrialTransport(self.root,self.root/'data/challenge',self.config,opener=Opener(lambda *_:b'captcha'),sleep=lambda _:None)
        with self.assertRaises(AccessControlError): t.get('https://example.test/a')
        self.assertTrue(t.state['boundary'])
        clock=[0]
        t=TrialTransport(self.root,self.root/'data/time',self.config,utc=lambda:clock[0],sleep=lambda _:None)
        clock[0]=14401
        with self.assertRaises(TrialBudgetError): t.get('https://example.test/a')
        self.assertEqual(t.state['transport_attempts'],0)
        class Interrupted(Response):
            def read1(self,count): raise KeyboardInterrupt()
        class InterruptedOpener:
            def open(self,*a,**k): return Interrupted(b'body')
        t=TrialTransport(self.root,self.root/'data/interrupted',self.config,opener=InterruptedOpener(),sleep=lambda _:None)
        with self.assertRaises(KeyboardInterrupt): t.get('https://example.test/a')
        state=read_ledger(self.root/'data/interrupted/ledger')[-1]['state']
        self.assertEqual(state['reserved_bytes'],65536)
        self.assertEqual(state['transport_attempts'],1)


if __name__=='__main__': unittest.main()
