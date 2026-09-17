# M1 Scale Team Runbook — 500 mã / 5 collectors

## 1. Kết luận vận hành hiện tại

Mục tiêu là 500 common equities có tối thiểu 3 năm usable observed history, chia thành 5 shard bất biến, mỗi shard 100 mã. Cửa sổ thu thập chung phải dài 5–15 năm; mã có 3–5 năm vẫn hợp lệ cho clustering và mã có lịch sử dài hơn được giữ toàn bộ phần nằm trong cửa sổ frozen. `REPRESENTATIVE_PILOT` đã PASS và mở **planning** cho `M1_SCALE`.

Official M1 scale tooling hiện đã có:

- deterministic assignment generator cho 5 shard × 100 mã;
- shard runner có zero-network dry-run, explicit execute và immutable resume;
- offline verifier kiểm tra exact union/disjoint/job definitions/raw checksums;
- central mapper dedupe theo canonical semantic key;
- central promoter tạo một canonical dataset và tính features đúng một lần.

Không dùng runner pilot năm lần và không sửa guard 50–60 để lách gate. Master universe 500 mã, scale config, security master và 5 assignment đã freeze; cả 5 official dry-run đều `READINESS=PASS network_requests=0`. Project owner đã chấp nhận bắt đầu acquisition do deadline. Universe là deterministic engineering sample dựa trên identity/history/source availability, không phải market-cap-weighted universe; không được diễn giải thành historical index membership.

## 2. Những lệnh chạy được ngay

Chạy từ repository root trên PowerShell. Mọi máy phải checkout cùng một commit và dùng cùng môi trường.

```powershell
git status --short
git rev-parse HEAD
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
git diff --check
```

Kiểm tra CLI hiện có:

```powershell
.venv\Scripts\python.exe scripts/plan_crawl.py --help
.venv\Scripts\python.exe scripts/run_representative_pilot.py --help
.venv\Scripts\python.exe scripts/finalize_representative_pilot.py --help
.venv\Scripts\python.exe scripts/map_representative_pilot_canonical.py --help
.venv\Scripts\python.exe scripts/promote_representative_pilot_canonical.py --help
.venv\Scripts\python.exe scripts/prepare_m1_scale_assignments.py --help
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py --help
.venv\Scripts\python.exe scripts/verify_m1_scale_handoff.py --help
.venv\Scripts\python.exe scripts/map_m1_scale_canonical.py --help
.venv\Scripts\python.exe scripts/promote_m1_scale_canonical.py --help
```

Sau khi frozen master universe/config và machine-readable pilot PASS gate tồn tại, coordinator có thể tạo read-only plan:

```powershell
.venv\Scripts\python.exe scripts/plan_crawl.py <REPRESENTATIVE_PILOT_GATE_JSON> --config <M1_SCALE_CONFIG_JSON>
```

Kết quả nằm trong `data/plans/`. `PLANNED` không có nghĩa là đã crawl.

Freeze năm assignments sau khi copy `configs/data/m1_scale.example.json` thành reviewed config và thay `universe_file`:

```powershell
.venv\Scripts\python.exe scripts/prepare_m1_scale_assignments.py `
  --config <M1_SCALE_CONFIG_JSON> `
  --pilot-gate <REPRESENTATIVE_PILOT_GATE_JSON> `
  --scale-id m1-scale-<timestamp>-<suffix> `
  --output-dir <FROZEN_ASSIGNMENT_DIRECTORY> `
  --collectors collector-01 collector-02 collector-03 collector-04 collector-05
```

Mỗi collector bắt buộc chạy dry-run trước:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config <M1_SCALE_CONFIG_JSON> `
  --pilot-gate <REPRESENTATIVE_PILOT_GATE_JSON> `
  --assignment <WORKER_ASSIGNMENT_JSON> `
  --dry-run
```

Chỉ sau dry-run PASS mới chạy network:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config <M1_SCALE_CONFIG_JSON> `
  --pilot-gate <REPRESENTATIVE_PILOT_GATE_JSON> `
  --assignment <WORKER_ASSIGNMENT_JSON> `
  --execute
```

Resume một run hợp lệ, không đổi bất kỳ input/code nào:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config <M1_SCALE_CONFIG_JSON> `
  --pilot-gate <REPRESENTATIVE_PILOT_GATE_JSON> `
  --assignment <WORKER_ASSIGNMENT_JSON> `
  --execute --resume <EXISTING_M1_SHARD_RUN_ID>
