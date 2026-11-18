import unittest
from delta_t1.experiments.financial_template_contract import (
    proposed_fields,finance_bridge,complete_reference_vectors,require_cluster_ready)


class TemplateContractTests(unittest.TestCase):
    def row(self,**kw):
        base=dict(template_sha256='known',statement='KQKD',mode='NAM',raw_code='23',mapping_status='UNIQUE_CODE_LABEL_CANDIDATE',
            value_status='NUMERIC_CANDIDATE',year=2025,quarter=0,value='10',label='Chi phí tài chính')
        return dict(base,**kw)

    def test_exact_template_proposal_retains_wrong_label_and_gates(self):
        row=proposed_fields([self.row()],{'known'})[0]
        self.assertEqual(row['proposed_field'],'interest_expense')
        self.assertEqual(row['label'],'Chi phí tài chính')
        self.assertFalse(row['accepted']);self.assertFalse(row['pit_ready'])

    def test_unknown_template_quarter_duplicate_invalid_not_corrected(self):
        for change in [dict(template_sha256='unknown'),dict(mode='QUY'),dict(quarter=1),
                       dict(mapping_status='DUPLICATE_TEMPLATE_CODE_QUARANTINED'),dict(value_status='MISSING')]:
            self.assertEqual(proposed_fields([self.row(**change)],{'known'}),[])

    def test_associate_loss_signed_and_missing_not_zero(self):
        v=dict(gross_profit='100',finance_income='20',finance_expense='10',associate_profit='-5',selling_expense='30',administrative_expense='15',reported_operating_profit='60')
        self.assertEqual(finance_bridge(v)['status'],'EXACT_EQUALITY')
        del v['associate_profit'];self.assertEqual(finance_bridge(v)['status'],'MISSING_INPUTS')

    def vectors(self):
        return [dict(symbol='AAA',year=2025,cohort_id='C',input_scope='CONSOLIDATED',period_kind='ANNUAL',family=f,value='1',variant=f,id=f,snapshot_date='2026-08-28' if f in ['PE','PB'] else None)
                for f in ['EPS','PE','PB','F_SCORE','M_SCORE','Z_SCORE']]

    def test_reference_vector_never_promotes_to_model(self):
        r=complete_reference_vectors(self.vectors())
        self.assertEqual(len(r),1);self.assertFalse(r[0]['financial_cluster_input_allowed'])
        for field,val in [('year',2024),('cohort_id','OTHER'),('period_kind','YTD'),('input_scope','SEPARATE')]:
            rows=self.vectors();rows[-1][field]=val
            self.assertEqual(complete_reference_vectors(rows),[])
        rows=self.vectors();rows[1]['snapshot_date']='2026-08-27'
        self.assertEqual(complete_reference_vectors(rows),[])

    def test_model_refuses_missing_or_false_gate(self):
        with self.assertRaisesRegex(ValueError,'FINANCIAL_CLUSTERING_HELD'):
            require_cluster_ready(dict(financial_protocol_approved=True))
        keys=['financial_protocol_approved','features_cluster_eligible','pit_inputs_verified','historical_identity_verified','development_sample_ready']
        for key in keys:
            r={k:True for k in keys};r[key]=False
            with self.assertRaises(ValueError):require_cluster_ready(r)
