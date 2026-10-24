# Báo cáo tổng kết M2 market và bàn giao tích hợp

Cập nhật 23/10/2026 sau integration với financial. Bản mô tả trước đây có các số
0,292/0,274 và câu chuyện Leader/Lagging không khớp current artifacts; không dùng
chúng để nghiệm thu. Git giữ bản trước để truy vết. Không thay numerical results.

## Phạm vi và protocol

C8 V2 có 1.522 candidates; tại 31/12/2025 có 1.410 market-ready, historical identity
và research readiness đều false. Dữ liệu giá nền 2016–2025 không đồng nghĩa mọi mã
đủ lịch sử. Development60tháng2019–2023, holdout24tháng2024–2025, membership theo
snapshot; tối thiểu100mã, không dùng fixedterminaluniverse.

KMeans Baseline, K=2, seed42, n_init10, max_iter300, robust scaling mỗi snapshot.
Tám feature: mom21/63/126/252, vol63, mdd126, beta126, liquidity21 (tên executable
trong config có dấu gạch dưới). Không tự coi liquidity raw VND là log input.
GlobalK và so sánh method chỉ development, không dùng return/Sharpe.

## Kết quả actual

| Chỉ số | Development | Holdout |
|---|---:|---:|
| Snapshots | 60 | 24 |
| Assignments | 45.646 | 30.155 |
| Median silhouette | 0,940837 | 0,949324 |
| Median Davies–Bouldin | 0,403127 | 0,398445 |
| Median cluster balance | 0,020996 | 0,022626 |
| Cụm nhỏ nhất: min / median / max | 2 / 14 / 32 | 22 / 28 / 41 |
| Tháng có cụm dưới10mã | 19 | 0 |

Nguồn: `M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv`,
`M2/artifacts/m2-evaluation-v2/methodology_comparison.csv` và
`M2/artifacts/m2-final-holdout/quality_summary.csv`.
PCA median silhouette0,946855; gap với baseline0,006018. Đây là số đo cấu trúc cụm,
không phải hiệu quả đầu tư. Balance nhỏ và silhouette cao đòi review outliers;
chưa đủ bằng chứng khẳng định hai nhóm kinh tế Leader/Lagging hữu ích.

## Bàn giao và giới hạn

Handoff hiện hành giữ75.801labels/84snapshots,174profiles gồm168monthly+6summary,
82internaltransitionpairs (59dev+23holdout, không có cặp qua ranh giới).
Đây là staticindependentmonthlyclustering và diagnosticstability, không DynamicClustering.
Holdout cũng fit tại từng snapshot theo protocol đã freeze, không phải dự đoán bằng
một model development cố định. Không tạo historicalidentity hoặc financialPITclaim.

Verifier tích hợp mới: `python scripts/verify_market_financial_integration.py --publish`.
Nó kiểmexacthash/sourceeligibility/labels/nearestcentroid, không fit hoặc backtest;
xuất referencehandoff tại `M2/artifacts/market-financial-integration-v1/`.
Các scriptsTask12/13V1 còn giữ để truy vết, không phải current84reproductionworkflow.
Source model paths chuẩn là `final_selected_model_v2` cho development và `holdout`
cho24tháng tiếp theo; giữ assembled84 để tương thích và pin đúng LF/CRLF.

Financial baseline giữ1.172symbols×annual2016–2025 và sáucoreratios; không tự ghép
vào támfeaturemarket. Tại cuối2025 giao ticker market-ready là1.148; historicaljoin
phải cócrosswalkvàpublication/vintages trước PIT/M3. Quality REVIEW_REQUIRED,
strictPIT/finalM3chưa nghiệm thu. Không sửaK/scaler hoặc refit trong integration.
