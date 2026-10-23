import copy
import json
import unittest
from pathlib import Path

from delta_t1.experiments.financial_pdf_reference_import import validate_review


class PdfReferenceImportTests(unittest.TestCase):
    def review(self):
        values=dict(current_assets=100,total_assets=200,total_liabilities=80,current_liabilities=40,net_revenue=300,gross_profit=60,net_profit=30,operating_cash_flow=50)
        fields=[dict(field=k,value=str(v),column_year=2018,visual_locator='code and row reviewed',column_label='Năm nay',ocr_receipt='page.json',ocr_receipt_sha256='OCR',pdf_page=7) for k,v in values.items()]
        return dict(symbol='AAA',year=2018,report_year=2018,interval='ANNUAL',unit='VND',scope='CONSOLIDATED',review_status='REVIEWED_REFERENCE_ONLY',review_method='AGENT_VISUAL_REVIEW_WITH_PINNED_OCR',pdf_path='doc.pdf',pdf_sha256='PDF',fields=fields)

    def pin(self,path,sha):
        if path=='page.json':
            return json.dumps(dict(status='OCR_CANDIDATE_ONLY',job=dict(pdf_sha256='PDF',pdf_path='doc.pdf',pdf_page=7,image_path='page.png',image_sha256='IMAGE'))).encode()
        return b'%PDF-1.7' if path=='doc.pdf' else b'PNG'

    def test_single_document_core_vector_uses_existing_reference_gate(self):
        vector,qa=validate_review(Path('.'),self.review(),self.pin)
        self.assertIsNotNone(vector['values'])
        self.assertTrue(any(r['difference'] is None for r in qa))

    def test_wrong_year_scope_and_missing_field_are_never_accepted(self):
        for key,value in [('report_year',2019),('unit','THOUSAND_VND'),('scope','STANDALONE')]:
            r=self.review();r[key]=value
            with self.assertRaises(ValueError):validate_review(Path('.'),r,self.pin)
        r=self.review();r['fields'].pop()
        with self.assertRaises(ValueError):validate_review(Path('.'),r,self.pin)

    def test_page_chain_and_duplicate_fields_fail_closed(self):
        r=self.review();r['fields'][0]['pdf_page']=8
        with self.assertRaisesRegex(ValueError,'chain mismatch'):validate_review(Path('.'),r,self.pin)
        r=self.review();r['fields'].append(copy.deepcopy(r['fields'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):validate_review(Path('.'),r,self.pin)

    def test_material_accounting_mismatch_is_not_hidden_by_review(self):
        r=self.review();r['fields'].append(dict(r['fields'][0],field='total_capital',value='250'))
        with self.assertRaisesRegex(ValueError,'accounting mismatch'):validate_review(Path('.'),r,self.pin)

    def test_cfo_component_bridge_must_match(self):
        r=self.review();r['cfo_signed_components']=['51']
        with self.assertRaisesRegex(ValueError,'CFO component'):validate_review(Path('.'),r,self.pin)
