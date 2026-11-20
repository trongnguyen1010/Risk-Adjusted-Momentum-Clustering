"""R2-15 rationale provenance, counter-evidence, replay and Peers mutation."""
import copy
import json
import unittest

from test_d_ass_01_rules import fixture, cell
from delta_t1.experiments.assessment.rationale import build_rationale
from delta_t1.experiments.assessment.rules_common import load_policy


def peer_data(values=(.1,.2,.3), metric='roa', **changes):
    financial = metric in load_policy()['features']['financial']
    result = dict(peer_basis='SAME_A_AND_B_PIT', membership_verified=True,
                  comparability_verified=True, evidence_ref='fixture://peers/verified',
                  members=[dict(ticker='P'+str(i),cell=cell(v,period='2024' if financial else '2025-12-31'))
                           for i,v in enumerate(values)])
    result.update(changes)
    return {metric:result}


def rows(result):
    return result['drivers']+result['risks']+result['counter_evidence']+result['context_evidence']


class RationaleTests(unittest.TestCase):
    def test_all_feature_claims_have_traceable_schema_and_fixed_templates(self):
        result=build_rationale(**fixture())
        self.assertEqual(result['verdict'],'RESEARCH_FAVORABLE')
        self.assertFalse(result['publishable'])
        for row in rows(result):
            for key in ('rule_id','metric','value','status','unit','period','evidence_ref','direction','template_id','text'):
                self.assertIsNotNone(row[key],key)
            self.assertIn(row['metric'],load_policy()['features']['whitelist'])
            self.assertTrue(row['evidence_ref'].startswith('fixture://'))
        json.dumps(result,ensure_ascii=False,allow_nan=False)

    def test_caution_retains_supporting_counter_evidence(self):
        args=fixture();args['financial_features']['cfo_to_ni']['value']=-1
        result=build_rationale(**args)
        self.assertEqual(result['verdict'],'CAUTION')
        self.assertIn('cfo_to_ni',[r['metric'] for r in result['risks']])
        self.assertIn('roa',[r['metric'] for r in result['counter_evidence']])

    def test_mixed_momentum_signs_are_not_hidden_when_no_full_adverse_rule(self):
        args=fixture();args['market_features']['mom_63']['value']=-.2
        result=build_rationale(**args)
        self.assertEqual(result['verdict'],'WATCH')
        self.assertIn('mom_63',[r['metric'] for r in result['risks']])
        self.assertTrue(result['counter_evidence'])

    def test_watch_warning_and_metadata_warning_keep_their_roles(self):
        args=fixture();args['financial_features']['current_ratio']['value']=.8
        result=build_rationale(**args)
        self.assertIn('WATCH_CURRENT_RATIO',[r['rule_id'] for r in result['risks']])
        args['liquidity']['value']='ILLIQUID'
        result=build_rationale(**args)
        self.assertEqual(result['verdict'],'CAUTION')
        self.assertEqual(result['metadata_warnings'][0]['rule_id'],'MARKET_ILLIQUID')
        self.assertFalse(any(r['metric']=='liquidity_flag' for r in rows(result)))
        self.assertTrue(result['metadata_warnings'][0]['qualifiers'][0]['evidence_ref'])

    def test_imputed_cfo_preserves_lineage_and_never_claims_observed_cfo(self):
        args=fixture();args['financial_features']['cfo_to_ni'].update(status='IMPUTED_MEDIAN',cell_lineage_verified=True)
        result=build_rationale(**args)
        row=next(r for r in result['drivers'] if r['metric']=='cfo_to_ni')
        self.assertEqual(row['status'],'IMPUTED_MEDIAN')
        self.assertFalse(row['is_observed'])
        self.assertIn('không phải số liệu quan sát',row['text'])
        self.assertTrue(row['cell_lineage_verified'])
        self.assertTrue(any(q.get('metadata')=='ni_denominator' for q in row['qualifiers']))

    def test_nonpositive_ni_ratio_is_context_without_sign_inference(self):
        args=fixture();args['denominator']['value']=-100
        args['financial_features']['cfo_to_ni']['value']=-2
        result=build_rationale(**args)
        row=next(r for r in result['context_evidence'] if r['metric']=='cfo_to_ni')
        self.assertEqual(row['template_id'],'CONTEXT_ONLY')
        self.assertFalse(any(r['metric']=='cfo_to_ni' for r in result['risks']))

    def test_zero_is_neutral_optional_missing_not_zero(self):
        args=fixture();args['financial_features']['cfo_to_ni']['value']=0
        del args['financial_features']['current_ratio']
        result=build_rationale(**args)
        self.assertEqual(result['verdict'],'WATCH')
        self.assertIn('CFO_ZERO',[r['template_id'] for r in result['context_evidence']])
        self.assertFalse(any(r['metric']=='current_ratio' for r in rows(result)))
        self.assertIn('current_ratio',[r['metric'] for r in result['skipped_evidence']])

    def test_missing_refs_bad_status_nonfinite_never_become_claims(self):
        for change in ({'evidence_ref':None},{'source_hash_verified':False},
                       {'value':float('nan')},{'status':'NOT_APPLICABLE'}, {'value':True}):
            args=fixture();args['financial_features']['gross_margin'].update(change)
            result=build_rationale(**args)
            self.assertFalse(any(r['metric']=='gross_margin' for r in rows(result)))
            json.dumps(result,allow_nan=False)

    def test_outside_whitelist_and_free_text_inputs_are_rejected(self):
        args=fixture();args['market_features']['future_return']=cell(.2)
        with self.assertRaises(ValueError):build_rationale(**args)
        args=fixture();args['peers']={'future_return':{}}
        with self.assertRaises(ValueError):build_rationale(**args)
        args=fixture();args['text']='buy now'
        with self.assertRaises(TypeError):build_rationale(**args)

    def test_peers_mutation_changes_g4_but_never_assessment(self):
        args=fixture();args.update(target_ticker='AAA',peers=peer_data())
        first=build_rationale(**args)
        args['peers']=peer_data((-.3,-.2,-.1))
        second=build_rationale(**args)
        self.assertEqual(first['assessment'],second['assessment'])
        self.assertNotEqual(first['peers'],second['peers'])
        self.assertEqual(first['peers'][0]['relative_position'],'BELOW')
        self.assertEqual(second['peers'][0]['relative_position'],'ABOVE')
        args['peers']=None
        self.assertEqual(first['assessment'],build_rationale(**args)['assessment'])

    def test_below_three_has_no_median_but_keeps_individual_evidence(self):
        args=fixture();args.update(target_ticker='AAA',peers=peer_data((.1,.2)))
        row=build_rationale(**args)['peers'][0]
        self.assertEqual(row['peer_count'],2)
        self.assertEqual(row['status'],'BELOW_MINIMUM')
        self.assertIsNone(row['peer_median']);self.assertIsNone(row['p25']);self.assertIsNone(row['p75'])
        self.assertEqual(len(row['members']),2)

    def test_peer_self_duplicates_invalid_units_and_future_periods_excluded(self):
        args=fixture();args.update(target_ticker='AAA',peers=peer_data())
        members=args['peers']['roa']['members']
        members += [dict(ticker=' aaa ',cell=cell(999)),dict(ticker='P0',cell=cell(888)),
                    dict(ticker='BAD',cell=cell(.1,unit='percent')),
                    dict(ticker='FUTURE',cell=cell(.1,period='2025')),
                    dict(ticker='MISSING',cell=cell(None))]
        row=build_rationale(**args)['peers'][0]
        self.assertEqual(row['peer_count'],2)
        self.assertEqual([m['ticker'] for m in row['members']],['P1','P2'])
        self.assertIsNone(row['peer_median'])

    def test_peer_basis_requires_correct_model_and_comparability_receipts(self):
        for change in ({'peer_basis':'SAME_B_ONLY'}, {'membership_verified':False},
                       {'comparability_verified':False}, {'evidence_ref':''}):
            args=fixture();args.update(target_ticker='AAA',peers=peer_data(**change))
            self.assertEqual(build_rationale(**args)['peers'][0]['status'],'UNVERIFIED_PEERS')
        args=fixture();args.update(target_ticker='AAA',peers=peer_data(peer_basis='SAME_B_PIT'))
        self.assertEqual(build_rationale(**args)['peers'][0]['status'],'VALID')
        args=fixture();args.update(target_ticker='AAA',peers=peer_data(metric='mom_63',peer_basis='SAME_A_V4'))
        self.assertEqual(build_rationale(**args)['peers'][0]['status'],'VALID')

    def test_missing_target_b_pit_does_not_use_a_only_peers(self):
        args=fixture();args['context']['metadata']['b_pit_label_valid']=False
        args.update(target_ticker='AAA',peers=peer_data())
        result=build_rationale(**args)
        self.assertEqual(result['verdict'],'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['peers'][0]['status'],'TARGET_LABELS_REQUIRED')
        self.assertFalse(result['peers'][0]['members'])
        self.assertFalse(result['drivers'])

    def test_peer_imputed_preserves_status_and_requires_peer_approval(self):
        args=fixture();args.update(target_ticker='AAA',peers=peer_data())
        args['peers']['roa']['members'][0]['cell'].update(status='IMPUTED_MEDIAN',cell_lineage_verified=True)
        result=build_rationale(**args)
        self.assertEqual(result['peers'][0]['members'][0]['status'],'IMPUTED_MEDIAN')
        policy=copy.deepcopy(load_policy());policy['imputed_policy']['allowed_for_peers']=False;args['policy']=policy
        self.assertIsNone(build_rationale(**args)['peers'][0]['peer_median'])

    def test_all_eighteen_context_features_stay_within_whitelist(self):
        args=fixture();policy=load_policy()
        for name in policy['features']['market']:args['market_features'].setdefault(name,cell(.1,period='2025-12-31'))
        for name in policy['features']['financial']:args['financial_features'].setdefault(name,cell(.1))
        result=build_rationale(**args)
        self.assertEqual({r['metric'] for r in rows(result)},set(policy['features']['whitelist']))
        self.assertFalse(any(r['metric']=='ni_denominator' for r in rows(result)))

    def test_replay_member_order_independent_and_does_not_mutate_inputs(self):
        args=fixture();args.update(target_ticker='AAA',peers=peer_data())
        original=copy.deepcopy(args)
        first=build_rationale(**args)
        self.assertEqual(args,original)
        self.assertEqual(first,build_rationale(**args))
        args['peers']['roa']['members'].reverse()
        self.assertEqual(first,build_rationale(**args))

    def test_future_or_mismatched_source_context_emits_no_feature_claim(self):
        for key,value in (('usable_from_date','2026-01-03'),('model_fiscal_year',2023)):
            args=fixture();args['context'][key]=value
            args.update(target_ticker='AAA',peers=peer_data())
            result=build_rationale(**args)
            self.assertFalse(rows(result))
            self.assertEqual(result['peers'][0]['status'],'TARGET_CONTEXT_UNVERIFIED')
        args=fixture();args['context']['source_pins']['market_bundle']['actual_sha256']='b'*64
        self.assertFalse(rows(build_rationale(**args)))

    def test_wrong_target_evidence_period_is_not_used_in_claims_or_peers(self):
        args=fixture();args['financial_features']['gross_margin']['period']='2023'
        args.update(target_ticker='AAA',peers=peer_data(metric='gross_margin'))
        result=build_rationale(**args)
        self.assertFalse(any(row['metric']=='gross_margin' for row in rows(result)))
        self.assertEqual(result['peers'][0]['status'],'TARGET_EVIDENCE_UNUSABLE')

    def test_finite_extreme_peer_values_do_not_overflow_aggregates(self):
        args=fixture();args.update(target_ticker='AAA',peers=peer_data((-1e308,0,1e308)))
        result=build_rationale(**args)
        json.dumps(result,allow_nan=False)
        self.assertEqual(result['peers'][0]['peer_median'],0)

    def test_default_runtime_remains_disabled(self):
        args=fixture();del args['fixture_only']
        result=build_rationale(**args)
        self.assertFalse(result['publishable'])
        self.assertEqual(result['verdict'],'INSUFFICIENT_EVIDENCE')


if __name__=='__main__':unittest.main()