```

## 3. Freeze contract trước khi chia việc

Coordinator phải tạo và khóa các input sau trước khi bất kỳ máy nào gọi network:

1. master universe v1 gồm đúng 500 `security_id` duy nhất;
2. master config v1 với một range chung 5–15 năm; từng mã phải có tối thiểu 3 năm usable history;
3. machine-readable `REPRESENTATIVE_PILOT=PASS` gate thật;
4. source route, adapter version, mapping/QC policy và rate-limit chung;
5. exact Git commit và Python dependency lock;
6. năm assignment files, mỗi file đúng 100 mã;
7. SHA-256 cho toàn bộ input trên và một `scale_id` chung.

Mỗi assignment cần có tối thiểu:

```json
{
  "scale_id": "m1-scale-<timestamp>-<suffix>",
  "assignment_id": "m1-scale-v1-worker-01",
  "collector": "NAME",
  "shard_index": 1,
  "security_ids": ["... exactly 100 security_id values ..."],
  "start": "YYYY-MM-DD",
  "end": "YYYY-MM-DD",
  "include_benchmark": true
}
```

Hashes của config, universe, pilot gate và từng assignment được khóa trong `index.json`; run header khóa thêm code hash, job-plan hash và adapter versions. Chỉ worker 01 có `include_benchmark=true`.

Phân shard theo `security_id` đã freeze. Năm set phải pairwise-disjoint và union phải bằng đúng master universe. Không thay mã thất bại bằng mã khác sau khi xem kết quả; thay universe phải tạo v2 và immutable scale run mới.

## 4. Quyền và trách nhiệm

Coordinator sở hữu master universe/config, assignment index, benchmark/VNINDEX job, merge và final gate. Mỗi collector chỉ sở hữu một shard và không được tự đổi code, symbol, date range, source, multiplier, timezone, price basis, pagination, retry hoặc QC policy.

Nếu gặp `401`, `403`, CAPTCHA, login wall, Cloudflare/managed challenge hoặc explicit automation block: dừng source path, không bypass. Với `429`, chỉ dùng bounded backoff hiện có; không proxy/IP rotation và không tăng concurrency.

Không sửa raw, không zero-fill missing, không forward-fill price, không average KBS/CafeF conflict, không trộn raw/adjusted price và không backfill current shares về lịch sử.

## 5. Storage trên từng máy

Runtime data nằm dưới `data/`, đã được Git ignore. Không commit raw/canonical/features thật.

Layout representative pilot hiện có:

```text
data/raw/representative_pilot/<run_id>/
  run.json
  source_gate_reference.json
  job_plan.json
  manifest.json
  gate.json
data/raw/kbs/<run_id>/...
data/raw/cafef/<run_id>/...
data/derived/representative_pilot_qc/<assessment_id>/...
data/canonical/<mapping_or_canonical_id>/...
```

Layout bắt buộc cho future M1 scale executor nên giữ cùng nguyên tắc, nhưng tách rõ scale và shard:

```text
data/raw/m1_scale/<scale_id>/shards/<assignment_id>/<run_id>/
  run.json
  assignment.json
  source_gate_reference.json
  job_plan.json
  manifest.json
  gate.json
data/raw/kbs/<run_id>/...
data/raw/cafef/<run_id>/...
data/derived/m1_scale_handoff/<handoff_id>/manifest.json
```

Mỗi run và raw response là immutable. Resume chỉ được phép khi commit/config/universe/gate/assignment/job-plan/adapter hashes không đổi.

## 6. Handoff từ 5 máy

Không gửi riêng CSV/JSON đã ghép tay. Mỗi collector bàn giao một bundle nguyên trạng:

```text
handoff/<scale_id>/<assignment_id>/
  run/
  raw/kbs/
  raw/cafef/
  assessment/
  checksums.sha256
  collector_report.md
