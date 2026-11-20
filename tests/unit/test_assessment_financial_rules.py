"""R2-13: profitability, CFO conditional denominator, warnings and approved imputed lineage."""
import copy
import itertools
import json
import unittest

from delta_t1.experiments.assessment.rules_common import load_policy
from delta_t1.experiments.assessment.rules_financial import evaluate_financial


def cell(value,status='OK',unit='ratio',period='2024',**changes):
    result=dict(value=value,status=status,unit=unit,period=period,evidence_ref='fixture://financial/FY2024',
                source_hash_verified=True,provenance_verified=True)
    result.update(changes)
    return result


def features():
    return dict(roa=cell(0.1),net_margin=cell(0.1),cfo_to_ni=cell(1),
                gross_margin=cell(0.2),current_ratio=cell(1.2),revenue_growth=cell(0.1))


def ni(value=100,**changes):return cell(value,unit='VND',**changes)
def validity(value=True,**changes):return cell(value,unit='boolean',**changes)


class FinancialRuleTests(unittest.TestCase):
    def evaluate(self,data=None,denominator=None,ratio=None,policy=None):
        return evaluate_financial(features() if data is None else data,
                                  denominator=ni() if denominator is None else denominator,
                                  ratio_validity=validity() if ratio is None else ratio,policy=policy)

    def test_all_27_profit_and_cash_sign_combinations_obey_strict_thresholds(self):
        for roa,margin,cfo in itertools.product((-0.1,0,0.1),repeat=3):
            with self.subTest(values=(roa,margin,cfo)):
                data=features();data.update(roa=cell(roa),net_margin=cell(margin),cfo_to_ni=cell(cfo))
                result=self.evaluate(data)
                expected='ADVERSE' if cfo<0 or (roa<0 and margin<0) else 'FAVORABLE' if roa>0 and margin>0 and cfo>0 else 'MIXED'
                self.assertEqual(result['financial_condition'],expected)
                self.assertEqual(result['status'],'PASS')
                self.assertIs(result['major_warning'],cfo<0)
                self.assertIs(result['profitability_adverse'],roa<0 and margin<0)
                self.assertFalse(result['verdict_issued'])

    def test_cfo_zero_is_mixed_not_favorable_or_major_warning(self):
        data=features();data['cfo_to_ni']=cell(0)
        result=self.evaluate(data)
        self.assertEqual(result['cash_flow_sign'],'ZERO')
        self.assertEqual(result['financial_condition'],'MIXED')
        self.assertFalse(result['financial_favorable']);self.assertFalse(result['major_warning'])

    def test_each_single_watch_warning_blocks_financial_favorable(self):
        for feature,value in (('gross_margin',-0.01),('current_ratio',0.99),('revenue_growth',-0.01)):
            data=features();data[feature]=cell(value)
            result=self.evaluate(data)
            self.assertTrue(result['watch_warning'])
            self.assertFalse(result['financial_favorable'])
            self.assertEqual(result['financial_condition'],'MIXED')
            self.assertTrue(result['rules'][0]['matched'])  # base profitability/CFO remains favorable.
        data=features();data.update(cfo_to_ni=cell(-1),current_ratio=cell(0.5))
        result=self.evaluate(data)
        self.assertTrue(result['major_warning'] and result['watch_warning'])
        self.assertEqual(result['financial_condition'],'ADVERSE')

    def test_equal_watch_thresholds_do_not_trigger_and_missing_is_not_zero(self):
        data=features();data.update(gross_margin=cell(0),current_ratio=cell(1),revenue_growth=cell(0))
        result=self.evaluate(data)
        self.assertTrue(result['financial_favorable']);self.assertFalse(result['watch_warning'])
        for value in (None,):
            data['current_ratio']=cell(value)
            result=self.evaluate(data)
            self.assertTrue(result['financial_favorable']);self.assertFalse(result['watch_warning'])
            watch=next(r for r in result['rules'] if r['rule_id']=='WATCH_CURRENT_RATIO')
            self.assertEqual(watch['status'],'SKIPPED')
        data['current_ratio']=cell(0)
        self.assertTrue(self.evaluate(data)['watch_warning'])

    def test_nonpositive_observed_ni_never_infers_cfo_sign_from_ratio(self):
        for denominator in (0,-100):
            for cfo in (-1,0,1,None):
                data=features();data['cfo_to_ni']=cell(cfo)
                result=self.evaluate(data,denominator=ni(denominator),ratio=validity(False))
                self.assertEqual(result['status'],'PASS')
                self.assertEqual(result['cash_flow_sign'],'NOT_INFERRED')
                self.assertIs(result['major_warning'],False)
                self.assertFalse(result['financial_favorable'])
                self.assertTrue(all(r['status']=='SKIPPED' for r in result['rules'][2:4]))

    def test_unknown_unverified_or_imputed_ni_cannot_open_cfo_gate(self):
        for denominator in ({},ni(None),ni(float('nan')),ni(True),ni('100'),
                            ni(100,source_hash_verified=False),ni(100,provenance_verified=False),
                            ni(100,status='IMPUTED_MEDIAN',cell_lineage_verified=True)):
            data=features();data['cfo_to_ni']=cell(-1)
            result=self.evaluate(data,denominator=denominator)
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
            self.assertEqual(result['financial_condition'],'UNKNOWN')
            self.assertEqual(result['cash_flow_sign'],'UNKNOWN')
            self.assertIsNone(result['major_warning'])
            json.dumps(result,allow_nan=False)

    def test_positive_ni_requires_usable_cfo_and_verified_true_ratio_validity(self):
        for cfo in (cell(None),cell(float('inf')),cell(1,status='MISSING_INPUT'),cell('1'),cell(True)):
            data=features();data['cfo_to_ni']=cfo
            result=self.evaluate(data)
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
            self.assertEqual(result['cash_flow_sign'],'UNKNOWN')
        for ratio in ({},validity(None),validity(False),validity(1),validity('true'),
                      validity(True,source_hash_verified=False),validity(True,status='IMPUTED_MEDIAN')):
            result=self.evaluate(ratio=ratio)
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
            self.assertEqual(result['cash_flow_sign'],'UNKNOWN')
            self.assertIsNone(result['major_warning'])

    def test_missing_or_invalid_mandatory_profitability_blocks_component(self):
        for key in ('roa','net_margin'):
            for value in (None,float('nan'),float('-inf'),False,'0.1'):
                data=features();data[key]=cell(value)
                result=self.evaluate(data)
                self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
                self.assertEqual(result['financial_condition'],'UNKNOWN')
                self.assertIsNone(result['financial_favorable'])

    def test_missing_or_not_applicable_optional_checks_are_skipped(self):
        for key in ('gross_margin','current_ratio','revenue_growth'):
            for status in ('MISSING_INPUT','NOT_APPLICABLE','CONFLICT'):
                data=features();data[key]=cell(0,status=status)
                result=self.evaluate(data)
                self.assertEqual(result['status'],'PASS')
                self.assertTrue(result['financial_favorable'])
                self.assertFalse(result['watch_warning'])
                rule=next(r for r in result['rules'] if r['rule_id']=='WATCH_'+key.upper())
                self.assertEqual(rule['status'],'SKIPPED')
                self.assertEqual(rule['evidence'][0]['status'],status)

    def test_approved_imputed_profitability_and_cfo_preserve_status_and_lineage(self):
        for key in ('roa','net_margin','cfo_to_ni'):
            data=features();data[key]=cell(0.1,status='IMPUTED_MEDIAN',cell_lineage_verified=True)
            result=self.evaluate(data)
            self.assertEqual(result['status'],'PASS')
            self.assertTrue(result['financial_favorable'])
            evidence=next(e for e in result['rules'][0]['evidence'] if e['metric']==key)
            self.assertEqual(evidence['status'],'IMPUTED_MEDIAN')
            self.assertFalse(evidence['is_observed']);self.assertTrue(evidence['cell_lineage_verified'])
        data=features();data['cfo_to_ni']=cell(-1,status='IMPUTED_MEDIAN',cell_lineage_verified=True)
        result=self.evaluate(data)
        self.assertTrue(result['major_warning'])
        evidence=result['rules'][3]['evidence'][0]
        self.assertFalse(evidence['is_observed'])
        self.assertEqual(evidence['status'],'IMPUTED_MEDIAN')

    def test_imputed_requires_rulebook_approval_and_cell_level_lineage(self):
        data=features();data['roa']=cell(0.1,status='IMPUTED_MEDIAN')
        result=self.evaluate(data)
        self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        self.assertTrue(any(r['reason']=='UNVERIFIED_IMPUTATION_LINEAGE' for r in result['eligibility_issues']))
        data['roa']['cell_lineage_verified']=True
        for change in ('approval','lineage'):
            policy=copy.deepcopy(load_policy())
            if change=='approval':policy['imputed_policy']['approval']['scope']=['PEERS']
            else:data['roa']['provenance_verified']=False
            result=self.evaluate(data,policy=policy)
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        policy=copy.deepcopy(load_policy());policy['imputed_policy']['allowed_for_rulebook']=False
        data=features();data['gross_margin']=cell(-1,status='IMPUTED_MEDIAN',cell_lineage_verified=True)
        result=self.evaluate(data,policy=policy)
        self.assertEqual(result['status'],'PASS');self.assertTrue(result['financial_favorable'])
        self.assertFalse(result['watch_warning'])

    def test_fiscal_period_mismatches_block_mandatory_cfo_and_skip_optional(self):
        for which in ('roa','net_margin','cfo_to_ni','denominator','ratio'):
            data=features();denominator=ni();ratio=validity()
            if which=='denominator':denominator['period']='2023'
            elif which=='ratio':ratio['period']='2023'
            else:data[which]['period']='2023'
            result=self.evaluate(data,denominator=denominator,ratio=ratio)
            self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        data=features();data['gross_margin']=cell(-1,period='2023')
        result=self.evaluate(data)
        self.assertEqual(result['status'],'PASS');self.assertTrue(result['financial_favorable'])
        self.assertFalse(result['watch_warning'])
        # A missing ROA must not allow a CFO ratio from another FY to borrow NI sign.
        data=features();data['roa']=cell(None);data['cfo_to_ni']['period']='2023'
        result=self.evaluate(data)
        self.assertEqual(result['cash_flow_sign'],'UNKNOWN')
        self.assertIsNone(result['major_warning'])

    def test_denominator_is_operational_metadata_not_feature_19(self):
        result=self.evaluate()
        allowed=set(load_policy()['features']['financial'])
        for rule in result['rules']:
            for evidence in rule['evidence']:
                self.assertIn(evidence['metric'],allowed)
                self.assertTrue({'rule_id','metric','value','status','unit','period','evidence_ref'} <= evidence.keys())
            for qualifier in rule['qualifiers']:
                self.assertIn('metadata',qualifier);self.assertNotIn('metric',qualifier)
        qualifiers=result['rules'][2]['qualifiers']
        self.assertEqual({q['metadata'] for q in qualifiers},
                         {'ni_denominator','ni_denominator_sign','ni_denominator_observed','cfo_ratio_valid'})

    def test_optional_context_and_cluster_future_annotations_do_not_change_results(self):
        original=self.evaluate()
        data=features()
        for name in ('roe','debt_to_equity','asset_turnover'):data[name]=cell(999)
        self.assertEqual(self.evaluate(data),original)
        for item in data.values():item.update(cluster_id=0,future_return=-999)
        self.assertEqual(self.evaluate(data),original)
        for name in ('f_score','z_score','eps','cluster_id','future_return','ni_denominator'):
            with self.assertRaisesRegex(ValueError,'Non-whitelisted'):
                self.evaluate(dict(features(),**{name:cell(1)}))

    def test_policy_thresholds_and_input_are_not_hardcoded_or_mutated(self):
        data=features();data['current_ratio']=cell(1.5)
        policy=copy.deepcopy(load_policy());original=copy.deepcopy((data,policy))
        before=self.evaluate(data,policy=policy)
        self.assertEqual((data,policy),original)
        expression=next(e for e in policy['rules']['warnings']['watch']['any'] if e['feature']=='current_ratio')
        expression['value']=2
        self.assertTrue(self.evaluate(data,policy=policy)['watch_warning'])
        policy=copy.deepcopy(load_policy());policy['rules']['warnings']['watch']['any'].reverse()
        after=self.evaluate(data,policy=policy)
        self.assertEqual(after['financial_favorable'],before['financial_favorable'])
        self.assertEqual(after['watch_warning'],before['watch_warning'])
        self.assertEqual(self.evaluate(data),self.evaluate(data))

    def test_component_does_not_activate_builder_or_emit_final_verdict(self):
        result=self.evaluate()
        self.assertFalse(result['verdict_issued'])
        self.assertNotIn('verdict',result)
        self.assertFalse(load_policy()['runtime_enabled'])
        self.assertFalse(load_policy()['integration']['current_builder_reads_policy'])


if __name__ == '__main__':
    unittest.main()
