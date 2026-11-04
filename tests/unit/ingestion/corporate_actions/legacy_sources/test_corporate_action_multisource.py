import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion import corporate_actions_v1 as base
from delta_t1.ingestion import corporate_action_collection as legacy
from delta_t1.ingestion import corporate_action_multisource as multi
from delta_t1.ingestion.corporate_action_sources import hnx_market_context, kinds, parse_hnx, terms, SourceLimitation
from delta_t1.ingestion.corporate_action_hose import collect_hose

SCOPE = [{"security_id": "SYNTHETIC-SEC", "ticker": "TEST", "exchange": "HNX", "isin": "VNTEST000001",
          "valid_from": "2010-01-01", "valid_to": "2030-01-01", "identity_status": "VERIFIED",
          "identity_source_url": "https://vsdc.vn/synthetic-identity"}]
CREATED = "2024-02-03T12:00:00+07:00"


def obs(source="VSDC", fields=None, url=None, published="2024-01-02T09:00:00+07:00", **meta):
    default = {"ticker": "TEST", "exchange": "HNX", "isin": "VNTEST000001", "event_type": "CASH_DIVIDEND",
               "record_date": "2024-01-11"}
    default.update(fields or {})
    return multi.observation(dict(source_type=source, source_url=url or {"VSDC": "https://vsdc.vn/vi/ad/1", "HNX": "https://www.hnx.vn/synthetic", "CAFEF": "https://cafef.vn/synthetic", "ISSUER_IR": "https://issuer.example/notice"}[source],
                                  raw_terms="SYNTHETIC TEST ONLY " + json.dumps(default, ensure_ascii=False), values=default,
                                  source_published_at=published, observed_at="2024-01-03T09:00:00+07:00", **meta))


def pair():
    return [obs(fields={"cash_dividend_per_share": "1500", "currency": "VND"}),
            obs("HNX", {"ex_date": "2024-01-10", "payment_date": "2024-02-01"})]


def reconcile(rows):
    return multi.reconcile(rows, SCOPE, CREATED)


def fixture_run(root, observations):
    root.mkdir()
    plan = dict(created_at=CREATED, start="2024-01-01", end="2024-12-31", sources=["VSDC", "HNX"])
    base.write_new(root / "scope.csv", base.csv_text(tuple(SCOPE[0]), SCOPE))
    base.write_new(root / "plan.json", base.json_text(plan))
    base.write_new(root / "source_checks.json", base.json_text(dict(checks=[], limitations=[])))
    base.write_new(root / "requests.json", "[]\n")
    multi.finalize(root, observations, SCOPE, plan)
    multi.manifest(root, dict(status="PARTIAL", network_requests=0))


