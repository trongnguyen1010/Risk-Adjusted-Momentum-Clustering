"""Unit tests for Feature Rebuild."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.features.rebuild import rebuild_features_v2
from delta_t1.io import write_json, write_rows


class FeatureRebuildTests(unittest.TestCase):
    def test_rebuild_features_v2(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)

            # Baseline canonical
            base_dir = root / "data" / "canonical" / "canonical-baseline-mock"
            base_clean = base_dir / "clean"
            base_features = base_dir / "features"
            base_clean.mkdir(parents=True)
            base_features.mkdir(parents=True)
            write_json(base_dir / "manifest.json", {"run_id": base_dir.name, "status": "PASS"})
            write_rows(base_clean / "benchmark_daily.jsonl", [
                {"trade_date": "2020-01-31", "close": 1000.0, "index_id": "VNINDEX", "available_at": "2020-01-31T17:00:00+07:00"}
            ])
            write_rows(base_clean / "trading_calendar.jsonl", [
                {"trade_date": "2020-01-31", "exchange": "HOSE", "is_open": True, "is_month_end": True, "decision_at": "2020-01-31T17:00:00+07:00"}
            ])
            write_rows(base_clean / "securities.jsonl", [{
                "security_id": "KBS:HOSE:LPB", "ticker": "LPB", "company_name": "LPBank",
                "exchange": "HOSE", "listing_date": "2017-10-05", "delisting_date": None,
                "valid_from": "2020-01-02", "valid_to": None, "available_at": "2020-01-02T17:00:00+07:00",
                "sector": None, "industry": None, "currency": "VND", "price_unit": "VND",
                "identity_status": "provisional", "source": "kbs_master",
                "fetched_at": "2026-09-17T07:38:37Z", "data_version": base_dir.name
            }])
            write_rows(base_clean / "prices_daily.jsonl", [
                {"security_id": "KBS:HOSE:LPB", "trade_date": "2020-01-31", "exchange": "HOSE", "adj_close": 10000.0, "raw_close": 10000.0, "volume": 100, "traded_value": 1000000.0, "adjustment_basis": "split_adjusted", "trading_status": "normal", "available_at": "2020-01-31T17:00:00+07:00", "source": "kbs", "data_version": base_dir.name}
            ])
            write_rows(base_features / "monthly.jsonl", [])

            # Enriched canonical v2
            v2_dir = root / "data" / "canonical" / "canonical-enriched-v2-mock"
            v2_clean = v2_dir / "clean"
            v2_clean.mkdir(parents=True)
            write_json(v2_dir / "manifest.json", {"canonical_id": v2_dir.name, "artifacts": {}, "status": "PASS"})
            write_rows(v2_clean / "benchmark_daily.jsonl", [
                {"trade_date": "2020-01-31", "close": 1000.0, "index_id": "VNINDEX", "available_at": "2020-01-31T17:00:00+07:00"}
            ])
            write_rows(v2_clean / "trading_calendar.jsonl", [
                {"trade_date": "2020-01-31", "exchange": "UPCOM", "is_open": True, "is_month_end": True, "decision_at": "2020-01-31T17:00:00+07:00"}
            ])
            write_rows(v2_clean / "securities.jsonl", [{
                "security_id": "KBS:HOSE:LPB", "ticker": "LPB", "company_name": "LPBank",
                "exchange": "UPCOM", "listing_date": "2017-10-05", "delisting_date": None,
                "valid_from": "2020-01-02", "valid_to": None, "available_at": "2020-01-02T17:00:00+07:00",
                "sector": None, "industry": None, "currency": "VND", "price_unit": "VND",
                "identity_status": "verified", "source": "verified_a6_identity",
                "fetched_at": "2026-09-17T07:38:37Z", "data_version": v2_dir.name
            }])
            write_rows(v2_clean / "prices_daily.jsonl", [
                {"security_id": "KBS:HOSE:LPB", "trade_date": "2020-01-31", "exchange": "UPCOM", "adj_close": 10000.0, "raw_close": 10000.0, "volume": 100, "traded_value": 1000000.0, "adjustment_basis": "split_adjusted", "trading_status": "normal", "available_at": "2020-01-31T17:00:00+07:00", "source": "kbs_recovered", "data_version": v2_dir.name}
            ])

            cfg_path = root / "market.json"
            write_json(cfg_path, {
                "feature_set": "delta_market_1.5.0",
                "benchmark_id": "VNINDEX",
                "minimum_history_years": 0,
                "accepted_adjustments": ["unadjusted", "split_adjusted", "vendor_adjusted"],
                "required_features": ["mom_21", "mom_63", "mom_126", "mom_252", "vol_63", "mdd_126", "beta_126", "liquidity_21"]
            })

            features_dir, result = rebuild_features_v2(
                v2_dir,
                base_dir,
                cfg_path,
                root=root,
            )

            self.assertEqual(result["status"], "PASS")
            self.assertTrue((features_dir / "monthly.jsonl").is_file())
            self.assertTrue((features_dir / "readiness_comparison.json").is_file())
            self.assertTrue((features_dir / "readiness_attribution.json").is_file())


if __name__ == "__main__":
    unittest.main()
