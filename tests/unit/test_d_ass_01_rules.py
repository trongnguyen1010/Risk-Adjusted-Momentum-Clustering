"""R2-14: eligibility/priority matrix; explicit non-publishable fixtures."""
import copy
import itertools
import json
import unittest

from delta_t1.experiments.assessment.rules_common import load_policy
from delta_t1.experiments.assessment.verdict import evaluate_verdict


def cell(value, period='2024', unit='ratio', **changes):
    result = dict(value=value, status='OK', period=period, unit=unit,
                  evidence_ref='fixture://verified/cell', source_hash_verified=True,
                  provenance_verified=True)
    result.update(changes)
    return result


def fixture():
    policy = load_policy()
    context = dict(assessment_context='SIMULATED_AS_OF', as_of='2026-01-02',
                   required_price_session='2025-12-31', last_price_date='2025-12-31',
                   required_market_snapshot_date='2025-12-31', market_snapshot_date='2025-12-31',
                   usable_from_date='2025-04-01', model_cutoff='2025-06-30',
                   fiscal_year=2024, latest_usable_fiscal_year=2024, model_fiscal_year=2024,
                   market_model='A_V4', financial_model='B_PIT_ENRICHED',
                   metadata={k: True for k in policy['eligibility']['required_metadata']},
                   metadata_evidence_refs={k: 'fixture://gate/'+k for k in policy['eligibility']['required_metadata']},
                   source_pins={k: dict(expected_sha256='a'*64, actual_sha256='a'*64,
                                       verified=True, evidence_ref='fixture://pin/'+k)
                                for k in policy['eligibility']['required_source_pins']})
    return dict(market_features={k: cell(0.1, period='2025-12-31') for k in ('mom_21','mom_63','mom_126','mom_252')},
                financial_features={k: cell(v) for k,v in dict(roa=.1, net_margin=.1, cfo_to_ni=1,
                                       gross_margin=.2, current_ratio=1.2, revenue_growth=.1).items()},
                liquidity=cell('LIQUID', period='2025-12-31', unit='category'),
                denominator=cell(100, unit='VND'), ratio_validity=cell(True, unit='boolean'),
                context=context, fixture_only=True)


