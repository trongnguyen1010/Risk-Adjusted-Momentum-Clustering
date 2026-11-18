"""Failure-mode checks for pilot identity, semantics and durable acquisition."""
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from delta_t1.experiments.financial_cafef_pilot import (
    PilotTransport, compute, FAMILIES, SYMBOLS, required_keys, pins, LIVING_SOURCES)
from delta_t1.experiments.financial_cafef_pilot import reviewed, verify_result
from delta_t1.ingestion.cafef_financial_deep import parse_report, compare_candidate, disclosures
from delta_t1.ingestion.financial_compact_trial import read_compact
from delta_t1.ingestion.cafef_financial import digest
from delta_t1.ingestion.sources.base import AccessControlError, RateLimitError
from delta_t1.features.financial_vas_reference import calculate_disclosed_basic_eps


def payload(groups, template=None):
    return json.dumps(dict(isSuccess=True,value=dict(templace=template or [dict(code=g['code'],
        data=[dict(code=g['code']+'_x',name='Test row')]) for g in groups],data=groups,unit=None))).encode()


def group(code,year,raw=0,symbol='BRC',quarter=0):
    return dict(code=code,data=[dict(symbol=symbol,year=year,quater=quarter,time=str(year),type='HK',
        data=[dict(code=code+'_x',value=raw)])])


