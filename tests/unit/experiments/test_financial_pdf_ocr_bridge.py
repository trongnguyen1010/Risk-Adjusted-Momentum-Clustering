import unittest
from delta_t1.experiments.financial_pdf_ocr_bridge import validate_selection


class OcrBridgeTests(unittest.TestCase):
    def test_unique_physical_pages_only(self):
        validate_selection([7,8,9,10],33)
        for pages in [[],[7,7],[0],[34],[True],list(range(1,42))]:
            with self.assertRaises(ValueError):validate_selection(pages,50 if len(pages)>40 else 33)
