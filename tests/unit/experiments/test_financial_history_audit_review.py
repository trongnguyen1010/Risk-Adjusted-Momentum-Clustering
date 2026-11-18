import copy
import unittest
from delta_t1.experiments.financial_history_audit_plan import FIELDS
from delta_t1.experiments.financial_history_audit_review import compare,quarantine_rows


class AuditReviewTests(unittest.TestCase):
    def fixture(self):
        sample=dict(id='seeded',symbol='AAA',year=2023,quarter=0,mode='NAM',provider_type='HK')
        facts=[];candidates=[]
        for field in sorted(FIELDS):
            instant=field in ['current_assets','total_assets','current_liabilities','total_liabilities','total_equity']
            facts.append(dict(field=field,value='123',pdf_page=5,row_label=field,period_kind='INSTANT' if instant else 'ANNUAL'))
            candidates.append(dict(symbol='AAA',year=2023,quarter=0,mode='NAM',provider_type='HK',field=field,value='123',provider_raw_unit='VND',unit_multiplier='1',unit_value='123',unit_status='RAW_VND_PROVIDER_DISPLAY_CONTRACT_REFERENCE'))
        review=dict(sample_id='seeded',symbol='AAA',year=2023,quarter=0,mode='NAM',source_report_year=2023,currency='VND',scope='CONSOLIDATED',scope_evidence='Explicit document title',fields=facts)
        return sample,candidates,review

    def test_match_keeps_provider_scope_and_research_closed(self):
        result=compare(*self.fixture())
        self.assertEqual(result['status'],'DOCUMENT_FIELD_AUDIT_MATCH_REFERENCE_ONLY')
        self.assertFalse(result['provider_scope_accepted']);self.assertFalse(result['pit_eligible'])
        self.assertEqual(result['accepted_facts'],0)

    def test_conflict_never_averaged_or_hidden(self):
        sample,rows,review=self.fixture();rows[0]['value']='-123';rows[0]['unit_value']='-123'
        result=compare(sample,rows,review)
        self.assertEqual(result['status'],'DOCUMENT_FIELD_AUDIT_CONFLICT')
        self.assertEqual(result['fields'][0]['difference'],'-246')

    def test_missing_duplicate_and_ambiguous_inputs_rejected(self):
        sample,rows,review=self.fixture()
        for altered in [review['fields'][:-1],review['fields'][:-1]+[review['fields'][0]]]:
            changed=copy.deepcopy(review);changed['fields']=altered
            with self.assertRaises(ValueError):compare(sample,rows,changed)
        with self.assertRaises(ValueError):compare(sample,rows+[rows[0]],review)

    def test_wrong_scope_currency_vintage_period_rejected(self):
        sample,rows,review=self.fixture()
        for key,value in [('sample_id','other'),('currency','MILLION_VND'),('scope','HK'),('source_report_year',2024),('year',2022)]:
            with self.subTest(key=key):
                changed=dict(review,**{key:value})
                with self.assertRaises(ValueError):compare(sample,rows,changed)

    def test_nonfinite_and_wrong_duration_rejected(self):
        sample,rows,review=self.fixture()
        changed=copy.deepcopy(review);changed['fields'][0]['value']='NaN'
        with self.assertRaises(ValueError):compare(sample,rows,changed)
        changed=copy.deepcopy(review);next(r for r in changed['fields'] if r['field']=='operating_cash_flow')['period_kind']='QUARTER_STANDALONE'
        with self.assertRaises(ValueError):compare(sample,rows,changed)

    def test_unknown_provider_unit_rejected_even_if_numbers_match(self):
        sample,rows,review=self.fixture();rows[0]['unit_status']='UNKNOWN'
        with self.assertRaises(ValueError):compare(sample,rows,review)

    def test_quarantine_keeps_exact_source_partition_and_never_overrides(self):
        sample,rows,review=self.fixture();rows[0]['value']='124';rows[0]['unit_value']='124'
        review['pdf_sha256']='pinned-document'
        quarantine=quarantine_rows([compare(sample,rows,review)])
        self.assertEqual(len(quarantine),1)
        row=quarantine[0]
        self.assertEqual((row['symbol'],row['year'],row['quarter'],row['mode'],row['provider_type']),('AAA',2023,0,'NAM','HK'))
        self.assertEqual(row['difference'],'1');self.assertEqual(row['pdf_sha256'],'pinned-document')
        self.assertFalse(row['accepted']);self.assertFalse(row['automatic_override'])

    def test_source_anomalies_not_lost_when_values_match(self):
        sample,rows,review=self.fixture();review['source_anomalies']=['Cover period differs from statement period']
        result=compare(sample,rows,review)
        self.assertEqual(result['source_anomalies'],review['source_anomalies'])
        self.assertEqual(quarantine_rows([result]),[])


if __name__=='__main__':unittest.main()
