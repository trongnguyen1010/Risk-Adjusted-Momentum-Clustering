"""Promote a hash-verified representative-pilot mapping to pilot canonical tables."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.representative_pilot_canonical import (
    promote_canonical_candidate,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--securities", required=True)
    parser.add_argument("--feature-config", required=True)
    args = parser.parse_args(argv)
    try:
        output, manifest = promote_canonical_candidate(
            args.candidate, args.universe, args.securities,
            args.feature_config, root=ROOT)
        counts = manifest["counts"]
        print(f"PROMOTION={manifest['canonical_promotion_status']} "
              f"FEATURE_STAGE_READY={manifest['feature_stage_ready']} network_requests=0")
        print(f"securities={counts['securities']} prices_daily={counts['prices_daily']} "
              f"features={counts['feature_snapshots']} "
              f"latest_eligible={counts['latest_feature_eligible']}")
        print(output / "manifest.json")
        return 0
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
