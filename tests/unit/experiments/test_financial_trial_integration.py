import copy
import tempfile
import unittest
from pathlib import Path

from delta_t1.experiments.financial_trial_integration import assess, evidence_pins, history_rows, values_at
from delta_t1.ingestion.cafef_financial import digest


def task(symbol='FPT', year=2025, name='EPS_RECOMPUTE'):
    return dict(symbol=symbol, year=year, task=name, candidate_input_cells=0,
                required_input_cells=3, missing_inputs=['reviewed_shares'], blockers=['PUBLICATION_PIT'])


def reference(symbol='FPT', year=None, name='EPS_RECOMPUTE', value='123'):
    return dict(symbol=symbol, year=year, task=name, value=value, basis='TTM' if year is None else 'ANNUAL',
                pit_status='DATE_ONLY', blockers=['METHOD_REVIEW'])


def fact_reference(**changes):
    f = dict(year=2025, item='net_profit', value=12, unit='VND', statement_scope='CONSOLIDATED',
             accounting_framework='VAS', validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',
             period_start='2025-01-01', period_end='2025-12-31', period_semantics='ANNUAL', vintage='CURRENT_ANNUAL')
    r = dict(fact=f, usable_from_date='2026-03-20', available_at=None,
             date_pit_status='DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR')
    r.update(changes)
    return r


class IntegrationTests(unittest.TestCase):
    def test_ttm_is_not_assigned_to_annual_task(self):
        rows, summary = assess([task()], [dict(ticker='FPT', proposed_company_type='Regular')], [reference()])
        self.assertIsNone(rows[0]['reference_value'])
        self.assertEqual(summary[0]['nonannual_reference_values'], 1)
        self.assertEqual(summary[0]['annual_reference_cells'], 0)

    def test_annual_reference_not_strict_acceptance_and_controls_excluded(self):
        members = [dict(ticker='FPT', proposed_company_type='Regular')]
        rows, summary = assess([task()], members, [reference(year=2025), reference(symbol='VNM', year=2025)])
        self.assertEqual(rows[0]['reference_value'], '123')
        self.assertFalse(rows[0]['strict_task_ready'])
        self.assertIsNone(rows[0]['strict_computed_value'])
        self.assertEqual(summary[0]['reference_families_with_any_basis'], 1)

    def test_missing_one_metric_does_not_block_other_metric(self):
        rows, _ = assess([task(), task(name='PE')], [dict(ticker='FPT', proposed_company_type='Regular')],
                         [reference(year=2025)])
        self.assertEqual(rows[0]['reference_status'], 'REVIEWED_REFERENCE_VALUE_AVAILABLE')
        self.assertEqual(rows[1]['reference_status'], 'REVIEWED_INPUTS_REQUIRED')

    def test_nonregular_sector_remains_separate(self):
        rows, _ = assess([task('TCB')], [dict(ticker='TCB', proposed_company_type='Bank')], [])
        self.assertEqual(rows[0]['reference_status'], 'SECTOR_TEMPLATE_REVIEW_REQUIRED')

    def test_competing_basis_and_nonfinite_values_rejected(self):
        members = [dict(ticker='FPT', proposed_company_type='Regular')]
        for ledger in [[reference(year=2025), reference(year=2025)], [reference(value='NaN')]]:
            with self.assertRaises(ValueError):
                assess([task()], members, ledger)

    def test_date_only_no_hours_and_strictly_after_publication(self):
        ref = fact_reference()
        self.assertEqual(values_at([ref], 2025, '2026-03-20'), {('net_profit', 0): 12})
        with self.assertRaises(ValueError):
            values_at([ref], 2025, '2026-03-19')

    def test_bad_scope_unit_vintage_and_publication_rejected(self):
        for key, value in [('unit', 'UNKNOWN'), ('statement_scope', 'STANDALONE'),
                           ('vintage', 'PREVIOUSLY_REPORTED'), ('period_end', '2025-06-30')]:
            r = fact_reference(); r['fact'][key] = value
            with self.assertRaises(ValueError): values_at([r], 2025, '2026-08-28')
        with self.assertRaises(ValueError):
            values_at([fact_reference(date_pit_status='UNVERIFIED')], 2025, '2026-08-28')

    def test_external_proof_and_nested_original_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'proof').write_bytes(b'proof')
            tree = dict(derivation=dict(original=dict(image_path='proof', image_sha256=digest(b'proof'))))
            self.assertEqual(evidence_pins(root, tree), {'proof': digest(b'proof')})
            (root/'proof').write_bytes(b'changed')
            with self.assertRaises(ValueError): evidence_pins(root, tree)
            with self.assertRaises(ValueError):
                evidence_pins(root, dict(pdf_path='../outside', pdf_sha256='0'*64))

    def test_conflicting_reviewed_cells_rejected(self):
        a = fact_reference(); b = copy.deepcopy(a); b['fact']['value'] = 13
        with self.assertRaises(ValueError): values_at([a, b], 2025, '2026-08-28')

    def test_history_not_reused_before_source_snapshot(self):
        source = dict(f_score=[dict(year=2025, decision_date='2026-03-20',
                                   vas_reference=dict(value=3))], m_score=[], existing_eps_z=[])
        self.assertEqual(history_rows(source, 'source', '2026-03-19', [2025]), [])


if __name__ == '__main__':
    unittest.main()
