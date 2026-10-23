import unittest
from delta_t1.experiments.financial_history_stage_gate import decide


class StageGateTests(unittest.TestCase):
    def evidence(self):
        return dict(planned_tasks=1100,terminal_tasks=1100,transport_attempts=574,failed_requests=1,
            unfinished_requests=0,successful_network_responses=563,network_parse_errors=0,cached_parse_errors=0,
            conflicting_raw_keys=0,unexplained_orphans=0,required_audits=6,completed_audits=6,
            audit_issuer_modes_complete=True,quarantine_complete=True,row_shift_cohorts_held=True,
            accepted_api_candidates=0,source_boundary_errors=0,active_api_blocked=False,
            baseline_references=29,baseline_target=30,resume_verified=True,targeted_validation_verified=True,
            budget_stop=False,pdf_attempts=11,pdf_downloads=10,ocr_pages=99,max_pdf_ocr_pages=27,
            artifact_bytes=1_000_000,free_disk_bytes=90_000_000_000,campaign_anchor=1000,decision_at=1100)

    def test_candidate_gate_not_numeric_pit_or_universe_promotion(self):
        result=decide(self.evidence())
        self.assertTrue(result['pilot_history_engineering_pass'])
        self.assertEqual(result['max_total_issuers_next_stage'],20)
        self.assertTrue(result['selection_metadata_required'])
        for flag in ['batch20_started','numeric_acceptance_allowed','financial_features_allowed','research_ready','m3_ready']:
            self.assertFalse(result[flag])

    def test_missing_public_coverage_does_not_change_engineering_gate(self):
        e=self.evidence();e['known_missing_coverage_slots']=57;e['missing_metric_inputs']=['VNM longterm currentportion']
        self.assertTrue(decide(e)['pilot_history_engineering_pass'])

    def test_pending_tasks_or_interrupted_requests_block_extension(self):
        for key,value in [('terminal_tasks',1099),('unfinished_requests',1),('planned_tasks',0)]:
            with self.subTest(key=key):
                e=dict(self.evidence(),**{key:value});self.assertFalse(decide(e)['pilot_history_engineering_pass'])

    def test_rate_limits_use_observed_denominators_and_exact_boundary(self):
        e=dict(self.evidence(),transport_attempts=100,failed_requests=2,successful_network_responses=100,network_parse_errors=1)
        self.assertTrue(decide(e)['pilot_history_engineering_pass'])
        e['transport_attempts']=99;self.assertFalse(decide(e)['checks']['failed_after_retry_rate'])
        e['successful_network_responses']=99;self.assertFalse(decide(e)['checks']['schema_parser_rate'])

    def test_zero_denominator_is_na_and_fail_closed(self):
        e=dict(self.evidence(),transport_attempts=0,successful_network_responses=0)
        result=decide(e);self.assertEqual(result['rate_denominator_status'],'N_A')
        self.assertIsNone(result['failed_after_retry_rate']);self.assertIsNone(result['schema_parser_failure_rate'])
        self.assertFalse(result['pilot_history_engineering_pass'])

    def test_unheld_source_conflicts_and_auto_acceptance_block(self):
        for key,value in [('quarantine_complete',False),('row_shift_cohorts_held',False),('accepted_api_candidates',1),('conflicting_raw_keys',1),('active_api_blocked',True),('source_boundary_errors',1)]:
            with self.subTest(key=key):self.assertFalse(decide(dict(self.evidence(),**{key:value}))['pilot_history_engineering_pass'])

    def test_audit_must_cover_all_frozen_targets_and_both_modes(self):
        for key,value in [('required_audits',4),('completed_audits',5),('audit_issuer_modes_complete',False)]:
            with self.subTest(key=key):self.assertFalse(decide(dict(self.evidence(),**{key:value}))['checks']['independent_document_audits'])

    def test_deadline_disk_and_ocr_caps_never_reset(self):
        for key,value in [('decision_at',260200),('free_disk_bytes',29_999_999_999),('ocr_pages',1001),('max_pdf_ocr_pages',41),('pdf_downloads',51),('budget_stop',True)]:
            with self.subTest(key=key):self.assertFalse(decide(dict(self.evidence(),**{key:value}))['pilot_history_engineering_pass'])

    def test_negative_or_boolean_counters_are_not_evidence(self):
        for key,value in [('failed_requests',-1),('network_parse_errors',False),('ocr_pages',-1)]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):decide(dict(self.evidence(),**{key:value}))


if __name__=='__main__':unittest.main()
