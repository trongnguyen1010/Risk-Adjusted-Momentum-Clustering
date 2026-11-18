import unittest
from delta_t1.ingestion.financial_pdf_flow import annual_links, extraction_state


class PdfFlowTests(unittest.TestCase):
    def test_scope_quarter_and_year_are_not_inferred_from_filename_alone(self):
        html = '''<a href="a.pdf">Báo cáo tài chính hợp nhất 2018</a>
        <a href="b.pdf">Báo cáo tài chính riêng 2018</a>
        <a href="c.pdf">Báo cáo tài chính hợp nhất quý4 2018</a>
        <a href="d.pdf">Báo cáo tài chính hợp nhất 2019</a>'''
        found = annual_links(html, 'https://example.org/list', 2018, 'CONSOLIDATED')
        self.assertEqual([r['url'] for r in found], ['https://example.org/a.pdf'])

    def test_relative_links_deduplicate_and_reject_credentials_http(self):
        html = '<a href="a.pdf">BCTC 2018</a><a href="a.pdf">BCTC 2018</a><a href="http://x/a.pdf">BCTC 2018</a><a href="https://user:pass@x/a.pdf">BCTC 2018</a>'
        self.assertEqual(len(annual_links(html, 'https://x/', 2018, 'UNKNOWN')), 1)

    def test_readable_text_and_numbers_do_not_become_accepted_financial_values(self):
        result = extraction_state([dict(page=1, text='TỔNG CỘNG TÀI SẢN 270 2018 2017\n100.000 (50.000)')])
        self.assertFalse(result['accepted'])
        self.assertIsNone(result['candidates'][0]['value'])
        self.assertEqual(result['candidates'][0]['column_status'], 'YEAR_COLUMN_REVIEW_REQUIRED')

    def test_scanned_pages_are_queued_without_automatic_full_document_ocr(self):
        result = extraction_state([dict(page=1, text='')])
        self.assertEqual(result['low_text_pages'], [1])
        self.assertEqual(len(result['missing_candidate_fields']), 8)
        self.assertFalse(result['financial_features_allowed'])
