import unittest
from delta_t1.experiments.financial_near_full_review import document_vectors, choose_document
from delta_t1.features.financial_exploratory import REQUIRED


class NearFullReviewTests(unittest.TestCase):
    def facts(self):
        values=dict(current_assets='500',current_liabilities='200',total_assets='1000',total_liabilities='400',
            net_revenue='1000',gross_profit='300',net_profit='-10',operating_cash_flow='-50')
        return [dict(symbol='AAA',year=2025,field=f,reviewed_value=values[f],reviewed_scope='CONSOLIDATED',reviewed_unit='VND',pdf_sha256='pdf1') for f in sorted(REQUIRED)]

    def test_complete_same_document_reference_keeps_negative_profit_cfo(self):
        r=document_vectors(self.facts());selected,status=choose_document(r)
        self.assertEqual(selected['values']['net_margin'],-0.01)
        self.assertEqual(selected['values']['operating_cashflow_to_assets'],-0.05)
        self.assertEqual(status,'SINGLE_REVIEWED_DOCUMENT_REFERENCE')

    def test_never_mix_documents_or_scopes_to_fill_fields(self):
        rows=self.facts();rows[-1]['pdf_sha256']='pdf2'
        self.assertIsNone(choose_document(document_vectors(rows))[0])
        rows=self.facts();rows[-1]['reviewed_scope']='ISSUER_NO_SUBSIDIARIES'
        self.assertIsNone(choose_document(document_vectors(rows))[0])

    def test_unknown_or_company_scope_and_inconsistent_unit_held(self):
        for scope in ['COMPANY_REPORTED','UNKNOWN']:
            rows=[dict(r,reviewed_scope=scope) for r in self.facts()]
            self.assertIsNone(choose_document(document_vectors(rows))[0])
        rows=self.facts();rows[0]['reviewed_unit']='VND_PER_SHARE'
        self.assertIsNone(choose_document(document_vectors(rows))[0])

    def test_conflicting_same_field_no_selection_or_averaging(self):
        rows=self.facts();rows.append(dict(rows[0],reviewed_value='999'))
        self.assertIsNone(choose_document(document_vectors(rows))[0])

    def test_multiple_vintages_never_choose_latest_even_if_values_equal(self):
        rows=self.facts()+[dict(r,pdf_sha256='pdf2') for r in self.facts()]
        self.assertEqual(choose_document(document_vectors(rows))[1],'MULTIPLE_DOCUMENT_VINTAGES_NO_SELECTION')

    def test_missing_and_bad_denominator_never_completed_with_zero(self):
        rows=self.facts()[1:];self.assertIsNone(choose_document(document_vectors(rows))[0])
        rows=self.facts()
        for row in rows:
            if row['field']=='current_liabilities':row['reviewed_value']='0'
        self.assertIsNone(choose_document(document_vectors(rows))[0])
