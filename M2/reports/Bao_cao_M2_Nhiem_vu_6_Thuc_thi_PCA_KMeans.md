# Báo cáo Nhiệm vụ 6: Thực thi phương pháp PCA + K-Means

## 1. Giới thiệu
Nhiệm vụ 6 thực hiện phương pháp gộp cụm PCA + K-Means trên 15 tháng (từ 11/2023 đến 01/2025). Phương pháp này giúp giảm chiều từ 8 đặc trưng tài chính ban đầu xuống số lượng thành phần chính (Principal Components) tối thiểu để giữ lại ít nhất 90% phương sai, sau đó thực thi phân cụm K-Means.

## 2. Thông số thiết lập
- **Không gian đặc trưng ban đầu:** 8 features (mom_21, mom_63, mom_126, mom_252, ol_63, mdd_126, eta_126, liquidity_21).
- **Chuẩn hóa dữ liệu:** Robust Scaler (theo từng snapshot).
- **Thuật toán giảm chiều:** Principal Component Analysis (PCA).
- **Thuật toán phân cụm:** K-Means với Global K = 2.

## 3. Kết quả thực thi (Freeze Component)
Dựa theo protocol, số lượng components được chọn nhỏ nhất thỏa mãn cumulative explained variance $\geq$ 90% là **4 components**. 

Thông số PCA này đã được **đóng băng (freeze)** cho toàn bộ 15 tháng trong tập development để đảm bảo tính đồng nhất của không gian phân cụm qua thời gian.

## 4. Dữ liệu bàn giao (Artifacts)
Pipeline đã xuất thành công các artifacts chuẩn hóa vào thư mục M2/artifacts/m2-task6-pca-kmeans-v1/:
- ssignments.csv / .jsonl: Chứa nhãn cụm của từng mã cổ phiếu theo tháng.
- profiles.csv / .jsonl: Chứa hồ sơ đặc trưng của từng cụm (tính trên 8 tính năng gốc).
- diagnostics.csv / .jsonl: Chứa điểm số chất lượng (Silhouette, DB, CH, Inertia, Balance) của từng tháng.
- stability.csv / .jsonl & 	ransitions.csv / .jsonl: Chứa dữ liệu dịch chuyển cụm theo thời gian.

Các mô hình (PCA Transformers & K-Means Fitted Models) của 15 tháng cũng đã được lưu đầy đủ dưới dạng JSON tại M2/models/pca_kmeans/.
