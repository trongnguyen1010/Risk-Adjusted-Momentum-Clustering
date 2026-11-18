import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from delta_t1.experiments.cafef_financial_trial import (CLOSED,LIMITS,SOURCES,exports,jobs,parse,prepare,prepare50,run,verify)
from delta_t1.ingestion.cafef_financial import digest,encoded
from delta_t1.ingestion.financial_batch_evidence import seal
from delta_t1.ingestion.financial_compact_trial import CompactTrialTransport,read_compact
from delta_t1.ingestion.financial_data_report import FIELDS
from delta_t1.ingestion.financial_requirements import EXTRA
from delta_t1.ingestion.financial_source_compare import COMMON
from delta_t1.ingestion.financial_trial_transport import TrialBudgetError
from delta_t1.ingestion.sources.base import AccessControlError

ROOT=Path(__file__).resolve().parents[3]


def html(job,missing=False):
    periods=[(y,0) for y in range(job['year']-3,job['year']+1)] if job['quarter']==0 else [(job['year'],q) for q in range(1,5)]
    heads=''.join(f'<td class="h_t">{y if not q else f"Quý {q}- {y}"}</td>' for y,q in periods)
    rows=[]
    for f,(st,code,token) in {**FIELDS,**EXTRA}.items():
        if st!=job['statement']:continue
        values=''.join('<td></td>' if missing else '<td>1.000</td>' for _ in periods)
        rows.append(f'<tr id="{code}"><td>{token}</td>{values}<td><table><tr><td>9</td></tr></table></td></tr>')
    return (f'<input id="x_txtKeyword" value="{job["symbol"]}"><div class="dltlonote">Đơn vị: tỷ đồng</div>'
            f'<table id="tblGridData"><tr>{heads}</tr></table><table id="tableContent">'+''.join(rows)+'</table>').encode()


class Response(io.BytesIO):status=200
class Opener:
    def __init__(self,handler):self.handler=handler;self.calls=[]
    def open(self,request,timeout):
        self.calls.append(request.full_url);value=self.handler(request.full_url)
        if isinstance(value,BaseException):raise value
        return Response(value)


