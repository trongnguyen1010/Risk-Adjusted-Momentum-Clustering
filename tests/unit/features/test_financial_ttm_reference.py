import copy
import unittest
from decimal import Decimal
from delta_t1.features.financial_ttm_reference import reported_ttm, reported_ttm_valuation, REGISTRY


class TtmReferenceTests(unittest.TestCase):
    def inputs(self):
        common=dict(symbol='X',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',
            numerator_unit='VND',share_unit='SHARES',statement_scope='CONSOLIDATED',
            accounting_framework='VAS',share_basis_id='BONUS_RESTATED',
            deduction_policy='ACTUAL_REPORTED_DEDUCTION',reported_deduction=0)
        periods=dict(
            fy=dict(common,period_start='2025-01-01',period_end='2025-12-31',parent_profit=1000,
                reported_eps_numerator=1000,weighted_basic_shares=100,usable_from_date='2026-03-20'),
            current_ytd=dict(common,period_start='2026-01-01',period_end='2026-06-30',parent_profit=600,
                reported_eps_numerator=600,weighted_basic_shares=100,usable_from_date='2026-08-24'),
            prior_ytd=dict(common,period_start='2025-01-01',period_end='2025-06-30',parent_profit=400,
                reported_eps_numerator=400,weighted_basic_shares=100,usable_from_date='2025-08-21'))
        bridge=dict(parent_earnings_unchanged=True,h1_parent_profit_comparison_equal=True,usable_from_date='2026-08-24')
        return periods,bridge

    def test_hand_calculated_exact_year_and_no_mutation(self):
        p,b=self.inputs();old=copy.deepcopy(p)
        r=reported_ttm(p,b,'2026-08-24')
        self.assertEqual(Decimal(r['value']),12)
        self.assertEqual(r['calendar_days'],dict(fy=365,current_ytd=181,prior_ytd=181,ttm=365))
        self.assertEqual(r['trailing_start'],'2025-07-01')
        self.assertEqual(p,old)

    def test_share_days_not_sum_of_eps_or_current_share_substitution(self):
        p,b=self.inputs();p['current_ytd']['weighted_basic_shares']=200
        r=reported_ttm(p,b,'2026-08-24')
        expected=Decimal(1200)/(Decimal(100)*184+Decimal(200)*181)*365
        self.assertAlmostEqual(Decimal(r['value']),expected,places=24)
        self.assertNotEqual(Decimal(r['value']),Decimal(10+3-4))
        self.assertNotEqual(Decimal(r['value']),Decimal(1200)/200)

    def test_reported_unknown_deduction_stays_null(self):
        p,b=self.inputs()
        for key in ['current_ytd','prior_ytd']:
            p[key].update(deduction_policy='NOT_ESTIMATED_NOT_DEDUCTED',reported_deduction=None)
        r=reported_ttm(p,b,'2026-08-24')
        self.assertEqual(Decimal(r['value']),12)
        self.assertIsNone(r['strict_normalized_ttm_eps'])
        p['current_ytd']['reported_deduction']=0
        self.assertIsNone(reported_ttm(p,b,'2026-08-24')['value'])

    def test_publication_date_and_scope_bridge_fail_closed(self):
        p,b=self.inputs()
        self.assertIsNone(reported_ttm(p,b,'2026-08-21')['value'])
        b['parent_earnings_unchanged']=False
        self.assertIsNone(reported_ttm(p,b,'2026-08-24')['value'])
        b['parent_earnings_unchanged']=True;b['usable_from_date']='2026-08-25'
        self.assertIsNone(reported_ttm(p,b,'2026-08-24')['value'])

    def test_incompatible_period_share_unit_identity_and_missing_inputs(self):
        for change in [dict(period_start='2026-02-01'),dict(period_end='2026-09-30'),
                dict(share_basis_id='NOT_RESTATED'),dict(numerator_unit='THOUSAND_VND'),
                dict(symbol='OTHER'),dict(reported_eps_numerator=None),dict(usable_from_date='2026-05-01')]:
            p,b=self.inputs();p['current_ytd'].update(change)
            self.assertIsNone(reported_ttm(p,b,'2026-08-24')['value'])

    def test_bad_denominators_and_reporting_precision(self):
        for value in [None,0,-1,True,'NaN','100.5']:
            p,b=self.inputs();p['current_ytd']['weighted_basic_shares']=value
            self.assertIsNone(reported_ttm(p,b,'2026-08-24')['value'])
        p,b=self.inputs();p['prior_ytd']['weighted_basic_shares']=1000
        self.assertIsNone(reported_ttm(p,b,'2026-08-24')['value'])

    def test_leap_year_calendar_days(self):
        p,b=self.inputs()
        for key,year in [('fy',2024),('prior_ytd',2024),('current_ytd',2025)]:
            end='12-31' if key=='fy' else '06-30'
            p[key].update(period_start=f'{year}-01-01',period_end=f'{year}-{end}',usable_from_date=f'{year+1}-03-20')
        r=reported_ttm(p,b,'2026-08-24')
        self.assertEqual(r['calendar_days'],dict(fy=366,current_ytd=181,prior_ytd=182,ttm=365))
        self.assertEqual(Decimal(r['value']),12)

    def test_reference_valuation_and_registry_cannot_promote(self):
        p,b=self.inputs();r=reported_ttm(p,b,'2026-08-24')
        v=reported_ttm_valuation(120,r,1000,100)
        self.assertEqual(Decimal(v['pe']),10);self.assertEqual(Decimal(v['pb']),12)
        self.assertIsNone(v['strict_event_adjusted_pb']);self.assertFalse(v['research_ready'])
        self.assertIsNone(reported_ttm_valuation(120,r,1000,True)['pb'])
        self.assertIsNone(reported_ttm_valuation(120,{},1000,100)['pe'])
        with self.assertRaises(ValueError):REGISTRY.require_cluster_eligible(REGISTRY.names())
