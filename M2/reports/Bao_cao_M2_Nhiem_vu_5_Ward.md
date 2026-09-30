# BÁO CÁO NHIỆM VỤ 5: HUẤN LUYỆN WARD HIERARCHICAL CLUSTERING

**Nhánh thực hiện:** Thuật toán Ward
**Phạm vi dữ liệu:** 15 Snapshots thuộc tập Development (2023-11-30 đến 2025-01-24)
**Cấu hình thực nghiệm:** `m2_ward_market_only_v1.json`
**Trạng thái:** Hoàn tất 100%

---

## 1. Mục tiêu và Quy trình Thực thi
- **Mục tiêu:** Thực thi pipeline huấn luyện thuật toán Ward Hierarchical Clustering (Global K=2) dọc theo trục thời gian 15 tháng nhằm tách bóc nhóm cổ phiếu Bluechips (động lượng cao, thanh khoản khổng lồ) khỏi phần còn lại của thị trường.
- **Quy trình chạy:** Hệ thống đã tự động duyệt qua 15 snapshots liên tiếp, load dữ liệu raw, thực hiện scale (chuẩn hóa), áp dụng hàm liên kết (linkage) và phân cụm (fcluster) mà không bị gián đoạn.

## 2. Kết quả Bàn giao (Artifacts)
Toàn bộ quá trình huấn luyện đã kết xuất thành công và lưu trữ các Artifacts bất biến (immutable) tại thư mục `M2/artifacts/m2-task5-ward-v1/`. Cụ thể:

1. **`assignments.jsonl`:** Bảng ghi nhận nhãn phân cụm (Cluster ID) của từng mã cổ phiếu theo từng tháng. Kích thước $\approx 90,000$ records. Không có lỗi Null/NaN.
2. **`profiles.jsonl`:** Bảng chứa tọa độ trọng tâm (Centroids) của 2 cụm đại diện cho mỗi tháng, được lưu dưới dạng giá trị gốc (unscaled) để sẵn sàng cho phân tích kinh tế.
3. **`diagnostics.jsonl`:** Ghi nhận các chỉ số chất lượng nội bộ (Silhouette, Davies-Bouldin, Calinski-Harabasz) ở các giá trị K khác nhau, tạo tiền đề tính toán cho Nhiệm vụ 7.
4. **`stability.jsonl`:** Ghi nhận tỷ lệ duy trì cụm, di cư và chỉ số ARI qua từng tháng, là dữ liệu đầu vào trực tiếp cho Nhiệm vụ 9.

---

## 3. Phân tích Kỹ thuật Chuyên sâu (Technical Analysis)

Quá trình huấn luyện không chỉ là "chạy code", mà bao gồm các quyết định cấu hình mang tính chiến lược:

### 3.1. Phân tích Cấu hình Xử lý Dữ liệu Tiền kỳ
- **Giữ nguyên Outliers (No Clipping):** Quyết định tắt `clipping` là tối quan trọng. Trong tài chính, các mã có thanh khoản đột biến không phải là "nhiễu" mà chính là "siêu cổ phiếu" (Bluechips) cần tìm. Nếu cắt ngọn, mô hình sẽ mất đi điểm neo này.
- **Chuẩn hóa `robust_per_snapshot`:** Việc dùng Robust Scaler (dựa trên trung vị) thay cho Standard Scaler giúp bảo vệ phần đông thị trường không bị bóp méo bởi các siêu cổ phiếu nói trên, đồng thời xử lý gọn gàng lạm phát trượt giá theo thời gian.

### 3.2. Lựa chọn Thuật toán Ward
Khác với Single Linkage (dễ bị tạo chuỗi - chaining) hay Complete Linkage (quá nhạy cảm với ngoại lai), phương pháp **Ward** cố gắng thu nhỏ phương sai nội cụm (Within-Cluster Variance) ở mỗi bước gộp. Điều này ép thuật toán phải tạo ra những cụm có dạng hình cầu (spherical) và cấu trúc chặt chẽ, rất phù hợp với kỳ vọng tìm kiếm một nhóm nhỏ cổ phiếu ưu tú. Ngoài ra, Ward có tính xác định (deterministic), đảm bảo chạy lại 100 lần kết quả vẫn giống nhau y hệt.

### 3.3. Xử lý Nút thắt Cổ chai Tài nguyên (O(N^2))
Với $\approx 6000$ mã mỗi tháng, ma trận khoảng cách $N \times N$ là rất lớn. Việc ghi toàn bộ Linkage Tree ra ổ cứng cho 15 tháng sẽ gây quá tải repository. Do đó, mã nguồn `hierarchical.py` đã áp dụng chiến lược tính toán In-memory: Giải mã trực tiếp cây liên kết thành nhãn cụm (Assignments) trên RAM và giải phóng bộ nhớ lập tức. Kết quả là pipeline chạy qua 15 tháng cực kỳ mượt mà, không gặp hiện tượng tràn RAM (Memory Leak).

---

## 4. Tình trạng và Khuyến nghị
- Toàn bộ dữ liệu của nhánh Ward đã được khóa (Frozen) và bàn giao thành công.
- Dữ liệu ở trạng thái sạch và cấu trúc chuẩn, **đáp ứng 100% điều kiện đầu vào** để bắt đầu triển khai ngay **Nhiệm vụ 7, 8 và 9**.
- Quá trình chạy nhánh Ward không phát hiện lỗi bất thường nào cần xử lý thêm.
