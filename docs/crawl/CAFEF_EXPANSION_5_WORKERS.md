# CafeF expansion v1 — runbook cho 5 workers

Mỗi worker chỉ clone, kiểm tra, dry-run, execute, package và gửi **một ZIP**. Không sửa code/config, không commit/push/merge, không đổi ticker và không normalize dữ liệu.

Owner phải gửi cho cả năm workers cùng một `FINAL_COMMIT_SHA` C6-R1 và worker number. Assignment tương ứng là `worker-01.json` … `worker-05.json`. Contract trong file dùng `execution_version=c6-cafef-expansion-v1` để tránh commit tự tham chiếu; runner bắt buộc đối chiếu SHA do owner cung cấp trước mọi network request.

## 1. Clone và kiểm tra

Thay `<FINAL_COMMIT_SHA>` và `<NN>` bằng thông tin owner gửi:

```powershell
git clone --branch m1-cafef-primary-experiment <REPOSITORY_URL> Risk-Adjusted-Momentum-Clustering
Set-Location Risk-Adjusted-Momentum-Clustering

git status --short
git branch --show-current
git rev-parse HEAD
```

Kết quả bắt buộc: status rỗng, branch `m1-cafef-primary-experiment`, HEAD đúng `<FINAL_COMMIT_SHA>`.

## 2. Setup Python

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e .
```

Không cần dependency plotting/research.

## 3. Dry-run — bắt buộc, zero network

```powershell
.venv\Scripts\python.exe scripts/run_cafef_expansion_worker.py `
  --assignment configs/data/cafef_expansion_v1/worker-<NN>.json `
  --expected-commit <FINAL_COMMIT_SHA> `
  --dry-run
```

Chỉ tiếp tục khi thấy:

```text
READINESS=PASS
network_requests=0
```

## 4. Execute hoặc resume

```powershell
.venv\Scripts\python.exe scripts/run_cafef_expansion_worker.py `
  --assignment configs/data/cafef_expansion_v1/worker-<NN>.json `
  --expected-commit <FINAL_COMMIT_SHA> `
  --execute
```

Ghi lại `run_id`. Nếu process dừng, resume đúng run đó:

```powershell
.venv\Scripts\python.exe scripts/run_cafef_expansion_worker.py `
  --assignment configs/data/cafef_expansion_v1/worker-<NN>.json `
  --expected-commit <FINAL_COMMIT_SHA> `
  --execute `
  --resume <RUN_ID>
```

Runner dùng concurrency 1, tối thiểu 3 giây/request, timeout 20 giây và tối đa 2 attempts chỉ cho 500/502/503/504. Nếu gặp 401/403/429, CAPTCHA, Cloudflare, managed challenge hoặc access denied: runner hard-stop; không bypass, proxy rotation hoặc fingerprint trick.

## 5. Package và gửi đúng một file

Run `PARTIAL` vẫn được package, không được che failure:

```powershell
.venv\Scripts\python.exe scripts/package_cafef_expansion_handoff.py `
  --assignment configs/data/cafef_expansion_v1/worker-<NN>.json `
  --run-id <RUN_ID>
```

Gửi duy nhất file:

```text
handoff/cafef-expansion-v1/cafef-expansion-v1-worker-<NN>.zip
```

Không gửi raw folder riêng. Không đưa cookie, token, credential, browser profile hoặc path máy cá nhân vào handoff.

## Owner verification sau khi nhận đủ 5 ZIP

Owner đặt các file tại `data/handoffs/cafef_expansion_v1/incoming/`, sau đó chạy:

```powershell
.venv\Scripts\python.exe scripts/verify_cafef_expansion_handoffs.py `
  --incoming data/handoffs/cafef_expansion_v1/incoming `
  --expected-commit <FINAL_COMMIT_SHA>
```

Kết quả bắt buộc là `HANDOFF_VERIFICATION=PASS`, `assignments=5`, `tickers=600`.
Lệnh từ chối old/new/mixed commit và chỉ verify, không merge/normalize/promote.

## Contract C8 sau merge — chưa thực thi

C8 phải audit hai lớp độc lập: (A) full history theo reviewed trading calendar và valid listing/identity interval; (B) latest 253 expected sessions tại snapshot `2026-08-28`. Full-history classification chỉ dùng `OBSERVED_VALID`, `OBSERVED_ZERO_VOLUME`, `MISSING_ON_TRADEHISTORYNEW`, `INVALID_PROVIDER_ROW`, `CONFLICTING_PROVIDER_OBSERVATION`, `IDENTITY_OR_LISTING_BOUNDARY`, `CALENDAR_UNCERTAIN`, `DEFERRED_REVIEW`. Không timeline compression, fill hoặc missing-to-zero. `FULL_HISTORY_COMPLETE` không đồng nghĩa `LATEST_253_COMPLETE`.
