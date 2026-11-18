"""Generate or verify the compact offline M2-PREP methodology audit."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.experiments.m2_prep import DEFAULT_OUTPUT, generate, verify_existing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: {ROOT}")
    if args.verify_existing:
        verify_existing(ROOT, args.output_dir)
        print("M2-PREP verification: PASS")
    else:
        generate(ROOT, args.output_dir)
        print(f"M2-PREP artifact written: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
