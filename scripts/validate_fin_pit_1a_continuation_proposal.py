from __future__ import annotations

import argparse
import json
from pathlib import Path

from delta_t1.ingestion.financial_pit_continuation import validate_proposal


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate FIN-PIT-1A continuation proposal without network")
    parser.add_argument("--proposal", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_proposal(args.proposal), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
