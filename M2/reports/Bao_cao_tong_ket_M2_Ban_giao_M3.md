# BÁO CÁO TỔNG KẾT MILESTONE M2 VÀ BÀN GIAO CHO MILESTONE M3
**Dự án:** Phân cụm động lượng điều chỉnh rủi ro thị trường chứng khoán Việt Nam (DELTA)  
**Tác giả:** Nhóm nghiên cứu Milestone M2  
**Phiên bản:** 2.0.0 (Chuẩn hóa 84 Snapshots: 60 Development + 24 Holdout)  
**Ngày bàn giao:** 2026-10-23  
**Trạng thái:** OFFICIALLY_HANDED_OFF (Đã đóng gói thành công gói bàn giao chuẩn hóa)

---

## CHƯƠNG 1 — TỔNG QUAN PHƯƠNG PHÁP LUẬN VÀ PROTOCOL THỰC NGHIỆM

### 1.1. Bối cảnh và Mục tiêu M2
Milestone M2 thực hiện nghiên cứu phát hiện cấu trúc phân nhóm cổ phiếu thị trường chứng khoán Việt Nam tại từng thời điểm cuối tháng (snapshot) bằng các thuật toán học không giám sát (Unsupervised Clustering). Mục tiêu cốt lõi là kiểm định xem liệu cổ phiếu trên thị trường có tự nhiên phân hóa thành các nhóm mang đặc trưng động lượng - rủi ro - thanh khoản tương đồng hay không, và cấu trúc này có bền vững qua thời gian để làm tiền đề cho chiến lược đầu tư tại Milestone M3 hay không.

### 1.2. Không gian 8 đặc trưng chuẩn hóa M2 V2
Nghiên cứu sử dụng nhất quán 8 đặc trưng thị trường sạch kế thừa từ Milestone M1 V2:
1. `mom_21`: Động lượng ngắn hạn ~1 tháng (21 ngày giao dịch).
2. `mom_63`: Động lượng trung hạn ~3 tháng (63 ngày giao dịch).
3. `mom_126`: Động lượng trung-dài hạn ~6 tháng (126 ngày giao dịch).
4. `mom_252`: Động lượng dài hạn ~12 tháng (252 ngày giao dịch).
5. `vol_63`: Biến động lợi suất hàng ngày 3 tháng (63 ngày giao dịch).
6. `mdd_126`: Mức giảm giá cực đại trong 6 tháng (126 ngày giao dịch).
7. `beta_126`: Hệ số Beta thị trường so với chỉ số VN-Index qua 6 tháng.
8. `liquidity_21`: Giá trị giao dịch trung bình khớp lệnh hàng ngày 1 tháng (log scale).

### 1.3. Quy tắc chuẩn hóa và lọc vũ trụ cổ phiếu theo Snapshot
- **Lọc Universe theo thời điểm (Point-in-Time Universe):** Tại mỗi thời điểm snapshot cuối tháng $t$, chỉ đưa vào phân cụm các cổ phiếu thỏa mãn tiêu chí `market_feature_ready_v2 = true` và quy mô snapshot đạt ngưỡng sàn $n_{\text{eligible}} \ge 100$ (tương đương chuẩn rổ VN100). Tuyệt đối không sử dụng danh mục cổ phiếu của thời điểm sau áp ngược về quá khứ (chống look-ahead bias).
- **Chuẩn hóa Robust Scaling per-snapshot:**
  $$x_{\text{scaled}} = \frac{x - \text{Median}}{\text{IQR}}$$
  Trong đó Median và IQR được tính độc lập trên chính các cổ phiếu đủ điều kiện của snapshot tháng đó. Mỗi tháng sở hữu một bộ scaler riêng, bảo toàn tính point-in-time độc lập.

### 1.4. Phân định ranh giới Development và Holdout
- **Giai đoạn Phát triển (Development Window):** 60 snapshots liên tục từ ngày `31/01/2019` đến `29/12/2023` (5 năm). Toàn bộ việc thử nghiệm số cụm $K$, so sánh thuật toán, tối ưu hóa tiền xử lý chỉ được diễn ra trong giai đoạn này.
- **Giai đoạn Kiểm định Ngoài mẫu (Final Holdout Window):** 24 snapshots liên tục từ ngày `31/01/2024` đến `31/12/2025` (2 năm). Bộ dữ liệu này được niêm phong tuyệt đối trong suốt quá trình phát triển mô hình.

---

## CHƯƠNG 2 — QUÁ TRÌNH LỰA CHỌN VÀ ĐÓNG BĂNG GLOBAL K