class CafeFTrialTests(unittest.TestCase):
    def setup_root(self,folder,seed=True):
        root=Path(folder);(root/'configs').mkdir();(root/'artifacts').mkdir()
        symbols=['FPT','VNM','PVS','ACV']+[f'T{i:03}' for i in range(46)]
        rows='ticker,security_id,market_feature_ready_v2\n'+''.join(f'{s},ID:{s},True\n' for s in symbols)
        market=root/'artifacts/market.csv';market.write_text(rows)
        plan=dict(version='financial-crawl-50-plan-v1',executable=False,universe_source=dict(path='artifacts/market.csv',sha256=digest(market.read_bytes())),
            members=[dict(ticker=s,security_id='ID:'+s,proposed_company_type='Regular') for s in symbols])
        path=root/'configs/plan.json';path.write_bytes(encoded(plan))
        c=dict(version='cafef-financial-trial-v1',source='CAFEF_DETAIL',plan_path='configs/plan.json',plan_sha256=digest(path.read_bytes()),
            symbols=symbols[:4],cache_epoch='test-pilot',approved_hosts=['cafef.vn'],annual_years=list(range(2021,2026)),quarter_years=[2024,2025],score_years=[2023,2024,2025],
            gap_request_limit=12,seed_run='data/benchmark' if seed else None,reference_benchmark='data/benchmark',pilot_gate=None,
            budgets=dict(LIMITS,min_seconds_between_transport_attempts=2),**CLOSED)
        for name in SOURCES:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        benchmark=root/'data/benchmark';benchmark.mkdir(parents=True)
        (benchmark/'config.json').write_bytes(encoded(dict(history_symbols=['FPT','VNM','PVS','ACV'],symbols={s:'Regular' for s in ['FPT','VNM','PVS','ACV']})))
        references=[dict(symbol=s,year=y,field=f,value='1000') for s in c['symbols'] for y in [2024,2025] for f in sorted(COMMON)][:78]
        refs=dict(source_pins={},references=references)
        (benchmark/'reference-inputs.json').write_bytes(encoded(refs))
        baseline=[dict(provider='CAFEF',**r,status='MATCH_WITHIN_TOLERANCE',candidate_values=['1000']) for r in references]
        (benchmark/'qa.json').write_bytes(encoded(baseline))
        requests=[]
        for job in jobs(c):
            body=html(job);raw=benchmark/'raw'/(digest(body)+'.html');raw.parent.mkdir(exist_ok=True)
            raw.write_bytes(body);requests.append(dict(job,provider='CAFEF',cohort='MAIN',status='PARSED_CANDIDATES',path=raw.relative_to(benchmark).as_posix(),sha256=digest(body)))
        (benchmark/'results.json').write_bytes(encoded(dict(requests=requests)));seal(benchmark)
        cfg=root/'configs/pilot.json';cfg.write_bytes(encoded(c));return root,c

    def factory(self,opener,utc=None):
        return lambda root,out,c,state:CompactTrialTransport(root,out,c,state,opener=opener,sleep=lambda _:None,utc=utc)

    def test_pilot_baseline_replay_gate_prepare50_and_no_raw_duplication(self):
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder)
            plan_path=root/'configs/plan.json';plan=json.loads(plan_path.read_bytes())
            # VNM/PVS need not belong to the market-ready trial50 cohort.
            for member in plan['members']:
                if member['ticker'] in ['VNM','PVS']:member.update(ticker='R'+member['ticker'],security_id='ID:R'+member['ticker'])
            market=root/'artifacts/market.csv';market.write_text(market.read_text().replace('VNM','RVNM').replace('PVS','RPVS'))
            plan['universe_source']['sha256']=digest(market.read_bytes());plan_path.write_bytes(encoded(plan))
            c['plan_sha256']=digest(plan_path.read_bytes());(root/'configs/pilot.json').write_bytes(encoded(c))
            forbidden=Opener(lambda _:AssertionError('unexpected network'))
            first=run(root,'configs/pilot.json','data/pilot',network=False,transport_factory=self.factory(forbidden))
            self.assertTrue(first['pilot_preflight_pass']);self.assertEqual(first['base_success'],48)
            self.assertEqual(first['qa_counts'],{'MATCH_WITHIN_TOLERANCE':78})
            self.assertEqual(first['present_statement_periods'],156);self.assertEqual(first['cache_hits'],48)
            self.assertFalse((root/'data/pilot/raw').exists())
            with self.assertRaisesRegex(ValueError,'epoch already started'):run(root,'configs/pilot.json','data/illegal',transport_factory=self.factory(forbidden))
            replay=run(root,'configs/pilot.json','data/replay','data/pilot',False,transport_factory=self.factory(forbidden))
            self.assertEqual(replay['trial_totals']['transport_attempts'],0)
            for name in ['candidates.jsonl','coverage.csv','feature-readiness.csv','qa.json']:
                self.assertEqual((root/'data/pilot'/name).read_bytes(),(root/'data/replay'/name).read_bytes())
            self.assertEqual(verify(root,'data/replay')['status'],'PASS')
            prepare50(root,'data/replay','configs/trial50.json')
            trial=json.loads((root/'configs/trial50.json').read_bytes());prepare(root,trial)
            self.assertEqual(len(jobs(trial)),600);self.assertIsNone(trial['seed_run'])
            self.assertFalse(trial['financial_cluster_allowed'])
            # A reference raw edit invalidates the transitive replay even though
            # no raw copies were created in either run.
            raw=next((root/'data/benchmark/raw').glob('*.html'));raw.write_bytes(b'changed')
            with self.assertRaises(ValueError):verify(root,'data/replay')

    def test_boundary_reservation_and_deadline_survive_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder,seed=False)
            blocked=Opener(lambda url:HTTPError(url,403,'blocked',{},None))
            first=run(root,'configs/pilot.json','data/first',network=True,transport_factory=self.factory(blocked))
            self.assertEqual(first['engineering_status'],'HARD_STOP');self.assertEqual(len(blocked.calls),1)
            replay=run(root,'configs/pilot.json','data/replay','data/first',True,transport_factory=self.factory(blocked))
            self.assertEqual(replay['engineering_status'],'HARD_STOP');self.assertEqual(len(blocked.calls),1)
            self.assertEqual(replay['trial_totals']['transport_attempts'],1)
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder,seed=False);c['budgets']['max_transport_attempts']=2
            (root/'configs/pilot.json').write_bytes(encoded(c));mapping={j['url']:html(j) for j in jobs(c)}
            opener=Opener(lambda url:mapping[url])
            first=run(root,'configs/pilot.json','data/first',network=True,transport_factory=self.factory(opener))
            self.assertEqual(first['engineering_status'],'BUDGET_STOP')
            replay=run(root,'configs/pilot.json','data/replay','data/first',True,transport_factory=self.factory(opener))
            self.assertEqual(len(opener.calls),2);self.assertEqual(replay['cache_hits'],2)
            self.assertEqual(replay['trial_totals']['transport_attempts'],2)

    def test_wrong_anchor_sector_units_and_same_field_conflict_remain_unaccepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder);job=jobs(c)[0];job.update(path='data/raw.html',sha256='a'*64)
            cells=parse(html(job),job,'Regular')
            assets=next(r for r in cells if r['field']=='total_assets')
            self.assertEqual(assets['raw_value'],1000);self.assertIsNone(assets['unit_scale'])
            self.assertEqual(assets['comparison_value'],'1000')
            self.assertFalse(assets['financial_features_allowed'])
            self.assertTrue(all(r['field'] is None for r in parse(html(job),job,'Bank')))
            with self.assertRaises(ValueError):parse(html(job).replace(b'2025',b'2020'),job,'Regular')
            duplicate=dict(assets,raw_value=2000,comparison_value='2000')
            _,requirements,tasks,conflicts=exports(cells+[duplicate],c,json.loads((root/'configs/plan.json').read_bytes())['members'][:4])
            self.assertTrue(conflicts);self.assertTrue(all(not row['task_ready'] for row in tasks))

    def test_torn_tail_only_and_hash_chain_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder);out=root/'data/journal';out.mkdir()
            t=CompactTrialTransport(root,out,c,opener=Opener(lambda _:b'body'),sleep=lambda _:None)
            t.context=dict(kind='structured');t.get('https://cafef.vn/test')
            original=(out/'transport.jsonl').read_bytes()
            (out/'transport.jsonl').write_bytes(original+b'{')
            ledger=read_compact(out);self.assertEqual(ledger['torn_tail_bytes'],1)
            self.assertEqual(ledger['state']['transport_attempts'],1)
            (out/'transport.jsonl').write_bytes(original.replace(b'"previous_sha256":null',b'"previous_sha256":"tampered"',1))
            with self.assertRaisesRegex(ValueError,'chain mismatch'):read_compact(out)

    def test_config_caps_and_pilot_gate_cannot_be_bypassed(self):
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder)
            for key,value in [('source','KBS'),('financial_cluster_allowed',True),('gap_request_limit',121)]:
                with self.assertRaises(ValueError):prepare(root,dict(c,**{key:value}))
            changed=json.loads(json.dumps(c));changed['budgets']['max_transport_attempts']=901
            with self.assertRaises(ValueError):prepare(root,changed)
            changed=dict(c,symbols=[m['ticker'] for m in json.loads((root/'configs/plan.json').read_bytes())['members']],seed_run=None)
            with self.assertRaisesRegex(ValueError,'pilot gate'):prepare(root,changed)

    def test_handoff_verifies_external_reviewed_reference_inputs(self):
        from scripts.crawl_cafef_financial import verify_handoff
        with tempfile.TemporaryDirectory() as folder:
            root,c=self.setup_root(folder)
            run(root,'configs/pilot.json','data/pilot',network=False,transport_factory=self.factory(Opener(lambda _:AssertionError('network'))))
            external=root/'data/external-fact.json';external.write_bytes(b'original')
            # The external reference snapshot is created before sealing this test run.
            out=root/'data/pilot';(out/'manifest.json').unlink()
            refs=json.loads((out/'references.json').read_bytes());refs['source_pins']={'data/external-fact.json':digest(b'original')}
            (out/'references.json').write_bytes(encoded(refs));seal(out)
            self.assertEqual(verify_handoff(root,'data/pilot')['reviewed_reference_files'],1)
            external.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'reviewed reference input changed'):verify_handoff(root,'data/pilot')

