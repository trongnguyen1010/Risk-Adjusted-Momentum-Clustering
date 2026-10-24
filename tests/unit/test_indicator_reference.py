import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web/backend'))
from app.indicators import IndicatorReferences
from app.repository import MissingData

class IndicatorReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def fixture(self,rows):
        fields=['symbol','family','cohort_id','year','value','variant','snapshot_date','period_kind','source_adapter','price_date','status']
        source=self.root/'metrics.csv'
        with source.open('w',encoding='utf8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        manifest=self.root/'manifest.json';manifest.write_text(json.dumps({'metrics.csv':sha(source)}),encoding='utf8')
        config=dict(sources=[dict(id='test',label='Test only',manifest='manifest.json',manifest_sha256=sha(manifest),file='metrics.csv',file_sha256=sha(source))])
        (self.root/'config.json').write_text(json.dumps(config),encoding='utf8')
        return IndicatorReferences(self.root,'config.json')
    def test_sparse_family_is_null_and_decimal_preserved(self):
        r=self.fixture([dict(symbol='TEST',family='EPS',cohort_id='c',year='2025',value='1234.567890123456789')])
        result=r.stock('TEST');metrics=result['groups'][0]['metrics']
        self.assertEqual(len(metrics),6);self.assertEqual(metrics[0]['value'],'1234.567890123456789')
        self.assertIsNone(metrics[1]['value']);self.assertFalse(metrics[0]['strict_pit_ready'])
        self.assertFalse(r.stock('MISSING')['available'])
    def test_distinct_reference_dates_never_merge(self):
        base=dict(symbol='FPT',family='EPS',cohort_id='same-pdf',year='2024',period_kind='ANNUAL',source_adapter='FPT_CACHE_FLOW')
        r=self.fixture([dict(base,snapshot_date='2025-03-17',value='100'),dict(base,snapshot_date='2026-03-20',value='200')])
        groups=r.stock('FPT')['groups'];self.assertEqual(len(groups),2)
        self.assertEqual({g['metrics'][0]['value'] for g in groups},{'100','200'})
        self.assertTrue(all(g['metrics'][0]['price_date'] is None for g in groups))
    def test_period_eps_not_conflated_with_annual_or_quarter(self):
        base=dict(symbol='MWG',family='EPS',cohort_id='period',year='2014')
        r=self.fixture([dict(base,period_kind='YTD9',value='300'),dict(base,period_kind='QUARTER_STANDALONE3',value='100')])
        groups=r.stock('MWG')['groups'];self.assertEqual(len(groups),2)
        self.assertEqual({g['metrics'][0]['period_kind'] for g in groups},{'YTD9','QUARTER_STANDALONE3'})
    def test_unapproved_duplicate_fails_closed(self):
        row=dict(symbol='TEST',family='EPS',cohort_id='same',year='2025',value='100')
        r=self.fixture([row,dict(row,value='200')])
        with self.assertRaises(MissingData):r.stock('TEST')
    def test_source_checksum_mismatch_rejected(self):
        r=self.fixture([dict(symbol='TEST',family='EPS',cohort_id='c',year='2025',value='1')])
        with (self.root/'metrics.csv').open('a') as f:f.write('changed')
        with self.assertRaises(MissingData):r.stock('TEST')
    def test_missing_local_package_remains_unavailable(self):
        self.assertFalse(IndicatorReferences(self.root,'absent.json').stock('TEST')['available'])

    def test_all_null_cohort_preserves_missing_reason_in_six_slots(self):
        r=self.fixture([dict(symbol='TEST',family='F_SCORE',cohort_id='c',year='2025',value='',status='MISSING_INPUT')])
        body=r.stock('TEST')
        self.assertFalse(body['available']);self.assertEqual(len(body['groups']),1)
        metrics=body['groups'][0]['metrics'];self.assertEqual(len(metrics),6)
        self.assertEqual(metrics[3]['availability'],'MISSING_INPUT')
        self.assertEqual(metrics[0]['availability'],'REVIEW_PENDING')

    def test_missing_configured_source_is_reported_not_zero_coverage(self):
        r=self.fixture([dict(symbol='TEST',family='EPS',cohort_id='c',year='2025',value='100')])
        (self.root/'metrics.csv').unlink()
        coverage=r.coverage()
        self.assertEqual(coverage['unavailable_sources'],['test']);self.assertEqual(coverage['packages'],[])

    def test_response_contract_keeps_decimal_text_and_availability(self):
        from app.schemas import IndicatorResponse
        r=self.fixture([dict(symbol='TEST',family='EPS',cohort_id='c',year='2025',value='123.000000000000000001')])
        model=IndicatorResponse.model_validate(r.stock('TEST'))
        self.assertEqual(model.groups[0].metrics[0].value,'123.000000000000000001')

    def test_manifest_mismatch_rejected_even_with_csv_hash_valid(self):
        r=self.fixture([dict(symbol='TEST',family='EPS',cohort_id='c',year='2025',value='1')])
        (self.root/'manifest.json').write_text('{}',encoding='utf8')
        with self.assertRaises(MissingData):r.stock('TEST')

    def test_pinned_calculation_evidence_supplies_partial_reason_and_components(self):
        r=self.fixture([dict(symbol='TEST',family='F_SCORE',cohort_id='c',year='2025',value='',status='PARTIAL')])
        detail=self.root/'details.json';deps=self.root/'dependencies.json'
        detail.write_text(json.dumps([dict(symbol='TEST',family='F_SCORE',result=dict(value=None,known_signals=8))]),encoding='utf8')
        deps.write_text(json.dumps([dict(symbol='TEST',family='F_SCORE',missing=[dict(field='long_term_debt_including_current_portion',year=2024)])]),encoding='utf8')
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        manifest=self.root/'manifest.json';pins=json.loads(manifest.read_bytes())
        pins.update({detail.name:sha(detail),deps.name:sha(deps)});manifest.write_text(json.dumps(pins),encoding='utf8')
        config=json.loads((self.root/'config.json').read_bytes());source=config['sources'][0];source['manifest_sha256']=sha(manifest)
        source['supplements']=[dict(kind=k,file=p.name,sha256=sha(p)) for k,p in [('calculation_details',detail),('dependencies',deps)]]
        (self.root/'config.json').write_text(json.dumps(config),encoding='utf8')
        metric=r.stock('TEST')['groups'][0]['metrics'][3]
        self.assertEqual(metric['availability'],'MISSING_INPUT');self.assertEqual(metric['components']['known_signals'],8)
        self.assertIn('2024',metric['missing_inputs'])
        r.load.cache_clear();detail.write_text('[]',encoding='utf8')
        with self.assertRaises(MissingData):r.stock('TEST')

if __name__=='__main__':unittest.main()
