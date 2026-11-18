import hashlib
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from delta_t1.experiments.financial_history_qa import (
    analyze, classify_gap, displacement, number, semantic_field, structural_header, unique_value)


class HistoryQATests(unittest.TestCase):
    def test_structural_zero_requires_exact_source_group(self):
        cell = dict(group='HDDT', raw_code='HDDT_21', value='0', label=None)
        payload = dict(value=dict(templace=[dict(code='HDDT', number=21, data=[])]))
        self.assertTrue(structural_header(cell, payload))
        self.assertFalse(structural_header(dict(cell, value='1'), payload))
        self.assertFalse(structural_header(dict(cell, value=None), payload))
        self.assertFalse(structural_header(dict(cell, raw_code='HDDT_22'), payload))
        self.assertFalse(structural_header(cell, dict(value=dict(templace=[]))))

    def test_child_zero_not_structural(self):
        payload = dict(value=dict(templace=[dict(code='HDKD', number=1, data=[dict(code='HDKD_1')])]))
        self.assertFalse(structural_header(dict(group='HDKD', raw_code='HDKD_1', value='0', label=None), payload))

    def test_old_direct_template_uses_own_group_number(self):
        payload = dict(value=dict(templace=[dict(code='HDDT', number=10, data=[])]))
        self.assertTrue(structural_header(dict(group='HDDT', raw_code='HDDT_10', value='0', label=None), payload))
        self.assertFalse(structural_header(dict(group='HDDT', raw_code='HDDT_21', value='0', label=None), payload))

    def test_mapping_requires_code_and_label(self):
        cell = dict(statement='CDKT', group='NV', raw_code='319', label='10. Phải trả ngắn hạn khác')
        self.assertEqual(semantic_field(cell), 'other_short_term_payables')
        self.assertIsNone(semantic_field(dict(cell, label='11. Vay và nợ thuê tài chính ngắn hạn')))
        self.assertIsNone(semantic_field(dict(cell, raw_code='320')))

    def test_provider_code_not_assumed_to_be_vas(self):
        cell = dict(statement='KQKD', group='KQKD', raw_code='21', label='Doanh thu hoạt động tài chính')
        self.assertIsNone(semantic_field(cell))

    def test_null_is_not_zero(self):
        self.assertIsNone(number(None))
        self.assertEqual(number('0'), Decimal(0))
        self.assertIsNone(unique_value([dict(value=None), dict(value='0')]))

    def test_conflicting_observations_no_vintage_selection(self):
        self.assertIsNone(unique_value([dict(value='100'), dict(value='101')]))
        self.assertEqual(unique_value([dict(value='100'), dict(value='100.0')]), Decimal(100))

    def test_row_shift_even_when_totals_balance(self):
        annual = {319: Decimal(0), 320: Decimal(1175), 321: Decimal(24141)}
        quarter = {319: Decimal(1175), 320: Decimal(24141), 321: Decimal(0)}
        self.assertEqual(sum(annual.values()), sum(quarter.values()))
        matches = displacement(annual, quarter)
        self.assertEqual(matches[0]['offset'], -1)
        self.assertEqual(len(matches[0]['pairs']), 2)
        self.assertFalse(displacement({319: Decimal(0), 320: Decimal(0)}, {319: Decimal(0)}))

    def test_single_repeated_amount_not_enough_for_displacement(self):
        self.assertFalse(displacement({320: Decimal(10), 321: Decimal(10)}, {319: Decimal(10), 320: Decimal(10)}))

    def test_h1_never_substitutes_for_q2(self):
        row = dict(symbol='FPT', year='2024', statement='KQKD', accepted='False', pit_ready='False')
        cs = [dict(symbol='FPT', year=2024, statement='KQKD', mode='LUYKE', quarter=2)]
        result = classify_gap(row, cs)
        self.assertEqual(result['h1_candidate_cells'], 1)
        self.assertFalse(result['accepted'])
        self.assertIn('NO_AUTOMATIC_Q2_SUBSTITUTION', result['h1_action'])
        self.assertIn('NOT_PROOF_OF_NONPUBLICATION', result['reason'])
        self.assertEqual(classify_gap(dict(row, statement='CDKT'), cs)['h1_candidate_cells'], 0)

    def test_raw_tamper_fails_before_classification(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def put(name, value):
                raw = value if isinstance(value, bytes) else json.dumps(value).encode()
                (root / name).write_bytes(raw)
                return hashlib.sha256(raw).hexdigest()
            put('facts.json', [])
            cell = dict(source_path='raw.json', source_sha256='0' * 64)
            ch = put('candidates.jsonl', (json.dumps(cell) + '\n').encode())
            cov = put('financial_coverage.csv', b'status\n')
            met = put('metrics.csv', b'status,value\n')
            put('raw.json', dict(value=dict(templace=[])))
            # A sealed candidate manifest cannot excuse a tampered underlying raw file.
            mh = put('manifest.json', {'candidates.jsonl': ch, 'financial_coverage.csv': cov, 'metrics.csv': met})
            config = dict(input_report='.', input_manifest_sha256=mh, reviewed_inputs='facts.json',
                          reviewed_inputs_sha256=hashlib.sha256((root / 'facts.json').read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError, 'input hash mismatch: raw.json'):
                analyze(root, config)

    def test_different_annual_q4_flags_stay_separate_but_are_diagnosed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def put(name, value):
                raw = value if isinstance(value, bytes) else json.dumps(value).encode()
                (root / name).write_bytes(raw)
                return hashlib.sha256(raw).hexdigest()
            raw_hash = put('raw.json', dict(value=dict(templace=[])))
            cells = []
            for mode, quarter, flag, codes in [('NAM', 0, 'K', {319: 0, 320: 1175, 321: 24141}),
                                              ('QUY', 4, 'N', {319: 1175, 320: 24141, 321: 0})]:
                for code, value in codes.items():
                    cells.append(dict(symbol='BRC', year=2025, quarter=quarter, mode=mode,
                        provider_type=flag, statement='CDKT', group='NV', raw_code=str(code),
                        label='unmapped diagnostic row', value=str(value), source_path='raw.json',
                        source_sha256=raw_hash, template_sha256='fixture', header='2025', interval='QUARTER'))
            ch = put('candidates.jsonl', b''.join((json.dumps(c)+'\n').encode() for c in cells))
            cov = put('financial_coverage.csv', b'status\n')
            met = put('metrics.csv', b'status,value\n')
            fh = put('facts.json', [])
            mh = put('manifest.json', {'candidates.jsonl': ch, 'financial_coverage.csv': cov, 'metrics.csv': met})
            config = dict(input_report='.', input_manifest_sha256=mh,
                          reviewed_inputs='facts.json', reviewed_inputs_sha256=fh)
            products, _, summary = analyze(root, config)
            shifts = json.loads(products['possible_row_displacements.json'])
            self.assertEqual(summary['possible_displacements'], 1)
            self.assertEqual(shifts[0]['annual_provider_type'], 'K')
            self.assertEqual(shifts[0]['q4_provider_type'], 'N')
            self.assertEqual(summary['accepted_new_facts'], 0)
            put('candidates.jsonl', b'changed sealed input')
            with self.assertRaisesRegex(ValueError, 'input hash mismatch'):
                analyze(root, config)


if __name__ == '__main__':
    unittest.main()
