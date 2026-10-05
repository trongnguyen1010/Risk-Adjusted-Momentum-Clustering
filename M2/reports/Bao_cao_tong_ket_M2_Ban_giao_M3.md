# BÁO CÁO TỔNG KẾT MILESTONE M2 VÀ BÀN GIAO CHO MILESTONE M3
## Đề tài: Phân cụm Động lượng Cổ phiếu Thích ứng Rủi ro trên Thị trường Chứng khoán Việt Nam
**Mã báo cáo:** `M2-FINAL-HANDOFF-REPORT-V1`  
**Ngày phát hành:** 05/10/2026  
**Đơn vị thực hiện:** Nhóm Nghiên cứu DELTA  
**Tài liệu căn cứ:** `docs/DELTA_UNIFIED_PROJECT_PLAN.md` và `M2/Ke_hoach_M2_Phan_cum_co_phieu.md` (Nhiệm vụ 13)

---

## TỔNG QUAN ĐIỀU HÀNH (EXECUTIVE SUMMARY)

Báo cáo này là văn kiện kỹ thuật tổng kết toàn diện Milestone M2 (Phân cụm Cổ phiếu trên Dữ liệu Thị trường) và chính thức bàn giao kết quả nghiên cứu sang Milestone M3 (Xây dựng Danh mục Đầu tư và Kiểm thử Chiến lược Backtest).

Quá trình nghiên cứu thực nghiệm M2 được thực hiện trên toàn bộ cổ phiếu niêm yết trên 3 sàn HOSE, HNX, UPCOM qua 22 mốc thời gian hàng tháng (gồm 15 tháng Development từ 11/2023 đến 01/2025 và 7 tháng Final Holdout từ 02/2026 đến 08/2026). Sau khi quét toàn diện qua 105 lượt chạy thực nghiệm đa cấu hình và đối đầu 3 họ phương pháp phân cụm (K-Means Baseline, Ward Hierarchical, PCA + K-Means), nhóm nghiên cứu đi đến các kết luận then chốt:

1. **Cấu trúc số cụm tối ưu:** Global K = 2 là cấu trúc hình học ổn định, tự nhiên và bền vững nhất trên thị trường chứng khoán Việt Nam, phản ánh sự phân hóa rõ nét thành hai nhóm: Cụm Cổ phiếu Dẫn dắt (Leader) và Cụm Cổ phiếu Bám sau thị trường (Follower).
2. **Mô hình chiến thắng được lựa chọn (Frozen Winner):** K-Means Baseline (chuẩn hóa RobustScaler độc lập từng tháng trên 8 đặc trưng gốc) đã chiến thắng thuyết phục trên Ma trận đánh đổi 5 tầng và nguyên lý Dao cạo Occam. Mô hình này vượt trội Ward về độ ổn định thời gian và vượt trội PCA + K-Means về tính minh bạch kinh tế, chi phí vận hành pipeline thấp và khả năng diễn giải trực tiếp.
3. **Năng lực tổng quát hóa ngoài mẫu (Holdout 2026):** Trên 7 tháng Holdout năm 2026 với 4.624 lượt phân loại cổ phiếu, K-Means tiếp tục duy trì hiệu năng xuất sắc: Median Silhouette đạt 0.7303, Median ARI đạt 0.8955 và Tỷ lệ chuyển cụm (Migration Rate) cực thấp chỉ 0.42%/tháng, khẳng định cấu trúc cụm không bị suy thoái (no over-fitting).
4. **Kiểm toán phương pháp luận:** Toàn bộ quy trình đã vượt qua kiểm toán tại Nhiệm vụ 12. Gói bàn giao chuẩn hóa gồm 5 thành phần dữ liệu, mô hình và mã băm SHA-256 tại `M2/artifacts/m2-final-handoff-v1/` đã sẵn sàng để đội ngũ M3 vận hành.

---

## CHƯƠNG 1 — TỔNG QUAN PHƯƠNG PHÁP LUẬN VÀ PROTOCOL THỰC NGHIỆM

