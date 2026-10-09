import unittest
from delta_t1.ingestion.financial_share_events import select_common_shares


class ShareEventTests(unittest.TestCase):
    def inputs(self):
        snapshot=dict(symbol='FPT',exchange='HOSE',publication_date='2026-03-19',balance_date='2025-12-31',
            common_shares=100,validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')
        event=dict(symbol='FPT',exchange='HOSE',event_id='ESOP',event_type='ACTUAL_COMMON_ISSUANCE',
            validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',publication_date='2026-08-21',
            known_notice_publication_date='2026-06-26',effective_not_before='2026-06-24',
            effective_not_after='2026-07-16',before_common_shares=100,new_shares=10,after_common_shares=110)
        calendar=[dict(exchange='HOSE',trade_date=d,is_open=True) for d in
            ['2026-03-19','2026-03-20','2026-06-26','2026-06-29','2026-08-21','2026-08-24','2026-08-28']]
        return snapshot,event,calendar

    def test_future_notice_and_publication_day_dont_apply_new_count(self):
        s,e,c=self.inputs()
        self.assertEqual(select_common_shares(s,[e],'2026-03-20',c)['value'],100)
        self.assertIsNone(select_common_shares(s,[e],'2026-06-29',c)['value'])
        self.assertIsNone(select_common_shares(s,[e],'2026-08-21',c)['value'])
        self.assertEqual(select_common_shares(s,[e],'2026-08-24',c)['value'],110)

    def test_plan_and_cash_do_not_issue_shares(self):
        s,e,c=self.inputs()
        for kind in ['APPROVED_PLAN','CASH_DIVIDEND']:
            e.update(event_type=kind,publication_date='2026-06-26')
            self.assertEqual(select_common_shares(s,[e],'2026-08-24',c)['value'],100)

    def test_known_effective_date_range_blocks_interior(self):
        s,e,c=self.inputs();e['publication_date']='2026-06-26'
        self.assertEqual(select_common_shares(s,[e],'2026-06-29',c)['status'],'EFFECTIVE_DATE_BASIS_UNRESOLVED')
        self.assertEqual(select_common_shares(s,[e],'2026-08-24',c)['value'],110)

    def test_snapshot_already_includes_event_no_double_add(self):
        s,e,c=self.inputs();e.update(effective_not_before='2025-05-01',effective_not_after='2025-06-30',
            publication_date='2026-03-19')
        self.assertEqual(select_common_shares(s,[e],'2026-03-20',c)['value'],100)

    def test_mismatch_duplicate_unknown_initial_and_rollforward_fail(self):
        for change in [dict(symbol='OTHER'),dict(after_common_shares=111),dict(effective_not_after=None),
                dict(validation_status='PENDING')]:
            s,e,c=self.inputs();e.update(change)
            self.assertIsNone(select_common_shares(s,[e],'2026-08-24',c)['value'])
        s,e,c=self.inputs()
        self.assertIsNone(select_common_shares(s,[e,e],'2026-08-24',c)['value'])
        s['validation_status']='PENDING'
        self.assertIsNone(select_common_shares(s,[e],'2026-08-24',c)['value'])
