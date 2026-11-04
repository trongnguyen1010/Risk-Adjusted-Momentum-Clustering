from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_decision_packet import change_scope
from delta_t1.ingestion.corporate_action_revision_review import review_edge, review_case, schedule


def doc(text, url="original", codes=None):
    return {"article_text": text, "source_url": url, "rights_codes": codes or [],
            "change_scope_review": change_scope(text, "AAA: Đính chính tài khoản" if "Số tài khoản" in text else "AAA: Điều chỉnh thời gian thực hiện quyền mua")}


def fixture():
    anchor = "Mã chứng khoán: AAA Ngày đăng ký cuối cùng: 20/01/2021 "
    old = "Thời gian đăng ký và đặt mua cổ phiếu: từ ngày 01/02/2021 đến ngày 01/03/2021. "
    new = "Thời gian đăng ký và đặt mua cổ phiếu: từ ngày 01/02/2021 đến ngày 12/03/2021. "
    original = doc(anchor + old)
    revision = doc(anchor + "Thông tin đã thông báo tại Thông báo số 44/TB-VSD ngày 08/01/2021: " + old
                   + "Thông tin điều chỉnh: " + new
                   + "Các nội dung khác trên thông báo số 44/TB-VSD ngày 08/01/2021 của VSD không thay đổi.", "revision")
    return original, revision