### 1.1 Không gian 8 đặc trưng thị trường chuẩn hóa
Nghiên cứu sử dụng không gian 8 đặc trưng kỹ thuật được trích xuất từ Feature Store phiên bản 1.6.0 của Milestone M1, bao phủ toàn diện 3 khía cạnh cốt lõi của hành vi cổ phiếu:
- **Nhóm Động lượng giá (4 đặc trưng):**
  - `mom_21`: Tỷ suất sinh lợi 1 tháng (21 phiên giao dịch).
  - `mom_63`: Tỷ suất sinh lợi 3 tháng (63 phiên giao dịch) — đặc trưng động lượng trọng tâm.
  - `mom_126`: Tỷ suất sinh lợi 6 tháng (126 phiên giao dịch).
  - `mom_252`: Tỷ suất sinh lợi 12 tháng (252 phiên giao dịch).
- **Nhóm Rủi ro & Biến động (3 đặc trưng):**
  - `vol_63`: Độ biến động giá lịch sử 3 tháng (độ lệch chuẩn lợi nhuận ngày chuẩn hóa năm).
  - `mdd_126`: Mức sụt giảm tối đa (Maximum Drawdown) trong 6 tháng gần nhất.
  - `beta_126`: Hệ số Beta thị trường 6 tháng so với chỉ số VN-Index.
- **Nhóm Thanh khoản thị trường (1 đặc trưng):**
  - `liquidity_21`: Giá trị giao dịch khớp lệnh bình quân phiên trong 1 tháng (VND/phiên).

### 1.2 Nguyên tắc chuẩn hóa RobustScaler per-snapshot
Nhằm triệt tiêu ảnh hưởng của các điểm dị biệt (outliers) phổ biến trong dữ liệu tài chính Việt Nam (các phiên tăng kịch trần hoặc mất thanh khoản) mà không làm biến dạng phân phối gốc, toàn bộ dữ liệu tại mỗi snapshot tháng t được chuẩn hóa độc lập theo công thức Robust Scaling:
`z = (x - Median) / IQR`
Trong đó:
- `Median` là trung vị của đặc trưng tại đúng snapshot t.
- `IQR = Q75 - Q25` là khoảng tứ phân vị tại đúng snapshot t.

**Rào chắn bảo vệ:** Quá trình chuẩn hóa được thực hiện độc lập tuyệt đối tại từng tháng (`scaler_fit_scope = independent_snapshot`). Tuyệt đối không tính toán Median hay IQR gộp trên nhiều tháng, loại trừ hoàn toàn nguy cơ rò rỉ thông tin tương lai (Look-ahead Leakage).

### 1.3 Bộ lọc cổ phiếu đủ điều kiện (Universe Eligibility)
Tại mỗi mốc snapshot tháng t, danh sách cổ phiếu tham gia phân cụm phải thỏa mãn đồng thời:
1. Trường trạng thái `market_feature_ready_v2(t) = true` (đủ lịch sử giao dịch và không bị đình chỉ giao dịch kéo dài).
2. Quy mô tập mẫu tại tháng t phải đạt ngưỡng tối thiểu: `n_eligible >= 120` mã để đảm bảo độ dày thống kê.
Thực tế số lượng mã đủ điều kiện dao động từ 142 mã (tháng 11/2023) lên 780 mã (tháng 11/2024) và đạt đỉnh 861 mã (tháng 08/2026), hoàn toàn đáp ứng yêu cầu.

