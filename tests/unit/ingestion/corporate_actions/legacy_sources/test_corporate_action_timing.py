import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import unittest
import copy
from delta_t1.ingestion.corporate_action_sources import Document, parse_vsdc, parse_vsdc_time
from delta_t1.ingestion import corporate_action_multisource as multi
from delta_t1.ingestion import corporate_actions_v1 as base


import hashlib

def sample_evidence(html: str, url: str = "https://vsdc.vn/vi/ad/1"):
    return dict(url=url, source_hash=hashlib.sha256(html.encode()).hexdigest(), fetched_at="2024-02-02T12:00:00+07:00")


def sample_html(raw_time_text="Cập nhật ngày 02/01/2024 - 09:00:00", tag_html="", title="Trả cổ tức bằng tiền"):
    info = (
        '<div class="item-info">Mã chứng khoán:</div><div class="item-info item-info-main">TEST</div>'
        '<div class="item-info">Mã ISIN:</div><div class="item-info item-info-main">VNTEST000001</div>'
        '<div class="item-info">Nơi giao dịch:</div><div class="item-info item-info-main">HNX</div>'
        '<div class="item-info">Ngày đăng ký cuối cùng:</div><div class="item-info item-info-main">11/01/2024</div>'
        '<div class="item-info">Lý do mục đích:</div><div class="item-info item-info-main">' + title + '</div>'
    )
    time_div = f'<div class="time-newstcph">{raw_time_text}</div>' if raw_time_text else ''
    return (
        f'<h3 class="title-category">TEST: {title}</h3>'
        f'{time_div}'
        f'{tag_html}'
        f'<div class="content-category">{info}<p>SYNTHETIC; Tỷ lệ thực hiện: 15% (01 cổ phiếu được nhận 1.500 đồng); '
        'Ngày giao dịch không hưởng quyền: 10/01/2024; Ngày thanh toán: 01/02/2024</p></div>'
    )


