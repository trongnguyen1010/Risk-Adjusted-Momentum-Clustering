# Báo cáo M2 - Nhiệm vụ 8: Hồ sơ cụm (PCA + K-Means)

## 1. Trực quan hóa Hồ sơ Cụm

### Biểu đồ 8.1: Radar Chart
![Radar Chart](../artifacts/m2-evaluation-pca-kmeans/radar_chart.png)

### Biểu đồ 8.2: Heatmap 2D
![Heatmap](../artifacts/m2-evaluation-pca-kmeans/heatmap.png)

## 2. Khung kết luận 3 phần bắt buộc (Profiling Rubrics)

### Phần A (Chân dung kinh tế):
- **Cụm 0 (Cluster 0):** Đại diện cho nhóm cổ phiếu "Cô lập/Ngoại lai" (Outliers). Nhóm này có mức biến động (Volatility) cực kỳ cao và thanh khoản/động lượng có xu hướng lệch lạc mạnh. Đây là các mã cờ bạc, thanh khoản nổ đột biến hoặc rớt thảm hại.
- **Cụm 1 (Cluster 1):** Đại diện cho phần lớn thị trường ("Thị trường chung"). Nhóm này có mức độ rủi ro (Beta, Volatility, MDD) ở mức bình quân, thanh khoản ổn định, đại diện cho nhóm cổ phiếu phổ thông.

### Phần B (Động lực phân tách chính):
Dựa vào Bảng Delta và Radar Chart, **động lực phân tách số 1 (Primary Driver)** là cụm rủi ro/biến động: **vol_63** và **mdd_126**. Thuật toán PCA + K-Means bị chi phối mạnh mẽ bởi các độ lệch cực đoan trong biến động giá. Thay vì chia thị trường thành "Tốt/Xấu" hay "Thanh khoản cao/Thấp", nó lại chia thành "Bình thường" và "Cực đoan rủi ro".

### Phần C (Tính khả thi cho M3):
Mặc dù Cụm 0 có những đặc tính nổi bật về mặt biến động, nhưng vì số lượng mã quá ít (dưới 5%) và thanh khoản thất thường, việc giải ngân thực tế (Backtest M3) vào cụm này sẽ gặp rào cản rất lớn về trượt giá (slippage) và rủi ro thanh khoản (liquidity risk). Danh mục M3 nên tập trung khai thác tín hiệu bên trong Cụm 1 (Thị trường chung) để đảm bảo an toàn vốn.
