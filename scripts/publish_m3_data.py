"""Publish the M3 working data to the public HF Dataset under `m3/` (owner request 26/10/2026).

Does not touch the files Render downloads (bundle, indicators). Uploads, with a README and a sha256 manifest:
- m3/disclosure_dates_v1/: CafeF "Công bố thông tin" crawl (raw pages, receipts, per-ticker records) and the
  availability table (ticker × fiscal year → usable_from_date) used by M3.
- m3/experiments/: input manifest, stage-0 report, Q5/Q6 feasibility counts, targets-only runs (no returns).
- m3/c8/: VNINDEX, trading calendar and the C8 daily prices (gzip; sha256 of the uncompressed file in the manifest).

Usage: python scripts/publish_m3_data.py [--dry-run] [--repo ngyen/delta-intelligence-data]
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATES = ROOT / 'data/financial/disclosure_dates_v1'
EXP = ROOT / 'data/experiments/m3'
C8 = ROOT / 'artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical'
SOURCES = [
    (DATES / 'full-20261025', 'm3/disclosure_dates_v1/full-20261025'),
    (DATES / 'availability-4f0f83108e761dae', 'm3/disclosure_dates_v1/availability-4f0f83108e761dae'),
    (DATES / 'b-tickers.txt', 'm3/disclosure_dates_v1/b-tickers.txt'),
    (EXP / 'inputs/manifest.json', 'm3/experiments/inputs/manifest.json'),
    (EXP / 'stage0-20261025T193924Z', 'm3/experiments/stage0-20261025T193924Z'),
    (EXP / 'feasibility-variants', 'm3/experiments/feasibility-variants'),
    (EXP / 'development/20261025T193607Z-21b14620', 'm3/experiments/targets-only/development'),
    (EXP / 'holdout/20261025T193615Z-21b14620', 'm3/experiments/targets-only/holdout'),
    (C8 / 'benchmark_daily.jsonl', 'm3/c8/benchmark_daily.jsonl'),
    (C8 / 'trading_calendar.jsonl', 'm3/c8/trading_calendar.jsonl'),
    (EXP / 'publish/prices_daily.jsonl.gz', 'm3/c8/prices_daily.jsonl.gz'),
]

README = """# DELTA — dữ liệu M3

Dữ liệu làm việc của M3 (backtest danh mục), kèm theo `docs/M3_PLAN.md` trên nhánh `feature/indicators-v1` của
repository `trongnguyen1010/Risk-Adjusted-Momentum-Clustering`. Các tệp mà web (Render) tải ở thư mục gốc của dataset
không đổi.

| Thư mục | Nội dung |
| --- | --- |
| `disclosure_dates_v1/full-20261025/` | Crawl "Thời gian gửi" từ API Công bố thông tin CafeF cho 1.362 mã: `raw/` (phản hồi gốc, tên = sha256), `receipts.jsonl`, `records/<mã>.csv`, `state.json` |
| `disclosure_dates_v1/availability-4f0f83108e761dae/` | `availability.csv`: mã × năm tài chính → `publication_date`, `date_source` (`CAFEF_DISCLOSURE` từ năm 2022, `LAG_RULE` = 30/06 năm sau trước đó), `usable_from_date`, cờ `non_december_fye` |
| `experiments/inputs/manifest.json` | sha256 các đầu vào M3 (bundle v4, indicators v1, bảng ngày, VNINDEX, lịch phiên, giá C8) |
| `experiments/stage0-*/` | Giai đoạn 0: đếm tập ứng viên từng tháng, kiểm cơ sở lợi suất (không có lợi suất danh mục) |
| `experiments/feasibility-variants/` | Số mã ứng viên theo 4 phương án Q5/Q6 |
| `experiments/targets-only/` | Danh sách mã mục tiêu từng tháng theo config `PROPOSED` (chưa khóa, chưa tính lợi suất) |
| `c8/` | VNINDEX, lịch phiên, giá ngày C8 (`prices_daily.jsonl.gz`; sha256 bản chưa nén trong `MANIFEST.json`) |

Ngày CafeF chỉ tin được từ năm tài chính 2022 (CafeF nhập lại lịch sử ngày 26/11/2022). Chưa có kết quả backtest:
quy tắc chiến lược đang chờ mentor chốt (`docs/M3_MENTOR_QUESTIONS.md`).
"""


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def collect():
    files = {}
    for src, dest in SOURCES:
        if not src.exists():
            raise SystemExit(f'missing: {src}')
        if src.is_file():
            files[dest] = src
        else:
            for p in sorted(src.rglob('*')):
                if p.is_file():
                    files[f'{dest}/{p.relative_to(src).as_posix()}'] = p
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='ngyen/delta-intelligence-data')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    files = collect()
    manifest = dict(created_at=datetime.now(timezone.utc).isoformat(),
                    files={k: dict(bytes=v.stat().st_size, sha256=sha256(v)) for k, v in files.items()},
                    prices_daily_uncompressed_sha256=sha256(C8 / 'prices_daily.jsonl'))
    total = sum(v['bytes'] for v in manifest['files'].values())
    print(f'{len(files)} files, {total / 1048576:.1f} MB')
    if args.dry_run:
        return
    from huggingface_hub import CommitOperationAdd, HfApi
    api = HfApi()
    ops = [CommitOperationAdd(path_in_repo=k, path_or_fileobj=str(v)) for k, v in files.items()]
    ops.append(CommitOperationAdd(path_in_repo='m3/README.md', path_or_fileobj=README.encode('utf-8')))
    ops.append(CommitOperationAdd(path_in_repo='m3/MANIFEST.json',
                                  path_or_fileobj=json.dumps(manifest, indent=1).encode('utf-8')))
    info = api.create_commit(args.repo, repo_type='dataset', operations=ops,
                             commit_message='Add M3 working data (disclosure dates, stage 0, targets-only, C8 prices)')
    print(info.commit_url)
    print(f'https://huggingface.co/datasets/{args.repo}/tree/main/m3')


if __name__ == '__main__':
    main()
