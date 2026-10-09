import unittest
from delta_t1.ingestion.financial_table_parser import grouped_integer, extract_cell


class TableParserTests(unittest.TestCase):
    def test_grouped_integer_keeps_sign_and_rejects_digit_repair(self):
        self.assertEqual(grouped_integer('(1.234,567)'), -1234567)
        for token in ['1.23.456', 'I.234.567', '(1.234', '1.234)', '-', '1.23']:
            with self.assertRaises(ValueError):
                grouped_integer(token)

    def test_row_boundary_does_not_capture_next_row_or_prior_year(self):
        def w(text,x,y,width=40):
            return dict(text=text,x=x,y=y,width=width,height=20)
        words=[w('2024',680,100),w('2023',900,100),w('300',50,200),w('310',50,250),
               w('10.000',600,199,120),w('9.000',820,199,120),w('8.000',600,249,120)]
        r=dict(width=1000,height=1000,lines=[dict(words=words)])
        self.assertEqual(extract_cell(r,dict(row_code='300'),2024)['value'],10000)
        words.append(w('7.000',600,205,120))
        self.assertIsNone(extract_cell(r,dict(row_code='300'),2024)['value'])

    def test_note_rectangle_reports_ambiguity_instead_of_guessing(self):
        r=dict(width=100,height=100,lines=[dict(words=[dict(text='1.000',x=50,y=50,width=20,height=10)])])
        self.assertEqual(extract_cell(r,dict(box=[.4,.4,.8,.8]),2024)['value'],1000)
        r['lines'][0]['words'].append(dict(text='2.000',x=50,y=60,width=20,height=10))
        self.assertIsNone(extract_cell(r,dict(box=[.4,.4,.8,.8]),2024)['value'])
