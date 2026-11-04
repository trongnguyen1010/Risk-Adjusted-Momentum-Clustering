import copy
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions.hnx_components import parse_popup_components, parse_details_v2, terms_v2
from delta_t1.ingestion.hnx_detail_parser import parse_popup, parse_details
from delta_t1.ingestion.corporate_action_sources import SourceLimitation, sha
from delta_t1.ingestion.hnx_announcement_discovery import discover
from delta_t1.ingestion.hnx_announcement_details import acquire_details
from tests.unit.ingestion.test_hnx_announcement_discovery import profile
from tests.unit.ingestion.test_hnx_detail_parser import inputs, popup, pipeline, listing, Transport, STOCK_TITLE, STOCK

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures/corporate_actions/hnx_components_v2"
MBS_TITLE = "Ngày đăng ký cuối cùng trả cổ phiếu thưởng cho cổ đông hiện hữu, phát hành cổ phiếu cho cổ đông hiện hữu"
TNG_TITLE = "Ngày đăng ký cuối cùng trả cổ tức bằng cổ phiếu cho cổ đông hiện hữu"


def sample(ticker, aid, title):
    html = (FIXTURES / f"{ticker.lower()}_{aid}.html").read_text(encoding="utf-8-sig")
    detail, record, clock = inputs(ticker, title)
    record["provider_article_id"] = aid
    record["detail_request"]["form"]["pArticlesID"] = aid
    detail["request_body"] = f"pArticlesID={aid}&pFileAttach=0"
    detail["source_hash"] = sha(html.encode())
    return html, detail, record, clock


def values(obs): return {f: v["normalized_value"] for f, v in obs["fields"].items()}