### 2.1. Khảo sát không gian siêu tham số $K$
Tại Nhiệm vụ 3, thuật toán K-Means được thực thi trên toàn bộ 60 snapshots giai đoạn Development với không gian số cụm $K \in \{2, 3, 4, 5, 6, 7, 8\}$ (tổng cộng 420 lượt huấn luyện mô hình độc lập).

### 2.2. Ma trận kết quả đánh giá chất lượng phân cụm
Chất lượng cụm được đánh giá qua 4 chỉ số không giám sát độc lập:
- **Silhouette Score:** Đo lường độ gắn kết nội cụm và độ tách biệt ngoại cụm (càng cao càng tốt).
- **Davies-Bouldin Index (DB):** Đo tỷ lệ phân tán nội cụm trên khoảng cách giữa các tâm cụm (càng thấp càng tốt).
- **Calinski-Harabasz Index (CH):** Tỷ số phân tán giữa các cụm so với nội cụm (càng cao càng tốt).
- **Cluster Balance:** Tỷ lệ kích thước cụm nhỏ nhất trên cụm lớn nhất.

**Bảng tổng hợp trung vị (Median Metrics) trên 60 development snapshots:**
- $K = 2$: Median Silhouette = **0.292**, Median DB = **1.354**, Median CH = **128.4**
- $K = 3$: Median Silhouette = 0.221, Median DB = 1.621, Median CH = 104.2
- $K = 4$: Median Silhouette = 0.185, Median DB = 1.782, Median CH = 91.6
- $K = 5..8$: Silhouette giảm dần về dưới 0.15, DB tăng trên 1.90.

### 2.3. Lập luận và Quyết định Đóng băng Global K = 2
Theo quy tắc lựa chọn đã freeze tại Protocol M2 (ưu tiên Silhouette cao nhất, DB thấp nhất làm tie-breaker, tuyệt đối không dùng return hay Sharpe):
- Cấu hình $K = 2$ vượt trội áp đảo tất cả các mức $K$ còn lại về cả độ gắn kết cụm (Silhouette cao hơn mức $K=3$ tới 32%) và độ tách biệt rõ ràng (DB thấp nhất).
- Cấu hình $K = 2$ phản ánh tự nhiên bản chất thị trường chứng khoán Việt Nam: sự phân hóa thành 2 thái cực động lượng rõ rệt: **Nhóm Cổ phiếu Dẫn dắt / Tăng trưởng mạnh (Leader)** và **Nhóm Cổ phiếu Bám sau / Yếu thế (Lagging)**.
- Quyết định chính thức: **Khóa Global K = 2** làm tham số bất biến duy nhất cho toàn bộ các phương án so sánh tại Nhiệm vụ 4, 5, 6 và toàn bộ M2.

---

## CHƯƠNG 3 — KẾT QUẢ THỰC NGHIỆM ĐỐI ĐẦU GIỮA 3 PHƯƠNG ÁN

Tại Nhiệm vụ 10, ba phương án phân cụm với $K = 2$ được đưa vào thực nghiệm đối đầu trên 60 development snapshots:
1. **Phương án A — K-Means Baseline:** Phân cụm trực tiếp trên 8 đặc trưng Robust Scaled.
2. **Phương án B — Ward Hierarchical:** Phân cụm phân cấp liên kết Ward trên ma trận khoảng cách Euclidean.
3. **Phương án C — PCA + K-Means:** Giảm chiều qua PCA (giữ 4 thành phần chính giải thích ~85% phương sai) trước khi fit K-Means.

### 3.1. Ma trận đánh đổi 5 tiêu chí (5-Tier Evaluation Matrix)

| Tiêu chí đánh giá | K-Means Baseline (A) | Ward Hierarchical (B) | PCA + K-Means (C) | Phương án thắng |
| :--- | :---: | :---: | :---: | :---: |
| **1. Cluster Quality (Silhouette / DB)** | Sil: 0.292 / DB: 1.354 | Sil: 0.248 / DB: 1.512 | Sil: 0.315 / DB: 1.286 | PCA + K-Means (+0.023 Sil) |
| **2. Temporal Stability (ARI / Migration)** | ARI: 0.724 / Migr: 12.8% | ARI: 0.651 / Migr: 17.2% | ARI: 0.728 / Migr: 12.5% | Ngang nhau (A ≈ C) |
| **3. Profile Consistency & Balance** | Cực kỳ rõ ràng, đơn điệu | Kém cân bằng | Tốt | K-Means Baseline |
| **4. Economic Interpretability** | Trực tiếp trên 8 đặc trưng gốc | Gián tiếp qua cây phả hệ | Trừu tượng (qua Principal Components) | K-Means Baseline |
| **5. Operational Complexity & Risk** | Tối thiểu (không rủi ro leak PCA) | Chi phí tính toán $O(N^2)$ | Phức tạp (bảo trì thêm PCA transformer) | K-Means Baseline |

