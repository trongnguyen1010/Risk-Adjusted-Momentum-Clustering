import unittest
from pathlib import Path
import tempfile

from delta_t1.ingestion.corporate_actions.vsdc_pagination_audit import snapshot_coverage, physical_failures, supplementation_scope, locate_receipt_body
from delta_t1.ingestion.corporate_action_sources import discover_vsdc, SourceLimitation
from delta_t1.ingestion.corporate_action_sources import sha
from delta_t1.ingestion.corporate_actions.vsdc_pagination_audit import is_deferred_pagination


class PaginationAuditTests(unittest.TestCase):
    def test_partial_query_does_not_require_redownloading_known_details(self):
        snapshot = snapshot_coverage('Hiển thị: 1 - 20 / 63 bản ghi'.encode(), list(range(20)))
        self.assertEqual("QUERY_LIST_INCOMPLETE", snapshot["query_status"])
        self.assertEqual(43, snapshot["unseen_query_row_slots"])
        result = supplementation_scope(snapshot, ["a", "b"], ["a", "b", "other-query"])
        self.assertEqual(2, result["known_urls_reusable_from_cache"])
        self.assertEqual([], result["known_urls_without_raw"])
        self.assertFalse(result["redownload_existing_details"])
        self.assertFalse(result["bulk_acquisition_authorized"])

    def test_query_exhaustion_is_not_historical_event_coverage(self):
        snapshot = snapshot_coverage('Hiển thị: 1 - 3 / 3 bản ghi'.encode(), [1, 2, 3])
        self.assertEqual("SAVED_QUERY_EXHAUSTED_NOT_HISTORY_CERTIFIED", snapshot["query_status"])
        self.assertFalse(snapshot["historical_event_coverage_certified"])

    def test_empty_missing_or_contradictory_counts_are_not_no_event_attestations(self):
        self.assertEqual("EMPTY_QUERY_NOT_NO_EVENTS", snapshot_coverage('Hiển thị: 0 - 0 / 0 bản ghi'.encode(), [])["query_status"])
        self.assertEqual("SEARCH_LAYOUT_UNVERIFIED", snapshot_coverage(b'unknown layout', [])["query_status"])
        self.assertEqual("SEARCH_COUNT_OR_LINKS_INCONSISTENT", snapshot_coverage('Hiển thị: 1 - 20 / 10 bản ghi'.encode(), [1])["query_status"])
        self.assertEqual("SEARCH_COUNT_OR_LINKS_INCONSISTENT", snapshot_coverage('Hiển thị: 1 - 20 / 63 bản ghi'.encode(), [1])["query_status"])

    def test_repeated_ledger_copies_are_not_multiple_physical_failures(self):
        receipt = {"url": "https://vsdc.vn/vi/search?text=MBS", "method": "POST", "request_body": '{"CurrentPage":2}',
            "fetched_at": "2026-11-01T00:00:00Z", "status": 400, "source_hash": "empty"}
        rows = [{"ledger": p, "index": 1, "receipt": dict(receipt)} for p in ["parent", "child", "replay"]]
        records = physical_failures(rows)
        self.assertEqual(1, len(records)); self.assertEqual(3, len(records[0]["ledger_references"]))

    def test_reproduce_deferred_page_two_even_with_twenty_page_budget(self):
        class Transport:
            def __init__(self): self.calls = []
            def fetch(self, url, payload=None):
                self.calls.append((url, payload))
                if payload is not None: raise SourceLimitation('PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400')
                return ''.join(f'<a href="/vi/ad/{n}">MBS</a>' for n in range(20)) + 'Hiển thị: 1 - 20 / 63 bản ghi', {"status": 200}
        transport = Transport()
        links, check = discover_vsdc(transport, "MBS", max_pages=20, max_details=100)
        self.assertEqual(20, len(links)); self.assertEqual(2, check["failed_page"])
        self.assertEqual('PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400', check['pagination_error'])
        self.assertEqual(2, len(transport.calls))

    def test_detail_budget_is_distinct_from_pagination_failure(self):
        class Transport:
            def __init__(self): self.calls = 0
            def fetch(self, *args):
                self.calls += 1
                return ''.join(f'<a href="/vi/ad/{n}">X</a>' for n in range(20)) + 'Hiển thị: 1 - 20 / 63 bản ghi', {}
        transport = Transport()
        links, check = discover_vsdc(transport, "MBS", max_pages=20, max_details=10)
        self.assertEqual(10, len(links)); self.assertIsNone(check['pagination_error']); self.assertEqual(1, transport.calls)

    def test_merged_parent_relative_path_does_not_override_hash_verified_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrong=Path(tmp)/'parent.bin';correct=Path(tmp)/'child.bin'
            wrong.write_bytes(b'unrelated body');correct.write_bytes(b'')
            chosen,rejected=locate_receipt_body([wrong,correct],sha(b''))
            self.assertEqual(correct,chosen);self.assertEqual(str(wrong),rejected[0]['path'])
            with self.assertRaisesRegex(ValueError,'NO_RECEIPT_BODY'):
                locate_receipt_body([wrong],sha(b''))

    def test_deferred_diagnostic_suffix_preserves_same_root_cause(self):
        self.assertTrue(is_deferred_pagination('PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400'))
        self.assertTrue(is_deferred_pagination('PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400; use preserved public first-page links'))
        self.assertFalse(is_deferred_pagination('HTTP_400'))
        self.assertFalse(is_deferred_pagination(None))


if __name__ == "__main__": unittest.main()