class DeepSemantics(unittest.TestCase):
    def test_group_headers_remain_independent(self):
        rows=parse_report(payload([group('HDKD',2022),group('HDDT',2026),group('HDTC',2026)]),
                          'BRC','LCTT','NAM','fixture')
        self.assertEqual([(r['group'],r['year']) for r in rows],[('HDKD',2022),('HDDT',2026),('HDTC',2026)])

    def test_quarter_cashflow_not_inferred_single_quarter(self):
        rows=parse_report(payload([group('HDKD',2026,quarter=3)]),'BRC','LCTT','QUY','f')
        self.assertEqual(rows[0]['interval'],'INTERVAL_UNRESOLVED')

    def test_luyke_half_year(self):
        r=parse_report(payload([group('HDKD',2026,quarter=2)]),'BRC','LCTT','LUYKE','f')[0]
        self.assertEqual(r['interval'],'H1_REVIEWED')

    def test_zero_is_not_dash_or_missing(self):
        for raw,expected in [(0,'0'),(None,None),('-',None),('—',None)]:
            r=parse_report(payload([group('TN',2025,raw)]),'BRC','CDKT','NAM','f')[0]
            self.assertEqual(r['value'],expected)

    def test_wrong_issuer_rejected(self):
        with self.assertRaisesRegex(ValueError,'issuer'):
            parse_report(payload([group('TN',2025,symbol='FPT')]),'BRC','CDKT','NAM','f')

    def test_debt_template_conflict_does_not_move_next_value(self):
        t=[dict(code='NV',data=[dict(code='320',name='Vay và nợ thuê tài chính'),
                               dict(code='321',name='Dự phòng phải trả')])]
        g=[dict(code='NV',data=[dict(symbol='BRC',year=2025,quater=0,time='2025',type='HK',data=[
            dict(code='320',value=1175123567),dict(code='321',value=24141566184)])])]
        rows=parse_report(payload(g,t),'BRC','CDKT','NAM','f')
        self.assertEqual(compare_candidate(rows[0],'24141566184'),'MAPPING_CONFLICT')
        self.assertEqual(rows[0]['value'],'1175123567')
        self.assertEqual(rows[1]['raw_code'],'321')

    def test_kqkd_flat_template_keeps_eps_precision(self):
        p=dict(isSuccess=True,value=dict(templace=[dict(code='70',name='Lãi cơ bản trên cổ phiếu')],
            data=[dict(symbol='FPT',year=2025,quater=0,time='2025',type='HK',data=[dict(code='70',value=5216)])]))
        r=parse_report(json.dumps(p).encode(),'FPT','KQKD','NAM','f')[0]
        self.assertEqual(r['value'],'5216')
        self.assertEqual(r['unit_status'],'FIELD_UNIT_REVIEW_REQUIRED')

    def test_template_version_changes_with_label(self):
        a=payload([group('TN',2025)])
        b=a.replace(b'Test row',b'Another label')
        self.assertNotEqual(parse_report(a,'BRC','CDKT','NAM','f')[0]['template_sha256'],
                            parse_report(b,'BRC','CDKT','NAM','f')[0]['template_sha256'])

    def test_disclosure_create_date_never_period_time(self):
        p=dict(Data=dict(BctcList=[dict(Id='id',Symbol='FPT',Year=2025,Quarter=5,ReportType='HK',
            Content='Annual audited',LinkFile='/exact.pdf',CreateDate='/Date(1773853200000)/')]))
        r=disclosures(json.dumps(p).encode(),'FPT')[0]
        self.assertEqual(r['precision'],'DATE_ONLY')
        self.assertEqual(r['publication_date'],'2026-03-19')
        self.assertEqual(r['provider_id'],'id')

    def test_basic_eps_not_blocked_by_dilution(self):
        r=calculate_disclosed_basic_eps('1001','10',12)
        self.assertEqual(r['value'],'100.1')
        self.assertIsNone(r['diluted_eps'])

    def test_missing_f_is_interval_not_full_score(self):
        rows,details,deps=compute([],{},dict(zip(FAMILIES,FAMILIES)))
        self.assertEqual(len(rows),30)
        self.assertEqual(len({(r['symbol'],r['family']) for r in rows}),30)
        self.assertTrue(all(r['value'] is None for r in rows))
        fs=next(r['result'] for r in details if r['family']=='F_SCORE')
        self.assertEqual(fs['interval'],[0,9])
        self.assertIn(('long_term_debt_including_current_portion',-1),required_keys('F_SCORE'))
        self.assertIn(('owned_tangible_ppe_depreciation',-1),required_keys('M_SCORE'))

    def test_adjusted_price_rejected(self):
        with self.assertRaisesRegex(ValueError,'adjusted'):
            compute([],{'BRC':dict(price_basis='VENDOR_ADJUSTED',price_date='2026-04-22',
                publication_date='2026-04-21')},dict(zip(FAMILIES,FAMILIES)))

    def test_price_same_day_as_date_only_publication_rejected(self):
        with self.assertRaisesRegex(ValueError,'publication'):
            compute([],{'BRC':dict(price_basis='RAW_UNADJUSTED_CLOSE',price_date='2026-04-21',
                publication_date='2026-04-21')},dict(zip(FAMILIES,FAMILIES)))


class Response:
    status=200
    def __init__(self,body=b'{}',interrupt=False):self.body=body;self.interrupt=interrupt
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read1(self,count):
        if self.interrupt:raise KeyboardInterrupt()
        body,self.body=self.body,b''
        return body[:count]
    read=read1


class Opener:
    def __init__(self,response=None,code=None):self.calls=0;self.response=response;self.code=code
    def open(self,*args,**kwargs):
        self.calls+=1
        if self.code:raise HTTPError('https://apiweb.cafef.vn/test',self.code,'fixture',{},None)
        return self.response