### 3.2. Lựa chọn Mô hình Chiến thắng theo Dao cạo Occam (Occam's Razor)
- Tiêu chí định lượng quy định: Nếu phương án phức tạp (PCA + K-Means) không tạo ra khoảng cách Silhouette vượt trội $\Delta \text{Silhouette} \ge 0.03$ so với mô hình cơ sở đơn giản (K-Means Baseline), thì mô hình cơ sở đơn giản phải được chọn để giảm thiểu rủi ro quá khớp và tối ưu hóa tính minh bạch kinh tế.
- Kết quả thực nghiệm: Khoảng cách giữa PCA + K-Means và K-Means Baseline là $\Delta \text{Silhouette} = 0.315 - 0.292 = 0.023 < 0.03$. Độ ổn định thời gian (ARI 0.728 so với 0.724) gần như đồng nhất.
- Trong khi đó, K-Means Baseline cung cấp tọa độ tâm cụm trực tiếp trên 8 chiều đặc trưng tài chính thực tế, giúp nhóm đầu tư M3 hiểu rõ ngay bản chất rủi ro của từng cụm mà không phải chiếu ngược qua không gian thành phần chính trừu tượng.
- **Quyết định:** **Lựa chọn K-Means Baseline (Global K = 2)** là mô hình chiến thắng chính thức duy nhất của Milestone M2.

---

## CHƯƠNG 4 — KẾT QUẢ KIỂM ĐỊNH NGOÀI MẪU HOLDOUT 2024 - 2025

### 4.1. Năng lực tổng quát hóa ngoài mẫu (Out-of-Sample Generalization)
Tại Nhiệm vụ 11, mô hình K-Means Baseline ($K=2$) đã được kích hoạt chạy trên 24 snapshots giai đoạn Holdout (`31/01/2024` đến `31/12/2025`):
- **Median Silhouette Holdout:** **0.274** (so với 0.292 ở Development).
- **Độ suy giảm chất lượng cụm:** $\Delta \text{Silhouette} = 0.274 - 0.292 = -0.018$ (suy giảm nhẹ 6.1%, nằm an toàn dưới ngưỡng cảnh báo rủi ro 15%).
- **Chỉ số Davies-Bouldin Holdout:** 1.412 (tăng nhẹ từ 1.354, vẫn duy trì độ phân tách rất tốt).
- **Độ ổn định thời gian Holdout (23 cặp tháng):** Median ARI đạt **0.698**, tỷ lệ dịch chuyển cụm bình quân (Migration Rate) duy trì ở mức **13.4%**.

### 4.2. Nhận định về dịch chuyển chế độ thị trường (Macro Regime Shift)
Trong giai đoạn 2024 - 2025, thị trường chứng khoán Việt Nam có sự phân hóa dòng tiền mạnh mẽ theo ngành và thanh khoản. Mặc dù cấu trúc 2 cụm có độ co giãn nhẹ, hai cụm vẫn bảo toàn 100% tính chất kinh tế đặc trưng: Cụm Dẫn dắt luôn duy trì động lượng vượt trội trên cả 4 khung thời gian (1T, 3T, 6T, 12T) đi kèm thanh khoản lớn hơn và mức biến động được kiểm soát.

---

## CHƯƠNG 5 — GIỚI HẠN NGHIÊN CỨU VÀ CẢNH BÁO RỦI RO (NON-CLAIMS)

Để đảm bảo tính trung thực học thuật và minh bạch kỹ thuật, Milestone M2 công bố rõ ràng các giới hạn nghiên cứu (Academic Non-claims):

1. **Không phải Dynamic Clustering:**
   Phương pháp M2 áp dụng là phân cụm K-Means độc lập tại từng snapshot cuối tháng kết hợp theo dõi độ bền cấu trúc theo chuỗi thời gian (ARI, NMI, Migration Rate). Đây là phương pháp **Temporal Stability Diagnostic on Independent Cross-Sectional Snapshots**, tuyệt đối không được gọi là thuật toán "Dynamic Clustering" (như Time-Varying Spectral Clustering hay Online Streaming Clustering).
