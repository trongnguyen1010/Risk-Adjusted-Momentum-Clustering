import json
import unittest
import csv,hashlib,tempfile
from pathlib import Path
from delta_t1.experiments.financial_annual_gap_audit import year_position,headers,legacy_state,quarter_group_coverage,numeric_value


class AnnualGapAuditTests(unittest.TestCase):
    def test_position_only_describes_observations_never_nonpublication(self):
        self.assertEqual(year_position(2023,[2022,2024]),'BETWEEN_OBSERVED_ANNUAL_YEARS')
        self.assertEqual(year_position(2016,[2017,2018]),'BEFORE_EARLIEST_OBSERVED_ANNUAL')
        self.assertEqual(year_position(2025,[2023,2024]),'AFTER_LATEST_OBSERVED_ANNUAL')
        self.assertEqual(year_position(2024,[2024]),'YEAR_PRESENT_IN_RAW_REQUIRES_REVIEW')
        self.assertEqual(year_position(2024,[]),'NO_ANNUAL_HEADERS_OBSERVED')

    def payload(self,quarter=0,symbol='AAA'):
        return json.dumps(dict(isSuccess=True,value=dict(data=[dict(symbol=symbol,year=2025,quater=quarter,type='K',time='2025',data=[dict(value=0),dict(value=None),dict(value=True),dict(value='NaN'),dict(value=-5)])]))).encode()

    def test_headers_keep_quarter_and_only_count_finite_numeric_cells(self):
        result=headers(self.payload(4),'KQKD','KQKD','AAA')
        self.assertEqual(result[0]['quarter'],4);self.assertEqual(result[0]['numeric_cells'],2)
        self.assertNotIn('accepted',result[0])

    def test_wrong_issuer_and_boolean_year_fail_closed(self):
        with self.assertRaises(ValueError):headers(self.payload(symbol='BBB'),'KQKD','KQKD','AAA')
        p=json.loads(self.payload());p['value']['data'][0]['year']=True
        with self.assertRaises(ValueError):headers(json.dumps(p).encode(),'KQKD','KQKD','AAA')

    def test_wrong_or_duplicate_group_never_selected(self):
        p=dict(isSuccess=True,value=dict(data=[dict(code='TN',data=[]),dict(code='TN',data=[])]))
        with self.assertRaises(ValueError):headers(json.dumps(p).encode(),'CDKT','TN','AAA')
        self.assertEqual(headers(json.dumps(p).encode(),'CDKT','NV','AAA'),[])

    def test_empty_legacy_columns_are_not_numeric_proof(self):
        self.assertEqual(legacy_state([]),'NO_MATCHING_LEGACY_ROWS')
        for value in [None,True,'NaN','Infinity','bad']:
            self.assertFalse(numeric_value(value))
            self.assertEqual(legacy_state([dict(field='total_assets',raw_value=value)]),'MATCHED_EMPTY_PLACEHOLDER_COLUMNS')
        self.assertTrue(numeric_value(0));self.assertTrue(numeric_value(-1))

    def test_quarter_group_presence_not_period_acceptance(self):
        rows=[dict(mode='QUY',quarter=str(q),statement=s,status='CANDIDATE_GROUPS_PRESENT') for q in [1,2,3,4] for s in ['CDKT','KQKD','LCTT']]
        self.assertEqual(quarter_group_coverage(rows),dict(q4_three_groups=True,all_four_quarters_three_groups=True))
        rows.pop();self.assertFalse(quarter_group_coverage(rows)['q4_three_groups'])
        self.assertFalse(quarter_group_coverage(rows)['all_four_quarters_three_groups'])

    def test_offline_audit_seals_outputs_without_fabricating_recovery(self):
        from delta_t1.experiments.financial_annual_gap_audit import run
        repo=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            def write(path,body):
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
                return hashlib.sha256(body).hexdigest()
            def js(path,value):return write(path,json.dumps(value).encode())
            def cs(path,rows,columns):
                import io
                f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
                return write(path,f.getvalue().encode())
            def source(path,manifest):
                return dict(path=path,manifest_sha256=js(path+'/manifest.json',manifest))
            for p in ['scripts/financial_annual_gap_audit.py','src/delta_t1/experiments/financial_annual_gap_audit.py','src/delta_t1/ingestion/cafef_financial_deep.py']:
                write(p,(repo/p).read_bytes())
            coverage=[dict(symbol=f'A{i:03}',registry_id=str(i),after_periods=9) for i in range(125)]
            gaps=[dict(r,year=2025,reasons=json.dumps(['NO_ANNUAL_PARTITION_IN_ACQUIRED_PAGES'])) for r in coverage]
            b=source('baseline',{'coverage-by-symbol.csv':cs('baseline/coverage-by-symbol.csv',coverage,list(coverage[0])),
                'remaining-document-review-candidates.csv':cs('baseline/remaining-document-review-candidates.csv',gaps,list(gaps[0]))})
            members={}
            for r in coverage:
                path='qa/symbols/'+r['registry_id']
                sha=js(path+'/manifest.json',{'input-pins.json':js(path+'/input-pins.json',{'sources':{}})})
                members[r['registry_id']]=dict(path=path+'/manifest.json',sha256=sha)
            q=source('qa',{'symbol-manifests.json':js('qa/symbol-manifests.json',members),
                'coverage.csv':cs('qa/coverage.csv',[],['symbol','year','mode','quarter','statement','status'])})
            cat=source('catalogue',{'document-links.json':js('catalogue/document-links.json',[])})
            legacy=source('legacy',{'files':{'candidates.jsonl':write('legacy/candidates.jsonl',b'')}})
            c=dict(version='financial-annual-gap-audit-v1',network_allowed=False,pdf_download_allowed=False,ocr_allowed=False,research_promotion_allowed=False,
                baseline_result=b,qa_result=q,catalogue_result=cat,legacy_result=legacy,output_root='output',report_root='report')
            js('config.json',c);result=run(root,'config.json')
            self.assertEqual(result['targets'],125);self.assertEqual(result['restored_rows'],0)
            self.assertEqual(result['full10_after'],462);self.assertFalse(result['strict_pit_ready'])
            self.assertTrue((root/result['output']/'manifest.json').exists())
