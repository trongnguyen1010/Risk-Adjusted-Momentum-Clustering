"""Freeze deterministic, disjoint M1 scale assignments from a reviewed universe."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.m1_scale import validate_master_universe, validate_pilot_gate
from delta_t1.io import digest, read_json, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--pilot-gate", required=True)
    parser.add_argument("--scale-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--guides-dir")
    parser.add_argument("--collectors", nargs="+", required=True)
    args = parser.parse_args(argv)
    try:
        config_path = Path(args.config).resolve()
        gate_path = Path(args.pilot_gate).resolve()
        config = read_json(config_path)
        gate = read_json(gate_path)
        validate_pilot_gate(gate)
        universe_path = Path(config["universe_file"])
        if not universe_path.is_absolute():
            universe_path = (config_path.parent / universe_path).resolve()
        universe = read_json(universe_path)
        validate_master_universe(universe, config)
        if len(args.collectors) != config["expected_shards"]:
            raise ValueError("collector count must equal expected_shards")
        if not args.scale_id.startswith("m1-scale-"):
            raise ValueError("scale_id must start with m1-scale-")
        output = Path(args.output_dir).resolve()
        if output.exists():
            raise ValueError("immutable assignment output directory already exists")
        ordered = sorted(universe, key=lambda row: (
            row["exchange"], row.get("sector") or "", row["security_id"]))
        shards = [[] for _ in args.collectors]
        for index, row in enumerate(ordered):
            shards[index % len(shards)].append(row["security_id"])
        entries = []
        for index, (collector, security_ids) in enumerate(zip(args.collectors, shards), 1):
            assignment = {
                "scale_id": args.scale_id,
                "assignment_id": f"{args.scale_id}-worker-{index:02d}",
                "collector": collector, "shard_index": index,
                "security_ids": security_ids, "start": config["start"],
                "end": config["end"], "include_benchmark": index == 1,
            }
            path = output / f"worker-{index:02d}.json"
            write_json(path, assignment)
            entries.append({
                "assignment_id": assignment["assignment_id"],
                "path": path.name, "sha256": digest(path.read_bytes()),
            })
        index = {
            "scale_id": args.scale_id, "status": "FROZEN",
            "config_sha256": digest(config_path.read_bytes()),
            "universe_sha256": digest(universe_path.read_bytes()),
            "pilot_gate_sha256": digest(gate_path.read_bytes()),
            "expected_total_symbols": config["expected_total_symbols"],
            "expected_shards": config["expected_shards"],
            "symbols_per_shard": config["symbols_per_shard"],
            "assignments": entries,
        }
        write_json(output / "index.json", index)
        if args.guides_dir:
            guides = Path(args.guides_dir).resolve()
            if guides.exists():
                raise ValueError("immutable worker-guide directory already exists")
            by_id = {row["security_id"]: row for row in universe}
            for position, entry in enumerate(entries, 1):
                assignment_path = output / entry["path"]
                assignment = read_json(assignment_path)
                rows = [by_id[value] for value in assignment["security_ids"]]
                table = "\n".join(
                    f"| {number} | {row['ticker']} | {row['exchange']} | {row['security_id']} |"
                    for number, row in enumerate(rows, 1))
                text = f"""# M1 Scale — Worker {position:02d}

## Phạm vi bất biến

- Collector: `{assignment['collector']}`
- Scale: `{assignment['scale_id']}`
- Assignment: `{assignment['assignment_id']}`
- Số mã: `{len(rows)}`
- Range: `{assignment['start']} .. {assignment['end']}`
- Eligibility: tối thiểu 3 năm usable history; range chung dài 5–15 năm
- Benchmark owner: `{str(assignment['include_benchmark']).lower()}`
- Assignment SHA-256: `{entry['sha256']}`

Không sửa config, assignment, ticker, date range hoặc code. Coordinator phải cung cấp đúng real pilot gate tại `data/input/representative_pilot/gate.json`.
Gate SHA-256 bắt buộc: `fac8cfba89be144e0ef8ceae3885c3b183bc18e066d6d69f53f79d18e894955f`.

## Preflight

```powershell
git status --short
git rev-parse HEAD
Get-FileHash {assignment_path.relative_to(ROOT).as_posix()} -Algorithm SHA256
Get-FileHash data/input/representative_pilot/gate.json -Algorithm SHA256
.venv\\Scripts\\python.exe -m unittest discover -s tests -v
.venv\\Scripts\\python.exe -m compileall -q src tests scripts run.py
```

## Zero-network dry-run

```powershell
.venv\\Scripts\\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment {assignment_path.relative_to(ROOT).as_posix()} `
  --dry-run
```

Chỉ chạy lệnh dưới đây sau khi dry-run in `READINESS=PASS network_requests=0`.

## Real execution

```powershell
.venv\\Scripts\\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment {assignment_path.relative_to(ROOT).as_posix()} `
  --execute
```

## Resume

Không đổi code/config/gate/assignment. Dùng run ID đã được lệnh execute in ra:

```powershell
.venv\\Scripts\\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment {assignment_path.relative_to(ROOT).as_posix()} `
  --execute --resume <RUN_ID>
```

## 100 mã được giao

| # | Ticker | Exchange | Security ID |
|---:|---|---|---|
{table}

## Bàn giao

Bàn giao nguyên trạng control run dưới `data/raw/m1_scale/{assignment['scale_id']}/shards/{assignment['assignment_id']}/<RUN_ID>/` và provider raw dưới `data/raw/kbs/<RUN_ID>/`, `data/raw/cafef/<RUN_ID>/`. Không gửi file đã ghép tay, không commit raw và không thay mã lỗi.
"""
                from delta_t1.io import atomic_write
                atomic_write(guides / f"WORKER_{position:02d}.md", text.encode("utf-8"))
        print(f"FROZEN={len(entries)} shards symbols={sum(len(s) for s in shards)}")
        print(output / "index.json")
        return 0
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