```

Bundle có thể chuyển qua shared drive/object storage có access control phù hợp quyền sử dụng dữ liệu. `checksums.sha256` phải phủ mọi file; không chứa cookie, token, credential hay absolute path phụ thuộc máy người crawl.

Collector chỉ đánh dấu `READY` khi run kết thúc, manifest/job set đầy đủ, artifact checksum hợp lệ và shard gate đã được ghi. Lỗi/gap/conflict phải để nguyên trong report; không xóa symbol để làm đẹp kết quả.

## 7. Merge trung tâm

Merge phải do code thực hiện, không copy-concatenate thủ công:

1. verify cùng `scale_id`, Git commit, config/universe/source-gate và policy hashes;
2. verify đúng 5 assignment, mỗi shard 100 mã, không overlap và union đúng 500;
3. verify exact job definitions, trạng thái và checksum của mọi artifact;
4. replay offline normalize/QC từ immutable raw;
5. merge candidates theo canonical semantic key;
6. duplicate có payload kinh tế khác nhau phải `STOP/CONFLICT`, tuyệt đối không average;
7. tạo một canonical run mới có lineage tới từng shard/raw hash;
8. tính features tập trung từ canonical run; không merge feature files do 5 máy tự tính.

Các key chính:

| Table | Merge key |
|---|---|
| `securities` | `security_id + valid_from` |
| `prices_daily` | `security_id + trade_date` |
| `benchmark_daily` | `index_id + trade_date` |
| `trading_calendar` | `exchange + trade_date` |
| `shares_history` | `security_id + effective_date` |
| `financial_reports` | canonical `report_id` sau PIT normalization |
| `financial_facts` | `report_id + statement_type + item_code` |
| `feature_snapshots` | `security_id + as_of_date` |

VNINDEX/benchmark chỉ nên do coordinator crawl một lần. Nếu lỡ có nhiều bản, chỉ dedupe khi content hash và semantics giống hệt; khác nhau phải tạo conflict.

Coordinator tạo `run-index.json`:

```json
{
  "scale_id": "m1-scale-<timestamp>-<suffix>",
  "runs": [
    {"assignment_id": "...worker-01", "run_id": "m1-shard-..."},
    {"assignment_id": "...worker-02", "run_id": "m1-shard-..."}
  ]
}
```

Mảng `runs` phải chứa đủ cả 5 assignment. Sau khi copy nguyên control runs và `data/raw/kbs|cafef/<run_id>` vào coordinator workspace:

```powershell
.venv\Scripts\python.exe scripts/verify_m1_scale_handoff.py `
  --config <M1_SCALE_CONFIG_JSON> --pilot-gate <REPRESENTATIVE_PILOT_GATE_JSON> `
  --assignment-index <ASSIGNMENT_INDEX_JSON> --run-index <RUN_INDEX_JSON>

.venv\Scripts\python.exe scripts/map_m1_scale_canonical.py `
  --config <M1_SCALE_CONFIG_JSON> --pilot-gate <REPRESENTATIVE_PILOT_GATE_JSON> `
  --assignment-index <ASSIGNMENT_INDEX_JSON> --run-index <RUN_INDEX_JSON>

.venv\Scripts\python.exe scripts/promote_m1_scale_canonical.py `
  --candidate <M1_SCALE_CANDIDATE_DIRECTORY> --config <M1_SCALE_CONFIG_JSON> `
  --securities <M1_SCALE_SECURITY_MASTER_JSON> `
  --feature-config configs/features/market.example.json
```

Scale security master phải có `purpose=M1_SCALE_SECURITY_MASTER`, `identity_scope=M1_OBSERVED_INTERVAL_ONLY`, `identity_status=provisional`, exact 500 stock rows và source evidence. Promotion vẫn ghi rõ observed interval không phải complete historical membership.

## 8. Raw → clean/map → feature hiện tại

```text
KBS direct + CafeF direct
  → immutable raw payload + request metadata + SHA-256
  → manifest/job plan/gate
  → offline QC assessment dưới data/derived/
  → normalized candidates + lineage dưới data/canonical/<mapping_id>/
  → security identity review + canonical promotion
  → clean canonical tables dưới data/canonical/<canonical_id>/clean/
  → monthly market features dưới data/canonical/<canonical_id>/features/monthly.jsonl
  → experiment runner đọc canonical features và ghi immutable experiment artifacts
```

Canonical pilot hiện ghi:

```text
data/canonical/<canonical_id>/
  manifest.json
  clean/securities.jsonl
  clean/prices_daily.jsonl
  clean/benchmark_daily.jsonl
  clean/trading_calendar.jsonl
  features/monthly.jsonl
  lineage/market.jsonl
```

Market-only M1 vẫn có thể tiếp tục khi financial là `PIT_UNRESOLVED`, nhưng `financial_features_allowed=false`. Financial data bổ sung sau chỉ match an toàn khi có stable `security_id`, canonical report identity, period/scope/revision semantics và `available_at`; không join bằng ticker hiện tại hoặc provider report ID đơn lẻ.

## 9. Definition of ready để giao cho 5 người

Chỉ giao lệnh network khi tất cả mục sau PASS:

- [x] master 500-symbol universe và five-shard assignment hashes đã freeze;
- [x] official 100-symbol shard executor có dry-run zero-network và explicit execute;
- [x] executor có immutable checkpoint/resume và access-control stop rules;
- [x] handoff verifier chứng minh exact union/disjoint/checksums/job definitions;
- [x] central merge xử lý canonical keys, conflicts và lineage fail-closed;
- [x] scale gate và canonical promotion có targeted tests;
- [x] cả 5 real-input zero-network shard dry-run PASS;
- [x] runbook và 5 worker guides dùng exact CLI đã test.
- [ ] full five-shard merge chỉ có targeted automated tests; end-to-end merge sẽ chạy sau khi nhận đủ năm immutable handoff.

**Execution status: READY TO START.** Mục chưa hoàn tất ở trên là residual operational risk đã được ghi rõ, không cho phép sửa raw, đổi ticker hay tự thay mã thất bại. Nếu merge fail, giữ nguyên năm handoff và sửa đúng blocker bằng version/run mới.