class TestVSDCTimingRecovery(unittest.TestCase):
    def test_update_and_unknown_tags_do_not_backdate_full_pipeline(self):
        tag = '<time datetime="2024-01-02T09:00:00+07:00"></time>'
        for text, semantic in [("Cập nhật ngày 02/01/2024 - 09:00:00", "UPDATE"), ("", "UNKNOWN")]:
            with self.subTest(semantic=semantic):
                html = sample_html(text, tag_html=tag)
                ev = sample_evidence(html)
                row = parse_vsdc(html, ev)[0]
                obs = multi.observation(row)
                self.assertEqual(semantic, obs["source_timing"]["semantic_label"])
                self.assertEqual(ev["fetched_at"], row["available_at"])
                self.assertEqual("FIRST_OBSERVED_AT_ONLY", row["available_at_evidence"])
                self.assertIsNone(obs["source_published_at"])
                scope = [{"security_id": "SYNTHETIC-SEC", "ticker": "TEST", "exchange": "HNX",
                          "isin": "VNTEST000001", "valid_from": "2010-01-01", "valid_to": "2030-01-01",
                          "identity_status": "VERIFIED", "identity_source_url": "https://vsdc.vn/synthetic-identity"}]
                event = multi.reconcile([obs], scope, "2024-02-03T12:00:00+07:00")[0][0]
                self.assertEqual("PARTIAL", event["pit_timing_verification"])
                self.assertEqual(ev["fetched_at"], event["available_at"])

    def test_explicit_publication_keeps_existing_acceptance(self):
        html = sample_html("Ngày đăng 02/01/2024 - 09:00:00",
                           '<time itemprop="datePublished" datetime="2024-01-02T09:00:00+07:00"></time>')
        row = parse_vsdc(html, sample_evidence(html))[0]
        obs = multi.observation(row)
        self.assertEqual("2024-01-02T09:00:00+07:00", row["available_at"])
        self.assertEqual("2024-01-02T09:00:00+07:00", obs["source_published_at"])

    def test_observation_does_not_accept_supplied_update_as_publication(self):
        html = sample_html()
        row = parse_vsdc(html, sample_evidence(html))[0]
        row["primary_source_published_at"] = "2024-01-02T09:00:00+07:00"
        row["available_at_evidence"] = "EXPLICIT_SOURCE_TIME"
        self.assertIsNone(multi.observation(row)["source_published_at"])

    def test_normalized_observation_enrichment_preserves_every_original_field(self):
        html = sample_html()
        ev = sample_evidence(html)
        ev["path"] = "raw/notice.bin"
        original = multi.observation(parse_vsdc(html, ev)[0])
        original["manual_input"] = True
        original["retained_extension"] = {"receipt": ["immutable"]}
        before = copy.deepcopy(original)
        supplied = copy.deepcopy(original)
        supplied["source_timing"] = parse_vsdc_time("Cập nhật ngày 02/01/2024 - 09:00:00")
        after = multi.observation(supplied)
        expected = dict(original, source_timing=supplied["source_timing"])
        self.assertEqual(expected, after)
        self.assertEqual(before, original)
        self.assertTrue(after["source_evidence"])
        self.assertEqual("2024-01-02", after["source_published_at_raw"])
        after["source_evidence"][0]["path"] = "changed"
        self.assertEqual("raw/notice.bin", supplied["source_evidence"][0]["path"])
        self.assertEqual(original, multi.observation(original))

    def test_normalized_observation_rejects_acquisition_overrides(self):
        html = sample_html()
        obs = multi.observation(parse_vsdc(html, sample_evidence(html))[0])
        with self.assertRaisesRegex(ValueError, "NORMALIZED_OBSERVATION"):
            multi.observation(obs, observed_at="2026-01-01T00:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "NORMALIZED_OBSERVATION"):
            multi.observation(obs, manual=True)

    def test_invalid_text_is_not_hidden_by_valid_tag(self):
        result = parse_vsdc_time("Cập nhật ngày 32/01/2024 - 09:00:00",
                                 ["2024-01-02T09:00:00+07:00"])
        self.assertEqual("INVALID_DATETIME", result["parse_status"])
        self.assertIsNone(result["parsed_datetime"])

    def test_invalid_timezone_cannot_become_available_at(self):
        html = sample_html("Ngày đăng 02/01/2024 - 09:00:00",
                           '<time datetime="2024-01-02T09:00:00+99:99"></time>')
        ev = sample_evidence(html)
        row = parse_vsdc(html, ev)[0]
        self.assertEqual(ev["fetched_at"], row["available_at"])
        self.assertIsNone(multi.observation(row)["source_published_at"])

    def test_full_datetime_hours_minutes_seconds(self):
        res = parse_vsdc_time("Cập nhật ngày 26/04/2025 - 14:53:30")
        self.assertEqual("VALID", res["parse_status"])
        self.assertEqual("DATETIME", res["precision"])
        self.assertEqual("2025-04-26", res["parsed_date"])
        self.assertEqual("14:53:30", res["parsed_time"])
        self.assertEqual("2025-04-26T14:53:30", res["parsed_datetime"])
        self.assertEqual("UPDATE", res["semantic_label"])
        self.assertIsNone(res["timezone"])
        self.assertEqual("NO_TIMEZONE_IN_SOURCE", res["timezone_evidence"])
        self.assertFalse(res["timing_issues"])

    def test_date_only_without_time(self):
        res = parse_vsdc_time("Cập nhật ngày 26/04/2025")
        self.assertEqual("VALID", res["parse_status"])
        self.assertEqual("DATE", res["precision"])
        self.assertEqual("2025-04-26", res["parsed_date"])
        self.assertIsNone(res["parsed_time"])
        self.assertIsNone(res["parsed_datetime"])
        self.assertEqual("UPDATE", res["semantic_label"])
        self.assertIsNone(res["timezone"])
        self.assertEqual("NO_TIMEZONE_IN_SOURCE", res["timezone_evidence"])

    def test_invalid_day_32_asserts_error_status(self):
        res = parse_vsdc_time("Cập nhật ngày 32/01/2024 - 10:00:00")
        self.assertEqual("INVALID_DATETIME", res["parse_status"])
        self.assertEqual("UNKNOWN", res["precision"])
        self.assertIsNone(res["parsed_date"])
        self.assertIsNone(res["parsed_time"])
        self.assertIsNone(res["parsed_datetime"])
        self.assertTrue(any("day is out of range for month" in issue for issue in res["timing_issues"]))

    def test_invalid_leap_year_feb_29_asserts_error_status(self):
        res = parse_vsdc_time("Cập nhật ngày 29/02/2023 - 10:00:00")
        self.assertEqual("INVALID_DATETIME", res["parse_status"])
        self.assertEqual("UNKNOWN", res["precision"])
        self.assertIsNone(res["parsed_date"])
        self.assertIsNone(res["parsed_time"])
        self.assertTrue(any("day is out of range for month" in issue for issue in res["timing_issues"]))

    def test_valid_leap_year_feb_29_passes(self):
        res = parse_vsdc_time("Cập nhật ngày 29/02/2024 - 10:00:00")
        self.assertEqual("VALID", res["parse_status"])
        self.assertEqual("DATETIME", res["precision"])
        self.assertEqual("2024-02-29", res["parsed_date"])
        self.assertEqual("10:00:00", res["parsed_time"])

    def test_invalid_month_13_asserts_error_status(self):
        res = parse_vsdc_time("Cập nhật ngày 15/13/2024 - 10:00:00")
        self.assertEqual("INVALID_DATETIME", res["parse_status"])
        self.assertEqual("UNKNOWN", res["precision"])
        self.assertIsNone(res["parsed_date"])
        self.assertTrue(any("month must be in 1..12" in issue for issue in res["timing_issues"]))

    def test_invalid_hour_25_asserts_error_status(self):
        res = parse_vsdc_time("Cập nhật ngày 15/05/2024 - 25:00:00")
        self.assertEqual("INVALID_DATETIME", res["parse_status"])
        self.assertEqual("UNKNOWN", res["precision"])
        self.assertIsNone(res["parsed_time"])
        self.assertTrue(any("hour must be in 0..23" in issue for issue in res["timing_issues"]))

    def test_invalid_minute_60_asserts_error_status(self):
        res = parse_vsdc_time("Cập nhật ngày 15/05/2024 - 10:60:00")
        self.assertEqual("INVALID_DATETIME", res["parse_status"])
        self.assertEqual("UNKNOWN", res["precision"])
        self.assertIsNone(res["parsed_time"])
        self.assertTrue(any("minute must be in 0..59" in issue for issue in res["timing_issues"]))

    def test_invalid_second_60_asserts_error_status(self):
        res = parse_vsdc_time("Cập nhật ngày 15/05/2024 - 10:00:60")
        self.assertEqual("INVALID_DATETIME", res["parse_status"])
        self.assertEqual("UNKNOWN", res["precision"])
        self.assertIsNone(res["parsed_time"])
        self.assertTrue(any("second must be in 0..59" in issue for issue in res["timing_issues"]))

    def test_time_tag_not_automatically_publication(self):
        # Having <time> tag without publication context does NOT make it PUBLICATION
        res = parse_vsdc_time("", ["2024-01-02T09:00:00+07:00"])
        self.assertEqual("VALID", res["parse_status"])
        self.assertEqual("DATETIME", res["precision"])
        self.assertEqual("UNKNOWN", res["semantic_label"])
        self.assertEqual("+07:00", res["timezone"])
        self.assertEqual("EXPLICIT_ISO_TAG", res["timezone_evidence"])

    def test_time_tag_with_update_text_retains_update_semantics(self):
        # When update text exists alongside <time> tag, semantics is UPDATE
        res = parse_vsdc_time("Cập nhật ngày 02/01/2024 - 09:00:00", ["2024-01-02T09:00:00+07:00"])
        self.assertEqual("VALID", res["parse_status"])
        self.assertEqual("DATETIME", res["precision"])
        self.assertEqual("UPDATE", res["semantic_label"])
        self.assertEqual("+07:00", res["timezone"])

    def test_explicit_publication_semantics(self):
        res1 = parse_vsdc_time("Ngày đăng 02/01/2024 - 09:00:00")
        self.assertEqual("PUBLICATION", res1["semantic_label"])

        res2 = parse_vsdc_time("Công bố thông tin: 02/01/2024 - 09:00:00")
        self.assertEqual("PUBLICATION", res2["semantic_label"])

    def test_multiple_conflicting_time_tags_report_ambiguity(self):
        # When multiple conflicting <time> tags exist, do not pick the first one
        tags = ["2024-01-02T09:00:00+07:00", "2024-01-03T10:00:00+07:00"]
        res = parse_vsdc_time("", tags)
        self.assertEqual("AMBIGUOUS", res["parse_status"])
        self.assertEqual("AMBIGUOUS", res["precision"])
        self.assertIsNone(res["parsed_date"])
        self.assertIsNone(res["parsed_time"])
        self.assertIsNone(res["parsed_datetime"])
        self.assertIn("CONFLICTING_TIME_TAGS", res["timing_issues"])

    def test_direct_observation_conversion_retains_timing_without_manual_assignment(self):
        # Test full conversion: parse_vsdc -> multi.observation -> directly verify obs["source_timing"]
        html = sample_html("Cập nhật ngày 02/01/2024 - 09:00:00")
        ev = sample_evidence(html)
        rows = parse_vsdc(html, ev)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertIn("source_timing", row)
        self.assertEqual("vsdc-html-v3", row["parser"])

        # Pass row directly to observation()
        obs = multi.observation(row)

        # DIRECT inspection on obs without any manual post-assignment!
        self.assertIn("source_timing", obs)
        st = obs["source_timing"]
        self.assertIsNotNone(st)
        self.assertEqual("VALID", st["parse_status"])
        self.assertEqual("DATETIME", st["precision"])
        self.assertEqual("2024-01-02", st["parsed_date"])
        self.assertEqual("09:00:00", st["parsed_time"])
        self.assertEqual("2024-01-02T09:00:00", st["parsed_datetime"])
        self.assertEqual("UPDATE", st["semantic_label"])
        self.assertIsNone(st["timezone"])
        self.assertEqual("NO_TIMEZONE_IN_SOURCE", st["timezone_evidence"])

        # Check PIT policy invariance:
        self.assertIsNone(obs["source_published_at"])
        self.assertEqual(ev["fetched_at"], obs["observed_at"])
        self.assertEqual("FIRST_OBSERVED_AT_ONLY", row["available_at_evidence"])

    def test_conflicting_tags_in_full_pipeline_produces_parser_issues(self):
        conflicting_tags = (
            '<time datetime="2024-01-02T09:00:00+07:00"></time>'
            '<time datetime="2024-01-03T10:00:00+07:00"></time>'
        )
        html = sample_html("", tag_html=conflicting_tags)
        ev = sample_evidence(html)
        rows = parse_vsdc(html, ev)
        obs = multi.observation(rows[0])
        self.assertEqual("AMBIGUOUS", obs["source_timing"]["parse_status"])
        self.assertIn("TIMING_AMBIGUITY", rows[0]["parser_issues"])
        self.assertIsNone(obs["source_timing"]["parsed_date"])


if __name__ == "__main__":
    unittest.main()