class RevisionReviewTests(unittest.TestCase):
    def edge(self, original, revision):
        return review_edge(original, original, revision, "AAA", "2021-01-20")

    def test_matching_schedule_supports_context_without_approval_or_notice_binding(self):
        original, revision = fixture()
        result = self.edge(original, revision)
        self.assertTrue(result["contextual_link_supported"])
        for key in ["lineage_approved", "historical_identity_verified", "publication_timestamp_inferred",
                    "terminal_execution_confirmed", "official_notice_number_to_article_binding_verified"]:
            self.assertFalse(result[key])

    def test_missing_intermediate_schedule_is_hold_even_same_ticker_date(self):
        original, revision = fixture()
        original["article_text"] = original["article_text"].replace("01/03/2021", "20/02/2021")
        result = self.edge(original, revision)
        self.assertFalse(result["contextual_link_supported"])
        self.assertIn("PREDECESSOR_SCHEDULE_GAP:subscription", result["hold_reasons"])

    def test_conflicting_notice_dates_are_not_silently_corrected(self):
        original, revision = fixture()
        revision = doc(revision["article_text"].replace("khác trên thông báo số 44/TB-VSD ngày 08/01", "khác trên thông báo số 44/TB-VSD ngày 07/01"))
        result = self.edge(original, revision)
        self.assertIn("CONTRADICTORY_NOTICE_DATE_LITERALS", result["hold_reasons"])
        self.assertEqual(["44/TB-VSD"], result["notice_ids_with_conflicting_date_literals"])

    def test_title_or_folder_hint_alone_does_not_link(self):
        original, revision = fixture()
        revision["article_text"] = revision["article_text"].replace("Mã chứng khoán: AAA", "Tên thư mục AAA")
        self.assertIn("EXPLICIT_BODY_TICKER_RECORD_ANCHOR_MISSING", self.edge(original, revision)["hold_reasons"])

    def test_wrong_record_date_holds_despite_shared_rights_code(self):
        original, revision = fixture()
        original["rights_codes"] = revision["rights_codes"] = ["MIRAAA211"]
        revision["article_text"] = revision["article_text"].replace("20/01/2021", "21/01/2021")
        self.assertFalse(self.edge(original, revision)["contextual_link_supported"])

    def test_second_event_anchor_prevents_cross_event_borrowing(self):
        original, revision = fixture()
        revision["article_text"] += " Mã chứng khoán: BBB Ngày đăng ký cuối cùng: 21/01/2021"
        self.assertIn("CONFLICTING_BODY_ENTITY_OR_RECORD_ANCHOR", self.edge(original, revision)["hold_reasons"])

    def test_prior_revision_compares_after_not_its_old_schedule(self):
        original, first = fixture()
        text = first["article_text"].replace("01/03/2021", "12/03/2021")
        # Replace only the after section; predecessor still has original/before.
        i = text.index("Thông tin điều chỉnh:")
        text = text[:i] + text[i:].replace("12/03/2021", "20/03/2021")
        second = doc(text, "second")
        self.assertTrue(review_edge(original, first, second, "AAA", "2021-01-20")["contextual_link_supported"])

    def test_missing_unchanged_clause_holds(self):
        original, revision = fixture()
        revision = doc(revision["article_text"].split("Các nội dung khác")[0])
        self.assertFalse(self.edge(original, revision)["contextual_link_supported"])

    def test_ambiguous_predecessor_schedule_holds(self):
        original, revision = fixture()
        original["article_text"] += "Thời gian đăng ký và đặt mua cổ phiếu: Từ ngày 01/02/2021 đến ngày 20/03/2021"
        self.assertFalse(self.edge(original, revision)["contextual_link_supported"])

    def test_account_change_requires_old_account_in_original(self):
        anchor = "Mã chứng khoán: AAA Ngày đăng ký cuối cùng: 20/01/2021 "
        original = doc(anchor + "Số tài khoản: 12345")
        revision = doc(anchor + "Thông tin đã thông báo tại Thông báo số 44/TB-VSD ngày 08/01/2021: Số tài khoản: 12345 "
            + "Thông tin đính chính: Số tài khoản: 67890 Lý do đính chính: nhầm tài khoản. "
            + "Các nội dung khác tại Thông báo số 44/TB-VSD ngày 08/01/2021 không thay đổi.")
        self.assertTrue(self.edge(original, revision)["contextual_link_supported"])
        original["article_text"] = anchor + "Số tài khoản: 99999"
        self.assertIn("ACCOUNT_CONTINUITY_UNRESOLVED", self.edge(original, revision)["hold_reasons"])

    def test_rights_code_expiry_is_schedule_not_offer_execution(self):
        result = schedule("Ngày hiệu lực hủy mã quyền mua: 04/03/2021")
        self.assertEqual([["2021-03-04"]], result["rights_code_expiry"]["values"])
        self.assertNotIn("offering_cancelled", result)

    def test_date_width_normalization_preserves_literal(self):
        result = schedule("Thời gian chuyển nhượng quyền mua: Từ ngày 30/8/2021 đến 12/10/2021")
        self.assertEqual([["2021-08-30", "2021-10-12"]], result["transfer"]["values"])
        self.assertIn("30/8/2021", result["transfer"]["quotes"][0]["text"])

    def test_member_deadline_retains_dossier_and_list_wording(self):
        for label in ["Danh sách", "Hồ sơ"]:
            result = schedule("Thời hạn TVLK nộp " + label + " đặt mua cổ phiếu và chuyển tiền đặt mua cổ phiếu cho VSD: 03/03/2021")
            self.assertEqual([["2021-03-03"]], result["member_deadline"]["values"])
            self.assertIn(label, result["member_deadline"]["quotes"][0]["text"])

    def test_case_keeps_sdk_and_holds_when_any_edge_unresolved(self):
        original, revision = fixture()
        original["article_text"] = original["article_text"].replace("01/03/2021", "20/02/2021")
        request = {"ticker": "AAA", "original_record_date_review_view": "2021-01-20", "vci_payload_sha256": "payload",
            "original_sdk_row": {"ratio": .33333333}, "sources": [],
            "conditional_price_selection_after_lineage_review": {"value": "10000", "unit": "VND/share"},
            "conditional_exact_source_ratio_after_lineage_review": {"numerator": 1, "denominator": 3}}
        saved = deepcopy(request)
        result = review_case(request, original, [revision])
        self.assertEqual(saved, request)
        self.assertEqual("HOLD_LINEAGE_GAP_OR_ANOMALY", result["status"])
        self.assertIsNone(result["owner_decision"])
        self.assertEqual(0, result["applied_fields"])
        self.assertTrue(result["revision_flags_preserved"])


if __name__ == "__main__":
    unittest.main()
