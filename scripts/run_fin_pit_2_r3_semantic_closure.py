"""Run or verify FIN-PIT-2-R3 semantic/quarantine closure."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from delta_t1.ingestion.financial_pit_semantic_closure import dry_run, execute, preflight, verify_existing

DEFAULT_R2 = ROOT / "artifacts/financial_pit/fin-pit-2-r2-period-scope-remediation-v2"
DEFAULT_OPEN11 = ROOT / "artifacts/financial_pit/open-11-scope-mapping-review-v1"
DEFAULT_R1 = Path(r"C:\Users\HP\.codex\worktrees\fin-pit-1\Phân cụm động lượng TTCK\artifacts\financial_pit\fin-pit-1-source-document-pilot-v1")
DEFAULT_OUTPUT = ROOT / "artifacts/financial_pit/fin-pit-2-r3-semantic-closure-v1"
DEFAULT_TESSDATA = ROOT / "tools/tessdata"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FIN-PIT-2-R3 offline semantic closure")
    parser.add_argument("--r2", type=Path, default=DEFAULT_R2)
    parser.add_argument("--open11", type=Path, default=DEFAULT_OPEN11)
    parser.add_argument("--fin-pit-1", type=Path, default=DEFAULT_R1)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tessdata-dir", type=Path, default=DEFAULT_TESSDATA)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--resume", action="store_true")
    modes.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    values = (args.r2.resolve(), args.open11.resolve(), args.fin_pit_1.resolve())
    if args.preflight:
        result = preflight(*values, tessdata_dir=args.tessdata_dir.resolve())
    elif args.dry_run:
        result = dry_run(*values, tessdata_dir=args.tessdata_dir.resolve())
    elif args.verify_existing or (args.resume and (args.output / "manifest.json").is_file()):
        result = verify_existing(*values, args.output.resolve())
    else:
        result = execute(*values, args.output.resolve(), tessdata_dir=args.tessdata_dir.resolve())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=dict))
    return 0 if result.get("status") in {"PASS", "PREFLIGHT_PASS", "DRY_RUN_PASS", "VERIFIED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
