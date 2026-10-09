import unittest
from delta_t1.ingestion.fpt_publication_evidence import parse_cards
class PublicationTests(unittest.TestCase):
    def card(self,url='/api/download?url=%2Fapi%2Fmedia%2Freport.pdf'):
        return '<span>Annual audited</span><div><span>Updated<!-- -->: <!-- -->19/03/2026</span><a href="'+url+'">'
    def test_link_and_date_are_preserved_without_timestamp(self):
        r=parse_cards(self.card())[0]
        self.assertEqual(r['publication_date'],'2026-03-19')
        self.assertEqual(r['attachment_url'],'https://fpt.com/api/media/report.pdf')
        self.assertIsNone(r['available_at']);self.assertIsNone(r['publication_timezone'])
    def test_external_or_path_traversal_is_not_a_download_target(self):
        for url in ['https://elsewhere.test/a.pdf','/api/download?url=%2Fapi%2Fmedia%2F..%2Fa.pdf']:
            with self.assertRaises(ValueError):parse_cards(self.card(url))
