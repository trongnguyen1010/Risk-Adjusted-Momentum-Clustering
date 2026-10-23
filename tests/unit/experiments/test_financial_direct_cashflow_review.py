import unittest
from delta_t1.experiments.financial_direct_cashflow_review import direct_observations, resolve_direct, longest_run, LABELS


class DirectCashflowTests(unittest.TestCase):
    def rows(self):
        values = ['10000000000','-8000000000','-1000000000','-500000000','-100000000','200000000','-200000000','400000000']
        return [dict(statement='LCTT', group='HDKD', mode='NAM', quarter=0, year=2025,
            provider_type='K', source_path='raw.json', source_sha256='abc', period_occurrence=0,
            raw_code=code, label=label, mapping_status='UNIQUE_CODE_LABEL_CANDIDATE',
            value_status='NUMERIC_CANDIDATE', value=value, provider_unit=None,
            template_sha256='template', raw_cell_ordinal=i) for i, ((code,label),value) in enumerate(zip(LABELS.items(),values))]

    def test_exact_label_signed_component_sum_no_inferred_unit(self):
        result=direct_observations(self.rows())
        self.assertEqual(resolve_direct(result),('400000000','DIRECT_CFO_RAW_VALUE_REFERENCE_ONLY'))
        self.assertIsNone(result[0]['provider_unit']);self.assertFalse(result[0]['accepted'])
        self.assertFalse(result[0]['strict_pit_ready'])

    def test_wrong_or_duplicate_code_label_missing_component_held(self):
        rows=self.rows();rows[-1]['label']='Lợi nhuận khác'
        self.assertIsNone(resolve_direct(direct_observations(rows))[0])
        rows=self.rows();rows.append(dict(rows[-1]))
        self.assertIsNone(resolve_direct(direct_observations(rows))[0])
        rows=self.rows();del rows[0]
        self.assertIsNone(resolve_direct(direct_observations(rows))[0])

    def test_quarter_ytd_or_wrong_group_never_treated_as_annual(self):
        for key,value in [('mode','QUY'),('quarter',4),('group','HDTC'),('statement','CDKT')]:
            rows=self.rows()
            for r in rows:r[key]=value
            self.assertEqual(direct_observations(rows),[])

    def test_invalid_component_or_nonzero_orphan_cannot_hide_behind_sum(self):
        rows=self.rows();rows[0]['value_status']='BOOLEAN_QUARANTINED';rows[0]['value']=None
        self.assertIsNone(resolve_direct(direct_observations(rows))[0])
        rows=self.rows();rows.append(dict(rows[0],raw_code='HDKD_1',value='1'))
        self.assertIsNone(resolve_direct(direct_observations(rows))[0])
        rows[-1]['value']='0'
        self.assertIsNotNone(resolve_direct(direct_observations(rows))[0])

    def test_wrong_total_material_difference_and_conflict_never_selected(self):
        rows=self.rows();rows[-1]['value']='400000002'
        self.assertIsNone(resolve_direct(direct_observations(rows))[0])
        good=direct_observations(self.rows())
        self.assertIsNone(resolve_direct(good+[dict(good[0],value='123')])[0])
        self.assertIsNone(resolve_direct(good+[dict(good[0],value=None)])[0])

    def test_negative_cfo_retained_and_small_residual_separate(self):
        rows=self.rows()
        for row in rows:row['value']=str(-int(row['value']))
        self.assertEqual(resolve_direct(direct_observations(rows))[0],'-400000000')
        rows[-1]['value']='-399999999'
        self.assertEqual(direct_observations(rows)[0]['component_decision'],'SMALL_RAW_RESIDUAL_REFERENCE_ONLY')

    def test_consecutive_counts_do_not_fill_gaps(self):
        self.assertEqual(longest_run([]),0)
        self.assertEqual(longest_run([2016,2017,2019,2020,2021,2025]),3)
        self.assertEqual(longest_run([2020,2020,2021]),2)
