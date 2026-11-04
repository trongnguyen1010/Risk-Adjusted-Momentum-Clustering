import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.contracts import validate_rows
from delta_t1.ingestion.corporate_actions_v1 import (
    COVERAGE_FIELDS, FIELDS, build, coverage_report, csv_text, digest,
    number, read_csv, validate, validate_file,
)

FIXTURE = ROOT / "tests/fixtures/corporate_actions_v1/events.csv"


def event(kind="CASH_DIVIDEND", **changes):
    row = dict.fromkeys(FIELDS, "")
    row.update(event_id="SYNTHETIC-CASH-001", event_group_id="SYNTHETIC-GROUP-001",
               security_id="SYNTHETIC-SEC-001", ticker="TEST", exchange="HOSE",
               event_type=kind, announcement_date="2024-01-02",
               available_at="2024-01-02T09:00:00+07:00", ex_date="2024-01-10",
               record_date="2024-01-11", payment_date="2024-02-01", currency="VND",
               primary_source_type="VSDC", primary_source_url="https://vsdc.vn/synthetic-test-only",
               primary_source_published_at="2024-01-02T09:00:00+07:00",
               raw_terms="SYNTHETIC TEST ONLY; not actual corporate action evidence",
               verification_status="VERIFIED", created_at="2024-02-02T12:00:00+07:00",
               schema_version="1.0.0", revision_status="ORIGINAL", identity_status="VERIFIED",
               identity_source_url="https://vsdc.vn/synthetic-identity-test-only",
               available_at_evidence="Synthetic fixture exact timestamp",
               verified_by="UNIT_TEST_ONLY", verified_at="2024-02-02T12:00:00+07:00")
    row.update({"CASH_DIVIDEND": {"cash_dividend_per_share": "1500"},
                "STOCK_DIVIDEND": {"stock_dividend_ratio": "15%"},
                "BONUS_SHARE": {"bonus_ratio": "10:3", "ratio_semantics": "OLD:NEW"},
                "RIGHTS_ISSUE": {"rights_ratio": "7%", "rights_subscription_price": "10000"},
                "STOCK_SPLIT": {"split_multiplier": "2"},
                "REVERSE_SPLIT": {"split_multiplier": "0.5"},
                "OTHER": {"notes": "Synthetic unsupported terms"}}[kind])
    row.update(changes)
    return row


