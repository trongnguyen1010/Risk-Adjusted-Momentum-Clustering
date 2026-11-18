import copy,json,tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from delta_t1.ingestion.cafef_financial import digest,encoded
from delta_t1.experiments.financial_inventory_qa import validate_ownership,coverage_grid,field_presence,load_receipt,process_symbol,consolidate
from delta_t1.experiments.financial_acquisition_qa import classify_templates
from delta_t1.experiments.financial_history_batch_qa import diagnose

class InventoryTests(unittest.TestCase):
 def member(self):return dict(registry_id='R0',ticker='S0',exchange='HOSE',company_name='Công ty kiểm thử')
 def grid(self):
  rows=[]
  for y in range(2013,2026):
   for mode,quarters in [('NAM',[0]),('QUY',[1,2,3,4])]:
    for q in quarters:
     for s in ['CDKT','KQKD','LCTT']:rows.append(dict(symbol='S0',year=str(y),quarter=str(q),mode=mode,statement=s,status='NO_CANDIDATE_IN_ACQUIRED_PAGES',observed_groups='[]',numeric_cells='0',accepted='False',pit_ready='False'))
  rows.append(dict(symbol='S0',year='2012',quarter='0',mode='NAM',statement='CDKT',status='AUXILIARY_NOT_ACQUIRED',observed_groups='[]',numeric_cells='0',accepted='False',pit_ready='False'));return rows
 def receipt(self,root):
  task=dict(id='t',kind='REPORT',symbol='S0',statement='CDKT',mode='NAM',group='TN',page=1,url='https://example.com/exact')
  body=json.dumps(dict(isSuccess=True,value=dict(templace=[dict(code='TN',data=[dict(code='100',name='TÀI SẢN NGẮN HẠN')])],data=[dict(code='TN',data=[dict(symbol='S0',year=2025,quater=0,type='HK',data=[dict(code='100',value=123)])])]))).encode()
  (root/'raw.json').write_bytes(body);receipt=dict(task=task,status='ACQUIRED',record=dict(path='raw.json',sha256=digest(body)));(root/'receipts').mkdir();raw=encoded(receipt);(root/'receipts/t.json').write_bytes(raw)
  return ('receipts/t.json',digest(raw),task,None)
 def test_disjoint_cohort_union_must_equal_registry(self):
  r=[self.member(),dict(self.member(),registry_id='R1',ticker='S1')]
  self.assertEqual(len(validate_ownership(r,[['S0'],['S1']])),2)
  for cohorts in [[['S0']],[['S0'],['S0','S1']],[['S0'],['OTHER']]]:self.assertRaises(ValueError,validate_ownership,r,cohorts)
 def test_coverage_requires196_distinct_slots_not_just_date_range(self):
  rows=self.grid();self.assertEqual(len(coverage_grid(rows,'S0')),196)
  self.assertRaises(ValueError,coverage_grid,rows[:-1],'S0');self.assertRaises(ValueError,coverage_grid,rows+[rows[0]],'S0')
 def test_presence_keeps_provider_partitions_and_conflicting_values(self):
  row=dict(symbol='S0',year=2025,quarter=0,mode='NAM',provider_type='HK',field='net_revenue',value='10',source_path='raw',source_sha256='hash',raw_code='10',label='Revenue')
  result=field_presence([row,dict(row,value='11'),dict(row,provider_type='S',value='10')])
  self.assertEqual(len(result),2);self.assertEqual(sorted(x['distinct_value_count'] for x in result),[1,2]);self.assertTrue(all(x['accepted'] is False for x in result))
 def test_receipt_raw_and_shard_tampering_fail_closed(self):
  with tempfile.TemporaryDirectory() as f:
   root=Path(f);item=self.receipt(root);self.assertEqual(len(load_receipt(root,item)[1]),1)
   bad=(*item[:3],dict(sha256='bad',cells=1));self.assertRaises(ValueError,load_receipt,root,bad)
   wrong=copy.deepcopy(item[2]);wrong['symbol']='OTHER';self.assertRaises(ValueError,load_receipt,root,(item[0],item[1],wrong,None))
   (root/'raw.json').write_bytes(b'{}');self.assertRaises(ValueError,load_receipt,root,item)
 def test_symbol_checkpoint_preserves_no_acceptance_and_detects_source_change(self):
  with tempfile.TemporaryDirectory() as f:
   root=Path(f);item=self.receipt(root);out=root/'checkpoint'
   with ThreadPoolExecutor(max_workers=2) as pool:
    inv=process_symbol(root,out,self.member(),[item],self.grid(),[],[],'job','source',pool)
    again=process_symbol(root,out,self.member(),[item],self.grid(),[],[],'job','source',pool)
    self.assertEqual(inv,again);self.assertEqual(inv['diagnostic_template_family'],'UNKNOWN');self.assertFalse(inv['numeric_acceptance_allowed']);self.assertFalse(inv['pit_ready'])
    (root/'raw.json').write_bytes(b'changed');self.assertRaises(ValueError,process_symbol,root,out,self.member(),[item],self.grid(),[],[],'job','source',pool)
 def test_bank_and_unknown_templates_never_get_regular_semantic_aliases(self):
  row=dict(symbol='S0',statement='KQKD',group='KQKD',mode='NAM',year=2025,quarter=0,provider_type='HK',raw_code='10',label='Doanh thu thuần về bán hàng và cung cấp dịch vụ',value='123',mapping_status='UNIQUE_CODE_LABEL_CANDIDATE',value_status='NUMERIC_CANDIDATE',template_sha256='H',source_path='raw')
  refs=[dict(symbol='REF',proposed_company_type='Bank')];templates=[dict(task=dict(symbol='REF',statement='KQKD'),template_sha256=['H'])]
  for templates_used,kind in [(templates,'Bank'),([],'UNKNOWN')]:
   profiles,_=classify_templates([row],refs,templates_used);self.assertEqual(profiles[0]['proposed_company_type'],kind)
   findings=diagnose([row],profiles,{'raw':{}},[]);self.assertEqual(findings['mapped'],[]);self.assertEqual(findings['arithmetic'],[])
 def test_consolidation_writes_sealed_csv_report_without_promoting_facts(self):
  with tempfile.TemporaryDirectory() as f:
   root=Path(f);item=self.receipt(root);job=root/'job';out=job/'symbols/R0'
   with ThreadPoolExecutor(max_workers=2) as pool:inv=process_symbol(root,out,self.member(),[item],self.grid(),[],[],'job','source',pool)
   result=consolidate(root,dict(report_root='report'),job,{},[inv],{'source':1},root/'status.json')
   self.assertEqual(result['symbols'],1);self.assertEqual(sum(result['coverage_statuses'].values()),196);self.assertFalse(result['numeric_acceptance_allowed']);self.assertFalse(result['pit_ready'])
   self.assertTrue((root/result['report']).exists());sealed=root/result['output'];manifest=json.loads((sealed/'manifest.json').read_bytes())
   self.assertTrue(all(digest((sealed/name).read_bytes())==sha for name,sha in manifest.items()));self.assertIn('company_name',(sealed/'symbols.csv').read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
