"""Unit tests for Stage A6.1 historical identity price recovery."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import unittest

from delta_t1.ingestion.transition_recovery import (
    plan_transition_requests,
    build_transition_recovery,
)
from delta_t1.io import write_json


class MockKBSProvider:
    def __init__(self):
        self.call_count = 0

    def acquire_ohlcv(self, symbol, start, end, is_index=False):
        self.call_count += 1
        return {
            "status": 200,
            "url": f"https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day",
            "fetched_at": "2026-09-21T12:00:00+00:00",
            "payload": {
                "symbol": symbol,
                "data_day": [
                    {
                        "t": "2020-01-02",
                        "o": 10.0,
                        "h": 10.5,
                        "l": 9.8,
                        "c": 10.2,
                        "v": 50000,
                    },
                    {
                        "t": "2020-01-03",
                        "o": 10.2,
                        "h": 10.8,
                        "l": 10.1,
                        "c": 10.6,
                        "v": 60000,
                    }
                ]
            }
        }


class TransitionRecoveryTests(unittest.TestCase):
    def test_plan_transition_requests(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "identity_recovery_candidates.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "candidate_id", "security_id", "from_ticker", "from_exchange",
                    "to_ticker", "to_exchange", "effective_date", "decision"
                ])
                writer.writeheader()
                writer.writerow({
                    "candidate_id": "EV-LPB-001",
                    "security_id": "KBS:HOSE:LPB",
                    "from_ticker": "LPB",
                    "from_exchange": "UPCOM",
                    "to_ticker": "LPB",
                    "to_exchange": "HOSE",
                    "effective_date": "2020-11-09",
                    "decision": "VERIFIED",
                })
                # Rejected row should be skipped
                writer.writerow({
                    "candidate_id": "EV-BAD-001",
                    "security_id": "KBS:HOSE:BAD",
                    "from_ticker": "BAD",
                    "from_exchange": "UPCOM",
                    "to_ticker": "BAD",
                    "to_exchange": "HOSE",
                    "effective_date": "2020-05-01",
                    "decision": "REJECTED",
                })

            plan = plan_transition_requests(csv_path, collection_start="2020-01-01", batch_days=180)
            self.assertTrue(len(plan) >= 1)
            first = plan[0]
            self.assertEqual(first["ticker"], "LPB")
            self.assertEqual(first["from_exchange"], "UPCOM")
            self.assertEqual(first["start"], "2020-01-01")

    def test_build_transition_recovery_with_mock(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            base = root / "artifacts" / "data_enrichment"
            a6_dir = base / "m1-a6-identity-recovery-mock"
            a6_dir.mkdir(parents=True)

            write_json(a6_dir / "manifest.json", {"run_id": a6_dir.name, "status": "PASS"})
            csv_path = a6_dir / "identity_recovery_candidates.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "candidate_id", "security_id", "from_ticker", "from_exchange",
                    "to_ticker", "to_exchange", "effective_date", "decision"
                ])
                writer.writeheader()
                writer.writerow({
                    "candidate_id": "EV-LPB-001",
                    "security_id": "KBS:HOSE:LPB",
                    "from_ticker": "LPB",
                    "from_exchange": "UPCOM",
                    "to_ticker": "LPB",
                    "to_exchange": "HOSE",
                    "effective_date": "2020-11-09",
                    "decision": "VERIFIED",
                })

            mock_provider = MockKBSProvider()
            out_dir, manifest = build_transition_recovery(
                a6_dir,
                root=root,
                provider=mock_provider,
                collection_start="2020-01-01",
                batch_days=180,
            )

            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["canonical_mutations"], 0)
            self.assertTrue((out_dir / "recovered_transition_rows.jsonl").is_file())
            self.assertTrue((out_dir / "transition_recovery_summary.csv").is_file())
            self.assertTrue((out_dir / "stage_report.md").is_file())
            self.assertTrue((out_dir / "manifest.json").is_file())
            self.assertTrue(mock_provider.call_count > 0)


if __name__ == "__main__":
    unittest.main()
