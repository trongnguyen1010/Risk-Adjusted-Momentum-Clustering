import json,unittest
from delta_t1.ingestion.cafef_financial import digest
from delta_t1.experiments.financial_template_candidates import parse_candidates
from delta_t1.experiments.financial_acquisition_audit import replay,classify
from delta_t1.experiments.financial_acquisition_batches_rate1 import validate_budget
from delta_t1.experiments.financial_acquisition_batches import validate_budget as old_budget
from unit.experiments.test_financial_acquisition_first import AcquisitionFirstTests
class StreamingAuditTests(unittest.TestCase):
 def fixture(self):
  task=dict(symbol='AAA',statement='CDKT',group='TN',mode='NAM')
  body=json.dumps(dict(isSuccess=True,value=dict(templace=[dict(code='TN',number=1,data=[dict(code='100',name='Assets')])],data=[dict(code='TN',data=[dict(symbol='AAA',year=2025,quater=0,type='HK',data=[dict(code='100',value=123)])])]))).encode()
  rec=dict(path='raw.json',sha256=digest(body));rows=parse_candidates(body,task,rec['path'],rec['sha256']);shard=b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode() for row in rows)
  return body,task,rec,shard
 def test_replay_detects_raw_and_candidate_tampering(self):
  b,t,r,s=self.fixture();self.assertEqual(len(replay(b,t,r,s)),1)
  self.assertRaises(ValueError,replay,b+b' ',t,r,s)
  self.assertRaises(ValueError,replay,b,t,r,s.replace(b'123',b'124'))
 def test_wrong_provider_symbol_cannot_join(self):
  b,t,r,s=self.fixture();t['symbol']='OTHER';self.assertRaises(ValueError,replay,b,t,r,s)
 def test_only_proved_root_zero_is_structural(self):
  row=dict(value='0',label=None,raw_code='TN_1',group='TN',value_status='NUMERIC_CANDIDATE',mapping_status='UNMAPPED_CODE_QUARANTINED')
  payload=dict(value=dict(templace=[dict(code='TN',number=1,data=[dict(code='100')])]))
  self.assertEqual(classify(row,payload),'PROVEN_STRUCTURAL_HEADER_ZERO')
  row['raw_code']='100';self.assertEqual(classify(row,payload),'UNRESOLVED_MAPPING')
 def test_invalid_numeric_and_promotion_fail_closed(self):
  row=dict(value_status='INVALID_NUMERIC_QUARANTINED');self.assertEqual(classify(row,{}),'INVALID_NUMERIC')
  row['accepted']=True;self.assertRaises(ValueError,classify,row,{})
 def test_new_rate_does_not_mutate_old_policy(self):
  c,s=AcquisitionFirstTests().config();c['budgets']['min_seconds_between_transport_attempts']=1
  validate_budget(c,s,30);self.assertRaises(ValueError,old_budget,c,s,30)
  c['budgets']['min_seconds_between_transport_attempts']=.5;self.assertRaises(ValueError,validate_budget,c,s,30)
if __name__=='__main__':unittest.main()
