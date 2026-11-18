import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from delta_t1.experiments import financial_user_workflow as f
from delta_t1.ingestion.cafef_financial import digest, encoded
from delta_t1.ingestion.financial_compact_trial import CompactTrialTransport


class Response(io.BytesIO):
    status = 200
    read1 = io.BytesIO.read


class Opener:
    def __init__(self, boundary=False):
        self.calls = 0; self.boundary = boundary

    def open(self, request, timeout):
        self.calls += 1
        if self.boundary:
            raise HTTPError(request.full_url, 403, 'Forbidden', {}, None)
        return Response(b'{"Success":true,"Data":[]}')


class UserWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        members = [dict(ticker=f'S{i:03}', proposed_company_type='Regular', exchange='HOSE') for i in range(50)]
        paths = {
            'data/trial/plan.json': dict(members=members), 'data/trial/requirements.json': [],
            'data/ocr/index.json': dict(documents=[]), 'data/review/references.json': [],
            'data/integration/reference-ledger.json': []}
        url = 'https://cafefnew.mediacdn.vn/sample.pdf'
        body = encoded(dict(Success=True, Data=[dict(Year=2025, Quarter=5, Name='unlabeled annual', Link=url)]))
        paths['data/list.json'] = None
        for path, obj in paths.items():
            f.write_new(self.root/path, body if obj is None else encoded(obj))
        f.write_new(self.root/'data/sample.pdf', b'%PDF-small fixture')
        cached = dict(symbol='S000', year=2025, kind='list', status='CACHED',
            url='https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol=s000&Type=1&Year=2025',
            path='data/list.json', sha256=digest(body))
        pdf = dict(status='CACHED', path='data/sample.pdf', sha256=digest(b'%PDF-small fixture'), url=url)
        probe = dict(requests=[cached, pdf], documents=[dict(symbol='S000',year=2025,
            acquisition=pdf,provider_report=dict(Name='unlabeled annual'))])
        f.write_new(self.root/'data/probe/results.json', encoded(probe))
        c = dict(version=f.VERSION,symbols=[m['ticker'] for m in members],target_years=[2025],
            document_years=[2023,2024,2025],trial_run='data/trial',probe_run='data/probe',ocr_run='data/ocr',
            review_run='data/review',integration_run='data/integration',extra_cached_pdfs=[],input_pins={},code_paths=[],
            approved_hosts=['cafef.vn','cafefnew.mediacdn.vn'],preview_pages=16,max_ocr_pages=6000,
            min_free_disk_bytes=1,budgets=dict(max_logical_requests=1,max_transport_attempts=1,
            max_pdf_download_attempts=1,max_response_bytes=1000,max_total_downloaded_bytes=10000,
            max_wall_seconds=86400,max_attempts_per_request=1,min_seconds_between_transport_attempts=2,
            timeout_seconds=1),**f.CLOSED)
        c['input_pins']={p:digest((self.root/p).read_bytes()) for p in paths}
        f.write_new(self.root/'configs/test.json', encoded(c))
        f.make_plan(self.root,'configs/test.json','data/user')
        return c, members

    def factory(self, opener):
        return lambda root,out,c,state: CompactTrialTransport(root,out,c,state,opener=opener,sleep=lambda x:None)

    def test_offline_resume_reuses_cache_and_does_not_finish_missing_jobs(self):
        self.fixture(); opener=Opener()
        r=f.acquire(self.root,'data/user',False,300,self.factory(opener))
        self.assertEqual(r['completed_jobs'],2); self.assertEqual(opener.calls,0)
        r=f.acquire(self.root,'data/user',False,300,self.factory(opener))
        self.assertEqual(r['completed_jobs'],0)
        report=f.report(self.root,'data/user')
        self.assertEqual(report['pending_acquisition_jobs'],149)
        self.assertEqual(report['tasks'],300); self.assertEqual(report['production_ready_symbols'],0)

    def test_counter_budget_cannot_reset_after_resume(self):
        self.fixture(); opener=Opener(); factory=self.factory(opener)
        f.acquire(self.root,'data/user',False,300,factory)
        r=f.acquire(self.root,'data/user',True,1,factory)
        self.assertEqual(r['counters']['transport_attempts'],1)
        r=f.acquire(self.root,'data/user',True,1,factory)
        self.assertEqual(r['status'],'GLOBAL_STOP')
        r=f.acquire(self.root,'data/user',True,300,factory)
        self.assertEqual(r['status'],'GLOBAL_STOP'); self.assertEqual(opener.calls,1)

    def test_access_boundary_survives_resume(self):
        self.fixture(); opener=Opener(True); factory=self.factory(opener)
        f.acquire(self.root,'data/user',False,300,factory)
        self.assertEqual(f.acquire(self.root,'data/user',True,1,factory)['status'],'GLOBAL_STOP')
        self.assertEqual(f.acquire(self.root,'data/user',True,1,factory)['status'],'GLOBAL_STOP')
        self.assertEqual(opener.calls,1)

    def test_crash_after_download_cache_commit_does_not_request_again(self):
        self.fixture(); opener=Opener(); factory=self.factory(opener)
        f.acquire(self.root,'data/user',False,300,factory)
        with patch.object(f,'seal',side_effect=RuntimeError('process interruption')):
            with self.assertRaises(RuntimeError):
                f.acquire(self.root,'data/user',True,1,factory)
        r=f.acquire(self.root,'data/user',False,300,factory)
        self.assertEqual(r['completed_jobs'],1); self.assertEqual(opener.calls,1)

    def test_missing_conflict_sector_and_reference_status_remain_distinct(self):
        _, members=self.fixture(); members=members[:2]; members[1]['proposed_company_type']='Bank'
        requirements=[dict(symbol='S000',year=2025,field='eps_adjusted_earnings_numerator',candidate_values=['1','2'])]
        rows=f.assessment(requirements,members,[],[2025])
        eps=next(r for r in rows if r['symbol']=='S000' and r['task']=='EPS_RECOMPUTE')
        self.assertIn('eps_adjusted_earnings_numerator@2025:VALUE_CONFLICT',eps['missing_fields'])
        self.assertEqual(rows[-1]['status'],'SECTOR_TEMPLATE_REQUIRED')
        self.assertTrue(all(r['production_value'] is None for r in rows))

    def test_frozen_input_drift_is_rejected(self):
        self.fixture(); (self.root/'data/trial/requirements.json').write_text('[1]')
        with self.assertRaisesRegex(ValueError,'input changed'):
            f.open_run(self.root,'data/user')

    def test_unlabeled_annual_is_preserved_but_not_accepted_and_unapproved_url_fails(self):
        rows=f.annual_rows(encoded(dict(Success=True,Data=[dict(Year=2025,Quarter=5,
            Name='annual',Link='https://bad.invalid/a.pdf')])),2025)
        self.assertEqual(len(rows),1)
        with self.assertRaises(ValueError):
            f.validate_url(rows[0]['Link'],['cafefnew.mediacdn.vn'])

    def reviewed(self):
        sha='a'*64
        vals=dict(current_assets=50,current_liabilities=30,total_assets=100,total_liabilities=60,
            total_equity=40,retained_earnings=10,document_reconciled_ebit=12,
            eps_adjusted_earnings_numerator=100,weighted_average_basic_shares=10,vendor_basic_eps=10)
        facts=[dict(field=k,year=2025,value=str(v),unit='SHARES' if k=='weighted_average_basic_shares' else
            'VND_PER_SHARE' if k=='vendor_basic_eps' else 'VND',pdf_page=1,locator='visually checked table',
            review_status='VISUALLY_VERIFIED_REFERENCE_ONLY') for k,v in vals.items()]
        d=dict(symbol='S000',year=2025,reviewer='owner',reviewed_at='2026-10-08',company_type='Regular',
            scope='CONSOLIDATED',framework='VAS',period_start='2025-01-01',period_end='2025-12-31',
            vintage_basis='CURRENT_AND_COMPARATIVE_IN_EXACT_PDF_REVIEWED',ebit_basis='DIRECT_DOCUMENT_RECONCILED_EBIT',
            receivables_basis='GROSS_SHORT_TERM_TRADE',pdf_sha256=sha,facts=facts,publication=None,**f.CLOSED)
        return d,{(sha,1):{}},[]

    def test_arithmetic_available_without_pit_does_not_open_gate(self):
        d,pages,calendar=self.reviewed()
        rows=f.calculate_review(d,pages,calendar,'2026-08-28','HOSE')
        z=next(r for r in rows if r['task']=='Z_SCORE'); eps=next(r for r in rows if r['task']=='EPS_RECOMPUTE')
        self.assertEqual(float(z['value']),6.3944); self.assertEqual(eps['value'],'10')
        self.assertFalse(z['date_eligible_at_snapshot']); self.assertFalse(z['financial_cluster_allowed'])
        self.assertIsNone(next(r for r in rows if r['task']=='F_SCORE')['value'])

    def test_review_rejects_wrong_units_zero_imputation_and_eps_mismatch(self):
        d,pages,cal=self.reviewed(); d['facts'][0]['unit']='MILLION_VND'
        with self.assertRaises(ValueError): f.calculate_review(d,pages,cal,'2026-08-28','HOSE')
        d,pages,cal=self.reviewed(); d['facts'][-1]['value']='11'
        rows=f.calculate_review(d,pages,cal,'2026-08-28','HOSE')
        self.assertIsNone(next(r for r in rows if r['task']=='EPS_RECOMPUTE')['value'])
        d,pages,cal=self.reviewed(); d['facts'][0]['value']=True
        with self.assertRaises(ValueError): f.calculate_review(d,pages,cal,'2026-08-28','HOSE')

    def test_review_rejects_sector_scope_fiscal_and_missing_page(self):
        for key,value in [('scope','STANDALONE'),('company_type','Bank'),('period_end','2025-06-30')]:
            d,pages,cal=self.reviewed(); d[key]=value
            with self.assertRaises(ValueError): f.calculate_review(d,pages,cal,'2026-08-28','HOSE')
        d,pages,cal=self.reviewed()
        with self.assertRaises(ValueError): f.calculate_review(d,{},cal,'2026-08-28','HOSE')

    def test_supporting_vintage_date_is_required_for_affected_metric_only(self):
        d,pages,cal=self.reviewed(); other='b'*64
        d['publication']=dict(pdf_sha256=d['pdf_sha256'],precision='DATE_ONLY',
            validation_status='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED',publication_date='2026-03-05')
        d['supporting_documents']=[dict(pdf_sha256=other,period_end='2024-12-31',publication=None)]
        d['facts'].append(dict(field='net_profit',year=2024,value='9',unit='VND',pdf_page=1,
            source_pdf_sha256=other,locator='older report',review_status='VISUALLY_VERIFIED_REFERENCE_ONLY'))
        pages[other,1]={}
        cal=[dict(exchange='HOSE',trade_date='2026-03-05',is_open=True),
             dict(exchange='HOSE',trade_date='2026-03-06',is_open=True)]
        rows=f.calculate_review(d,pages,cal,'2026-08-28','HOSE')
        self.assertIsNotNone(next(r for r in rows if r['task']=='EPS_RECOMPUTE')['usable_from_date'])
        self.assertIsNone(next(r for r in rows if r['task']=='F_SCORE')['usable_from_date'])


if __name__=='__main__': unittest.main()
