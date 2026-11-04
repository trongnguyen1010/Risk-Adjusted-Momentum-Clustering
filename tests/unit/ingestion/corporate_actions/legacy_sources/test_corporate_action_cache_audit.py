from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_cache_audit import document_view,search_links,provider_id,candidate,assess_field


def article(text="",ticker="AAA",title="AAA: Thực hiện quyền mua cổ phiếu",day="21/03/2024"):
    return (f'<h1 class="title-category">{title}</h1><div class="time-newstcph">Cập nhật: {day}</div>'
        '<div class="content-category">'+(f'<span class="item-info">Mã chứng khoán:</span><span class="item-info">{ticker}</span>' if ticker else '')+
        f'<span class="item-info">Ngày đăng ký cuối cùng:</span><span class="item-info">{day}</span> '+text+'</div>').encode()


def doc(body=None):
    return document_view(body or article('Tỷ lệ thực hiện: 20% Giá phát hành: 10.000 đồng/cổ phiếu'),"https://vsdc.vn/vi/ad/12",["RIGHTS_ISSUE"])|{
        "document_id":"test","source_url":"https://vsdc.vn/vi/ad/12","legacy":{}}


def task(record="2024-03-21"):
    return {"ticker":"AAA","category":"RIGHTS_ISSUE","original_sdk_row":{"record_date":record,"ex_right_date":None,"ratio":.2,"public_date":"2024-03-01"}}


class CacheAuditTests(unittest.TestCase):
    def test_unit_must_belong_to_primary_price(self):
        d=doc(article('Giá phát hành: 10.000 đồng. Giá bán cổ phiếu dư: 10.000 đồng/cổ phiếu'))
        c=candidate(task(),d)
        self.assertEqual("RAW_AMOUNT_PRESENT_PRIMARY_UNIT_NOT_EXPLICIT",assess_field("rights_subscription_price",[c])["status"])

    def test_dates_are_independent_and_not_inferred(self):
        d=doc();self.assertEqual(["2024-03-21"],d["record_dates"]);self.assertEqual([],d["ex_dates"])
        self.assertEqual("MATCHED_CACHED_DOCUMENT_FIELD_NOT_EXPLICIT",assess_field("ex_date",[candidate(task(),d)])["status"])

    def test_meeting_record_date_cannot_link_to_rights(self):
        self.assertIsNone(candidate(task(),doc(article(title="AAA: Họp đại hội đồng cổ đông"))))

    def test_title_or_crawl_ticker_is_not_identity(self):
        d=doc(article(ticker=None));self.assertIsNone(d["ticker"]);self.assertEqual("AAA",d["title_ticker_hint"])
        self.assertIsNone(candidate(task(),d))

    def test_duplicate_conflicting_declared_tickers_are_unresolved(self):
        d=doc(article('<span class="item-info">Mã chứng khoán:</span><span class="item-info">BBB</span>'))
        self.assertIsNone(d["ticker"])

    def test_conflicting_original_date_blocks_strong_anchor(self):
        t=task();t["original_sdk_row"]["ex_right_date"]="2024-03-20"
        d=doc();d["ex_dates"]=["2024-03-19"]
        c=candidate(t,d);self.assertEqual("EXPLICIT_DATE_CONFLICT_REVIEW",c["mode"])
        self.assertFalse(assess_field("rights_subscription_price",[c])["raw_field_support_document_ids"])

    def test_original_sdk_z_date_uses_utc7_review_view(self):
        self.assertEqual("EXPLICIT_DATED_ANCHOR",candidate(task("2024-03-20T17:00:00.000Z"),doc())["mode"])

    def test_ratio_time_hint_is_not_event_proof(self):
        c=candidate(task(None),doc());self.assertEqual("TERMS_AND_TIME_HINT_CANDIDATE_ONLY",c["mode"])
        r=assess_field("record_date",[c]);self.assertEqual("CACHED_FIELD_CANDIDATE_EVENT_LINK_UNVERIFIED",r["status"])
        self.assertFalse(r["field_approved"]);self.assertEqual([],r["raw_field_support_document_ids"])

    def test_raw_presence_is_separate_from_normalized_presence(self):
        d=doc();r=assess_field("rights_subscription_price",[candidate(task(),d)])
        self.assertFalse(r["price_already_in_normalized_cache"])
        d["legacy"]={"RIGHTS_ISSUE":[{"rights_subscription_price":10000}]}
        r=assess_field("rights_subscription_price",[candidate(task(),d)])
        self.assertTrue(r["price_already_in_normalized_cache"]);self.assertFalse(r["field_approved"])

    def test_unrecognized_layout_is_not_empty_successful_article(self):
        d=document_view(b'<html>captcha</html>',"https://vsdc.vn/vi/ad/12",["RIGHTS_ISSUE"])
        self.assertEqual("UNRECOGNIZED",d["layout"]);self.assertIsNone(d["ticker"])

    def test_uncached_links_are_observed_candidates_not_missing_field_proof(self):
        links=search_links(b'<a href="/vi/ad/12">AAA: x</a><a href="https://other.test/vi/ad/13">x</a>',"https://vsdc.vn/vi/search")
        self.assertEqual(1,len(links));self.assertEqual("12",links[0]["provider_article_id"])
        r=assess_field("record_date",[],1);self.assertIn("RELEVANCE_UNVERIFIED",r["status"])
        self.assertEqual("NONE_IN_THIS_STAGE",r["network_action"])

    def test_provider_identity_does_not_require_url_variant_equality(self):
        self.assertEqual(provider_id("https://vsdc.vn/vi/ad/12"),provider_id("https://vsdc.vn/vi/ad1/12"))
        self.assertIsNone(provider_id("https://other.test/vi/ad/12"))

    def test_runner_path_escape_and_immutable_output(self):
        spec=importlib.util.spec_from_file_location("cache_runner",ROOT/"scripts/audit_corporate_action_cache_v1.py")
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        with self.assertRaises(ValueError):runner.inside(ROOT,"../escape")
        with self.assertRaises(FileExistsError):runner.run(ROOT)

    def test_bounded_file_reads_keep_input_order_and_propagate_failure(self):
        spec=importlib.util.spec_from_file_location("cache_runner",ROOT/"scripts/audit_corporate_action_cache_v1.py")
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        self.assertEqual([(i,i*i) for i in range(20)],list(runner.bounded_reads(lambda i:i*i,range(20),workers=2)))
        with self.assertRaises(ZeroDivisionError):list(runner.bounded_reads(lambda i:1/i,[1,0,2],workers=2))


if __name__=="__main__":unittest.main()
