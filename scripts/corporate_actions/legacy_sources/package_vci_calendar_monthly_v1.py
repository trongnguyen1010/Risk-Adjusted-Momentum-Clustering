"""Đóng gói offline một notebook VCI theo tháng sau successful pilot V3."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.vci_calendar_monthly import (
    SCOPE_SHA, PILOT_SHA, validate_inputs, months,
)

WHEEL = ("https://vnstocks.com/api/packages/files/vnstock/5.2.1/"
         "vnstock-5.2.1-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
         "#sha256=7ed7016a8aef823a20f4f8847196a4072cb97cb19801ce08a6981ac628200fc5")

INSTALL_CELL = '''import subprocess, sys, json
try:
    installed = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '--upgrade', WHEEL_URL],
                               capture_output=True, text=True, timeout=300)
    INSTALL_OK = installed.returncode == 0
    print(json.dumps({'sdk_install_ok': INSTALL_OK, 'returncode': installed.returncode}))
except Exception as exc:
    INSTALL_OK = False
    print(json.dumps({'sdk_install_ok': False, 'error_type': type(exc).__name__}))
'''

RUN_CELL = '''from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys, queue, threading, time

# Không cần sửa cấu hình hoặc thêm Dataset ở lần đầu.
# Để tiếp tục: attach đúng MỘT ZIP delta-vci-state-*.zip của lượt trước.
RESUME_ZIP = None
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
WORK = Path('/kaggle/working') / ('delta-vci-monthly-' + stamp)
WORK.mkdir(exist_ok=False)
for name, body in PORTABLE_FILES.items():
    if hashlib.sha256(body.encode()).hexdigest() != PORTABLE_HASHES[name]:
        raise ValueError('PORTABLE_FILE_HASH_MISMATCH')
    (WORK / name).write_text(body, encoding='utf-8')
sys.path.insert(0, str(WORK))
from vci_calendar_monthly import (prepare, report, seal, write_json, archive_state, months)
plan = json.loads(PORTABLE_FILES['plan.json'])
scope = json.loads(PORTABLE_FILES['scope.json'])
gate = json.loads(PORTABLE_FILES['pilot_gate.json'])
OUTPUT = WORK / 'state'
windows = months(plan['start'], plan['end'])
key = None
proc = None
runner_status = 'STOPPED_NOTEBOOK_RUNNER'
runner_stage = 'RESUME_SELECTION'
runner_diagnostic = None
resume = None
try:
    candidates = list(Path('/kaggle/input').rglob('delta-vci-state-*.zip'))
    if RESUME_ZIP is None and len(candidates) > 1:
        raise ValueError('MULTIPLE_RESUME_ZIPS_ATTACH_ONLY_LATEST_ONE')
    resume = Path(RESUME_ZIP) if RESUME_ZIP else (candidates[0] if candidates else None)
    # Validate resume completely BEFORE any Secret access/login.
    if resume:
        runner_stage = 'RESUME_VERIFY'
        from vci_calendar_monthly import verify_state
        prior = verify_state(resume)
        previous = json.loads(prior['result.json'])
        if previous['status'] not in {'STOPPED_TIME_BUDGET', 'COLLECTION_EXPORTS_READY_FOR_REVIEW'}:
            raise ValueError('SOURCE_STOP_REQUIRES_REVIEW_NO_AUTOMATIC_RESUME')
        for name in ('plan.json', 'scope.json', 'pilot_gate.json'):
            if json.loads(prior[name]) != json.loads(PORTABLE_FILES[name]):
                raise ValueError('RESUME_INPUT_MISMATCH')
    print(json.dumps({'stage': 'VCI_MONTHLY_START', 'windows': len(windows), 'c8_v2_tickers': 1522,
                      'resume_attached': bool(resume), 'session_seconds': plan['session_seconds']}), flush=True)
    if not INSTALL_OK:
        raise RuntimeError('SDK_INSTALL_FAILED_NO_LOGIN')
    runner_stage = 'SECRET_INPUT'
    from kaggle_secrets import UserSecretsClient
    key = UserSecretsClient().get_secret('VNSTOCK_API_KEY')
    cmd = [sys.executable, str(WORK / 'vci_calendar_monthly.py'), '--inputs', str(WORK), '--output', str(OUTPUT)]
    if resume:
        cmd += ['--resume', str(resume)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, encoding='utf-8')
    proc.stdin.write(key)
    proc.stdin.close()
    key = None
    lines = queue.Queue()
    def read_lines():
        try:
            for line in proc.stdout:
                # Discard SDK output; forward only collector's narrow progress schema.
                if len(line) < 600:
                    lines.put(line)
        finally:
            lines.put(None)
    threading.Thread(target=read_lines, daemon=True).start()
    runner_stage = 'COLLECTOR_PROCESS'
    deadline = time.monotonic() + plan['parent_timeout_seconds']
    ended = False
    while not ended:
        if time.monotonic() >= deadline:
            proc.kill()
            proc.wait(timeout=15)
            runner_status = 'STOPPED_RUNNER_TIMEOUT_REVIEW_REQUIRED'
            runner_diagnostic = {'stage': 'COLLECTOR_PROCESS', 'error_type': 'TimeoutExpired'}
            break
        try:
            line = lines.get(timeout=1)
        except queue.Empty:
            continue
        if line is None:
            ended = True
            continue
        try:
            item = json.loads(line)
            allowed = {'event', 'month', 'completed', 'total', 'rows', 'status'}
            if not isinstance(item, dict) or not set(item) <= allowed:
                continue
            if item.get('event') not in {'QUERY_STARTED', 'QUERY_SAVED', 'FINISHED'}:
                continue
            if any(type(item[k]) is not int or not 0 <= item[k] <= 20000 for k in ('completed', 'total', 'rows') if k in item):
                continue
            if 'month' in item and item['month'] not in {w['id'] for w in windows}:
                continue
            statuses = {'COLLECTION_EXPORTS_READY_FOR_REVIEW', 'STOPPED_TIME_BUDGET',
                        'STOPPED_SOURCE_OR_ROUTE_MISMATCH', 'STOPPED_SCHEMA_REVIEW_REQUIRED',
                        'STOPPED_POSSIBLE_ROW_TRUNCATION', 'STOPPED_SDK_OR_EXPORT_ERROR_NO_RETRY',
                        'STOPPED_SETUP_OR_INTEGRITY_ERROR'}
            if 'status' in item and item['status'] not in statuses:
                continue
            print(json.dumps(item), flush=True)
        except Exception:
            pass
    proc.wait(timeout=15)
except Exception as exc:
    # No exception text/traceback, key, SDK stdout/stderr or auth caches are exported.
    print(json.dumps({'stage': 'NOTEBOOK_RUNNER', 'error_type': type(exc).__name__}), flush=True)
    runner_diagnostic = {'stage': runner_stage, 'error_type': type(exc).__name__}
finally:
    key = None
    if proc is not None and proc.poll() is None:
        proc.kill()
        proc.wait(timeout=15)
    if not (OUTPUT / 'manifest.json').exists():
        try:
            if not OUTPUT.exists():
                prepare(OUTPUT, plan, scope, gate, resume)
            report(OUTPUT, plan, windows, runner_status, None, runner_diagnostic)
        except Exception:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            if not (OUTPUT / 'runner_failure.json').exists():
                write_json(OUTPUT / 'runner_failure.json', {'status': runner_status, 'resumable': False,
                    'canonical_build': False, 'pit_status': 'NOT_PROMOTED'})
            if not (OUTPUT / 'manifest.json').exists():
                seal(OUTPUT)
    ZIP = Path('/kaggle/working') / ('delta-vci-state-' + stamp + '.zip')
    archive_state(OUTPUT, ZIP)
    if (OUTPUT / 'result.json').exists():
        final = json.loads((OUTPUT / 'result.json').read_text())
        print(json.dumps({k: final[k] for k in ('status', 'completed_window_count', 'total_windows',
                          'sdk_export_rows_cumulative', 'resumable')}), flush=True)
    print('TẢI ZIP KẾT QUẢ:', ZIP, flush=True)
'''


def build(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    config = (ROOT / "configs/data/vci_calendar_monthly_v1.json").read_text(encoding="utf-8")
    plan = json.loads(config)
    canonical = (ROOT / "artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl").read_bytes()
    if hashlib.sha256(canonical).hexdigest() != SCOPE_SHA:
        raise ValueError("C8_V2_CANONICAL_HASH_MISMATCH")
    securities = [json.loads(line) for line in canonical.decode().splitlines() if line.strip()]
    scope = {"canonical_sha256": SCOPE_SHA, "inventory_only_not_historical_identity": True,
             "securities": [{k: row[k] for k in ("ticker", "exchange", "security_id", "identity_status")}
                            for row in securities]}
    audit = json.loads((ROOT / "tmp/vci_pilot_v3_success_audit_20261102_v1/audit.json").read_text(encoding="utf-8"))
    gate = {"access_and_export_gate": audit["access_and_export_gate"], "input_sha256": audit["input_sha256"],
            "zip_crc_pass": audit["zip_crc"] == "PASS", "manifest_hashes": audit["manifest_file_hash_checks"],
            "source_acceptance": "NOT_APPROVED", "history_completeness": "NOT_CERTIFIED"}
    if gate["input_sha256"] != PILOT_SHA:
        raise ValueError("PILOT_HASH_MISMATCH")
    validate_inputs(plan, scope, gate)
    portable = {"plan.json": config, "scope.json": json.dumps(scope, ensure_ascii=False, indent=2),
                "pilot_gate.json": json.dumps(gate, ensure_ascii=False, indent=2)}
    for name in ("vci_calendar_monthly.py", "vci_calendar_pilot.py", "vnstock_auth_diagnostic.py"):
        portable[name] = (ROOT / "src/delta_t1/ingestion" / name).read_text(encoding="utf-8")
    hashes = {name: hashlib.sha256(body.encode()).hexdigest() for name, body in portable.items()}
    setup = "PORTABLE_FILES = " + repr(portable) + "\nPORTABLE_HASHES = " + repr(hashes) + "\nWHEEL_URL = " + repr(WHEEL) + "\n"
    cells = [{"cell_type": "markdown", "metadata": {}, "source": [
        "# DELTA — Thu thập VCI theo tháng, 2019–2025\n",
        "Một notebook, CPU và Internet ON. Bật Secret VNSTOCK_API_KEY. Không cần Dataset ở lần đầu.\n",
        "84 khoảng từ 31/01/2019 đến 31/12/2025; nghỉ 8 giây, không tự retry lỗi.\n",
        "Giữ SDK exports và metadata; chưa canonical/PIT/historical identity. Thiếu trường và dòng trùng được giữ để review.\n",
        "Khi dừng vì thời gian, attach đúng một ZIP delta-vci-state-*.zip mới nhất để chạy tiếp.\n"]}]
    for body in (setup, INSTALL_CELL, RUN_CELL):
        compile(body, "vci-monthly-notebook-cell", "exec")
        cells.append({"cell_type": "code", "metadata": {}, "source": body.splitlines(keepends=True),
                      "execution_count": None, "outputs": []})
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
          "language_info": {"name": "python"}, "kaggle": {"isInternetEnabled": True, "isGpuEnabled": False}},
          "nbformat": 4, "nbformat_minor": 4}
    output.mkdir(parents=True)
    for name, body in portable.items():
        (output / name).write_text(body, encoding="utf-8")
    (output / "DELTA_VCI_Monthly_2019_2025.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "HUONG_DAN.txt").write_text(
        "1. Kaggle: tạo notebook rồi File > Import Notebook; chọn DELTA_VCI_Monthly_2019_2025.ipynb.\n"
        "2. CPU, Internet ON; Add-ons > Secrets > tích VNSTOCK_API_KEY. Không dán key vào code.\n"
        "3. Không cần Dataset/ZIP HNX ở lần đầu. Chỉ chạy một notebook.\n"
        "4. Save Version > Save & Run All. Log QUERY_STARTED và QUERY_SAVED hiển thị từng tháng.\n"
        "5. Tải ZIP delta-vci-state-*.zip trong Output rồi gửi kiểm tra.\n"
        "6. status COLLECTION_EXPORTS_READY_FOR_REVIEW và completed_window_count=84 nghĩa là đã xuất hết cửa sổ truy vấn, chưa chứng nhận đầy đủ lịch sử.\n"
        "7. Chỉ khi STOPPED_TIME_BUDGET: upload ZIP mới nhất thành Dataset private, attach vào notebook rồi chạy lại; không sửa code.\n"
        "8. Lỗi auth/device/source/schema/cap/timeout: giữ ZIP và gửi kiểm tra, không tự retry/chuyển tài khoản.\n"
        "Mọi dữ liệu VSDC/HNX/20 mã cũ giữ nguyên. Không sửa M2, không canonical/PIT/identity promotion.\n", encoding="utf-8")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}
    (output / "manifest.json").write_text(json.dumps({"stage": "VCI_MONTHLY_NOTEBOOK_HANDOFF_V1", "windows": len(months(plan['start'], plan['end'])),
        "scope_count": len(securities), "files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(output.resolve()), "windows": 84, "scope_count": 1522}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), ensure_ascii=False))
