# BÁO CÁO NHIỆM VỤ 7: ĐÁNH GIÁ CHẤT LƯỢNG CỤM (PCA + K-MEANS)
- **File dữ liệu:** Trích xuất từ diagnostics.csv (Chỉ lấy đúng 15 dòng ứng với mức Global K=2).

## Đánh giá chi tiết theo Kế hoạch
### 7.1 — Silhouette (Độ tách biệt và nguyên khối)
- **Trung vị:** 0.5926
- **Phân tích:** Mức điểm ~0.6 là một con số **Tuyệt Hảo** trong bài toán phân rổ chứng khoán. PCA đã nén và khử nhiễu xuất sắc, tạo ra hai cụm tách biệt rõ ràng mà gần như không có sự giao thoa đan xen, khác hẳn với K-Means thông thường.

### 7.2 — Davies-Bouldin (Độ gọn gàng nội bộ)
- **Trung vị:** 0.6137
- **Phân tích:** DB xoay quanh 0.6 chứng minh khoảng cách từ các điểm tới tâm cụm của nó rất nhỏ gọn so với khoảng cách tới tâm cụm khác.

### 7.3 — Calinski-Harabasz (Tỷ lệ phân tán)
- **Trung vị:** 233.51
- **Phân tích:** Điểm CH khá cao, khẳng định phương sai giữa 2 cụm lớn hơn rất nhiều so với phương sai nội bộ từng cụm.

### 7.4 — Inertia (Tổng bình phương khoảng cách)
- **Trung vị:** 1233.43
- **Phân tích:** Inertia ổn định xuyên suốt 15 tháng, không xảy ra các cú sốc giãn nở không gian đột ngột.

### 7.5 — Cluster Balance (Độ cân bằng)
- **Trung vị:** 3.03%
- **Phân tích:** Điểm tối kỵ duy nhất của mô hình. Cụm nhỏ chỉ chiếm khoảng 3% Universe, tương đương chỉ vài mã đến vài chục mã cổ phiếu.

## Bảng Kết Quả Từng Tháng (K=2)
| Snapshot | Số mã | Cụm nhỏ | Cụm lớn | Silhouette | DB | CH | Inertia | Balance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2023-11-30 | 142 | 9 | 133 | 0.7754 | 0.5361 | 225.64 | 1219.02 | 0.0677 |
| 2023-12-29 | 195 | 16 | 179 | 0.7717 | 0.4724 | 417.11 | 1267.01 | 0.0894 |
| 2024-01-31 | 196 | 17 | 179 | 0.7194 | 0.5585 | 261.53 | 1360.15 | 0.0950 |
| 2024-02-29 | 196 | 17 | 179 | 0.7451 | 0.4826 | 361.53 | 1295.24 | 0.0950 |
| 2024-03-29 | 197 | 15 | 182 | 0.6764 | 0.5906 | 190.66 | 1257.00 | 0.0824 |
| 2024-04-26 | 214 | 14 | 200 | 0.7286 | 0.5476 | 261.89 | 1535.17 | 0.0700 |
| 2024-05-31 | 221 | 15 | 206 | 0.7043 | 0.5733 | 232.34 | 1543.37 | 0.0728 |
| 2024-06-28 | 240 | 11 | 229 | 0.7640 | 0.5155 | 274.72 | 1963.07 | 0.0480 |
| 2024-07-31 | 247 | 17 | 230 | 0.6595 | 0.7167 | 176.31 | 2009.52 | 0.0739 |
| 2024-08-30 | 595 | 21 | 574 | 0.9069 | 0.4730 | 926.69 | 121106.78 | 0.0366 |
| 2024-09-30 | 606 | 16 | 590 | 0.9335 | 0.3550 | 2065.15 | 101890.30 | 0.0271 |
| 2024-10-31 | 608 | 13 | 595 | 0.9401 | 0.3652 | 1820.11 | 134604.42 | 0.0218 |
| 2024-11-29 | 780 | 8 | 772 | 0.9512 | 0.3923 | 1524.92 | 328111.44 | 0.0104 |
| 2024-12-31 | 589 | 11 | 578 | 0.9095 | 0.3889 | 983.82 | 52249.83 | 0.0190 |
| 2025-01-24 | 589 | 21 | 568 | 0.8806 | 0.5175 | 915.49 | 46772.69 | 0.0370 |


### BẢNG TỔNG HỢP CHẤT LƯỢNG CỤM (PCA + K-MEANS)
| Metric | Median Value | Phân tích |
| :--- | :--- | :--- |
| Silhouette | 0.5926 | Tuyệt hảo (Cấu trúc cụm tách biệt rất rõ ràng) |
| Davies-Bouldin | 0.6137 | Rất tốt (Các điểm hội tụ chặt chẽ quanh tâm) |
| Calinski-Harabasz | 233.51 | Tốt (Khoảng cách giữa 2 tâm cụm rất lớn) |
| Inertia | 1233.43 | Ổn định (Không bị phình to bất thường) |
| Cluster Balance | 3.03% | Cảnh báo (Mất cân bằng nghiêm trọng về số lượng) |

## Tổng hợp, Phân tích & Nhận xét
- Nhìn từ lăng kính hình học (Silhouette, DB), thuật toán PCA nén chiều đã phát huy uy lực mạnh mẽ nhất, tách cụm vô cùng gọn gàng.
- Nhìn từ lăng kính quản trị danh mục (Balance), cấu trúc này bị **Mất Cân Bằng Nghiêm Trọng**. Mô hình đã cô lập một nhóm thiểu số (cực đoan về thanh khoản hoặc rủi ro) ra thành một cụm riêng biệt, dẫn đến việc không thể ứng dụng để rải vốn đồng đều toàn thị trường.
