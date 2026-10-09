import importlib.util
import unittest
from pathlib import Path
from delta_t1.experiments.financial_fpt_acceptance import unique_usable


class AcceptanceSelectionTests(unittest.TestCase):
    def test_future_result_not_used_and_ambiguity_rejected(self):
        rows = [dict(year=2025, decision_date='2026-03-20', value=3)]
        self.assertIsNone(unique_usable(rows, 2025, '2026-03-19'))
        self.assertEqual(unique_usable(rows, 2025, '2026-03-20')['value'], 3)
        with self.assertRaises(ValueError):
            unique_usable(rows + rows, 2025, '2026-03-20')

    def test_disjoint_ocr_ranges_skip_employee_list_and_reject_overlap(self):
        root = Path(__file__).resolve().parents[3]
        spec = importlib.util.spec_from_file_location('page_extractor', root / 'scripts/extract_financial_selected_pages.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        first = dict(pdf_path='a.pdf', pdf_sha256='hash', first_page=1, last_page=3)
        last = dict(first, first_page=12, last_page=12)
        groups = module.grouped_ranges([first, last])
        self.assertEqual(groups['a']['pages'], {1, 2, 3, 12})
        with self.assertRaises(ValueError):
            module.grouped_ranges([first, dict(last, first_page=3)])
        with self.assertRaises(ValueError):
            module.grouped_ranges([first, dict(last, pdf_path='other/a.pdf')])
