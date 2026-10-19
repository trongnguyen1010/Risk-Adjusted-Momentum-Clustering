import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from delta_t1.experiments.financial_pilot_completion import (
    acquire, digest, number, supplemental_facts, validate)

ROOT = Path(__file__).resolve().parents[3]


class ClosingDebtTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ['note.pdf', 'page.png']:
            (self.root/name).write_bytes(name.encode())
        self.package = dict(version='pilot5-closing-debt-review-v1', source_pins={
            name:digest((self.root/name).read_bytes()) for name in ['note.pdf', 'page.png']},
            observations=[dict(symbol='VNM', year=year, balance_date=f'{year}-12-31',
                scope='CONSOLIDATED', framework='VAS', unit='VND',
                review_status='REVIEWED_REFERENCE_ONLY', basis='ORIGINAL_LONG_TERM_CLOSING_STOCK',
                reviewed_by='test-reviewer', current_portion='20', noncurrent_portion='80',
                total_original_long_term_debt='100', evidence=[dict(pdf_path='note.pdf',
                    image_path='page.png', pdf_page=47, locator='Loan note: closing columns')])
                for year in [2024, 2025]])

    def test_explicit_components_sum_to_total_without_mutating_source(self):
        before = copy.deepcopy(self.package)
        facts = supplemental_facts(self.root, self.package)
        self.assertEqual([f['value'] for f in facts], ['100', '100'])
        self.assertEqual(before, self.package)
        self.assertEqual(facts[0]['field'], 'long_term_debt_including_current_portion')

    def test_missing_is_not_zero_and_invalid_numeric_values_rejected(self):
        for value in [None, True, 'NaN', 'Infinity', '-1', 'bad']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value)
        self.assertEqual(number('0'), 0)

    def test_parent_ifrs_flow_wrong_date_and_unreviewed_rejected(self):
        for change in [dict(scope='SEPARATE'), dict(framework='IFRS'), dict(unit='MILLION_VND'),
                dict(basis='IN_YEAR_RECLASSIFICATION_FLOW'), dict(balance_date='2025-06-30'),
                dict(review_status='OCR_CANDIDATE'), dict(reviewed_by='')]:
            package = copy.deepcopy(self.package)
            package['observations'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                supplemental_facts(self.root, package)

    def test_component_mismatch_rejected(self):
        self.package['observations'][0]['current_portion'] = '21'
        with self.assertRaisesRegex(ValueError, 'arithmetic'):
            supplemental_facts(self.root, self.package)

    def test_both_years_required(self):
        self.package['observations'].pop()
        with self.assertRaisesRegex(ValueError, 'both closing'):
            supplemental_facts(self.root, self.package)

    def test_image_tamper_rejected(self):
        (self.root/'page.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            supplemental_facts(self.root, self.package)

    def test_exact_locator_required(self):
        self.package['observations'][0]['evidence'][0]['locator'] = ''
        with self.assertRaisesRegex(ValueError, 'locator'):
            supplemental_facts(self.root, self.package)

    def test_empty_review_still_verifies_evidence_pins(self):
        self.package['observations'] = []
        self.assertEqual(supplemental_facts(self.root, self.package), [])
        (self.root/'note.pdf').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            supplemental_facts(self.root, self.package)


class CompletionAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/'configs/data/financial_pilot5_completion_v1.json').read_bytes())

    def test_caps_and_closed_gates_cannot_expand(self):
        validate(self.config)
        for key, value in [('max_transport_attempts', 2), ('max_pdf_download_attempts', 2)]:
            config = copy.deepcopy(self.config)
            config['budgets'][key] = value
            with self.assertRaises(ValueError): validate(config)
        config = dict(self.config, research_ready=True)
        with self.assertRaises(ValueError): validate(config)

    def test_terminal_receipt_resumes_without_constructing_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            run = root/self.config['output_root']; run.mkdir(parents=True)
            (run/'document-receipt.json').write_text(json.dumps(dict(status='ACCESS_STOP')))
            with patch('delta_t1.experiments.financial_pilot_completion.PilotTransport') as transport:
                result = acquire(root, self.config, transport_class=transport)
            self.assertEqual(result['status'], 'ACCESS_STOP')
            transport.assert_not_called()

    def test_previously_attempted_url_cannot_start_a_new_campaign(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            doc = self.config['documents'][0]
            source = root/doc['discovered_on']; source.parent.mkdir(parents=True)
            source.write_text(json.dumps(dict(Data=dict(BctcList=[dict(
                LinkFile='/Images/Uploaded/DuLieuDownload/BCTC/'+doc['url'].rsplit('/',1)[1],
                Symbol='VNM', Year=2025, ReportType='MK')]))))
            with patch('delta_t1.experiments.financial_pilot_completion.read_compact', return_value=dict(
                    state=dict(requests={'old':dict(url=doc['url'])}))), self.assertRaisesRegex(
                    ValueError, 'previously attempted'):
                acquire(root, self.config)

    def test_failed_acquisition_receipt_is_terminal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            doc = self.config['documents'][0]
            source = root/doc['discovered_on']; source.parent.mkdir(parents=True)
            source.write_text(json.dumps(dict(Data=dict(BctcList=[dict(
                LinkFile='/Images/Uploaded/DuLieuDownload/BCTC/'+doc['url'].rsplit('/',1)[1],
                Symbol='VNM', Year=2025, ReportType='MK')]))))
            class BoundaryTransport:
                def __init__(self, *args):
                    self.state = dict(boundary=True, budget_stop=False)
                def get(self, url):
                    raise ValueError('HTTP403')
            with patch('delta_t1.experiments.financial_pilot_completion.read_compact', return_value=dict(
                    state=dict(requests={}))):
                result = acquire(root, self.config, transport_class=BoundaryTransport)
            self.assertEqual(result['status'], 'ACCESS_STOP')
            with patch('delta_t1.experiments.financial_pilot_completion.PilotTransport') as transport:
                self.assertEqual(acquire(root, self.config, transport_class=transport), result)
                transport.assert_not_called()


if __name__ == '__main__':
    unittest.main()