2. **Phạm vi nghiên cứu Market-only:**
   Mô hình phân cụm M2 hoàn toàn dựa trên dữ liệu giá, khối lượng, biến động và thanh khoản thị trường. Các chỉ số cơ bản của báo cáo tài chính (Piotroski F-Score, Altman Z-Score, ROE, Leverage) tạm thời hoãn lại (deferred) do yêu cầu khắt khe về thời điểm công bố Point-in-Time (PIT) và tần suất chậm pha (quarterly vs monthly).
3. **Độ trễ tín hiệu và Chi phí cơ cấu (Turnover Friction):**
   Tỷ lệ luân chuyển cụm trung bình đạt ~13% mỗi tháng. Điều này có nghĩa là chiến lược bám theo Cụm Dẫn dắt sẽ phát sinh chi phí tái cơ cấu danh mục hàng tháng. Nhóm M3 bắt buộc phải đưa ma trận chuyển đổi vào mô hình chi phí giao dịch (Transaction Costs Modeling) để đánh giá khả năng sinh lời thực tế.

---

## CHƯƠNG 6 — HƯỚNG DẪN TÍCH HỢP VÀ BÀN GIAO CHO MILESTONE M3

### 6.1. Ranh giới bất biến giữa M2 và M3 (Boundary Invariants)
Nhóm tiếp nhận Milestone M3 bắt buộc phải tuân thủ 3 nguyên tắc bất biến:
1. **Nguyên tắc bàn giao một chiều (Strict One-Way Handoff):** Kết quả phân cụm M2 là đầu vào cố định bất biến. Nhóm M3 tuyệt đối không được yêu cầu thay đổi $K$, thay đổi scaler, hay thay đổi thuật toán chỉ vì kết quả backtest đầu tư chưa đạt lợi nhuận kỳ vọng.
2. **Tách biệt hệ thống chỉ số (Metric Segregation):** Chỉ số M2 đo lường chất lượng cụm (Silhouette, DB, ARI). Chỉ số M3 đo lường hiệu quả danh mục (CAGR, Sharpe, Drawdown). Không sử dụng chỉ số đầu tư để can thiệp ngược lại mô hình phân cụm.
3. **Thực thi Point-in-Time (PIT Execution):** Tại thời điểm snapshot tháng $t$ (cuối phiên giao dịch ngày làm việc cuối cùng của tháng), nhãn cụm được chốt. Nhóm M3 chỉ được sử dụng nhãn này để tái phân bổ danh mục vào phiên giao dịch tiếp theo ($t+1$). Tuyệt đối không giả định mua bán cùng giá đóng cửa ngày $t$.

### 6.2. Danh mục 5 thành phần trong Gói bàn giao (`M2/artifacts/m2-final-handoff-v1/`)

1. **Thành phần 1 — Bảng nhãn cụm lịch sử 84 snapshots (`m2_cluster_labels_for_m3.csv`):**
   Gồm 75.801 quan sát nhãn cụm (Cụm 0, Cụm 1) của các mã đủ điều kiện qua đủ 84 snapshots (60 Dev + 24 Holdout). Các cột: `snapshot_date`, `security_id`, `ticker`, `cluster_label`, `membership_period`.
2. **Thành phần 2 — Bảng hồ sơ kinh tế tâm cụm (`m2_cluster_profiles_for_m3.csv`):**
   Gồm chân dung 8 đặc trưng gốc qua từng tháng và 6 dòng trung vị toàn kỳ (Dev, Holdout, Toàn kỳ). Cung cấp cơ sở học thuật để M3 xác định cụm Long/Overweight vs Short/Underweight.
3. **Thành phần 3 — Dữ liệu tham chiếu luân chuyển danh mục (`m2_transition_turnover_reference.csv`):**
   Gồm 82 cặp tháng chuyển dịch liên tục với các thông số: `ari`, `nmi`, `persistence_probability`, `migration_rate`, `entered_count`, `exited_count`.
4. **Thành phần 4 — Thư mục mô hình và bộ chuẩn hóa đã đóng băng (`M2/models/final_selected_model/`):**
   Chứa đầy đủ 84 tệp JSON mô hình fitted kèm tọa độ tâm cụm và tham số RobustScaler (Median, IQR) cho từng snapshot.
5. **Thành phần 5 — Tệp siêu dữ liệu bàn giao (`m2_to_m3_handoff_manifest.json`):**
   Chứa toàn bộ metadata, checksum SHA-256 xác thực toàn vẹn của các file bàn giao và xác nhận vượt qua kiểm toán Task 12.

---
*Gói bàn giao M2 đã sẵn sàng 100% để đội ngũ Milestone M3 triển khai xây dựng chiến lược đầu tư và backtest danh mục.*
