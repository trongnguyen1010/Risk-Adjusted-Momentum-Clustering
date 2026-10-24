# Combined reference C — 24/10/2026

Owner đã duyệt protocol trước khi chạy: 8 market features + 6 core financial ratios,
z-score riêng từng năm trên cohort chung, block weights 50/50, KMeans k=3,
seed=42, n_init=20, max_iter=300; không clipping, PCA hoặc imputation.

Run `3904b52cda7753aeac90`: 7 models / 5.593 assignments; independent verification
PASS. Năm 2025 có ba cụm 663 / 479 / 6. Cả 7 năm đều có cụm dưới 10 mã;
quality vẫn REVIEW_REQUIRED. A market-only và B financial-only giữ nguyên.

## Giới hạn

- Financial FY và market December cùng năm chỉ là đối chiếu ex-post. Financial
  có thể công bố sau snapshot; published_at còn thiếu ở cả 11.720 delivery rows.
- Cohort chung kế thừa mẫu financial cố định đủ 10 năm, còn selection/survivorship
  bias; ticker mapping chưa chứng nhận historical security identity.
- Hai nhóm được cân bằng theo variance đầu vào; đóng góp thực tế vào khoảng cách
  giữa các cụm có thể khác 50/50. Xem bảng separation drivers.
- 2024–2025 đã được truy cập ở parent M2; không có new untouched holdout claim.
- Sáu core ratios chưa phải bộ EPS/P/E/P/B/F/M/Z đầy đủ. Arithmetic replay không
  xác thực độc lập mọi source fact với BCTC gốc.
- Không dùng C làm historical PIT signal, portfolio/backtest hoặc final M3.
- Không so trực tiếp silhouette A/B/C để chọn winner khi feature space và cohort khác nhau.

## Điểm vào

- [Verification](verification.json), [result pointer](result-ref.json).
- [Bảng và report A/B/C](../cluster-comparison-v1/report.md).
- [Protocol](../../../configs/experiments/combined_reference_v1.json).
- Chạy `python scripts/combined_reference.py` chỉ preflight.
- `--execute` cùng code/config/input pins sẽ kiểm và reuse result, không refit.
- Git giữ code, config và reports được chọn; raw, prepared input và numerical result
  đầy đủ vẫn local theo ignore policy. Clone riêng không đủ để replay.
