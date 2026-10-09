import unittest
from delta_t1.ingestion.financial_date_pit import next_session,overlay,select_as_of,task_date_coverage

class DatePitTests(unittest.TestCase):
    def test_task_date_coverage_cannot_promote_complete_input_or_use_future(self):
        ref=dict(publication=dict(publication_date='2025-03-14'),usable_from_date='2025-03-17',
            date_pit_status='DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR',
            fact=dict(symbol='FPT',year=2024,item='eps',value=100,unit='VND_PER_SHARE'))
        result=dict(rows=[dict(symbol='FPT',year=2024,field='eps',references=[ref])])
        tasks=dict(financial_features_allowed=False,rows=[dict(symbol='FPT',year=2024,task='EPS_RECOMPUTE',
            inputs=[dict(field='eps',year=2024)])])
        before=task_date_coverage(result,tasks,'2025-03-14')['rows'][0]
        after=task_date_coverage(result,tasks,'2025-03-17')['rows'][0]
        self.assertEqual(before['date_covered_inputs'],0)
        self.assertTrue(after['date_input_coverage_complete'])
        self.assertFalse(after['task_ready'])
        self.assertIsNone(after['computed_value'])

    def setUp(self):
        self.calendar=[dict(exchange='HOSE',trade_date=d,is_open=o) for d,o in
                       [('2025-03-13',True),('2025-03-14',True),('2025-03-15',False),('2025-03-17',True),('2025-03-18',True)]]
    def test_next_session_excludes_same_day_weekend_and_calendar_boundary(self):
        self.assertEqual(next_session('2025-03-14','HOSE',self.calendar)[0],'2025-03-17')
        self.assertEqual(next_session('2025-03-15','HOSE',self.calendar)[0],'2025-03-17')
        self.assertIsNone(next_session('2025-03-18','HOSE',self.calendar)[0])
        self.assertIsNone(next_session('2024-01-01','HOSE',self.calendar)[0])
        self.assertIsNone(next_session('2025-03-14','HNX',self.calendar)[0])
    def test_exact_hash_link_preserves_missing_vintages_without_fake_timestamp(self):
        r=dict(financial_features_allowed=False,rows=[dict(symbol='FPT',year=2024,field='eps',evidence_status='verified',
            document_evidence=[dict(symbol='FPT',pdf_sha256='a'),dict(symbol='FPT',pdf_sha256='b')])])
        p=dict(documents=[dict(symbol='FPT',pdf_sha256='a',publication_date='2025-03-14',exchange='HOSE',precision='DATE_ONLY',
                              validation_status='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED')])
        policy=dict(financial_features_allowed=False,timestamp_inference_allowed=False,max_documents=10,max_facts=10,
                    availability_rule='FIRST_OBSERVED_EXCHANGE_SESSION_STRICTLY_AFTER_PUBLICATION_DATE',
                    decision_frequency='DAILY_OR_MONTHLY',calendar_quality='OBSERVED')
        out=overlay(r,p,self.calendar,policy);refs=out['rows'][0]['references']
        self.assertEqual(refs[0]['usable_from_date'],'2025-03-17');self.assertIsNone(refs[0]['available_at'])
        self.assertEqual(refs[1]['date_pit_status'],'EXACT_VINTAGE_PUBLICATION_MISSING')
        p['documents'].append(p['documents'][0])
        with self.assertRaises(ValueError):overlay(r,p,self.calendar,policy)
    def test_revision_never_backfills_and_same_date_conflict_is_unresolved(self):
        def ref(pub,usable,value):return dict(publication=dict(publication_date=pub),usable_from_date=usable,
            date_pit_status='DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR',fact=dict(symbol='FPT',year=2024,item='eps',value=value,unit='VND_PER_SHARE'))
        old=ref('2025-03-14','2025-03-17',4944);new=ref('2025-04-02','2025-04-03',4292)
        self.assertIsNone(select_as_of([old,new],'2025-03-14')['selected'])
        self.assertEqual(select_as_of([old,new],'2025-03-17')['selected'][0]['fact']['value'],4944)
        self.assertEqual(select_as_of([old,new],'2025-04-03')['selected'][0]['fact']['value'],4292)
        conflict=ref('2025-04-02','2025-04-03',4500)
        self.assertIsNone(select_as_of([old,new,conflict],'2025-04-03')['selected'])
