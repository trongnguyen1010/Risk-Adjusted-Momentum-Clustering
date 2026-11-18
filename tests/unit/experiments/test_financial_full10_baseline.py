import unittest

from delta_t1.experiments.financial_full10_baseline import validate_rows, extract_values, compare_ratios
from delta_t1.features.financial_exploratory import FEATURES, calculate_core


class Full10BaselineTests(unittest.TestCase):
    def values(self):
        return dict(gross_profit='20', net_profit='-5', net_revenue='100', total_liabilities='50',
                    total_assets='200', current_assets='80', current_liabilities='40', operating_cash_flow='-10')

    def row(self):
        return dict(symbol='AAA', registry_id='candidate-a', year=2025, source_kind='', provider_type='K',
                    source_evidence='inputs.json', strict_pit_ready='False', research_ready='False',
                    financial_features_allowed='False', **calculate_core(self.values())['values'])

    def test_exact_cohort_missing_duplicate_and_identity(self):
        row = self.row(); members = [dict(symbol='AAA', registry_id='candidate-a')]
        validate_rows([row], members, [2025], 1)
        for rows, years in [([], [2025]), ([row, row], [2025]), ([row], [2024, 2025]),
                            ([dict(row, symbol='BBB')], [2025])]:
            with self.assertRaises(ValueError):
                validate_rows(rows, members, years, 1)

    def test_nonfinite_or_promoted_row_rejected(self):
        row = self.row(); members = [dict(symbol='AAA', registry_id='candidate-a')]
        for update in [dict(gross_margin='nan'), dict(research_ready='True'), dict(strict_pit_ready='True')]:
            with self.assertRaises(ValueError):
                validate_rows([dict(row, **update)], members, [2025], 1)

    def test_partition_selection_does_not_mix_providers(self):
        fields = [dict(field=f, value=v, year=2025, provider_type='K') for f, v in self.values().items()]
        fields += [dict(field='net_profit', value='999', year=2025, provider_type='HK')]
        values = extract_values(self.row(), lambda path: fields)
        self.assertEqual(values['net_profit'], '-5')
        self.assertEqual(compare_ratios(self.row(), values)['net_margin'], -0.05)

    def test_ambiguous_values_never_selected(self):
        fields = [dict(field=f, value=v, year=2025, provider_type='K') for f, v in self.values().items()]
        fields.append(dict(field='net_profit', value='999', year=2025, provider_type='K'))
        with self.assertRaises(ValueError):
            extract_values(self.row(), lambda path: fields)

    def test_changed_ratio_or_missing_source_input_rejected(self):
        with self.assertRaises(ValueError):
            compare_ratios(dict(self.row(), gross_margin=99), self.values())
        values = self.values(); del values['operating_cash_flow']
        with self.assertRaises(ValueError):
            compare_ratios(self.row(), values)

    def test_dstock_string_year_and_unique_selected_case(self):
        row = dict(self.row(), source_kind='DSTOCK_API_EXPLORATORY_COMPLETE_VECTOR')
        case = dict(target=dict(registry_id=row['registry_id'], year='2025'), eligible_reference=True, values=self.values())
        self.assertEqual(extract_values(row, lambda path: dict(cases=[case])), self.values())
        with self.assertRaises(ValueError):
            extract_values(row, lambda path: dict(cases=[case, case]))