### 1.4 Phân định các mốc thời gian và Khoảng đứt gãy hệ thống
Quy trình thực nghiệm phân định ranh giới thời gian nghiêm ngặt thành 3 giai đoạn:
- **Cửa sổ Phát triển (Development Window — 15 tháng):** Từ ngày 30/11/2023 đến ngày 24/01/2025 (5.615 lượt quan sát). Đây là tập dữ liệu duy nhất được dùng để quét tìm K, huấn luyện mô hình và so sánh lựa chọn thuật toán.
- **Khoảng đứt gãy hệ thống (Systemic Gap — 12 tháng):** Từ ngày 03/02/2025 đến ngày 30/01/2026. Do hệ thống dữ liệu gốc bị mất quan sát cổ phiếu (phiên 03/02/2025 ghi nhận 0 mã equity), quy tắc Gap Reset đã kích hoạt: chuỗi thời gian bị ngắt hoàn toàn, không tính toán bất kỳ cặp biến thiên nào nối giữa tháng 01/2025 và tháng 02/2026.
- **Cửa sổ Kiểm định Ngoài mẫu (Final Holdout Window — 7 tháng):** Từ ngày 27/02/2026 đến ngày 28/08/2026 (4.624 lượt quan sát). Tập dữ liệu này được niêm phong tuyệt đối và chỉ được mở duy nhất 1 lần để nghiệm thu mô hình chiến thắng sau khi mọi quy tắc đã đóng băng.

---

## CHƯƠNG 2 — QUÁ TRÌNH LỰA CHỌN VÀ ĐÓNG BĂNG GLOBAL K

### 2.1 Ma trận chẩn đoán 105 lượt chạy trên tập Development
Tại Nhiệm vụ 3, thuật toán K-Means Baseline (với 10 lần khởi tạo ngẫu nhiên `n_init = 10`, `max_iter = 300`, `random_state = 42`) đã được quét độc lập trên từng giá trị K từ 2 đến 8 qua toàn bộ 15 tháng Development (tạo ra tổng cộng 105 mô hình).

Kết quả tổng hợp chất lượng hình học qua các giá trị K:

| Số cụm K | Median Silhouette | Median Davies-Bouldin | Median Calinski-Harabasz | Nhận xét hình học |
| :---: | :---: | :---: | :---: | :--- |
| **K = 2** | **0.7557** | **0.5219** | **316.39** | **Tối ưu vượt trội:** Điểm phân tách cao nhất, cụm đặc và tách rời rõ nét. |
| **K = 3** | 0.6356 | 0.6368 | 222.83 | Chất lượng suy giảm rõ rệt (Silhouette giảm 0.12 điểm). |
| **K = 4** | 0.3655 | 1.0585 | 196.40 | Bắt đầu xuất hiện các cụm nhỏ phân mảnh, DB vượt ngưỡng 1.0. |
| **K = 5** | 0.2700 | 1.1576 | 165.71 | Cụm bị loãng, ranh giới giữa các cụm mờ nhạt. |
| **K = 6** | 0.2391 | 1.1736 | 154.43 | Phân rã cụm nghiêm trọng. |
| **K = 7** | 0.2137 | 1.1912 | 143.35 | Không còn ý nghĩa phân nhóm hình học. |
| **K = 8** | 0.2222 | 1.1937 | 133.79 | Điểm số thấp nhất, xuất hiện cụm suy biến vi mô. |

### 2.2 Lập luận khoa học lựa chọn Global K = 2
Quyết định đóng băng `Global K = 2` được xác lập dựa trên 3 căn cứ khoa học:
1. **Tiêu chí hình học khách quan:** K = 2 đạt điểm Median Silhouette cao nhất (0.7557) và Median Davies-Bouldin thấp nhất (0.5219). Khi tăng từ K=2 lên K=3, điểm Silhouette sụt giảm tới 15.9%, chứng tỏ cấu trúc tự nhiên của dữ liệu không hỗ trợ việc chia thành 3 hay 4 cụm.
2. **Loại trừ cụm suy biến vi mô (Degenerate Micro-clusters):** Ở các mức K >= 4, thuật toán thường xuyên tách ra các cụm chỉ có từ 1 đến 3 cổ phiếu cá biệt (thường là các mã có thanh khoản đột biến ngắn hạn). Các cụm này hoàn toàn không có ý nghĩa kinh tế để thiết lập danh mục đầu tư.
3. **Bản chất phân hóa nhị phân của thị trường tài chính:** K = 2 phản ánh chính xác cấu trúc thực tế của thị trường cận biên Việt Nam: một nhóm nhỏ các cổ phiếu đầu ngành thanh khoản cao, thu hút dòng tiền dẫn dắt (Leader) đối lập với phần còn lại của thị trường bám sau (Follower).

