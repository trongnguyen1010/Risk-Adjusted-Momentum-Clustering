"""Live terminal monitor for M1 scale shard progress."""
import glob
import json
import os
import time


def main():
    while True:
        paths = [
            p for p in glob.glob("data/raw/m1_scale/**/manifest.json", recursive=True)
            if "dry-run" not in p
        ]
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 45)
        print("     DELTA - M1 SCALE WORKER 01 MONITOR     ")
        print("=" * 45)
        if paths:
            latest = max(paths, key=os.path.getmtime)
            try:
                with open(latest, encoding="utf-8") as stream:
                    data = json.load(stream)
                jobs = data.get("jobs", {})
                total = len(jobs)
                cafef_done = sum(1 for j in jobs.values() if j.get("status") == "COMPLETE" and j.get("job", {}).get("provider") == "cafef")
                kbs_done = sum(1 for j in jobs.values() if j.get("status") == "COMPLETE" and j.get("job", {}).get("provider") == "kbs")
                done = cafef_done + kbs_done
                pct = (done / total * 100) if total else 0.0
                # Each CafeF symbol has ~55 pages, KBS has 1 request per job
                est_done_req = cafef_done * 55 + kbs_done
                est_total_req = 100 * 55 + 1414
                real_pct = min(100.0, (est_done_req / est_total_req * 100)) if est_total_req else 0.0
                bar_len = int(real_pct / 100 * 30)
                bar = "#" * bar_len + "-" * (30 - bar_len)
                print(f"Run ID:            {data.get('run_id')}")
                print(f"Tiến độ thực tế:   [{bar}] {real_pct:.1f}% (khối lượng công việc)")
                print(f"  + CafeF (55 trang/mã): {cafef_done}/100 mã ({cafef_done}%)")
                print(f"  + KBS (nến OHLCV):     {kbs_done}/1414 jobs ({kbs_done/1414*100:.1f}%)")
                print(f"Tiến độ Jobs thô:  {done}/{total} jobs ({pct:.1f}%)")
                print(f"Trạng thái:        {data.get('status')}")
            except Exception:
                print("Đang đồng bộ bản ghi manifest...")
        else:
            print("Chưa tìm thấy tiến trình cào thật nào đang chạy.")
        print("\n(Bấm Ctrl + C để dừng theo dõi)")
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng theo dõi.")
