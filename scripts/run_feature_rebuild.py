"""CLI runner to execute Feature Rebuild on Canonical Enriched Dataset v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.features.rebuild import rebuild_features_v2

DEFAULT_BASELINE = "data/canonical/canonical-m1-scale-20260921T045028Z-19da7c61"
DEFAULT_FEATURE_CONFIG = "configs/features/market.example.json"


def _find_latest_canonical_v2(base_dir: Path) -> Path:
    candidates = sorted(base_dir.glob("canonical-m1-scale-enriched-v2-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        manifest_file = c / "manifest.json"
        if manifest_file.is_file():
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if data.get("status") == "PASS":
                return c
    raise FileNotFoundError(f"No PASS canonical-m1-scale-enriched-v2-* found in {base_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", help="Canonical Enriched v2 directory (defaults to latest PASS)")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, help="Baseline canonical directory")
    parser.add_argument("--feature-config", default=DEFAULT_FEATURE_CONFIG, help="Path to feature config")
    parser.add_argument("--execute", action="store_true", help="Required acknowledgement flag to execute Feature Rebuild")

    args = parser.parse_args(argv)
    if not args.execute:
        print("STOPPED: Add --execute flag to acknowledge executing Feature Rebuild.", file=sys.stderr)
        return 2

    can_base = ROOT / "data" / "canonical"
    canonical_dir = Path(args.canonical) if args.canonical else _find_latest_canonical_v2(can_base)
    if not canonical_dir.is_absolute():
        canonical_dir = ROOT / canonical_dir

    baseline_dir = Path(args.baseline) if Path(args.baseline).is_absolute() else ROOT / args.baseline
    feature_cfg_path = Path(args.feature_config) if Path(args.feature_config).is_absolute() else ROOT / args.feature_config

    print(f"Canonical Enriched v2: {canonical_dir.name}")
    print(f"Canonical Baseline:    {baseline_dir.name}")
    print(f"Feature Config:        {feature_cfg_path.name}")

    try:
        features_dir, result = rebuild_features_v2(
            canonical_dir,
            baseline_dir,
            feature_cfg_path,
            root=ROOT,
            progress=print,
        )
        comp = result["comparison"]
        attr = result["attribution"]
        print("\n" + "="*60)
        print("SUCCESS: Feature Rebuild Completed Successfully!")
        print(f"Snapshot Date:               {comp['snapshot_date']}")
        print(f"Market-Feature-Ready (v2):   {comp['market_feature_ready']['enriched_v2']} (Baseline: {comp['market_feature_ready']['baseline']})")
        print(f"Historical Identity Ready:   {comp['historical_identity_ready']['enriched_v2']} (Baseline: {comp['historical_identity_ready']['baseline']})")
        print(f"Readiness Gain Attribution:  {attr['gain_from_identity_recovery']} gained from identity recovery")
        print(f"Features Output Directory:   {features_dir}")
        print("="*60)
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
