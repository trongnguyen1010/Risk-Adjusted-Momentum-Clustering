import json
import tempfile
import unittest
from pathlib import Path
from delta_t1.experiments.financial_three_symbol_pilot import (
    annual_math, eligible, next_session, numeric, optional_ttm, pinned, reviewed_cell,
)
from delta_t1.experiments.financial_ttm_valuation import file_hash


class ThreeSymbolPilotTests(unittest.TestCase):
    def values(self):
        rows = dict(current_assets=[60, 50], current_liabilities=[20, 20], total_assets=[100, 90],
                    total_equity=[50, 45], total_liabilities=[50, 45], retained_earnings=[20, 15],
                    net_revenue=[100, 90], gross_profit=[40, 30], net_profit=[10, 8],
                    operating_cash_flow=[15, 12], net_tangible_ppe=[20, 20], receivables=[10, 10],
                    selling_expense=[5, 5], administrative_expense=[5, 5],
                    noncurrent_loans_and_finance_leases=[10, 10], owned_tangible_ppe_depreciation=[5, 5],
                    current_portion_original_long_term_debt=[2, 3], profit_before_tax=[12, 10], interest_expense=[1, 1],
                    parent_net_profit=[8, 7], eps_reserve_deduction=[2, 1], eps_adjusted_earnings_numerator=[6, 6],
                    weighted_average_basic_shares=[2, 2], vendor_basic_eps=[3, 3])
        v = {(f, o): str(x) for f, pair in rows.items() for o, x in zip([0, -1], pair)}
        v['total_assets', -2] = '80'; v['parent_common_equity_issuance_verified', 0] = '0'
        return v

    def test_accounting_bridges_and_hand_calculated_eps(self):
        r = annual_math(self.values(), 'RESERVE_DEDUCTED_REPORTED_NOTE', True)
        self.assertEqual(r['eps']['value'], '3')
        self.assertEqual(r['eps']['dilution_reference']['value']['diluted'], '3')
        self.assertEqual(r['f_vas']['known_signals'], 9)
        self.assertFalse(r['f_vas']['strict_original_score'])
        self.assertIsNone(r['f_strict']['value'])
        self.assertTrue(all(q['passed'] for q in r['qa']))
        # EBIT=13, WC=40, TA=100, RE=20, E/TL=1: independently calculated.
        self.assertAlmostEqual(float(r['z']['value']['em_z_double_prime_reference']), 8.4496)

    def test_no_alias_of_noncurrent_debt_for_original_long_term_total(self):
        v = self.values(); del v['current_portion_original_long_term_debt', 0]
        r = annual_math(v, 'RESERVE_DEDUCTED_REPORTED_NOTE', True)
        self.assertIsNone(r['f_vas']['value'])
        self.assertEqual(r['f_vas']['known_signals'], 8)
        self.assertIsNone(r['f_vas']['signals']['reduced_leverage']['value'])

    def test_owned_ppe_depreciation_not_replaced_by_cfo_total(self):
        v = self.values(); del v['owned_tangible_ppe_depreciation', -1]
        v['cash_flow_total_depreciation', -1] = '5'
        self.assertIsNone(annual_math(v, 'RESERVE_DEDUCTED_REPORTED_NOTE', True)['m_sensitivity']['value'])

    def test_acv_style_unestimated_reserve_and_unknown_dilution(self):
        v = self.values(); v['reported_eps_numerator', 0] = '8'; v['vendor_basic_eps', 0] = '4'
        r = annual_math(v, 'REPORTED_UNESTIMATED_RESERVE_NOT_NORMALIZED', False)
        self.assertEqual(r['eps']['value'], '4')
        self.assertIsNone(r['eps']['diluted_eps'])
        self.assertIsNone(r['eps']['strict_normalized_eps'])
        self.assertIsNone(r['eps']['dilution_reference']['value'])

    def test_transcription_balance_numerator_and_rounded_eps_errors_rejected(self):
        for field in ['total_assets', 'eps_adjusted_earnings_numerator', 'vendor_basic_eps']:
            v = self.values(); v[field, 0] = str(int(v[field, 0]) + 1)
            with self.assertRaises(ValueError): annual_math(v, 'RESERVE_DEDUCTED_REPORTED_NOTE', True)
        for bad in [True, None, 'NaN', 'Infinity']:
            with self.assertRaises(ValueError): numeric(bad)

    def test_date_only_same_date_and_future_are_unusable(self):
        rows = [dict(exchange='HOSE', trade_date=d, is_open=True) for d in ['2026-07-30', '2026-07-31']]
        usable = next_session(rows, 'HOSE', '2026-07-30')
        self.assertEqual(usable, '2026-07-31')
        self.assertFalse(eligible(usable, '2026-07-30'))
        self.assertTrue(eligible(usable, '2026-07-31'))
        self.assertIsNone(next_session(rows, 'HOSE', '2026-09-03'))

    def test_image_and_input_hashes_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); image = root / 'data/ocr/document/page-01.png'
            image.parent.mkdir(parents=True); image.write_bytes(b'reviewed image')
            proof = dict(image_path=str(image), image_sha256=file_hash(image),
                         validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',
                         review_method='HUMAN_VISUAL_EXACT_RENDERED_PDF_PAGE_NOT_AUTOMATIC_OCR_ACCEPTANCE')
            image.with_name('page-01.ocr.json').write_text(json.dumps(dict(image_sha256=proof['image_sha256'], lines=[])))
            case = dict(symbol='VNM', page_reviews={'data/ocr/document/1': proof})
            docs = {('data/ocr', 'document'): dict(ranges=[(1, 1)], pdf_path='statement.pdf', pdf_sha256='pinned', report_year=2025)}
            cell = reviewed_cell(root, case, docs, 'net_profit', -1, '12', 'data/ocr', 'document', 1)
            self.assertEqual(cell['year'], 2024)
            self.assertEqual(cell['source_report_year'], 2025)
            self.assertFalse(cell['production_accepted'])
            image.write_bytes(b'changed')
            with self.assertRaises(ValueError): reviewed_cell(root, case, docs, 'net_profit', 0, '12', 'data/ocr', 'document', 1)
            with self.assertRaises(ValueError): pinned(root, root.parent / 'escape', 'checksum')

    def test_ttm_unknown_and_changed_prior_profit_stay_null(self):
        self.assertIsNone(optional_ttm(Path('.'), {}, {}, [], None, '2026-08-28', {})['value'])
        old = dict(parent_profit='30', reported_deduction='5', reported_eps_numerator='25', weighted_basic_shares='10')
        bridge = dict(validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED', scope_status='SAME_PARENT_COMMON_EARNINGS_SCOPE_REVIEWED',
                      evidence=[], old_h125_diagnostic=old, share_basis_id='same common basis')
        base = dict(symbol='VNM', source_period_end='2026-06-30', usable_from_date='2026-07-31')
        prior = dict(base, **old, period_start='2025-01-01', period_end='2025-06-30')
        current = dict(base, parent_profit='40', reported_deduction='7', reported_eps_numerator='33', weighted_basic_shares='10',
                       period_start='2026-01-01', period_end='2026-06-30')
        v = {('weighted_average_basic_shares', 0): '10', ('eps_adjusted_earnings_numerator', 0): '90',
             ('parent_net_profit', 0): '100', ('eps_reserve_deduction', 0): '10'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder = root/'data/ocr/note'; folder.mkdir(parents=True)
            pdf = root/'note.pdf'; pdf.write_bytes(b'synthetic statement')
            docs = {('data/ocr', 'note'): dict(pdf_sha256=file_hash(pdf))}
            for page in [1, 2]:
                image = folder/f'page-{page:02d}.png'; image.write_bytes(b'synthetic reviewed image')
                bridge['evidence'].append(dict(image_path=str(image), image_sha256=file_hash(image), pdf_path=str(pdf),
                    pdf_sha256=file_hash(pdf), pdf_page=page, ocr_run='data/ocr', pdf_stem='note'))
            args = [root, dict(symbol='VNM', ttm_bridge=bridge), v, [prior, current], '2026-02-28', '2026-08-28', docs]
            self.assertEqual(optional_ttm(*args)['value'], '9.8')
            prior['parent_profit'] = '29'
            self.assertEqual(optional_ttm(*args)['status'], 'PRIOR_EARNINGS_OR_SHARE_BASIS_CHANGED')
            self.assertIsNone(optional_ttm(*args)['value'])


if __name__ == '__main__': unittest.main()