class CorporateActionsV1Tests(unittest.TestCase):
    def codes(self, rows):
        return {i["code"] for i in validate(rows)["issues"]}

    def test_all_six_types_valid_and_schema_compatible(self):
        for kind in ("CASH_DIVIDEND", "STOCK_DIVIDEND", "BONUS_SHARE", "RIGHTS_ISSUE",
                     "STOCK_SPLIT", "REVERSE_SPLIT"):
            with self.subTest(kind=kind):
                result = validate([event(kind)])
                self.assertEqual("PASS", result["status"], result["issues"])
                validate_rows("corporate_actions_v1", [result["records"][0]["normalized"]])

    def test_decimal_percent_colon_and_preserved_inputs(self):
        self.assertEqual(.6458, number("64.58%", "bonus_ratio", ""))
        self.assertEqual(.07, number("7%", "rights_ratio", ""))
        result = validate([event("BONUS_SHARE")])["records"][0]["normalized"]
        self.assertEqual(.3, result["bonus_ratio"])
        self.assertEqual("10:3", result["normalization_inputs"]["bonus_ratio"])
        self.assertIn("SYNTHETIC", result["raw_terms"])
        with self.assertRaises(ValueError):
            number("10:3", "bonus_ratio", "")
        raw = "  10:3 source quote\n  exact original whitespace  "
        self.assertEqual(raw, validate([event("BONUS_SHARE", raw_terms=raw)])["records"][0]["normalized"]["raw_terms"])

    def test_invalid_percentage_nonfinite_negative_and_decimal_comma(self):
        for value in ("15%%", "-1%", "NaN", "Infinity", "64,58%", "0", "1e9999"):
            with self.subTest(value=value):
                result = validate([event("BONUS_SHARE", bonus_ratio=value)])
                self.assertEqual({"INVALID": 1}, result["counts"])

    def test_abnormal_percentage_not_silently_repaired(self):
        row = event("BONUS_SHARE", bonus_ratio="6458%")
        result = validate([row])
        self.assertEqual(64.58, result["records"][0]["normalized"]["bonus_ratio"])
        self.assertEqual({"MANUAL_REVIEW": 1}, result["counts"])

    def test_missing_ex_date_and_availability_are_not_inferred(self):
        for field in ("ex_date", "available_at", "primary_source_url", "available_at_evidence"):
            with self.subTest(field=field):
                result = validate([event(**{field: ""})])
                self.assertEqual({"MANUAL_REVIEW": 1}, result["counts"])
                self.assertIsNone(result["records"][0]["normalized"][field])

    def test_missing_terms_not_zero_filled(self):
        result = validate([event("RIGHTS_ISSUE", rights_subscription_price="")])
        self.assertEqual({"MANUAL_REVIEW": 1}, result["counts"])
        self.assertIsNone(result["records"][0]["normalized"]["rights_subscription_price"])

    def test_duplicate_rows_and_changed_id_duplicate(self):
        self.assertIn("DUPLICATE_EVENT_ID", self.codes([event(), event()]))
        self.assertIn("DUPLICATE_EVENT_KEY", self.codes([event(), event(event_id="new")]))

    def test_cross_source_terms_conflict_blocks_both(self):
        result = validate([event(), event(event_id="new", cash_dividend_per_share="1700",
                                         primary_source_type="HOSE", primary_source_url="https://hsx.vn/test")])
        self.assertEqual({"MANUAL_REVIEW": 2}, result["counts"])
        self.assertIn("TERM_CONFLICT", {i["code"] for i in result["issues"]})

    def test_explicit_conflict_and_vendor_never_auto_promoted(self):
        self.assertIn("SOURCE_CONFLICT", self.codes([event(conflict_notes="A 6458%; B 64.58%")]))
        self.assertIn("AUTHORITATIVE_SOURCE_REQUIRED", self.codes([event(primary_source_type="VENDOR")]))
        self.assertIn("SOURCE_AUTHORITY_URL_MISMATCH", self.codes([event(primary_source_url="https://cafef.vn/test")]))

    def test_mixed_same_day_and_no_mixed_terms_in_one_row(self):
        rows = [event(), event("STOCK_DIVIDEND", event_id="SYNTHETIC-STOCK-001")]
        self.assertEqual("PASS", validate(rows)["status"])
        self.assertIn("UNRELATED_TERM_MIXED_ROW", self.codes([event(stock_dividend_ratio="15%")]))
        rows[1]["ex_date"] = ""
        self.assertTrue(all(r["normalized"]["verification_status"] != "VERIFIED"
                            for r in validate(rows)["records"]))

    def test_group_id_and_same_day_group_mismatch(self):
        self.assertIn("GROUP_IDENTITY_DATE_CONFLICT", self.codes([
            event(), event("STOCK_DIVIDEND", event_id="new", ticker="OTHER", security_id="other")]))
        self.assertIn("SAME_DAY_GROUP_MISMATCH", self.codes([
            event(), event("STOCK_DIVIDEND", event_id="new", event_group_id="different")]))

    def test_date_order_publication_and_timezone(self):
        for changes, expected in (({"record_date": "2024-01-09"}, "DATE_ORDER"),
                                  ({"available_at": "2024-01-01T09:00:00+07:00"}, "AVAILABLE_BEFORE_PUBLICATION"),
                                  ({"available_at": "2024-01-02T09:00:00"}, "SCHEMA_VALUE"),
                                  ({"created_at": "2024-01-01T09:00:00+07:00"}, "COLLECTION_BEFORE_AVAILABILITY")):
            self.assertIn(expected, self.codes([event(**changes)]))

    def test_late_knowledge_and_date_only_not_backdated(self):
        result = validate([event(available_at="2024-01-12T09:00:00+07:00")])
        self.assertEqual({"MANUAL_REVIEW": 1}, result["counts"])
        self.assertEqual("2024-01-12T09:00:00+07:00", result["records"][0]["normalized"]["available_at"])
        self.assertEqual("PASS", validate([event(primary_source_published_at="2024-01-02")])["status"])
        self.assertIn("SCHEMA_VALUE", self.codes([event(available_at="2024-01-02")]))

    def test_splits_direction_other_and_identity(self):
        self.assertIn("SPLIT_DIRECTION", self.codes([event("STOCK_SPLIT", split_multiplier=".5")]))
        self.assertIn("SPLIT_DIRECTION", self.codes([event("REVERSE_SPLIT", split_multiplier="2")]))
        self.assertIn("OTHER_REQUIRES_REVIEW", self.codes([event("OTHER")]))
        self.assertIn("HISTORICAL_IDENTITY_UNVERIFIED", self.codes([event(identity_status="UNVERIFIED")]))

    def test_revision_blocks_original_even_if_ex_date_changed(self):
        rows = [event(), event(event_id="correction", event_group_id="new-group", ex_date="2024-01-09",
                              revision_status="CORRECTION", revision_of_event_id="SYNTHETIC-CASH-001")]
        self.assertEqual({"MANUAL_REVIEW": 2}, validate(rows)["counts"])

    def test_fixture_valid_and_no_production_evidence(self):
        result = validate_file(FIXTURE)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(6, result["row_count"])
        self.assertTrue(all("SYNTHETIC" in r["normalized"]["raw_terms"] for r in result["records"]))

    def test_csv_schema_width_duplicate_header_and_examples_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.csv"
            for content in ("event_id,event_id\na,b\n", "event_id\na,b\n", csv_text(FIELDS + ("is_example",), [])):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    validate_file(path)

    def test_build_immutable_manifest_and_quarantine(self):
        with tempfile.TemporaryDirectory() as temp:
            path, out = Path(temp) / "input.csv", Path(temp) / "artifact"
            path.write_text(csv_text(FIELDS, [event(), event("OTHER", event_id="other", event_group_id="other",
                                                          ex_date="2024-01-09")]), encoding="utf-8")
            manifest = build(path, out)
            self.assertEqual(1, manifest["verified_event_count"])
            self.assertEqual(1, manifest["review_row_count"])
            self.assertEqual("PARTIAL", manifest["status"])
            self.assertEqual(path.read_bytes(), (out / "input.csv").read_bytes())
            for name, checksum in manifest["files"].items():
                self.assertEqual(checksum, digest(out / name))
            with self.assertRaises(ValueError):
                build(path, out)
            import shutil
            copy = shutil.copyfile
            def concurrent_edit(source, destination):
                source.write_bytes(source.read_bytes() + b"\n")
                return copy(source, destination)
            incomplete = Path(temp) / "incomplete"
            with patch("delta_t1.ingestion.corporate_actions_v1.shutil.copyfile", side_effect=concurrent_edit):
                with self.assertRaisesRegex(ValueError, "INPUT_CHANGED_DURING_BUILD"):
                    build(path, incomplete)
            self.assertFalse((incomplete / "manifest.json").exists())

    def coverage_setup(self, root, events=None):
        events_path, coverage_path, scope_path = root / "events.csv", root / "coverage.csv", root / "scope.csv"
        scope = [{"security_id": "SYNTHETIC-SEC-001", "ticker": "TEST", "exchange": "HOSE"}]
        scope_path.write_text(csv_text(("security_id", "ticker", "exchange"), scope), encoding="utf-8")
        events_path.write_text(csv_text(FIELDS, events or []), encoding="utf-8")
        row = dict.fromkeys(COVERAGE_FIELDS, "") | scope[0] | {
            "review_status": "REVIEWED", "reviewed_start_date": "2019-01-31",
            "reviewed_end_date": "2025-12-31", "reviewed_event_types": "ALL_V1",
            "primary_source_type": "VSDC", "primary_source_url": "https://vsdc.vn/synthetic-test-only",
            "coverage_evidence": "SYNTHETIC TEST ONLY full-window review log", "reviewer": "UNIT_TEST_ONLY",
            "last_checked_at": "2026-01-02T09:00:00+07:00"}
        coverage_path.write_text(csv_text(COVERAGE_FIELDS, [row]), encoding="utf-8")
        return events_path, coverage_path, scope_path, row

    def report(self, paths):
        return coverage_report(*paths[:3], "2019-01-31", "2025-12-31")

    def test_zero_events_needs_full_attestation(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.coverage_setup(Path(temp))
            self.assertEqual("NO_EVENT_CONFIRMED", self.report(paths)["rows"][0]["coverage_status"])
            self.assertTrue(self.report(paths)["coverage_pass"])
            paths[1].write_text(csv_text(COVERAGE_FIELDS, []), encoding="utf-8")
            report = self.report(paths)
            self.assertFalse(report["coverage_pass"])
            self.assertEqual("NOT_YET_REVIEWED", report["rows"][0]["coverage_status"])

    def test_coverage_requires_window_source_reviewer_all_types_and_time(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.coverage_setup(Path(temp))
            for field, value in (("reviewed_start_date", "2024-01-01"), ("reviewer", ""),
                                 ("primary_source_url", "https://cafef.vn/test"),
                                 ("last_checked_at", "2024-01-01T09:00:00+07:00"),
                                 ("coverage_evidence", ""), ("reviewed_event_types", "CASH_DIVIDEND")):
                paths[1].write_text(csv_text(COVERAGE_FIELDS, [paths[3] | {field: value}]), encoding="utf-8")
                self.assertEqual("MANUAL_REVIEW_REQUIRED", self.report(paths)["rows"][0]["coverage_status"])

    def test_verified_event_is_not_full_coverage_without_attestation(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.coverage_setup(Path(temp), [event()])
            self.assertEqual("HAS_VERIFIED_EVENTS", self.report(paths)["rows"][0]["coverage_status"])
            paths[1].write_text(csv_text(COVERAGE_FIELDS, []), encoding="utf-8")
            self.assertEqual("NOT_YET_REVIEWED", self.report(paths)["rows"][0]["coverage_status"])

    def test_missing_ex_date_conflict_and_invalid_block_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            for changes in ({"ex_date": ""}, {"cash_dividend_per_share": "bad"}, {"conflict_notes": "unresolved"}):
                paths = self.coverage_setup(Path(temp), [event(**changes)])
                report = self.report(paths)
                self.assertFalse(report["coverage_pass"])
                self.assertEqual(1, report["rows"][0]["event_count"])
                self.assertEqual("MANUAL_REVIEW_REQUIRED", report["rows"][0]["coverage_status"])

    def test_unscoped_identity_and_duplicate_coverage_block(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.coverage_setup(Path(temp), [event(ticker="UNSCOPED")])
            self.assertFalse(self.report(paths)["coverage_pass"])
            self.assertEqual([2], self.report(paths)["unscoped_event_rows"])
            paths[1].write_text(csv_text(COVERAGE_FIELDS, [paths[3], paths[3]]), encoding="utf-8")
            self.assertEqual("MANUAL_REVIEW_REQUIRED", self.report(paths)["rows"][0]["coverage_status"])

    def test_cli_help_init_validate_build_and_report(self):
        script = ROOT / "scripts/collect_corporate_actions_v1.py"
        def run(*args):
            result = subprocess.run([sys.executable, str(script), *map(str, args)], cwd=ROOT,
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            return result.stdout
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self.coverage_setup(root, [event()])
            run("--help")
            run("init-template", "--output", root / "template.csv", "--universe", paths[2],
                "--coverage-output", root / "queue.csv")
            self.assertEqual([], read_csv(root / "template.csv", FIELDS))
            self.assertEqual("NOT_YET_REVIEWED", read_csv(root / "queue.csv", COVERAGE_FIELDS)[0]["review_status"])
            run("validate", "--input", FIXTURE)
            run("build", "--input", FIXTURE, "--output", root / "artifact")
            run("report", "--input", paths[0], "--coverage", paths[1], "--universe", paths[2],
                "--output", root / "report.json")
            self.assertTrue(json.loads((root / "report.json").read_text(encoding="utf-8"))["coverage_pass"])


if __name__ == "__main__":
    unittest.main()
