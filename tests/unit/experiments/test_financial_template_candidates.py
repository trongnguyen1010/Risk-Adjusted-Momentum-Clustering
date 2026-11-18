import json,unittest
from delta_t1.ingestion.cafef_financial import digest
from delta_t1.experiments.financial_template_candidates import parse_candidates


class CandidateTemplateAdapterTests(unittest.TestCase):
    def payload(self):
        return dict(isSuccess=True,value=dict(unit='VND',templace=[dict(code='NV',data=[
            dict(code='',name='Heading',number=1),dict(code='310',name='Debt',number=2),
            dict(code='',name='Uncoded child',number=3),dict(code='400',name='Total',number=4)])],
            data=[dict(code='NV',data=[dict(symbol='EIB',year=2025,quater=0,type='HK',time='2025',data=[
                dict(code='',value=0),dict(code='310',value=123),dict(code='',value=17),dict(code='400',value=140)])])]))

    def parse(self,p):
        raw=json.dumps(p).encode();return parse_candidates(raw,dict(symbol='EIB',statement='CDKT',mode='NAM',group='NV'),'source.json',digest(raw))

    def test_uncoded_rows_preserved_without_positional_label_assignment(self):
        rows=self.parse(self.payload());self.assertEqual(len(rows),4)
        self.assertEqual([r['value'] for r in rows],['0','123','17','140'])
        for row in [rows[0],rows[2]]:
            self.assertIsNone(row['label']);self.assertEqual(row['mapping_status'],'BLANK_CODE_QUARANTINED')
            self.assertEqual(len(row['label_candidates']),2);self.assertFalse(row['accepted'])
        self.assertEqual(rows[1]['label'],'Debt');self.assertEqual(rows[3]['label'],'Total')
        self.assertTrue(all(r['scope_status']=='UNRESOLVED' and not r['pit_ready'] for r in rows))

    def test_reordered_cells_match_unique_codes_without_shift_repair(self):
        p=self.payload();p['value']['data'][0]['data'][0]['data'].reverse();rows=self.parse(p)
        self.assertEqual(rows[0]['label'],'Total');self.assertEqual(rows[0]['value'],'140')
        self.assertEqual(rows[2]['label'],'Debt');self.assertIsNone(rows[1]['label'])

    def test_nonblank_template_duplicate_is_also_quarantined(self):
        p=self.payload();p['value']['templace'][0]['data'].append(dict(code='310',name='Different debt',number=5))
        row=self.parse(p)[1];self.assertIsNone(row['label']);self.assertEqual(row['mapping_status'],'DUPLICATE_TEMPLATE_CODE_QUARANTINED')

    def test_duplicate_observations_preserved_as_conflict_candidates(self):
        p=self.payload();p['value']['data'][0]['data'][0]['data'].append(dict(code='310',value=999))
        rows=[r for r in self.parse(p) if r['raw_code']=='310'];self.assertEqual(len(rows),2)
        self.assertTrue(all(r['mapping_status']=='DUPLICATE_OBSERVATION_CODE_QUARANTINED' and r['label'] is None for r in rows))

    def test_missing_unknown_zero_and_invalid_numeric_remain_distinct(self):
        for value,status in [(None,'MISSING'),(0,'NUMERIC_CANDIDATE'),(True,'BOOLEAN_QUARANTINED'),('NaN','INVALID_NUMERIC_QUARANTINED')]:
            p=self.payload();p['value']['data'][0]['data'][0]['data'][1]['value']=value
            row=self.parse(p)[1];self.assertEqual(row['value_status'],status)
            if value is None:self.assertIsNone(row['value'])
        p=self.payload();p['value']['data'][0]['data'][0]['data'][1]['code']='UNRECOGNIZED'
        self.assertEqual(self.parse(p)[1]['mapping_status'],'UNMAPPED_CODE_QUARANTINED')

    def test_issuer_fiscal_header_and_repeated_group_fail_closed(self):
        p=self.payload();p['value']['data'][0]['data'][0]['symbol']='WRONG'
        with self.assertRaises(ValueError):self.parse(p)
        p=self.payload();p['value']['data'][0]['data'][0]['quater']=True
        with self.assertRaises(ValueError):self.parse(p)
        p=self.payload();p['value']['data'].append(p['value']['data'][0])
        with self.assertRaises(ValueError):self.parse(p)

    def test_decimal_tokens_remain_exact_with_original_raw_hash(self):
        p=self.payload();raw=json.dumps(p).replace('123','123.1234567890123456789').encode()
        rows=parse_candidates(raw,dict(symbol='EIB',statement='CDKT',mode='NAM',group='NV'),'source.json',digest(raw))
        self.assertEqual(rows[1]['value'],'123.1234567890123456789')
        self.assertEqual(rows[1]['raw_value'],'123.1234567890123456789')
        with self.assertRaises(ValueError):parse_candidates(raw,{},'source.json','0'*64)


if __name__=='__main__':unittest.main()
