import unittest
from delta_t1.ingestion.financial_note_evidence import selections
class NoteEvidenceTests(unittest.TestCase):
    def test_remaining_pages_do_not_repeat_reviewed_prefix(self):
        r=selections(dict(financial_features_allowed=False,documents=[dict(symbol='FPT',quarter=0,total_pages=51)]))
        self.assertEqual((r[0]['first_page'],r[0]['pages_selected']),(19,33))
    def test_caps_and_wrong_scope_fail_before_rendering(self):
        good=dict(financial_features_allowed=False,documents=[dict(symbol='FPT',quarter=0,total_pages=51)])
        with self.assertRaises(ValueError):selections(good,max_total_pages=32)
        for changes in [dict(symbol='VNM'),dict(quarter=1),dict(total_pages=121)]:
            bad=dict(good,documents=[dict(good['documents'][0],**changes)])
            with self.assertRaises(ValueError):selections(bad)
