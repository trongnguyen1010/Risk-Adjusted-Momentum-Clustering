import unittest
from delta_t1.experiments.financial_reference_flow import evaluate, DILUTION_RULE, eps_case_as_of, evaluate_f_score


class FinancialFlowTests(unittest.TestCase):
    def setUp(self):
        values={'eps_adjusted_earnings_numerator':1000,'weighted_average_basic_shares':3,'weighted_average_diluted_shares':3}
        self.task=dict(symbol='FPT',year=2024,task='EPS_RECOMPUTE',inputs=[dict(field=f,year=2024) for f in values])
        self.rows=[]
        for field,value in values.items():
            fact=dict(symbol='FPT',year=2024,item=field,value=value,unit='VND' if 'numerator' in field else 'SHARES',
                      statement_scope='CONSOLIDATED',accounting_framework='VAS',period_start='2024-01-01',period_end='2024-12-31',
                      pdf_sha256='a',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',derivation=dict(rule=DILUTION_RULE))
            ref=dict(fact=fact,publication=dict(publication_date='2025-03-14'),usable_from_date='2025-03-17',
                     date_pit_status='DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR')
            self.rows.append(dict(symbol='FPT',year=2024,field=field,references=[ref]))
        self.checks=[dict(field=f,passed=True,candidate=dict(value=value)) for f,value in
                     [('eps_adjusted_earnings_numerator',1000),('weighted_average_basic_shares',3),('vendor_basic_eps',333)]]
        self.case=dict(pdf_sha256='a')

    def test_publication_same_day_blocked_next_session_computes(self):
        old=evaluate(self.task,self.rows,self.case,self.checks,'2025-03-14')
        self.assertIsNone(old['value'])
        result=evaluate(self.task,self.rows,self.case,self.checks,'2025-03-17')
        self.assertEqual(result['status'],'REFERENCE_QA_PASS')
        self.assertTrue(result['qa']['passed'])
        self.assertFalse(result['research_ready'])

    def test_mixed_vintages_ocr_error_and_unproved_dilution_are_blocked(self):
        self.rows[0]['references'][0]['fact']['pdf_sha256']='b'
        self.assertEqual(evaluate(self.task,self.rows,self.case,self.checks,'2025-03-17')['status'],'BLOCKED_JOINT_VINTAGE_OR_TEMPLATE')
        self.rows[0]['references'][0]['fact']['pdf_sha256']='a'
        self.checks[0]['passed']=False
        self.assertIsNone(evaluate(self.task,self.rows,self.case,self.checks,'2025-03-17')['value'])
        self.checks[0]['passed']=True
        self.rows[2]['references'][0]['fact']['derivation']={}
        self.assertEqual(evaluate(self.task,self.rows,self.case,self.checks,'2025-03-17')['status'],'BLOCKED_DILUTION_SEMANTICS')

    def test_known_unmapped_revision_blocks_old_result_only_after_release(self):
        self.case['revision_alerts']=[dict(task='EPS_RECOMPUTE',usable_from_date='2026-03-20')]
        self.assertEqual(evaluate(self.task,self.rows,self.case,self.checks,'2025-03-17')['status'],'REFERENCE_QA_PASS')
        result=evaluate(self.task,self.rows,self.case,self.checks,'2026-03-20')
        self.assertEqual(result['status'],'BLOCKED_LATER_REVISION_NOT_MAPPED')
        self.assertIsNone(result['value'])

    def test_revised_eps_template_is_selected_only_after_release(self):
        import copy
        for row in self.rows:
            ref=copy.deepcopy(row['references'][0])
            ref['fact']['pdf_sha256']='revised'
            if row['field'].endswith('shares'):ref['fact']['value']=4
            ref['publication']['publication_date']='2026-03-19'
            ref['usable_from_date']='2026-03-20'
            row['references'].append(ref)
        cases=[self.case,dict(pdf_sha256='revised')]
        for date,expected in [('2026-03-19','a'),('2026-03-20','revised')]:
            case=eps_case_as_of(self.task,self.rows,cases,date)
            self.assertEqual(case['pdf_sha256'],expected)
        revised_checks=[dict(field=f,passed=True,candidate=dict(value=v)) for f,v in
                        [('eps_adjusted_earnings_numerator',1000),('weighted_average_basic_shares',4),('vendor_basic_eps',250)]]
        result=evaluate(self.task,self.rows,cases[1],revised_checks,'2026-03-20')
        self.assertEqual(result['rounded']['annual_basic_eps_reference'],'250')
        self.assertIsNone(evaluate(self.task,self.rows,cases[1],revised_checks,'2026-03-19')['value'])

    def test_fscore_missing_and_unreviewed_vintage_cannot_create_total(self):
        result=evaluate_f_score('FPT',2024,self.rows,{'2024':'a'},'2025-03-17')
        self.assertEqual(result['known_signals'],0)
        self.assertIsNone(result['value'])
