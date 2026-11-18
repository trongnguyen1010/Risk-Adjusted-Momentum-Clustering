import tempfile
import unittest
from pathlib import Path

from delta_t1.ingestion.cafef_c8_verify import (
    derive_market_blockers,
    latest_blockers,
    sha256_file,
    verify_generated_manifest,
    write_json,
)


def audit(**changes):
    row = {
        "calendar_uncertain_253": "0", "missing_sessions_253": "0",
        "invalid_sessions_253": "0", "conflicting_sessions_253": "0",
        "boundary_sessions_253": "0",
    }
    row.update(changes)
    return row


class CafeFC8VerifyTests(unittest.TestCase):
    def test_latest_blockers_preserve_simultaneous_causes(self):
        row = audit(calendar_uncertain_253="3", invalid_sessions_253="2",
                    boundary_sessions_253="5")
        self.assertEqual([
            ("CALENDAR_UNCERTAIN", 3),
            ("INVALID_PROVIDER_ROW", 2),
            ("IDENTITY_OR_PROVIDER_BOUNDARY", 5),
        ], latest_blockers(row))

    def test_feature_complete_not_ready_is_exactly_history_gate(self):
        readiness = {
            "security_id": "SID", "feature_complete": "True",
            "latest253_complete": "True", "missing_required_features": "",
        }
        snapshot = {
            "na_reason": {"history": "minimum_3_calendar_years_of_observed_data",
                          "historical_identity": "provisional_observed_interval_only"},
            "lookback_observations": 253,
        }
        primary, blockers = derive_market_blockers(readiness, snapshot, audit())
        self.assertEqual("INSUFFICIENT_THREE_YEAR_HISTORY", primary)
        self.assertEqual(["INSUFFICIENT_THREE_YEAR_HISTORY"], blockers)

    def test_absent_snapshot_is_not_reinterpreted_as_provider_gap(self):
        readiness = {
            "security_id": "SID", "feature_complete": "False",
            "latest253_complete": "False", "missing_required_features": "mom_21",
        }
        primary, blockers = derive_market_blockers(
            readiness, None, audit(boundary_sessions_253="253")
        )
        self.assertEqual("NO_FEATURE_SNAPSHOT_AT_COMPARISON_DATE", primary)
        self.assertIn("IDENTITY_OR_PROVIDER_BOUNDARY", blockers)
        self.assertNotIn("MISSING_ON_TRADEHISTORYNEW", blockers)

    def test_compact_artifact_manifest_hashes_every_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            evidence = output / "evidence.csv"
            evidence.write_text("key,value\ncount,1\n", encoding="utf-8")
            write_json(output / "manifest.json", {
                "outputs": {"evidence.csv": sha256_file(evidence)},
            })
            self.assertEqual(1, verify_generated_manifest(output))
            evidence.write_text("key,value\ncount,2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "output hash mismatch"):
                verify_generated_manifest(output)


if __name__ == "__main__":
    unittest.main()
