import unittest
from delta_t1.features.financial_exploratory import calculate_core,FEATURES
from delta_t1.experiments.financial_exploratory import eligible_periods,fit_year,validate_mode


class FinancialExploratoryTests(unittest.TestCase):
    def values(self):
        return dict(gross_profit='200',net_profit='-50',net_revenue='500',total_liabilities='400',total_assets='1000',current_assets='400',current_liabilities='200',operating_cash_flow='-200')

    def config(self):
        return dict(version='financial-exploratory-core-v1',owner_approval='EXPLORATORY_CORE_RATIOS_APPROVED_IN_CURRENT_THREAD',
            scope='NON_PIT_FINANCIAL_ONLY_REFERENCE',portfolio_evaluation_enabled=False,research_promotion_allowed=False,
            network_allowed=False,features=FEATURES,k=3,winsor_quantile=0,scaling='zscore',minimum_observations=30,
            seed=42,n_init=2,max_iter=100)

    def test_signed_profit_cashflow_and_explicit_ending_asset_basis(self):
        r=calculate_core(self.values());v=r['values']
        self.assertEqual(v['gross_margin'],0.4);self.assertEqual(v['net_margin'],-0.1)
        self.assertEqual(v['operating_cashflow_to_assets'],-0.2)
        self.assertEqual(v['asset_turnover_ending_assets'],0.5);self.assertFalse(r['strict_pit_ready'])

    def test_missing_and_nonpositive_denominator_not_imputed(self):
        for field in ['net_revenue','total_assets','current_liabilities']:
            v=self.values();v[field]='0';self.assertIsNone(calculate_core(v)['values'])
        v=self.values();del v['operating_cash_flow'];self.assertEqual(calculate_core(v)['status'],'MISSING_INPUTS')
        for value in [True,'NaN']:
            v=self.values();v['gross_profit']=value;self.assertIsNone(calculate_core(v)['values'])

    def test_multiple_provider_partitions_held_even_when_one_fails_qa(self):
        eligible,held=eligible_periods([dict(year=2025,quality_gate=True),dict(year=2025,quality_gate=False)])
        self.assertEqual(eligible,[]);self.assertIn('MULTIPLE_PROVIDER',held[0]['reason'])

    def test_explicit_reference_mode_refuses_research_or_portfolio_promotion(self):
        validate_mode(self.config())
        for field,value in [('scope','PIT'),('owner_approval','UNAPPROVED'),('research_promotion_allowed',True),('portfolio_evaluation_enabled',True)]:
            c=self.config();c[field]=value
            with self.assertRaises(ValueError):validate_mode(c)

    def test_actual_static_baseline_deterministic_and_tiny_sample_skipped(self):
        c=self.config();self.assertIn('SKIPPED',fit_year([],c)['status'])
        rows=[dict(symbol=str(i),registry_id=str(i).zfill(3),year=2025,**{f:(i//10)*10+(i%10)*0.01 for f in FEATURES}) for i in range(30)]
        first=fit_year(rows,c);second=fit_year(list(reversed(rows)),c)
        self.assertEqual(first['assignments'],second['assignments'])
        self.assertEqual(sorted(first['diagnostics']['cluster_sizes'].values()),[10,10,10])
        self.assertTrue(all(r['reference_only'] and not r['research_ready'] for r in first['assignments']))
