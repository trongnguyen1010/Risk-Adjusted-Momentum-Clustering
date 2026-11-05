# DELTA — dữ liệu và phân cụm cổ phiếu Việt Nam

Phân cụm cổ phiếu Việt Nam theo đặc trưng thị trường (A) và tài chính (B), rồi backtest danh mục chọn từ hai hệ cụm (M3).
Lịch sử từng lượt làm việc nằm ở [CHANGELOG](CHANGELOG.md); trạng thái hiện hành ở [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md).

## Hướng chính thức (D-DIR-01, 26/10/2026)

- **Phân cụm thị trường (A):** mô hình A của bundle web v4 — 9 đặc trưng, lọc thanh khoản nhẹ, log + cắt đuôi + z-score,
  K-Means k=3 (chọn bằng `clustering_rework_v2`; chọn lại chỉ trên 2019–2023 vẫn k=3).
- **Phân cụm tài chính (B):** mô hình B v4 (9 chỉ số D-IND-01, k=3). M3 dùng bản point-in-time
  [B-PIT](data/financial/b_pit_v1/bpit-4a9d2e87f0de84ec/manifest.json) (ADR D-M3-01).
- **M3:** methodology khóa trong [KE_HOACH_M3_SCHEMA_GITHUB](docs/m3/KE_HOACH_M3_SCHEMA_GITHUB.md) và
  `configs/experiments/m3_strategy_v1.json`. Development và Holdout đã seal; Final Evaluation `NOT_READY` (chưa đủ dữ liệu 2026).
  Kết quả: [M3/outputs](M3/outputs/README.md), [báo cáo kỹ thuật](M3/reports/BAO_CAO_KY_THUAT_M3.md),
  [báo cáo backtest](docs/REPORT_BACKTEST.md).
- **LEGACY (chỉ đối chứng/tái lập):** bàn giao M2 K=2 trong `M2/`, web cũ `web/index.html|app.js|styles.css`.
  Bằng chứng so sánh: `artifacts/reports/m2-vs-rework-v1/report.md`.

## Cài đặt và lệnh chính

```powershell
python -m pip install -e ".[research]"
python scripts/run_m3.py --segment development --targets-only   # chọn danh mục, chưa tính lợi suất
python scripts/start_delta_terminal.py                          # web local đọc artifact A/B/C
python -m unittest discover -s tests -t tests                   # cần PYTHONPATH=src;tests
```

Bảng lệnh đầy đủ theo nhóm: [scripts/README.md](scripts/README.md). Notebook tái lập M3: `M3/notebooks/`.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `src/delta_t1/` | Package Python: `ingestion`, `features`, `indicators`, `clustering`, `evaluation`, `experiments`, `backtest`, `m3`, `product`, `reporting` |
| `scripts/` | Entry point dòng lệnh; `scripts/corporate_actions/` cho thu thập sự kiện doanh nghiệp |
| `configs/` | `data/` (crawl), `experiments/` (protocol, có hash), `features/`, `product/` |
| `tests/` | `unit/`, `integration/`, `regression/`, `fixtures/` |
| `docs/` | [START HERE](docs/README.md); `m3/`, `architecture/`, `reports/`, `research/`, `crawl/`, `plans/`, `presentation/` |
| `M3/` | Output M3 đã seal, notebook, báo cáo — **không di chuyển/sửa** (manifest ghi đường dẫn và SHA256) |
| `M2/` | Bàn giao M2 K=2 (LEGACY) — **không di chuyển** (`.gitattributes` và config ghim byte) |
| `artifacts/` | Evidence đã seal theo từng lượt — **không di chuyển** |
| `data/` | Dữ liệu local (phần lớn không commit); `data/financial/b_pit_v1/` được commit và ghim hash |
| `web/` | `backend/` (FastAPI), `frontend/` (Next.js), `monitor/` |

## Ranh giới nghiên cứu

Không chọn `k`/thuật toán bằng return, Sharpe hay ROI; Sharpe chỉ ở Final Evaluation. Chỉ dùng dữ liệu có
`usable_from_date <= decision_date`; không forward-fill giá. Chi tiết: [AGENTS](AGENTS.md), [DECISIONS](docs/DECISIONS.md),
[ROADMAP](docs/ROADMAP.md). Hướng dẫn đóng góp: [CONTRIBUTING](CONTRIBUTING.md).
