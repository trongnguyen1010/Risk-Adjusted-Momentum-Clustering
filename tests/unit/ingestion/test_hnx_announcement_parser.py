import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_parser import parse_notice, parse_probe
from delta_t1.ingestion.corporate_action_sources import SourceLimitation

URL = "https://hnx.vn/vi-vn/m-niem-yet/tin-tuc/synthetic-1-0.html"


def fixture(extra="", time="06/11/2024 15:40", term="Trả cổ tức bằng tiền 7% (01 cổ phiếu được nhận 700 đồng)"):
    return ('<div>Menu cổ tức bằng cổ phiếu 99%</div><div class="news-container">'
            '<div class="news-title">Ngày đăng ký cuối cùng trả cổ tức</div>'
            f'<div class="news-public-time">{time}</div><div class="news-content">'
            'Thông báo đối với cổ phiếu PVS như sau: Ngày đăng ký cuối cùng: 14/11/2024; '
            f'Ngày giao dịch không hưởng quyền: 13/11/2024; {term}; '
            f'Thời gian thực hiện: 17/12/2024; {extra}</div></div>')


def evidence(html):
    return {"url": URL, "path": "raw/source.bin", "source_hash": hashlib.sha256(html.encode()).hexdigest(),
            "fetched_at": "2026-11-01T15:36:24+00:00", "status": 200}


class HnxAnnouncementParserTests(unittest.TestCase):
    def test_cash_fields_and_minute_precision_without_pit_promotion(self):
        html = fixture();ev = evidence(html);before = copy.deepcopy(ev)
        obs = parse_notice(html, ev, "PVS", "HNX")
        values = {k:v["normalized_value"] for k,v in obs["fields"].items()}
        self.assertEqual(700, values["cash_dividend_per_share"])
        self.assertEqual("2024-11-13", values["ex_date"])
        self.assertEqual("2024-11-14", values["record_date"])
        self.assertEqual("2024-12-17", values["payment_date"])
        self.assertEqual("2024-11-06", values["announcement_date"])
        self.assertEqual("CASH_DIVIDEND", values["event_type"])
        self.assertEqual("15:40", obs["source_timing"]["parsed_time"])
        self.assertEqual("MINUTE", obs["source_timing"]["time_precision"])
        self.assertIsNone(obs["source_timing"]["timezone"])
        self.assertIsNone(obs["source_published_at"])
        self.assertEqual(ev["fetched_at"], obs["observed_at"])
        self.assertEqual(before, ev)
        self.assertTrue(obs["source_evidence"])

    def test_ticker_not_silently_assigned_from_input(self):
        html = fixture()
        with self.assertRaisesRegex(SourceLimitation,"TICKER"):
            parse_notice(html, evidence(html), "ACV", "UPCOM")

    def test_ambiguous_article_containers_rejected(self):
        html = fixture() * 2
        with self.assertRaisesRegex(SourceLimitation,"LAYOUT"):
            parse_notice(html, evidence(html), "PVS", "HNX")

    def test_conflicting_dates_are_not_selected(self):
        html = fixture("Ngày giao dịch không hưởng quyền: 12/11/2024")
        obs = parse_notice(html,evidence(html),"PVS","HNX")
        self.assertNotIn("ex_date",obs["fields"])
        self.assertIn("DATE_PARSE_AMBIGUITY:ex_date",obs["parser_issues"])

    def test_invalid_display_time_not_used(self):
        html = fixture(time="32/13/2024 25:60")
        obs = parse_notice(html,evidence(html),"PVS","HNX")
        self.assertIsNone(obs["source_timing"]["parsed_date"])
        self.assertIsNone(obs["source_published_at"])

    def test_stock_ratio_not_confused_with_cash_or_payment_period(self):
        html = fixture(term="Trả cổ tức bằng cổ phiếu; Tỷ lệ thực hiện: 7%")
        obs = parse_notice(html,evidence(html),"PVS","HNX")
        self.assertEqual(.07, obs["fields"]["stock_dividend_ratio"]["normalized_value"])
        self.assertNotIn("payment_date", obs["fields"])
        self.assertNotIn("cash_dividend_per_share", obs["fields"])

    def test_mixed_components_are_kept_for_review_without_term_leakage(self):
        html=fixture(term="Trả cổ tức bằng cổ phiếu và trả cổ tức bằng tiền mặt; Tỷ lệ thực hiện: 7%")
        obs=parse_notice(html,evidence(html),"PVS","HNX")
        self.assertEqual("OTHER",obs["fields"]["event_type"]["normalized_value"])
        self.assertIn("MIXED_OR_UNKNOWN_EVENT_TYPE",obs["parser_issues"])
        self.assertNotIn("stock_dividend_ratio",obs["fields"])

    def test_offline_probe_parse_preserves_raw_and_original_observation_time(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"probe";p.mkdir();(p/"raw").mkdir();html=fixture();ev=evidence(html)
            (p/ev["path"]).write_bytes(html.encode())
            (p/"requests.json").write_text(json.dumps([ev]),encoding="utf-8")
            (p/"result.json").write_text(json.dumps({"public_response_received":True}),encoding="utf-8")
            hashes={f.relative_to(p).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
            (p/"manifest.json").write_text(json.dumps({"artifact_type":"hnx-announcement-access-pilot-v1","files":hashes}),encoding="utf-8")
            before={f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob('*') if f.is_file()}
            out=Path(t)/"parsed";result=parse_probe(p,out,"PVS","HNX")
            self.assertEqual(0,result["network_requests"])
            self.assertEqual(ev["fetched_at"],result["observed_at"])
            self.assertIsNone(result["accepted_publication_timestamp"])
            self.assertEqual(before,{f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob('*') if f.is_file()})
            with self.assertRaises(FileExistsError):parse_probe(p,out,"PVS","HNX")
            (p/ev['path']).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'CHECKSUM'):
                parse_probe(p,Path(t)/"bad","PVS","HNX")


if __name__ == "__main__":
    unittest.main()
