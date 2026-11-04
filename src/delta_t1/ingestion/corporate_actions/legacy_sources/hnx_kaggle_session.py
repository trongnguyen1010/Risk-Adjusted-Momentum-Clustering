"""Điều phối các chặng V5 cùng checkpoint, chỉ nối tiếp khi hết budget hợp lệ.

Module này được nhúng vào notebook; không ghi đè code đã pin trong state V5.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time


def run_session(project, index, *, exporter, collect=True, max_requests=1000,
                max_seconds=21600, runner=subprocess.run, clock=time.monotonic, sleep=time.sleep):
    """Giữ một deadline chung; budget stop được resume, source stop luôn kết thúc."""
    project = Path(project).resolve()
    if index not in range(4) or not 1 <= max_requests <= 1000 or not 1 <= max_seconds <= 21600:
        raise ValueError("INVALID_SESSION_CONFIGURATION")
    assignment = json.loads((project / f"assignments/shard_{index}.json").read_text(encoding="utf-8"))
    if assignment["shard_index"] != index:
        raise ValueError("SESSION_SHARD_MISMATCH")
    members = set(assignment["hnx_tickers"])
    stamp = lambda: datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = project / "kaggle_sessions" / f"shard_{index}" / ("session-" + stamp())
    folder.mkdir(parents=True, exist_ok=False)
    deadline = clock() + max_seconds
    chunks, latest, exported = [], None, None
    status, error = "SESSION_TIME_LIMIT_REACHED", None

    def checkpoint():
        nonlocal exported
        exported = project.parent / f"delta-hnx-state-s{index}-{stamp()}.zip"
        exporter(project, exported, index)
        print("TẢI FILE NÀY VỀ / ATTACH CHO LƯỢT TIẾP:", exported, flush=True)

    try:
        while True:
            remaining = int(deadline - clock())
            if remaining < 1:
                break
            collections = lambda: set((project / f"kaggle_runs/shard_{index}").glob("run-*/collection"))
            before = collections()
            command = [sys.executable, str(project / "scripts/run_hnx_kaggle_v1.py"),
                       "--shard-index", str(index), "--max-requests", str(max_requests),
                       "--max-seconds", str(remaining)]
            if collect:
                command.append("--collect")
            print(f"BẮT ĐẦU CHẶNG {len(chunks) + 1}, SHARD {index}; còn tối đa {remaining} giây trong phiên.", flush=True)
            child = runner(command, cwd=project)
            new = collections() - before
            entry = {"chunk": len(chunks) + 1, "returncode": child.returncode,
                     "allocated_seconds": remaining, "collection": None, "result": None}
            if len(new) == 1:
                output = new.pop()
                body = (output / "result.json").read_bytes()
                manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
                if hashlib.sha256(body).hexdigest() != manifest["files"]["result.json"]:
                    raise ValueError("SESSION_RESULT_CHECKSUM_MISMATCH")
                latest = json.loads(body)
                pending = latest["pending_tickers"]
                quarantined = latest["quarantined_tickers"]
                if (latest["scope_tickers"] != len(members) or len(pending) != len(set(pending))
                        or len(quarantined) != len(set(quarantined)) or set(pending) & set(quarantined)
                        or not set(pending + quarantined) <= members
                        or latest["handled_tickers"] + len(pending) + len(quarantined) != len(members)
                        or type(latest["resumable"]) is not bool):
                    raise ValueError("SESSION_RESULT_SCOPE_MISMATCH")
                entry.update(collection=str(output), result=latest)
            chunks.append(entry)
            with (folder / "progress.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
            if child.returncode != 0:
                status = "STOPPED_COLLECTOR_ERROR"
                break
            if not collect:
                status = "PREFLIGHT_ONLY"
                break
            if entry["result"] is None:
                status = "STOPPED_NO_NEW_COLLECTION_RESULT"
                break
            if latest["resumable"] is not True or latest["status"] == "STOPPED_REVIEW_REQUIRED":
                status = "STOPPED_REVIEW_REQUIRED"
                break
            print(json.dumps({"session_chunk": len(chunks), "handled_tickers": latest["handled_tickers"],
                              "pending_tickers_count": len(latest["pending_tickers"]),
                              "quarantined_tickers_count": len(latest["quarantined_tickers"]),
                              "stop_reason": latest["stop_reason"]}, ensure_ascii=False), flush=True)
            if not latest["pending_tickers"]:
                status = "NO_PENDING_TICKERS_REVIEWS_REMAIN"
                break
            if latest["stop_reason"] not in {"RUN_REQUEST_BUDGET_EXHAUSTED", "RUN_TIME_BUDGET_EXHAUSTED"}:
                status = "STOPPED_NOT_AN_AUTOMATIC_BUDGET_RESUME"
                break
            if latest["network_requests_this_run"] <= 0:
                status = "STOPPED_NO_REQUEST_PROGRESS"
                break
            checkpoint()
            print("Đã lưu checkpoint; tự tiếp tục các mã còn chờ trong cùng phiên.", flush=True)
            sleep(8)  # Preserve spacing before the next subprocess's fresh preflight client.
    except KeyboardInterrupt:
        status = "INTERRUPTED_BY_USER"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        status, error = "STOPPED_SESSION_ERROR", str(exc)
    finally:
        summary = {"stage": "HNX_V5_RESUME_SESSION_V1", "shard_index": index, "status": status,
                   "error": error, "session_seconds_limit": max_seconds, "chunk_requests_limit": max_requests,
                   "chunk_count": len(chunks), "chunks": chunks, "last_result": latest,
                   "canonical_build": False, "historical_coverage_certified": False}
        with (folder / "result.json").open("x", encoding="utf-8") as stream:
            json.dump(summary, stream, ensure_ascii=False, indent=2)
        checkpoint()
    print(json.dumps({"session_status": status, "chunk_count": len(chunks),
                      "last_state_zip": str(exported), "error": error}, ensure_ascii=False), flush=True)
    return summary
