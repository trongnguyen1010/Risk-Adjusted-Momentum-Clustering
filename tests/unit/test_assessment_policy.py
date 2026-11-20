"""R2-11 policy contract tests; expression evaluation here is a fixture interpreter, not a production engine."""
import json
import operator
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MARKET = {'mom_21','mom_63','mom_126','mom_252','vol_63','downside_vol_63','mdd_126','beta_126','liquidity_21'}
FINANCIAL = {'roe','roa','gross_margin','net_margin','debt_to_equity','current_ratio','asset_turnover','revenue_growth','cfo_to_ni'}


def evaluate(expression, policy, values, metadata, states):
    if 'all' in expression:
        return all(evaluate(e, policy, values, metadata, states) for e in expression['all'])
    if 'any' in expression:
        return any(evaluate(e, policy, values, metadata, states) for e in expression['any'])
    if 'not' in expression:
        return not evaluate(expression['not'], policy, values, metadata, states)
    if 'always' in expression:
        return expression['always']
    if 'rule_ref' in expression:
        rule = policy['rules']
        for key in expression['rule_ref'].split('.'):
            rule = rule[key]
        return evaluate(rule, policy, values, metadata, states)
    if 'state' in expression:
        return states[expression['state']]
    actual = values.get(expression['feature']) if 'feature' in expression else metadata.get(expression['metadata'])
    if actual is None:
        return False  # skipped check; never substitute zero.
    return {'>': operator.gt, '<': operator.lt, '==': operator.eq}[expression['op']](actual, expression['value'])


def verdict(policy, values, metadata, *, eligible=True):
    for code in policy['verdicts']['priority']:
        if evaluate(policy['verdicts']['conditions'][code], policy, values, metadata, {'eligibility_pass': eligible}):
            return code
    raise AssertionError('Missing default verdict')


class AssessmentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'configs/product/assessment_policy_v1.json').read_text(encoding='utf-8'))
        self.values = dict(mom_21=0.1,mom_63=0.2,mom_126=0.3,mom_252=-0.1,
                           roa=0.1,net_margin=0.1,cfo_to_ni=1)
        self.meta = dict(ni_denominator_sign='POSITIVE',ni_denominator_observed=True,
                         cfo_ratio_valid=True,liquidity_flag='LIQUID')

    def test_policy_version_scope_and_real_runtime_remain_explicitly_not_activated(self):
        p = self.policy
        self.assertEqual((p['policy_id'],p['version']), ('D-ASS-01','1.0.0'))
        self.assertEqual(p['status'], 'POLICY_CODED_TESTED_ONLY')
        self.assertFalse(p['runtime_enabled'])
        self.assertFalse(p['integration']['current_builder_reads_policy'])
        self.assertFalse(p['integration']['activation_enforcement_verified'])
        self.assertEqual(p['scope']['as_of'], '2026-01-02')
        self.assertEqual(p['scope']['required_price_session'], '2025-12-31')
        self.assertEqual(p['scope']['financial_stale_months'], 18)
        self.assertEqual(p['scope']['market_frequency'], 'MONTHLY')
        self.assertIsNone(p['scope']['fixed_session_age_limit'])
        self.assertFalse(p['scope']['cluster_id_is_rank'])
        self.assertFalse(p['scope']['model_selection_uses_portfolio_performance'])

    def test_whitelist_is_exactly_18_unique_features_and_roles_partition_it(self):
        f = self.policy['features']
        self.assertEqual(set(f['market']), MARKET)
        self.assertEqual(set(f['financial']), FINANCIAL)
        self.assertEqual(len(f['whitelist']), 18)
        self.assertEqual(set(f['whitelist']), MARKET | FINANCIAL)
        required = set(f['mandatory']); conditional = set(f['conditional_mandatory']); optional = set(f['optional'])
        self.assertEqual(required, {'mom_21','mom_63','mom_126','mom_252','roa','net_margin'})
        self.assertEqual(conditional, {'cfo_to_ni'})
        self.assertFalse(required & optional or required & conditional or optional & conditional)
        self.assertEqual(required | conditional | optional, MARKET | FINANCIAL)
        self.assertFalse(f['missing_is_zero'])
        self.assertEqual(f['optional_missing_action'], 'SKIP_CORRESPONDING_CHECK')
        self.assertEqual(set(self.policy['evidence']['allowed_features']), MARKET | FINANCIAL)

    def test_all_rule_features_and_references_are_closed_and_do_not_use_peers_or_scores(self):
        seen_features = set()
        def walk(expression):
            if isinstance(expression, list):
                for item in expression: walk(item)
            elif isinstance(expression, dict):
                if 'feature' in expression:
                    self.assertIn(expression['feature'], MARKET | FINANCIAL)
                    seen_features.add(expression['feature'])
                    self.assertIn(expression['op'], ('>','<','=='))
                if 'rule_ref' in expression:
                    rule = self.policy['rules']
                    for key in expression['rule_ref'].split('.'): rule = rule[key]
                    self.assertIsInstance(rule, dict)
                for key,value in expression.items():
                    self.assertNotIn(key, ('score','penalty','future_return','cluster_rank','peer_count'))
                    walk(value)
        walk(self.policy['rules']); walk(self.policy['verdicts']['conditions'])
        self.assertTrue(seen_features <= MARKET | FINANCIAL)
        self.assertIsNone(self.policy['verdicts']['total_score'])
        self.assertIsNone(self.policy['verdicts']['penalty'])

    def test_four_codes_and_priority_match_table_8_3(self):
        expected = ['INSUFFICIENT_EVIDENCE','CAUTION','RESEARCH_FAVORABLE','WATCH']
        self.assertEqual(self.policy['verdicts']['priority'], expected)
        self.assertEqual(set(self.policy['verdicts']['conditions']), set(expected))
        self.assertEqual(set(self.policy['verdicts']['labels_vi']), set(expected))
        self.assertEqual(self.policy['verdicts']['labels_vi']['RESEARCH_FAVORABLE'], 'Đáng cân nhắc đầu tư')
        self.assertTrue(self.policy['verdicts']['first_match_wins'])
        self.assertEqual(verdict(self.policy,self.values,self.meta), 'RESEARCH_FAVORABLE')
        self.assertEqual(verdict(self.policy,self.values,dict(self.meta,liquidity_flag='ILLIQUID')), 'CAUTION')
        self.assertEqual(verdict(self.policy,self.values,dict(self.meta,liquidity_flag='ILLIQUID'),eligible=False),
                         'INSUFFICIENT_EVIDENCE')

    def test_market_strict_zero_boundaries_and_symmetric_negative_condition(self):
        for feature in ('mom_63','mom_126'):
            with self.subTest(feature=feature):
                values=dict(self.values,**{feature:0})
                self.assertEqual(verdict(self.policy,values,self.meta), 'WATCH')
        values=dict(self.values,mom_21=0,mom_252=0)
        self.assertEqual(verdict(self.policy,values,self.meta), 'WATCH')
        values=dict(self.values,mom_21=-1,mom_63=-1,mom_126=-1,mom_252=0,roa=-0.1,net_margin=-0.1)
        metadata=dict(self.meta,ni_denominator_sign='NEGATIVE',cfo_ratio_valid=False)
        self.assertEqual(verdict(self.policy,values,metadata), 'CAUTION')
        self.assertTrue(evaluate(self.policy['rules']['market']['adverse'],self.policy,values,metadata,{}))

    def test_one_watch_warning_blocks_favorable_but_equal_threshold_does_not(self):
        for feature,value in (('gross_margin',-0.01),('current_ratio',0.99),('revenue_growth',-0.01)):
            with self.subTest(feature=feature):
                self.assertEqual(verdict(self.policy,dict(self.values,**{feature:value}),self.meta), 'WATCH')
        equality=dict(self.values,gross_margin=0,current_ratio=1,revenue_growth=0)
        self.assertEqual(verdict(self.policy,equality,self.meta), 'RESEARCH_FAVORABLE')
        self.assertEqual(verdict(self.policy,dict(equality,current_ratio=None),self.meta), 'RESEARCH_FAVORABLE')
        self.assertEqual(verdict(self.policy,dict(equality,current_ratio=0),self.meta), 'WATCH')

    def test_cfo_zero_unknown_or_nonpositive_denominator_cannot_assert_positive_cashflow(self):
        self.assertEqual(verdict(self.policy,dict(self.values,cfo_to_ni=0),self.meta), 'WATCH')
        for metric in ('roa','net_margin'):
            self.assertEqual(verdict(self.policy,dict(self.values,**{metric:0}),self.meta), 'WATCH')
        self.assertEqual(verdict(self.policy,dict(self.values,cfo_to_ni=-1),self.meta), 'CAUTION')
        for sign in ('ZERO','NEGATIVE','UNKNOWN'):
            metadata=dict(self.meta,ni_denominator_sign=sign)
            self.assertFalse(evaluate(self.policy['rules']['financial']['cash_positive'],self.policy,self.values,metadata,{}))
            self.assertFalse(evaluate(self.policy['rules']['financial']['cash_negative'],self.policy,
                                      dict(self.values,cfo_to_ni=-1),metadata,{}))
        for change in (dict(ni_denominator_observed=False),dict(cfo_ratio_valid=False)):
            self.assertFalse(evaluate(self.policy['rules']['financial']['cash_positive'],self.policy,
                                      self.values,dict(self.meta,**change),{}))
        self.assertEqual(self.policy['features']['conditional_mandatory']['cfo_to_ni']['unknown_denominator_action'],
                         'INSUFFICIENT_EVIDENCE')

    def test_missing_mandatory_and_latest_fy_model_cannot_fall_back(self):
        e = self.policy['eligibility']
        self.assertEqual(e['mandatory_unusable_action'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(e['latest_fy_without_model_action'], 'INSUFFICIENT_EVIDENCE')
        self.assertFalse(e['allow_fallback_to_older_fy'])
        self.assertFalse(e['allow_fallback_to_baseline'])
        self.assertIn('trading_calendar',e['required_source_pins'])
        self.assertEqual(e['accept_only_statuses'],['OK','IMPUTED_MEDIAN'])
        for key in ('a_label_valid','b_pit_label_valid','required_price_session_matches','liquidity_flag_present',
                    'latest_usable_fiscal_year_selected','b_pit_cutoff_pass'):
            self.assertIn(key,e['required_metadata'])
        self.assertEqual(verdict(self.policy,dict(self.values,roa=None),self.meta,eligible=False), 'INSUFFICIENT_EVIDENCE')

    def test_user_approved_imputed_cells_keep_provenance_and_do_not_gain_observed_status(self):
        p = self.policy['imputed_policy']
        self.assertEqual(p['approval']['status'], 'APPROVED_BY_USER')
        self.assertEqual(set(p['approval']['scope']), {'RULEBOOK','PEERS'})
        self.assertTrue(p['allowed_for_rulebook'] and p['allowed_for_peers'])
        self.assertTrue(p['preserve_status'] and p['preserve_cell_provenance'])
        self.assertTrue(p['require_verified_source_hash_and_cell_lineage'])
        self.assertTrue(p['cfo_sign_requires_observed_positive_denominator'])
        self.assertFalse(p['treat_as_observed'])
        self.assertFalse(p['describe_median_as_observed_company_cfo'])
        self.assertFalse(p['add_score_or_penalty'] or p['allow_new_imputation'])
        self.assertIn('IMPUTED_MEDIAN',self.policy['eligibility']['accept_only_statuses'])
        self.assertEqual(p['if_approval_missing']['mandatory'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(p['if_approval_missing']['optional'], 'SKIP_CORRESPONDING_CHECK')
        self.assertEqual(p['if_approval_missing']['peers'], 'EXCLUDE_CELL')

    def test_peer_policy_uses_three_and_correct_feature_specific_expansion(self):
        p = self.policy['peers']
        self.assertEqual(p['min_valid_peers'],3)
        self.assertEqual(p['preferred_basis'],'SAME_A_AND_B_PIT')
        self.assertEqual(p['fallback_basis'],dict(financial='SAME_B_PIT',market='SAME_A_V4'))
        self.assertTrue(p['exclude_self'] and p['deduplicate'])
        self.assertEqual(p['required_target_labels'],['A_V4','B_PIT'])
        self.assertFalse(p['allow_a_only_target_fallback'])
        self.assertFalse(p['missing_peers_block_verdict'] or p['peer_values_change_verdict'])
        for count in (0,1,2,3,100):
            self.assertEqual(verdict(self.policy,self.values,dict(self.meta,peer_count=count)), 'RESEARCH_FAVORABLE')

    def test_evidence_and_activation_gates_do_not_claim_real_s1_acceptance(self):
        p = self.policy
        self.assertEqual(set(p['evidence']['required_fields']),
                         {'rule_id','metric','value','status','unit','period','evidence_ref'})
        self.assertFalse(p['evidence']['free_text_without_evidence_allowed'])
        self.assertFalse(p['evidence']['predict_future_returns'])
        self.assertIn('S1_REAL_PINNED_INPUTS_AND_PEERS_ACCEPTED',p['activation']['required_gates'])
        self.assertTrue(p['activation']['current_blockers'])
        self.assertTrue(p['activation']['do_not_rebuild_or_publish_real_verdicts'])


if __name__ == '__main__':
    unittest.main()
