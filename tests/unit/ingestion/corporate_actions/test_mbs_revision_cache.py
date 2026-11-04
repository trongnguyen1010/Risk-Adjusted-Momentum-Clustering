from copy import deepcopy
import unittest

from delta_t1.ingestion.corporate_actions.mbs_revision_cache import vsdc_search_coverage, classify_document, recommendation
from delta_t1.ingestion.corporate_action_decision_packet import BODY_CHANGE


TARGET = {"ticker": "MBS", "expected_price_vnd": 10000,
    "original_sdk_row": {"record_date": "2025-09-24T17:00:00Z", "ex_right_date": "2025-09-23T17:00:00Z"}}


def article(**changes):
    return {"ticker": "MBS", "title_ticker_hint": "MBS", "provider_article_id": "581051", "title": "Thực hiện quyền mua",
        "source_url": "https://example.test/article", "kinds": ["RIGHTS_ISSUE"], "record_dates": ["2025-09-25"],
        "ex_dates": ["2025-09-24"], "rights_codes": [], "article_text": "Mã chứng khoán: MBS. Ngày đăng ký cuối cùng: 25/09/2025",
        "title_change_markers": [], "body_change_quotes": [], "possible_outcome_title": False,
        "isolated_rights_prices_vnd": [10000], **changes}


class MbsCacheTests(unittest.TestCase):
    def test_search_page_twenty_of_sixty_three_is_not_exhaustive(self):
        result = vsdc_search_coverage("<p>Hiển thị: 1 - 20 / 63 bản ghi</p>")
        self.assertEqual(20, result["rows_on_page"])
        self.assertEqual(43, result["rows_outside_saved_page"])
        self.assertTrue(result["reported_count_is_query_rows_not_event_count"])

    def test_missing_contradictory_or_duplicate_coverage_markers_fail_closed(self):
        for text in ["No results", "Hiển thị: 20 - 1 / 63 bản ghi", "Hiển thị: 1 - 70 / 63 bản ghi",
                "Hiển thị: 1 - 20 / 63 bản ghi Hiển thị: 1 - 20 / 63 bản ghi"]:
            with self.subTest(text=text), self.assertRaises(ValueError): vsdc_search_coverage(text)

    def test_bond_prefix_does_not_identify_mbs_equity(self):
        result = classify_document(article(ticker="MBS12501"), TARGET)
        self.assertEqual("EXCLUDED_OTHER_SECURITY", result["status"])

    def test_next_year_same_price_rights_issue_is_not_target_round(self):
        result = classify_document(article(provider_article_id="193811", record_dates=["2026-04-03"], ex_dates=[]), TARGET)
        self.assertEqual("OTHER_OR_UNLINKED_DOCUMENT", result["status"])

    def test_body_anchored_change_must_be_held(self):
        result = classify_document(article(title_change_markers=["Đính chính"]), TARGET)
        self.assertEqual("LINKED_CHANGE_REVIEW_REQUIRED", result["status"])
        self.assertEqual("HOLD_LINKED_CHANGE_OR_SCOPE_CONFLICT", recommendation([result], ["coverage gap"])["status"])

    def test_unlinked_change_with_no_record_anchor_not_silently_ignored(self):
        result = classify_document(article(record_dates=[], ex_dates=[], article_text="Thông báo sửa đổi", title_change_markers=["Sửa đổi"]), TARGET)
        self.assertEqual("UNLINKED_CHANGE_CANDIDATE_REQUIRES_SCOPE_REVIEW", result["status"])

    def test_linked_conflicting_price_or_dates_prevents_clearance(self):
        price = classify_document(article(isolated_rights_prices_vnd=[20000]), TARGET)
        self.assertEqual("LINKED_PRICE_CONFLICT_REVIEW_REQUIRED", price["status"])
        dates = classify_document(article(record_dates=["2025-09-26"]), TARGET, selected_provider_ids=["581051"])
        self.assertEqual("LINKED_DATE_CONFLICT_REVIEW_REQUIRED", dates["status"])

    def test_normal_residual_share_cancellation_is_not_event_cancellation(self):
        text = "Cổ phiếu lẻ sẽ bị hủy bỏ. Số cổ phần chênh lệch sẽ bị hủy bỏ. Ngày hiệu lực hủy mã quyền mua 07/05/2026."
        quotes = [m.group() for m in BODY_CHANGE.finditer(text)]
        self.assertEqual([], quotes)
        result = classify_document(article(article_text=text, body_change_quotes=quotes), TARGET)
        self.assertEqual("TARGET_DOCUMENT_IN_CACHE", result["status"])

    def test_actual_event_cancellation_body_is_a_change_signal(self):
        text = "Mã chứng khoán: MBS. Ngày đăng ký cuối cùng: 25/09/2025. Hủy bỏ đợt chào bán."
        quotes = [m.group() for m in BODY_CHANGE.finditer(text)]
        self.assertTrue(quotes)
        result = classify_document(article(article_text=text, body_change_quotes=quotes), TARGET)
        self.assertEqual("LINKED_CHANGE_REVIEW_REQUIRED", result["status"])

    def test_absence_of_change_in_partial_cache_does_not_clear_owner_condition(self):
        source = article(); before = deepcopy(source)
        doc = classify_document(source, TARGET)
        result = recommendation([doc], ["VSDC_ONLY_20_OF_63_QUERY_ROWS_SAVED"])
        self.assertEqual("HOLD_CACHE_COVERAGE_GAP", result["status"])
        self.assertFalse(result["ready_to_recommend_owner_price_approval"])
        self.assertFalse(result["no_revision_exists_certified"])
        self.assertFalse(result["canonical_written"])
        self.assertEqual(before, source)

    def test_declared_scope_ready_is_still_unsigned_and_not_historical_certification(self):
        result = recommendation([classify_document(article(), TARGET)], [])
        self.assertTrue(result["ready_to_recommend_owner_price_approval"])
        self.assertFalse(result["no_revision_exists_certified"])
        self.assertFalse(result["source_selection_approved"])
        self.assertFalse(result["historical_identity_verified"])


if __name__ == "__main__": unittest.main()
