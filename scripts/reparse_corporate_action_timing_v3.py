"""Khôi phục metadata VSDC offline; giữ nguyên observations và chính sách PIT."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_action_multisource import observation
from delta_t1.ingestion.corporate_action_sources import Document, parse_vsdc_time


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = {}

    def pin(path):
        body = path.read_bytes()
        name = path.relative_to(ROOT).as_posix()
        inputs[name] = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body)}
        return body

    def rows(path):
        return [json.loads(line) for line in pin(path).decode("utf-8-sig").splitlines() if line.strip()]

    def dump(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def jsonl(name, values):
        with (output / name).open("x", encoding="utf-8", newline="") as stream:
            for value in values:
                stream.write(encoded(value) + "\n")

    checkpoint = ROOT / "tmp/ca_c8_v2_checkpoint_20261101_v5"
    shards = ROOT / "data/corporate_actions/work/outputs"
    streams = {"v5_active": [], "v5_inventory": [], "shards": []}
    pin(checkpoint / "manifest.json")
    for label, path in [("v5_active", checkpoint / "collection/observations.jsonl"),
                        ("v5_inventory", checkpoint / "normalized_observations/all_observations.jsonl")]:
        streams[label] = [(o, path, checkpoint / "collection") for o in rows(path) if o["source_type"] == "VSDC"]
    for index in range(4):
        shard = shards / f"batch_shard_{index}"
        pin(shard / "manifest.json")
        pin(shard / "batch_results.json")
        for folder in sorted((shard / "source_receipts").iterdir()):
            if folder.is_dir():
                path = folder / "observations.jsonl"
                streams["shards"].extend((o, path, folder) for o in rows(path) if o["source_type"] == "VSDC")

    # One representative verified body per content hash; receipt copies stay in observations.
    registry = defaultdict(list)
    for obs, _, folder in streams["v5_inventory"] + streams["shards"]:
        for receipt in obs.get("source_evidence", []):
            if receipt.get("source_hash") and receipt.get("path"):
                raw = Path(receipt["path"])
                path = raw if raw.is_absolute() else folder / raw
                if not path.is_file() and (ROOT / raw).is_file():
                    path = ROOT / raw
                registry[receipt["source_hash"]].append((path.resolve(), receipt.get("url", "")))

    def reparse(item):
        digest, references = item
        path, url = next(((p, u) for p, u in references if p.is_file()), references[0])
        relative = path.relative_to(ROOT).as_posix()
        result = {"source_hash": digest, "raw_path": relative, "source_url": url}
        if not path.is_file():
            return result | {"status": "MISSING"}
        body = path.read_bytes()
        actual = hashlib.sha256(body).hexdigest()
        result.update(actual_hash=actual, file_size=len(body))
        if actual != digest:
            return result | {"status": "HASH_MISMATCH"}
        doc = Document(body.decode("utf-8", errors="replace")).root
        times = doc.find(cls="time-newstcph")
        text = times[0].text() if len(times) == 1 else ""
        timing = parse_vsdc_time(text, doc.find("time"), url=url, raw_path=relative, source_hash=digest)
        if len(times) > 1:
            timing.update(raw_text="; ".join(t.text() for t in times), parse_status="AMBIGUOUS",
                          precision="AMBIGUOUS", semantic_label="UNKNOWN", parsed_date=None,
                          parsed_time=None, parsed_datetime=None, timezone=None,
                          timing_issues=["MULTIPLE_SOURCE_TIME_BLOCKS"])
        return result | {"status": "VERIFIED_MATCH", "timing": timing}

    print(encoded({"raw_documents": len(registry), "network_requests": 0}), flush=True)
    documents = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        for index, result in enumerate(executor.map(reparse, sorted(registry.items())), 1):
            documents[result["source_hash"]] = result
            if index % 1000 == 0:
                print(encoded({"raw_documents_checked": index, "total": len(registry)}), flush=True)

    unique = {}
    occurrences = []
    unchanged = {}
    output_names = {"v5_active": "reparsed_v5_active_observations.jsonl",
                    "v5_inventory": "reparsed_v5_inventory_observations.jsonl",
                    "shards": "reparsed_shards_observations.jsonl"}
    for label, original in streams.items():
        enriched = []
        for index, (obs, path, _) in enumerate(original):
            receipt = next((r for r in obs.get("source_evidence", []) if r.get("source_hash") == obs["source_hash"]), None)
            doc = documents.get(receipt["source_hash"]) if receipt else None
            if doc and doc["status"] == "VERIFIED_MATCH":
                timing = doc["timing"]
            else:
                timing = parse_vsdc_time(url=obs["source_url"], source_hash=obs["source_hash"])
                timing["timing_issues"] = [doc["status"] if doc else "MISSING_MATCHING_RECEIPT"]
            after = observation(dict(obs, source_timing=timing))
            before_core = {k: v for k, v in obs.items() if k != "source_timing"}
            after_core = {k: v for k, v in after.items() if k != "source_timing"}
            if before_core != after_core:
                raise ValueError(f"OBSERVATION_CHANGED: {label}:{index}:{obs['observation_id']}")
            enriched.append(after)
            if label != "v5_active":
                unique.setdefault(obs["observation_id"], after)
            occurrences.append({"observation_id": obs["observation_id"], "stream": label,
                                "input_path": path.relative_to(ROOT).as_posix(), "vsdc_ordinal": index})
        unchanged[label] = {"compared": len(original), "unchanged_except_source_timing": len(enriched)}
        jsonl(output_names[label], enriched)

    jsonl("reparsed_vsdc_observations_unique.jsonl", unique.values())
    jsonl("observation_occurrences.jsonl", occurrences)
    jsonl("raw_documents_timing.jsonl", documents.values())
    with (output / "raw_payload_verification.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["source_hash", "status", "actual_hash", "raw_path", "source_url"])
        writer.writeheader()
        writer.writerows({k: d.get(k, "") for k in writer.fieldnames} for d in documents.values())

    statuses = Counter(d["status"] for d in documents.values())
    timings = [d["timing"] for d in documents.values() if d["status"] == "VERIFIED_MATCH"]
    def distribution(key):
        return dict(Counter(t[key] for t in timings))
    complete = statuses.get("VERIFIED_MATCH", 0) == len(documents) and all(t["parse_status"] == "VALID" for t in timings)
    summary = {"step": "STEP_2_VSDC_TIMING_RECOVERY_V3", "status": "PASS" if complete else "PARTIAL",
               "created_at": datetime.now(timezone.utc).isoformat(), "network_requests": 0,
               "unique_raw_documents": len(documents), "raw_verification": dict(statuses),
               "parse_status_distribution": distribution("parse_status"),
               "precision_distribution": distribution("precision"), "semantic_distribution": distribution("semantic_label"),
               "timezone_evidence_distribution": distribution("timezone_evidence"),
               "vsdc_observations": {"inventory_entries": len(streams["v5_inventory"]) + len(streams["shards"]),
                                     "unique_ids": len(unique), "stream_comparison": unchanged},
               "normalized_observation_invariants": "All original fields preserved; source_timing is the only allowed difference.",
               "unique_output_semantics": "First representative per ID; every occurrence and original receipt is retained in separate streams. No event reconciliation or freeze.",
               "policy": "UPDATE/UNKNOWN remain first-observed only. No timezone inference, EOD convention, canonical build or PIT promotion."}
    dump("timing_recovery_summary.json", summary)
    report = (f"# Khôi phục metadata VSDC — Bước 2 V3\n\n"
              f"Trạng thái kỹ thuật: **{summary['status']}**. Mạng: **0 requests**.\n\n"
              f"Đã kiểm tra {len(documents):,} raw bodies unique theo SHA-256; {dict(statuses)}.\n"
              f"Parse status: {distribution('parse_status')}; ngữ nghĩa: {distribution('semantic_label')}.\n\n"
              f"VSDC inventory/shards: {summary['vsdc_observations']['inventory_entries']:,} lượt; "
              f"{len(unique):,} observation IDs. Active v5: {len(streams['v5_active'])}.\n\n"
              "Đối chiếu toàn bộ observations: chỉ source_timing được thay đổi; receipts, thời gian gốc, "
              "observed_at, terms và ID giữ nguyên. Unique output chỉ là representative, không phải canonical.\n\n"
              "Giữ nguyên raw/V1/V2; chưa có chính sách dùng UPDATE làm PUBLICATION, chưa suy timezone, "
              "chưa build corporate_actions hoặc promote research readiness. Bước 3 cần review riêng.\n")
    (output / "timing_recovery_report.md").write_text(report, encoding="utf-8")
    for path in [Path(__file__), ROOT / "src/delta_t1/ingestion/corporate_action_sources.py",
                 ROOT / "src/delta_t1/ingestion/corporate_action_multisource.py",
                 ROOT / "tests/unit/ingestion/test_corporate_action_timing.py",
                 ROOT / "configs/data/corporate_actions_multisource_v1.json"]:
        pin(path)
    # Detect concurrent changes to all non-raw input files before sealing.
    for name, entry in inputs.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"INPUT_CHANGED: {name}")
    output_hashes = {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "size_bytes": p.stat().st_size}
                     for p in sorted(output.iterdir()) if p.is_file()}
    dump("manifest.json", {"artifact_type": "vsdc-timing-recovery-v3", "status": summary["status"],
                           "created_at": datetime.now(timezone.utc).isoformat(), "inputs_read": inputs,
                           "raw_checks": "raw_payload_verification.csv; one body per source_hash, not all duplicate receipt copies",
                           "outputs_created": output_hashes})
    print(encoded(summary), flush=True)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
