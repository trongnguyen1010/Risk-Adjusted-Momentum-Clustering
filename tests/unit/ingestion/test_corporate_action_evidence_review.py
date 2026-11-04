from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from delta_t1.ingestion.corporate_action_evidence_review import (
    inspect_article, inspect_hose_calendar, ratios, ratio_relation, vi_decimal, review_price, diagnose_conflict,
)


def article(text, title="AAA: Thực hiện quyền mua cổ phiếu"):
    return (f'<h1 class="title-category">{title}</h1><div class="content-category">'
            f'Mã chứng khoán: AAA Ngày đăng ký cuối cùng: 21/03/2024 {text}</div>').encode()


class RawReviewTests(unittest.TestCase):
    def test_rights_two_legs_support_ratio_with_zero_padding_and_decimal_new_shares(self):
        r = ratios("Tỷ lệ thực hiện: 100:17,251827503 (01 cổ phiếu được hưởng 01 quyền, 100 quyền được mua 17,251827503 cổ phiếu mới)", "RIGHTS_ISSUE")
        self.assertEqual("EXPLICIT_RATIO_SUPPORTED", r["status"])
        v = r["values"][0]
        self.assertEqual(Fraction(Decimal(".17251827503")), Fraction(v["numerator"], v["denominator"]))

    def test_non_unit_allocation_is_multiplied_instead_of_assuming_one_right_per_share(self):
        r = ratios("Tỷ lệ thực hiện: 5:1 (1 cổ phiếu được hưởng 2 quyền, 10 quyền được mua 1 cổ phiếu mới)", "RIGHTS_ISSUE")
        v = r["values"][0]
        self.assertEqual(Fraction(1,5), Fraction(v["numerator"], v["denominator"]))

    def test_ownership_to_rights_to_shares_cannot_be_collapsed_into_direct_share_ratio(self):
        r=ratios("Tỷ lệ thực hiện: 100:75 (cổ đông sở hữu 01 cổ phiếu sẽ được 01 quyền mua, cổ đông sở hữu 100 quyền mua được quyền mua thêm 75 cổ phiếu)", "RIGHTS_ISSUE")
        self.assertEqual("EXACT",ratio_relation(.75,r))
        self.assertFalse(any(e["role"]=="EXPLICIT_EXISTING_TO_NEW_SHARES" for e in r["evidence"]))

    def test_rights_mua_and_co_phan_are_explicit_units(self):
        r=ratios("Tỷ lệ thực hiện: 3:2 (01 cổ phiếu được hưởng 01 quyền mua, cứ 03 quyền mua sẽ được mua 02 cổ phần mới)", "RIGHTS_ISSUE")
        self.assertEqual("SDK_10_DECIMAL_COMPARISON_COMPATIBLE",ratio_relation(.6666666667,r))

    def test_colon_and_explicit_rights_legs_disagreement_is_internal_source_conflict(self):
        r=ratios("Tỷ lệ thực hiện: 2:1 (sở hữu 01 cổ phần được hưởng 01 quyền, 01 quyền được mua 02 cổ phần mới)", "RIGHTS_ISSUE")
        self.assertEqual("RAW_INTERNAL_RATIO_DIFFERENCE",r["status"])

    def test_spelled_number_annotations_do_not_erase_raw_quote_offsets(self):
        r=ratios("Tỷ lệ thực hiện: 1:1 (01 (một) cổ phiếu được hưởng 01 (một) quyền, 01 (một) quyền được mua 01 (một) cổ phiếu mới)", "RIGHTS_ISSUE")
        self.assertEqual("EXACT",ratio_relation(1,r))
        for entry in r["evidence"]:
            q=entry["quote"];self.assertEqual(q["text"],r["evidence_text"][q["start"]:q["end"]])

    def test_execution_leg_alone_does_not_prove_ratio_per_existing_share(self):
        r = ratios("Tỷ lệ thực hiện: 3:2 (3 quyền được mua 2 cổ phiếu mới)", "RIGHTS_ISSUE")
        self.assertEqual("INCOMPLETE_OR_AMBIGUOUS_RIGHTS_LEGS", r["status"])
        self.assertEqual([], r["values"])

    def test_direct_share_semantics_and_declared_percent_disagreement_is_preserved(self):
        r = ratios("Tỷ lệ thực hiện: 10% (Người sở hữu 100 cổ phiếu được nhận 9 cổ phiếu mới)", "STOCK_DIVIDEND")
        self.assertEqual("RAW_INTERNAL_RATIO_DIFFERENCE", r["status"])

    def test_mixed_article_price_and_ratio_stay_in_rights_component(self):
        text = "1. Trả cổ tức bằng cổ phiếu Tỷ lệ thực hiện: 100:17 (sở hữu 100 cổ phiếu được nhận 17 cổ phiếu mới) 2. Thực hiện quyền mua cổ phiếu Giá phát hành: 10.000 đồng/cổ phiếu Tỷ lệ thực hiện: 100:20 (1 cổ phiếu được hưởng 1 quyền, 100 quyền được mua 20 cổ phiếu mới)"
        r = inspect_article(article(text, "AAA: Trả cổ tức bằng cổ phiếu; Thực hiện quyền mua cổ phiếu"), "VSDC", "RIGHTS_ISSUE", "https://vsdc.vn/vi/ad/1")
        self.assertEqual("EXPLICIT_COMPONENT_SECTION", r["component_scope"])
        self.assertEqual("EXACT", ratio_relation(.2,r["ratio"]))
        self.assertEqual("10000", r["prices"][0]["value_vnd"])

    def test_no_price_borrowed_from_another_component_without_explicit_boundary(self):
        r = inspect_article(article("Giá phát hành: 10.000 đồng/cổ phiếu Tỷ lệ thực hiện: 20%", "AAA: Trả cổ tức bằng cổ phiếu; Thực hiện quyền mua cổ phiếu"), "VSDC", "RIGHTS_ISSUE", "https://vsdc.vn/vi/ad/1")
        self.assertEqual("COMPONENT_UNRESOLVED", r["component_scope"])
        self.assertEqual([],r["prices"])

    def test_price_requires_explicit_per_share_unit_and_all_alternatives_retained(self):
        r = inspect_article(article("Giá phát hành: 10.000 đồng Giá đăng ký mua: 12.000 đồng/01 cổ phiếu"), "VSDC", "RIGHTS_ISSUE", "https://vsdc.vn/vi/ad/1")
        self.assertEqual([False,True],[p["explicit_per_share_unit"] for p in r["prices"]])
        self.assertEqual({"10000","12000"},{p["value_vnd"] for p in r["prices"]})

    def test_ordinary_boilerplate_adjustment_does_not_create_revision(self):
        r=inspect_article(article("TVLK phối hợp điều chỉnh thông tin sai lệch"), "VSDC", "RIGHTS_ISSUE", "url")
        self.assertEqual("NO_TITLE_REVISION_MARKER",r["revision_diagnostic"])
        revised=inspect_article(article("Thông tin điều chỉnh", "AAA: Điều chỉnh thời gian thực hiện quyền mua cổ phiếu"), "VSDC", "RIGHTS_ISSUE", "url")
        self.assertEqual("SCHEDULE_REVISION_CANDIDATE",revised["revision_diagnostic"])

    def test_rounding_diagnosis_does_not_change_either_ratio_or_tolerance(self):
        r=ratios("Tỷ lệ thực hiện: 3:1 (sở hữu 3 cổ phiếu được nhận 1 cổ phiếu mới)", "BONUS_SHARE")
        before=deepcopy(r)
        self.assertEqual("POSSIBLE_PROVIDER_ROUNDING_REVIEW_ONLY",ratio_relation(.33333333,r))
        self.assertEqual(before,r)
        self.assertEqual("DIFFERENT",ratio_relation(.2,r))

    def test_shorter_precision_in_source_is_diagnosis_only(self):
        r=ratios("Tỷ lệ thực hiện: 33,3333% (1 cổ phiếu được hưởng 1 quyền, 100 quyền được mua 33,3333 cổ phiếu mới)", "RIGHTS_ISSUE")
        self.assertEqual("POSSIBLE_SOURCE_PRECISION_DIFFERENCE_REVIEW_ONLY",ratio_relation(.33333333,r))

    def test_explicit_year_components_are_not_misdiagnosed_as_coarse_rounding(self):
        r=ratios("Tỷ lệ thực hiện:100:10 (sở hữu 100 cổ phiếu được nhận 10 cổ phiếu mới) Trong đó: Tỷ lệ thực hiện năm 2020: 100:5 Tỷ lệ thực hiện năm 2021: 100:5", "STOCK_DIVIDEND")
        result=diagnose_conflict(.05,r,[.05])
        self.assertEqual("RAW_ARTICLE_COMPONENTS_REQUIRE_REVIEW",result["diagnosis"])

    def test_component_sum_diagnosis_never_aggregates_duplicate_payload_variants(self):
        r=ratios("Tỷ lệ thực hiện:9,5% (sở hữu 1000 cổ phiếu được nhận 95 cổ phiếu mới)", "STOCK_DIVIDEND")
        result=diagnose_conflict(.07,r,[.07,.025,.07])
        self.assertEqual("COHORT_COMPONENT_SUM_CANDIDATE_REVIEW_ONLY",result["diagnosis"])
        self.assertTrue(result["no_aggregation_or_tolerance_applied"])

    def test_no_component_diagnosis_from_generic_boilerplate_outside_ratio_window(self):
        r=ratios("Tỷ lệ thực hiện:33,3333% (1 cổ phiếu được hưởng 1 quyền,100 quyền được mua 33,3333 cổ phiếu mới) Phương án xử lý cổ phiếu trong đó nhà đầu tư được mua", "RIGHTS_ISSUE")
        self.assertEqual("POSSIBLE_SOURCE_PRECISION_DIFFERENCE_REVIEW_ONLY",diagnose_conflict(.33333333,r,[.33333333])["diagnosis"])

    def test_vi_number_format_is_not_inferred_from_magnitude(self):
        self.assertEqual(Decimal("26400"),vi_decimal("26.400"))
        self.assertEqual(Decimal("17.25"),vi_decimal("17,25"))
        with self.assertRaises(ValueError): vi_decimal("17.25")

    def test_no_date_inference_and_quote_offsets_have_reproducible_text_basis(self):
        r=inspect_article(article("Giá phát hành: 10.000 đồng/cổ phiếu Tỷ lệ thực hiện: 10%"), "VSDC", "RIGHTS_ISSUE", "url")
        self.assertEqual([],r["dates"]["ex_date"])
        for items,basis in [(r["tickers"],r["article_text_for_review"]),(r["dates"]["record_date"],r["article_text_for_review"]),(r["prices"],r["component_text_for_review"]),(r["ratio"]["evidence"],r["ratio"]["evidence_text"])]:
            for item in items:
                q=item["quote"];self.assertEqual(q["text"],basis[q["start"]:q["end"]])

    def test_hose_json_requires_exact_code_epoch_and_category(self):
        e={"ticker":"AAA","values":{"ex_date":"2024-03-20"},"fields":{"ex_date":{"raw_value":1710892800},"event_type":{"raw_value":"04: quyền mua"}}}
        record={"code":"AAA","postedDate":1710892800,"catName":"04: quyền mua","id":1}
        result=inspect_hose_calendar(json.dumps({"data":{"list":[record]}}).encode(),e)
        self.assertEqual("/data/list/0",result["json_pointer"])
        record["code"]="BBB"
        with self.assertRaises(ValueError): inspect_hose_calendar(json.dumps({"data":{"list":[record]}}).encode(),e)

    def test_price_review_never_approves_canonical_even_with_supported_fields(self):
        a=inspect_article(article("Giá phát hành: 10.000 đồng/cổ phiếu Tỷ lệ thực hiện: 25%"), "VSDC", "RIGHTS_ISSUE", "url")
        row={"ticker":"AAA","original_sdk_row":{"ratio":.25},"official_links":[{"evidence_id":"one"}],"fields":{"record_date":{"original_review_value":"2024-03-21","proposed_value_pending_review":None},"rights_subscription_price":{"proposed_value_pending_review":10000,"candidate_values":[{"evidence":[{"evidence_id":"one"}]}]}}}
        result=review_price(row,{"one":a})
        self.assertEqual("RAW_PRICE_SUPPORTED_EVENT_TERMS_SUPPORTED",result["status"])
        self.assertFalse(result["canonical_approved"])
        self.assertEqual("MANUAL_REVIEW_REQUIRED",result["review_status"])


if __name__ == "__main__": unittest.main()
