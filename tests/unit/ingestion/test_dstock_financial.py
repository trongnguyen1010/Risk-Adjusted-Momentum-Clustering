import json,unittest
from decimal import Decimal
from delta_t1.ingestion.dstock_financial import SCHEMA,vector,parse_page,url

class DStockTests(unittest.TestCase):
 def models(self):return {code:[dict(codeList='AAA',modelType=1,note='TEST')] for code in SCHEMA}
 def row(self,value=0,code=11000):return dict(code='AAA',itemCode=code,modelType=1,numericValue=value,fiscalDate='2024-12-31',reportType='ANNUAL')
 def test_explicit_zero_is_retained_but_absent_and_null_are_missing(self):
  v=vector([self.row(0),self.row(None,12700)],'AAA',2024,self.models())
  self.assertEqual(v['values'],{'current_assets':'0'})
 def test_no_sign_transformation(self):
  v=vector([self.row(-10,22100)],'AAA',2024,self.models());self.assertEqual(v['values']['cost_of_goods_sold'],'-10')
 def test_duplicate_even_equal_is_held(self):
  self.assertIn('DUPLICATE_PROVIDER_KEY',vector([self.row(),self.row()],'AAA',2024,self.models())['reasons'])
 def test_foreign_membership_is_held(self):
  m=self.models();m[11000][0]['codeList']='BBB'
  self.assertIn('MODEL_MEMBERSHIP_OR_SCOPE_AMBIGUOUS',vector([self.row()],'AAA',2024,m)['reasons'])
 def test_decimal_wire_precision(self):
  raw=b'{"data":[{"code":"AAA","reportType":"ANNUAL","fiscalDate":"2024-12-31","numericValue":123456789012345678.0}],"currentPage":1,"totalPages":1,"totalElements":1,"size":2000}'
  self.assertEqual(parse_page(raw,['AAA'],2024,1)['data'][0]['numericValue'],Decimal('123456789012345678'))
 def test_wrong_period_rejected(self):
  payload=dict(data=[dict(code='AAA',reportType='QUARTER',fiscalDate='2024-12-31')],currentPage=1,totalPages=1,totalElements=1,size=2000)
  with self.assertRaises(ValueError):parse_page(json.dumps(payload),['AAA'],2024,1)
 def test_unbounded_page_rejected(self):
  with self.assertRaises(ValueError):parse_page(json.dumps(dict(data=[],currentPage=1,totalPages=10,totalElements=0,size=2000)),['AAA'],2024,1)
 def test_query_bounded(self):
  with self.assertRaises(ValueError):url(['AAA']*6,2024)
  self.assertIn('page=2',url(['AAA'],2024,2))
 def test_missing_is_not_replaced(self):self.assertEqual(vector([],'AAA',2024,self.models())['values'],{})
 def test_nonfinite_rejected(self):self.assertIn('NONFINITE',vector([self.row('NaN')],'AAA',2024,self.models())['reasons'])
if __name__=='__main__':unittest.main()
