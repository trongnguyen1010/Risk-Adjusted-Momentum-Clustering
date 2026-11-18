import unittest
from delta_t1.experiments.financial_scale_analysis import candidate_math,hints


class ScaleAnalysisTests(unittest.TestCase):
    def rows(self):
        return [dict(symbol='NEW',year=2025,field=k,candidate_values=[str(v)]) for k,v in dict(
            current_assets=50,current_liabilities=30,total_assets=100,total_liabilities=60,
            total_equity=40,retained_earnings=10,profit_before_tax=10,interest_expense=2).items()]

    def test_arithmetic_is_diagnostic_and_missing_eps_not_zero(self):
        r=candidate_math(self.rows(),'NEW',2025,'Regular')
        self.assertEqual(float(r['z_arithmetic']),6.3944)
        self.assertFalse(r['financial_features_allowed']);self.assertIsNone(r['recomputed_eps'])
        self.assertIsNone(r['f_full_value']);self.assertIsNone(r['m_value'])

    def test_missing_conflict_and_bad_balance_do_not_compute_z(self):
        a=self.rows();a[0]['candidate_values']=['50','51']
        b=self.rows();b[2]['candidate_values']=['105']
        for rows in [a,b,self.rows()[:-1]]:self.assertIsNone(candidate_math(rows,'NEW',2025,'Regular')['z_arithmetic'])

    def test_sector_not_generic_and_hint_not_acceptance(self):
        self.assertEqual(candidate_math(self.rows(),'NEW',2025,'Bank')['status'],'SECTOR_TEMPLATE_REQUIRED')
        r=hints([dict(pdf_page=3,text='BẢNG CÂN ĐỐI KẾ TOÁN hợp nhất, đơn vị: VND')])
        self.assertEqual(r[0]['categories'],['BALANCE','UNITS'])


if __name__=='__main__':unittest.main()
