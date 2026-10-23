import unittest
from delta_t1.experiments.financial_cached_fact_verification import compare_fact, replay_z, normalize_reviewed_schema


class CachedFactVerificationTests(unittest.TestCase):
    def test_reviewed_spelling_normalization_never_changes_number_or_api_units(self):
        original=dict(field='weighted_basic_shares',unit='shares',value='123')
        normalized=normalize_reviewed_schema(original)
        self.assertEqual(normalized['unit'],'SHARES');self.assertEqual(normalized['value'],'123')
        self.assertEqual(original['field'],'weighted_basic_shares')
        self.assertEqual(normalize_reviewed_schema(dict(field='total_assets',unit='VND',value='100'))['value'],'100')
    def test_same_field_different_year_not_compared(self):
        fact=dict(field='total_assets',year=2025,value='100')
        self.assertEqual(compare_fact(fact,[dict(field='total_assets',year=2024,value='100')]),[])

    def test_provider_partitions_and_missing_values_retained(self):
        fact=dict(field='total_assets',year=2025,value='100')
        cells=[dict(field='total_assets',year=2025,provider_type=p,value=v,observations=[]) for p,v in [('HK','100.0'),('K','90'),('H',None)]]
        self.assertEqual([r['status'] for r in compare_fact(fact,cells)],['EXACT_NUMERIC_MATCH','NUMERIC_DIFFERENCE_OR_VINTAGE','API_VALUE_AMBIGUOUS_OR_MISSING'])

    def fixture(self):
        values=dict(current_assets='400',current_liabilities='200',total_assets='1000',retained_earnings='100',total_equity='600',total_liabilities='400',profit_before_tax='70',interest_expense='10')
        facts=[dict(symbol='AAA',year=2025,scope='CONSOLIDATED',field=f,value=v,unit='VND',verification_id=f,provenance=dict(pdf_sha256='pdf')) for f,v in values.items()]
        matches=[dict(verification_id=f,field=f,api_comparisons=[dict(provider_type='HK',status='EXACT_NUMERIC_MATCH')]) for f in values]
        return facts,matches

    def test_same_pdf_exact_inputs_reproduce_frozen_z(self):
        facts,matches=self.fixture();rows=replay_z(facts,matches)
        self.assertEqual(rows[0]['value'],'7.0006')
        self.assertFalse(rows[0]['api_document_vintage_verified'])
        self.assertFalse(rows[0]['financial_features_allowed'])

    def test_no_cross_pdf_year_scope_or_provider_input_filling(self):
        for field,new in [('year',2024),('scope','ISSUER_NO_SUBSIDIARIES'),('provenance',dict(pdf_sha256='other'))]:
            facts,matches=self.fixture();facts[-1][field]=new
            self.assertEqual(replay_z(facts,matches),[])
        facts,matches=self.fixture();matches[-1]['api_comparisons'][0]['provider_type']='K'
        self.assertEqual(replay_z(facts,matches),[])

    def test_numeric_difference_conflicting_reference_and_balance_hold(self):
        facts,matches=self.fixture();matches[-1]['api_comparisons'][0]['status']='NUMERIC_DIFFERENCE_OR_VINTAGE'
        self.assertEqual(replay_z(facts,matches),[])
        facts,matches=self.fixture();facts.append(dict(facts[-1],value='99'))
        self.assertEqual(replay_z(facts,matches),[])
        facts,matches=self.fixture();facts[2]['value']='999'
        self.assertEqual(replay_z(facts,matches),[])