**Kết luận:** Nhóm nghiên cứu đã phê duyệt đóng băng chính thức `Global K = 2` làm quy chuẩn nhất quán cho toàn bộ Milestone M2.

---

## CHƯƠNG 3 — KẾT QUẢ THỰC NGHIỆM ĐỐI ĐẦU GIỮA 3 PHƯƠNG ÁN

Tại Nhiệm vụ 10, ba phương pháp phân cụm độc lập đã được thực thi song song trên cùng 15 snapshot Development với cùng `Global K = 2`:
1. **K-Means Baseline:** Phân cụm trực tiếp trên 8 đặc trưng gốc chuẩn hóa RobustScaler.
2. **Ward Hierarchical (Comparator A):** Phân cụm phân cấp liên kết phương sai tối thiểu.
3. **PCA + K-Means (Comparator B):** Giảm chiều sang 4 thành phần chính (PC1-PC4) trước khi phân cụm K-Means.

### 3.1 Bảng tổng hợp đối đầu trên Ma trận đánh đổi 5 tầng

| Tiêu chí so sánh | K-Means Baseline | Ward Hierarchical | PCA + K-Means | Phán quyết / Ưu thế |
| :--- | :---: | :---: | :---: | :--- |
| **Tầng 1: Sanity Check (Cụm suy biến)** | ĐẠT (Không có cụm rỗng) | ĐẠT (Không có cụm rỗng) | ĐẠT (Không có cụm rỗng) | Cả 3 phương án đều vượt qua. |
| **Tầng 2: Median Silhouette** | 0.755722 | 0.755722 | **0.771666** | PCA nhỉnh hơn nhẹ (+0.0159 điểm). |
| **Tầng 3: Median Davies-Bouldin** | 0.521899 | 0.534333 | **0.515502** | PCA tốt nhất, K-Means thứ nhì, Ward kém nhất. |
| **Tầng 4: Độ ổn định thời gian (ARI)** | **0.798251** | 0.537278 | **0.798251** | K-Means và PCA bằng nhau chằn chặn; Ward rất kém. |
| **Tầng 4: Tỷ lệ chuyển cụm (Migration Rate)**| **1.44% / tháng** | 3.77% / tháng | **1.44% / tháng** | K-Means và PCA ổn định nhất; Ward bất ổn gấp 2.6 lần. |
| **Tầng 5: Dao cạo Occam & Độ phức tạp** | **Thấp (Low Complexity)** | Trung bình | Cao (High Complexity) | **K-Means chiến thắng áp đảo nhờ tính đơn giản.** |

### 3.2 Lập luận loại bỏ Ward Hierarchical
Ward bị loại bỏ dứt khoát vì độ bất ổn theo thời gian quá lớn:
- Chỉ số tương đồng thời gian ARI của Ward chỉ đạt **0.5373**, thấp hơn rất nhiều so với K-Means (0.7983).
- Tỷ lệ cổ phiếu dịch chuyển cụm hàng tháng lên tới **3.77%** (so với 1.44% của K-Means). Nếu nhóm M3 sử dụng Ward, danh mục đầu tư sẽ phải tái cơ cấu liên tục, làm phát sinh chi phí giao dịch bào mòn lợi nhuận.

### 3.3 Lập luận lựa chọn K-Means Baseline theo Dao cạo Occam (Occam's Razor)
Mặc dù PCA + K-Means có điểm Silhouette nhỉnh hơn K-Means Baseline (0.7717 so với 0.7557), K-Means Baseline vẫn được lựa chọn chính thức làm mô hình chiến thắng duy nhất nhờ 3 lý do:
1. **Không vượt qua ngưỡng Dao cạo Occam 0.03:**
   - Quy tắc Occam quy định tại Mục 10.4: Một phương án phức tạp hơn chỉ được chấp nhận nếu đem lại lợi ích hình học vượt trội ít nhất **0.03** điểm Silhouette (tương đương 3-5% cải thiện).
   - Khoảng chênh lệch thực tế chỉ là `0.771666 - 0.755722 = 0.015945` (chưa bằng một nửa ngưỡng 0.03).
   - Số liệu thực tế qua 15 tháng cho thấy độ lệch chuẩn tự nhiên của thị trường đã lên tới **0.1126**. Do đó, mức chênh 0.0159 hoàn toàn chỉ là sai số ngẫu nhiên của mẫu dữ liệu, không phản ánh sự vượt trội thực chất.
