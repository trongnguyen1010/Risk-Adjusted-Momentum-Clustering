import copy
import io
import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs
import zipfile

from delta_t1.ingestion.corporate_actions import hnx_local_supplement as h
from delta_t1.ingestion.corporate_action_sources import PublicTransport, SourceLimitation, sha
from tests.unit.ingestion.test_hnx_announcement_discovery import profile
from tests.unit.ingestion.test_hnx_detail_parser import listing, popup

ROOT = Path(__file__).resolve().parents[4]
CONFIG = h.read(ROOT / h.CONFIG)
PLAN = h.read(ROOT / h.PREP / "plan.json")


class Clock:
    def __init__(self): self.value = 1000.
    def now(self): return self.value
    def sleep(self, value): self.value += value


class Response(io.BytesIO):
    def __init__(self, text, status=200, extra=None):
        super().__init__(text.encode())
        self.code = status
        self.headers = {"Content-Type": "text/html", **(extra or {})}


class Source:
    def __init__(self, clock, failure=None):
        self.clock, self.failure, self.calls = clock, failure, []
        self.ticker = None

    def factory(self, root, **options):
        self_options = dict(options, opener=self, sleep=self.clock.sleep)
        return PublicTransport(root, **self_options)

    def open(self, request, timeout=None):
        self.calls.append((self.clock.now(), request.full_url, request.data))
        if len(self.calls) == 2 and self.failure:
            if isinstance(self.failure, Exception): raise self.failure
            if self.failure == "challenge": return Response("verify you are human")
            if self.failure == "retry-after": return Response("ok", extra={"Retry-After": "60"})
            if self.failure == "layout": return Response("<html>unrecognized list</html>")
            return Response("error", self.failure)
        if request.data is None:
            self.ticker = request.full_url.rsplit("-", 1)[-1].removesuffix(".html")
            target = next(t for t in PLAN["targets"] if t["ticker"] == self.ticker)
            return Response(profile(self.ticker, "NY" if target["exchange"] == "HNX" else "UC"))
        form = parse_qs(request.data.decode())
        if "pStockCode" in form:
            target = next(t for t in PLAN["targets"] if t["ticker"] == self.ticker)
            from datetime import date
            clock = date.fromisoformat(target["search_hint_date"]).strftime("%d/%m/%Y") + " 15:40"
            body = listing(str(1000 + h.TICKERS.index(self.ticker))).replace("06/11/2024 15:40", clock)
            return Response(body)
        return Response(popup(self.ticker))


def tls(*args, **kwargs): return ssl.create_default_context(), {"status": "VALIDATED"}
def quiet(*args, **kwargs): pass


