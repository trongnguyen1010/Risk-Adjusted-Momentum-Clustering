"""Offline methodology-protection tests for Stage A3 primary recovery."""
from __future__ import annotations

import csv
from datetime import date, timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest

from delta_t1.ingestion.primary_recovery import (
    build_stage_a3,
    execute_request_plan,
    group_missing_ranges,
    select_pilot,
)
from delta_t1.io import atomic_write, digest, encoded, write_json, write_rows


class FakeKBS:
    def __init__(self, *, empty=False, invalid=False, malformed=False,
                 invalid_envelope=False):
        self.calls = []
        self.empty = empty
        self.invalid = invalid
        self.malformed = malformed
        self.invalid_envelope = invalid_envelope

    def acquire_ohlcv(self, symbol, start, end, *, is_index=False):
        self.calls.append((symbol, start, end, is_index))
        if self.invalid_envelope:
            return {"url": f"https://example.invalid/{symbol}", "status": 200,
                    "body": b"<html>provider error</html>", "payload": {}}
        rows = [] if self.empty else [{
            "t": f"{start} 07:00", "o": 1000.0, "h": 1010.0,
            "l": 990.0, "c": 1005.0, "v": -1 if self.invalid else 100,
        }]
        if self.malformed:
            rows[0].pop("o")
        payload = {"symbol": symbol, "data_day": rows}
        return {"url": f"https://example.invalid/{symbol}", "status": 200,
                "body": encoded(payload), "payload": payload}


