import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from delta_t1.experiments.financial_selected_ocr import validate_jobs, run
from delta_t1.experiments.financial_history_documents import put

class SelectedOCRTests(unittest.TestCase):
    def job(self):return dict(id='p1',pdf_sha256='a',pdf_page=1,image_path='image.png')
    def test_cap_and_page_identity(self):
        with self.assertRaisesRegex(ValueError,'cap'):validate_jobs([self.job()]*41,40)
        with self.assertRaisesRegex(ValueError,'duplicate'):validate_jobs([self.job()]*2,40)
        with self.assertRaisesRegex(ValueError,'1-based'):validate_jobs([dict(self.job(),pdf_page=0)],40)
    def test_interrupted_reservation_not_repeated(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);put(out/'reservations/p1.json',dict(charged_pages=1))
            with patch('subprocess.run',side_effect=AssertionError('OCR called')):
                with self.assertRaisesRegex(ValueError,'interrupted'):run(out,dict(jobs=[self.job()],max_ocr_pages=1),out)
    def test_completed_page_does_not_consume_second_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);put(out/'pages/p1.json',dict(status='OCR_CANDIDATE_ONLY'))
            with patch('subprocess.run',side_effect=AssertionError('OCR called')):
                run(out,dict(jobs=[self.job()],max_ocr_pages=1),out)
