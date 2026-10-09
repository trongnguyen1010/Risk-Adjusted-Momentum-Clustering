import unittest
from delta_t1.ingestion.financial_workflow import build

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.policy=dict(symbols=['FPT'],max_symbols=4,max_queue_cells=10,max_hints_per_field=2,
            financial_features_allowed=False,field_recipes={'debt':dict(requires_mapping=True,search_terms=['vay'])})
    def test_shared_dependencies_deduplicate_without_promoting_ocr(self):
        r=dict(rows=[],financial_features_allowed=False)
        t=dict(rows=[dict(symbol='FPT',year=2025,task=name,inputs=[dict(field='debt',year=2024)])
                     for name in ['F_SCORE','M_SCORE']],financial_features_allowed=False)
        docs=[dict(symbol='FPT',year=2024)]
        pages=[dict(symbol='FPT',year=2024,text='Vay dài hạn',pdf_sha256='a',pdf_page=50,ocr_path='o',image_path='i')]
        out=build(r,t,docs,pages,self.policy)
        self.assertEqual(out['unique_field_year_cells'],1)
        self.assertEqual(len(out['rows'][0]['consumers']),2)
        self.assertEqual(out['rows'][0]['action'],'REVIEW_SEMANTIC_MAPPING')
        self.assertEqual(len(out['rows'][0]['search_page_hints']),1)
        self.assertFalse(out['financial_features_allowed'])
    def test_accepted_values_still_require_publication_missing_docs_require_acquisition(self):
        r=dict(rows=[dict(symbol='FPT',year=2025,field='eps',evidence_status='DOCUMENT_VALUE_VERIFIED_PIT_PENDING'),
                     dict(symbol='FPT',year=2024,field='assets',evidence_status='RAW_UNVERIFIED')],financial_features_allowed=False)
        t=dict(rows=[],financial_features_allowed=False)
        out=build(r,t,[],[],self.policy)
        self.assertEqual({x['action'] for x in out['rows']},{'REVIEW_VINTAGE_AND_PUBLICATION','ACQUIRE_SCOPE_FRAMEWORK_DOCUMENT'})
        self.policy['document_gaps']=[dict(symbol='FPT',years=[2024])]
        out=build(r,t,[dict(symbol='FPT',year=2024)],[],self.policy)
        self.assertEqual(next(x for x in out['rows'] if x['year']==2024)['action'],'ACQUIRE_REQUIRED_FRAMEWORK_DOCUMENT')
        self.policy['max_queue_cells']=1
        with self.assertRaisesRegex(ValueError,'budget'):build(r,t,[],[],self.policy)
    def test_feature_promotion_and_unbounded_symbols_rejected(self):
        r=dict(rows=[],financial_features_allowed=True);t=dict(rows=[],financial_features_allowed=False)
        with self.assertRaises(ValueError):build(r,t,[],[],self.policy)
        r['financial_features_allowed']=False;self.policy['symbols']=['FPT']*5
        with self.assertRaises(ValueError):build(r,t,[],[],self.policy)
