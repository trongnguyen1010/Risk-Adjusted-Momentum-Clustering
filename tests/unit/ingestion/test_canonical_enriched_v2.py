"""Unit tests for Canonical Enriched Dataset v2 Builder."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.canonical_enriched_v2 import build_canonical_enriched_v2
from delta_t1.io import write_json, write_rows


class CanonicalEnrichedV2Tests(unittest.TestCase):
    def test_build_canonical_enriched_v2(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)

            # 1. Setup Canonical Baseline
            can_dir = root / "data" / "canonical" / "canonical-baseline-mock"
            clean_dir = can_dir / "clean"
            clean_dir.mkdir(parents=True)
            write_json(can_dir / "manifest.json", {"run_id": can_dir.name, "canonical_id": can_dir.name, "status": "PASS"})
            write_rows(clean_dir / "benchmark_daily.jsonl", [{"trade_date": "2020-01-02", "close": 1000.0}])
            write_rows(clean_dir / "trading_calendar.jsonl", [{"trade_date": "2020-01-02", "exchange": "HOSE", "is_open": True}])
            write_rows(clean_dir / "securities.jsonl", [{
                "security_id": "KBS:HOSE:LPB", "ticker": "LPB", "company_name": "LPBank",
                "exchange": "HOSE", "listing_date": "2017-10-05", "delisting_date": None,
                "valid_from": "2020-01-02", "valid_to": None, "available_at": "2020-01-02T17:00:00+07:00",
                "sector": None, "industry": None, "currency": "VND", "price_unit": "VND",
                "identity_status": "provisional", "source": "kbs_master",
                "fetched_at": "2026-09-17T07:38:37Z", "data_version": can_dir.name
            }])
            write_rows(clean_dir / "prices_daily.jsonl", [
                {"security_id": "KBS:HOSE:LPB", "trade_date": "2020-01-02", "exchange": "HOSE", "adj_close": 10000.0, "volume": 100, "source": "kbs_provisional"}
            ])

            # 2. Setup A6 artifact
            base_enrich = root / "artifacts" / "data_enrichment"
            a6_dir = base_enrich / "m1-a6-identity-recovery-mock"
            a6_dir.mkdir(parents=True)
            write_json(a6_dir / "manifest.json", {"run_id": a6_dir.name, "status": "PASS"})

            # 3. Setup Transition Recovery artifact
            trans_dir = base_enrich / "m1-transition-recovery-mock"
            trans_dir.mkdir(parents=True)
            write_json(trans_dir / "manifest.json", {
                "run_id": trans_dir.name,
                "status": "PASS",
                "a6_artifact_id": a6_dir.name,
                "candidates_count": 1,
            })
            write_rows(trans_dir / "recovered_transition_rows.jsonl", [
                {"security_id": "KBS:HOSE:LPB", "trade_date": "2020-01-02", "exchange": "UPCOM", "adj_close": 10000.0, "volume": 100, "source": "kbs_delta_public_http", "fetched_at": "2026-09-21T14:00:00Z"}
            ])

            out_dir, manifest = build_canonical_enriched_v2(
                can_dir,
                a6_dir,
                trans_dir,
                root=root,
            )

            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["baseline_security_count"], 1)
            self.assertEqual(manifest["identity_recovered_count"], 1)
            self.assertEqual(manifest["identity_updated_rows"], 1)

            # Verify updated exchange in clean/prices_daily.jsonl
            updated_prices = [json.loads(line) for line in (out_dir / "clean" / "prices_daily.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(updated_prices), 1)
            self.assertEqual(updated_prices[0]["exchange"], "UPCOM")
            self.assertEqual(updated_prices[0]["source"], "kbs_delta_public_http")


if __name__ == "__main__":
    unittest.main()
