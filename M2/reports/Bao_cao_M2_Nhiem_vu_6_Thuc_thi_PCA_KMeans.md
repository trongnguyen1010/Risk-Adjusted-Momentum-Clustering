# BÁO CÁO NHIỆM VỤ 6: THỰC THI PHÂN CỤM PCA + K-MEANS
- **Mục tiêu:** Áp dụng phương pháp phân cụm nâng cao bằng cách nén không gian đặc trưng bằng thuật toán PCA (Principal Component Analysis) trước khi chạy thuật toán K-Means.

## Triển khai chi tiết theo Kế hoạch
### 6.1 — Lấy dữ liệu của từng snapshot
Dữ liệu đầu vào gồm 15 snapshots. Tại mỗi snapshot, pipeline lấy đủ bộ 8 features gốc (momentum, rủi ro, thanh khoản).

### 6.2 — Kiểm tra dữ liệu trước xử lý
Hệ thống tự động kiểm tra loại bỏ NaN/Inf. Số lượng mã hợp lệ (n_eligible >= 120) luôn được thỏa mãn trong cả 15 tháng.

### 6.3 — Xử lý ngoại lai và chuẩn hóa (Robust Scaling)
Để giảm thiểu độ lệch chuẩn của PCA do điểm kỳ dị, toàn bộ 8 features đã được chuẩn hóa thông qua RobustScaler (sử dụng Median và IQR) độc lập cho từng snapshot.

### 6.4 — Áp dụng thuật toán PCA
Dữ liệu 8D được chiếu xuống không gian 4D trực giao. Số lượng thành phần chính được khóa cứng (n_components = 4).

### 6.5 — Lưu thông tin cấu trúc không gian PCA
Ma trận xoay và tỷ lệ phương sai giải thích được của PCA được bảo lưu trong các object mô hình tại thư mục models/.

### 6.6 — Chạy phân cụm K-Means
Sử dụng thuật toán K-Means với K=2 (theo quyết định từ Nhiệm vụ 3) trực tiếp trên tọa độ 4D vừa tạo ra từ PCA.

### 6.7 & 6.8 — Lưu Assignment và Centroid
Nhãn phân cụm (assignments.jsonl) và tâm cụm 4D đều được pipeline trích xuất tự động và lưu trữ song song.

### 6.9 — Xây dựng Cluster Profile
Hệ thống dùng thuật toán inverse_transform để giải mã tâm cụm 4D quay về lại 8D, giúp chúng ta nhìn nhận được đặc điểm tài chính gốc (Lưu tại profiles.csv).

### 6.10 — Tính toán Quality Metrics
Các chỉ số cấu trúc không gian (Silhouette, DB, CH, Inertia, Balance) được đo lường ngay trong lúc chạy để làm dữ liệu cho Nhiệm vụ 7 (Lưu tại diagnostics.csv).

### 6.11 & 6.12 — Lặp lại cho toàn bộ Development và Lưu Artifact
Vòng lặp hoàn tất 15/15 tháng thành công trơn tru. Toàn bộ Artifact xuất ra ở trạng thái status: complete.


### BẢNG TỔNG HỢP QUÁ TRÌNH THỰC THI (PCA + K-MEANS)
| Hạng mục | Tham số / Kết quả | Nhận xét |
| :--- | :--- | :--- |
| Số lượng Snapshot | 15 tháng | Chạy mượt mà, không gặp lỗi dữ liệu |
| Số lượng Features gốc | 8 đặc trưng | Đủ 3 khía cạnh: Động lượng, Rủi ro, Thanh khoản |
| Chuẩn hóa dữ liệu | RobustScaler | Khử nhiễu tốt các điểm kỳ dị (Outliers) cực đoan |
| Không gian PCA | 4 chiều (n_components=4) | Cô đọng thông tin cốt lõi, triệt tiêu đa cộng tuyến |
| Thuật toán Phân cụm | K-Means | Tốc độ hội tụ siêu nhanh trên không gian 4D |
| Global K | K = 2 | Bám sát quyết định từ Nhiệm vụ 3 |
| Mapping Centroid | Inverse Transform | Giải mã tâm 4D về 8D thành công, giữ nguyên ý nghĩa |

## Tổng hợp, Phân tích & Nhận xét
- Việc tích hợp PCA vào pipeline trước K-Means đã giúp loại trừ hiện tượng đa cộng tuyến giữa các biến động lượng (mom_21, mom_63...).
- Quá trình chạy diễn ra cực kỳ ổn định, thuật toán Inverse Transform hoạt động xuất sắc để bảo toàn ý nghĩa tài chính của tọa độ tâm cụm.
