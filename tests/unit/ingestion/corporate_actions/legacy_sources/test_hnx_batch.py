import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import ssl
from urllib.error import URLError
from unittest.mock import patch
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_batch import run_batch, verify_artifact
from delta_t1.ingestion.hnx_announcement_discovery import discover, discover_for_batch
from delta_t1.ingestion.corporate_action_sources import PublicTransport, sha

CASH_TITLE = "Ngày đăng ký cuối cùng trả cổ tức bằng tiền mặt"
STOCK_TITLE = "Ngày đăng ký cuối cùng trả cổ tức bằng cổ phiếu"


class Clock:
    def __init__(self): self.value, self.delays = 1000.0, []
    def now(self): return self.value
    def sleep(self, seconds): self.delays.append(seconds); self.value += seconds


class Response(io.BytesIO):
    def __init__(self, body, status=200):
        super().__init__(body.encode()); self.code = status; self.headers = {"Content-Type": "text/html; charset=utf-8"}


class Source:
    def __init__(self, clock, *, blocked=False, shell=False, missing_terms=False, pages=1):
        self.clock, self.calls, self.blocked, self.shell, self.missing_terms, self.pages = clock, [], blocked, shell, missing_terms, pages
    def factory(self, root, **options):
        return PublicTransport(root, opener=self, sleep=self.clock.sleep, **options)
    def listing(self, ticker, page):
        title = STOCK_TITLE if ticker == "ACV" else CASH_TITLE
        total = self.pages if self.pages > 1 else 2
        numbers = [page - 1] if self.pages > 1 else [0, 1]
        prefix = 200 if ticker == "ACV" else 100
        rows = ''.join(f'<tr><td>{n+1}</td><td>06/11/2024 15:40</td><td><a onclick="return XemChiTietDetailArticlesByID({prefix+n},0)">{title}</a></td></tr>' for n in numbers)
        return '<table><tr><th>Ngày đăng tin</th><th>Tiêu đề tin</th></tr>' + rows + f'</table>Tổng số {total} bản ghi'
    def body(self, aid):
        ticker = "ACV" if aid.startswith("2") else "PVS"
        title = STOCK_TITLE if ticker == "ACV" else CASH_TITLE
        term = ("Trả cổ tức bằng cổ phiếu; Tỷ lệ thực hiện: 100:64,58 (Người sở hữu 100 cổ phiếu sẽ được nhận 64,58 cổ phiếu mới)."
                if ticker == "ACV" else "Trả cổ tức bằng tiền mặt; 01 cổ phiếu được nhận 700 đồng; Thời gian thực hiện: 17/12/2024")
        if self.missing_terms: term = "Trả cổ tức bằng cổ phiếu" if ticker == "ACV" else "Trả cổ tức bằng tiền mặt"
        return (f'<div class="divContentArticlesDetail"><div class="Box-TieuDe">{title}</div><div class="Box-Noidung">'
                f'Thông báo đối với cổ phiếu {ticker}: Ngày đăng ký cuối cùng: 14/11/2024; '
                f'Ngày giao dịch không hưởng quyền: 13/11/2024; {term}</div></div>')
    def open(self, request, timeout=None):
        form = parse_qs(request.data.decode(), keep_blank_values=True) if request.data else {}
        self.calls.append({"url": request.full_url, "form": form, "at": self.clock.now()})
        if self.blocked: return Response("Access denied", 403)
        if not request.data:
            ticker = "ACV" if "-ACV.html" in request.full_url else "PVS"
            market = "UC" if ticker == "ACV" else "NY"
            return Response(f'<input id="StockCode" value="{ticker}"><input id="MarketCode" value="{market}">'
                            '<input id="txtTuNgayTinCB"><input id="txtDenNgayTinCB">/ModuleIssuer/List/ThongTinCongBo')
        if "pStockCode" in form: return Response(self.listing(form["pStockCode"][0], int(form["pNumPage"][0])))
        return Response("<html>Enable JavaScript</html>" if self.shell else self.body(form["pArticlesID"][0]))


