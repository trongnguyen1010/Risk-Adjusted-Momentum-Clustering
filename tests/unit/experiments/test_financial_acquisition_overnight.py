import copy,csv,json,time,unittest
from pathlib import Path
from unittest.mock import patch
from delta_t1.experiments.financial_acquisition_overnight import campaign_assignment,check_parent
from unit.experiments.test_financial_acquisition_waves import WaveTests
class OvernightTests(unittest.TestCase):
 def test_real_schedule_covers_registry_exactly_and_keeps_unknown_legacy_unknown(self):
  root=Path(__file__).resolve().parents[3];c=json.loads((root/'configs/data/financial_acquisition_overnight_v1.json').read_bytes())
  with (root/c['registry']['path']).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
  initial=json.loads((root/c['initial_assignment']['path']).read_bytes());previous=initial['previous_members']+initial['members'];sizes=[];unknown=0
  for item in c['assignments']:
   a=json.loads((root/item['path']).read_bytes());members=campaign_assignment(rows,previous,a);sizes.append(len(members));unknown+=sum(not m['legacy_security_id'] for m in members);previous+=members
  self.assertEqual(sizes,[300,300,122]);self.assertEqual(unknown,421);self.assertEqual(len(previous),1522)
  self.assertEqual({m['registry_id'] for m in previous},{r['registry_id'] for r in rows})
 def test_previous_membership_must_match_exact_chain(self):
  rows,a=WaveTests().fixture();previous=a['previous_members'];self.assertEqual(len(campaign_assignment(rows,previous,a)),300)
  bad=copy.deepcopy(previous);bad.reverse();self.assertRaises(ValueError,campaign_assignment,rows,bad,a)
 def test_parent_failure_latch_and_deadline_fail_closed(self):
  state=dict(created_at=1792414507.836684,logical_requests=1,transport_attempts=1,downloaded_bytes=2,reserved_bytes=0,boundary=False,budget_stop=False,requests={},cache={})
  summary=dict(status='COMPLETE_CANDIDATE_TASK_ACCOUNTING',parser_errors=0,task_statuses=dict(ACQUIRED=1),counters={k:v for k,v in state.items() if k not in ['requests','cache']});ledger=dict(state=state,torn_tail_bytes=0)
  with patch('delta_t1.experiments.financial_acquisition_overnight.time.time',return_value=state['created_at']+100):
   self.assertEqual(check_parent(summary,ledger),state)
   for field in ['boundary','budget_stop']:
    bad=copy.deepcopy(ledger);bad['state'][field]=True;self.assertRaises(ValueError,check_parent,summary,bad)
   bad=copy.deepcopy(summary);bad['task_statuses']['FAILED_OR_STOPPED']=1;self.assertRaises(ValueError,check_parent,bad,ledger)
   bad=copy.deepcopy(ledger);bad['torn_tail_bytes']=1;self.assertRaises(ValueError,check_parent,summary,bad)
  with patch('delta_t1.experiments.financial_acquisition_overnight.time.time',return_value=state['created_at']+259201):self.assertRaises(ValueError,check_parent,summary,ledger)
if __name__=='__main__':unittest.main()
