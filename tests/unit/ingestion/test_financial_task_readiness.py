import unittest
from delta_t1.ingestion.financial_task_readiness import matrix,ANNUAL_TASKS
class TaskReadinessTests(unittest.TestCase):
    def test_complete_annual_eps_does_not_imply_pe_or_pit(self):
        rows=[dict(symbol='FPT',year=2025,field=f,evidence_status='DOCUMENT_VALUE_VERIFIED_PIT_PENDING')
              for f,_ in ANNUAL_TASKS['EPS_RECOMPUTE']]
        r=matrix(dict(rows=rows,financial_features_allowed=False),['FPT'],[2025])
        eps=next(x for x in r['rows'] if x['task']=='EPS_RECOMPUTE')
        pe=next(x for x in r['rows'] if x['task']=='PE')
        self.assertTrue(eps['annual_input_presence_complete']);self.assertFalse(eps['task_ready'])
        self.assertIn('COMPATIBLE_EPS_TTM_NOT_ANNUAL_EPS',pe['semantic_blockers'])
        self.assertTrue(all(x['computed_value'] is None for x in r['rows']))
    def test_prior_year_and_unmapped_inputs_are_explicit(self):
        r=matrix(dict(rows=[],financial_features_allowed=False),['FPT'],[2021])
        f=next(x for x in r['rows'] if x['task']=='F_SCORE')
        self.assertIn(2019,{x['year'] for x in f['inputs']})
        self.assertTrue(all(x['evidence_status']=='MISSING_SEMANTIC_MAPPING' for x in f['inputs']))