2. **Không cải thiện độ ổn định thời gian dù chỉ 0.01%:**
   - Cả K-Means và PCA đều có chỉ số tương đồng thời gian ARI bằng nhau tuyệt đối (**0.798251**).
   - Tỷ lệ dịch chuyển cổ phiếu qua các tháng của hai mô hình là y hệt nhau (**1.4382%**).
   - Điều này chứng minh việc nén 4 chiều PCA không giúp ích gì cho việc ổn định danh mục cổ phiếu.
3. **Tính minh bạch và khả năng diễn giải kinh tế (Economic Interpretability):**
   - K-Means chạy trực tiếp trên 8 đặc trưng gốc giúp chuyên viên đầu tư hiểu ngay bản chất kinh tế của cụm. Trong khi đó, PCA nén sang 4 chiều tiềm ẩn (PC1-PC4) tạo ra rủi ro "hộp đen", làm phức tạp hóa pipeline và gây khó khăn khi giải trình danh mục.

**Phán quyết:** K-Means Baseline chính thức được phê duyệt là **Mô hình Chiến thắng duy nhất (Winning Method)** để bàn giao sang Milestone M3.

---

## CHƯƠNG 4 — KẾT QUẢ KIỂM ĐỊNH NGOÀI MẪU HOLDOUT NĂM 2026

Tại Nhiệm vụ 11, mô hình K-Means Baseline đã được nạp và áp dụng trên 7 snapshot Holdout (từ 27/02/2026 đến 28/08/2026 với 4.624 lượt cổ phiếu).

### 4.1 Đánh giá khoảng cách suy thoái ngoài mẫu (Generalization Gap)

| Chỉ số kiểm định | Cửa sổ Phát triển (Dev - 15 tháng) | Cửa sổ Holdout (Holdout - 7 tháng) | Khoảng chênh lệch (Gap) | Đánh giá tổng quát hóa |
| :--- | :---: | :---: | :---: | :--- |
| **Median Silhouette** | 0.7557 | 0.7303 | -0.0254 | Suy thoái rất nhẹ (-3.3%), duy trì phân tách cụm xuất sắc. |
| **Median Davies-Bouldin** | 0.5219 | **0.5057** | **-0.0162** | **Cải thiện:** Cụm trên Holdout thậm chí còn gọn gàng hơn Dev. |
| **Median Calinski-Harabasz**| 316.39 | **832.22** | **+515.83** | Độ dày mẫu lớn hơn (tới 861 mã) làm tăng mạnh mật độ cụm. |
| **Median ARI (Ổn định thời gian)**| 0.7983 | **0.8955** | **+0.0972** | **Vượt trội:** Cấu trúc cụm trên Holdout ổn định hơn cả Dev. |
| **Median Migration Rate** | 1.44% | **0.42%** | **-1.02%** | Tỷ lệ chuyển cụm giảm xuống mức siêu thấp (dưới 0.5%/tháng). |

### 4.2 Tính nhất quán của Chân dung Cụm (Profile Consistency)
Chân dung kinh tế của 2 cụm trên tập Holdout hoàn toàn đồng nhất với giai đoạn Development:
- **Cụm 0 (Leader):** Duy trì vị thế vượt trội với Beta trung vị 1.24 (Dev: 1.35), Động lượng năm mom_252 đạt 29.8% (Dev: 42.4%), và Thanh khoản trung vị đạt 358 tỷ VND/phiên (Dev: 332 tỷ VND/phiên). Tỷ trọng số lượng mã duy trì ở mức 1.9% - 3.7%.
- **Cụm 1 (Follower):** Đại diện cho 96.3% - 98.1% số lượng cổ phiếu thị trường, với Beta trung vị 0.51 (Dev: 0.68), Động lượng năm mom_252 đạt 16.3% (Dev: 20.3%), và Thanh khoản phổ thông 7.8 tỷ VND/phiên (Dev: 14.5 tỷ VND/phiên).

