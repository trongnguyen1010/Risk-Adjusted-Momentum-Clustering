from __future__ import annotations

import argparse
import json
from pathlib import Path

from delta_t1.ingestion.financial_pit_continuation import execute, load_config, verify_existing


def main() -> int:
    parser = argparse.ArgumentParser(description="Run approved FIN-PIT-1A continuation")
    parser.add_argument("--config", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.dry_run:
        config, branch = load_config(args.config, root)
        bounds = branch.get("bounds", branch)
        result = {"run_id": config["run_id"], "branch_id": config["branch_id"], "proposal_sha256": config["proposal_sha256"],
                  "network_requests": 0, "urls": len(config["urls"]), "maximum_requests_this_run": config["network_policy"]["maximum_requests"],
                  "maximum_requests_branch_total": bounds["maximum_requests"],
                  "maximum_documents": bounds["maximum_documents"], "readiness": "APPROVED_FOR_EXECUTION"}
    elif args.execute:
        result = execute(args.config, root)
    else:
        result = verify_existing(args.config, root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
