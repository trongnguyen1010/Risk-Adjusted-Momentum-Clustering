"""Exercise six synthetic securities over 18 months through vendor promotion."""
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from generate_demo import generate
from delta_t1.ingestion.synthetic import build_vendor
from delta_t1.ingestion.promotion import promote
from delta_t1.io import read_rows, write_json
from delta_t1.pipeline import run, run_canonical
from delta_t1.research import experiment

if __name__ == "__main__":
    working = ROOT / "data/offline_pilots" / ("synthetic-" + uuid.uuid4().hex[:12])
    config = generate(working)
    initial, source = run(config, working)
    if source["status"] != "complete":
        raise SystemExit("Synthetic input QC failed: " + str(initial))
    tables = {p.stem: read_rows(p) for p in (initial / "clean").glob("*.jsonl")}
    vendor, policy = build_vendor(working, tables)
    canonical, promoted = promote(vendor, policy, ROOT)
    if promoted["status"] != "complete":
        raise SystemExit("Synthetic promotion failed: " + str(canonical))
    data_run, data = run_canonical(canonical, config, ROOT)
    if data["status"] != "complete":
        raise SystemExit("Synthetic canonical QC failed: " + str(data_run))
    output, result = experiment(data_run, ROOT / "configs/research.demo.json", ROOT)
    write_json(working / "result.json", dict(synthetic=True, vendor=str(vendor), canonical=str(canonical), data_run=str(data_run), experiment=str(output), status=result["status"]))
    print(f"SYNTHETIC {result['status']}: {output / 'report.md'}")
    raise SystemExit(0 if result["status"] == "complete" else 2)