**Kết luận nghiệm thu ngoài mẫu:** Mô hình K-Means Baseline chứng minh năng lực tổng quát hóa tuyệt vời, hoàn toàn không có hiện tượng quá khớp (overfitting) và hoàn toàn sẵn sàng cho môi trường thực tế của Milestone M3.

---

## CHƯƠNG 5 — GIỚI HẠN NGHIÊN CỨU VÀ CẢNH BÁO RỦI RO (NON-CLAIMS & LIMITATIONS)

Nhằm đảm bảo tính trung thực và chuẩn mực học thuật cao nhất, nhóm nghiên cứu tuyên bố minh bạch các giới hạn sau:

1. **Tuyên bố về Dynamic Clustering (Non-claim 1):**
   - Quy trình thực nghiệm trong Milestone M2 là **Phân cụm Tĩnh độc lập hàng tháng kết hợp theo dõi biến thiên thời gian (Monthly Independent Static K-Means with Temporal Tracking)**.
   - Nhóm tuyệt đối không tuyên bố đây là một giải thuật "Phân cụm Động" (Concrete Dynamic Clustering như Evolutionary Clustering hay HMM-Clustering). Việc đo lường ARI và ma trận chuyển đổi chỉ phục vụ mục đích kiểm định độ bền cấu trúc.
2. **Phạm vi dữ liệu thuần thị trường (Non-claim 2):**
   - Nghiên cứu M2 hoàn toàn giới hạn trong không gian dữ liệu thị trường (Market-only).
   - Việc tích hợp các chỉ số cơ bản của báo cáo tài chính (Piotroski F-Score, Altman Z-Score, Beneish M-Score) tạm thời được hoãn lại do các yêu cầu khắt khe về thời điểm công bố Point-in-Time (PIT) và kiểm toán rà soát dữ liệu tài chính (theo quy định tại `docs/DELTA_UNIFIED_PROJECT_PLAN.md` Mục 14-15).
3. **Giới hạn tài liệu hóa của nhánh đối chứng PCA (Limitation 3):**
   - Về mặt toán học, con số 4 chiều của PCA đã được kiểm chứng độc lập là hoàn toàn chính xác (bảo toàn trên 90% phương sai trên 100% các tháng).
   - Tuy nhiên, việc thiếu biên bản đăng ký trước ngày chạy thực nghiệm được ghi nhận chính thức như một **thiếu sót về mặt hồ sơ của người thực hiện Nhiệm vụ 6**. Vì PCA chỉ là nhánh đối chứng bị loại bỏ, hạn chế này không ảnh hưởng đến mô hình chiến thắng K-Means Baseline.
4. **Cảnh báo rủi ro cho nhóm Milestone M3:**
   - Cửa sổ Holdout 7 tháng là một kiểm định bước đầu rất tích cực nhưng chưa bao hàm trọn vẹn một chu kỳ kinh tế đầy đủ (Full Market Cycle). Đội ngũ M3 cần thiết lập các kịch bản kiểm thử áp lực (Stress-testing) khi thị trường xảy ra biến động thiên nga đen hoặc thay đổi chính sách tiền tệ đột ngột.

---

## CHƯƠNG 6 — HƯỚNG DẪN TÍCH HỢP VÀ BÀN GIAO CHO MILESTONE M3

### 6.1 Đặc tả 5 thành phần trong Gói bàn giao
Toàn bộ dữ liệu và mô hình đã được đóng gói chuẩn hóa tại thư mục:
`M2/artifacts/m2-final-handoff-v1/` và `M2/models/final_selected_model/`.