class SupplementTests(unittest.TestCase):
    def run_fake(self, output, source, clock, **kwargs):
        with patch.object(h, "load_preparation", return_value=(copy.deepcopy(CONFIG), copy.deepcopy(PLAN))), \
                patch("time.monotonic", clock.now):
            return h.run(ROOT, output, transport_factory=source.factory, prepare_tls=tls,
                clock=clock.now, emit=kwargs.pop("emit", quiet), **kwargs)

    def test_scope_and_budgets_cannot_expand(self):
        h.validate(CONFIG, PLAN)
        for key, value in [("workers", 2), ("interval_seconds", 7), ("max_requests_job", 51),
                ("max_pages_per_ticker", 3), ("retry", True), ("canonical_build", True)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                h.validate(dict(CONFIG, **{key: value}), PLAN)
        changed = copy.deepcopy(PLAN); changed["targets"][0]["ticker"] = "PVS"
        with self.assertRaises(ValueError): h.validate(CONFIG, changed)
        changed = copy.deepcopy(PLAN); changed["targets"][0]["hnx_cached_successful_details"] = 1
        with self.assertRaises(ValueError): h.validate(CONFIG, changed)

    def test_dry_run_has_no_tls_network_or_output(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(h, "load_preparation", return_value=(CONFIG, PLAN)):
            out = Path(temp) / "state"
            result = h.run(ROOT, out, dry_run=True, prepare_tls=lambda *a, **k: self.fail("TLS called"))
            self.assertEqual(0, result["network_requests"])
            self.assertFalse(out.exists())

    def test_ten_ticker_chain_global_delay_receipts_and_zip(self):
        clock = Clock(); source = Source(clock)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "state"
            result = self.run_fake(out, source, clock)
            self.assertEqual("FINISHED_BOUNDED_REVIEW_REQUIRED", result["status"])
            self.assertEqual((10, 10, 10, 30), (result["tickers_finished"],
                result["successful_detail_articles"], result["preview_observations"], result["requests_total"]))
            self.assertTrue(all(b[0] - a[0] >= 8 for a, b in zip(source.calls, source.calls[1:])))
            self.assertEqual(30, len(h.rows(out / "request_log.jsonl")))
            starts = [r["start_monotonic"] for r in h.rows(out / "request_timing.jsonl")]
            self.assertTrue(all(b - a >= 8 for a, b in zip(starts, starts[1:])))
            self.assertEqual(0, result["canonical_fields_applied"])
            self.assertFalse(result["pit_or_identity_promoted"])
            self.assertFalse(result["resumable"])
            self.assertGreaterEqual(len(list((out / "checkpoints").glob("*.json"))), 60)
            for parsed in out.glob("work/*/parsed-*/observations.jsonl"):
                obs = h.rows(parsed)[0]
                self.assertIn("SOURCE_PUBLIC_TIME_UNVERIFIED", obs["parser_issues"])
                self.assertIn("HISTORICAL_IDENTITY_NOT_CERTIFIED", obs["parser_issues"])
            archive = Path(temp) / "result.zip"
            h.seal(out, archive, artifact_type=h.TYPE)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                for name, digest in json.loads(z.read("manifest.json"))["files"].items():
                    self.assertEqual(digest, sha(z.read(name)))

    def test_all_access_boundaries_stop_whole_job_and_export_partial(self):
        for failure in [401, 403, 429, "challenge", "retry-after", URLError(ssl.SSLError("TLS failed")),
                URLError(ConnectionResetError("reset")), TimeoutError("request timeout")]:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                clock = Clock(); source = Source(clock, failure)
                out = Path(temp) / "state"
                result = self.run_fake(out, source, clock)
                self.assertEqual("SOURCE_OR_INTEGRITY_STOP", result["status"])
                self.assertEqual(2, len(source.calls))
                self.assertFalse(result["resumable"])
                self.assertTrue(h.read(out / "checkpoint.json")["source_stopped"])
                h.seal(out, Path(temp) / "partial.zip", artifact_type=h.TYPE)

    def test_two_pages_two_details_cap_fifty_requests_including_final_offline_parse(self):
        clock = Clock(); source = Source(clock)
        original = source.open
        def forty(request, timeout=None):
            response = original(request, timeout)
            form = parse_qs(request.data.decode()) if request.data else {}
            if "pStockCode" not in form:
                return response
            page = int(form["pNumPage"][0])
            one = response.getvalue().decode()
            header, row = one.split("<tr><td>", 1)
            row = "<tr><td>" + row.split("</tr>", 1)[0] + "</tr>"
            aid = str(1000 + h.TICKERS.index(source.ticker))
            fragments = [row.replace("(" + aid + ",0)", "(" + str(int(aid) * 100 + page * 20 + n) + ",0)")
                for n in range(20)]
            return Response(header + "".join(fragments) + "</table>Tổng số 40 bản ghi")
        source.open = forty
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_fake(Path(temp) / "state", source, clock)
            self.assertEqual("FINISHED_BOUNDED_REVIEW_REQUIRED", result["status"])
            self.assertEqual(50, result["requests_total"])
            self.assertEqual(400, result["discovered_articles"])
            self.assertEqual(20, result["successful_detail_articles"])
            self.assertEqual(20, result["preview_observations"])

    def test_cached_article_id_is_never_selected_for_redownload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "discovered_articles.jsonl").write_text(json.dumps({
                "provider_article_id": "7", "price_action_title_candidate": True,
                "publication_date_candidate": "2024-11-25", "title": "quyền mua"}) + "\n", encoding="utf-8")
            target = dict(PLAN["targets"][0], cached_successful_article_ids=["7"])
            self.assertEqual([], h.candidates(root, target))

    def test_layout_error_quarantines_one_ticker_then_continues(self):
        clock = Clock(); source = Source(clock, "layout")
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "state"; result = self.run_fake(out, source, clock)
            self.assertEqual("FINISHED_BOUNDED_REVIEW_REQUIRED", result["status"])
            self.assertEqual(9, result["preview_observations"])
            state = h.read(out / "checkpoint.json")
            self.assertEqual("QUARANTINE", state["targets"]["VE3"]["action"])

    def test_parser_rejection_preserves_raw_and_moves_on(self):
        clock = Clock(); source = Source(clock)
        original = source.open
        def broken(request, timeout=None):
            response = original(request, timeout)
            if source.ticker == "VE3" and request.data and b"pArticlesID" in request.data:
                return Response("<html>bad popup</html>")
            return response
        source.open = broken
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "state"; result = self.run_fake(out, source, clock)
            self.assertEqual(10, result["successful_detail_articles"])
            self.assertEqual(9, result["preview_observations"])
            parsed = h.read(next(out.glob("work/VE3/parsed-*/result.json")))
            self.assertEqual("REVIEW_REQUIRED", parsed["extraction_gate"])
            self.assertTrue(list(out.glob("work/VE3/detail-*/raw/*.bin")))

    def test_tls_setup_failure_has_zero_source_requests(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(h, "load_preparation", return_value=(CONFIG, PLAN)):
            def fail(*a, **k): raise ValueError("TLS chain failed")
            result = h.run(ROOT, Path(temp) / "state", prepare_tls=fail, emit=quiet)
            self.assertEqual(0, result["requests_this_run"])
            self.assertFalse(result["resumable"])

    def test_source_stop_or_legacy_state_cannot_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(h, "load_preparation", return_value=(CONFIG, PLAN)), self.assertRaisesRegex(ValueError, "ONLY_NEW"):
                h.run(ROOT, Path(temp) / "new", resume=ROOT / "tmp/hnx_batch_first_two_20261101_v1")
        # A valid new-family artifact with a source stop remains nonresumable.
        base = ROOT / h.BASE
        with tempfile.TemporaryDirectory(dir=base.parent) as temp:
            clock = Clock(); source = Source(clock, 403); out = Path(temp) / "state"
            self.run_fake(out, source, clock); h.seal(out, Path(temp) / "partial.zip", artifact_type=h.TYPE)
            with patch.object(h, "BASE", str(Path(temp).relative_to(ROOT))), \
                    patch.object(h, "load_preparation", return_value=(CONFIG, PLAN)), self.assertRaisesRegex(ValueError, "NOT_ELIGIBLE"):
                h.run(ROOT, Path(temp) / "next", resume=out)

    def test_budget_boundary_resume_skips_completed_units_and_preserves_parent(self):
        # Put the temporary job inside the permitted new-family namespace.
        with tempfile.TemporaryDirectory(dir=ROOT / "data/corporate_actions/work") as temp:
            with patch.object(h, "BASE", str(Path(temp).relative_to(ROOT))):
                clock = Clock(); source = Source(clock)
                def emit(message, **options):
                    if json.loads(message)["ticker"] == "TNG": clock.value += 1201
                out = Path(temp) / "first"
                result = self.run_fake(out, source, clock, emit=emit)
                self.assertEqual("BUDGET_STOP", result["status"])
                self.assertTrue(result["resumable"])
                self.assertEqual(3, result["requests_total"])
                h.seal(out, Path(temp) / "first.zip", artifact_type=h.TYPE)
                before = h.hashes(out)
                clock2 = Clock(); source2 = Source(clock2)
                second = Path(temp) / "second"
                result2 = self.run_fake(second, source2, clock2, resume=out)
                self.assertEqual("FINISHED_BOUNDED_REVIEW_REQUIRED", result2["status"])
                self.assertEqual(30, result2["requests_total"])
                self.assertEqual(27, result2["requests_this_run"])
                self.assertEqual(before, h.hashes(second / "parent"))
                self.assertEqual(before, h.hashes(out))

    def test_global_request_and_time_budget_before_any_new_request(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "request_log.jsonl").touch()
            clock = Clock(); source = Source(clock)
            with patch("time.monotonic", clock.now):
                budget = h.RunBudget(root, 1, 10, source.factory, clock.now)
                client = budget.transport(root, max_requests=3, interval=8, timeout=15)
                source.ticker = "VE3"
                client.fetch("https://www.hnx.vn/vi-vn/cophieu-etfs/chi-tiet-chung-khoan-ny-VE3.html")
                with self.assertRaisesRegex(SourceLimitation, "REQUEST_BUDGET"):
                    client.fetch("https://www.hnx.vn/test")
                self.assertEqual(1, len(source.calls))

    def test_unknown_receipt_errors_never_quarantine(self):
        self.assertEqual("SOURCE_STOP", h.classify("TLS failed", {"error": "bad cert"}))
        self.assertEqual("SOURCE_STOP", h.classify("HNX_DESKTOP_SCOPE_CONTEXT_MISMATCH",
            {"status": 200, "error": "SOURCE_ACCESS_LIMITATION"}))


if __name__ == "__main__": unittest.main()
