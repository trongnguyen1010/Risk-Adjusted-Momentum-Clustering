"""Tạo notebook nối chặng budget cho state V5, giữ nguyên input/code pin cũ."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "412a4ffaeaa26e857123eb0f9f90ccb9c8487dd681b752b9241398133b39876c"


def build(output):
    source = ROOT / "tmp/hnx_kaggle_export_20261102_v5"
    policy = json.loads((ROOT / "configs/data/hnx_kaggle_session_v1.json").read_text(encoding="utf-8"))
    if (policy["input_bundle_manifest_sha256"] != PIN or policy["session_seconds"] != 21600
            or policy["chunk_requests"] != 1000 or policy["run_collection"] is not True
            or set(policy["automatic_resume_reasons"]) != {"RUN_REQUEST_BUDGET_EXHAUSTED", "RUN_TIME_BUDGET_EXHAUSTED"}
            or policy["source_stop_policy"] != "STOP_NO_AUTOMATIC_RETRY" or policy["canonical_build"] is not False):
        raise ValueError("SESSION_POLICY_REQUIRES_REVIEW")
    body = (source / "project/bundle_manifest.json").read_bytes()
    if hashlib.sha256(body).hexdigest() != PIN:
        raise ValueError("V5_BASE_PIN_MISMATCH")
    wrapper = (ROOT / "src/delta_t1/ingestion/hnx_kaggle_session.py").read_text(encoding="utf-8")
    output.mkdir(parents=True, exist_ok=False)
    for index in range(4):
        notebook = json.loads((source / f"DELTA_HNX_Shard_{index}.ipynb").read_text(encoding="utf-8"))
        notebook["cells"][0]["source"] = [
            f"# DELTA — HNX shard {index}, tiếp tục đến hết mã còn chờ\n",
            "Dùng state V5 mới nhất đúng shard. RUN_COLLECTION=True theo yêu cầu user.\n",
            "Phiên tối đa 6 giờ; mỗi chặng 1000 requests, tự lưu ZIP và resume khi hết budget.\n",
            "Giữ delay 8 giây, TLS và source-stop. Mã quarantined vẫn chờ review.\n",
            "Nếu gặp 401/403/429/challenge, dừng các job HNX khác. Không certify PIT/identity/history.\n"]
        config = "".join(notebook["cells"][1]["source"])
        config = config.replace("RUN_COLLECTION = False", "RUN_COLLECTION = True")
        config = config.replace("MAX_SECONDS = 3600", "MAX_SECONDS = 21600")
        notebook["cells"][1]["source"] = config.splitlines(keepends=True)
        execute = wrapper + '''\n\nsys.path.insert(0, str(WORK/'src'))
from delta_t1.ingestion.hnx_kaggle import export_state
SESSION_RESULT = run_session(WORK, SHARD_INDEX, exporter=export_state,
                             collect=RUN_COLLECTION, max_requests=MAX_REQUESTS,
                             max_seconds=MAX_SECONDS)
'''
        notebook["cells"][3]["source"] = execute.splitlines(keepends=True)
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), "notebook-cell", "exec")
                cell.update(execution_count=None, outputs=[])
        target = output / f"DELTA_HNX_Resume_Shard_{index}.ipynb"
        target.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}
    (output / "manifest.json").write_text(json.dumps({"stage": "HNX_V5_RESUME_NOTEBOOKS_V1",
        "v5_input_pin": PIN, "session_seconds": 21600, "chunk_requests": 1000,
        "wrapper_sha256": hashlib.sha256(wrapper.encode()).hexdigest(), "files": files}, indent=2) + "\n", encoding="utf-8")
    return {"output": str(output), "notebooks": 4, "input_pin": PIN}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output.resolve()), ensure_ascii=False, indent=2))