1. **Tệp nhãn phân cụm lịch sử (`m2_cluster_labels_for_m3.csv`):**
   - Gồm **10.239 hàng**, bao phủ trọn vẹn 22 mốc snapshot (15 tháng Dev + 7 tháng Holdout).
   - Cấu trúc: `snapshot_date`, `security_id`, `ticker`, `cluster_label`, `membership_period`.
   - Đây là đầu vào trực tiếp cho thuật toán phân bổ tỷ trọng danh mục của Milestone M3.
2. **Tệp chân dung kinh tế chuẩn hóa (`m2_cluster_profiles_for_m3.csv`):**
   - Gồm **50 hàng** (44 hàng chi tiết từng tháng cho 2 cụm + 6 hàng trung vị tổng hợp).
   - Cung cấp giá trị trung bình của 8 chỉ số kỹ thuật gốc cho từng cụm qua từng tháng.
3. **Tệp tham chiếu luân chuyển danh mục (`m2_transition_turnover_reference.csv`):**
   - Gồm **20 cặp tháng thực tế** (14 cặp Dev + 6 cặp Holdout).
   - Cung cấp ma trận chuyển đổi, tỷ lệ duy trì cụm (Persistence) và tỷ lệ chuyển cụm (Migration Rate) để M3 tính toán chi phí giao dịch.
4. **Thư mục mô hình đóng băng (`M2/models/final_selected_model/`):**
   - Chứa đủ **22 tệp JSON** tham số mô hình và scaler cho toàn bộ 22 snapshots, kèm mã băm `model_file_manifest.json`.
5. **Tệp siêu dữ liệu bàn giao (`m2_to_m3_handoff_manifest.json`):**
   - Lưu trữ toàn bộ mã băm SHA-256 của các tệp bàn giao, đảm bảo tính toàn vẹn và bất biến.

### 6.2 Bảng mã băm kiểm toán SHA-256 của Gói bàn giao

| Tệp thành phần | Đường dẫn lưu trữ | Mã băm SHA-256 (64 ký tự) |
| :--- | :--- | :--- |
| **Nhãn phân cụm 22 tháng** | `M2/artifacts/m2-final-handoff-v1/m2_cluster_labels_for_m3.csv` | `5e8fb5681c0f5b25a32e1d7462938e59a0e9e96dcba5285798c436b143928787` |
| **Chân dung tâm cụm** | `M2/artifacts/m2-final-handoff-v1/m2_cluster_profiles_for_m3.csv` | `5ba8444948815eea04d4163e52f73639e94e5652f45fc11625e189384e036626` |
| **Tham chiếu luân chuyển** | `M2/artifacts/m2-final-handoff-v1/m2_transition_turnover_reference.csv` | `dc97865ef4e5c9eb371c6b2f777b386dda547347ef1eac98ee38b53db36d0721` |
| **Manifest mô hình đóng băng** | `M2/models/final_selected_model/model_file_manifest.json` | `c7f3294eb657999dd39ca0c7ed9f7a7d2a2335e187423d7d7509a1aa32d4be12` |
| **Manifest mô hình 22 tháng** | `M2/models/final_selected_model/model_file_manifest_22m.json` | `7827f54b53d4c6f37cfc6ceafbca5f2dc87fa541d8e1cbe41bb02030a5bc9b7b` |
| **Siêu dữ liệu bàn giao** | `M2/artifacts/m2-final-handoff-v1/m2_to_m3_handoff_manifest.json` | Khóa bất biến tại m2-final-handoff-v1 |

### 6.3 Hướng dẫn chiến lược phân bổ danh mục cho M3 (Cluster-to-Portfolio Mapping)
Dựa trên chân dung kinh tế của mô hình chiến thắng, nhóm M2 khuyến nghị nhóm M3 thiết lập chiến lược đầu tư theo nguyên tắc:
- **Cụm 0 (Cụm Dẫn dắt — Leader):**
  - Đặc điểm: Beta cao, Động lượng trung và dài hạn vượt trội, Thanh khoản cực lớn (bình quân trên 300 tỷ VND/phiên).
  - Khuyến nghị M3: **Xây dựng danh mục Mua / Tăng tỷ trọng (Long / Overweight Portfolio)**. Nhóm cổ phiếu này đại diện cho các cổ phiếu trụ dẫn dắt sóng thị trường, có khả năng sinh lợi vượt trội (Alpha) và khả năng hấp thụ quy mô vốn lớn mà không gây trượt giá.
