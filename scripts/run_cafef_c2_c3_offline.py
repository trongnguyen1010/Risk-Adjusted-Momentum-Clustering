#!/usr/bin/env python3
"""Run CafeF C1 post-crawl audit, C2 candidates, and C3 field readiness offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.cafef_primary_offline import run_from_config  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs/data/cafef_c2_c3_offline.v1.json"
DEFAULT_OUTPUT = ROOT / "artifacts/cafef_primary/cafef-c2-c3-offline-20260924"


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline CafeF C1-C3 audit; performs zero network requests")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    manifest = run_from_config(ROOT, config, args.output_dir)
    print(json.dumps({
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "pilot_security_count": manifest["summary"]["pilot_security_count"],
        "normalized_candidate_count": manifest["summary"]["normalized_candidate_count"],
        "raw_audit_pass_count": manifest["summary"]["raw_audit_pass_count"],
        "cafef_canonical_ready": manifest["cafef_canonical_ready"],
        "network_requests": manifest["network_requests"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
