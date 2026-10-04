# Báo cáo Nhiệm vụ 6 — PCA + K-Means

Nguồn model: `experiment-20261003T113748Z-acb3a2e7`. Bộ kiểm chứng/xuất lại: `m2-task6-pca-kmeans-v1`.
Bộ kết quả đã sửa được lưu tại đường dẫn v1 theo yêu cầu người dùng.
Fitted model được tái dùng và kiểm chứng, không huấn luyện lại.

## A — Thực thi và kiểm chứng
15/15 snapshot; universe 142–780 mã;
5.615 nhãn khớp dự đoán từ model, 30 profiles trên 8 feature gốc.
Global K=2; Robust Scaling độc lập; seed=42, n_init=10, max_iter=300.

## B — Quy tắc PCA đã kiểm chứng
Số chiều cố định 4 là max của số chiều tối thiểu đạt 90% trên từng development snapshot.
Phương sai giữ lại: median 96.8639%, min 93.6424%, max 99.8398%.
Không tùy ý đổi số chiều từng tháng và không sử dụng holdout.

## C — Bàn giao nhiệm vụ 7–9
Đủ assignments, PC1–PC4 scores, loadings, PCA diagnostics, scaler parameters,
13-cột cluster_profiles, quality diagnostics và ba temporal inputs aligned.
Model ở `M2/models/pca_kmeans/`; manifest kiểm tra checksum của toàn bộ bộ xuất.
Kết quả chỉ mô tả development market-only, không phải dynamic clustering hoặc bằng chứng sinh lợi.
