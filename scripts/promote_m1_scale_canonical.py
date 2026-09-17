"""Promote one verified M1 scale candidate and build central market features."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.m1_scale import promote_scale_candidate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--securities", required=True)
    parser.add_argument("--feature-config", required=True)
    args = parser.parse_args(argv)
    try:
        output, manifest = promote_scale_candidate(
            args.candidate, args.config, args.securities, args.feature_config,
            root=ROOT)
        print(f"M1_SCALE={manifest['canonical_promotion_status']} network_requests=0")
        print(output / "manifest.json")
        return 0 if manifest["canonical_promotion_status"] == "PASS" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
