import copy,unittest
from delta_t1.ingestion.financial_ocr_probe import code_cell


def record():
    def w(t,x,y,width=60):return dict(text=t,x=x,y=y,width=width,height=20)
    words=[w('2025',600,200),w('2024',820,200),w('270',430,250),w('1.234.567',550,250,110),w('1.200.000',770,250,110)]
    return dict(width=1000,height=1400,lines=[dict(words=words)])


class OcrProbeTests(unittest.TestCase):
    def test_reviewed_code_band_excludes_equation_duplicate(self):
        r=record();w=copy.deepcopy(r['lines'][0]['words'][2]);w['x']=200;w['y']=300
        r['lines'][0]['words'].append(w)
        self.assertIsNone(code_cell(r,'270',['2025'],['2024'])['value'])
        self.assertEqual(code_cell(r,'270',['2025'],['2024'],code_band=[.4,.5])['value'],1234567)

    def test_reviewed_end_begin_year_header_labels_and_multiline_pair(self):
        r=record();r['lines'][0]['words'][0]['text']='näm';r['lines'][0]['words'][1]['text']='näm'
        r['lines'][0]['words'][1]['y']=220
        self.assertEqual(code_cell(r,'270',['näm'],['näm'])['value'],1234567)
        with self.assertRaises(ValueError):code_cell(r,'270',['näm'],['näm'],1)

    def test_year_columns_and_code_in_middle(self):
        self.assertEqual(code_cell(record(),'270',['2025'],['2024'])['value'],1234567)
        self.assertEqual(code_cell(record(),'270',['2025'],['2024'],-1)['value'],1200000)

    def test_missing_and_ocr_letter_not_repaired_or_zero(self):
        for token in ['-','1.2O4.567','']:
            r=record();r['lines'][0]['words'][3]['text']=token
            self.assertIsNone(code_cell(r,'270',['2025'],['2024'])['value'])

    def test_duplicate_headers_or_rows_fail(self):
        for index in [0,2]:
            r=record();r['lines'][0]['words'].append(copy.deepcopy(r['lines'][0]['words'][index]))
            self.assertIsNone(code_cell(r,'270',['2025'],['2024'])['value'])

    def test_adjacent_row_not_taken(self):
        r=record();r['lines'][0]['words'][3]['y']=290
        self.assertIsNone(code_cell(r,'270',['2025'],['2024'])['value'])


if __name__=='__main__':unittest.main()