class VerdictTests(unittest.TestCase):
    def test_verdict_matrix_and_first_match_priority(self):
        # 3 trend states x 3 profitability states x 3 CFO signs x 2 liquidity x 2 watch.
        for trend, profit, cfo, illiquid, watch in itertools.product((-1,0,1),(-1,0,1),(-1,0,1),(False,True),(False,True)):
            with self.subTest(case=(trend,profit,cfo,illiquid,watch)):
                args=fixture()
                for item in args['market_features'].values(): item['value']=trend
                for key in ('roa','net_margin'): args['financial_features'][key]['value']=profit
                args['financial_features']['cfo_to_ni']['value']=cfo
                args['financial_features']['current_ratio']['value']=.5 if watch else 1.2
                args['liquidity']['value']='ILLIQUID' if illiquid else 'LIQUID'
                expected='CAUTION' if illiquid or cfo<0 or (trend<0 and profit<0) else 'RESEARCH_FAVORABLE' if trend>0 and profit>0 and cfo>0 and not watch else 'WATCH'
                result=evaluate_verdict(**args)
                self.assertEqual(result['verdict'],expected)
                self.assertTrue(result['eligibility_pass'])
                self.assertFalse(result['publishable'])
                self.assertFalse(result['verdict_issued'])

    def test_insufficient_precedes_major_warning(self):
        args=fixture();args['liquidity']['value']='ILLIQUID'
        args['financial_features']['roa']['value']=None
        result=evaluate_verdict(**args)
        self.assertEqual(result['verdict'],'INSUFFICIENT_EVIDENCE')
        self.assertTrue(result['verdict_matches']['CAUTION'])

    def test_each_required_gate_and_receipt_must_be_verified(self):
        for key in load_policy()['eligibility']['required_metadata']:
            for value in (False, None, 1, 'true'):
                args=fixture();args['context']['metadata'][key]=value
                self.assertEqual(evaluate_verdict(**args)['verdict'],'INSUFFICIENT_EVIDENCE',key)
            args=fixture();del args['context']['metadata_evidence_refs'][key]
            self.assertFalse(evaluate_verdict(**args)['eligibility_pass'])

    def test_all_source_pins_require_hash_match_proof_and_reference(self):
        for name in load_policy()['eligibility']['required_source_pins']:
            for change in ({'actual_sha256':'b'*64},{'actual_sha256':'bad'}, {'verified':1}, {'evidence_ref':''}):
                args=fixture();args['context']['source_pins'][name].update(change)
                self.assertFalse(evaluate_verdict(**args)['eligibility_pass'],name)
            args=fixture();del args['context']['source_pins'][name]
            self.assertFalse(evaluate_verdict(**args)['eligibility_pass'])

    def test_future_dates_and_wrong_expected_sessions_block(self):
        for key,value in (('model_cutoff','2026-01-03'), ('usable_from_date','2026-01-03'),
                          ('last_price_date','2025-12-30'), ('market_snapshot_date','2025-11-28'),
                          ('as_of','invalid'), ('model_cutoff',None)):
            args=fixture();args['context'][key]=value
            self.assertFalse(evaluate_verdict(**args)['eligibility_pass'],key)

    def test_simulated_scope_is_fixed_and_context_is_required(self):
        for key,value in (('as_of','2026-01-01'), ('required_price_session','2025-12-30'),
                          ('required_market_snapshot_date','2025-11-28'), ('assessment_context','OTHER')):
            args=fixture();args['context'][key]=value
            self.assertFalse(evaluate_verdict(**args)['eligibility_pass'])
        args=fixture();args['context']=None
        self.assertEqual(evaluate_verdict(**args)['verdict'],'INSUFFICIENT_EVIDENCE')

    def current(self, as_of):
        args=fixture();args['context'].update(assessment_context='CURRENT_AS_OF',as_of=as_of,
                                             monthly_release_schedule_accepted=True,
                                             monthly_release_schedule_ref='fixture://accepted/monthly')
        return args

    def test_staleness_boundary_is_inclusive_and_not_fixed_session_count(self):
        self.assertTrue(evaluate_verdict(**self.current('2026-06-30'))['eligibility_pass'])
        result=evaluate_verdict(**self.current('2026-07-01'))
        self.assertFalse(result['eligibility_pass'])
        self.assertIn('FINANCIAL_STALE',[i['reason'] for i in result['eligibility_issues']])

    def test_exact_usable_date_and_cutoff_are_allowed(self):
        args=fixture()
        args['context']['usable_from_date']=args['context']['model_cutoff']='2026-01-02'
        self.assertTrue(evaluate_verdict(**args)['eligibility_pass'])

    def test_current_context_requires_accepted_monthly_schedule(self):
        for key,value in (('monthly_release_schedule_accepted',False),('monthly_release_schedule_ref','')):
            args=self.current('2026-01-15');args['context'][key]=value
            self.assertFalse(evaluate_verdict(**args)['eligibility_pass'])
        args=self.current('2026-01-15')
        self.assertTrue(evaluate_verdict(**args)['eligibility_pass'])

    def test_latest_fy_missing_model_never_falls_back(self):
        for changes in ({'model_fiscal_year':None}, {'model_fiscal_year':2023},
                        {'latest_usable_fiscal_year':2025}, {'fiscal_year':True},
                        {'financial_model':'BASELINE'}, {'market_model':'A_LEGACY'}):
            args=fixture();args['context'].update(changes)
            self.assertEqual(evaluate_verdict(**args)['verdict'],'INSUFFICIENT_EVIDENCE')

    def test_matching_cells_from_wrong_snapshot_or_fiscal_year_cannot_pass(self):
        args=fixture()
        for item in args['market_features'].values():item['period']='2025-11-28'
        args['liquidity']['period']='2025-11-28'
        self.assertFalse(evaluate_verdict(**args)['eligibility_pass'])
        args=fixture()
        for item in args['financial_features'].values():item['period']='2023'
        args['denominator']['period']=args['ratio_validity']['period']='2023'
        self.assertFalse(evaluate_verdict(**args)['eligibility_pass'])

    def test_optional_missing_skips_checks_without_changing_verdict(self):
        args=fixture()
        for key in ('gross_margin','current_ratio','revenue_growth'):del args['financial_features'][key]
        result=evaluate_verdict(**args)
        self.assertEqual(result['verdict'],'RESEARCH_FAVORABLE')
        self.assertEqual(len(result['financial']['optional_issues']),3)

    def test_peers_missing_extreme_or_mutated_never_change_verdict(self):
        baseline=evaluate_verdict(**fixture())
        for peers in (None, [], {'median':-1e99}, {'median':1e99}, {'status':'MISSING_INPUT'}):
            args=fixture();args['peers']=peers
            self.assertEqual(evaluate_verdict(**args),baseline)

    def test_nonpositive_ni_skips_cfo_unknown_ni_blocks(self):
        for value in (0,-100):
            args=fixture();args['denominator']['value']=value;args['ratio_validity']={}
            del args['financial_features']['cfo_to_ni']
            self.assertEqual(evaluate_verdict(**args)['verdict'],'WATCH')
        args=fixture();args['denominator']['value']=None
        self.assertEqual(evaluate_verdict(**args)['verdict'],'INSUFFICIENT_EVIDENCE')

    def test_approved_imputed_requires_lineage_preserves_status(self):
        args=fixture();args['financial_features']['cfo_to_ni'].update(status='IMPUTED_MEDIAN',cell_lineage_verified=True)
        result=evaluate_verdict(**args)
        self.assertEqual(result['verdict'],'RESEARCH_FAVORABLE')
        self.assertEqual(result['financial']['rules'][2]['evidence'][0]['status'],'IMPUTED_MEDIAN')
        args['financial_features']['cfo_to_ni']['cell_lineage_verified']=False
        self.assertEqual(evaluate_verdict(**args)['verdict'],'INSUFFICIENT_EVIDENCE')

    def test_production_disabled_by_default_even_with_favorable_fixture(self):
        args=fixture();del args['fixture_only']
        result=evaluate_verdict(**args)
        self.assertEqual(result['verdict'],'INSUFFICIENT_EVIDENCE')
        self.assertFalse(result['publishable'])
        self.assertTrue(any(i['field']=='activation' for i in result['eligibility_issues']))

    def test_setting_runtime_flag_alone_does_not_bypass_activation(self):
        args=fixture();args['fixture_only']=False
        policy=copy.deepcopy(load_policy());policy['runtime_enabled']=True
        args['policy']=policy
        self.assertFalse(evaluate_verdict(**args)['publishable'])

    def test_fixed_priority_and_explicit_fixture_type(self):
        args=fixture();policy=copy.deepcopy(load_policy());policy['verdicts']['priority'].reverse();args['policy']=policy
        with self.assertRaises(ValueError):evaluate_verdict(**args)
        args=fixture();args['fixture_only']='true'
        with self.assertRaises(ValueError):evaluate_verdict(**args)

    def test_replay_deterministic_and_input_not_mutated(self):
        args=fixture();original=copy.deepcopy(args)
        result=evaluate_verdict(**args)
        self.assertEqual(result,evaluate_verdict(**args))
        self.assertEqual(args,original)
        json.dumps(result,allow_nan=False)


if __name__ == '__main__':
    unittest.main()
