import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from delta_t1.ingestion.cafef_financial import digest
from delta_t1.experiments.financial_history_batch import tasks,collect,decide_gate,EvidenceIntegrityError


class HistoryBatchTests(unittest.TestCase):
    def members(self):
        return [dict(registry_id=f'R{i}',symbol=f'S{i}',provider_partition_id=f'PROVISIONAL:R{i}') for i in range(15)]

    def task(self,page):
        return next(t for t in tasks(self.members()) if (t['symbol'],t['statement'],t['mode'],t['group'],t['page'])==('S0','CDKT','NAM','TN',page))

    def body(self,year):
        return json.dumps(dict(isSuccess=True,value=dict(templace=[dict(code='TN',data=[dict(code='100',name='Assets')])],
            data=[dict(code='TN',data=[dict(symbol='S0',year=year,quater=0,type='HK',data=[dict(code='100',value=123)])])]))).encode()

    def fixture(self,root):
        out=root/'batch';out.mkdir();return out,dict(tasks=[self.task(1),self.task(2)],cache={},boundaries=dict(blocked_hosts=[]),seed=dict(requests={},boundary=False,budget_stop=False))

    def fake(self,responses,requested,seed=None):
        class Transport:
            def __init__(self,*args):self.state=dict(requests=dict(seed or {}),boundary=False,budget_stop=False);self.context={}
            def get(self,url):
                requested.append(url);self.state['requests'][url]=dict(url=url)
                return responses[url],200
        return Transport

    def test_task_scope_and_deterministic_independent_pagination(self):
        rows=tasks(self.members());self.assertEqual(len(rows),3300)
        self.assertEqual(len({r['id'] for r in rows}),3300)
        self.assertEqual(sum(r['kind']=='REPORT' for r in rows),2100)
        self.assertEqual({r['mode'] for r in rows if r['statement']=='CDKT'},{'NAM','QUY'})
        self.assertEqual(rows,tasks(self.members()[::-1]))
        for mode,expected in [('NAM',5),('QUY',15),('LUYKE',5)]:
            self.assertEqual(max(r['page'] for r in rows if r['mode']==mode),expected)

    def test_cache_target_boundary_stops_next_page_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);body=self.body(2012);(root/'cached.json').write_bytes(body)
            c['cache'][self.task(1)['url']]=dict(path='cached.json',sha256=digest(body))
            self.assertEqual(collect(root,{},out,c,False,0),0)
            rs=[json.loads(p.read_bytes()) for p in (out/'receipts').glob('*.json')]
            self.assertEqual({r['status'] for r in rs},{'CACHED_PROBE','NOT_REQUIRED_AFTER_SERIES_STOP'})

    def test_resume_preserves_prior_receipt_and_wave_cap(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);urls=[t['url'] for t in c['tasks']];requested=[]
            factory=self.fake({urls[0]:self.body(2025),urls[1]:self.body(2021)},requested)
            with patch('delta_t1.experiments.financial_history_batch.shutil.disk_usage',return_value=type('Disk',(),dict(free=99_000_000_000))()):
                self.assertEqual(collect(root,{},out,c,True,1,factory),1)
                rp=out/'receipts'/(self.task(1)['id']+'.json');before=rp.read_bytes()
                self.assertEqual(collect(root,{},out,c,True,1,factory),1)
            self.assertEqual(requested,urls);self.assertEqual(rp.read_bytes(),before)

    def test_silent_period_repeat_stops_even_when_values_change(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);c['tasks'].append(self.task(3));requested=[]
            response={t['url']:self.body(2025).replace(b'123',b'999') for t in c['tasks']}
            with patch('delta_t1.experiments.financial_history_batch.shutil.disk_usage',return_value=type('Disk',(),dict(free=99_000_000_000))()):
                self.assertEqual(collect(root,{},out,c,True,3,self.fake(response,requested)),2)
            third=json.loads((out/'receipts'/(self.task(3)['id']+'.json')).read_bytes())
            self.assertEqual(third['status'],'NOT_REQUIRED_AFTER_SERIES_STOP');self.assertEqual(len(requested),2)

    def test_imported_boundary_and_missing_predecessor_never_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);c['boundaries']['blocked_hosts']=['apiweb.cafef.vn']
            self.assertEqual(collect(root,{},out,c,True,10,lambda *a:self.fail('blocked network')),0)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);c['tasks']=[self.task(2)]
            self.assertEqual(collect(root,{},out,c,True,10,lambda *a:self.fail('missing predecessor network')),0)

    def test_interrupted_request_without_receipt_requires_review(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);url=self.task(1)['url']
            with patch('delta_t1.experiments.financial_history_batch.shutil.disk_usage',return_value=type('Disk',(),dict(free=99_000_000_000))()):
                with self.assertRaisesRegex(ValueError,'without receipt'):
                    collect(root,{},out,c,True,1,self.fake({},[],dict(old=dict(url=url))))

    def test_raw_corruption_is_fatal_not_parser_backlog(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out,c=self.fixture(root);(root/'cached.json').write_bytes(self.body(2025))
            c['cache'][self.task(1)['url']]=dict(path='cached.json',sha256='0'*64)
            with self.assertRaises(EvidenceIntegrityError):collect(root,{},out,c,False,0)

    def gate_fixture(self):
        profiles=[];catalogue=[]
        for i in range(15):
            kind=['Regular','Bank','Securities'][i%3]
            profiles.append(dict(symbol=f'S{i}',status='CURRENT_PROFILE_OBSERVED',proposed_company_type=kind,exchange=['HOSE','HNX','UPCOM'][i%3]))
            catalogue.append(dict(task=dict(symbol=f'S{i}',statement='KQKD'),template_sha256=[kind]))
        adapter=dict(tasks=180,parsed_tasks=180,parser_errors=0,quarantined_cells=1,numeric_acceptance_allowed=False,research_ready=False,original_strict_parser_review_tasks=4)
        return dict(pilot_history_engineering_pass=True),profiles,adapter,catalogue,[dict(accepted=False,pit_ready=False)]

    def test_new_adapter_gate_does_not_erase_old_failures_or_promote_numbers(self):
        result=decide_gate(*self.gate_fixture());self.assertTrue(result['candidate_acquisition_allowed'])
        self.assertEqual(result['original_strict_parser_review_tasks'],4);self.assertFalse(result['numeric_acceptance_allowed'])

    def test_gate_holds_parser_quarantine_and_template_diversity_errors(self):
        for key,value in [('parser_errors',2),('parser_errors',-1),('parser_errors',False),('parsed_tasks',0),('quarantined_cells',2),('numeric_acceptance_allowed',True)]:
            args=self.gate_fixture();args[2][key]=value
            self.assertFalse(decide_gate(*args)['candidate_acquisition_allowed'])
        args=self.gate_fixture();args[3][0]['template_sha256']=['Bank']
        self.assertFalse(decide_gate(*args)['candidate_acquisition_allowed'])


if __name__=='__main__':unittest.main()
