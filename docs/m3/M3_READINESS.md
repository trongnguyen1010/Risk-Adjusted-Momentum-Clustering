# M3 — Báo cáo sẵn sàng và hướng dẫn chạy backtest

**Ngày:** 03/11/2026 · **Nhánh:** `feature/indicators-v1` · **Quyết định:** ADR D-M3-01 (`docs/DECISIONS.md`)
**Kế hoạch chuẩn:** `docs/m3/KE_HOACH_M3_SCHEMA_GITHUB.md` (bản rà soát 03/11, bảng R1–R8 ở đầu tài liệu)

**Trạng thái hiện hành 04/11/2026 — config `LOCKED`, chờ commit.** B-PIT đã build/audit/pin, feasibility và
targets-only Development/Holdout đã PASS. `PriceBook` đã giới hạn cả phiên lân cận Q17 trong đoạn;
49 test M3, compile, synthetic smoke và kiểm tra phạm vi giá trên dữ liệu thật đã PASS.
Xem [báo cáo Mục 3.11 và Mục 4](../REPORT_BACKTEST.md#311-strict-isolation-q17-và-khóa-config).
Commit code/config để đạt `git_dirty=false` trước official Development. Sau Development verify/seal mới chạy
Holdout bằng cùng code/config/input. Các mô tả trạng thái chờ B-PIT bên dưới ghi lại checkpoint 03/11;
trạng thái hiện hành trong đoạn này được ưu tiên. Chưa có kết quả lợi suất M3 tại bước khóa.

**Cập nhật 04/11/2026.** Gate cutoff ở Mục 3.1.5 của kế hoạch chuẩn đã triển khai. Khi dùng B-PIT, runner và
feasibility tạm loại mã khỏi Combined/Financial-only nếu FY mới nhất đã usable thiếu model hợp lệ hoặc ngày
quyết định sớm hơn cutoff. Bộ test M3 hiện có 43 test đạt. Trạng thái artifact local và gate đầu vào tài chính
được ghi trong [báo cáo thực hiện](../REPORT_BACKTEST.md).

**Chấp nhận đầu vào ngày 04/11/2026.** Owner duyệt dùng snapshot Indicators v1 theo cùng cách B v4 cho B-PIT,
gồm VCG FY2023 và SBT FY2024. Audit PDF/revision được lưu làm disclosure về giới hạn dữ liệu. Các kiểm tra
Q-date, cutoff và audit artifact tiếp tục áp dụng. Artifact local đã build và được kiểm tra trong
[báo cáo thực hiện](../REPORT_BACKTEST.md), bước tiếp theo là pin vào config.

## Tóm tắt

Methodology đã khóa, code và config đã sync, 35 test M3 pass. **Phần duy nhất chưa làm được là chạy trên dữ liệu thật:**
`data/` (bundle v4, indicators, availability, C8) không nằm trong git nên các bước 1–5 bên dưới phải chạy trên máy có
dữ liệu. Config đang ở `READY_TO_LOCK_AFTER_BPIT`: `run_m3.py` chỉ cho `--targets-only` cho tới khi B-PIT được build,
pin và config chuyển sang `LOCKED`.

## Đã làm trong commit này

| Hạng mục | Thay đổi | Tệp |
|---|---|---|
| ADR | D-M3-01 ghi toàn bộ quyết định 02/11 + R1–R8 | `docs/DECISIONS.md` |
| Config | `financial_rule = not_weakest`, `costs_bps_one_way = [0]`, `segment_end_dates`, `financial_pit` (chờ pin), status `READY_TO_LOCK_AFTER_BPIT` | `configs/experiments/m3_strategy_v1.json` |
| B-PIT (R1, R2) | Module fit/assign theo cutoff, thứ tự cụm đóng băng; script build + audit không rò rỉ + ARI so với B v4 | `src/delta_t1/m3/bpit.py`, `scripts/build_financial_pit_clusters.py` |
| Ranh giới đoạn (R3) | Không thực thi quyết định có phiên giao dịch sau `segment_end_date`, ghi `NOT_EXECUTED_SEGMENT_END`; định giá cuối tại phiên cuối trong đoạn; không đọc giá ngoài đoạn | `scripts/run_m3.py` |
| N_min (R4) | Loại `FINANCIAL_CRITERIA_MISSING` trước, rồi mới kiểm tra N_min và tính top 30% trên cùng N | `src/delta_t1/m3/strategies.py` |
| Trần/sàn (R5) | Thiếu dữ liệu trần/sàn → lệnh thất bại, cờ `LIMIT_DATA_MISSING` trong ledger và metrics | `src/delta_t1/m3/prices.py`, `scripts/run_m3.py` |
| Audit (R6) | `universe_audit_<strategy>.csv` cho mọi run; manifest có `git_commit`, `git_dirty`, `inputs_sha256`, `financial_source`, ranh giới đoạn | `scripts/run_m3.py` |
| Độ cũ | `stale_months` đọc từ config | `src/delta_t1/m3/universe.py` |
| Feasibility (R8) | Đọc B-PIT nếu đã pin; thêm số đếm theo đúng config chính thức (sau khi loại thiếu FC) | `scripts/m3_feasibility_variants.py` |
| Tên lý do | `FINANCIAL_NOT_IN_LEADING_CLUSTER` → `FINANCIAL_NOT_IN_ALLOWED_CLUSTER` (đúng nghĩa với `not_weakest`) | `universe.py` |
| Khác | Chặn chia cho 0 ở Equal-weight/Momentum-only (`NO_CANDIDATES`); test dashboard legacy tự skip vì `m3_dashboard.py` đã xóa | `strategies.py`, `tests/test_m3_dashboard.py` |

Kiểm thử: `tests/unit/test_m3_engine.py` (26) + `tests/unit/test_m3_readiness.py` (9, mới) đều pass. Các test M1/M2 khác
cần dữ liệu local nên không chạy được trên máy không có `data/`; commit này không chạm tới chúng.

## Các bước chạy (trên máy có `data/`)

Chạy từ thư mục gốc repo, Python 3.12 với `requirements-research.lock.txt` (cần numpy, scikit-learn).

### Bước 1 — Build B-PIT

```text
python scripts/build_financial_pit_clusters.py
```

Kết quả: `data/financial/b_pit_v1/bpit-<sha16>/` gồm `labels.csv`, `models.json`, `audit.json`, `manifest.json`, và in ra
`artifact` + `labels_sha256`.

Cần kiểm tra trước khi đi tiếp:

- Script tự dừng nếu có báo cáo được fit sau cutoff (`audit.status` phải là `PASS`).
- Dòng in ra cho từng năm: FY2016–FY2021 phải có `cutoff` = phiên đầu sau 30/06 năm sau, `assigned 0`, và **ARI so
  với B v4 ≈ 1,0** (cùng dữ liệu, cùng công thức). Nếu ARI thấp rõ rệt ở các năm này → dừng, báo lại (công thức
  chưa khớp B v4).
- FY2022–FY2025: `cutoff` = 30/04 năm sau, `assigned` khoảng 9–15% số mã; ARI dưới 1 là bình thường.
- `cluster_order` mỗi năm có đủ 3 cụm.
- Năm tài chính mới nhất (thường FY2025) có thể in `skipped` vì báo cáo chưa nằm trong lịch giá (CALENDAR_PENDING);
  không quyết định nào trong Development/Holdout dùng năm này nên không ảnh hưởng.

Đã chạy thử toàn bộ chuỗi build B-PIT → feasibility → targets-only → full run trên dữ liệu giả lập (60 mã, 2019–2025):
ARI các năm FY < 2022 = 1,0; development 60/59/1 (quyết định/thực thi/không thực thi), holdout 24/23/1; ngày NAV cuối
đúng ranh giới; số dòng audit khớp `candidates`; cờ `LIMIT_DATA_MISSING` xuất hiện đúng mã bị thiếu dữ liệu trần/sàn.
Đây chỉ là kiểm tra luồng, không phải kết quả.

### Bước 2 — Pin B-PIT vào config

Sửa `configs/experiments/m3_strategy_v1.json`:

```json
"financial_pit": {"artifact": "data/financial/b_pit_v1/bpit-<sha16>", "labels_sha256": "<giá trị in ra>"}
```

Giữ nguyên status `READY_TO_LOCK_AFTER_BPIT`. Commit thay đổi config này.

### Bước 3 — Đếm lại feasibility với B-PIT (không có lợi suất)

```text
python scripts/m3_feasibility_variants.py
```

Đọc dòng `official config (after FINANCIAL_CRITERIA_MISSING)`. Mốc so sánh trên B v4 (Va, trước khi loại thiếu FC):
Development trung vị 26 ứng viên, tối thiểu 3, **13/60 tháng dưới 10**; Holdout trung vị 40, 0/24 tháng dưới 10.

**Cổng quyết định:** nếu `universe_too_small` ở Development tăng rõ (ví dụ trên ~20/60 tháng), báo owner/mentor chốt
lại N_min hoặc Q5 **ngay tại đây**, trước khi có bất kỳ con số lợi suất nào. Không chỉnh rule sau khi đã xem return.

Đối chứng M2 K=2 (R7): số ứng viên lấy từ `python scripts/m3_stage0.py` (cột `m2_candidates`), không backtest.

### Bước 4 — Targets-only cho hai đoạn

```text
python scripts/run_m3.py --segment development --targets-only
python scripts/run_m3.py --segment holdout --targets-only
```

Kiểm tra trong `data/experiments/m3/<segment>/<run_id>/`:

- `manifest.json`: `financial_source = B_PIT`, `b_pit_labels_sha256` khớp config, `git_dirty = false`.
- `counts`: development 60 quyết định, 59 executed, 1 `not_executed_segment_end` (29/12/2023); holdout 24 quyết định,
  23 executed, 1 `not_executed_segment_end` (31/12/2025).
- Với mỗi kỳ: số dòng `in_candidate_universe = True` trong `universe_audit_<strategy>.csv` bằng cột `candidates`
  trong `targets_<strategy>.csv`.
- Tỷ lệ lý do loại (đặc biệt `FINANCIAL_SECTOR_NO_B`, `FINANCIAL_CRITERIA_MISSING`) hợp lý, không có lý do lạ.

### Bước 5 — Khóa config và chạy backtest

1. Đổi `"status": "LOCKED"` trong config, commit, ghi lại `config_sha256` (sha256 của file config).
2. Chạy Development, kiểm tra, seal (lưu thư mục run + manifest, không sửa):

   ```text
   python scripts/run_m3.py --segment development
   ```

3. Chỉ sau khi Development đã seal, chạy Holdout bằng đúng config/commit đó:

   ```text
   python scripts/run_m3.py --segment holdout
   ```

Kiểm tra sau mỗi run:

- `metrics.json`: `limit_data_missing` của mỗi strategy. Nếu khác 0 nhiều, xem `trade_ledger_*.csv` cột `flag` — thiếu
  dữ liệu trần/sàn ở C8 cho mã/ngày đó.
- `nav_*.csv` có ngày cuối = 2023-12-29 (development) hoặc 2025-12-31 (holdout); không có ngày nào sau ranh giới.
- Không có `sharpe_rf0` ở development/holdout (Sharpe chỉ ở Final).
- Khi báo cáo: không nối NAV development và holdout thành một chuỗi (tháng 1/2024 không thuộc đoạn nào); báo số tháng
  `UNIVERSE_TOO_SMALL` cạnh mọi chỉ số lợi suất của Combined/Market-only/Financial-only.

## Rủi ro đã biết

- **Combined đứng yên một phần thời gian:** với B v4, khoảng 13/60 tháng development dưới 10 ứng viên → chỉ giữ/bán.
  Chênh lệch Combined so với Market-only có thể một phần do quy tắc này.
- **B kém ổn định** (độ ổn định lấy mẫu con 0,50): nên báo cáo ARI B-PIT so với B v4 theo năm (`audit.json`) và độ
  trùng thành viên cụm "không yếu nhất" giữa các năm.
- **B-PIT chỉ khác B v4 ở FY ≥ 2022** (chủ yếu ảnh hưởng Holdout); với FY < 2022 hai bản trùng nhau theo thiết kế.
- **Final Evaluation** chưa có trong config: chỉ thêm `segments.final` + `segment_end_dates.final` sau readiness audit
  dữ liệu 2026 (Q16).
