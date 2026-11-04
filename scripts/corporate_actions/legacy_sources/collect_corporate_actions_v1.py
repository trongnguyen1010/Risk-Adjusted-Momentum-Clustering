"""Bounded public collection, offline validation and signed review for M3 Q11."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions_v1 import (
    build, coverage_report, csv_text, init_template, json_text, validate_file, write_new,
)
from delta_t1.ingestion import corporate_action_collection as semi
from delta_t1.ingestion import corporate_action_multisource as multi


def is_multi(root):
    return json.loads((root / "manifest.json").read_text(encoding="utf-8")).get("schema_version") == multi.VERSION


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Semiautomatic corporate_actions_v1 collection for M3 Q11; no price series")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init-template", help="Create a header-only event CSV and optional scope queue")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--coverage-output", type=Path)
    init.add_argument("--universe", type=Path, help="Explicit scoped security_id,ticker,exchange CSV")
    valid = commands.add_parser("validate", help="Validate CSV without changing input")
    valid_inputs = valid.add_mutually_exclusive_group(required=True)
    valid_inputs.add_argument("--input", type=Path, help="Legacy manual CSV, contract 1.0.0")
    valid_inputs.add_argument("--collection", type=Path, help="Immutable semiautomatic collection directory")
    valid.add_argument("--output", type=Path, help="Optional new JSON diagnostic file")
    canonical = commands.add_parser("build", help="Create a new immutable bundle; quarantine unresolved rows")
    build_inputs = canonical.add_mutually_exclusive_group(required=True)
    build_inputs.add_argument("--input", type=Path, help="Legacy manual CSV, contract 1.0.0")
    build_inputs.add_argument("--collection", type=Path, help="Semiautomatic collection directory, contract 1.1.0")
    canonical.add_argument("--reviews", type=Path, help="Signed review CSV from review-report")
    canonical.add_argument("--output", type=Path, required=True, help="New artifact directory")
    report = commands.add_parser("report", help="Check attested coverage against an explicit universe")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--coverage", type=Path, required=True)
    report.add_argument("--universe", type=Path, required=True)
    report.add_argument("--config", type=Path, default=ROOT / "configs/data/corporate_actions_v1.json")
    report.add_argument("--output", type=Path, required=True)
    auto = commands.add_parser("collect", help="Fetch bounded public VSDC/HNX pages into a new candidate run")
    auto_scope = auto.add_mutually_exclusive_group(required=True)
    auto_scope.add_argument("--universe", type=Path, help="Scope CSV; historical identity fields needed for AUTO_VERIFIED")
    auto_scope.add_argument("--tickers", nargs="+", help="Start discovery without a scope CSV; identity remains unresolved")
    auto.add_argument("--exchange", choices=["HOSE", "HNX", "UPCOM"], help="Required with --tickers")
    auto.add_argument("--config", type=Path)
    auto.add_argument("--multi-source", action="store_true", help="Contract 1.2: field completion and separate event-data/PIT verification")
    auto.add_argument("--field-input", type=Path, help="Partial-source observation JSONL (IR/vendor/official evidence); requires --multi-source")
    auto.add_argument("--start", help="Required ex-date window, YYYY-MM-DD; default from config")
    auto.add_argument("--end")
    auto.add_argument("--output", type=Path, required=True)
    auto.add_argument("--sources", nargs="+", choices=["VSDC", "HNX", "HOSE"])
    auto.add_argument("--max-pages", type=int)
    auto.add_argument("--max-details", type=int)
    auto.add_argument("--max-requests", type=int)
    auto.add_argument("--manual-input", type=Path, help="Optional legacy template supplement; same checks and review")
    auto.add_argument("--dry-run", action="store_true", help="Plan only; no network and no output artifact")
    queue = commands.add_parser("review-report", help="Create an editable review queue copy; preserves evidence columns")
    queue.add_argument("--collection", type=Path, required=True)
    queue.add_argument("--output", type=Path, required=True)
    coverage = commands.add_parser("coverage", help="Candidate/verified/review counts and full-window coverage")
    coverage.add_argument("--collection", type=Path, required=True)
    coverage.add_argument("--reviews", type=Path)
    coverage.add_argument("--attestation", type=Path, help="Optional full-window review CSV, legacy coverage header")
    coverage.add_argument("--output", type=Path, required=True)
    replay = commands.add_parser("replay", help="Reclassify archived parsed candidates into a new run; zero network")
    replay.add_argument("--collection", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--universe", type=Path, help="Contract 1.2: new reviewed identity scope without refetching sources")
    replay.add_argument("--field-input", type=Path, help="Contract 1.2: partial evidence supplement JSONL")
    replay.add_argument("--reparse", action="store_true", help="Contract 1.2: parse archived VSDC/HNX responses with current parser; zero network")
    args = parser.parse_args(argv)
    try:
        if args.command == "init-template":
            init_template(args.output, args.coverage_output, args.universe)
            print(f"TEMPLATE_CREATED: {args.output}")
            return 0
        if args.command == "validate":
            if args.collection:
                if is_multi(args.collection):
                    observations, _, _ = multi.load(args.collection)
                    result = {"status": "PASS", "observation_count": len(observations), "meaning": "CHECKSUM_VERIFIED; NOT_COVERAGE_CERTIFICATION"}
                else:
                    candidates, _ = semi.load_collection(args.collection)
                    result = {"status": "PASS", "candidate_count": len(candidates), "meaning": "INTEGRITY_AND_REDERIVATION_ONLY"}
            else:
                result = {k: v for k, v in validate_file(args.input).items() if k != "records"}
            if args.output:
                write_new(args.output, json_text(result))
            passed = result["status"] == "PASS"
        elif args.command == "build":
            if args.reviews and not args.collection:
                raise ValueError("--reviews requires --collection; legacy input remains unchanged")
            result = (multi.build(args.collection, args.output, args.reviews) if is_multi(args.collection) else semi.build_collection(args.collection, args.output, args.reviews)) if args.collection else build(args.input, args.output)
            passed = result["status"] == "PASS"
        elif args.command == "collect":
            workflow = multi if args.multi_source else semi
            config_path = args.config or ROOT / ("configs/data/corporate_actions_multisource_v1.json" if args.multi_source else "configs/data/corporate_actions_semiautomatic_v1.json")
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            if cfg.get("schema_version") != workflow.VERSION:
                raise ValueError("unsupported collector config version")
            if args.field_input and not args.multi_source:
                raise ValueError("--field-input requires --multi-source")
            def run_collect(scope):
                return workflow.collect(scope, args.output, args.start or cfg["required_start_date"], args.end or cfg["required_end_date"],
                                    args.max_pages if args.max_pages is not None else cfg["max_pages"],
                                    args.max_details if args.max_details is not None else cfg["max_details"],
                                    args.max_requests if args.max_requests is not None else cfg["max_requests"],
                                    args.sources or (["VSDC", "HNX", "HOSE"] if args.multi_source else ["VSDC", "HNX"]), args.manual_input, args.dry_run,
                                    transport_options={"interval": cfg["min_request_interval_seconds"], "timeout": cfg["timeout_seconds"], "max_bytes": cfg["max_response_bytes"]},
                                    **({"field_input": args.field_input} if args.multi_source else {}))
            if args.tickers:
                if not args.exchange:
                    raise ValueError("--tickers requires --exchange; no exchange/identity inference")
                temp_root = ROOT / "tmp"
                temp_root.mkdir(exist_ok=True)
                with tempfile.TemporaryDirectory(dir=temp_root) as temp:
                    scope = Path(temp) / "scope.csv"
                    scope.write_text(csv_text(("ticker", "exchange"), [{"ticker": t, "exchange": args.exchange} for t in args.tickers]), encoding="utf-8")
                    result = run_collect(scope)
            else:
                result = run_collect(args.universe)
            passed = result.get("status") == "DRY_RUN" or result.get("live_source_validation") != "BLOCKED"
        elif args.command == "review-report":
            if is_multi(args.collection):
                observations, scope, plan = multi.load(args.collection)
                events, rows = multi.reconcile(observations, scope, plan["created_at"])
                allowed = {e["event_id"] for e in multi.load_choices(args.collection)[0]}
                rows = [r for r in rows if r["event_id"] in allowed]
                fields = multi.QUEUE_FIELDS
            else:
                candidates, _ = semi.load_collection(args.collection)
                rows, fields = semi.queue_rows(candidates), semi.QUEUE_FIELDS
            write_new(args.output, csv_text(fields, rows))
            result, passed = {"review_queue_rows": len(rows), "output": str(args.output)}, True
        elif args.command == "coverage":
            result = (multi.coverage if is_multi(args.collection) else semi.coverage)(args.collection, args.reviews, args.attestation)
            write_new(args.output, json_text(result))
            passed = result["coverage_pass"]
        elif args.command == "replay":
            if is_multi(args.collection):
                result = multi.replay(args.collection, args.output, args.universe, args.field_input, args.reparse)
            else:
                if args.universe or args.field_input or args.reparse:
                    raise ValueError("scope/field-input/reparse replay options require contract 1.2")
                result = semi.replay_collection(args.collection, args.output)
            passed = True
        else:
            config = json.loads(args.config.read_text(encoding="utf-8"))
            result = coverage_report(args.input, args.coverage, args.universe,
                                     config["required_start_date"], config["required_end_date"])
            result["window_config"] = config
            write_new(args.output, json_text(result))
            passed = result["coverage_pass"]
        print(json_text(result), end="")
        return 0 if passed else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
