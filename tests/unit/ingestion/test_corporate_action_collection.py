import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion import corporate_actions_v1 as base
from delta_t1.ingestion import corporate_action_collection as pipeline
from delta_t1.ingestion.corporate_action_sources import (
    PublicTransport, SourceLimitation, parse_vsdc, parse_hnx, sha, search_url, discover_vsdc, terms, component_sections,
)

SCOPE = [{"security_id": "SYNTHETIC-SEC", "ticker": "TEST", "exchange": "HNX",
          "isin": "VNTEST000001", "valid_from": "2010-01-01", "valid_to": "2030-01-01",
          "identity_status": "VERIFIED", "identity_source_url": "https://vsdc.vn/synthetic-identity"}]
SCOPE_FIELDS = tuple(SCOPE[0])


def notice(kind="CASH_DIVIDEND", term=None, ex=True, explicit_time=True, title=None):
    names = {"CASH_DIVIDEND": "Trả cổ tức bằng tiền", "STOCK_DIVIDEND": "Trả cổ tức bằng cổ phiếu",
             "BONUS_SHARE": "Phát hành cổ phiếu thưởng", "RIGHTS_ISSUE": "Thực hiện quyền mua cổ phiếu",
             "STOCK_SPLIT": "Tách cổ phiếu", "REVERSE_SPLIT": "Gộp cổ phiếu"}
    terms = {"CASH_DIVIDEND": "Tỷ lệ thực hiện: 15% (01 cổ phiếu được nhận 1.500 đồng)",
             "STOCK_DIVIDEND": "Tỷ lệ thực hiện: 15%", "BONUS_SHARE": "Tỷ lệ thực hiện: 64,58%",
             "RIGHTS_ISSUE": "Tỷ lệ thực hiện: 10:3 (Người sở hữu 10 cổ phiếu được mua 3 cổ phiếu); Giá phát hành: 10.000 đồng/cổ phiếu",
             "STOCK_SPLIT": "Hệ số tách: 2", "REVERSE_SPLIT": "Hệ số gộp: 0,5"}
    pairs = [("Mã chứng khoán", "TEST"), ("Mã ISIN", "VNTEST000001"), ("Nơi giao dịch", "HNX"),
             ("Ngày đăng ký cuối cùng", "11/01/2024"), ("Lý do mục đích", names[kind])]
    info = "".join(f'<div class="item-info">{k}:</div><div class="item-info item-info-main">{v}</div>' for k, v in pairs)
    return ('<h3 class="title-category">TEST: ' + (title or names[kind]) + '</h3>'
            + ('<div class="time-newstcph">Ngày đăng 02/01/2024 - 09:00:00</div>' if explicit_time
               else '<div class="time-newstcph">Cập nhật ngày 02/01/2024 - 09:00:00</div>')
            + ('<time datetime="2024-01-02T09:00:00+07:00"></time>' if explicit_time else '')
            + '<div class="content-category">' + info + '<p>SYNTHETIC TEST ONLY; ' + (term if term is not None else terms[kind])
            + ('; Ngày giao dịch không hưởng quyền: 10/01/2024' if ex else '')
            + '; Ngày thanh toán: 01/02/2024</p></div>')


def evidence(html, url="https://vsdc.vn/vi/ad/1"):
    return dict(url=url, source_hash=sha(html.encode()), fetched_at="2024-02-02T12:00:00+07:00")


def parsed(kind="CASH_DIVIDEND", **kwargs):
    html = notice(kind, **kwargs)
    return parse_vsdc(html, evidence(html))


def classify(rows):
    return pipeline.classify(rows, SCOPE, "2024-02-03T12:00:00+07:00")


class FakeTransport:
    calls = 0
    def __init__(self, root, **kwargs):
        self.root, self.requests = root, []
    def fetch(self, url, payload=None, content_type=None):
        FakeTransport.calls += 1
        html = '<a href="/vi/ad/1">TEST</a>Hiển thị: 1 - 1 / 1 bản ghi' if '/search?' in url else notice()
        ev = evidence(html, url)
        path = self.root / 'raw' / f'response-{len(self.requests)+1}.bin'
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(html.encode())
        ev.update(path=path.relative_to(self.root).as_posix(), status=200)
        self.requests.append(ev)
        return html, ev