def _csv(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


class PrimaryRecoveryTests(unittest.TestCase):
    def test_missing_ranges_are_short_bounded_and_recent(self):
        values = ["2025-03-10", "2025-03-11", "2025-04-02",
                  "2025-05-01", "2025-05-02", "2025-06-20"]
        ranges = group_missing_ranges(
            values, max_dates_per_range=2, max_calendar_span_days=5, max_ranges=2)
        self.assertEqual([
            {"start": "2025-05-01", "end": "2025-05-02",
             "targeted_dates": ["2025-05-01", "2025-05-02"]},
            {"start": "2025-06-20", "end": "2025-06-20",
             "targeted_dates": ["2025-06-20"]},
        ], ranges)

    def test_selection_does_not_invent_unavailable_priority_strata(self):
        rows = []
        exchanges = ("HOSE", "HNX", "UPCOM")
        for index in range(12):
            rows.append({
                "security_id": f"S{index:02d}", "ticker": f"T{index:02d}",
                "exchange": exchanges[index % 3], "missing_sessions_total": index + 1,
                "missing_last_252": index % 4, "coverage_ratio": 0.5 + index / 100,
                "market_feature_ready": False, "recovery_priority": "P4",
            })
        selected, contract = select_pilot(
            rows, sample_size=10, high_priority_symbols=["T01"])
        self.assertEqual(10, len(selected))
        self.assertEqual(["P0", "P1", "P2"], contract["required_priorities_unavailable"])
        self.assertEqual([], contract["priorities_included"])
        self.assertEqual(["T01"], contract["high_priority_included"])
        self.assertEqual({"HOSE", "HNX", "UPCOM"},
                         {row["exchange"] for row in selected})
        self.assertEqual(2, len(contract["sparse_controls"]))

    def test_empty_provider_response_stays_unresolved_without_fill(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "artifact"
            output.mkdir()
            request = {
                "request_id": "kbs-AAA-01-2025-01-02-2025-01-02",
                "security_id": "S:AAA", "ticker": "AAA", "exchange": "HOSE",
                "start": "2025-01-02", "end": "2025-01-02",
                "targeted_dates": ["2025-01-02"],
            }
            candidates, results, statuses = execute_request_plan(
                [request], provider=FakeKBS(empty=True), output=output, root=root,
                decision_by_key={("HOSE", "2025-01-02"): "2025-01-02T17:00:00+07:00"})
            self.assertEqual([], candidates)
            self.assertEqual("UNRESOLVED", results[0]["status"])
            self.assertEqual("PRIMARY_PROVIDER_RETURNED_NO_TARGET_ROW", results[0]["reason"])
            self.assertEqual("SUCCESS", statuses[0]["status"])
            self.assertNotIn("0", results[0].values())

    def test_invalid_primary_row_is_rejected_not_repaired(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "artifact"
            output.mkdir()
            request = {
                "request_id": "kbs-AAA-01-2025-01-02-2025-01-02",
                "security_id": "S:AAA", "ticker": "AAA", "exchange": "HOSE",
                "start": "2025-01-02", "end": "2025-01-02",
                "targeted_dates": ["2025-01-02"],
            }
            candidates, results, _ = execute_request_plan(
                [request], provider=FakeKBS(invalid=True), output=output, root=root,
                decision_by_key={("HOSE", "2025-01-02"): "2025-01-02T17:00:00+07:00"})
            self.assertEqual("REJECT", candidates[0]["decision"])
            self.assertIn("INVALID_REQUIRED_MARKET_ROW", candidates[0]["rejection_reason"])
            self.assertEqual("REJECT", results[0]["status"])
            self.assertNotEqual("0", candidates[0]["normalized_row_json"])

    def test_malformed_target_row_is_preserved_as_rejected_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "artifact"
            output.mkdir()
            request = {
                "request_id": "kbs-AAA-01-2025-01-02-2025-01-02",
                "security_id": "S:AAA", "ticker": "AAA", "exchange": "HOSE",
                "start": "2025-01-02", "end": "2025-01-02",
                "targeted_dates": ["2025-01-02"],
            }
            candidates, results, _ = execute_request_plan(
                [request], provider=FakeKBS(malformed=True), output=output, root=root,
                decision_by_key={("HOSE", "2025-01-02"): "2025-01-02T17:00:00+07:00"})
            self.assertEqual(1, len(candidates))
            self.assertEqual("REJECT", candidates[0]["decision"])
            self.assertIn("ROW_MAPPING_OR_DATE_INVALID", candidates[0]["rejection_reason"])
            self.assertEqual("REJECT", results[0]["status"])
            self.assertEqual(candidates[0]["candidate_id"], results[0]["candidate_id"])

    def test_invalid_envelope_bytes_and_failure_metadata_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "artifact"
            output.mkdir()
            request = {
                "request_id": "kbs-AAA-01-2025-01-02-2025-01-02",
                "security_id": "S:AAA", "ticker": "AAA", "exchange": "HOSE",
                "start": "2025-01-02", "end": "2025-01-02",
                "targeted_dates": ["2025-01-02"],
            }
            candidates, results, statuses = execute_request_plan(
                [request], provider=FakeKBS(invalid_envelope=True), output=output, root=root,
                decision_by_key={("HOSE", "2025-01-02"): "2025-01-02T17:00:00+07:00"})
            self.assertEqual([], candidates)
            self.assertEqual("UNRESOLVED", results[0]["status"])
            self.assertTrue(results[0]["raw_path"])
            self.assertEqual("FAILED", statuses[0]["status"])
            raw_dir = output / "primary_recovery_raw"
            self.assertEqual(b"<html>provider error</html>",
                             (raw_dir / f"{request['request_id']}.json").read_bytes())
            metadata_path = raw_dir / f"{request['request_id']}.metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual("REJECTED_ENVELOPE", metadata["validation_status"])
            self.assertIn("raw body is not valid JSON", metadata["validation_error"])

    def _fixture(self, root):
        canonical = root / "data" / "canonical" / "canonical-fixture"
        clean, features = canonical / "clean", canonical / "features"
        clean.mkdir(parents=True)
        features.mkdir()
        exchanges = ("HOSE", "HNX", "UPCOM")
        start = date(2025, 1, 1)
        days = [(start + timedelta(days=index)).isoformat() for index in range(30)]
        securities, prices, feature_rows = [], [], []
        missing_by_ticker = {}
        for index in range(10):
            ticker, exchange = f"T{index:02d}", exchanges[index % 3]
            security_id = f"KBS:{exchange}:{ticker}"
            missing = days[10 + index]
            missing_by_ticker[ticker] = missing
            securities.append({
                "security_id": security_id, "ticker": ticker, "exchange": exchange,
                "valid_from": days[0], "valid_to": None, "listing_date": None,
                "delisting_date": None, "identity_status": "provisional",
            })
            prices.extend({"security_id": security_id, "trade_date": day,
                           "source": "kbs_delta_public_http",
                           "adjustment_basis": "vendor_adjusted"}
                          for day in days if day != missing)
            feature_rows.append({
                "security_id": security_id, "as_of_date": days[-1],
                "mom_21": None, "mom_63": None, "mom_126": None, "mom_252": None,
                "market_feature_ready": False,
            })
        calendar = [{
            "exchange": exchange, "trade_date": day, "is_open": True,
            "is_month_end": day == days[-1],
            "decision_at": f"{day}T17:00:00+07:00",
            "source": "kbs_observed_session_union",
        } for exchange in exchanges for day in days]
        files = {
            "clean/securities.jsonl": securities,
            "clean/prices_daily.jsonl": prices,
            "clean/trading_calendar.jsonl": calendar,
            "features/monthly.jsonl": feature_rows,
        }
        for relative, rows in files.items():
            write_rows(canonical / relative, rows)
        artifacts = {relative: digest((canonical / relative).read_bytes()) for relative in files}
        write_json(canonical / "manifest.json", {
            "run_id": canonical.name, "canonical_promotion_status": "PASS",
            "synthetic": False, "collection_end": "2025-02-15", "artifacts": artifacts,
        })

        a1 = root / "artifacts" / "data_enrichment" / "a1-fixture"
        a1.mkdir(parents=True)
        priority_rows = [{"security_id": row["security_id"], "recovery_priority": "P4",
                          "priority_reason": "fixture_provisional"} for row in securities]
        priority_path = a1 / "recovery_priority.csv"
        atomic_write(priority_path, _csv(priority_rows,
                                          ["security_id", "recovery_priority", "priority_reason"]))
        atomic_write(a1 / "stage_a1_report.md", b"fixture\n")
        a1_artifacts = {path.name: digest(path.read_bytes()) for path in a1.iterdir()}
        write_json(a1 / "manifest.json", {
            "run_id": a1.name, "status": "PASS", "canonical_run_id": canonical.name,
            "artifacts": a1_artifacts,
        })

        a2 = root / "artifacts" / "data_enrichment" / "a2-fixture"
        a2.mkdir(parents=True)
        atomic_write(a2 / "stage_a2_report.md", b"fixture\n")
        write_json(a2 / "manifest.json", {
            "run_id": a2.name, "status": "PASS", "canonical_run_id": canonical.name,
            "a1_run_id": a1.name, "metrics": {"accepted_rows": 0},
            "artifacts": {"stage_a2_report.md": digest((a2 / "stage_a2_report.md").read_bytes())},
        })
        return canonical, a1, a2, missing_by_ticker

    def test_end_to_end_writes_immutable_artifact_with_mock_provider(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical, a1, a2, missing = self._fixture(root)
            before = digest((canonical / "clean" / "prices_daily.jsonl").read_bytes())
            provider = FakeKBS()
            output, manifest = build_stage_a3(
                canonical, a1, a2, root=root, provider=provider, sample_size=10,
                high_priority_symbols=["T00"], max_ranges_per_symbol=1)
            self.assertEqual(10, len(provider.calls))
            self.assertEqual(10, manifest["metrics"]["rows_recovered"])
            self.assertEqual(0, manifest["canonical_mutations"])
            self.assertEqual("PARTIAL", manifest["status"])
            self.assertEqual(before, digest((canonical / "clean" / "prices_daily.jsonl").read_bytes()))
            required = {
                "primary_recovery_requests.jsonl", "primary_recovery_raw",
                "primary_recovery_candidates.parquet", "primary_recovery_results.csv",
                "manifest.json", "stage_a3_report.md",
            }
            self.assertTrue(required <= {path.name for path in output.iterdir()})
            parquet = (output / "primary_recovery_candidates.parquet").read_bytes()
            self.assertEqual(b"PAR1", parquet[:4])
            self.assertEqual(b"PAR1", parquet[-4:])
            with (output / "primary_recovery_results.csv").open(encoding="utf-8") as stream:
                results = list(csv.DictReader(stream))
            self.assertEqual(set(missing), {row["ticker"] for row in results})
            self.assertTrue(all(row["status"] == "RECOVERED" for row in results))


if __name__ == "__main__":
    unittest.main()