def universe(root):
    path = root / "securities.jsonl"
    path.write_text('\n'.join(json.dumps({"ticker": t, "exchange": e}) for t, e in
                              [("PVS", "HNX"), ("ACV", "UPCOM"), ("AAA", "HOSE")]), encoding="utf-8")
    return path


def run(root, source, name="run", **kwargs):
    with patch("delta_t1.ingestion.corporate_action_sources.time.monotonic", source.clock.now):
        return run_batch(root / "securities.jsonl", root / name, transport_factory=source.factory,
                         clock=source.clock.now, **kwargs)


class HnxBatchTests(unittest.TestCase):
    def test_empty_query_keeps_scope_review_and_next_ticker_is_processed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock())
            original=source.listing
            empty=(ROOT/'tests/fixtures/hnx_disclosure_empty_aav_20261101.html').read_text(encoding='utf-8')
            source.listing=lambda ticker,page:empty if ticker=='ACV' else original(ticker,page)
            result=run(root,source)
            self.assertEqual(['ACV'],result['empty_query_tickers']);self.assertEqual(2,result['handled_tickers'])
            self.assertEqual(2,result['observation_count']);self.assertEqual(6,result['network_requests_this_run'])
            self.assertIsNone(result['stop_reason']);self.assertEqual('INCOMPLETE_NOT_CERTIFIED',result['source_history_coverage'])
            self.assertEqual(0,result['accepted_publication_timestamps']);self.assertFalse(result['canonical_build'])
            with (root/'run/review_queue.csv').open(encoding='utf-8',newline='') as f:reviews=list(csv.DictReader(f))
            scope_rows=[r for r in reviews if r['reason']=='EMPTY_QUERY_NOT_HISTORICAL_COVERAGE']
            self.assertEqual(1,len(scope_rows));self.assertEqual('ACV',scope_rows[0]['ticker'])
            self.assertEqual('',scope_rows[0]['provider_article_id'])
            resumed=run(root,source,'resumed-empty',resume_from=root/'run')
            self.assertEqual(0,resumed['network_requests_this_run']);self.assertEqual(5,resumed['review_queue_rows'])

    def test_full_composition_and_review_remain_open_with_shared_host_interval(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock())
            result = run(root, source)
            self.assertEqual("COLLECTED_WITH_REVIEWS", result["status"])
            self.assertEqual(2, result["scope_tickers"]); self.assertEqual(2, result["handled_tickers"])
            self.assertEqual(8, result["network_requests_this_run"]); self.assertEqual(4, result["observation_count"])
            self.assertEqual(0, result["accepted_publication_timestamps"]); self.assertFalse(result["canonical_build"])
            self.assertEqual("INCOMPLETE_NOT_CERTIFIED", result["source_history_coverage"])
            self.assertTrue(all(b["at"] - a["at"] >= 2 for a, b in zip(source.calls, source.calls[1:])))
            verify_artifact(root / "run", {"hnx-supplemental-batch-v1"})
            observations = [json.loads(s) for s in (root / "run/observations.jsonl").read_text(encoding="utf-8").splitlines()]
            for obs in observations:
                self.assertIsNone(obs["source_published_at"])
                for ev in obs["source_evidence"]: self.assertEqual(ev["source_hash"], sha((root / "run" / ev["path"]).read_bytes()))
            with (root / "run/review_queue.csv").open(encoding="utf-8", newline="") as f: reviews = list(csv.DictReader(f))
            self.assertEqual(4, sum(r["reason"] == "SOURCE_PUBLIC_TIME_UNVERIFIED" for r in reviews))
            self.assertEqual(4, sum(r["reason"] == "HISTORICAL_IDENTITY_NOT_CERTIFIED" for r in reviews))

    def test_budget_partial_detail_is_preserved_and_resume_skips_completed_requests(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock())
            first = run(root, source, max_requests=3)
            self.assertEqual("RUN_REQUEST_BUDGET_EXHAUSTED", first["stop_reason"])
            self.assertEqual(1, first["observation_count"]); self.assertTrue(first["resumable"])
            before = {str(p): p.read_bytes() for p in (root / "run").rglob("*") if p.is_file()}
            second = run(root, source, "continued", resume_from=root / "run")
            self.assertEqual(5, second["network_requests_this_run"])
            self.assertEqual(4, second["observation_count"])
            self.assertEqual(1, sum(c["form"].get("pArticlesID") == ["200"] for c in source.calls))
            self.assertEqual(before, {str(p): p.read_bytes() for p in (root / "run").rglob("*") if p.is_file()})

    def test_time_budget_during_delay_starts_no_late_http_request(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock())
            result = run(root, source, max_seconds=1)
            self.assertEqual("RUN_TIME_BUDGET_EXHAUSTED", result["stop_reason"])
            self.assertEqual(1, len(source.calls)); self.assertTrue(result["resumable"])

    def test_access_failure_stops_all_symbols_and_cannot_be_automatically_resumed(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock(), blocked=True)
            result = run(root, source)
            self.assertEqual(1, len(source.calls)); self.assertFalse(result["resumable"])
            self.assertEqual("STOPPED_REVIEW_REQUIRED", result["status"])
            with self.assertRaisesRegex(ValueError, "REQUIRES_REVIEW"):
                run(root, source, "bad-resume", resume_from=root / "run")
            self.assertEqual(1, len(source.calls))

    def test_layout_rejection_quarantines_tickers_and_missing_terms_stay_in_field_review(self):
        for shell in [True, False]:
            with tempfile.TemporaryDirectory() as t:
                root = Path(t); universe(root); source = Source(Clock(), shell=shell, missing_terms=not shell)
                result = run(root, source)
                if shell:
                    self.assertIsNone(result["stop_reason"])
                    self.assertEqual(["ACV","PVS"],result["quarantined_tickers"])
                    self.assertEqual(0,result["observation_count"])
                    self.assertEqual(0,result["handled_tickers"])
                    self.assertEqual([],result["pending_tickers"])
                    self.assertEqual("COLLECTED_WITH_QUARANTINED_TICKERS",result["status"])
                else:
                    self.assertEqual(4, result["observation_count"]); self.assertIsNone(result["stop_reason"])
                    self.assertIn("MISSING_REQUIRED_FIELD", (root / "run/review_queue.csv").read_text())

    def test_discovery_failure_is_reviewed_then_next_ticker_runs_and_resume_skips_bad_ticker(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.listing
            source.listing=lambda ticker,page:'<html>Changed issuer layout</html>' if ticker=='ACV' else normal(ticker,page)
            result=run(root,source)
            self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(1,result['handled_tickers'])
            self.assertEqual(2,result['observation_count']);self.assertEqual([],result['pending_tickers'])
            self.assertEqual(6,len(source.calls));self.assertEqual('INCOMPLETE_NOT_CERTIFIED',result['source_history_coverage'])
            with (root/'run/collection_issues.csv').open(encoding='utf-8',newline='') as f:issues=list(csv.DictReader(f))
            self.assertEqual(1,len(issues));self.assertEqual('ACV',issues[0]['ticker']);self.assertEqual('DISCOVERY',issues[0]['stage'])
            self.assertEqual('PENDING',issues[0]['review_status']);self.assertEqual('SKIP_TICKER_KEEP_EVIDENCE',issues[0]['action'])
            self.assertTrue(Path(issues[0]['artifact_path']).is_dir())
            verify_artifact(root/'run')
            resumed=run(root,source,'continued',resume_from=root/'run')
            self.assertEqual(0,resumed['network_requests_this_run']);self.assertEqual(['ACV'],resumed['quarantined_tickers'])
            self.assertEqual(1,resumed['collection_issue_rows']);self.assertEqual(6,len(source.calls))

    def test_partial_article_parse_keeps_good_observations_and_moves_to_next_ticker(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.body
            source.body=lambda aid:'<html>Unrecognized article body</html>' if aid=='200' else normal(aid)
            result=run(root,source)
            self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(3,result['observation_count'])
            self.assertEqual(1,result['handled_tickers']);self.assertEqual(8,len(source.calls))
            self.assertIn('PARSER_REJECTED_ARTICLE_REQUIRES_REVIEW',(root/'run/collection_issues.csv').read_text())
            observations=[json.loads(s) for s in (root/'run/observations.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual({'ACV','PVS'},{o['fields']['ticker']['normalized_value'] for o in observations})
            self.assertTrue(all(o['source_published_at'] is None for o in observations))

    def test_profile_scope_mismatch_does_not_assign_wrong_ticker_or_stop_other_tickers(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.open
            def failing(request,timeout=None):
                response=normal(request,timeout)
                if not request.data and '-ACV.html' in request.full_url:
                    return Response('<input id="StockCode" value="PVS"><input id="MarketCode" value="UC">')
                return response
            source.open=failing;result=run(root,source)
            self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(2,result['observation_count'])
            self.assertEqual(5,len(source.calls))
            observations=[json.loads(s) for s in (root/'run/observations.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual({'PVS'},{o['fields']['ticker']['normalized_value'] for o in observations})

    def test_runtime_integrity_error_remains_global_instead_of_skipping_silently(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal_factory=source.factory
            def corrupting_factory(path,**options):
                client=normal_factory(path,**options);fetch=client.fetch
                def corrupting_fetch(url,payload=None,**kwargs):
                    result=fetch(url,payload,**kwargs)
                    if payload and parse_qs(payload.decode()).get('pStockCode')==['ACV']:
                        (path/result[1]['path']).write_bytes(b'tampered body')
                    return result
                client.fetch=corrupting_fetch;return client
            source.factory=corrupting_factory;result=run(root,source)
            self.assertFalse(result['resumable']);self.assertEqual('STOPPED_REVIEW_REQUIRED',result['status'])
            self.assertEqual([],result['quarantined_tickers']);self.assertEqual(2,len(source.calls))
            self.assertIn('MISMATCH',result['stop_reason'])

    def test_new_access_guard_failure_cannot_reuse_previous_reviewable_http_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal_open=source.open;normal_factory=source.factory
            def first_missing(request,timeout=None):
                response=normal_open(request,timeout)
                if request.data and parse_qs(request.data.decode()).get('pStockCode')==['ACV']:
                    return Response('Issuer not found',404)
                return response
            source.open=first_missing
            def guarded(path,**options):
                client=normal_factory(path,**options);fetch=client.fetch
                def checked(url,*args,**kwargs):
                    if '-PVS.html' in url:
                        from delta_t1.ingestion.corporate_action_sources import SourceLimitation
                        raise SourceLimitation('SOURCE_ACCESS_LIMITATION: URL outside approved public adapters')
                    return fetch(url,*args,**kwargs)
                client.fetch=checked;return client
            source.factory=guarded;result=run(root,source)
            self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(['PVS'],result['pending_tickers'])
            self.assertFalse(result['resumable']);self.assertEqual('STOPPED_REVIEW_REQUIRED',result['status'])

    def test_plain_url_and_server_errors_are_quarantined_without_automatic_retry(self):
        for status in [404,410,500,502,503,504]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as t:
                root=Path(t);universe(root);source=Source(Clock());normal=source.open
                def failing(request,timeout=None):
                    response=normal(request,timeout)
                    if request.data and parse_qs(request.data.decode()).get('pStockCode')==['ACV']:
                        return Response('Issuer endpoint error',status)
                    return response
                source.open=failing
                result=run(root,source)
                self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(2,result['observation_count'])
                self.assertEqual(6,len(source.calls));self.assertTrue(result['resumable'])
                resumed=run(root,source,'continued',resume_from=root/'run')
                self.assertEqual(0,resumed['network_requests_this_run']);self.assertEqual(6,len(source.calls))

    def test_detail_404_preserves_failed_response_and_next_ticker_is_collected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.open
            def failing(request,timeout=None):
                response=normal(request,timeout)
                if request.data and parse_qs(request.data.decode()).get('pArticlesID')==['200']:
                    return Response('Article not found',404)
                return response
            source.open=failing;result=run(root,source)
            self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(2,result['observation_count'])
            self.assertEqual(7,len(source.calls))
            with (root/'run/collection_issues.csv').open(encoding='utf-8',newline='') as f:issues=list(csv.DictReader(f))
            self.assertEqual('DETAIL',issues[0]['stage'])
            receipts=json.loads((Path(issues[0]['artifact_path'])/'requests.json').read_text())
            self.assertEqual(404,receipts[0]['status'])
            self.assertTrue((Path(issues[0]['artifact_path'])/receipts[0]['path']).is_file())

    def test_typed_request_timeout_is_reviewable_and_no_retry_on_resume(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.open
            def failing(request,timeout=None):
                response=normal(request,timeout)
                if request.data and parse_qs(request.data.decode()).get('pStockCode')==['ACV']:
                    raise URLError(TimeoutError('response timed out'))
                return response
            source.open=failing;result=run(root,source)
            self.assertEqual(['ACV'],result['quarantined_tickers']);self.assertEqual(2,result['observation_count'])
            resumed=run(root,source,'continued',resume_from=root/'run')
            self.assertEqual(0,resumed['network_requests_this_run']);self.assertEqual(6,len(source.calls))

    def test_ssl_failure_remains_global_and_cannot_be_resumed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.open
            def failing(request,timeout=None):
                normal(request,timeout);raise URLError(ssl.SSLCertVerificationError('certificate verify failed'))
            source.open=failing;result=run(root,source)
            self.assertEqual(1,len(source.calls));self.assertFalse(result['resumable']);self.assertEqual([],result['quarantined_tickers'])
            self.assertEqual('STOPPED_REVIEW_REQUIRED',result['status'])

    def test_retry_after_and_challenges_stop_all_requests(self):
        for status,body,header in [(401,'Unauthorized',None),(429,'Too many requests',None),
                                   (503,'Server busy','60'),(200,'Normal page','60'),(200,'captcha challenge',None)]:
            with self.subTest(status=status,body=body),tempfile.TemporaryDirectory() as t:
                root=Path(t);universe(root);source=Source(Clock());normal=source.open
                def failing(request,timeout=None):
                    normal(request,timeout);response=Response(body,status)
                    if header:response.headers['Retry-After']=header
                    return response
                source.open=failing;result=run(root,source)
                self.assertEqual(1,len(source.calls));self.assertFalse(result['resumable'])
                self.assertEqual([],result['quarantined_tickers']);self.assertEqual('STOPPED_REVIEW_REQUIRED',result['status'])

    def test_access_denied_body_timeout_keeps_http_status_and_stops_globally(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.open
            class DeniedTimeout(Response):
                def read(self,*args):raise TimeoutError('denial body timed out')
            def failing(request,timeout=None):normal(request,timeout);return DeniedTimeout('Denied',403)
            source.open=failing;result=run(root,source)
            self.assertEqual(1,len(source.calls));self.assertFalse(result['resumable']);self.assertEqual([],result['quarantined_tickers'])
            logs=[json.loads(s) for s in (root/'run/request_log.jsonl').read_text().splitlines()]
            self.assertEqual(403,logs[0]['receipt']['status'])

    def test_budget_after_quarantine_resumes_only_remaining_ticker(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);universe(root);source=Source(Clock());normal=source.listing
            source.listing=lambda ticker,page:'<html>Changed layout</html>' if ticker=='ACV' else normal(ticker,page)
            first=run(root,source,max_requests=2)
            self.assertEqual(['ACV'],first['quarantined_tickers']);self.assertEqual(['PVS'],first['pending_tickers'])
            self.assertEqual('RUN_REQUEST_BUDGET_EXHAUSTED',first['stop_reason'])
            second=run(root,source,'continued',resume_from=root/'run')
            self.assertEqual(4,second['network_requests_this_run']);self.assertEqual(2,second['observation_count'])
            self.assertEqual(['ACV'],second['quarantined_tickers']);self.assertEqual([],second['pending_tickers'])

    def test_batch_pagination_does_not_relax_pilot_caps_or_claim_complete_history(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock(), pages=4)
            result = run(root, source, tickers=["PVS"], max_pages=4)
            self.assertEqual(4, result["observation_count"]); self.assertEqual([], result["discovery_page_limit_tickers"])
            self.assertEqual(9, result["network_requests_this_run"])
            with self.assertRaises(ValueError):
                discover([{"ticker":"PVS","exchange":"HNX"}], "2019-01-31", "2025-12-31", root / "pilot", max_pages=4, dry_run=True)
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock(), pages=4)
            result = run(root, source, tickers=["PVS"], max_pages=2)
            self.assertEqual(["PVS"], result["discovery_page_limit_tickers"])
            self.assertEqual("INCOMPLETE_NOT_CERTIFIED", result["source_history_coverage"])

    def test_seed_reuses_discovery_without_network_and_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); canonical = universe(root); source = Source(Clock())
            with patch("delta_t1.ingestion.corporate_action_sources.time.monotonic", source.clock.now):
                discover_for_batch({"ticker":"PVS","exchange":"HNX"}, "2019-01-31", "2025-12-31", root / "seed",
                                   transport_factory=source.factory, scope_evidence={"sha256":sha(canonical.read_bytes())})
            source.calls.clear()
            dry = run(root, source, "dry", tickers=["PVS"], seed_discovery=root / "seed", dry_run=True)
            self.assertEqual(1, dry["cached_discovery_tickers"]); self.assertFalse((root / "dry").exists()); self.assertEqual([], source.calls)
            result = run(root, source, tickers=["PVS"], seed_discovery=root / "seed")
            self.assertEqual(2, result["network_requests_this_run"])
            self.assertTrue(all("pArticlesID" in c["form"] for c in source.calls))

    def test_resume_tamper_or_contract_scope_change_rejected_before_network(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock()); run(root, source)
            count = len(source.calls)
            with self.assertRaisesRegex(ValueError, "CONTRACT_CHANGED"):
                run(root, source, "bad-scope", tickers=["PVS"], resume_from=root / "run")
            (root / "run/checkpoint.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "CHECKSUM"):
                run(root, source, "tampered", resume_from=root / "run")
            self.assertEqual(count, len(source.calls))

    def test_journal_recovers_sealed_work_after_abrupt_kill_without_checkpoint(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock()); run(root, source, max_requests=3)
            interrupted = root / "abrupt"; interrupted.mkdir()
            for name in ["plan.json", "progress.jsonl", "request_log.jsonl"]:
                (interrupted / name).write_bytes((root / "run" / name).read_bytes())
            with (interrupted / "progress.jsonl").open("a", encoding="utf-8") as f: f.write('{"ticker":')
            result = run(root, source, "recovered", resume_from=interrupted)
            self.assertEqual(5, result["network_requests_this_run"]); self.assertEqual(4, result["observation_count"])

    def test_abrupt_source_failure_cannot_resume_via_unsealed_journal(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock(), blocked=True); run(root, source)
            interrupted = root / "abrupt"; interrupted.mkdir()
            for name in ["plan.json", "progress.jsonl", "request_log.jsonl"]:
                (interrupted / name).write_bytes((root / "run" / name).read_bytes())
            with self.assertRaisesRegex(ValueError, "PRIOR_SOURCE_FAILURE"):
                run(root, source, "blocked-resume", resume_from=interrupted)
            self.assertEqual(1, len(source.calls))

    def test_scope_is_c8_hnx_upcom_and_outputs_never_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock())
            dry = run(root, source, "dry", dry_run=True)
            self.assertEqual(3, dry["universe_rows"]); self.assertEqual(2, dry["scope_tickers"])
            with self.assertRaisesRegex(ValueError, "OUTSIDE"):
                run(root, source, "bad", tickers=["AAA"])
            run(root, source)
            with self.assertRaises(FileExistsError): run(root, source)

    def test_seed_batch_expands_work_scope_without_refetching_finished_ticker(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); universe(root); source = Source(Clock())
            first = run(root, source, tickers=["PVS"])
            self.assertEqual(4, first["network_requests_this_run"])
            result = run(root, source, "expanded", seed_batch=root / "run")
            self.assertEqual(4, result["network_requests_this_run"]); self.assertEqual(4, result["observation_count"])
            self.assertEqual(2, result["handled_tickers"])
            self.assertEqual(1, sum(c["form"].get("pArticlesID") == ["100"] for c in source.calls))


if __name__ == "__main__": unittest.main()