class SemiautomaticCorporateActionTests(unittest.TestCase):
    def test_abbreviated_dividend_needs_explicit_per_share_cash_proof(self):
        html=notice().replace('Trả cổ tức bằng tiền','Chi trả tạm ứng cổ tức đợt 1 năm 2021')
        rows=parse_vsdc(html,evidence(html))
        self.assertEqual('CASH_DIVIDEND',rows[0]['event_type'])
        self.assertEqual('1500',rows[0]['cash_dividend_per_share'])
        no_cash=notice(term='Tỷ lệ thực hiện: 15%').replace('Trả cổ tức bằng tiền','Chi trả tạm ứng cổ tức đợt 1 năm 2021')
        self.assertEqual('OTHER',parse_vsdc(no_cash,evidence(no_cash))[0]['event_type'])

    def test_cancellation_and_purpose_change_titles_keep_revision_review(self):
        for title in ['TEST: Hủy thông báo ngày đăng ký cuối cùng','TEST: Hủy danh sách người sở hữu chứng khoán','TEST: Thay đổi mục đích chốt danh sách']:
            html=notice(title=title)
            self.assertEqual('UNRESOLVED',parse_vsdc(html,evidence(html))[0]['revision_status'])

    def test_rights_two_leg_proof_required_and_preserved(self):
        phrase = ('Tỷ lệ thực hiện: 5:1 (01 cổ phiếu được hưởng 01 quyền, '
                  '05 quyền được mua 01 cổ phiếu mới). Giá chào bán: 15.000 đồng/cổ phiếu')
        raw = {}
        values,issues = terms('RIGHTS_ISSUE',phrase,raw)
        self.assertEqual('5:1',values['rights_ratio'])
        self.assertEqual('15000',values['rights_subscription_price'])
        self.assertEqual('5:1',raw['rights_ratio'])
        self.assertFalse(issues)
        missing_allocation = phrase.replace('01 cổ phiếu được hưởng 01 quyền, ','')
        values,issues = terms('RIGHTS_ISSUE',missing_allocation)
        self.assertNotIn('rights_ratio',values)
        self.assertIn('RATIO_PARSE_AMBIGUITY',issues)
        contradictory = phrase.replace('05 quyền được mua 01','05 quyền được mua 02')
        self.assertNotIn('rights_ratio',terms('RIGHTS_ISSUE',contradictory)[0])

    def test_explicit_mixed_sections_inside_one_paragraph_keep_terms_separate(self):
        fragment = ('a. Trả cổ tức bằng tiền: 01 cổ phiếu được nhận 1.000 đồng '
                    'b. Phát hành cổ phiếu thưởng: Tỷ lệ thực hiện: 6:2 '
                    '(Người sở hữu 06 cổ phiếu được nhận 02 cổ phiếu mới) '
                    'c. Chào bán cổ phiếu cho cổ đông hiện hữu: Giá phát hành: 15.000 đồng/cổ phiếu '
                    'Tỷ lệ thực hiện: 100:10 (01 cổ phiếu được hưởng 01 quyền, 100 quyền được mua 10 cổ phiếu mới)')
        rows=parsed(term=fragment,title='Trả cổ tức bằng tiền, phát hành cổ phiếu thưởng và thực hiện quyền mua')
        by_type={r['event_type']:r for r in rows}
        self.assertEqual(3,len(rows))
        self.assertEqual('1000',by_type['CASH_DIVIDEND']['cash_dividend_per_share'])
        self.assertEqual('6:2',by_type['BONUS_SHARE']['bonus_ratio'])
        self.assertEqual('100:10',by_type['RIGHTS_ISSUE']['rights_ratio'])
        self.assertNotIn('rights_subscription_price',by_type['BONUS_SHARE'])
        self.assertNotIn('bonus_ratio',by_type['RIGHTS_ISSUE'])
        classified=classify(rows)
        self.assertEqual(1,len({r['event']['event_group_id'] for r in classified}))
        self.assertEqual(3,len({r['event']['event_id'] for r in classified}))

    def test_duplicate_component_headings_remain_ambiguous(self):
        text=('a. Trả cổ tức bằng tiền: 01 cổ phiếu nhận 100 đồng '
              'b. Trả cổ tức bằng tiền: 01 cổ phiếu nhận 200 đồng '
              'c. Thực hiện quyền mua: Tỷ lệ thực hiện: 5:1')
        self.assertNotIn('CASH_DIVIDEND',component_sections(text))

    def test_search_later_page_failure_preserves_earlier_links_and_marks_partial(self):
        class BrokenPagination:
            def fetch(self, url, payload=None):
                if payload is not None:
                    raise SourceLimitation('SOURCE_ACCESS_LIMITATION: HTTP 400')
                html = '<a href="/vi/ad/1">TEST</a>Hiển thị: 1 - 20 / 47 bản ghi'
                return html, evidence(html,url)
        links, check = discover_vsdc(BrokenPagination(), 'TEST', 20, 100)
        self.assertEqual(['https://vsdc.vn/vi/ad/1'],links)
        self.assertEqual('PARTIAL',check['status'])
        self.assertEqual(2,check['failed_page'])
        self.assertIn('HTTP 400',check['pagination_error'])
        self.assertEqual(1,len(check['search_evidence']))

    def test_search_first_page_failure_still_raises(self):
        class Unavailable:
            def fetch(self, *args, **kwargs):
                raise SourceLimitation('SOURCE_ACCESS_LIMITATION: HTTP 403')
        with self.assertRaises(SourceLimitation):
            discover_vsdc(Unavailable(),'TEST',20,100)

    def test_collection_keeps_details_after_search_pagination_failure(self):
        class PartialSearch(FakeTransport):
            def fetch(self,url,payload=None,content_type=None):
                if payload is not None:
                    raise SourceLimitation('SOURCE_ACCESS_LIMITATION: HTTP 400')
                html, ev = super().fetch(url,payload,content_type)
                if '/search?' in url:
                    html = html.replace('1 - 1 / 1','1 - 20 / 47')
                    ev['source_hash'] = sha(html.encode())
                    (self.root/ev['path']).write_bytes(html.encode())
                return html, ev
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scope = root/'scope.csv'
            scope.write_text(base.csv_text(SCOPE_FIELDS,SCOPE),encoding='utf-8')
            result = pipeline.collect(scope,root/'run','2019-01-31','2025-12-31',
                                      sources=['VSDC'],transport_factory=PartialSearch,max_pages=20,max_details=100)
            self.assertEqual(1,result['candidate_count'])
            checks = json.loads((root/'run/source_checks.json').read_text())
            self.assertEqual(2,checks['checks'][0]['failed_page'])

    def test_partial_search_does_not_retry_host_after_pagination_403(self):
        class Opener:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                if self.calls == 1:
                    body = b'<a href="/vi/ad/1">TEST</a>'
                    return HTTPError(request.full_url,200,'test',{'Content-Type':'text/html'},io.BytesIO(body))
                raise HTTPError(request.full_url,403,'test',{'Content-Type':'text/html'},io.BytesIO(b'denied'))
        with tempfile.TemporaryDirectory() as temp:
            opener = Opener()
            client = PublicTransport(Path(temp),opener=opener,sleep=lambda _:None)
            links,check = discover_vsdc(client,'TEST',20,100)
            self.assertEqual(2,check['failed_page'])
            with self.assertRaises(SourceLimitation):
                client.fetch(links[0])
            self.assertEqual(2,opener.calls)

    def make_run(self, root):
        scope, run = root / "scope.csv", root / "run"
        scope.write_text(base.csv_text(SCOPE_FIELDS, SCOPE), encoding="utf-8")
        pipeline.collect(scope, run, "2019-01-31", "2025-12-31", sources=["VSDC"], transport_factory=FakeTransport)
        return run, scope

    def test_six_valid_event_types_and_decimal_normalization(self):
        for kind in pipeline.base.TERMS:
            if kind == "OTHER":
                continue
            with self.subTest(kind=kind):
                rows = classify(parsed(kind))
                self.assertEqual("AUTO_VERIFIED", rows[0]["verification_status"], rows[0]["review_reasons"])
        self.assertEqual(.6458, classify(parsed("BONUS_SHARE"))[0]["event"]["bonus_ratio"])
        self.assertEqual(.3, classify(parsed("RIGHTS_ISSUE"))[0]["event"]["rights_ratio"])
        self.assertEqual(1500, classify(parsed())[0]["event"]["cash_dividend_per_share"])

    def test_missing_ex_date_never_inferred_from_record(self):
        row = classify(parsed(ex=False))[0]
        self.assertIn("MISSING_EX_DATE", row["review_reasons"])
        self.assertIsNone(row["event"]["ex_date"])

    def test_missing_available_at_and_unknown_source_time(self):
        raw = parsed()[0]
        raw["available_at"] = None
        self.assertIn("MISSING_AVAILABLE_AT", classify([raw])[0]["review_reasons"])
        row = classify(parsed(explicit_time=False))[0]
        self.assertEqual("2024-02-02T12:00:00+07:00", row["event"]["available_at"])
        self.assertIn("SOURCE_PUBLIC_TIME_UNVERIFIED", row["review_reasons"])

    def test_invalid_percentage_ambiguous_ratio_and_literal_outlier(self):
        for term in ("Tỷ lệ thực hiện: 15%%", "Tỷ lệ thực hiện: 10:3", "Tỷ lệ thực hiện: 6458%"):
            row = classify(parsed("BONUS_SHARE", term=term))[0]
            self.assertNotEqual("AUTO_VERIFIED", row["verification_status"], term)
        self.assertEqual(64.58, classify(parsed("BONUS_SHARE", term="Tỷ lệ thực hiện: 6458%"))[0]["event"]["bonus_ratio"])

    def test_exact_repeat_deduplicated_but_distinct_notices_reviewed(self):
        rows = parsed()
        dedup = classify(rows + rows)
        self.assertEqual(1, len(dedup))
        self.assertEqual(2, dedup[0]["duplicate_evidence_count"])
        other = parsed()[0]
        other["primary_source_url"] = "https://vsdc.vn/vi/ad/2"
        suspect = classify(rows + [other])
        self.assertEqual(2, len(suspect))
        self.assertTrue(all("DUPLICATE_SUSPECTED" in r["review_reasons"] for r in suspect))

    def test_conflict_preserves_all_values(self):
        a, b = parsed()[0], parsed(term="01 cổ phiếu được nhận 1.700 đồng")[0]
        b["primary_source_url"] = "https://vsdc.vn/vi/ad/2"
        rows = classify([a, b])
        self.assertEqual({1500, 1700}, {r["event"]["cash_dividend_per_share"] for r in rows})
        self.assertTrue(all("SOURCE_CONFLICT" in r["review_reasons"] for r in rows))
        self.assertTrue(pipeline.queue_rows(rows)[0]["conflicting_value"])

    def test_mixed_same_day_separate_rows_and_missing_component_blocks_group(self):
        rows = classify(parsed() + parsed("STOCK_DIVIDEND"))
        self.assertEqual(2, len(rows))
        self.assertEqual(1, len({r["event"]["event_group_id"] for r in rows}))
        self.assertTrue(all(r["verification_status"] == "AUTO_VERIFIED" for r in rows))
        bad = parsed("STOCK_DIVIDEND", term="Tỷ lệ chưa xác định")
        rows = classify(parsed() + bad)
        self.assertTrue(all(r["verification_status"] != "AUTO_VERIFIED" for r in rows))

    def test_revision_quarantined_and_raw_provenance_kept(self):
        rows = classify(parsed(title="Đính chính thông báo trả cổ tức bằng tiền"))
        self.assertIn("REVISION_OR_CORRECTION_DETECTED", rows[0]["review_reasons"])
        self.assertEqual("UNRESOLVED", rows[0]["event"]["revision_status"])
        self.assertTrue(rows[0]["source"]["source_hash"])
        original = parsed()[0]
        correction = parsed(title="Đính chính thông báo trả cổ tức bằng tiền")[0]
        correction.update(primary_source_url="https://vsdc.vn/vi/ad/2", ex_date="2024-01-09",
                          revision_reference_urls=[original["primary_source_url"]])
        both = classify([original, correction])
        self.assertTrue(all(r["verification_status"] == "MANUAL_REVIEW" for r in both))

    def test_identity_requires_historical_interval_and_isin_match(self):
        row = parsed()[0]
        row["isin"] = "WRONG"
        self.assertNotEqual("AUTO_VERIFIED", classify([row])[0]["verification_status"])
        scope = [SCOPE[0] | {"valid_from": "2025-01-01"}]
        self.assertNotEqual("AUTO_VERIFIED", pipeline.classify(parsed(), scope, "2024-02-03T12:00:00+07:00")[0]["verification_status"])

    def test_hnx_explicit_dates_crosscheck_does_not_backdate_knowledge(self):
        html = '<table><tr><th>Ngày GDKHQ</th><th>Ngày ĐKCC</th></tr><tr><td>Trả cổ tức bằng tiền</td><td>10/01/2024</td><td>11/01/2024</td><td>01/02/2024</td></tr></table>'
        ev = evidence(html, "https://www.hnx.vn/vi-vn/m-tim-kiem-TEST.html")
        calendar, _ = parse_hnx(html, ev, "TEST")
        result = classify(parsed(ex=False) + calendar)
        self.assertEqual(1, len(result))
        self.assertEqual("2024-01-10", result[0]["event"]["ex_date"])
        self.assertEqual(ev["fetched_at"], result[0]["event"]["available_at"])
        self.assertNotEqual("AUTO_VERIFIED", result[0]["verification_status"])
        self.assertEqual(2, len(result[0]["source"]["evidence"]))

    def test_manual_approval_and_rejection_select_existing_evidence(self):
        a, b = parsed()[0], parsed(term="01 cổ phiếu được nhận 1.700 đồng")[0]
        b["primary_source_url"] = "https://vsdc.vn/vi/ad/2"
        candidates = classify([a, b])
        queue = pipeline.queue_rows(candidates)
        for i, row in enumerate(queue):
            row.update(review_status="APPROVED" if i == 0 else "REJECTED", reviewed_by="UNIT_TEST_ONLY",
                       reviewed_at="2024-02-04T09:00:00+07:00", review_decision="USE_CANDIDATE" if i == 0 else "REJECT_CANDIDATE",
                       review_note="SYNTHETIC TEST ONLY; explicit source resolution")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reviews.csv"
            path.write_text(base.csv_text(pipeline.QUEUE_FIELDS, queue), encoding="utf-8")
            resolved = pipeline.decisions(candidates, path)
            self.assertEqual(["MANUALLY_VERIFIED", "REJECTED"], [r["verification_status"] for r in resolved])
            queue[0]["candidate_value"] = "tampered"
            path.write_text(base.csv_text(pipeline.QUEUE_FIELDS, queue), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "evidence fields edited"):
                pipeline.decisions(candidates, path)

    def test_manual_approval_cannot_fill_missing_terms_or_bypass_identity(self):
        candidates = classify(parsed(ex=False))
        queue = pipeline.queue_rows(candidates)
        queue[0].update(review_status="APPROVED", reviewed_by="UNIT_TEST_ONLY", reviewed_at="2024-02-04T09:00:00+07:00",
                        review_decision="USE_CANDIDATE", review_note="SYNTHETIC TEST ONLY")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "review.csv"
            path.write_text(base.csv_text(pipeline.QUEUE_FIELDS, queue), encoding="utf-8")
            self.assertEqual("MANUAL_REVIEW", pipeline.decisions(candidates, path)[0]["verification_status"])

    def test_manual_supplement_signed_approval_to_canonical(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scope, manual = root / "scope.csv", root / "manual.csv"
            scope.write_text(base.csv_text(SCOPE_FIELDS, SCOPE), encoding="utf-8")
            row = classify(parsed())[0]["base_input"]
            manual.write_text(base.csv_text(base.FIELDS, [row]), encoding="utf-8")
            run = root / "manual-run"
            pipeline.collect(scope, run, "2019-01-31", "2025-12-31", sources=[], manual_input=manual, transport_factory=FakeTransport)
            candidates, _ = pipeline.load_collection(run)
            self.assertEqual(["MANUAL_EVIDENCE_INPUT"], candidates[0]["review_reasons"])
            queue = pipeline.queue_rows(candidates)
            from delta_t1.ingestion.corporate_action_sources import now
            queue[0].update(review_status="APPROVED", reviewed_by="UNIT_TEST_ONLY", reviewed_at=now(),
                            review_decision="USE_CANDIDATE", review_note="SYNTHETIC TEST ONLY signed approval")
            reviews = root / "reviews.csv"
            reviews.write_text(base.csv_text(pipeline.QUEUE_FIELDS, queue), encoding="utf-8")
            output = root / "canonical"
            self.assertEqual(1, pipeline.build_collection(run, output, reviews)["verified_event_count"])
            canonical = pipeline.read_jsonl(output / "corporate_actions_v1.jsonl")[0]
            self.assertEqual("MANUALLY_VERIFIED", canonical["verification_status"])
            self.assertEqual("UNIT_TEST_ONLY", canonical["reviewed_by"])

    def test_collect_build_integrity_schema_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run, _ = self.make_run(root)
            rows, _ = pipeline.load_collection(run)
            self.assertEqual("AUTO_VERIFIED", rows[0]["verification_status"])
            self.assertEqual([], base.read_csv(run / "manual_review_queue.csv", pipeline.QUEUE_FIELDS))
            output = root / "canonical"
            result = pipeline.build_collection(run, output)
            self.assertEqual(1, result["verified_event_count"])
            self.assertEqual("AUTO_VERIFIED", pipeline.read_jsonl(output / "corporate_actions_v1.jsonl")[0]["verification_status"])
            with self.assertRaises(ValueError):
                pipeline.build_collection(run, output)
            replay = root / "replay"
            requests_before = FakeTransport.calls
            self.assertEqual(0, pipeline.replay_collection(run, replay)["network_requests"])
            self.assertEqual(requests_before, FakeTransport.calls)
            self.assertEqual(rows[0]["candidate_id"], pipeline.load_collection(replay)[0][0]["candidate_id"])
            (run / "candidates.jsonl").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CHECKSUM"):
                pipeline.load_collection(run)

    def test_zero_events_not_reviewed_and_no_event_confirmed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run, scope = self.make_run(root)
            # Separate manual-only, genuinely empty fixture collection.
            empty = root / "empty"
            pipeline.collect(scope, empty, "2019-01-31", "2025-12-31", sources=[], transport_factory=FakeTransport)
            report = pipeline.coverage(empty)
            self.assertFalse(report["coverage_pass"])
            self.assertEqual("NOT_YET_REVIEWED", report["rows"][0]["coverage_status"])
            attestation = root / "attest.csv"
            attestation.write_text(base.csv_text(base.COVERAGE_FIELDS, [dict.fromkeys(base.COVERAGE_FIELDS, "") | {k: SCOPE[0][k] for k in ("security_id", "ticker", "exchange")} | {
                "reviewed_start_date": "2019-01-31", "reviewed_end_date": "2025-12-31", "review_status": "REVIEWED",
                "reviewed_event_types": "ALL_V1", "primary_source_type": "VSDC", "primary_source_url": "https://vsdc.vn/synthetic-test-only",
                "coverage_evidence": "SYNTHETIC TEST ONLY complete archive log", "reviewer": "UNIT_TEST_ONLY", "last_checked_at": "2026-01-02T09:00:00+07:00"}]), encoding="utf-8")
            confirmed = pipeline.coverage(empty, attestation=attestation)
            self.assertTrue(confirmed["coverage_pass"])
            self.assertEqual("NO_EVENT_CONFIRMED", confirmed["rows"][0]["coverage_status"])

    def test_verified_event_alone_does_not_complete_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            run, _ = self.make_run(Path(temp))
            report = pipeline.coverage(run)
            self.assertFalse(report["coverage_pass"])
            self.assertEqual("HAS_VERIFIED_EVENTS", report["rows"][0]["coverage_status"])
            self.assertEqual("COVERAGE_INCOMPLETE", report["rows"][0]["completeness_status"])

    def test_dry_run_zero_network_and_no_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scope = root / "scope.csv"
            scope.write_text(base.csv_text(SCOPE_FIELDS, SCOPE), encoding="utf-8")
            count = FakeTransport.calls
            result = pipeline.collect(scope, root / "dry", "2019-01-31", "2025-12-31", dry_run=True, transport_factory=FakeTransport)
            self.assertEqual(0, result["network_requests"])
            self.assertEqual(count, FakeTransport.calls)
            self.assertFalse((root / "dry").exists())

    def test_transport_401_403_429_redirect_challenge_and_budget_fail_closed(self):
        class Opener:
            def __init__(self, status, data=b"denied"):
                self.status, self.data, self.calls = status, data, 0
            def open(self, request, timeout):
                self.calls += 1
                raise HTTPError(request.full_url, self.status, "test", {"Content-Type": "text/html"}, io.BytesIO(self.data))
        with tempfile.TemporaryDirectory() as temp:
            for status in (401, 403, 429, 302):
                root = Path(temp) / str(status)
                root.mkdir()
                opener = Opener(status)
                client = PublicTransport(root, opener=opener, sleep=lambda _: None, max_requests=1)
                with self.assertRaises(SourceLimitation):
                    client.fetch(search_url("TEST"))
                with self.assertRaises(SourceLimitation):
                    client.fetch(search_url("TEST"))
                self.assertEqual(1, opener.calls)
                self.assertTrue(client.requests[0]["source_hash"])

    def test_parser_layout_change_is_limitation_not_empty_coverage(self):
        for parser, args in ((parse_vsdc, ("<html>changed</html>", {})), (parse_hnx, ("<html>changed</html>", {}, "TEST"))):
            with self.assertRaises(SourceLimitation):
                parser(*args)


if __name__ == "__main__":
    unittest.main()
