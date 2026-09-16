"""Plan or execute the official smoke-gated REPRESENTATIVE_PILOT acquisition path."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.representative_pilot import dry_run, run_real


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--gate-report", required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="validate and write a plan with exactly zero network requests")
    parser.add_argument("--resume", help="resume an existing immutable real pilot run ID")
    args = parser.parse_args(argv)
    if args.dry_run and args.resume:
        parser.error("--resume is only valid for an explicitly started real execution")
    try:
        if args.dry_run:
            directory, manifest = dry_run(args.config, args.gate_report, root=ROOT)
            print(f"READINESS={manifest['readiness']} network_requests=0")
            print(directory / "manifest.json")
            return 0
        directory, manifest, gate = run_real(
            args.config, args.gate_report, root=ROOT, resume=args.resume)
        print(f"{gate['gate']}={gate['status']} unlocks={','.join(gate['unlocks']) or 'NONE'}")
        print(directory / "manifest.json")
        return 0 if gate["status"] == "PASS" else 2
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
