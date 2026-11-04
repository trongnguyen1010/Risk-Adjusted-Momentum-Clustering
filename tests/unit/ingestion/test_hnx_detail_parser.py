import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_detail_parser import parse_popup, parse_details
from delta_t1.ingestion.hnx_announcement_discovery import discover, parse_search_page, DETAIL_URL
from delta_t1.ingestion.hnx_announcement_details import acquire_details
from delta_t1.ingestion.corporate_action_sources import SourceLimitation

CASH_TITLE = "Ngày đăng ký cuối cùng trả cổ tức bằng tiền mặt"
STOCK_TITLE = "Ngày đăng ký cuối cùng trả cổ tức bằng cổ phiếu"
CASH = "Trả cổ tức bằng tiền mặt; Tỷ lệ thực hiện: 7% (01 cổ phiếu được nhận 700 đồng); Thời gian thực hiện: 17/12/2024"
STOCK = "Trả cổ tức bằng cổ phiếu; Tỷ lệ thực hiện: 100:64,58 (Người sở hữu 100 cổ phiếu sẽ được nhận 64,58 cổ phiếu mới)."


def popup(ticker="PVS", title=CASH_TITLE, term=CASH, extra=""):
    return (f'<div class="divContentArticlesDetail"><div class="Box-TieuDe">{title}</div>'
            f'<div class="Box-Noidung">Thông báo đối với cổ phiếu {ticker}: '
            'Ngày đăng ký cuối cùng: 14/11/2024; Ngày giao dịch không hưởng quyền: 13/11/2024; '
            f'{term}; {extra}</div></div>')


def listing(aid="100", title=CASH_TITLE):
    return ('<table><tr><th>Ngày đăng tin</th><th>Tiêu đề tin</th></tr>'
            f'<tr><td>1</td><td>06/11/2024 15:40</td><td><a onclick="return XemChiTietDetailArticlesByID({aid},0)">{title}</a>'
            '</td></tr></table>Tổng số 1 bản ghi')


def inputs(ticker="PVS", title=CASH_TITLE):
    record = parse_search_page(listing(title=title), ticker, "HNX", 1)[0][0]
    detail = {"url": DETAIL_URL, "method": "POST", "request_body": "pArticlesID=100&pFileAttach=0",
              "path": "raw/detail.bin", "source_hash": "detail-hash", "fetched_at": "2026-11-01T16:17:20+00:00"}
    clock = {"url": "https://www.hnx.vn/ModuleIssuer/List/ThongTinCongBo", "path": "raw/list.bin",
             "source_hash": "list-hash", "fetched_at": "2026-11-01T16:08:08+00:00"}
    return detail, record, clock


class Transport:
    def __init__(self, root, responses, **kwargs):
        self.root, self.responses, self.requests = root, iter(responses), []
    def fetch(self, url, payload=None, content_type=None):
        html = next(self.responses); path = "raw/" + str(len(self.requests)) + ".bin"
        (self.root / "raw").mkdir(exist_ok=True); (self.root / path).write_bytes(html.encode())
        receipt = {"url": url, "method": "POST" if payload else "GET", "request_body": payload.decode() if payload else None,
                   "path": path, "source_hash": hashlib.sha256(html.encode()).hexdigest(), "status": 200,
                   "fetched_at": "2026-11-01T16:17:20+00:00"}
        self.requests.append(receipt); return html, receipt


def pipeline(root, bodies=None):
    scopes = [{"ticker": "PVS", "exchange": "HNX"}, {"ticker": "ACV", "exchange": "UPCOM"}]
    responses = []
    for scope, aid, title in zip(scopes, ["100", "200"], [CASH_TITLE, STOCK_TITLE]):
        market = "NY" if scope["exchange"] == "HNX" else "UC"
        responses.extend([f'<input id="StockCode" value="{scope["ticker"]}"><input id="MarketCode" value="{market}">'
                          '<input id="txtTuNgayTinCB"><input id="txtDenNgayTinCB">/ModuleIssuer/List/ThongTinCongBo', listing(aid, title)])
    discover(scopes, "2019-01-31", "2025-12-31", root / "discovery",
             transport_factory=lambda p, **kw: Transport(p, responses, **kw))
    bodies = bodies or [popup(), popup("ACV", STOCK_TITLE, STOCK)]
    acquire_details(root / "discovery", ["100", "200"], root / "details",
                    transport_factory=lambda p, **kw: Transport(p, bodies, **kw))