class MultiSourceCorporateActionTests(unittest.TestCase):
    def test_replay_shared_component_receipt_path_prefixed_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';out=Path(temp)/'replay'
            rows=pair()
            receipt={'path':'raw/shared.bin','source_hash':'0'*64}
            for row in rows:row['source_evidence']=[receipt]
            fixture_run(root,rows)
            plan=json.loads((root/'plan.json').read_text())
            with patch.object(multi,'load',return_value=(rows,SCOPE,plan)):
                multi.replay(root,out)
            replayed=legacy.read_jsonl(out/'observations.jsonl')
            self.assertEqual(['prior/raw/shared.bin']*2,[o['source_evidence'][0]['path'] for o in replayed])
            self.assertEqual('raw/shared.bin',receipt['path'])

    def test_same_event_vsdc_hnx_completion_and_provenance(self):
        events, queue = reconcile(pair())
        self.assertEqual(1, len(events))
        e = events[0]
        self.assertEqual("AUTO_VERIFIED", e["verification_status"], e["issues"])
        self.assertEqual("COMPLETE", e["pit_timing_verification"])
        self.assertEqual(1500, e["values"]["cash_dividend_per_share"])
        self.assertEqual("HNX", e["field_provenance"]["ex_date"]["observations"][0]["source_type"])
        self.assertEqual("VSDC", e["field_provenance"]["cash_dividend_per_share"]["observations"][0]["source_type"])
        self.assertFalse(queue)

    def test_same_ratio_different_raw_format_is_not_conflict(self):
        a = obs(fields={"event_type": "STOCK_DIVIDEND", "stock_dividend_ratio": "15%", "ex_date": "2024-01-10"})
        b = obs("CAFEF", {"event_type": "STOCK_DIVIDEND", "stock_dividend_ratio": "0.15", "ex_date": "2024-01-10"})
        e = reconcile([a, b])[0][0]
        self.assertEqual("VERIFIED", e["event_data_verification"])
        self.assertEqual(.15, e["values"]["stock_dividend_ratio"])
        self.assertEqual({"15%", "0.15"}, {o["raw_value"] for o in e["field_provenance"]["stock_dividend_ratio"]["observations"]})

    def test_authority_vendor_conflict_not_silently_resolved(self):
        a = obs(fields={"event_type": "STOCK_DIVIDEND", "stock_dividend_ratio": "64.58%", "ex_date": "2024-01-10"})
        b = obs("CAFEF", {"event_type": "STOCK_DIVIDEND", "stock_dividend_ratio": "6458%", "ex_date": "2024-01-10"})
        events, queue = reconcile([a, b])
        self.assertEqual("PARTIAL", events[0]["event_data_verification"])
        q = next(r for r in queue if r["conflicting_field"] == "stock_dividend_ratio" and r["review_reason"] == "FIELD_CONFLICT")
        choice = q | dict(review_status="APPROVED", chosen_observation_id=a["observation_id"], reviewed_by="TEST", reviewed_at="2024-02-04T09:00:00+07:00", review_decision="USE_OBSERVATION", review_note="SYNTHETIC USE_VSDC_VALUE")
        resolved = multi.reconcile([a, b], SCOPE, CREATED, {q["review_id"]: choice})[0][0]
        self.assertEqual("MANUALLY_VERIFIED", resolved["verification_status"])
        self.assertEqual(.6458, resolved["values"]["stock_dividend_ratio"])
        self.assertEqual(2, len(resolved["field_provenance"]["stock_dividend_ratio"]["observations"]))
        with tempfile.TemporaryDirectory() as temp:
            root, output = Path(temp) / "run", Path(temp) / "canonical"
            fixture_run(root, [a, b])
            review_file = Path(temp) / "reviews.csv"
            review_file.write_text(base.csv_text(multi.QUEUE_FIELDS, [choice]), encoding="utf-8")
            self.assertEqual(1, multi.build(root, output, review_file)["verified_event_count"])
            canonical = legacy.read_jsonl(output / "corporate_actions_v1.jsonl")[0]
            self.assertEqual(.6458, canonical["stock_dividend_ratio"])
            self.assertEqual(2, len(legacy.read_jsonl(output / "observations.jsonl")))

    def test_pit_partial_does_not_invalidate_verified_terms(self):
        rows = pair()
        rows[1]["source_published_at"] = None
        rows[1]["observed_at"] = "2026-11-01T09:00:00+07:00"
        events, queue = reconcile(rows)
        e = events[0]
        self.assertEqual("VERIFIED", e["event_data_verification"])
        self.assertEqual("PARTIAL", e["pit_timing_verification"])
        self.assertEqual("2026-11-01T09:00:00+07:00", e["available_at"])
        self.assertTrue(any(q["review_reason"] == "PIT_TIMESTAMP_INCOMPLETE" for q in queue))

    def test_missing_ex_date_only_requests_missing_field(self):
        events, queue = reconcile([pair()[0]])
        self.assertEqual("PARTIAL", events[0]["event_data_verification"])
        self.assertEqual(["ex_date"], [r["conflicting_field"] for r in queue if r["review_reason"] == "MISSING_EX_DATE"])

    def test_mixed_events_are_separate_components_same_group(self):
        stock = obs(fields={"event_type": "STOCK_DIVIDEND", "stock_dividend_ratio": "15%", "ex_date": "2024-01-10"})
        events, _ = reconcile(pair() + [stock])
        self.assertEqual(2, len(events))
        self.assertEqual(1, len({e["event_group_id"] for e in events}))
        self.assertEqual(2, len({e["event_id"] for e in events}))
        self.assertTrue(all(e["event_data_verification"] == "VERIFIED" for e in events))

    def test_incomplete_mixed_group_cannot_partial_promote(self):
        stock = obs(fields={"event_type": "STOCK_DIVIDEND", "ex_date": "2024-01-10"})
        events, _ = reconcile(pair() + [stock])
        self.assertTrue(all(e["event_data_verification"] == "PARTIAL" for e in events))
        bad_cash = obs(fields={"cash_dividend_per_share": "1500", "currency": "VND", "ex_date": "2024-01-10", "stock_dividend_ratio": "15%"})
        self.assertEqual("PARTIAL", reconcile([bad_cash])[0][0]["event_data_verification"])

    def test_multiple_announcements_same_source_ambiguous(self):
        duplicate = obs(fields={"cash_dividend_per_share": "1500", "currency": "VND"}, url="https://vsdc.vn/vi/ad/2")
        events, queue = reconcile(pair() + [duplicate])
        self.assertEqual("AMBIGUOUS", events[0]["matching_status"])
        self.assertTrue(any(r["review_reason"] == "EVENT_MATCH_AMBIGUOUS" for r in queue))

    def test_same_ticker_near_date_not_merged(self):
        a, b = pair()
        b["fields"]["record_date"]["normalized_value"] = "2024-01-12"
        events, _ = reconcile([a, b])
        self.assertEqual(2, len(events))
        self.assertTrue(all(e["event_data_verification"] == "PARTIAL" for e in events))

    def test_revision_signed_effective_record_preserves_original(self):
        original = obs(fields={"cash_dividend_per_share": "1500", "currency": "VND", "ex_date": "2024-01-10"})
        correction = obs(fields={"cash_dividend_per_share": "1700", "currency": "VND", "ex_date": "2024-01-10"}, url="https://vsdc.vn/vi/ad/2",
                         published="2024-01-02T10:00:00+07:00", revision_status="CORRECTION", revision_of=[original["source_url"]], revision_number=2)
        events, queue = reconcile([original, correction])
        self.assertEqual("PARTIAL", events[0]["event_data_verification"])
        q = next(r for r in queue if r["conflicting_field"] == "__revision__")
        choice = q | dict(review_status="APPROVED", chosen_observation_id=correction["observation_id"], review_decision="USE_REVISION")
        e = multi.reconcile([original, correction], SCOPE, CREATED, {q["review_id"]: choice})[0][0]
        self.assertEqual("VERIFIED", e["event_data_verification"], e["issues"])
        self.assertEqual(1700, e["values"]["cash_dividend_per_share"])
        self.assertEqual(correction["observation_id"], e["effective_revision_id"])
        self.assertEqual(2, len(e["revision_lineage"]["observations"]))
        self.assertEqual("2024-01-02T10:00:00+07:00", e["available_at"])
        last = obs(fields={"cash_dividend_per_share": "1800", "currency": "VND", "ex_date": "2024-01-10"}, url="https://vsdc.vn/vi/ad/3",
                   published="2024-01-02T11:00:00+07:00", revision_status="CORRECTION", revision_of=[correction["source_url"]], revision_number=3)
        initial, qs = reconcile([original, correction, last])
        rq = next(r for r in qs if r["conflicting_field"] == "__revision__")
        selected = rq | dict(review_status="APPROVED", chosen_observation_id=last["observation_id"], review_decision="USE_REVISION")
        final = multi.reconcile([original, correction, last], SCOPE, CREATED, {rq["review_id"]: selected})[0][0]
        self.assertEqual("VERIFIED", final["event_data_verification"], final["issues"])
        self.assertEqual(1800, final["values"]["cash_dividend_per_share"])

    def test_manual_ir_partial_fields_use_same_validation(self):
        supplied = dict(source_type="ISSUER_IR", source_url="https://issuer.example/notice", raw_terms="SYNTHETIC TEST ONLY", values={"ticker": "TEST", "exchange": "HNX", "event_type": "RIGHTS_ISSUE", "record_date": "2024-01-11", "rights_subscription_price": "bad"})
        o = multi.observation(supplied, observed_at=CREATED, manual=True)
        self.assertEqual("INVALID", o["fields"]["rights_subscription_price"]["parse_status"])
        self.assertEqual(CREATED, o["observed_at"])

    def test_vendor_only_field_never_authority_equivalent(self):
        a = obs("CAFEF", {"cash_dividend_per_share": "1500", "currency": "VND", "ex_date": "2024-01-10"})
        self.assertEqual("PARTIAL", reconcile([a])[0][0]["event_data_verification"])

    def test_canonical_build_and_field_coverage_matrix(self):
        with tempfile.TemporaryDirectory() as temp:
            run, output = Path(temp) / "run", Path(temp) / "canonical"
            fixture_run(run, pair())
            result = multi.build(run, output)
            self.assertEqual(1, result["verified_event_count"])
            self.assertEqual("corporate-actions-v1-canonical-multisource", result["artifact_type"])
            with self.assertRaises(ValueError):
                multi.load(output)
            row = legacy.read_jsonl(output / "corporate_actions_v1.jsonl")[0]
            self.assertEqual("1.2.0", row["schema_version"])
            self.assertEqual("HNX", row["field_provenance"]["ex_date"]["observations"][0]["source_type"])
            report = multi.coverage(run)
            self.assertEqual(1, report["rows"][0]["events_with_verified_ex_date"])
            self.assertEqual(1, report["rows"][0]["events_with_verified_terms"])
            matrix = {r["source"]: r for r in report["source_completeness_matrix"]}
            self.assertEqual(1, matrix["VSDC"]["cash_dividend_per_share"])
            self.assertEqual(0, matrix["VSDC"]["ex_date"])
            self.assertEqual(1, matrix["HNX_LISTED"]["ex_date"])
            self.assertFalse(report["coverage_pass"])
            with self.assertRaises(ValueError):
                multi.build(run, output)

    def test_canonical_terms_verified_pit_partial_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            rows = pair();rows[1]["source_published_at"] = None
            run, output = Path(temp) / "run", Path(temp) / "canonical"
            fixture_run(run, rows)
            result = multi.build(run, output)
            self.assertEqual("PARTIAL", result["status"])
            e = legacy.read_jsonl(output / "corporate_actions_v1.jsonl")[0]
            self.assertEqual("VERIFIED", e["event_data_verification"])
            self.assertEqual("PARTIAL", e["pit_timing_verification"])

    def test_upcom_uses_observed_market_parameter(self):
        html = "<script>var _stock_code = 'TEST'; var _market_code = 'UC';</script>"
        self.assertEqual(("UC", "UPCOM"), hnx_market_context(html, "TEST"))
        with self.assertRaises(SourceLimitation):
            hnx_market_context(html, "WRONG")
        table = '<table><tr><th>Ngày GDKHQ</th><th>Ngày ĐKCC</th></tr><tr><td>Trả cổ tức bằng tiền</td><td>10/01/2024</td><td>11/01/2024</td><td>01/02/2024</td></tr></table>'
        rows, _ = parse_hnx(table, {"fetched_at": CREATED, "url": "https://www.hnx.vn/test", "source_hash": "0"*64}, "TEST", "UPCOM")
        self.assertEqual("UPCOM", rows[0]["exchange"])

    def test_cp_alias_and_vietnamese_decimal_colon_have_explicit_semantics(self):
        self.assertEqual(["STOCK_DIVIDEND"], kinds("Trả cổ tức bằng CP"))
        self.assertEqual(["STOCK_DIVIDEND"], kinds("Phát hành cổ phiếu để trả cổ tức cho cổ đông hiện hữu"))
        raw_values = {}
        parsed, issues = terms("STOCK_DIVIDEND", "Tỷ lệ thực hiện: 100:64,58 (Người sở hữu 100 cổ phiếu sẽ được nhận 64,58 cổ phiếu mới)", raw_values)
        self.assertEqual([], issues)
        self.assertEqual("100:64,58", raw_values["stock_dividend_ratio"])
        self.assertEqual(.6458, base.number(parsed["stock_dividend_ratio"], "stock_dividend_ratio", parsed["ratio_semantics"]))

    def test_zero_event_coverage_requires_full_attestation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            fixture_run(root, [])
            self.assertEqual("NOT_YET_REVIEWED", multi.coverage(root)["rows"][0]["coverage_status"])
            a = dict.fromkeys(base.COVERAGE_FIELDS, "") | {k: SCOPE[0][k] for k in ("security_id", "ticker", "exchange")} | dict(
                reviewed_start_date="2024-01-01", reviewed_end_date="2024-12-31", review_status="REVIEWED", reviewed_event_types="ALL_V1",
                primary_source_type="VSDC", primary_source_url="https://vsdc.vn/synthetic", coverage_evidence="SYNTHETIC FULL WINDOW LOG", reviewer="TEST", last_checked_at="2025-01-02T09:00:00+07:00")
            path = Path(temp) / "attestation.csv"
            path.write_text(base.csv_text(base.COVERAGE_FIELDS, [a]), encoding="utf-8")
            report = multi.coverage(root, attestation=path)
            self.assertTrue(report["coverage_pass"])
            self.assertEqual("NO_EVENT_CONFIRMED", report["rows"][0]["coverage_status"])

    def test_replay_does_not_refetch_and_preserves_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            run, output = Path(temp) / "run", Path(temp) / "replay"
            fixture_run(run, pair())
            result = multi.replay(run, output)
            self.assertEqual(0, result["network_requests"])
            self.assertEqual({o["observation_id"] for o in pair()}, {o["observation_id"] for o in multi.load(output)[0]})
            scope_file = Path(temp) / "reviewed_scope.csv"
            scope_file.write_text(base.csv_text(tuple(SCOPE[0]), [SCOPE[0] | {"security_id": "SYNTHETIC-REVIEWED-SEC"}]), encoding="utf-8")
            overridden = Path(temp) / "replay-scope"
            multi.replay(run, overridden, scope_override=scope_file)
            self.assertEqual(base.digest(overridden / "scope.csv"), multi.load(overridden)[2]["scope_sha256"])

    def test_hose_public_json_route_is_calendar_not_publication_time(self):
        class Client:
            def fetch(self, url):
                if "/q/" in url:
                    payload = {"items": [{"id": 1, "code": "TEST", "isin": "VNTEST000001"}]}
                else:
                    payload = {"success": True, "data": {"list": [{"code": "TEST", "catName": "Giao dịch không hưởng cổ tức bằng tiền", "id": 123, "postedDate": 1704844800}], "paging": {"totalPages": 1}}}
                return json.dumps(payload), {"url": url, "source_hash": "0"*64, "fetched_at": CREATED}
        rows, check = collect_hose(Client(), "TEST")
        self.assertEqual("2024-01-10", rows[0]["ex_date"])
        self.assertIsNone(rows[0]["primary_source_published_at"])
        self.assertEqual("FIRST_OBSERVED_AT_ONLY", rows[0]["available_at_evidence"])
        self.assertEqual("PARTIAL", check["status"])


if __name__ == "__main__":
    unittest.main()
