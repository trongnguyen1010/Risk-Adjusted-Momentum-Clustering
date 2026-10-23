import unittest
from delta_t1.experiments.financial_compute_first import metric_row,classify_api_task,summarize_symbols
from delta_t1.experiments.financial_cafef_pilot import FAMILIES
class ComputeFirstTests(unittest.TestCase):
 def metric(self,symbol='AAA',year=2025,family='EPS',value='10',cohort='A',kind='ANNUAL',scope='CONSOLIDATED'):
  r=metric_row(dict(symbol=symbol,year=year,family=family,value=value,status='REFERENCE'), 'test','evidence',cohort=cohort,kind=kind,scope=scope);r['id']='id';return r
 def test_alias_absence_is_unknown_mapping_not_raw_missing_or_zero(self):
  row=classify_api_task('AAA',2025,'EPS',{},'Regular',[])
  self.assertEqual(row['status'],'API_INPUT_QUALITY_NOT_YET_ESTABLISHED');self.assertIsNone(row['numeric_value']);self.assertIn('weighted_average_basic_shares@2025',row['not_evaluated_by_current_alias_catalogue']);self.assertFalse(row['financial_features_allowed'])
 def test_nonregular_models_held_but_valuation_not_mislabeled_inapplicable(self):
  self.assertEqual(classify_api_task('AAA',2025,'F_SCORE',{},'Bank',[])['status'],'MODEL_APPLICABILITY_REVIEW_REQUIRED')
  self.assertEqual(classify_api_task('AAA',2025,'PE',{},'Bank',[])['status'],'API_INPUT_QUALITY_NOT_YET_ESTABLISHED')
 def test_multiple_provider_values_never_count_as_ready(self):
  r=classify_api_task('AAA',2025,'Z_SCORE',{(2025,'total_assets'):[dict(distinct_value_count='2')]},'Regular',[])
  self.assertIn('total_assets@2025',r['conflicting_aliases']);self.assertIsNone(r['numeric_value'])
 def test_six_families_must_share_same_cohort_year_and_scope(self):
  rows=[self.metric(family=f) for f in FAMILIES];s=summarize_symbols(['AAA'],rows)[0];self.assertTrue(s['has_six_family_reference_cohort']);self.assertFalse(s['full_market10y_six_family_reference_history'])
  for field,value in [('cohort_id','B'),('year',2024),('input_scope','COMPANY_REPORTED'),('period_kind','YTD9')]:
   changed=[dict(r) for r in rows];changed[-1][field]=value;self.assertFalse(summarize_symbols(['AAA'],changed)[0]['has_six_family_reference_cohort'])
 def test_duplicate_dates_vintages_and_missing_values_do_not_inflate_symbol_count(self):
  rows=[self.metric(),self.metric(cohort='B'),self.metric(value=None)]
  result=summarize_symbols(['AAA','BBB'],rows);self.assertEqual(result[0]['reference_families'],1);self.assertEqual(result[1]['reference_families'],0)
 def test_period_eps_never_satisfies_annual_task(self):
  r=classify_api_task('AAA',2025,'EPS',{},'Regular',[self.metric(kind='YTD9')]);self.assertEqual(r['reference_ids'],[])
 def test_invalid_value_rejected_and_zero_retained(self):
  for value in [True,'NaN','Infinity']:self.assertRaises(ValueError,self.metric,value=value)
  self.assertEqual(self.metric(value='0')['value'],'0')
if __name__=='__main__':unittest.main()