class DurableTransport(unittest.TestCase):
    def config(self):
        return dict(cache_epoch='fixed-fixture',approved_hosts=['apiweb.cafef.vn'],budgets=dict(
            max_logical_requests=3,max_transport_attempts=4,max_pdf_download_attempts=1,
            max_response_bytes=100,max_total_downloaded_bytes=200,max_wall_seconds=21600,
            max_attempts_per_request=2,timeout_seconds=25,min_seconds_between_transport_attempts=2))

    def transport(self,p,opener,utc=100):
        t=PilotTransport(p,p,self.config(),opener=opener,sleep=lambda x:None,utc=lambda:utc)
        t.context=dict(kind='listing')
        return t

    def test_counter_and_deadline_survive_restart(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);t=self.transport(p,Opener(Response()))
            t.get('https://apiweb.cafef.vn/test')
            u=self.transport(p,Opener(Response()),utc=110)
            self.assertEqual(u.state['transport_attempts'],1)
            self.assertEqual(u.state['created_at'],100)
            self.assertEqual(u.remaining_seconds(),21590)
            self.assertEqual(read_compact(p)['state']['downloaded_bytes'],2)

    def test_interrupted_read_reservation_is_not_refunded(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);t=self.transport(p,Opener(Response(interrupt=True)))
            with self.assertRaises(KeyboardInterrupt):t.get('https://apiweb.cafef.vn/test')
            u=self.transport(p,Opener(Response()),utc=111)
            self.assertEqual(u.state['transport_attempts'],1)
            self.assertEqual(u.state['reserved_bytes'],100)
            self.assertEqual(u.state['created_at'],100)

    def test_access_boundary_latches_without_retry(self):
        for code in [401,403,429]:
            with self.subTest(code=code),tempfile.TemporaryDirectory() as d:
                p=Path(d);o=Opener(code=code);t=self.transport(p,o)
                with self.assertRaises((AccessControlError,RateLimitError)):t.get('https://apiweb.cafef.vn/test')
                self.assertEqual(o.calls,1)
                o2=Opener(Response());u=self.transport(p,o2)
                with self.assertRaises(AccessControlError):u.get('https://apiweb.cafef.vn/other')
                self.assertEqual(o2.calls,0)

    def test_tampered_journal_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.transport(p,Opener(Response()))
            f=p/'transport.jsonl';f.write_bytes(f.read_bytes().replace(b'fixed-fixture',b'changed-value'))
            # Initial state has no request epoch; corrupt a chained previous hash instead.
            f.write_bytes(f.read_bytes()+b'{"index":5}\n')
            with self.assertRaises(ValueError):read_compact(p)

    def test_torn_tail_not_silently_discarded(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.transport(p,Opener(Response()))
            with (p/'transport.jsonl').open('ab') as f:f.write(b'{"partial":')
            with self.assertRaisesRegex(ValueError,'torn'):self.transport(p,Opener(Response()))

    def test_snapshot_supersession_does_not_waive_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);rel=next(iter(LIVING_SOURCES));file=p/rel;file.parent.mkdir(parents=True)
            file.write_bytes(b'new living version');s=p/'snapshots';s.mkdir();sha=digest(b'frozen version')
            (s/(sha+'.bin')).write_bytes(b'frozen version')
            pins(p,{rel:sha},s)
            (s/(sha+'.bin')).write_bytes(b'tampered')
            with self.assertRaises(ValueError):pins(p,{rel:sha},s)

    def test_cached_document_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'document.pdf';f.write_bytes(b'original')
            sha=digest(f.read_bytes());f.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):pins(p,{'document.pdf':sha})

    def test_incompatible_framework_and_scope_rejected(self):
        for framework,scope in [('IFRS','CONSOLIDATED'),('VAS','SEPARATE_PARENT')]:
            with self.subTest(framework=framework,scope=scope),tempfile.TemporaryDirectory() as d:
                p=Path(d);(p/'reviews').mkdir()
                fact=dict(symbol='VNM',field='net_profit',year=2025,value='1',unit='VND',
                    review_status='REVIEWED_REFERENCE_ONLY',provenance={'page':10},framework=framework,scope=scope)
                (p/'reviews/01.json').write_text(json.dumps(dict(version='pilot5-reviewed-inputs-v1',
                    source_pins={},facts=[fact])),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'scope/framework'):reviewed(p,p)

    def test_metric_artifact_tamper_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'metrics.csv').write_bytes(b'changed')
            (p/'manifest.json').write_text(json.dumps(dict(files={'metrics.csv':digest(b'original')})))
            with self.assertRaisesRegex(ValueError,'result tamper'):verify_result(p,p)


if __name__=='__main__':unittest.main()
