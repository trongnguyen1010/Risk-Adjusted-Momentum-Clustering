import unittest
from delta_t1.ingestion.financial_pilot_readiness import reconcile, eligible_fact

def fact(**changes):
    f=dict(symbol='FPT',year=2025,item='operating_cash_flow',value=0,unit='VND',
       statement_scope='CONSOLIDATED',accounting_framework='VAS',period_start='2025-01-01',period_end='2025-12-31',
       pdf_sha256='a',vintage='CURRENT',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')
    return dict(f,**changes)

def baseline():
    return dict(financial_features_allowed=False,rows=[dict(symbol='FPT',year=2025,field='operating_cash_flow',
      candidate_values=[],presence_status='MISSING')])

class ReadinessTests(unittest.TestCase):
    def test_wrong_issuer_hash_is_quarantined_without_deleting_raw(self):
        r=reconcile(baseline(),[fact()],rejected_pdf_hashes={'a'})
        self.assertEqual(r['accepted_annual_observations'],0)
        self.assertEqual(r['quarantined_observations'],1)
        self.assertEqual(r['rows'][0]['document_evidence'],[])

    def test_fixed_assets_are_instant_not_annual_flow(self):
        self.assertTrue(eligible_fact(fact(item='fixed_assets',period_start=None,period_semantics='INSTANT')))
        self.assertFalse(eligible_fact(fact(item='fixed_assets')))

    def test_quarter_scope_framework_and_later_quote_are_not_annual_acceptance(self):
        for changes in [dict(period_end='2025-09-30'),dict(period_start='2025-10-01'),dict(statement_scope='SEPARATE'),
                        dict(accounting_framework='IFRS'),dict(accounting_framework=None),dict(vintage='PREVIOUSLY_REPORTED_AS_QUOTED_IN_ANNUAL_2025'),
                        dict(validation_status='OCR_REQUIRES_VISUAL_VERIFICATION')]:
            self.assertFalse(eligible_fact(fact(**changes)))
    def test_zero_is_present_and_never_promotes_pit(self):
        r=reconcile(baseline(),[fact()])
        self.assertEqual(r['rows'][0]['evidence_status'],'DOCUMENT_VALUE_VERIFIED_PIT_PENDING')
        self.assertIsNone(r['rows'][0]['selected_canonical_value'])
        self.assertFalse(r['financial_features_allowed'])
        self.assertTrue(all(x['signal_value'] is None for x in r['f_score_dependencies']))
    def test_conflict_within_vintage_but_revisions_preserved(self):
        r=reconcile(baseline(),[fact(),fact(value=2)])
        self.assertEqual(r['rows'][0]['evidence_status'],'DOCUMENT_VALUE_CONFLICT')
        r=reconcile(baseline(),[fact(),fact(value=2,pdf_sha256='b')])
        self.assertEqual(r['rows'][0]['document_vintages'],2)
        self.assertIsNone(r['rows'][0]['selected_canonical_value'])
    def test_document_snapshot_end_is_required(self):
        self.assertFalse(eligible_fact(fact(item='total_assets',period_end='2025-06-30')))
        self.assertFalse(eligible_fact(fact(item='total_assets')))
        self.assertTrue(eligible_fact(fact(item='total_assets',period_start=None,period_semantics='INSTANT')))
    def test_missing_invalid_values_do_not_count_as_evidence(self):
        for value in [None, True, '0', float('nan'), float('inf')]:
            self.assertFalse(eligible_fact(fact(value=value)))
        self.assertFalse(eligible_fact(fact(unit='UNKNOWN')))
        self.assertFalse(eligible_fact(fact(unit='SHARES')))
        self.assertFalse(eligible_fact(fact(item='basic_eps',unit='VND')))

if __name__=='__main__':unittest.main()