class HnxComponentTests(unittest.TestCase):
    def test_real_tng_optional_them_allocation_recovers_ratio_without_legacy_change(self):
        args = sample("TNG", "523090", TNG_TITLE)
        legacy = parse_popup(*args)
        self.assertNotIn("stock_dividend_ratio", values(legacy))
        self.assertIn("RATIO_PARSE_AMBIGUITY", legacy["parser_issues"])
        repaired, = parse_popup_components(*args)
        self.assertEqual(.08, values(repaired)["stock_dividend_ratio"])
        self.assertEqual("2024-07-12", values(repaired)["ex_date"])
        self.assertEqual("100:8", repaired["fields"]["stock_dividend_ratio"]["raw_value"])
        self.assertNotIn("RATIO_PARSE_AMBIGUITY", repaired["parser_issues"])
        self.assertEqual(legacy["source_evidence"], repaired["source_evidence"])
        self.assertEqual(legacy["observed_at"], repaired["observed_at"])

    def test_real_mbs_components_do_not_leak_ratios_price_or_identity(self):
        args = sample("MBS", "581051", MBS_TITLE)
        original = copy.deepcopy(args)
        legacy = parse_popup(*args)
        self.assertEqual("OTHER", values(legacy)["event_type"])
        bonus, rights = parse_popup_components(*args)
        self.assertEqual("BONUS_SHARE", values(bonus)["event_type"])
        self.assertEqual(.03, values(bonus)["bonus_ratio"])
        self.assertNotIn("rights_subscription_price", values(bonus))
        self.assertNotIn("rights_ratio", values(bonus))
        self.assertEqual("RIGHTS_ISSUE", values(rights)["event_type"])
        self.assertEqual(.12, values(rights)["rights_ratio"])
        self.assertEqual(10000, values(rights)["rights_subscription_price"])
        self.assertNotIn("bonus_ratio", values(rights))
        self.assertNotEqual(bonus["observation_id"], rights["observation_id"])
        for obs in [bonus, rights]:
            self.assertEqual("2025-09-24", values(obs)["ex_date"])
            self.assertEqual("2025-09-25", values(obs)["record_date"])
            self.assertEqual("HNX_ARTICLE:581051", obs["event_reference"])
            self.assertIsNone(obs["source_published_at"])
            self.assertIsNone(obs["source_timing"]["timezone"])
            self.assertIn("SOURCE_PUBLIC_TIME_UNVERIFIED", obs["parser_issues"])
            self.assertIn("HISTORICAL_IDENTITY_NOT_CERTIFIED", obs["parser_issues"])
            evidence = obs["component_evidence"]
            raw = evidence["full_article_raw_terms"]
            self.assertEqual(evidence["component_text"], raw[evidence["flattened_body_start"]:evidence["flattened_body_end"]])
            self.assertEqual(legacy["source_evidence"], obs["source_evidence"])
            self.assertEqual(legacy["observed_at"], obs["observed_at"])
        self.assertEqual(original, args)

    def test_explicit_allocation_required_and_conflicts_are_not_accepted(self):
        base = "Trả cổ tức bằng cổ phiếu; Tỷ lệ thực hiện: 100:8. "
        for suffix in ["", "Người sở hữu 100 cổ phiếu được nhận thêm 9 cổ phiếu mới",
                "Người sở hữu 100 cổ phiếu được nhận thêm 8 cổ phiếu mới. Người có 100 cổ phiếu được nhận thêm 9 cổ phiếu mới",
                "Người sở hữu 100 cổ phiếu được nhận 8 cổ phiếu mới. Người có 100 cổ phiếu được nhận thêm 9 cổ phiếu mới",
                "Tỷ lệ thực hiện: 10%; Người sở hữu 100 cổ phiếu được nhận thêm 8 cổ phiếu mới"]:
            with self.subTest(suffix=suffix):
                parsed, issues = terms_v2("STOCK_DIVIDEND", base + suffix)
                self.assertNotIn("stock_dividend_ratio", parsed)
                self.assertIn("RATIO_PARSE_AMBIGUITY", issues)

    def test_ambiguous_percent_colon_and_missing_rights_allocation_remain_blocked(self):
        raw = "Tỷ lệ thực hiện: 100:12. Giá phát hành: 10.000 đồng/cổ phiếu. 100 quyền được mua 12 cổ phiếu mới"
        parsed, issues = terms_v2("RIGHTS_ISSUE", raw)
        self.assertNotIn("rights_ratio", parsed)
        self.assertIn("RATIO_PARSE_AMBIGUITY", issues)
        raw += ". 1 cổ phiếu được hưởng 1 quyền"
        parsed, issues = terms_v2("RIGHTS_ISSUE", raw)
        self.assertEqual("100:12", parsed["rights_ratio"])

    def test_unknown_duplicate_unmarked_or_conflicting_components_fail_closed(self):
        args = list(sample("MBS", "581051", MBS_TITLE))
        for old, new in [("* Phát hành cổ phiếu cho cổ đông hiện hữu:", "* Loại quyền chưa xác minh:"),
                ("* Phát hành cổ phiếu cho cổ đông hiện hữu:", "* Trả cổ phiếu thưởng cho cổ đông hiện hữu:"),
                ("* Phát hành cổ phiếu cho cổ đông hiện hữu:", "Phát hành cổ phiếu cho cổ đông hiện hữu:"),
                ("* Phát hành cổ phiếu cho cổ đông hiện hữu:", "* Phát hành cổ phiếu cho cổ đông hiện hữu: Trả cổ tức bằng tiền mặt;")]:
            with self.subTest(replacement=new):
                altered = args.copy(); self.assertIn(old, altered[0]); altered[0] = altered[0].replace(old, new)
                obs, = parse_popup_components(*altered)
                self.assertEqual("OTHER", values(obs)["event_type"])
                self.assertNotIn("rights_subscription_price", values(obs))

    def test_receipt_title_ticker_and_article_joins_remain_strict(self):
        args = sample("MBS", "581051", MBS_TITLE)
        for index, change in [(0, lambda x: x.replace("đối với cổ phiếu MBS", "đối với cổ phiếu TNG")),
                (1, lambda x: dict(x, request_body="pArticlesID=111&pFileAttach=0")),
                (2, lambda x: dict(x, title="Unrelated title"))]:
            changed = list(copy.deepcopy(args)); changed[index] = change(changed[index])
            with self.subTest(index=index), self.assertRaises((ValueError, SourceLimitation)):
                parse_popup_components(*changed)

    def test_original_revision_title_retained_for_both_components(self):
        args = list(sample("MBS", "581051", MBS_TITLE))
        args[0] = re.sub(r'(<div\s+class="Box-TieuDe[^"\n]*"[^>]*>)', r'\1Đính chính: ', args[0], count=1)
        args[2]["title"] = "Đính chính: " + MBS_TITLE
        observations = parse_popup_components(*args)
        self.assertEqual(2, len(observations))
        for obs in observations:
            self.assertEqual("UNRESOLVED", obs["revision_status"])
            self.assertIn("REVISION_OR_CORRECTION_DETECTED", obs["parser_issues"])

    def test_cash_and_previous_decimal_allocation_fields_unchanged(self):
        for body, ticker, title in [(popup(), "PVS", "Ngày đăng ký cuối cùng trả cổ tức bằng tiền mặt"),
                (popup("ACV", STOCK_TITLE, STOCK), "ACV", STOCK_TITLE)]:
            detail, record, clock = inputs(ticker, title)
            legacy = parse_popup(body, detail, record, clock)
            repaired, = parse_popup_components(body, detail, record, clock)
            self.assertEqual(legacy["fields"], repaired["fields"])
            self.assertEqual(legacy["parser_issues"], repaired["parser_issues"])

    def test_v2_writer_applies_same_integrity_review_gates_and_never_networks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline(root)
            with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network forbidden")):
                old = parse_details(root / "details", root / "old")
                new = parse_details_v2(root / "details", root / "new")
            for result in (old, new):
                for sample in result["samples"]:
                    sample["source_timing"].pop("parser_version")
            self.assertEqual(old, new)
            self.assertEqual(0, new["network_requests"])
            self.assertFalse(new["canonical_build"])
            target = root / "details/raw/0.bin"
            target.write_bytes(target.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "CHECKSUM"):
                parse_details_v2(root / "details", root / "tampered")

    def test_mixed_article_writer_counts_components_and_keeps_required_terms(self):
        html = sample("MBS", "581051", MBS_TITLE)[0]
        bodies = iter([profile("MBS"), listing("581051", MBS_TITLE), html])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = lambda path, **kw: Transport(path, bodies, **kw)
            discover([{"ticker": "MBS", "exchange": "HNX"}], "2019-01-31", "2025-12-31",
                root / "discovery", transport_factory=factory)
            acquire_details(root / "discovery", ["581051"], root / "details", transport_factory=factory)
            result = parse_details_v2(root / "details", root / "parsed")
            self.assertEqual(1, result["input_detail_responses"])
            self.assertEqual(2, result["observation_count"])
            self.assertEqual("PASS_FOR_INPUT_ARTICLES", result["extraction_gate"])
            self.assertEqual(6, result["review_queue_rows"])  # 2 metadata + payment INFO per component.
            self.assertEqual(0, result["accepted_publication_timestamps"])

    def test_missing_component_ratio_does_not_borrow_from_other_component(self):
        args = list(sample("MBS", "581051", MBS_TITLE))
        args[0] = args[0].replace("Tỷ lệ thực hiện: 100:03", "Tỷ lệ đang chờ xác minh")
        bonus, rights = parse_popup_components(*args)
        self.assertNotIn("bonus_ratio", values(bonus))
        self.assertEqual(.12, values(rights)["rights_ratio"])


if __name__ == "__main__": unittest.main()
