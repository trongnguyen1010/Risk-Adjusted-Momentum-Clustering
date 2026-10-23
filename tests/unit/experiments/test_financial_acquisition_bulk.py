import copy,csv,json,tempfile,unittest
from pathlib import Path
from delta_t1.ingestion.cafef_financial import digest,encoded
from delta_t1.ingestion.financial_compact_trial import read_compact
from delta_t1.ingestion.financial_journal_stream import read_stream,StreamingTransport
from delta_t1.experiments.financial_acquisition_bulk import validate_policy,validate_members,snapshot,boundaries
from delta_t1.experiments.financial_acquisition_batches import snapshot as old_snapshot
from delta_t1.experiments.financial_history_pit import audit_boundaries
from unit.experiments.test_financial_history_batch import HistoryBatchTests
class BulkTests(unittest.TestCase):
 def test_stream_transport_resumes_same_key_and_spaces_first_attempt(self):
  url='https://apiweb.cafef.vn/api/test';key=digest(encoded(dict(url=url,kind='structured',cache_epoch='same')))
  seed=dict(created_at=1000,logical_requests=1,transport_attempts=0,pdf_download_attempts=0,downloaded_bytes=0,reserved_bytes=0,text_pages=0,reserved_text_pages=0,requests={key:dict(url=url,kind='structured',attempts=0)},cache={},boundary=False,budget_stop=False,stop_reason=None)
  c=dict(approved_hosts=['apiweb.cafef.vn'],cache_epoch='same',budgets=dict(max_logical_requests=10,max_transport_attempts=20,max_pdf_download_attempts=1,max_total_downloaded_bytes=10000,max_response_bytes=1000,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=.4))
  clock=[1000.];sleeps=[]
  class Response:
   status=200
   def __enter__(self):self.sent=False;return self
   def __exit__(self,*a):pass
   def read(self,n):
    if self.sent:return b''
    self.sent=True;return b'{}'
  class Opener:
   def open(self,*a,**k):return Response()
  def sleep(delay):sleeps.append(delay);clock[0]+=delay
  with tempfile.TemporaryDirectory() as f:
   root=Path(f);kwargs=dict(opener=Opener(),sleep=sleep,clock=lambda:clock[0],utc=lambda:clock[0])
   first=StreamingTransport(root,root/'network',c,seed,**kwargs);first.context=dict(kind='structured');self.assertEqual(first.get(url),(b'{}',200))
   resumed=StreamingTransport(root,root/'network',c,seed,**kwargs)
   self.assertEqual(resumed.state['logical_requests'],1);self.assertEqual(resumed.state['transport_attempts'],1);self.assertEqual(resumed.state['requests'][key]['attempts'],1)
   self.assertEqual(sleeps,[.4]);self.assertEqual(read_stream(root/'network'),read_compact(root/'network'))
 def test_campaign_membership_keeps_checkpoint_and_limits_wave(self):
  root=Path(__file__).resolve().parents[3]
  a=json.loads((root/'configs/data/financial_acquisition_total500_bulk_assignment_v1.json').read_bytes());old=json.loads((root/'configs/data/financial_acquisition_total300_assignment_v1.json').read_bytes())
  with (root/'configs/data/securities_collection_registry_v1.csv').open(encoding='utf-8-sig',newline='') as stream:registry=list(csv.DictReader(stream))
  self.assertEqual(validate_members(registry,a,old),200)
  for change in ['remove','duplicate','promote']:
   bad=copy.deepcopy(a)
   if change=='remove':bad['members'].pop(0)
   if change=='duplicate':bad['members'][-1]=bad['members'][0]
   if change=='promote':bad['members'][-1]['historical_identity_ready']=True
   self.assertRaises(ValueError,validate_members,registry,bad,old)
 def journal(self,root,boundary=False):
  folder=root/'network';folder.mkdir();state=dict(created_at=1,logical_requests=0,transport_attempts=0,pdf_download_attempts=0,downloaded_bytes=0,reserved_bytes=0,text_pages=0,reserved_text_pages=0,requests={},cache={},boundary=False,budget_stop=False,stop_reason=None)
  events=[];prev=None
  def add(action,detail):
   nonlocal prev
   event=dict(index=len(events)+1,previous_sha256=prev,at='2026-10-21T00:00:00Z',action=action,state=copy.deepcopy(state),detail=detail);line=json.dumps(event,sort_keys=True,separators=(',',':')).encode();events.append(line+b'\n');prev=digest(line)
  add('START_OR_RESUME',{})
  state['requests']={'key':dict(url='https://apiweb.cafef.vn/exact',kind='structured',attempts=0)};state['logical_requests']=1
  add('REQUEST_RESERVED',dict(request_key='key',request_snapshot=state['requests']['key']))
  state['requests']['key']['attempts']=1;state['transport_attempts']=1;add('ATTEMPT_START',dict(request_key='key',request_snapshot=state['requests']['key']))
  if boundary:state['boundary']=True;state['stop_reason']='HTTP429';add('HARD_STOP',dict(request_key='key',request_snapshot=state['requests']['key']))
  (folder/'transport.jsonl').write_bytes(b''.join(events));return folder
 def test_stream_reader_exactly_matches_existing_format(self):
  with tempfile.TemporaryDirectory() as f:
   folder=self.journal(Path(f));self.assertEqual(read_stream(folder),read_compact(folder))
   p=folder/'transport.jsonl';p.write_bytes(p.read_bytes()+b'{partial');self.assertEqual(read_stream(folder),read_compact(folder));self.assertGreater(read_stream(folder)['torn_tail_bytes'],0)
 def test_stream_reader_rejects_hash_corruption(self):
  with tempfile.TemporaryDirectory() as f:
   folder=self.journal(Path(f));p=folder/'transport.jsonl';p.write_bytes(p.read_bytes().replace(b'ATTEMPT_START',b'ATTEMPT_CHANGED'))
   # Last-event hash has no successor, so tamper an earlier chained event instead.
   p.write_bytes(p.read_bytes().replace(b'REQUEST_RESERVED',b'REQUEST_CHANGED'))
   self.assertRaises(ValueError,read_stream,folder)
 def test_boundary_import_preserves_429_latch(self):
  with tempfile.TemporaryDirectory() as f:
   root=Path(f);self.journal(root,True);out=root/'new';out.mkdir();config=dict(boundary_roots=['network'])
   self.assertEqual(boundaries(root,config,out),audit_boundaries(root,config,out));self.assertEqual(boundaries(root,config,out)['blocked_hosts'],['apiweb.cafef.vn'])
 def policy(self):
  o=dict(budgets=dict(min_seconds_between_transport_attempts=1,max_logical_requests=33260,max_transport_attempts=47260,max_total_downloaded_bytes=2389061341,max_wall_seconds=259200,max_attempts_per_request=2,max_pdf_download_attempts=20),network_concurrency=1,years=list(range(2013,2026)),auxiliary_balance_year=2012,approved_hosts=['apiweb.cafef.vn'],max_campaign_days=90,cache_epoch='same',boundary_roots=['data/financial'],numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False)
  c=copy.deepcopy(o);c['local_io_workers']=8;c['budgets'].update(min_seconds_between_transport_attempts=.4,max_logical_requests=61260,max_transport_attempts=103260,max_total_downloaded_bytes=4389061341);return c,o
 def test_only_authorized_rate_and_added_work_increase(self):
  c,o=self.policy();validate_policy(c,o,200)
  for k,v in [('max_wall_seconds',259201),('max_attempts_per_request',3),('min_seconds_between_transport_attempts',.3)]:
   b=copy.deepcopy(c);b['budgets'][k]=v;self.assertRaises(ValueError,validate_policy,b,o,200)
  c['network_concurrency']=2;self.assertRaises(ValueError,validate_policy,c,o,200)
 def test_snapshot_aggregation_is_byte_equivalent_to_old(self):
  helper=HistoryBatchTests()
  with tempfile.TemporaryDirectory() as f:
   root=Path(f);out,contract=helper.fixture(root);contract['seed']=dict(created_at=1,logical_requests=0,transport_attempts=0,boundary=False,budget_stop=False,requests={});contract['gate']={}
   (out/'contract.json').write_bytes(b'{}');(out/'receipts').mkdir()
   for task,year in zip(contract['tasks'],[2025,2012]):
    body=helper.body(year);p=root/(str(year)+'.json');p.write_bytes(body);r=dict(task=task,status='ACQUIRED',record=dict(path=p.name,sha256=digest(body)))
    (out/'receipts'/(task['id']+'.json')).write_bytes(encoded(r))
   c=dict(years=list(range(2013,2026)),batch_id='test')
   original=old_snapshot(root,c,out,contract,'run');streamed=snapshot(root,c,out,contract,'verify');self.assertEqual(original,streamed)
if __name__=='__main__':unittest.main()
