import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError

from delta_t1.ingestion.financial_source_compare import BenchmarkTransport, kbs_request, parse_kbs
from delta_t1.experiments.financial_source_benchmark import coverage, qa, validate_config, run
from delta_t1.ingestion.sources.base import AccessControlError


def payload(heads=None,extra=None):
    return json.dumps(dict(Head=heads if heads is not None else [dict(YearPeriod=2025,TermCode='N',BusinessType=1)],
        Content={'BS':[dict(ReportNormID=2996,NameEn='Total Assets',Value1=123,Value2=extra)]})).encode()


def request():
    return dict(kbs_request('FPT','CDKT','year'),path='raw/example.json',sha256='a'*64)


class BenchmarkTests(unittest.TestCase):
    def test_page_one_preserves_null_padding_but_rejects_unheaded_numeric(self):
        rows,meta=parse_kbs(payload(),request(),'Regular')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['comparison_value'],'123000')
        self.assertEqual(meta['null_trailing_columns'],1)
        with self.assertRaisesRegex(ValueError,'non-null numeric'):parse_kbs(payload(extra=456),request(),'Regular')
        rows,meta=parse_kbs(payload(heads=[] ,extra=None).replace(b'123',b'null'),request(),'Regular')
        self.assertEqual(rows,[]);self.assertEqual(meta['status'],'END_OF_SERIES')

    def test_duplicates_and_sector_do_not_acquire_mappings(self):
        heads=[dict(YearPeriod=2025,TermCode='N',BusinessType=1)]*2
        rows,_=parse_kbs(payload(heads,456),request(),'Regular')
        self.assertFalse(any(row['unambiguous'] for row in rows))
        rows,_=parse_kbs(payload(),request(),'Bank')
        self.assertIsNone(rows[0]['field']);self.assertIsNone(rows[0]['comparison_value'])
        with self.assertRaises(ValueError):parse_kbs(payload().replace(b'123',b'1e309'),request(),'Regular')

    def test_period_denominator_and_conflicts_do_not_count_as_accuracy(self):
        config=dict(symbols={'FPT':'Regular'},history_symbols=['FPT'],annual_years=list(range(2021,2026)),quarter_years=[2024,2025])
        row=dict(provider='KBS',symbol='FPT',report='CDKT',year=2025,quarter=0,raw_value=1,
                 unambiguous=True,numeric_status='CANDIDATE',field='total_assets',comparison_value='1000')
        rows=coverage([row],config)
        self.assertEqual(len(rows),78);self.assertEqual(sum(r['present'] for r in rows),1)
        refs=[dict(symbol='FPT',year=2025,field='total_assets',value='1000')]
        result=qa([row,dict(row,comparison_value='5000')],refs)
        self.assertEqual(result[0]['status'],'MISSING_OR_UNMAPPED')
        self.assertEqual(result[1]['status'],'MULTIPLE_CANDIDATE_VALUES')

    def test_config_does_not_allow_scale_or_gate_changes(self):
        root=Path(__file__).resolve().parents[3]
        config=json.loads((root/'configs/data/financial_source_benchmark_v1.json').read_bytes())
        validate_config(config)
        for key,value in [('max_attempts',451),('interval_seconds',0),('financial_features_allowed',True),('approved_hosts',['example.test'])]:
            changed=dict(config,**{key:value})
            with self.assertRaises(ValueError):validate_config(changed)

    def test_access_boundary_latches_and_journal_is_compact(self):
        class Opener:
            calls=0
            def open(self,request,timeout):
                self.calls+=1
                raise HTTPError(request.full_url,429,'blocked',{},None)
        config=dict(approved_hosts=['kbbuddywts.kbsec.com.vn'],max_attempts=2,max_response_bytes=100,
                    max_total_bytes=1000,max_seconds=60,interval_seconds=2)
        with tempfile.TemporaryDirectory() as folder:
            opener=Opener();transport=BenchmarkTransport(Path(folder),config,opener=opener,sleep=lambda _:None)
            with self.assertRaises(AccessControlError):transport.get(request())
            with self.assertRaises(AccessControlError):transport.get(request())
            self.assertEqual(opener.calls,1)
            journal=[json.loads(line) for line in (Path(folder)/'transport.jsonl').read_text(encoding='utf8').splitlines()]
            self.assertEqual(len(journal),2);self.assertTrue(journal[-1]['state']['boundary'])
            self.assertEqual(transport.state['reserved_bytes'],0)

    def test_orchestrator_seals_partial_source_errors_and_stops_global_boundary(self):
        original=Path(__file__).resolve().parents[3]
        config=json.loads((original/'configs/data/financial_source_benchmark_v1.json').read_bytes())
        config.update(symbols={'VNM':'Regular'},history_symbols=[],ground_truth_paths=[])
        class Transport:
            def __init__(self,*args):self.state=dict(boundary=False,attempts=0,bytes_read=0,reserved_bytes=0)
            def get(self,job):
                self.state['attempts']+=1
                if job['provider']=='CAFEF':raise ValueError('HTTP 302; no redirect/workaround')
                return b'{"Head":[],"Content":{}}',.01
        class Boundary(Transport):
            def get(self,job):
                self.state.update(boundary=True,attempts=1)
                raise AccessControlError('HTTP 429')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'configs/data').mkdir(parents=True)
            (root/'configs/data/test.json').write_text(json.dumps(config))
            for name in ['ingestion/financial_source_compare.py','experiments/financial_source_benchmark.py']:
                path=root/'src/delta_t1'/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes((original/'src/delta_t1'/name).read_bytes())
            partial=run(root,'configs/data/test.json','data/partial',True,transport_class=Transport)
            self.assertEqual(partial['engineering_status'],'PARTIAL')
            self.assertEqual(len(partial['requests']),12)
            self.assertEqual(partial['source_summary']['KBS']['present_statement_periods'],0)
            self.assertTrue((root/'data/partial/manifest.json').is_file())
            blocked=run(root,'configs/data/test.json','data/blocked',True,transport_class=Boundary)
            self.assertEqual(blocked['engineering_status'],'HARD_STOP')
            self.assertEqual(len(blocked['requests']),1)
            self.assertFalse(blocked['financial_cluster_allowed'])
            planned=run(root,'configs/data/test.json','data/planned',False,transport_class=Transport)
            self.assertEqual(planned['engineering_status'],'PLANNED')
            self.assertEqual(planned['transport_totals']['attempts'],0)

    def test_response_cap_reserves_before_read_and_counts_rejected_bytes(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,count):return b'x'*count
        class Opener:
            def open(self,request,timeout):return Response()
        config=dict(approved_hosts=['kbbuddywts.kbsec.com.vn'],max_attempts=2,max_response_bytes=100,
                    max_total_bytes=1000,max_seconds=60,interval_seconds=2)
        with tempfile.TemporaryDirectory() as folder:
            transport=BenchmarkTransport(Path(folder),config,opener=Opener(),sleep=lambda _:None)
            with self.assertRaisesRegex(ValueError,'response byte cap'):transport.get(request())
            self.assertEqual(transport.state['bytes_read'],101)
            self.assertEqual(transport.state['reserved_bytes'],0)
