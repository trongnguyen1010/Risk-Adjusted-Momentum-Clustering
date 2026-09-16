"""Map the frozen representative pilot to standard market-table candidates offline."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.representative_pilot_canonical import map_canonical_candidates


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--gate-report", required=True)
    parser.add_argument("--qc-policy", required=True)
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    try:
        output, manifest = map_canonical_candidates(
            args.config, args.gate_report, args.qc_policy, args.assessment,
            args.run_id, root=ROOT)
        print(f"MAPPING={manifest['mapping_status']} "
              f"CANONICAL_PROMOTION={manifest['canonical_promotion_status']} "
              "network_requests=0")
        print(f"prices_daily={manifest['counts']['prices_daily']} "
              f"benchmark_daily={manifest['counts']['benchmark_daily']}")
        print(output / "manifest.json")
        return 0 if manifest["mapping_status"] == "PASS" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