def reseal(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in manifest["files"]}
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class HnxDetailParserTests(unittest.TestCase):
    def test_cash_two_receipts_clock_and_content_do_not_promote_pit(self):
        detail, record, clock = inputs(); before = copy.deepcopy([detail, record, clock])
        obs = parse_popup(popup(), detail, record, clock)
        self.assertEqual("HNX_ARTICLE:100", obs["event_reference"])
        self.assertEqual(700, obs["fields"]["cash_dividend_per_share"]["normalized_value"])
        self.assertEqual("2024-12-17", obs["fields"]["payment_date"]["normalized_value"])
        self.assertEqual("15:40", obs["source_timing"]["parsed_time"])
        self.assertEqual("MINUTE", obs["source_timing"]["time_precision"])
        self.assertEqual("list-hash", obs["source_timing"]["source_hash"])
        self.assertEqual("detail-hash", obs["source_hash"])
        self.assertEqual(2, len(obs["source_evidence"])); self.assertIsNone(obs["source_published_at"])
        self.assertIsNone(obs["source_timing"]["timezone"])
        self.assertEqual(before, [detail, record, clock])

    def test_decimal_stock_ratio_requires_explicit_old_new_wording(self):
        detail, record, clock = inputs("ACV", STOCK_TITLE)
        obs = parse_popup(popup("ACV", STOCK_TITLE, STOCK), detail, record, clock)
        self.assertAlmostEqual(.6458, obs["fields"]["stock_dividend_ratio"]["normalized_value"])
        self.assertEqual("100:64,58", obs["fields"]["stock_dividend_ratio"]["raw_value"])
        self.assertNotIn("payment_date", obs["fields"])
        ambiguous = parse_popup(popup("ACV", STOCK_TITLE, "Trả cổ tức bằng cổ phiếu; Tỷ lệ thực hiện: 100:64,58"), detail, record, clock)
        self.assertNotIn("stock_dividend_ratio", ambiguous["fields"])
        self.assertIn("RATIO_PARSE_AMBIGUITY", ambiguous["parser_issues"])

    def test_id_title_and_ticker_mismatches_rejected(self):
        detail, record, clock = inputs()
        for html in [popup("ACV"), popup(title="Different title")]:
            with self.assertRaises(SourceLimitation): parse_popup(html, detail, record, clock)
        bad = dict(detail, request_body="pArticlesID=200&pFileAttach=0")
        with self.assertRaisesRegex(ValueError, "ARTICLE_ID"): parse_popup(popup(), bad, record, clock)

    def test_shell_or_duplicate_container_not_interpreted_as_article(self):
        for html in ["<html>Enable Javascript</html>", popup() * 2]:
            with self.assertRaisesRegex(SourceLimitation, "LAYOUT"): parse_popup(html, *inputs())

    def test_mixed_and_conflicting_dates_keep_review_without_guessing(self):
        obs = parse_popup(popup(term=CASH + "; Trả cổ tức bằng cổ phiếu", extra="Ngày giao dịch không hưởng quyền: 12/11/2024"), *inputs())
        self.assertEqual("OTHER", obs["fields"]["event_type"]["normalized_value"])
        self.assertNotIn("cash_dividend_per_share", obs["fields"])
        self.assertNotIn("ex_date", obs["fields"])
        self.assertIn("DATE_PARSE_AMBIGUITY:ex_date", obs["parser_issues"])

    def test_revision_and_later_clock_receipt_are_not_silently_backdated(self):
        title = CASH_TITLE + " đính chính"
        detail, record, clock = inputs(title=title)
        clock["fetched_at"] = "2026-11-02T00:00:00+00:00"
        obs = parse_popup(popup(title=title), detail, record, clock)
        self.assertEqual("UNRESOLVED", obs["revision_status"])
        self.assertEqual(clock["fetched_at"], obs["observed_at"])
        self.assertEqual("2026-11-01T16:17:20+00:00", obs["source_evidence"][0]["fetched_at"])

    def test_end_to_end_archived_pipeline_preserves_inputs_and_local_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); pipeline(root)
            before = {str(p): p.read_bytes() for d in ["discovery", "details"] for p in (root / d).rglob("*") if p.is_file()}
            result = parse_details(root / "details", root / "out")
            self.assertEqual(2, result["observation_count"]); self.assertEqual(0, result["network_requests"])
            self.assertEqual("PASS_FOR_INPUT_ARTICLES", result["extraction_gate"])
            self.assertEqual(0, result["accepted_publication_timestamps"])
            self.assertFalse(result["canonical_build"]); self.assertFalse(result["bulk_collection_ready"])
            manifest = json.loads((root / "out/manifest.json").read_text())
            for name, digest in manifest["files"].items(): self.assertEqual(digest, hashlib.sha256((root / "out" / name).read_bytes()).hexdigest())
            observations = [json.loads(s) for s in (root / "out/observations.jsonl").read_text(encoding="utf-8").splitlines()]
            for obs in observations:
                for ev in obs["source_evidence"]: self.assertEqual(ev["source_hash"], hashlib.sha256((root / "out" / ev["path"]).read_bytes()).hexdigest())
            with (root / "out/review_queue.csv").open(encoding="utf-8", newline="") as f: queue = list(csv.DictReader(f))
            self.assertTrue(any(r["ticker"] == "ACV" and r["field"] == "payment_date" for r in queue))
            self.assertEqual(before, {str(p): p.read_bytes() for d in ["discovery", "details"] for p in (root / d).rglob("*") if p.is_file()})
            with self.assertRaises(FileExistsError): parse_details(root / "details", root / "out")

    def test_tampered_raw_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); pipeline(root); next((root / "details/raw").glob("*")).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "CHECKSUM"): parse_details(root / "details", root / "out")
            self.assertFalse((root / "out").exists())

    def test_resealed_forged_clock_does_not_override_raw_list(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); pipeline(root)
            path = root / "discovery/discovered_articles.jsonl"
            rows = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]
            rows[0]["list_time_raw"] = "01/01/2019 00:00"
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8"); reseal(root / "discovery")
            new_hash = hashlib.sha256((root / "discovery/manifest.json").read_bytes()).hexdigest()
            plan_path = root / "details/plan.json"; plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["origin_manifest_sha256"] = new_hash; plan["selected_articles"][0] = rows[0]
            plan_path.write_text(json.dumps(plan), encoding="utf-8"); reseal(root / "details")
            mpath = root / "details/manifest.json"; m = json.loads(mpath.read_text()); m["origin_manifest_sha256"] = new_hash
            mpath.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, "LIST_RAW_ARTICLE_JOIN"): parse_details(root / "details", root / "out")

    def test_shell_rejection_and_missing_terms_fail_extraction_gate(self):
        for body in ["<html>Enable Javascript</html>", popup(term="Trả cổ tức bằng tiền mặt")]:
            with tempfile.TemporaryDirectory() as t:
                root = Path(t); pipeline(root, [body, popup("ACV", STOCK_TITLE, STOCK)])
                result = parse_details(root / "details", root / "out")
                self.assertEqual("REVIEW_REQUIRED", result["extraction_gate"])
                self.assertFalse(result["bulk_collection_ready"])


if __name__ == "__main__": unittest.main()
