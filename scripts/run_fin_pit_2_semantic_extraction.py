"""Run or verify FIN-PIT-2 offline semantic extraction."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from delta_t1.ingestion.financial_pit_semantic import dry_run, execute, verify_existing

DEFAULT_INPUT = ROOT / "artifacts/financial_pit/fin-pit-1-source-document-pilot-v1"
DEFAULT_OUTPUT = ROOT / "artifacts/financial_pit/fin-pit-2-semantic-extraction-v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FIN-PIT-2 offline semantic extraction")
    parser.add_argument("--input-artifact", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true", help="validate immutable input; write nothing")
    modes.add_argument("--execute", action="store_true", help="extract candidates offline")
    modes.add_argument("--resume", action="store_true", help="verify completed output or execute if absent")
    modes.add_argument("--verify-existing", action="store_true", help="offline checksum/contract verification")
    args = parser.parse_args(argv)
    input_dir = args.input_artifact.resolve()
    output_dir = args.output.resolve()
    if args.dry_run:
        result = dry_run(input_dir, output_dir)
    elif args.verify_existing:
        result = verify_existing(input_dir, output_dir)
    elif args.resume and (output_dir / "manifest.json").is_file():
        result = verify_existing(input_dir, output_dir)
    else:
        result = execute(input_dir, output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {"PASS", "PARTIAL", "BLOCKED", "DRY_RUN_PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
