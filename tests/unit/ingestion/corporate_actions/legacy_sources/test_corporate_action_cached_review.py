from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_cached_review import split_components,parse_scoped_article,review_link,primary_prices

STOCK="Trả cổ tức bằng cổ phiếu"
RIGHTS="Thực hiện quyền mua cổ phiếu"
DETAIL="Tỷ lệ thực hiện: 2:1 (01 cổ phiếu được hưởng 01 quyền, 02 quyền được mua 01 cổ phiếu mới)"


def body(text,title="AAA: Trả cổ tức bằng cổ phiếu và thực hiện quyền mua cổ phiếu"):
    return (f'<h1 class="title-category">{title}</h1><div class="content-category">'
        '<span class="item-info">Mã chứng khoán:</span><span class="item-info">AAA</span>'
        '<span class="item-info">Ngày đăng ký cuối cùng:</span><span class="item-info">21/03/2024</span> '
        +text+'</div>').encode()


def row(ratio=.5):
    return {"ticker":"AAA","original_sdk_row":{"record_date":"2024-03-20T17:00:00.000Z","ex_right_date":None,"ratio":ratio}}


def article(text=None):
    text=text or f'1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu {DETAIL}'
    return parse_scoped_article(body(text),"https://vsdc.vn/vi/ad/1")


class CachedReviewTests(unittest.TestCase):
    def test_summary_headings_are_ignored_without_terms(self):
        text=f'1. {STOCK} 2. {RIGHTS} Nội dung cụ thể: 1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu {DETAIL}'
        a=article(text)
        self.assertEqual("UNIQUE_TERMS_BEARING_COMPONENTS",a["partition"]["status"])
        self.assertEqual(.5,float(a["components"]["RIGHTS_ISSUE"]["ratio"]["values"][0]["decimal"]))

    def test_hierarchical_markers_separate_cash_and_rights(self):
        a=article(f'1.1. {STOCK}: Tỷ lệ thực hiện: 10% 1.2. {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu {DETAIL}')
        self.assertTrue(review_link(row(),a)["field_data_supported_pending_review"])
        self.assertNotIn("10%",a["components"]["RIGHTS_ISSUE"]["text"])

    def test_no_space_and_noun_headings_are_supported(self):
        a=article(f'a.{STOCK}: Tỷ lệ thực hiện: 10% b.Quyền mua cổ phiếu: Giá phát hành: 10.000 đồng/cổ phiếu {DETAIL}')
        self.assertTrue(review_link(row(),a)["field_data_supported_pending_review"])

    def test_two_terms_bearing_rights_sections_fail_closed(self):
        text=f'1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: {DETAIL} Giá phát hành: 10.000 đồng/cổ phiếu 3. {RIGHTS}: {DETAIL} Giá phát hành: 12.000 đồng/cổ phiếu'
        a=article(text)
        self.assertEqual({},a["components"])
        self.assertIn("COMPONENT_SCOPE_UNRESOLVED",review_link(row(),a)["blockers"])

    def test_unheaded_mixed_text_is_not_assigned_by_price_presence(self):
        a=article(f'{STOCK}: Tỷ lệ thực hiện: 10% {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu {DETAIL}')
        self.assertEqual({},a["components"])

    def test_all_detected_component_kinds_require_a_terms_section(self):
        a=article(f'1. {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu {DETAIL}')
        self.assertEqual("COMPONENT_SCOPE_UNRESOLVED",a["partition"]["status"])

    def test_residual_price_unit_cannot_complete_primary_price(self):
        a=article(f'1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: Giá phát hành: 10.000 đồng {DETAIL}. Giá bán cổ phiếu dư: 10.000 đồng/cổ phiếu')
        r=review_link(row(),a)
        self.assertEqual(["10000"],r["primary_price_values_vnd"])
        self.assertFalse(r["primary_unit_explicit"])
        self.assertIn("PRIMARY_PRICE_UNIT_EVIDENCE_REQUIRED",r["blockers"])

    def test_cash_amount_is_never_a_subscription_price(self):
        a=article(f'1. {STOCK}: Tỷ lệ thực hiện: 10% Giá phát hành: 1.000 đồng/cổ phiếu 2. {RIGHTS}: {DETAIL}')
        self.assertEqual([],review_link(row(),a)["primary_price_values_vnd"])

    def test_rounding_diagnostic_does_not_enable_matching(self):
        a=article();r=review_link(row(.50001),a)
        self.assertFalse(r["field_data_supported_pending_review"])
        self.assertIn("RATIO_TERM_REVIEW_REQUIRED",r["blockers"])
        self.assertFalse(r["rounding_override_applied"])

    def test_sdk_ten_decimal_compatibility_keeps_both_original_ratios(self):
        a=article(f'1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu Tỷ lệ thực hiện: 3:1 (01 cổ phiếu được hưởng 01 quyền, 03 quyền được mua 01 cổ phiếu mới)')
        r=review_link(row(.3333333333),a)
        self.assertEqual("SDK_10_DECIMAL_COMPARISON_COMPATIBLE",r["raw_ratio_relation"])
        self.assertEqual(.3333333333,r["sdk_ratio_unchanged"])
        self.assertEqual(3,r["source_ratio_exact"]["denominator"])
        self.assertFalse(r["field_approved"])

    def test_nonunit_allocation_is_multiplied(self):
        a=article(f'1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: Giá phát hành: 25.000 đồng/cổ phiếu Tỷ lệ thực hiện: 2:3 Phân bổ quyền: 2:3 (02 cổ phiếu được hưởng 03 quyền) Thực hiện: 1:1 (01 quyền được mua 01 cổ phiếu mới)')
        r=review_link(row(1.5),a);self.assertEqual("EXACT",r["raw_ratio_relation"])

    def test_conflicting_dates_do_not_use_ticker_alone(self):
        a=article();a["record_dates"]=["2024-03-22"]
        self.assertFalse(review_link(row(),a)["ticker_date_anchor_supported"])

    def test_multiple_primary_amounts_require_review(self):
        a=article(f'1. {STOCK}: Tỷ lệ thực hiện: 10% 2. {RIGHTS}: Giá phát hành: 10.000 đồng/cổ phiếu Giá chào bán: 12.000 đồng/cổ phiếu {DETAIL}')
        r=review_link(row(),a);self.assertIsNone(r["candidate_price_vnd_pending_review"])
        self.assertIn("PRIMARY_PRICE_MISSING_OR_AMBIGUOUS",r["blockers"])

    def test_revision_title_remains_pending(self):
        a=article();a["title_revision_candidate"]=True
        self.assertIn("REVISION_REVIEW_REQUIRED",review_link(row(),a)["blockers"])

    def test_exact_sections_and_quotes_preserve_offsets(self):
        a=article()
        for s in a["components"].values():
            self.assertEqual(s["text"],a["article_text"][s["start"]:s["end"]])
            for p in s["primary_prices"]:
                q=p["quote"];self.assertEqual(q["text"],s["text"][q["start"]:q["end"]])

    def test_runner_refuses_overwrite_and_path_escape(self):
        spec=importlib.util.spec_from_file_location("cached26_runner",ROOT/"scripts/review_cached_corporate_actions26_v1.py")
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        with self.assertRaises(FileExistsError):runner.run(ROOT)
        with self.assertRaises(ValueError):runner.safe(ROOT,"../escape")


if __name__=="__main__":unittest.main()
