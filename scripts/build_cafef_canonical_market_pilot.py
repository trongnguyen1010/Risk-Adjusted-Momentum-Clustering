#!/usr/bin/env python3
"""Build the immutable CafeF C3-R1 canonical market pilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.cafef_canonical_market import (  # noqa: E402
    acquire_benchmark_extension,
    build_canonical_pilot,
)


DEFAULT_CONFIG = ROOT / "configs/data/cafef_canonical_market_pilot.v1.json"
DEFAULT_OUTPUT = ROOT / "artifacts/cafef_primary/cafef-canonical-market-pilot-v1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CafeF C3-R1 canonical market pilot")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--acquire-missing-benchmark",
        action="store_true",
        help="perform the single bounded VNINDEX extension request if evidence is absent",
    )
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.acquire_missing_benchmark:
        acquire_benchmark_extension(ROOT, config)
    manifest = build_canonical_pilot(ROOT, config, args.output_dir)
    print(json.dumps({
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "network_requests": manifest["network_requests"],
        "prices_daily": manifest["counts"]["prices_daily"],
        "securities": manifest["counts"]["securities"],
        "trading_calendar": manifest["counts"]["trading_calendar"],
        "benchmark_daily": manifest["counts"]["benchmark_daily"],
        "market_feature_ready": manifest["feature_readiness"]["market_feature_ready"],
        "research_ready": manifest["feature_readiness"]["research_ready"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