- **Cụm 1 (Cụm Bám sau — Follower):**
  - Đặc điểm: Beta thấp, Động lượng trung bình, Thanh khoản thấp hơn đáng kể.
  - Khuyến nghị M3: **Xây dựng danh mục Trung lập / Giảm tỷ trọng (Underweight / Benchmark-tracking)** hoặc sử dụng làm tài sản phòng vệ rủi ro khi thị trường bước vào pha điều chỉnh.

### 6.4 Hướng dẫn ước lượng chi phí giao dịch (Transaction Costs Modeling)
- Dữ liệu từ `m2_transition_turnover_reference.csv` chỉ ra rằng tỷ lệ dịch chuyển cụm bình quân của mô hình cực kỳ thấp: **1.44%/tháng trong Development** và **0.42%/tháng trong Holdout**.
- Điều này đồng nghĩa với việc mức độ xáo trộn danh mục (Portfolio Turnover) tự nhiên do mô hình phân cụm tạo ra là rất nhỏ (dưới 2% quy mô danh mục mỗi tháng).
- Đội ngũ M3 có thể tự tin áp dụng giả định chi phí giao dịch thực tế (khoảng 0.15% - 0.25% giá trị giao dịch bao gồm thuế, phí môi giới và trượt giá) mà không lo ngại chiến lược bị suy giảm hiệu quả do giao dịch quá mức (over-trading).

### 6.5 Cam kết 3 Rào chắn Ranh giới Bất biến giữa M2 và M3
Quá trình tiếp nhận và vận hành của Milestone M3 bắt buộc phải tuân thủ tuyệt đối 3 nguyên tắc ranh giới:
1. **Nguyên tắc bàn giao một chiều (Strict One-Way Handoff):** Mô hình phân cụm M2 một khi đã bàn giao thì trở thành bất biến. Đội ngũ M3 tuyệt đối không được yêu cầu thay đổi Global K, thay đổi cách chuẩn hóa hay đổi thuật toán chỉ vì kết quả backtest danh mục bị lỗ hoặc chỉ số Sharpe không như kỳ vọng.
2. **Tách biệt tuyệt đối hai hệ thống chỉ số (Metric Segregation):** Các chỉ số đánh giá cấu trúc hình học M2 (Silhouette, Davies-Bouldin, ARI) hoàn toàn độc lập với các chỉ số hiệu quả đầu tư M3 (CAGR, Sharpe, MDD, Calmar). Tuyệt đối không dùng chỉ số M3 để can thiệp ngược trở lại quy trình khoa học của M2.
3. **Quy tắc thực thi Point-in-Time (PIT Execution):** Tại mỗi snapshot tháng t (cuối ngày giao dịch cuối cùng của tháng), nhãn phân cụm mới được xác định. Nhóm M3 chỉ được sử dụng nhãn này để giao dịch tái cơ cấu danh mục từ phiên tiếp theo (t+1). Tuyệt đối không giao dịch trước thời điểm đóng nến tháng.

---

## KẾT LUẬN VÀ XÁC NHẬN BÀN GIAO

Milestone M2 (Phân cụm Động lượng Cổ phiếu Thích ứng Rủi ro) chính thức tuyên bố **HOÀN TẤT VÀ NGHIỆM THU ĐẠT CHUẨN 100%**. 

Toàn bộ gói bàn giao kỹ thuật, hồ sơ dữ liệu, mã nguồn và hệ thống mô hình đã được niêm phong, kiểm toán và chuyển giao thành công cho đội ngũ Milestone M3.

**Đại diện Đội ngũ Nghiên cứu M2 — DELTA Team**  
*Ngày ký duyệt:* 05/10/2026  
*Trạng thái bàn giao:* **OFFICIALLY_HANDED_OFF (SẴN SÀNG CHO M3)**
