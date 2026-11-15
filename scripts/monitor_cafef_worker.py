"""Công cụ theo dõi tiến trình cào dữ liệu CafeF Worker theo thời gian thực (Live Monitor)."""
import glob
import json
import os
import sys
import time
from datetime import datetime, timezone

# Đảm bảo mã hóa UTF-8 và tự động xả buffer (flush) cho terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

def clear_screen():
    # Dùng ANSI escape code hoặc cls
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()

def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    return f"{minutes:02d}m {secs:02d}s"

def make_bar(percent, width=28):
    percent = max(0.0, min(100.0, percent))
    filled = int(width * percent / 100)
    bar = "=" * filled + (">" if filled < width else "") + " " * (width - filled - 1 if filled < width else 0)
    return f"[{bar[:width]}] {percent:5.1f}%"

def find_latest_run():
    base_pattern = "data/raw/cafef_expansion/*/*/*/state.json"
    matches = glob.glob(base_pattern)
    if not matches:
        matches = glob.glob("data/raw/cafef_expansion/**/state.json", recursive=True)
    if not matches:
        return None
    matches.sort(key=lambda p: os.path.getmtime(p))
    state_file = matches[-1]
    run_dir = os.path.dirname(state_file)
    run_file = os.path.join(run_dir, "run.json")
    assignment_file = os.path.join(run_dir, "assignment.json")
    return run_dir, state_file, run_file, assignment_file

def display_once():
    info = find_latest_run()
    clear_screen()
    now = datetime.now()

    if not info:
        lines = [
            "=" * 60,
            "        BANG THEO DOI TIEN DO CAFEF WORKER (LIVE)",
            "=" * 60,
            "Chua tim thay tien trinh cao nao dang chay.",
            "Vui long dam bao ban da chay lenh --execute.",
            f"Cap nhat luc: {now.strftime('%H:%M:%S')}",
            "=" * 60,
        ]
        print("\n".join(lines), flush=True)
        return

    run_dir, state_file, run_file, assignment_file = info
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        return

    run_data = {}
    if os.path.exists(run_file):
        try:
            with open(run_file, "r", encoding="utf-8") as f:
                run_data = json.load(f)
        except Exception:
            pass

    assignment_data = {}
    if os.path.exists(assignment_file):
        try:
            with open(assignment_file, "r", encoding="utf-8") as f:
                assignment_data = json.load(f)
        except Exception:
            pass

    worker_id = assignment_data.get("worker_id") or run_data.get("assignment_id") or "WORKER"
    worker_label = worker_id.upper().replace("-", " ")
    target_reqs = assignment_data.get("estimated_requests", 6960)

    lines = []
    lines.append("=" * 60)
    lines.append(f"        BANG THEO DOI TIEN DO CAFEF {worker_label} (LIVE)")
    lines.append("=" * 60)

    run_id = run_data.get("run_id", os.path.basename(run_dir))
    status = run_data.get("status", "RUNNING")
    reqs = run_data.get("network_requests", 0)
    started_at_str = run_data.get("started_at")

    elapsed_str = "--"
    eta_str = "Dang tinh toan..."
    if started_at_str:
        try:
            st = datetime.fromisoformat(started_at_str)
            elapsed_seconds = (datetime.now(timezone.utc) - st).total_seconds()
            elapsed_str = format_duration(elapsed_seconds)

            if reqs > 5 and elapsed_seconds > 10:
                sec_per_req = elapsed_seconds / reqs
                rem_reqs = max(0, target_reqs - reqs)
                rem_seconds = rem_reqs * sec_per_req
                eta_str = format_duration(rem_seconds)
        except Exception:
            pass

    tickers = state.get("tickers", {})
    total_tickers = len(tickers)
    done_tickers = sum(1 for v in tickers.values() if v.get("status") == "COMPLETE")
    running_list = [k for k, v in tickers.items() if v.get("status") == "RUNNING"]
    curr_ticker = running_list[0] if running_list else ("HOAN THANH" if (done_tickers == total_tickers and total_tickers > 0) else "Tam dung")
    curr_page = tickers.get(curr_ticker, {}).get("next_page", 1) if running_list else "-"

    pct = (done_tickers / total_tickers * 100) if total_tickers else 0.0

    lines.append(f" Run ID          : {run_id}")
    lines.append(f" Trang thai      : {status}")
    lines.append(f" Thoi gian chay  : {elapsed_str} (Du kien con lai: ~{eta_str})")
    lines.append(f" Tong Requests   : {reqs} / ~{target_reqs:,}")
    lines.append("-" * 60)
    lines.append(f" Tien do ma CK   : {done_tickers}/{total_tickers} ma da xong")
    lines.append(f"                   {make_bar(pct, width=28)}")
    lines.append(f" Ma dang cao     : {curr_ticker} (Dang lay trang {curr_page})")
    lines.append("=" * 60)
    lines.append(f" [Cap nhat luc {now.strftime('%H:%M:%S')} - Tu dong refresh moi 3s - Ctrl+C de thoat]")

    print("\n".join(lines), flush=True)

def main():
    try:
        while True:
            display_once()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nDa thoat man hinh theo doi. Tien trinh cao van dang tiep tuc chay ngam.", flush=True)

if __name__ == "__main__":
    main()
