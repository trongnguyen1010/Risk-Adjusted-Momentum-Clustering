"""R2-12: strict momentum truth table, missing evidence, liquidity and policy-driven components."""
import copy
import itertools
import json
from pathlib import Path
import unittest

from delta_t1.experiments.assessment.rules_common import load_policy, evaluate_expression
from delta_t1.experiments.assessment.rules_market import MOMENTUM, evaluate_market


def cell(value, *, status='OK', unit='ratio', period='2025-12-31', evidence_ref='fixture://a-v4/2025-12-31'):
    return dict(value=value,status=status,unit=unit,period=period,evidence_ref=evidence_ref,
                source_hash_verified=True,provenance_verified=True)


def features(values=(0.1,0.2,0.3,0.4)):
    return {name:cell(value) for name,value in zip(MOMENTUM,values)}


def liquidity(value='LIQUID'):
    return cell(value,unit='category',evidence_ref='fixture://a-v4/liquidity')


class MarketRuleTests(unittest.TestCase):
    def test_all_81_sign_combinations_match_symmetric_policy_and_zero_is_not_positive(self):
        for m21,m63,m126,m252 in itertools.product((-0.1,0,0.1),repeat=4):
            with self.subTest(values=(m21,m63,m126,m252)):
                result=evaluate_market(features((m21,m63,m126,m252)),liquidity=liquidity())
                favorable=m63>0 and m126>0 and (m21>0 or m252>0)
                adverse=m63<0 and m126<0 and (m21<0 or m252<0)
                expected='FAVORABLE' if favorable else 'ADVERSE' if adverse else 'MIXED'
                self.assertEqual(result['market_condition'],expected)
                self.assertEqual(result['status'],'PASS')
                self.assertIs(result['major_warning'],False)
                self.assertFalse(result['verdict_issued'])

    def test_either_short_or_long_momentum_can_complete_favorable_condition(self):
        for values in ((-0.1,0.2,0.3,0.1),(0.1,0.2,0.3,-0.1)):
            self.assertEqual(evaluate_market(features(values),liquidity=liquidity())['market_condition'],'FAVORABLE')
        self.assertEqual(evaluate_market(features((0.1,0,0.3,0.1)),liquidity=liquidity())['market_condition'],'MIXED')

    def test_each_missing_mandatory_momentum_is_unknown_even_when_other_or_branch_is_true(self):
        for name in MOMENTUM:
            for absent in (False,True):
                with self.subTest(name=name,absent=absent):
                    data=features()
                    if absent:del data[name]
                    else:data[name]=cell(None)
                    result=evaluate_market(data,liquidity=liquidity())
                    self.assertEqual(result['market_condition'],'UNKNOWN')
                    self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
                    self.assertTrue(all(r['matched'] is None for r in result['rules'][:2]))
                    issue=next(i for i in result['eligibility_issues'] if i['field']==name)
                    self.assertEqual(issue['reason'],'MISSING_INPUT')

    def test_unusable_status_is_not_converted_to_zero_or_observed(self):
        for status in ('MISSING_INPUT','NOT_APPLICABLE','CONFLICT','UNVERIFIED'):
            data=features();data['mom_63']=cell(1,status=status)
            result=evaluate_market(data,liquidity=liquidity())
            self.assertEqual(result['market_condition'],'UNKNOWN')
            evidence=next(e for e in result['rules'][0]['evidence'] if e['metric']=='mom_63')
            self.assertEqual(evidence['status'],status)
            self.assertFalse(evidence['usable'])
            self.assertFalse(evidence['is_observed'])

    def test_nan_infinity_boolean_and_numeric_strings_are_unknown_and_json_safe(self):
        for value in (float('nan'),float('inf'),float('-inf'),True,False,'0.1'):
            with self.subTest(value=value):
                data=features();data['mom_126']=cell(value)
                result=evaluate_market(data,liquidity=liquidity())
                self.assertEqual(result['market_condition'],'UNKNOWN')
                self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
                json.dumps(result,allow_nan=False)

    def test_missing_or_unverified_evidence_blocks_component_without_invented_reference(self):
        for key in ('unit','period','evidence_ref','source_hash_verified','provenance_verified','status'):
            with self.subTest(key=key):
                data=features();del data['mom_21'][key]
                result=evaluate_market(data,liquidity=liquidity())
                self.assertEqual(result['market_condition'],'UNKNOWN')
                self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
                if key=='evidence_ref':
                    evidence=next(e for e in result['rules'][0]['evidence'] if e['metric']=='mom_21')
                    self.assertIsNone(evidence['evidence_ref'])

    def test_illiquid_is_major_warning_but_component_does_not_issue_final_verdict(self):
        result=evaluate_market(features(),liquidity=liquidity('ILLIQUID'))
        self.assertEqual(result['market_condition'],'FAVORABLE')
        self.assertIs(result['major_warning'],True)
        self.assertEqual(result['rules'][2]['status'],'MATCH')
        self.assertFalse(result['verdict_issued'])
        self.assertNotIn('verdict',result)

    def test_missing_or_unknown_liquidity_is_not_assumed_liquid(self):
        for flag in (None,{},liquidity(None),liquidity('UNKNOWN'),liquidity(True)):
            result=evaluate_market(features(),liquidity=flag)
            self.assertEqual(result['market_condition'],'FAVORABLE')
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
            self.assertIsNone(result['major_warning'])
            self.assertEqual(result['rules'][2]['status'],'UNKNOWN')

    def test_period_unit_or_liquidity_snapshot_mismatch_is_not_silently_mixed(self):
        for key,value in (('period','2025-11-28'),('unit','percent')):
            data=features();data['mom_21'][key]=value
            result=evaluate_market(data,liquidity=liquidity())
            self.assertEqual(result['market_condition'],'UNKNOWN')
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        flag=liquidity();flag['period']='2025-11-28'
        result=evaluate_market(features(),liquidity=flag)
        self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        self.assertIsNone(result['major_warning'])

    def test_optional_market_context_does_not_change_momentum_direction(self):
        before=evaluate_market(features(),liquidity=liquidity())
        data=features()
        for name in ('vol_63','downside_vol_63','mdd_126','beta_126','liquidity_21'):
            data[name]=cell(None,status='MISSING_INPUT')
        self.assertEqual(evaluate_market(data,liquidity=liquidity()),before)

    def test_financial_imputation_approval_does_not_authorize_filling_market_momentum(self):
        data=features();data['mom_21']=cell(0.1,status='IMPUTED_MEDIAN')
        result=evaluate_market(data,liquidity=liquidity())
        self.assertEqual(result['market_condition'],'UNKNOWN')
        self.assertEqual(result['eligibility_issues'][0]['reason'],'IMPUTATION_NOT_ALLOWED_FOR_MARKET')

    def test_cluster_id_and_future_return_cannot_be_used_as_signals(self):
        before=evaluate_market(features(),liquidity=liquidity())
        annotated=features()
        for item in annotated.values():item.update(cluster_id=999,future_return=999)
        flag=liquidity();flag['cluster_id']=-1
        self.assertEqual(evaluate_market(annotated,liquidity=flag),before)
        for extra in ('future_return','cluster_id','roe'):
            with self.assertRaisesRegex(ValueError,'Non-whitelisted'):
                evaluate_market(dict(features(),**{extra:cell(1)}),liquidity=liquidity())
        policy=copy.deepcopy(load_policy())
        policy['rules']['market']['favorable']['all'][0]['feature']='future_return'
        with self.assertRaisesRegex(ValueError,'four momentum'):
            evaluate_market(features(),liquidity=liquidity(),policy=policy)

    def test_policy_is_consumed_without_mutation_and_result_is_deterministic(self):
        policy=copy.deepcopy(load_policy());original=copy.deepcopy(policy)
        data=features();original_data=copy.deepcopy(data)
        first=evaluate_market(data,liquidity=liquidity(),policy=policy)
        self.assertEqual(first,evaluate_market(data,liquidity=liquidity(),policy=policy))
        self.assertEqual(policy,original);self.assertEqual(data,original_data)
        reordered=copy.deepcopy(policy)
        reordered['rules']['warnings']['major']['any'].reverse()
        self.assertEqual(first,evaluate_market(data,liquidity=liquidity(),policy=reordered))
        for expression in policy['rules']['market']['favorable']['all'][:2]:expression['value']=0.5
        self.assertEqual(evaluate_market(data,liquidity=liquidity(),policy=policy)['market_condition'],'MIXED')
        self.assertFalse(load_policy()['runtime_enabled'])

    def test_evidence_fields_are_complete_and_liquidity_remains_operational_metadata(self):
        result=evaluate_market(features(),liquidity=liquidity())
        for rule in result['rules'][:2]:
            self.assertEqual({e['metric'] for e in rule['evidence']},set(MOMENTUM))
            for item in rule['evidence']:
                self.assertTrue({'rule_id','metric','value','status','unit','period','evidence_ref'} <= item.keys())
                self.assertEqual(item['rule_id'],rule['rule_id'])
                self.assertEqual(item['validation_status'],'VALID')
        self.assertEqual(result['rules'][2]['evidence'],[])
        qualifier=result['rules'][2]['qualifiers'][0]
        self.assertEqual(qualifier['metadata'],'liquidity_flag')
        self.assertNotIn('metric',qualifier)

    def test_three_valued_helper_does_not_treat_unknown_as_numeric_zero(self):
        cells={'mom_21':dict(usable=False,value=None)}
        expression=dict(feature='mom_21',op='<',value=1)
        self.assertIsNone(evaluate_expression(expression,cells))
        self.assertIsNone(evaluate_expression({'not':expression},cells))
        self.assertIs(evaluate_expression({'any':[{'always':True},expression]},cells),True)
        self.assertIs(evaluate_expression({'all':[{'always':False},expression]},cells),False)


if __name__ == '__main__':
    unittest.main()
