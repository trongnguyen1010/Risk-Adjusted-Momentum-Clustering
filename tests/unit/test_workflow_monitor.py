import json,tempfile,threading,unittest
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from delta_t1.product.monitor import WorkflowMonitor
from delta_t1.product.server import make_handler

class MonitorTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.qa=self.root/'data/financial/history_inventory1522_qa_v1';self.acq=self.root/'data/financial/history_acquisition_overnight_v2';self.qa.mkdir(parents=True);self.acq.mkdir(parents=True)
  self.write(self.qa/'pipeline-status.json',dict(stage='RUNNING_SYMBOL_QA',completed=5,total=10,last_symbol='FPT'))
  self.write(self.acq/'pipeline-status.json',dict(stage='COMPLETE_CURRENT_REGISTRY_TASK_ACCOUNTING',partitions=10))
  self.monitor=WorkflowMonitor(self.root)
 def tearDown(self):self.temp.cleanup()
 def write(self,path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf-8')
 def test_true_progress_and_read_only_projection(self):
  before=(self.qa/'pipeline-status.json').read_bytes();s=self.monitor.snapshot();self.assertEqual(s['qa']['percent'],50);self.assertEqual(s['qa']['last_symbol'],'FPT');self.assertEqual(s['acquisition']['percent'],100);self.assertTrue(s['read_only']);self.assertEqual(s['downloads'],{});self.assertEqual(before,(self.qa/'pipeline-status.json').read_bytes())
 def test_partial_write_preserves_last_good_and_shows_warning(self):
  self.monitor.snapshot();(self.qa/'pipeline-status.json').write_bytes(b'{incomplete');s=self.monitor.snapshot();self.assertEqual(s['qa']['completed'],5);self.assertTrue(any(w['using_last_good'] for w in s['warnings']))
 def test_held_status_uses_last_checkpoint_not_zero_or_fake_complete(self):
  self.write(self.qa/'pipeline-status.json',dict(stage='HELD_REVIEW_REQUIRED',reason='hash differs'))
  (self.qa/'worker.log').write_text(json.dumps(dict(event='INVENTORY_QA_CHECKPOINT',completed=4,total=10,last_symbol='VNM'))+'\n',encoding='utf-8')
  s=self.monitor.snapshot();self.assertEqual(s['qa']['completed'],4);self.assertEqual(s['qa']['percent'],40);self.assertFalse(s['qa']['complete']);self.assertEqual(s['qa']['reason'],'hash differs')
 def test_output_path_cannot_escape_inventory_root(self):
  self.write(self.qa/'pipeline-status.json',dict(output='../../outside',stage='COMPLETE_OFFLINE_INVENTORY_QA_DIAGNOSTICS'))
  self.assertIsNone(self.monitor.artifact('summary'));self.assertIsNone(self.monitor.artifact('../secrets'))
 def test_tail_is_bounded_and_excludes_partial_prefix(self):
  p=self.qa/'worker.log';p.write_bytes(b'X'*10000+b'\nlast complete\n');self.assertEqual(self.monitor.tail(p,100),['last complete'])
 def test_http_serves_dashboard_json_and_rejects_writes(self):
  web=self.root/'web';(web/'monitor').mkdir(parents=True);(web/'monitor/index.html').write_text('<title>Monitor</title>',encoding='utf-8')
  server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(None,web,self.monitor));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_address[1])
  try:
   with urlopen(base+'/monitor/') as response:self.assertIn(b'Monitor',response.read())
   with urlopen(base+'/api/v1/monitor') as response:self.assertEqual(json.load(response)['qa']['completed'],5)
   for path,method,code in [('/api/v1/monitor','POST',405),('/api/v1/monitor/files/../../../secret','GET',404),('/api/v1/companies','GET',404)]:
    with self.assertRaises(HTTPError) as error:urlopen(Request(base+path,data=b'{}' if method=='POST' else None,method=method))
    self.assertEqual(error.exception.code,code)
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
