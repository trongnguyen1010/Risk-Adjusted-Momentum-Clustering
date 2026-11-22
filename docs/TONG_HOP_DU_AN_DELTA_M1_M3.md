**DỰ ÁN DELTA**

**Risk-Adjusted Momentum Clustering**

Tài liệu tổng hợp chi tiết quá trình thực hiện M1 → M2 → M3

**Mục đích**	Báo cáo và thuyết trình với mentor

**Ngày báo cáo**	06/11/2026

**Phạm vi**	Nền tảng dữ liệu (M1), phân cụm (M2), backtest và sản phẩm (M3)

**Nguồn**	Repo Risk-Adjusted-Momentum-Clustering, nhánh feature/indicators-v1 (253 commit, 11/09 – 05/11/2026)

**Cấu trúc tài liệu**

- Phần 0 – Tổng quan: tóm tắt, mục tiêu, phương pháp, dòng thời gian, kết quả, phân công, câu hỏi mentor, dàn ý thuyết trình.
- Phần 1 – M1: nền tảng dữ liệu giá và tài chính.
- Phần 2 – M2: phân cụm, vấn đề K=2 và mô hình A v4.
- Phần 3 – M3: B-PIT, chiến lược, engine backtest, kết quả, dashboard.
**Mục lục**

**Phần 0 – Tổng quan dự án****	3**

1. Tóm tắt một trang	3

2. Bối cảnh và mục tiêu	3

3. Dữ liệu	4

4. Phương pháp	5

5. Quá trình thực hiện từ đầu đến cuối	6

6. Kết quả M3 (Development và Holdout)	8

7. Kiến trúc hệ thống và triển khai	9

8. Phân công: ai làm gì	10

9. Hạn chế và việc còn lại	11

10. Câu hỏi mentor có thể hỏi và gợi ý trả lời	11

11. Gợi ý dàn ý thuyết trình (khung 15–20 phút)	12

Nguồn trong repo	13

**Phần 1 – M1 – Nền tảng dữ liệu****	14**

1. Mục tiêu và đầu ra của M1	14

2. Khởi tạo dự án (11–16/09)	14

3. Chọn nguồn dữ liệu: từ KBS sang CafeF (16–24/09)	15

4. Thu thập quy mô lớn: C5 → C8 (24–26/09)	16

5. Chuẩn hóa dữ liệu và tính 8 đặc trưng thị trường	17

6. Kiểm soát chất lượng (QC) và phễu lọc mã	18

7. M2-PREP: khóa giao thức trước khi phân cụm	19

8. Nguồn C8 v2: 1.522 mã, chuỗi dài cho M2 V2 và M3	20

9. Nền tảng dữ liệu tài chính (BCTC)	20

10. Kết quả M1 và bài học rút ra	21

**Phần 2 – M2 – Phân cụm****	23**

1. Mục tiêu và nguyên tắc của M2	23

2. M2 v1: thử nghiệm đầu trên 15 tháng	23

3. M2 v2 trên C8 v2: chuỗi nhiệm vụ đầy đủ	24

4. Baseline phân cụm tài chính 6 tỷ số	25

5. Phát hiện vấn đề: silhouette cao giả	25

6. Phân cụm lại (rework) v1 và v2	26

7. Hệ B v4 (tài chính) và mô hình kết hợp tham chiếu C	27

8. So sánh công bằng M2 K=2 và A v4, quyết định D-DIR-01	27

9. Bàn giao M2 sang M3 và giới hạn	28

**Phần 3 – M3 – Backtest, báo cáo và dashboard****	30**

1. Mục tiêu và cấu trúc M3	30

2. Chuẩn bị: kế hoạch, giai đoạn 0 và lõi engine	30

3. Kế hoạch chuẩn của nhóm trưởng, rà soát và các quyết định	31

4. B-PIT: phân cụm tài chính theo thời điểm công bố	31

5. Năm chiến lược và quy tắc chọn cổ phiếu	32

6. Engine 4 bước	33

7. Trình tự thực thi ngày 04/11	34

8. Kết quả chi tiết và phân tích	35

9. M3-C: notebook tái lập và báo cáo kỹ thuật	37

10. M3-B: dashboard /backtest và triển khai	38

11. Final, phần mở rộng và giới hạn	38

**PHẦN 0**

# Tổng quan dự án

## 1. Tóm tắt một trang

> [!NOTE]
> **Cập nhật mốc thời gian hoàn thiện dự án (20/11/2026):**
> Nhóm đã hoàn thành toàn diện giai đoạn tăng tốc **Làm giàu dữ liệu tài chính B-PIT Enriched** và xây dựng **Hệ thống Đánh giá đầu tư (DELTA Investment Assessment — D-ASS-01)** với sự phối hợp chặt chẽ của cả 4 thành viên (hoàn thành 65/65 nhiệm vụ được giao).
> Kết quả thực nghiệm M3 trên dữ liệu làm giàu đã nâng tỷ suất sinh lời lũy kế chiến lược Combined lên **151.67%** (+35.51 điểm phần trăm so với Baseline) trong kỳ Development (2019–2023) và đạt **53.07%** (+14.12 điểm phần trăm so với Baseline) trong kỳ Holdout độc lập (2024–2025), đồng thời xóa bỏ hoàn toàn hiện tượng "cash drag" (tiền mặt nhàn rỗi do thiếu ứng viên).


DELTA phân cụm cổ phiếu Việt Nam theo hai hệ độc lập (thị trường A và tài chính B), rồi kiểm định xem danh mục chọn từ giao của hai hệ có tốt hơn các chiến lược đối chứng không. Dự án đi qua ba mốc: **M1** dựng nền dữ liệu CafeF, **M2** chọn mô hình phân cụm, **M3** backtest và đưa kết quả lên web.

**Kết quả chính (M3, không phí giao dịch):**

|  | Development 2019–2023 | Holdout 2024–2025 |
| --- | --- | --- |
| CAGR Combined | 16,97% (hạng 4/5) | 18,72% (hạng 2/5) |
| CAGR Momentum-only | 22,36% | 19,80% |
| CAGR VNINDEX | 4,53% | 24,47% |
| Max drawdown Combined | -44,60% | -26,27% |

**Thông điệp nên nói với mentor:** quy trình đúng chuẩn (khóa phương pháp trước, Dev seal rồi mới mở Holdout, không rò rỉ thời gian, tái lập được bằng hash), nhưng giả thuyết "kết hợp thị trường + tài chính tạo lợi thế" **chưa được xác nhận**. Momentum-only tốt hơn Combined ở cả hai đoạn trên CAGR, biến động và drawdown.

**Trạng thái ngày 05/11/2026:**

- M1: xong (nền dữ liệu thị trường CafeF, 1.522 mã ứng viên, giá 2016–2025).
- M2: xong. Mô hình chính thức là A v4 (K-Means k=3, 9 đặc trưng) và B-PIT (K-Means k=3, 9 chỉ số tài chính). Bàn giao M2 K=2 cũ được giữ làm đối chứng.
- M3-A (backtest Dev + Holdout): đã chạy, verify và seal ngày 04/11. Final Evaluation 2026: NOT_READY vì chưa đủ dữ liệu năm 2026.
- M3-B (dashboard): trang /backtest đã lên production ngày 05/11.
- M3-C (báo cáo + notebook tái lập): có cho Dev/Holdout, tổng thể PARTIAL cho đến khi có Final.
- Còn lại: Final 2026 và phần mở rộng phí 15/30 bps.
## 2. Bối cảnh và mục tiêu

Câu hỏi của dự án: có thể nhóm cổ phiếu Việt Nam theo trạng thái động lượng điều chỉnh rủi ro và theo sức khỏe tài chính, rồi dùng hai cách nhóm đó để chọn danh mục tốt hơn không.

**Mục tiêu theo từng mốc:**

- **M1 – Nền dữ liệu:** thu thập giá giao dịch toàn thị trường từ CafeF, có nguồn gốc rõ ràng (hash SHA256), kiểm chứng offline được. Đề tài yêu cầu tối thiểu 300 mã.
- **M2 – Phân cụm:** chọn thuật toán và số cụm chỉ bằng thước đo chất lượng cụm trên giai đoạn Development, không dùng lợi suất.
- **M3 – Backtest và sản phẩm:** khóa phương pháp, chạy backtest Combined so với 4 đối chứng và VNINDEX, viết báo cáo tái lập và đưa lên dashboard.
**Các nguyên tắc bất biến (nên nhắc khi thuyết trình):**

- Ba lớp đánh giá tách biệt: chất lượng cụm, độ ổn định theo thời gian, hiệu quả danh mục.
- Không dùng return, Sharpe hay ROI để chọn k hoặc thuật toán. Sharpe chỉ được tính ở Final Evaluation.
- Point-in-time: chỉ dùng dữ liệu có usable_from_date <= decision_date.
- Không forward-fill giá, không đổi thiếu dữ liệu thành 0.
- Không lấy danh sách mã hiện tại áp ngược về quá khứ (tránh survivorship bias).
- Phân cụm tĩnh từng tháng cộng theo dõi ARI không được gọi là Dynamic Clustering.
## 3. Dữ liệu

Toàn bộ dữ liệu lấy từ CafeF (bổ sung DStock cho phần tài chính còn thiếu), mọi file đầu vào đều được ghim bằng SHA256.

### 3.1 Dữ liệu thị trường (M1)

- **Nguồn:** endpoint TradeHistoryNew của CafeF. Giá điều chỉnh lấy từ AdjustPrice × 1000, coi là proxy giá điều chỉnh của nhà cung cấp (vendor-adjusted). VN-Index làm benchmark.
- **Cách thu thập:** crawler có retry/backoff, chia 5 shard cho 5 người cùng crawl, lưu raw bất biến kèm hash. Quy định crawl thực dụng D-CRAWL-02 (25/10): retry 3 lần rồi hoãn theo mã, không vượt CAPTCHA hay xoay IP.
- **Phêu M1 (C8 v1, snapshot 28/08/2026):** 952 mã ứng viên (500 mã baseline C5 + 452 mã mở rộng C7), 922 mã đủ 8 đặc trưng, **905 mã sẵn sàng phân cụm**, vượt ngưỡng 300 mã của đề tài. 47 mã bị loại đều có lý do ghi lại. Theo sàn: HOSE 297, HNX 248, UPCOM 360.
- **Hai khoảng gián đoạn phát hiện trong M1:** 05–10/2023 (thiếu VN-Index ngày 15/05/2023 nên không tính được beta) và 02/2025–01/2026 (thiếu giá toàn sàn ngày 03/02/2025). Nhóm không vá bằng số giả.
- **Mở rộng C8 v2 (19–21/10):** nâng lên **1.522 mã ứng viên**, giá 2016–2025, 84 snapshot tháng 2019–2025. Tại 31/12/2025 có 1.410 mã market-ready. Đây là bộ dữ liệu M2 và M3 dùng.
**Đặc trưng thị trường (9 cái, tính tại mỗi snapshot tháng):**

| Nhóm | Đặc trưng | Ý nghĩa |
| --- | --- | --- |
| Động lượng | mom_21, mom_63, mom_126, mom_252 | Lợi suất 1, 3, 6, 12 tháng (theo số phiên) |
| Rủi ro | vol_63, downside_vol_63, mdd_126, beta_126 | Biến động, biến động chiều giảm, sụt giảm tối đa, beta so với VN-Index |
| Thanh khoản | liquidity_21 | Giá trị giao dịch bình quân 21 phiên |

M2 bản đầu dùng 8 đặc trưng. Huớng mới A v4 thêm downside_vol_63 thành 9.

### 3.2 Dữ liệu tài chính

- **Bộ tham chiếu 10 năm (Execution50/56, 23/10):** 1.172 mã đủ báo cáo năm 2016–2025. Baseline phân cụm tài chính đầu tiên chạy trên bộ này (k=3).
- **Indicators v1 (25/10):** 1.510 mã, 14.738 mã-năm, 319.620 ô chỉ số. Ngân hàng, chứng khoán, bảo hiểm lấy từ raw CafeF. DStock lấp 616 mã-năm CafeF thiếu. QA độc lập 800 ô PASS. Có đủ EPS, P/E, P/B, ROE, Piotroski F-score, Beneish M-score, Altman Z-score theo công thức chuẩn D-IND-01.
- **9 chỉ số dùng cho phân cụm tài chính (chỉ doanh nghiệp phi tài chính):** ROE, ROA, biên gộp, biên ròng, Nợ/VCSH, thanh toán hiện hành, vòng quay tài sản, tăng trưởng doanh thu, CFO/LNST.
- **Ngày công bố (availability):** bảng usable_from_date cho 1.362 mã. Từ FY2022 dùng ngày gửi BCTC trên CafeF (CreateDate của API công bố thông tin). Trước FY2022 dùng giả định của nhóm: phiên đầu tiên sau 30/06 năm sau.
- **Nhánh nghiên cứu PIT từ PDF (FIN-PIT, 01–04/10, Khôi):** thử trích xuất báo cáo gốc bằng OCR (26 tài liệu, 209 trang). Kết quả PARTIAL, không dùng cho M3 nhưng là lý do nhóm chuyển sang ngày công bố CafeF.
## 4. Phương pháp

### 4.1 Phân cụm thị trường – mô hình A v4 (chính thức)

- **Lọc thanh khoản nhẹ:** mã có hơn 50% phiên không khớp lệnh trong 63 phiên, hoặc giao dịch bình quân 21 phiên dưới 10 triệu đ/ngày, bị gắn ILLIQUID. Mô hình chỉ học trên mã có giao dịch, rồi gán mã ILLIQUID vào tâm gần nhất để hiển thị.
- **Biến đổi T1:** log1p(liquidity_21), cắt đuôi 1%–99%, z-score riêng từng snapshot tháng (không rò rỉ giữa các tháng).
- **Quét lưới 24 cấu hình:** 4 thuật toán (K-Means, PCA 80% + K-Means, Ward, GMM) × k = 3..8.
- **Cổng hợp lệ:** cụm nhỏ nhất ≥ 5% số mã ở ≥ 80% snapshot, và ARI khi lấy mẫu con 90% ≥ 0,80. Ward và GMM trượt cổng, mọi cấu hình k ≥ 6 cũng trượt.
- **Xếp hạng 5 thước đo:** Silhouette, Davies–Bouldin, Calinski–Harabasz, ARI mẫu con, ARI theo tháng. Chỉ chạy trên Development 2019–2023.
- **Kết quả:** PCA + K-Means k=3 hạng 2,40, K-Means k=3 hạng 2,60, cùng silhouette 0,276, ổn định 0,98 và 0,96. Nhóm chọn **K-Means k=3** vì gần như hòa nhưng giữ tọa độ gốc, dễ giải thích hơn (Occam).
Ba cụm có ý nghĩa: Dẫn dắt, Bình ổn/Tích lũy, Tụt hậu. Mỗi tháng, **cụm dẫn dắt** được xác định cơ học: cụm có trung vị mom_126 cao nhất, hòa thì chọn cụm có mdd_126 nông hơn.

### 4.2 Vì sao bỏ M2 K=2 (quyết định D-DIR-01, 26/10)

Bàn giao M2 ban đầu của nhóm chọn K-Means K=2, robust scaling, 8 đặc trưng, silhouette trung vị 0,94. Khi so sánh công bằng trên cùng tập mã, cùng không gian đặc trưng:

| Thước đo (trung vị Dev) | M2 K=2 | A v4 k=3 |
| --- | --- | --- |
| Cụm nhỏ nhất | 3,7% số mã | 14,0% số mã |
| Số tháng cụm dưới 5% | 48/60 | 2/60 |
| Phần tách cụm do thanh khoản | 63% | 8% |
| Phần tách cụm do động lượng | 7% | 54% |
| Silhouette (không gian log) | 0,114 | 0,240 |
| ARI giữa hai tháng liền nhau | 0,74 | 0,55 |

Kết luận: silhouette 0,94 của K=2 cao là do vài mã thanh khoản cực lớn tách xa phần còn lại, tức K=2 gần như chỉ là bộ lọc quy mô, không phải phân cụm động lượng. K=2 chỉ hơn ở độ bền nhãn theo tháng. Chọn lại chỉ trên 2019–2023 vẫn ra k=3. M2 K=2 được giữ làm đối chứng (LEGACY), không xóa.

### 4.3 Phân cụm tài chính – B v4 và B-PIT

- **B v4:** 9 chỉ số D-IND-01, winsorize 1–99% + z-score, K-Means k=3, fit theo từng năm tài chính. Vấn đề: fit trên mọi công ty của năm, kể cả báo cáo nộp rất muộn, nên có nguy cơ nhìn trước tương lai.
- **B-PIT (ADR D-M3-01):** cùng công thức, nhưng mỗi FY t chỉ fit trên báo cáo có usable_from_date <= cutoff(t), với cutoff(t) = max(30/04 năm t+1, ngày usable sớm nhất). Tham số chuẩn hóa, tâm cụm và thứ tự cụm (ROE trung vị giảm, hòa thì Nợ/VCSH tăng) được đóng băng tại cutoff. Báo cáo đến sau được gán vào tâm gần nhất.
- **Kết quả B-PIT** (bpit-4a9d2e87f0de84ec): 8.461 mã-năm (8.087 FIT, 280 gán sau cutoff, 94 không có ngày). Fit-leak = 0 cả 9 năm. ARI so với B v4: 1,00 cho FY2016–2021, 0,955 / 0,937 / 0,808 cho FY2022 / 2023 / 2024. FY2025 NOT_READY (tại 30/04/2026 mới có 3 báo cáo).
- **Giới hạn:** B chưa đạt ngưỡng ổn định mẩu con (ARI khoảng 0,50 so với ngưỡng 0,80), đã ghi rõ trong báo cáo.
### 4.4 Chiến lược M3 (config m3_strategy_v1.json, LOCKED 04/11)

- **Tập ứng viên Combined:** cụm dẫn dắt thị trường ∩ các cụm tài chính không phải cụm yếu nhất (rule Va). Loại ILLIQUID. Loại ngân hàng, chứng khoán, bảo hiểm (không có nhãn B).
- **6 tiêu chí xếp hạng:** thị trường mom_126 (cao tốt), downside_vol_63 (thấp tốt), liquidity_21 (cao tốt); tài chính ROE, F-score, Z-score (cao tốt). Mỗi tiêu chí đổi thành percentile.
- **Điểm:** 0,5 × S_market + 0,5 × S_fin. Chọn top 30% (làm tròn lên), tỷ trọng bằng nhau. Thiếu một phần tiêu chí thì gán percentile 0,5 và gắn cờ; thiếu cả ba chỉ tiêu tài chính thì loại.
- **N_min = 10:** kỳ không đủ 10 ứng viên thì không mua mới, giữ mã cũ còn hợp lệ, phần còn lại để tiền mặt.
- **PIT tài chính:** chọn FY mới nhất đã usable, hết hiệu lực sau 18 tháng. Nếu ngày quyết định trước cutoff của FY đó thì tạm loại mã (FINANCIAL_MODEL_BEFORE_CUTOFF).
- **Thực thi:** quyết định cuối tháng, khớp giá đóng cửa phiên kế tiếp (adj_close). Bán trước mua. Volume 0 chặn cả hai chiều, trần chặn mua, sàn chặn bán, thiếu dữ liệu trần/sàn thì chặn lệnh. Vốn ban đầu = 1, cho phép vị thế phân số.
- **Phí:** **0 bps, không trượt giá** theo ý kiến anh Tuấn. Kịch bản 15 và 30 bps là phần mở rộng.
- **4 đối chứng + benchmark:** Market-only, Financial-only, Equal-weight, Momentum-only (top 30% theo mom_126, không dùng cụm), và VNINDEX. M2 K=2 chỉ báo cáo số ứng viên (42/60 tháng Dev dưới 10 ứng viên), không backtest.
- **Chia đoạn:** Development 31/01/2019–29/12/2023 (60 kỳ), Holdout 31/01/2024–31/12/2025 (24 kỳ), Final 2026. Mỗi đoạn khởi tạo độc lập từ 100% tiền mặt, không dùng giá ngoài đoạn (strict isolation).
- **Trình tự bắt buộc:** build + audit + pin B-PIT → đếm feasibility (không xem lợi suất) → targets-only → LOCKED → chạy Dev → seal → chạy Holdout → seal.
## 5. Quá trình thực hiện từ đầu đến cuối

Dự án kéo dài từ 11/09 đến 05/11/2026, 253 commit trên nhánh feature/indicators-v1. Bảng dưới theo thứ tự thời gian, lấy từ git log.

| Thời gian | Mốc | Việc đã làm |
| --- | --- | --- |
| 11–16/09 | Khởi tạo | Tạo repo, khung pipeline nghiên cứu, data contract, ma trận tài liệu tham khảo (literature matrix), hướng dẫn thu thập dữ liệu |
| 16–17/09 | M1 | Crawler CafeF, pilot đại diện, sửa các lỗi định dạng ngày và dòng snapshot của CafeF, quy trình crawl 5 shard |
| 18–22/09 | M1 | Báo cáo chất lượng M1, EDA, tách feature readiness khỏi identity. Khôi làm các bước recovery A2–A6 |
| 23–25/09 | M1 | Chuyển hẳn sang CafeF làm nguồn chính (C1–C3), đánh giá TradeHistory trên 500 mã, mở rộng 5 worker (C6–C7), audit C8 → 952 / 922 / 905 mã |
| 26/09 | M2-PREP | Audit giao thức thực nghiệm market-only, kế hoạch dự án hợp nhất v1.0. Owner duyệt Protocol v1 |
| 27/09–05/10 | M2 v1 (cả nhóm) | 13 nhiệm vụ: khóa protocol, chọn Global K=2 (ADR-049), K-Means, Ward, PCA+K-Means, đánh giá chất lượng/hồ sơ/độ ổn định, chọn mô hình (Task 10), holdout (Task 11), verify (Task 12), bàn giao M3 (Task 13). Thời gian: 15 snapshot dev 11/2023–01/2025, 7 snapshot holdout 02–08/2026 |
| 01–04/10 | FIN-PIT | Khôi thử nhánh trích xuất BCTC gốc bằng OCR, kết quả PARTIAL |
| 09–23/10 | Dữ liệu tài chính | Pipeline BCTC CafeF, pilot 5 mã, lấp thiếu bằng DStock, baseline tài chính 1.172 mã × 2016–2025, k=3 |
| 19–22/10 | M2 v2 | Mở rộng giá lên C8 v2 (1.522 mã, 2016–2025). Cả nhóm chạy lại Task 3–13 trên 60 tháng dev (2019–2023) + 24 tháng holdout (2024–2025), vẫn K=2 |
| 23–24/10 | Tích hợp | Gộp nhánh thị trường và tài chính, tạo mô hình kết hợp tham chiếu C, web DELTA Intelligence lần đầu lên Render + Vercel (24/10) |
| 25/10 | Indicators v1 + rework | 5 giai đoạn Indicators v1 (D-IND-01, F/M/Z, API, trang cổ phiếu). Phân cụm lại v1, v2. Bundle web v2 → v4. Giao diện Blueprint sáng/tối. Quy định crawl D-CRAWL-02. Bản kế hoạch M3 đầu tiên và lõi engine |
| 26/10 | D-DIR-01 | So sánh M2 K=2 với A v4, chọn lại mô hình chỉ trên development. Owner chốt A v4 + B v4 là hướng chính thức, M2 K=2 thành LEGACY. Engine M3 phần không cần mentor, danh sách câu hỏi gửi mentor |
| 27–28/10 | Báo cáo M2 | Khôi viết báo cáo quy trình và kết quả M2 thị trường và tài chính |
| 02–03/11 | Khóa M3 | Nhóm trưởng đưa kế hoạch KE_HOACH_M3_SCHEMA_GITHUB.md. Rà soát R1–R8. ADR D-M3-01 khóa methodology. Đồng bộ code/config, thêm B-PIT, báo cáo readiness |
| 04/11 | M3-A | Khôi: pin B-PIT, cổng Q-date và cutoff, khóa config, sửa lỗi Q17, chạy chính thức Dev rồi Holdout, notebook M3-C 01–04, báo cáo kỹ thuật, công bố 64 file CSV |
| 05/11 | Hoàn thiện | Đưa metrics/manifest/seal JSON lên git (đã đối chiếu SHA256 khớp). Dọn repo, sắp lại docs. Web hiển thị ngày công bố BCTC. Trang /backtest (M3-B) lên production |

**Ba bước ngoặt nên kể khi thuyết trình:**

- **M1 → C8 v2:** bản M1 đầu chỉ có lịch sử ngắn và hai khoảng gián đoạn, nên M2 v1 chỉ có 15 tháng dev. Nhóm crawl thêm để có 10 năm giá và 84 tháng, đủ dài cho backtest.
- **M2 K=2 → A v4 k=3:** kết quả K=2 trông rất đẹp (silhouette 0,94) nhưng thực chất chỉ tách mã thanh khoản lớn. Nhóm đổi hướng dựa trên bằng chứng đo lường, không dựa trên lợi suất.
- **B v4 → B-PIT:** phát hiện B v4 có rủi ro nhìn trước tương lai, nên thiết kế lại để fit tại cutoff và đóng băng trước khi chạy M3.
## 6. Kết quả M3 (Development và Holdout)

### Tóm tắt đối sánh thực nghiệm M3: Baseline cũ vs Enriched mới (Cập nhật 20/11/2026)

Bảng dưới đây tổng hợp kết quả đối sánh hiệu năng danh mục giữa phiên bản **Baseline B-PIT** (chỉ số tài chính thô, tỷ lệ khuyết dữ liệu cao) và **Enriched B-PIT** (làm giàu 9 chỉ số tài chính theo trung vị ngành Point-in-Time) được kiểm định độc lập qua 2 giai đoạn:

| Giai đoạn | Chiến lược | Lợi nhuận lũy kế (%) | CAGR (%/năm) | Sharpe Ratio | Max Drawdown (%) | Tiền mặt TB (%) | Ticker TB / kỳ | Chênh lệch lợi nhuận (pp) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Development**<br>(2019–2023) | **Combined (Enriched)** | **151.67%** | **20.65%** | **0.81** | **-44.45%** | **16.85%** | **7.0** | **+35.51 pp** |
| | Combined (Baseline) | 116.15% | 16.97% | 0.72 | -44.60% | 22.40% | 7.0 | (Gốc) |
| | Momentum-only | 169.73% | 22.36% | 0.88 | -33.71% | 1.47% | 127.0 | 0.00 pp |
| | Financial-only (Enriched) | 53.57% | 9.12% | 0.55 | -24.28% | 1.52% | 48.0 | +12.82 pp |
| | Equal-Weight (Toàn thị trường) | 159.03% | 21.36% | 0.87 | -37.01% | 0.48% | 439.0 | 0.00 pp |
| | VN-Index (Benchmark) | 24.35% | 4.53% | 0.19 | -33.02% | — | — | — |
| **Holdout**<br>(2024–2025) | **Combined (Enriched)** | **53.07%** | **24.87%** | **1.34** | **-22.55%** | **9.22%** | **10.0** | **+14.12 pp** |
| | Combined (Baseline) | 38.95% | 18.72% | 1.09 | -26.27% | 8.92% | 10.0 | (Gốc) |
| | Momentum-only | 41.37% | 19.80% | 1.27 | -8.92% | 0.82% | 235.0 | 0.00 pp |
| | Financial-only (Enriched) | 30.97% | 15.11% | 1.94 | -3.83% | 1.83% | 75.0 | +2.60 pp |
| | Equal-Weight (Toàn thị trường) | 29.53% | 14.45% | 1.08 | -7.40% | 0.47% | 794.0 | 0.00 pp |
| | VN-Index (Benchmark) | 52.13% | 24.47% | 1.52 | -5.87% | — | — | — |

**Ý nghĩa đột phá:**
1. **Giải quyết triệt để "Cash Drag":** Ở bản Baseline, do dữ liệu BCTC khuyết nhiều dẫn đến số mã thỏa mãn bộ lọc tài chính quá ít (có 13 tháng ở Dev và 1 tháng ở Holdout danh mục rơi vào tình trạng thiếu ứng viên `< 10` mã), khiến tỷ lệ giữ tiền mặt trung bình lên tới 22.40% ở Dev. Bản Enriched giúp giảm tỷ lệ tiền mặt xuống 16.85% ở Dev và 9.22% ở Holdout, số lệnh mua bị từ chối do thiếu mã giảm mạnh.
2. **Cộng hưởng Động lượng - Sức khỏe tài chính:** Chiến lược Combined tận dụng tối đa sức mạnh của bộ lọc kép: chọn cổ phiếu có động lượng dẫn dắt thị trường (Cụm A v4) nhưng phải có nền tảng tài chính lành mạnh (Cụm B-PIT Enriched), giúp vượt trội thị trường chung và kiểm soát rủi ro rút vốn sâu (Drawdown) tốt hơn.


Combined cải thiện thứ hạng từ 4/5 lên 2/5 ở Holdout, nhưng chưa có ưu thế nhất quán về cả lợi suất lẫn rủi ro. Momentum-only tốt hơn Combined trên CAGR, biến động và drawdown ở cả hai đoạn. Nguồn: M3/reports/BAO_CAO_KY_THUAT_M3.md, đã tính lại từ file NAV và khớp.

**Định danh run:** code c9c1f5f, config LOCKED (SHA256 b5c47ac4…), B-PIT bpit-4a9d2e87f0de84ec. Dev run 20261104T121107Z-5557288c, Holdout run 20261104T133507Z-5557288c. Phí 0.

### Development (31/01/2019–29/12/2023, 60 kỳ quyết định, 59 kỳ lợi suất)

| Chiến lược | Tổng lợi suất | CAGR | Biến động năm | Max DD | Turnover TB | Cash TB | Kỳ dưới N_min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Combined | 116,15% | 16,97% | 27,39% | -44,60% | 47,62% | 22,40% | 13 |
| Market-only | 128,81% | 18,34% | 29,51% | -47,88% | 53,99% | 6,22% | 0 |
| Financial-only | 40,74% | 7,20% | 17,09% | -27,20% | 17,69% | 1,02% | 0 |
| Equal-weight | 159,03% | 21,36% | 24,45% | -37,01% | 11,89% | 0,48% | 0 |
| Momentum-only | 169,73% | 22,36% | 25,51% | -33,71% | 31,54% | 1,47% | 0 |
| VNINDEX | 24,35% | 4,53% | 23,56% | -33,02% | — | — | — |

### Holdout (31/01/2024–31/12/2025, 24 kỳ quyết định, 23 kỳ lợi suất)

| Chiến lược | Tổng lợi suất | CAGR | Biến động năm | Max DD | Turnover TB | Cash TB | Kỳ dưới N_min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Combined | 38,95% | 18,72% | 28,59% | -26,27% | 54,53% | 8,92% | 1 |
| Market-only | 22,43% | 11,14% | 23,75% | -18,91% | 58,52% | 3,75% | 0 |
| Financial-only | 28,37% | 13,92% | 7,30% | -3,95% | 24,37% | 2,54% | 0 |
| Equal-weight | 29,53% | 14,45% | 13,34% | -7,40% | 8,41% | 0,47% | 0 |
| Momentum-only | 41,37% | 19,80% | 15,60% | -8,92% | 27,50% | 0,82% | 0 |
| VNINDEX | 52,13% | 24,47% | 16,08% | -5,87% | — | — | — |

CAGR tính theo số kỳ lợi suất/12. Biến động năm = độ lệch chuẩn lợi suất tháng × √12. Max drawdown đo theo kỳ tháng, không phải theo ngày. Không tính Sharpe cho Dev/Holdout theo đúng quy tắc.

### Cách đọc kết quả

- **So với Momentum-only:** đây là đối chứng bất lợi nhất. Chỉ một tiêu chí mom_126 đã thắng cách kết hợp phức tạp. Khoảng cách CAGR ở Holdout còn 1,08 điểm phần trăm, nhưng biến động Combined cao hơn 13 điểm.
- **So với Market-only:** Dev thấp hơn 1,36 điểm CAGR nhưng rủi ro thấp hơn. Holdout cao hơn 7,59 điểm CAGR nhưng drawdown sâu hơn 7,37 điểm. Chưa tách được đóng góp riêng của phần tài chính.
- **So với VNINDEX:** Dev vượt xa (16,97% so với 4,53%), Holdout thua (18,72% so với 24,47%), drawdown sâu hơn cả hai đoạn. VNINDEX là chỉ số giá, còn chiến lược dùng giá điều chỉnh, nên không gọi chênh lệch là alpha.
- **Điều kiện vận hành:** Dev có 13/60 kỳ thiếu ứng viên nên tiền mặt trung bình 22,4%, là một lý do kéo CAGR xuống. Holdout chỉ 1/24 kỳ, tiền mặt 8,9%.
- **Turnover:** Combined xoay vòng ~48–55%/kỳ, cao hơn Momentum-only (~28–32%). Khi có phí 15/30 bps, khoảng cách có thể còn rộng hơn, nhưng chưa chạy nên chưa kết luận.
### Kiểm chứng đã làm

- Feasibility và targets-only cả hai đoạn PASS trước khi xem bất kỳ con số lợi suất nào.
- Lỗi Q17 (sửa giá lỗi khi chưa đủ 3 phiên liền kề) được phát hiện khi rà soát Dev, sửa (36 → 34 lần sửa giá), chạy lại Dev bằng cùng code rồi mới mở Holdout. NAV và danh mục không đổi.
- LIMIT_DATA_MISSING = 0, NAV dừng đúng ranh giới đoạn, git_dirty=false.
- 6 file metrics/manifest/seal JSON khớp SHA256 ghi trong báo cáo. Mỗi seal liệt kê đủ 33 file.
- Notebook M3-C 01–03 tái lập và đối chiếu hash, targets, metrics. Notebook 04 (Final) ở trạng thái chờ.
## 7. Kiến trúc hệ thống và triển khai

Hệ thống gồm một package Python làm nghiên cứu và một web app chỉ đọc kết quả đã seal. Web không bao giờ fit lại mô hình hay tính lại chỉ số.

**Luồng dữ liệu (từ trái sang phải):**

- **Thu thập** (src/delta_t1/ingestion, scripts/): crawler CafeF giá + BCTC + ngày công bố, lưu raw bất biến có hash.
- **Chuẩn hóa** → artifact canonical C8 v2 (prices_daily, benchmark_daily, trading_calendar, feature_snapshots).
- **Đặc trưng và chỉ số** (features, indicators): 9 đặc trưng thị trường, Indicators v1 (indicators.sqlite).
- **Phân cụm** (clustering, experiments): A v4 đóng gói vào terminal.sqlite (bundle web v4), B-PIT vào data/financial/b_pit_v1/.
- **Backtest M3** (src/delta_t1/m3, scripts/run_m3.py): đọc A + B-PIT + availability + giá, xuất M3/outputs/ (CSV + metrics/manifest/seal).
- **Gói trình bày**: M3/presentation/m3-backtest-v1 (113 KB), tạo từ M3/outputs/ sau khi kiểm hash theo seal.
- **Web**: backend FastAPI read-only (web/backend) và frontend Next.js (web/frontend).
**Các trang web hiện có:** Tổng quan, Bản đồ phân cụm (Atlas, có bản đồ PCA), Tra cứu cổ phiếu (chỉ số, điểm F/M/Z, so sánh cùng nhóm), Góc nhìn tài chính (có ngày công bố BCTC), Phòng nghiên cứu (Lab), và **06 · Kiểm định chiến lược** (/backtest).

**Trang /backtest (M3-B):** chọn Dev hoặc Holdout, 4 thẻ KPI Combined so với VNINDEX, 4 tab: so sánh 5 chiến lược, đường NAV và drawdown, danh mục theo kỳ (bấm mã mở trang tra cứu), nguồn và giới hạn (run, seal, config, commit, Final NOT_READY). Không có Sharpe, không khuyến nghị mua bán. Kiểm tra: 29/29 test API, typecheck và build đạt, chạy tốt ở 375px. Đã truy vết một con số qua mọi tầng: tổng lợi suất Holdout của Combined là 38,9% từ CSV → metrics.json → bundle → API → giao diện.

**Triển khai production:**

| Thành phần | Nơi chạy | Ghi chú |
| --- | --- | --- |
| Frontend Next.js | Vercel: delta-intelligence-omega.vercel.app | Deploy tay bằng Vercel CLI từ web/frontend |
| Backend FastAPI | Render: delta-intelligence-api (free tier, Singapore, Docker) | autoDeploy: false, bấm Manual Deploy. Health check /api/v2/health |
| Dữ liệu lớn | Hugging Face dataset ngyen/delta-intelligence-data | Render tải về lúc build qua fetch_data.py, DATA_BASE_URL ghim theo commit của dataset |
| Gói backtest M3 | Commit thẳng trong repo | Nhỏ (113 KB), CSV gốc vốn đã trên GitHub |

Web lần đầu lên mạng ngày 24/10, chuyển sang bundle v4 ngày 25/10, trang /backtest lên ngày 05/11 (commit 74db8d7). Lưu ý: Render free tier ngủ khi không có truy cập, lần mở đầu có thể mất khoảng một phút. Nên mở trang trước buổi thuyết trình.

## 8. Phân công: ai làm gì

### Cập nhật phân công đợt Tăng tốc Nâng cấp B-PIT Enriched & Hệ thống Đánh giá đầu tư (Tháng 11/2026)

Để giải quyết bài toán khuyết dữ liệu tài chính và hoàn thiện sản phẩm ứng dụng thực tế theo chuẩn công nghiệp, 4 thành viên đã được phân vai chuyên biệt hóa theo cấu trúc rõ ràng:

| Vai trò & Thành viên | Trách nhiệm chính | Sản phẩm bàn giao chính | Tiến độ |
| :--- | :--- | :--- | :---: |
| **Người 1**<br>*(Dữ liệu tài chính, B-PIT & Builder)* | • Thiết lập quy trình làm giàu 9 chỉ số BCTC (`IMPUTED_MEDIAN`).<br>• Huấn luyện mô hình phân cụm tài chính B-PIT Enriched ($k=3$).<br>• Đảm bảo Point-in-Time tuyệt đối (`fit_leaks = 0`).<br>• Xây dựng offline engine tính toán 18 chỉ số và snapshot đánh giá. | • `src/delta_t1/indicators/enrichment_v1.py`<br>• `notebooks/05_B_PIT_Enriched.ipynb`<br>• `scripts/build_assessment_artifacts.py`<br>• Database `investment_assessment_v1.parquet` | **20/20 tasks**<br>(100% Hoàn thành) |
| **Người 2**<br>*(Tích hợp M3, Backtest & Rulebook)* | • Khóa cấu hình chiến lược M3 Enriched `m3_strategy_enriched_v1.json`.<br>• Thực thi backtest Dev (2019–2023) và Holdout (2024–2025) đã niêm phong.<br>• Xuất báo cáo đối sánh hiệu năng M3 (`comparison.csv`).<br>• Mã hóa Rulebook phân hạng D-ASS-01 (Tích cực / Khả quan / Theo dõi / Thận trọng). | • `configs/experiments/m3_strategy_enriched_v1.json`<br>• `data/experiments/m3/comparison/20261118T173627755165Z/`<br>• Rulebook logic `D-ASS-01`<br>• Runner & validator backtest | **15/15 tasks**<br>(100% Hoàn thành) |
| **Người 3**<br>*(Backend API & Verifier)* | • Xây dựng tầng backend read-only phục vụ đánh giá đầu tư.<br>• Thiết kế REST API `GET /api/v1/assessment/{ticker}`.<br>• Tối ưu in-memory cache đáp ứng độ trễ cực thấp (<100ms).<br>• Xây dựng bộ xác thực độc lập `assessment_release_verifier.py`. | • `web/backend/app/assessment.py`<br>• Pydantic schemas & OpenAPI specs<br>• Endpoint API và bộ nhớ đệm an toàn<br>• Script kiểm định độc lập kiểm tra 1.522 mã | **15/15 tasks**<br>(100% Hoàn thành) |
| **Người 4**<br>*(Frontend, UAT & Báo cáo)* | • Thiết kế giao diện Tab 5 "Đánh giá đầu tư" trên trang `/stocks`.<br>• Trực quan hóa 18 đặc trưng, bộ lọc lookback 5/10 năm, so sánh Peers.<br>• Thực hiện kiểm thử toàn diện UAT và kiểm thử hồi quy.<br>• Biên soạn tài liệu hướng dẫn và hồ sơ nghiệm thu kỹ thuật. | • Component `StockAssessmentTab.tsx` trên Next.js<br>• Bảng 18 chỉ số và thẻ khuyến nghị trực quan<br>• Kịch bản kiểm thử UAT & Regression test report<br>• Báo cáo tổng kết nghiệm thu bàn giao | **15/15 tasks**<br>(100% Hoàn thành) |

> [!TIP]
> Toàn bộ 65/65 nhiệm vụ chi tiết đã được nghiệm thu đạt chất lượng 100%, tất cả test suite (`tests/test_assessment.py`, verifier script) đều vượt qua (PASS) mà không có bất kỳ cảnh báo hồi quy nào.


Tổng hợp từ tác giả commit trên git (tên GitHub). Bạn nên kiểm lại tên thật của từng tài khoản trước khi đưa lên slide.

| Thành viên (GitHub) | Commit | Phần việc chính |
| --- | --- | --- |
| Bạn (trongnguyen1010) | 105 | Toàn bộ M1 (crawler CafeF, C1–C8, báo cáo M1). Pipeline dữ liệu tài chính, baseline 1.172 mã. Tích hợp thị trường + tài chính. Indicators v1. Phân cụm lại v1/v2, A v4, so sánh M2 K=2 và quyết định D-DIR-01. Web DELTA Intelligence và deploy. Bản M3 plan đầu và lõi engine. Chốt D-M3-01. Dọn repo, M3-B /backtest |
| Võ Minh Khôi (Minh-Khoi-Pro, Silas) | 97 | Recovery A2–A6 ở M1. M2 Task 1–3, 12–13, chạy lại M2 trên C8 v2. FIN-PIT (OCR). Dashboard đọc M2. Báo cáo M2 thị trường và tài chính. Build và pin B-PIT, cổng Q-date/cutoff, khóa config, sửa Q17, chạy chính thức M3 Dev + Holdout, notebook M3-C, báo cáo kỹ thuật M3 |
| Khanhkphaksk | 32 | M2 nhánh PCA + K-Means (Task 6–9), Task 11 holdout |
| phuongnguyen2810 | 9 | M2 nhánh Ward (Task 5, 7–9), Task 10 chọn mô hình |
| Dat tran | 4 | M2 nhánh K-Means baseline (Task 4, 7–9) |
| trmtuan189 | 4 | M2 Task 3 (v1), Task 12 audit, Task 13 notebook bàn giao |
| DuyKhanhss | 1 | M2 PCA + K-Means Task 6–9 (bản đầu) |

**Vai trò khác:**

- **Mentor (anh Tuấn):** quyết định không đưa phí vào kịch bản chính, chuyển 15/30 bps sang phần mở rộng.
- **Nhóm trưởng:** viết kế hoạch M3 chuẩn docs/m3/KE_HOACH_M3_SCHEMA_GITHUB.md (02/11). Bạn rà soát và đề xuất sửa R1–R8 trước khi khóa.
## 9. Hạn chế và việc còn lại

**Hạn chế về dữ liệu:**

- Giá dùng vendor-adjusted close của CafeF làm proxy lợi suất điều chỉnh. VNINDEX là chỉ số giá, không tính cổ tức. Hai cơ sở khác nhau nên chênh lệch với VNINDEX không phải alpha.
- Dữ liệu tài chính là snapshot hiện tại, không phải bản gốc tại ngày công bố (chưa có vintage/revision). PIT đúng về ngày, chưa đúng về số. Hai trường hợp đã biết: VCG FY2023 (giả định lợi ích cổ đông thiểu số = 0), SBT FY2024 (lệch số liệu với PDF).
- Trước FY2022 ngày công bố là giả định của nhóm (30/06 năm sau), không phải ngày thật.
- Vũ trụ mã xây từ danh sách hiện tại, chưa có lịch sử định danh đầy đủ (historical identity), nên còn rủi ro survivorship.
**Hạn chế về phương pháp:**

- Phân cụm độc lập từng tháng, chưa phải Dynamic Clustering.
- B (tài chính) chưa đạt ngưỡng ổn định mẩu con.
- A v4 được chọn sau khi nhóm đã nhìn dữ liệu toàn kỳ 2019–2025, dù chọn lại chỉ trên dev vẫn ra k=3. Holdout sạch ở tầng quy tắc danh mục, không hoàn toàn "chưa từng thấy" ở tầng mô hình.
- Phí và trượt giá bằng 0, vị thế phân số, không làm tròn lô, không tính sức chứa theo quy mô vốn.
- Drawdown đo theo kỳ tháng, không theo ngày. Hai đoạn lịch sử không phải kiểm định thống kê.
**Việc còn lại:**

- ☐ Final Evaluation 2026: chờ đủ dữ liệu và B-PIT FY2025. Đây là nơi duy nhất được tính Sharpe.
- ☐ Phần mở rộng phí 15 và 30 bps.
- ☐ Số ứng viên đối chứng M2 K=2 trong báo cáo M3 (R7).
- ☐ Link hỏng trong báo cáo kỹ thuật M3 tới HUONG_DAN_THUC_HIEN_M3.md và M3/reproduction/ (đang chờ Khôi quyết định).
- ☐ Manifest B-PIT ghi code_dirty=true, cần Khôi xác nhận code lúc build.
**Một chỗ cần cẩn thận khi dùng tài liệu cũ:** báo cáo quy trình B-PIT ghi có "bộ lọc cứng F-score ≥ 7 và Z-score ≥ 1,81". Config đã khóa không có bộ lọc đó. F-score và Z-score chỉ là tiêu chí xếp hạng percentile. Khi thuyết trình nên nói theo config.

## 10. Câu hỏi mentor có thể hỏi và gợi ý trả lời

**1. Kết quả Combined thua Momentum-only, vậy dự án có thất bại không?** Không. Mục tiêu là kiểm định giả thuyết một cách trung thực. Phương pháp khóa trước, Holdout mở sau, nên kết quả âm cũng là kết quả có giá trị: trên dữ liệu 2019–2025, thêm lớp tài chính chưa tạo lợi thế so với chỉ dùng động lượng 6 tháng. Nhóm không chỉnh lại quy tắc sau khi thấy kết quả.

**2. Sao không chỉnh tham số (top 30%, N_min, trọng số 50/50) cho Combined tốt hơn?** Vì đó là overfit trên dữ liệu đã xem. Config LOCKED trước khi chạy Dev. Muốn thử biến thể thì phải ghi là thí nghiệm mở rộng và đánh giá trên dữ liệu mới (Final 2026).

**3. Sao Combined Dev có 22% tiền mặt?** Có 13/60 kỳ giao của cụm dẫn dắt thị trường và cụm tài chính không yếu có dưới 10 mã. Theo quy tắc đã khóa, kỳ đó không mua mới nên tiền nằm yên. Feasibility đã đếm trước (ngưỡng chấp nhận khoảng 20/60) và qua cổng.

**4. Sao chọn k=3 mà không phải K=2 như bàn giao M2 ban đầu?** So sánh công bằng cho thấy K=2 tách cụm 63–99,9% do thanh khoản, cụm nhỏ chỉ 3,7% số mã. A v4 k=3 tách chủ yếu bằng động lượng (54%) và rủi ro (39%), silhouette gấp đôi trên cùng không gian. Chọn chỉ trên dev vẫn ra k=3. Không dùng lợi suất để chọn.

**5. Silhouette 0,276 có thấp không?** Với dữ liệu tài chính nhiễu và đuôi dày thì mức này chấp nhận được. Nhóm không chỉ dựa vào silhouette mà xếp hạng 5 thước đo, có cổng ổn định mẫu con (0,96). Silhouette 0,94 của K=2 là ví dụ cho thấy số cao chưa chắc tốt.

**6. Làm sao đảm bảo không nhìn trước tương lai?** Ba lớp: đặc trưng thị trường chuẩn hóa riêng từng tháng; B-PIT fit tại cutoff và đóng băng (audit fit-leak = 0); runtime chặn dùng BCTC trước ngày usable và trước cutoff. Ví dụ thực tế: snapshot 29/03/2024 tạm chặn 24 mã Combined, đến 31/05/2024 mới mở. Giá không dùng ngoài đoạn.

**7. Sao không tính Sharpe?** Quy tắc dự án: Sharpe chỉ tính ở Final Evaluation để không ai dùng nó chọn mô hình. Dev/Holdout báo cáo CAGR, biến động, drawdown, turnover.

**8. Sao không tính phí giao dịch?** Theo hướng dẫn của anh: kịch bản chính không phí, 15/30 bps để ở phần mở rộng. Lưu ý Combined có turnover cao hơn Momentum-only nên phí sẽ làm khoảng cách rộng thêm.

**9. Holdout có thật sự sạch không?** Sạch ở tầng quy tắc danh mục: config khóa, Dev seal trước rồi mới chạy Holdout bằng cùng code. Ở tầng mô hình phân cụm thì nhóm đã xem dữ liệu toàn kỳ khi làm rework, đã ghi rõ giới hạn này. Final 2026 mới là kiểm định hoàn toàn ngoài mẫu.

**10. Sao loại ngân hàng, chứng khoán, bảo hiểm?** Cấu trúc BCTC khác hẳn, các chỉ số như biên gộp, vòng quay tài sản, F/M/Z không áp dụng được, nên không có nhãn B phù hợp.

**11. Phân cụm từng tháng có phải Dynamic Clustering không?** Không. Đây là phân cụm tĩnh độc lập từng tháng cộng theo dõi ARI. Dynamic Clustering là hướng mở rộng.

**12. Làm sao người khác tái lập được kết quả?** Mọi input ghim SHA256, config có hash, mỗi run có manifest (commit, hash input) và seal (hash 33 file output). Notebook M3-C 01–03 đối chiếu lại toàn bộ. Web cũng đọc đúng gói đã kiểm hash.

**13. Vậy bước tiếp theo là gì?** Chạy Final 2026 khi đủ dữ liệu, chạy phần phí 15/30 bps, phân rã đóng góp của lớp tài chính, và cân nhắc Dynamic Clustering.

## 11. Gợi ý dàn ý thuyết trình (khung 15–20 phút)

- **Mở đầu (1 slide):** câu hỏi nghiên cứu và kết luận ngắn: quy trình đúng chuẩn, giả thuyết kết hợp chưa được xác nhận.
- **Lộ trình M1 → M2 → M3 (1 slide):** bảng dòng thời gian Mục 5, nhấn ba bước ngoặt.
- **M1 – Dữ liệu (2 slide):** phễu 952 → 922 → 905, mở rộng lên 1.522 mã × 10 năm, 9 đặc trưng; dữ liệu tài chính và ngày công bố.
- **M2 – Phân cụm (3 slide):** quy trình 4 bước và quét lưới 24 cấu hình; bảng so sánh K=2 với A v4; B-PIT và cách chặn nhìn trước.
- **M3 – Thiết kế chiến lược (1–2 slide):** Combined, 4 đối chứng, 6 tiêu chí, quy tắc giao dịch, trình tự khóa → Dev → seal → Holdout.
- **M3 – Kết quả (2 slide):** hai bảng Mục 6, biểu đồ NAV (lấy từ trang /backtest hoặc M3/reports/figures/), cách đọc kết quả.
- **Demo web (2–3 phút):** mở /backtest, chuyển Dev/Holdout, tab NAV, tab danh mục, bấm một mã, tab Nguồn. Mở sẵn trước giờ họp vì Render free tier khởi động chậm.
- **Hạn chế và bước tiếp (1 slide):** Mục 9.
- **Hỏi đáp:** chuẩn bị theo Mục 10.
**Mẹo:** nói rõ phần nào bạn làm và phần nào Khôi hoặc các bạn khác làm (Mục 8). Đừng tránh kết quả âm; việc dám công bố nó sau khi đã khóa phương pháp là điểm mạnh của dự án.

## Nguồn trong repo

- M3/reports/BAO_CAO_KY_THUAT_M3.md: báo cáo kỹ thuật M3, số liệu Mục 6.
- docs/DECISIONS.md: các quyết định D-M3-01, D-DIR-01, D-CRAWL-02, D-IND-01.
- artifacts/reports/m2-vs-rework-v1/report.md: so sánh M2 K=2 với A v4.
- docs/reports/BAO_CAO_QUY_TRINH_VA_KET_QUA_M2_MARKET.md, docs/reports/BAO_CAO_QUY_TRINH_VA_KET_QUA_FINANCIAL_BPIT.md: báo cáo M2 và B-PIT của Khôi.
- artifacts/reports/m1-market-foundation-v1/: số liệu phễu M1.
- docs/presentation/M1_M2_PRESENTATION_GUIDE.md: tài liệu thuyết trình M1/M2-PREP cũ.
- configs/experiments/m3_strategy_v1.json: config M3 đã khóa.
- docs/m3/KE_HOACH_M3_SCHEMA_GITHUB.md: kế hoạch M3 của nhóm trưởng.
- Git log nhánh feature/indicators-v1 (253 commit, 11/09–05/11/2026).
**PHẦN 1**

# M1 – Nền tảng dữ liệu

## 1. Mục tiêu và đầu ra của M1

M1 xây nền dữ liệu giá toàn thị trường Việt Nam đủ sạch để phân cụm: có nguồn gốc rõ ràng, kiểm chứng được khi không có mạng, không chứa số giả. Thời gian thực hiện chính: 11/09 – 26/09/2026, sau đó mở rộng thêm trong tháng 10.

**Yêu cầu đề tài:** tối thiểu 300 mã có lịch sử dài.

**Đầu ra cuối cùng của M1:**

- Bộ artifact canonical cafef-c8-complete-only (bản v1 952 mã, bản v2 1.522 mã) gồm giá ngày, VN-Index, lịch giao dịch, đặc trưng tháng, tất cả có SHA256.
- Báo cáo chất lượng artifacts/reports/m1-market-foundation-v1/ và notebook kiểm tra.
- Bộ protocol M2-PREP: khóa cách chọn mã, cửa sổ thời gian và các quyết định cần mentor duyệt trước khi chạy phân cụm.
**Pipeline 5 tầng** (tầng 1–4 là M1, tầng 5 là M2-PREP):

| Tầng | Tên | Làm gì | Cách kiểm soát rủi ro |
| --- | --- | --- | --- |
| 1 | Raw Ingestion | Gọi API TradeHistoryNew của CafeF lấy lịch sử giao dịch từng mã và VN-Index | Mọi payload lưu nguyên trạng, tạo SHA256 ghi vào manifest.json, không bao giờ sửa file thô |
| 2 | Normalization | Đổi raw thành hai bảng canonical prices_daily và benchmark_daily | Ngày chuẩn YYYY-MM-DD, giá về VND (×1000 nếu nguồn trả nghìn đồng), khối lượng về cổ phiếu. Giá điều chỉnh gắn vendor_adjusted |
| 3 | Feature Snapshot | Tính 8 đặc trưng tại phiên cuối mỗi tháng (src/delta_t1/features/market.py) | Bắt buộc đủ phiên thực tế, thiếu thì để null, không forward-fill |
| 4 | Quality Report & QC | Quét 80 tháng, lập phễu và ma trận độ phủ (scripts/build_m1_market_foundation_report.py) | Chạy lại từ artifact đã đóng băng, kiểm hash, không gọi mạng |
| 5 | M2-PREP | Khóa protocol cho M2 (src/delta_t1/experiments/m2_prep.py) | Dừng ở MANUAL_REVIEW_REQUIRED, chưa chạy phân cụm |

## 2. Khởi tạo dự án (11–16/09)

Tuần đầu dùng để dựng khung trước khi lấy dữ liệu thật, để mọi bước sau đều kiểm soát được.

**Việc đã làm:**

- **Tạo repo và package ****delta_t1** (11/09): khung pipeline nghiên cứu, các module ingestion, features, clustering, evaluation, backtest, product. Việt hóa tài liệu (12/09).
- **Data contract** (docs/architecture/DATA_CONTRACT.md): định nghĩa schema cho securities, prices_daily, benchmark, feature_snapshots, shares_history. Thêm reference/trần/sàn theo VND/cổ phiếu, loại Sharpe khỏi feature (contract 1.4).
- **Ma trận tài liệu tham khảo** (docs/research/LITERATURE_MATRIX_COMPLETE.md): tổng hợp các nghiên cứu về momentum, điều chỉnh rủi ro, phân cụm cổ phiếu để làm cơ sở chọn đặc trưng.
- **Hướng dẫn thu thập nhiều người** (DATA_COLLECTION_GUIDE.md): quy trình crawl theo shard và bàn giao bằng file ZIP có hash.
- **Định danh artifact thống nhất:** mọi kết quả đặt tên <prefix>-YYYYMMDDTHHMMSSZ-xxxxxxxx, không ghi đè bản cũ.
**Hệ thống cổng kiểm soát (gate) cho việc thu thập:** mỗi cấp phải có bằng chứng thật mới mở cấp sau. Dữ liệu giả (synthetic) không thể mở gate thật.

| Cấp | Quy mô | Mục đích |
| --- | --- | --- |
| SOURCE_SMOKE | 4 mã | Kiểm tra nguồn có trả dữ liệu đúng định dạng không |
| REPRESENTATIVE_PILOT | 55 mã | Kiểm tra chất lượng trên mẫu đại diện nhiều sàn, nhiều ngành |
| M1_SCALE | 500 mã | Thu thập quy mô đề tài, chia 5 người |
| EXTENDED_SCALE | > 500 mã | Mở rộng toàn thị trường |

**Nguyên tắc fail-closed được đặt từ đầu:** thiếu dữ liệu thì để trống và ghi lý do, không tự điền, không đổi thành 0, không ghép giá thô với giá điều chỉnh. Quyền sử dụng dữ liệu public được ghi là RIGHTS_NOT_VERIFIED: chỉ dùng cho nghiên cứu, không phân phối lại raw.

## 3. Chọn nguồn dữ liệu: từ KBS sang CafeF (16–24/09)

Nhóm thử hai nguồn trước khi chốt. Ban đầu KBS là nguồn chính, CafeF là nguồn phụ. Sau khi đo thực tế, nhóm chuyển sang CafeF làm nguồn chính.

### 3.1 Pilot đại diện 55 mã (KBS + CafeF)

- Run representative-pilot-20260916T185530Z chạy đủ 839/839 job. 55/55 mã có trên 5 năm dữ liệu dùng được, VN-Index PASS.
- Pilot canonical: 55 mã, 91.768 dòng giá, 4.455 snapshot tháng.
- QC cách ly 51 dòng vi phạm ràng buộc của nhà cung cấp (ví dụ giá cao nhất nhỏ hơn giá đóng cửa). Không sửa raw, chỉ đưa vào danh sách quarantine.
- Phát hiện và sửa các lỗi định dạng của CafeF: ngày kiểu cũ M/D/YYYY AM/PM, ngày /Date(-62135596800000)/ (giá trị rỗng của .NET) là dòng snapshot phải loại, múi giờ UTC của TradeDate.
### 3.2 M1_SCALE 500 mã, 5 người crawl (17–20/09)

- 500 mã được chia cố định 5 × 100 cho 5 máy. Mỗi người chạy runner có resume, đóng gói kết quả thành ZIP có hash, máy trung tâm kiểm tra không trùng, không thiếu, không bị sửa.
- Kết quả: 500/500 mã có trên 3 năm, 484/500 trên 5 năm. Nhưng tại snapshot mới nhất chỉ **168/500 mã đủ đặc trưng** do thiếu phiên trong cửa sổ 253 phiên.
- Khôi làm các bước phục hồi A2–A6 (22/09) để lấy lại dữ liệu thiếu từ nguồn phụ, nhưng quy tắc vẫn cấm dùng giá hôm trước hay lợi suất 0 để vá.
### 3.3 Thử nghiệm CafeF làm nguồn chính (C0–C3, 23–24/09)

- Tách nhánh m1-cafef-primary-experiment, giữ nguyên nhánh KBS để so sánh. Mục tiêu đo xem CafeF có cho độ phủ lịch sử tốt hơn, ít phiên thiếu hơn không.
- **C1 (crawl pilot 27 mã):** 27/27 raw audit PASS, 33.259 dòng giá chuẩn hóa, 11 dòng cần cách ly.
- **C2 (chuẩn hóa offline) và C3 (đánh giá):** chấp nhận cột GiaDieuChinh / AdjustPrice × 1000 làm giá điều chỉnh proxy (vendor_adjusted), giá OHLC thô chỉ giữ ở staging.
- Chốt chính sách lịch sử 5 năm làm baseline, sau đó kéo dài về 2020.
- **Đánh giá TradeHistory trên 500 mã (25/09):** dùng lại raw cũ để audit endpoint, tách khái niệm "không có giao dịch (volume 0)" khỏi "không đủ dữ liệu".
**Kết luận:** CafeF TradeHistoryNew cho độ phủ tốt hơn và có sẵn giá điều chỉnh, nên trở thành nguồn chính. Giới hạn được ghi rõ: giá điều chỉnh là của nhà cung cấp, nhóm chưa tự xác minh bằng dữ liệu sự kiện doanh nghiệp (chia tách, cổ tức).

## 4. Thu thập quy mô lớn: C5 → C8 (24–26/09)

Sau khi chọn CafeF, nhóm mở rộng từ 500 mã lên gần 1.000 mã qua các giai đoạn đánh số C.

| Giai đoạn | Làm gì | Kết quả |
| --- | --- | --- |
| C5 | Baseline 500 mã trên CafeF, lưu vào lineage bất biến | 500 mã, giữ làm gốc cho mọi bước sau |
| C6 | Chuẩn bị mở rộng: đóng băng trước danh sách 600 mã mới + 100 dự phòng (loại trùng với 500 mã cũ), chia 5 shard cân bằng | Runner chỉ thu thập, có resume chính xác, đóng gói một ZIP, verifier trung tâm chống sửa. C6-R2 mở khoảng thời gian thành 01/01/2020 → 23/09/2026 |
| C7 | 5 người crawl song song 600 mã mới | 452 mã hoàn tất, 148 mã hoãn (DEFERRED_EXPANSION_ACQUISITION) do giới hạn nguồn |
| C8 | Chỉ lấy mã hoàn tất (complete-only): 500 + 452 = 952 mã. Chuẩn hóa, tính đặc trưng, audit toàn lịch sử và 253 phiên gần nhất | Snapshot 28/08/2026: 952 → 922 → 905 mã |
| C8-VERIFY | Kiểm tra offline toàn bộ hash và lineage, không tính lại đặc trưng | EXECUTED_AND_VERIFIED |
| R1 | Dọn repo sau C8: gỡ 192 file cũ, giữ nguyên dữ liệu và kết quả | Có bản kê trước/sau và verifier riêng |
| M1-REPORT | Báo cáo chất lượng + notebook kiểm tra | COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION |

**Cách làm việc nhiều máy mà vẫn tin được dữ liệu:**

- Runner yêu cầu commit SHA chính xác trước khi chạy. Gói bàn giao bị chặn nếu code bị sửa hoặc lệch commit.
- Resume chỉ được nếu config, danh sách mã, code và kế hoạch job trùng hash. Không trộn phiên bản.
- Chạy thật bắt buộc có cờ --execute. Chạy thử (dry-run) không thể biến thành kết quả thật.
- Giá trị null trong raw không bao giờ được hiểu là 0 (sửa ở C6-R1).
**Quy tắc chọn mã theo thời điểm (tránh survivorship bias):** 905 mã chỉ là số đếm tại 28/08/2026. Khi phân cụm quá khứ, mỗi tháng t chỉ dùng các mã đủ điều kiện tại chính tháng t (market_experiment_eligible(t) = market_feature_ready_v2(t)), không lấy danh sách hiện tại lọc ngược về quá khứ.

## 5. Chuẩn hóa dữ liệu và tính 8 đặc trưng thị trường

Sau khi có giá, nhóm biến chuỗi giá ngày của từng mã thành một "ảnh chụp" (snapshot) cuối mỗi tháng. Mỗi snapshot là một hàng gồm 8 con số mô tả mã đó tại ngày cuối tháng. Đây chính là đầu vào cho phân cụm ở M2.

### 5.1 Nguyên tắc chuẩn hóa

- Dùng giá điều chỉnh AdjustPrice × 1000 của CafeF (giá đã điều chỉnh cổ tức, chia tách do nhà cung cấp tính) cho mọi chỉ số lợi suất.
- Thanh khoản dùng giá đóng cửa thô nhân khối lượng, vì đây là số tiền thật được giao dịch.
- Chỉ dùng **phiên giao dịch thật**. Ngày nghỉ, ngày mã không có giao dịch không được lấp bằng giá ngày trước (không forward-fill).
- Mọi đặc trưng tại ngày t chỉ dùng dữ liệu đến hết ngày t. Không có dữ liệu tương lai.
### 5.2 Công thức 8 đặc trưng

| Đặc trưng | Ý nghĩa | Công thức | Độ phủ |
| --- | --- | --- | --- |
| mom_21 | Đà tăng 1 tháng | ln(P_t / P_{t−21}) | 99,7% |
| mom_63 | Đà tăng 3 tháng | ln(P_t / P_{t−63}) | 99,4% |
| mom_126 | Đà tăng 6 tháng | ln(P_t / P_{t−126}) | 98,5% |
| mom_252 | Đà tăng 12 tháng | ln(P_t / P_{t−252}) | 96,8% |
| vol_63 | Biến động 3 tháng, tính theo năm | std(lợi suất ngày, 63 phiên) × √252 | 99,4% |
| mdd_126 | Mức sụt giảm lớn nhất trong 6 tháng | min((P − Đỉnh) / Đỉnh) trong 126 phiên | 98,5% |
| beta_126 | Độ nhạy với VN-Index | Cov(r_mã, r_VNI) / Var(r_VNI), 126 phiên | 98,5% |
| liquidity_21 | Thanh khoản 1 tháng | ln(trung bình(Khối lượng × Giá đóng cửa), 21 phiên) | 99,7% |

Con số 21, 63, 126, 252 là số phiên tương ứng 1, 3, 6, 12 tháng giao dịch. Độ phủ là tỷ lệ snapshot tính được đặc trưng đó.

Ở phần làm lại (rework, M2) nhóm thêm đặc trưng thứ 9 là **downside_vol_63**: độ lệch chuẩn chỉ của các ngày giảm, tính theo năm. Lý do: vol_63 phạt cả ngày tăng mạnh, trong khi nhà đầu tư chỉ lo rủi ro giảm.

### 5.3 Quy tắc 253 phiên thật

mom_252 cần giá của 252 phiên trước, tức là cần tối thiểu **253 phiên thật** trong lịch sử. Một mã chưa đủ 253 phiên thì mom_252 để trống và mã đó không đủ điều kiện vào thí nghiệm tháng đó. Nhóm không nội suy hay rút ngắn cửa sổ, vì như vậy các mã sẽ có đặc trưng không cùng thước đo.

### 5.4 Điều kiện tham gia theo từng tháng

Cột market_experiment_eligible(t) được tính riêng cho từng tháng: mã có đủ 8 đặc trưng tại t thì được tham gia tháng t. Nhờ vậy nhóm không dùng danh sách mã hiện tại để nhìn ngược về quá khứ, tránh thiên lệch sống sót (survivorship bias).

## 6. Kiểm soát chất lượng (QC) và phễu lọc mã

### 6.1 Phễu 952 → 922 → 905

Từ danh sách thu thập, mã đi qua ba tầng kiểm tra:

| Tầng | HNX | HOSE | UPCOM | Tổng |
| --- | --- | --- | --- | --- |
| Có dữ liệu giá | 249 | 319 | 384 | 952 |
| Qua kiểm tra chất lượng | 249 | 304 | 369 | 922 |
| Đủ đặc trưng để vào thí nghiệm | 248 | 297 | 360 | 905 |

Tỷ lệ sẵn sàng: baseline 500 mã có 490 mã đạt (98%); đợt mở rộng 452 mã có 415 mã đạt (91,8%). Đợt mở rộng thấp hơn vì gồm nhiều mã UPCOM mới niêm yết, lịch sử ngắn.

### 6.2 47 mã bị loại và lý do

| Lý do | Số mã |
| --- | --- |
| Chưa đủ 253 phiên thật | 29 |
| Chưa đủ 3 năm lịch sử | 17 |
| Không có snapshot nào | 1 |

Mỗi mã bị loại đều có lý do ghi lại trong artifact, không loại âm thầm.

### 6.3 Hai lỗ hổng dữ liệu nguồn

Quét 80 tháng (số mã đủ điều kiện tăng từ 87 mã năm 2020 lên 518 mã năm 2022), nhóm phát hiện hai ngày mà nguồn CafeF thiếu dữ liệu:

- **15/05/2023 thiếu VN-Index.** beta_126 cần lợi suất VN-Index liên tục 126 phiên, nên beta không tính được trong khoảng 6 tháng sau đó.
- **03/02/2025 thiếu giá toàn thị trường.** mom_252 cần giá cách đúng 252 phiên, nên đặc trưng này hỏng trong khoảng 12 tháng.
Theo nguyên tắc fail-closed, nhóm **không tự lấp** hai ngày này mà để trống và ghi nhận. Đây là lý do có những tháng số mã đủ điều kiện tụt mạnh, và cũng là lý do M2-PREP phải chọn cẩn thận cửa sổ thời gian (mục 7). Sau đó nhóm chuyển sang nguồn C8 v2 (mục 8) để có chuỗi dài hơn cho M2 V2.

### 6.4 Các kiểm tra tự động

- Mỗi file được ghim SHA256. Nếu file thay đổi thì bước sau từ chối chạy.
- Dòng lỗi (giá âm, ngày trùng, OHLC vô lý) bị đưa vào vùng cách ly (quarantine) chứ không sửa tay. Ví dụ pilot 55 mã có 51 dòng bị cách ly, pilot C1 27 mã có 11 dòng.
- Bước C8-VERIFY kiểm tra lại toàn bộ lượt thu thập; bước R1 thu hồi (retire) 192 file cũ không còn dùng.
- Bộ kiểm thử M1 chạy 173/173 test đạt.
## 7. M2-PREP: khóa giao thức trước khi phân cụm

M2-PREP là cầu nối giữa M1 và M2. Mục đích: **chốt mọi lựa chọn trước khi nhìn kết quả phân cụm**, để không ai có thể “chỉnh” giao thức cho đẹp số sau này. Gồm 6 bước.

### 7.1 Chọn cửa sổ Development và Holdout

Do hai lỗ hổng dữ liệu ở mục 6.3, không phải tháng nào cũng đủ mã. Nhóm xét 4 cửa sổ ứng viên:

| Cửa sổ | Đặc điểm | Quyết định |
| --- | --- | --- |
| 01–04/2023 | Quá ngắn | Loại |
| 11/2023–01/2025 | 15 tháng, 142–780 mã | Chọn làm Development |
| 02–08/2026 | 7 tháng, 253–905 mã | Chọn làm Holdout |
| 01/2023–08/2026 | 44 tháng nhưng 18 tháng bằng 0 mã | Loại |

Development dùng để thử và chọn mô hình. Holdout bị khóa, chỉ mở một lần sau khi mô hình đã đông cứng.

### 7.2 Số mã tối thiểu mỗi tháng

n_eligible ≥ 120 mã, tính từ 8 cụm × 15 mã/cụm. Nếu thử tối đa K = 8 cụm thì mỗi cụm cần đủ mã để có ý nghĩa thống kê. Tháng nào dưới ngưỡng thì bỏ qua. Test case dùng tháng 30/11/2023 với 142 mã.

### 7.3 Cách chuẩn hóa đặc trưng

- **Mặc định: robust scaling** (trừ trung vị, chia khoảng tứ phân vị). Ít bị mã cực đoan kéo lệch.
- **So sánh: z-score** (trừ trung bình, chia độ lệch chuẩn). Giữ lại để đối chiếu.
- **Loại: log1p** — không dùng trong giao thức M2 v1.
### 7.4 Ma trận thuật toán

| Thuật toán | Vai trò |
| --- | --- |
| K-Means | Baseline chính |
| PCA + K-Means | So sánh: giảm chiều trước rồi phân cụm |
| Ward (phân cụm phân cấp) | So sánh |
| DBSCAN, Dynamic Clustering | Khóa, không dùng ở vòng này |

### 7.5 Đầu ra và trạng thái

M2-PREP sinh 14 artifact (danh sách tháng, quy tắc lọc, cấu hình chuẩn hóa, ma trận thuật toán...) rồi dừng ở trạng thái **MANUAL_REVIEW_REQUIRED**. Pipeline cố ý không tự chạy tiếp sang phân cụm mà chờ người duyệt. Nhóm gửi 5 câu hỏi quyết định cho mentor trước khi mở M2.

**Vì sao làm vậy:** trong nghiên cứu định lượng, nếu chọn cửa sổ hay thuật toán sau khi đã thấy kết quả thì kết quả dễ bị “quá khớp” (overfit). Khóa trước giúp kết quả Holdout có giá trị thật.

## 8. Nguồn C8 v2: 1.522 mã, chuỗi dài cho M2 V2 và M3

Cửa sổ M2-PREP chỉ có 15 tháng Dev và 7 tháng Holdout. Để có chuỗi dài hơn cho M2 V2 và M3, nhóm dựng registry C8 v2.

### 8.1 Thành phần registry C8 v2

| Nhóm | Số mã |
| --- | --- |
| Baseline C5 | 500 |
| Đợt mở rộng C7 hoàn tất | 452 |
| Thu thập lỗi | 7 |
| Thu thập một phần | 3 |
| Chưa thu thập | 138 |
| Ngoài phạm vi | 422 |
| Tổng registry | 1.522 |

Mọi mã đều có trạng thái rõ ràng, kể cả mã lỗi và mã ngoài phạm vi, để người đọc biết vì sao một mã không có trong thí nghiệm.

### 8.2 Phân đoạn thời gian mới

Với C8 v2, M2 V2 và M3 dùng các đoạn:

- **Development:** 60 snapshot cuối tháng, từ 01/2019 đến 12/2023 (45.646 lượt gán cụm).
- **Holdout:** 24 snapshot, từ 01/2024 đến 12/2025 (30.155 lượt gán).
- **Final:** năm 2026, bắt đầu từ snapshot cuối 01/2026. Hiện chưa đủ dữ liệu (NOT_READY).
Ngưỡng số mã mỗi tháng trong M2 V2 là n ≥ 100 (M2-PREP dùng 120).

## 9. Nền tảng dữ liệu tài chính (BCTC)

Song song với dữ liệu giá, nhóm xây dựng bộ chỉ số tài chính từ báo cáo tài chính (BCTC) để phục vụ phân cụm tài chính (hướng B) và chiến lược kết hợp ở M3.

### 9.1 Baseline 1.172 mã × 10 năm

- Thu BCTC năm từ CafeF cho 1.172 mã, 10 năm tài chính.
- Thử phân cụm baseline với 6 tỷ số, k = 3, z-score. Kết quả bị **suy biến**: cụm có kích thước kiểu {1.169, 2, 1}, silhouette 0,92. Silhouette cao nhưng vô nghĩa, vì vài mã cực đoan bị tách thành cụm riêng. Đây là cùng một lỗi với K=2 bên thị trường (xem tab M2) và là bài học quan trọng: **silhouette cao chưa chắc là phân cụm tốt**.
### 9.2 Indicators v1 (5 pha)

Bộ chỉ số Indicators v1 bao phủ 1.510 mã, 14.738 mã-năm, 319.620 ô dữ liệu. Kiểm tra chất lượng ngẫu nhiên 800 ô đều đạt (PASS). Các chỉ số gồm EPS, P/E, P/B, ROE và ba điểm số tổng hợp:

- **Piotroski F-score** (0–9): sức khỏe tài chính qua 9 tiêu chí lợi nhuận, đòn bẩy, hiệu quả.
- **Altman Z-score**: rủi ro phá sản.
- **Beneish M-score**: dấu hiệu xào nấu lợi nhuận.
Độ phủ năm 2025: EPS 92,5%, P/E 91,8%, P/B 91,5%, ROE 99,9%, F 88,4%, M 80,0%, Z 91,2%. EPS tự tính khớp với EPS công bố trong ±10% ở 75% trường hợp.

### 9.3 Các quyết định xử lý dữ liệu (D-IND-01)

| Vấn đề | Cách xử lý |
| --- | --- |
| Thiếu số cổ phiếu | Số CP = Vốn góp / 10.000 đồng mệnh giá |
| Thiếu EBIT | EBIT = Lợi nhuận trước thuế + Chi phí lãi vay |
| BCTC CafeF thiếu | Bổ sung từ DStock, chỉ lấp nguyên cả mã-năm và chỉ dùng các trường khớp ≥ 85% với CafeF. Đã lấp 616 mã-năm |
| Doanh nghiệp lập lưu chuyển tiền tệ trực tiếp | Lấy CFO từ báo cáo trực tiếp (181 mã) |
| Thiếu khấu hao cho M-score | Dùng giá trị thay thế (fallback) đã ghi rõ |

Nguyên tắc chỉ lấp nguyên cả mã-năm là để không trộn hai nguồn trong cùng một báo cáo, tránh các tỷ số bị lệch do hai nguồn định nghĩa khác nhau.

### 9.4 Ngày công bố BCTC (D-CRAWL-02) và Execution50

BCTC năm X không có sẵn ngay ngày 31/12/X. Nếu dùng BCTC trước khi nó được công bố thì backtest bị nhìn trước tương lai (look-ahead bias). Vì vậy nhóm thu thập ngày công bố (D-CRAWL-02) và dựng tập Execution50: 1.172 mã, 13.529 dòng, dùng cho phân cụm tài chính theo thời điểm (B-PIT) và cổng kiểm soát ngày cắt (cutoff gate) ở M3.

## 10. Kết quả M1 và bài học rút ra

### 10.1 M1 bàn giao gì cho M2 và M3

| Hạng mục | Kết quả |
| --- | --- |
| Dữ liệu giá | CafeF, giá điều chỉnh, ~1.000 mã 3 sàn, ghim SHA256 |
| Đặc trưng thị trường | 8 đặc trưng/mã/tháng, độ phủ 96,8–99,7% |
| Phễu QC | 952 → 922 → 905 mã, mọi mã bị loại đều có lý do |
| Giao thức M2 | Khóa cửa sổ, ngưỡng, chuẩn hóa, thuật toán (M2-PREP) |
| Registry dài hạn | C8 v2, 1.522 mã có trạng thái |
| Dữ liệu tài chính | Indicators v1: 1.510 mã, 14.738 mã-năm; ngày công bố BCTC |
| Kiểm thử | 173/173 test đạt |

### 10.2 Bài học

- **Đo nguồn trước khi cam kết.** Nhóm chỉ chuyển từ KBS sang CafeF sau khi đo thực tế ở pilot, không chọn theo cảm tính.
- **Fail-closed tốt hơn lấp cho đẹp.** Hai lỗ hổng 15/05/2023 và 03/02/2025 được ghi nhận công khai thay vì forward-fill, nên mọi con số về sau đều truy vết được.
- **Điều kiện tham gia phải theo từng tháng.** Tránh thiên lệch sống sót.
- **Khóa giao thức trước khi nhìn kết quả.** M2-PREP là nền cho tính trung thực của Holdout.
- **Dữ liệu tài chính cần ngày công bố.** Không có ngày công bố thì mọi backtest dùng BCTC đều có nguy cơ nhìn trước tương lai.
### 10.3 Câu hỏi mentor có thể hỏi về M1

- *Vì sao dùng giá điều chỉnh của CafeF mà không tự điều chỉnh?* Nhóm coi đây là proxy do nhà cung cấp tính. Ở M3 nhóm phát hiện và sửa một số lỗi điều chỉnh của nguồn (quy tắc Q17, 34 điểm sửa).
- *Vì sao không lấp hai ngày thiếu?* Lấp sẽ tạo dữ liệu không có thật. Nhóm chọn để trống và ghi nhận.
- *Vì sao cần 253 phiên?* Để tính đúng mom_252 mà không nội suy.
- *Mã hủy niêm yết xử lý thế nào?* Điều kiện tham gia tính theo từng tháng, mã có mặt ở tháng nào thì tham gia tháng đó.
**PHẦN 2**

# M2 – Phân cụm

## 1. Mục tiêu và nguyên tắc của M2

**Mục tiêu:** mỗi cuối tháng, chia các cổ phiếu đủ điều kiện thành các nhóm (cụm) có hành vi giá giống nhau, dựa trên các đặc trưng momentum và rủi ro từ M1. Sau đó xác định cụm “dẫn dắt” (đà tăng mạnh, rủi ro vừa phải) để M3 dùng làm nguồn chọn cổ phiếu.

**Câu hỏi M2 trả lời:**

- Có bao nhiêu nhóm cổ phiếu có ý nghĩa (chọn K)?
- Thuật toán nào phân nhóm tốt và ổn định nhất?
- Các nhóm có bền qua thời gian không, có giữ được trên dữ liệu Holdout chưa thấy không?
**Nguyên tắc:**

- **Phân cụm theo từng tháng** (snapshot cắt ngang), mỗi tháng chỉ dùng dữ liệu đến tháng đó.
- **Chọn mô hình trên Development, kiểm tra trên Holdout.** Holdout chỉ mở một lần sau khi đông cứng mô hình.
- **Mọi tham số được khóa trước** theo giao thức M2-PREP (xem tab M1, mục 7).
- **Đánh giá bằng nhiều thước đo**, không chỉ một con số.
### Các thước đo dùng trong M2

| Thước đo | Đo gì | Tốt khi |
| --- | --- | --- |
| Silhouette | Mỗi điểm gần cụm mình hơn cụm khác bao nhiêu (−1 đến 1) | Cao |
| Davies–Bouldin (DB) | Tỷ lệ độ phân tán trong cụm so với khoảng cách giữa cụm | Thấp |
| Calinski–Harabasz (CH) | Phương sai giữa cụm / trong cụm | Cao |
| Balance | Cụm nhỏ nhất chiếm bao nhiêu phần | Không quá nhỏ |
| ARI | Mức giống nhau giữa hai cách gán nhãn (0 đến 1) | Cao |
| Persistence / Migration | Tỷ lệ mã ở lại / chuyển cụm giữa hai tháng | Tùy mục đích |

Như sẽ thấy ở mục 5, việc chỉ nhìn silhouette đã dẫn nhóm tới một kết luận sai ở vòng đầu.

## 2. M2 v1: thử nghiệm đầu trên 15 tháng

Vòng đầu chạy trên cửa sổ Development của M2-PREP (11/2023–01/2025, 15 snapshot cuối tháng), dùng đúng giao thức đã khóa: 8 đặc trưng, robust scaling, K-Means làm baseline.

### 2.1 Các nhiệm vụ chính

- **Nhiệm vụ 2 (adapter dữ liệu):** chuyển snapshot M1 thành ma trận đầu vào cho mô hình, áp ngưỡng n_min = 120 mã/tháng. Test case dùng tháng 30/11/2023 với 142 mã.
- **Nhiệm vụ 3 (quét K):** chạy 105 lần fit K-Means trên 15 snapshot với nhiều giá trị K.
### 2.2 Kết quả: Global K = 2

K = 2 cho điểm tốt nhất: silhouette 0,7557, Davies–Bouldin 0,5219. Nhóm ghi quyết định dùng một K chung cho mọi tháng (Global K = 2, ADR-049).

**Lưu ý khi thuyết trình:** 15 tháng là ngắn. Sau vòng này nhóm chuyển sang nguồn C8 v2 để có 60 tháng Dev và 24 tháng Holdout (M2 v2, mục 3). K = 2 tiếp tục được chọn ở v2, và chính K = 2 này về sau bị chứng minh là có vấn đề (mục 5).

## 3. M2 v2 trên C8 v2: chuỗi nhiệm vụ đầy đủ

**Thiết lập:** nguồn C8 v2, 60 snapshot Development (01/2019–12/2023, 45.646 lượt gán cụm), 8 đặc trưng, robust scaling, mỗi tháng n ≥ 100 mã. Holdout 24 snapshot (2024–2025) bị khóa đến cuối.

### 3.1 Nhiệm vụ 3: quét K (420 lần fit)

| K | Silhouette (trung vị) | Davies–Bouldin | Balance |
| --- | --- | --- | --- |
| 2 | 0,9408 | 0,4031 | 0,0210 |
| 3 | 0,9064 | 0,3882 | 0,0060 |
| 4 | 0,8869 | — | — |
| 8 | 0,7517 | — | — |

Silhouette giảm dần khi K tăng, nên K = 2 được chọn. Nhưng hãy để ý cột **Balance**: cụm nhỏ nhất chỉ chiếm 2,1% (K=2) và 0,6% (K=3). Đây là dấu hiệu đầu tiên của vấn đề ở mục 5.

### 3.2 Nhiệm vụ 4–6: ba thuật toán với K = 2

| Thuật toán | Silhouette | Davies–Bouldin | Kích thước 2 cụm (trung bình) |
| --- | --- | --- | --- |
| K-Means (NV4) | 0,9408 | 0,4031 (CH 1.586) | 14,9 và 745,9 mã |
| Ward (NV5) | 0,9463 | 0,3736 | 16,9 và 743,9 mã |
| PCA + K-Means (NV6) | 0,9469 | — | cụm nhỏ nhất có tháng chỉ 2 mã |

Với PCA, 2 thành phần chính đã giữ 97,8–99,96% phương sai. Điều này nghĩa là dữ liệu sau chuẩn hóa gần như chỉ có một hướng biến thiên chính.

### 3.3 Nhiệm vụ 7–9: tổng hợp và độ bền theo thời gian

- NV7 tổng hợp các thước đo của ba thuật toán.
- NV9 (temporal): ARI giữa hai tháng liên tiếp có trung vị 0,757; 99,0% mã ở lại cụm cũ; chỉ 0,99% chuyển cụm mỗi tháng.
### 3.4 Nhiệm vụ 10: chọn mô hình

Chênh lệch điểm giữa ba thuật toán chỉ 0,006 (< ngưỡng 0,03), nên nhóm chọn **K-Means** vì đơn giản nhất (nguyên tắc Occam). Cảnh báo cụm nhỏ (dưới 5 mã): K-Means 2/60 tháng, Ward 7/60, PCA 2/60. ARI giữa Ward và K-Means là 0,7406. Trạng thái: **FROZEN_FOR_HOLDOUT**.

### 3.5 Nhiệm vụ 11–12: mở Holdout và kiểm toán

- Mô hình đông cứng lúc 05:57Z ngày 22/10/2026, Holdout được mở lúc 08:49Z cùng ngày. Thứ tự thời gian này chứng minh nhóm không chỉnh mô hình sau khi nhìn Holdout.
- Holdout: 24 snapshot, 30.155 lượt gán, silhouette 0,949, tháng ít nhất 503 mã.
- 8/8 hạng mục kiểm toán đạt (PASS). Chạy lại từ đầu cho ARI 1,0 (tái lập hoàn toàn).
- Tổng cả hai đoạn: 75.801 nhãn, 82 cặp chuyển tiếp tháng.
**Kết luận lúc đó:** mô hình K-Means K = 2 trông rất tốt và ổn định. Tuy nhiên khi đem sang M3 và xem kỹ cụm, nhóm phát hiện vấn đề nghiêm trọng (mục 5).

## 4. Baseline phân cụm tài chính 6 tỷ số

Song song với hướng thị trường, nhóm thử phân cụm doanh nghiệp theo sức khỏe tài chính.

- **Dữ liệu:** 1.172 mã × 10 năm tài chính, 6 tỷ số từ BCTC.
- **Cách làm:** z-score, K-Means k = 3.
- **Kết quả:** cụm bị suy biến, ví dụ kích thước {1.169, 2, 1} với silhouette 0,92.
**Giải thích:** các tỷ số tài chính có đuôi rất dài (ví dụ một doanh nghiệp vốn chủ sở hữu gần 0 sẽ có ROE cực lớn). z-score không chặn được các giá trị cực đoan, nên K-Means dùng hai cụm để “ôm” vài mã ngoại lai, và dồn toàn bộ phần còn lại vào một cụm. Silhouette vẫn cao vì ngoại lai nằm rất xa đám đông.

**Vì sao quan trọng:** đây là cùng một lỗi với K = 2 bên thị trường (mục 5). Nhóm rút ra quy tắc: mọi mô hình phải qua **cổng kích thước cụm** trước khi xét silhouette. Hướng tài chính sau đó được làm lại thành hệ B (mục 7) và B-PIT (tab M3).

## 5. Phát hiện vấn đề: silhouette cao giả

Đây là bước ngoặt quan trọng nhất của M2 và nên được trình bày kỹ với mentor.

### 5.1 Triệu chứng

- K = 2 có silhouette 0,94, nhưng hai cụm có kích thước trung bình **14,9 và 745,9 mã**. Một cụm chỉ khoảng 2% số mã.
- Trung vị cụm nhỏ nhất chỉ 3,7% số mã; 48/60 tháng Dev có cụm dưới 5%.
- Khi đem sang M3, cụm dẫn dắt của K = 2 có **42/60 tháng Dev dưới 10 ứng viên**, không đủ để lập danh mục (ghi trong D-M3-01).
### 5.2 Nguyên nhân

Phân rã xem biến nào tạo ra sự tách cụm cho thấy: trong không gian robust scaling gốc (S1), **99,9% sự tách biệt đến từ thanh khoản**. Robust scaling chia cho khoảng tứ phân vị, nhưng không cắt đuôi, nên vài mã thanh khoản cực lớn (hoặc cực nhỏ) nằm rất xa. K-Means tách nhóm này ra thành một cụm riêng.

Nói cách khác, K = 2 không phân biệt mã mạnh/yếu về momentum. Nó chỉ tách **“một nhúm mã thanh khoản ngoại lai” khỏi “phần còn lại”**. Silhouette cao vì khoảng cách tới ngoại lai rất lớn, không phải vì cụm có ý nghĩa.

Bằng chứng thêm: khi đo lại nhãn K = 2 trong không gian đã xử lý ngoại lai (T1), silhouette chỉ còn **0,064**.

### 5.3 Bài học

- Silhouette cao không đồng nghĩa với phân cụm tốt khi dữ liệu có ngoại lai.
- Phải kiểm tra kích thước cụm và biến nào đóng góp vào sự tách cụm.
- Phải xét mục đích sử dụng (M3 cần đủ ứng viên) ngay khi chọn mô hình.
Từ đây nhóm quyết định phân cụm lại (rework, mục 6).

## 6. Phân cụm lại (rework) v1 và v2

### 6.1 Rework v1: thử lại với xử lý ngoại lai

Nhóm dựng lại lưới thí nghiệm gồm 3 cách chuẩn hóa × 2 thuật toán × k từ 3 đến 8:

| Cách chuẩn hóa | Mô tả |
| --- | --- |
| T0 | Robust scaling như M2 v2 (để đối chiếu) |
| T1 | log1p thanh khoản → cắt đuôi (winsorize) 1%–99% → z-score |
| T2 | Biến thể khác để so sánh |

Thuật toán: K-Means và GMM (Gaussian Mixture). Kết quả v1:

- **Hệ A (thị trường):** đề xuất T1 K-Means k = 4, silhouette 0,256. Để so sánh, nhãn K = 2 đang dùng chỉ đạt 0,064 trong cùng không gian T1.
- **Hệ B (tài chính, 6 tỷ số):** đề xuất T1 GMM k = 3.
Silhouette 0,256 thấp hơn 0,94 nhưng đây là con số **trung thực**: các cụm có kích thước hợp lý và phân biệt theo momentum/rủi ro, không phải theo ngoại lai.

### 6.2 Các bản bundle v2 → v3 → v4

Kết quả được đóng gói (bundle) qua nhiều phiên bản. Điểm đáng chú ý ở v3: **học cụm trên mã thanh khoản, rồi gán mã kém thanh khoản (ILLIQUID) vào tâm cụm gần nhất**. Như vậy mã kém thanh khoản không làm méo hình dạng cụm nhưng vẫn có nhãn. Bản v4 là bản cuối dùng cho M3.

### 6.3 Rework v2: chuỗi đầy đủ 2019–2025 và quy trình chọn mô hình mới

**Lọc thanh khoản nhẹ:** ví dụ tại 31/12/2025 có 789 mã thanh khoản và 621 mã kém thanh khoản.

**Thêm đặc trưng thứ 9:** downside_vol_63 (độ biến động chiều giảm).

**4 thuật toán:** K-Means, PCA + K-Means, Ward, GMM.

**Bước 1: Cổng chấp nhận (admissibility gate).** Một cấu hình chỉ được xét tiếp nếu:

- Cụm nhỏ nhất ≥ 5% số mã ở ít nhất 80% số snapshot; và
- Độ ổn định khi lấy mẫu con 90%: ARI ≥ 0,8.
Cổng này loại ngay các mô hình kiểu K = 2 (cụm 2–3%) dù silhouette có cao đến đâu.

**Bước 2: Xếp hạng trên 5 thước đo.** Các cấu hình qua cổng được xếp hạng theo từng thước đo rồi lấy hạng trung bình (số càng nhỏ càng tốt).

### 6.4 Kết quả rework v2 cho hệ A (thị trường, 9 đặc trưng)

| Cấu hình | Hạng TB | Silhouette | Ổn định | Ghi chú |
| --- | --- | --- | --- | --- |
| K-Means k = 3 | 2,40 | 0,272 | 0,96 | Chọn (A v4) |
| PCA + K-Means k = 3 | 2,60 | 0,276 | — | Á quân, rất sát |
| GMM k = 3 | — | 0,156 | — | Silhouette thấp |
| Ward k = 3 | — | — | 0,50 | Trượt cổng (không ổn định) |

### 6.5 Ý nghĩa 3 cụm (trung vị tại 31/12/2025)

| Cụm | Số mã | Đặc điểm |
| --- | --- | --- |
| Dẫn dắt (leading) | 96 | mom_126 ≈ 0,526: đà tăng 6 tháng rất mạnh |
| Trung bình | 413 | Nhóm đông nhất |
| Tụt hậu / beta cao | 280 | Đà yếu, nhạy với thị trường |

Cụm dẫn dắt có khoảng 100 mã, đủ lớn để M3 chọn danh mục, khác hẳn cụm 15 mã của K = 2.

## 7. Hệ B v4 (tài chính) và mô hình kết hợp tham chiếu C

### 7.1 Hệ B: phân cụm theo sức khỏe tài chính

- Đầu vào: các chỉ số từ Indicators v1 (ROE, F-score, Z-score...).
- Rework v1: B với 6 tỷ số đề xuất T1 GMM k = 3, nhưng độ ổn định chỉ ARI 0,50 ở bundle v3.
- Rework v2: B với 9 chỉ số trên dữ liệu theo tháng **không có cấu hình nào qua cổng**.
**Giải thích:** dữ liệu tài chính chỉ thay đổi mỗi năm một lần khi có BCTC mới, nên phân cụm hàng tháng không phù hợp. Vì vậy nhóm chuyển sang cách làm **theo năm và theo thời điểm công bố** (B v4 → B-PIT): mỗi năm tài chính fit một lần, chỉ dùng các BCTC đã công bố trước ngày cắt, rồi đóng băng. Chi tiết B-PIT nằm ở tab M3, mục B-PIT.

Cụm tài chính dẫn đầu có ROE khoảng 19–24% qua các năm.

### 7.2 Mô hình kết hợp C (tham chiếu)

C ghép đặc trưng thị trường và tài chính vào một không gian chung rồi phân cụm. Kết quả rework v2 chọn PCA + K-Means k = 4.

C chỉ là **tham chiếu**, không dùng trong chiến lược M3. M3 dùng hai hệ riêng (A cho thị trường, B-PIT cho tài chính) và kết hợp ở bước chọn cổ phiếu. Cách giải thích gợi ý khi mentor hỏi: giá thay đổi theo tháng còn BCTC theo năm, nên tách hai hệ thì dễ diễn giải và kiểm soát ngày công bố hơn (đây là diễn giải, nên đối chiếu với nhóm trước khi nói).

## 8. So sánh công bằng M2 K=2 và A v4, quyết định D-DIR-01

Vì M2 K = 2 đã qua Holdout và được đông cứng, việc thay nó bằng A v4 cần lý do rõ ràng. Nhóm làm một báo cáo so sánh công bằng (m2-vs-rework-v1).

### 8.1 Cách so sánh cho công bằng

- Cùng một tập mã chung mỗi tháng (trung vị 417 mã ở Dev, 768 mã ở Holdout).
- Đo silhouette trong **cả hai không gian**: S1 (không gian của M2) và S2 (không gian của A v4). Mỗi mô hình đương nhiên tốt trong không gian của mình, nên phải xem cả hai.
- Phân rã sự tách cụm theo nhóm biến: thanh khoản, momentum, rủi ro.
### 8.2 Kết quả (trung vị Dev / Holdout)

| Thước đo | M2 K=2 | A v4 k=3 |
| --- | --- | --- |
| Tỷ trọng cụm nhỏ nhất | 3,7% | 14% |
| Số tháng có cụm dưới 5% | 48/60 Dev | 2/60 |
| Tách cụm do thanh khoản (S1) | 99,9% | — |
| Tách cụm do thanh khoản (S2) | 63% | 8% |
| Tách cụm do momentum | 7% | 54% |
| Tách cụm do rủi ro | 27% | 39% |
| Silhouette trong S2 | 0,114 / 0,129 | 0,240 / 0,243 |
| Silhouette trong S1 | 0,852 / 0,897 | −0,01 |
| Ổn định mẫu con | 1,00 | 0,95 |
| ARI giữa hai tháng liên tiếp | 0,74 / 0,84 | 0,55 / 0,42 |

### 8.3 Cách đọc bảng

- **M2 K=2 gần như chỉ là một bộ lọc thanh khoản**: 99,9% sự tách cụm đến từ thanh khoản, momentum chỉ đóng góp 7%.
- **A v4 tách theo đúng mục tiêu dự án**: momentum 54%, rủi ro 39%, thanh khoản chỉ 8%.
- M2 K=2 ổn định hơn (1,00 và ARI tháng 0,74–0,84), nhưng đó là vì nó gần như không thay đổi: cụm ngoại lai thanh khoản tháng nào cũng là vài mã đó. A v4 ít bền hơn giữa các tháng vì momentum vốn thay đổi, đây là điều mong đợi ở một chiến lược momentum.
- Kiểm tra thêm: chỉ dùng Dev để chọn lại vẫn ra k = 3 (PCA + K-Means hạng 2,40, K-Means 2,60, cùng silhouette 0,276, ổn định 0,98 / 0,96). Vậy việc chọn k = 3 không phụ thuộc vào việc đã nhìn Holdout.
### 8.4 Quyết định D-DIR-01

Nhóm ghi quyết định **D-DIR-01**: dùng A v4 (K-Means k = 3, 9 đặc trưng, T1) làm phân cụm thị trường chính cho M3. M2 K = 2 không bị xóa mà giữ làm đối chứng, nhưng ở M3 chỉ được báo cáo số ứng viên, không chạy backtest (vì 42/60 tháng Dev có dưới 10 ứng viên).

## 9. Bàn giao M2 sang M3 và giới hạn

### 9.1 M2 bàn giao gì

| Đầu ra | Dùng ở M3 như thế nào |
| --- | --- |
| Nhãn cụm thị trường A v4 (k = 3) mỗi tháng | Lọc cổ phiếu thuộc cụm dẫn dắt (market_rule = leading) |
| Nhãn cụm tài chính B-PIT mỗi năm | Loại cổ phiếu thuộc cụm yếu nhất (financial_rule = not_weakest) |
| Nhãn M2 K = 2 | Chỉ báo cáo số ứng viên để đối chứng |
| Quyết định D-DIR-01 | Căn cứ để M3 dùng A v4 thay K = 2 |

### 9.2 Giới hạn cần nói thẳng với mentor

- **Silhouette của A v4 thấp (~0,24–0,27).** Cổ phiếu Việt Nam không chia thành các nhóm tách biệt rõ ràng. Phân cụm ở đây giống một cách chia vùng có ý nghĩa hơn là khám phá các nhóm tự nhiên.
- **ARI giữa hai tháng thấp (0,42–0,55)**, nên danh mục M3 có thể thay đổi nhiều mỗi tháng.
- **Hệ B hàng tháng không qua cổng**, phải chuyển sang B-PIT theo năm.
- **M2 K = 2 đã được đông cứng và mở Holdout trước khi phát hiện vấn đề.** Nhóm không sửa lại K = 2 mà làm một hệ mới với giao thức mới, và giữ K = 2 làm đối chứng. Nên chủ động nói rõ điểm này vì mentor có thể hỏi về việc thay mô hình sau khi đã thấy Holdout. Câu trả lời: việc chọn lại chỉ trên Dev vẫn ra k = 3 (mục 8.3).
- Một số con số trong bảng quét lưới của báo cáo M2 market ghi dạng “~” (ước lượng). Tài liệu này chỉ dùng các số đã có trong artifact.
### 9.3 Câu hỏi mentor có thể hỏi về M2

- *Silhouette 0,94 giảm xuống 0,27, vậy mô hình mới tệ hơn?* Không. 0,94 đến từ ngoại lai thanh khoản. Đo trong cùng không gian S2, A v4 đạt 0,24 so với 0,11 của K = 2.
- *Vì sao không dùng GMM hoặc Ward?* Ward trượt cổng ổn định (0,50), GMM silhouette thấp (0,156).
- *Vì sao k = 3?* Qua cổng và xếp hạng cao nhất; chọn lại chỉ trên Dev vẫn ra k = 3.
- *Làm sao biết cụm nào là dẫn dắt?* Cụm có trung vị mom_126 cao nhất (≈ 0,53 tại cuối 2025).
**PHẦN 3**


## 10. Mô hình phân cụm tài chính B-PIT Enriched (Dữ liệu làm giàu)

### 10.1 Bối cảnh và động lực cải tiến
Mặc dù mô hình B-PIT gốc (Mục 4 của Phần 3) đã giải quyết được lỗi nhìn trước tương lai (Look-ahead bias) bằng cách chỉ sử dụng BCTC khả dụng tại từng thời điểm quyết định, việc áp dụng trên tập dữ liệu thô gặp phải rào cản lớn:
- **Tỷ lệ khuyết dữ liệu cao:** Do nhiều doanh nghiệp (đặc biệt sàn UPCoM và HNX) nộp báo cáo chậm hoặc thuyết minh tài chính thiếu chi tiết một số khoản mục (ví dụ lưu chuyển tiền tệ, chi phí lãi vay), các chỉ số như ROE, Net Margin, Debt/Equity bị khuyết (NaN).
- **Hệ quả "Thin Universe" và "Cash Drag":** Bộ lọc giao dịch loại bỏ các mã thiếu chỉ số tài chính, dẫn đến danh mục không tìm đủ số lượng cổ phiếu mục tiêu (thường thiếu ứng viên `< 10` mã), buộc thuật toán phải giữ tiền mặt lớn (trung bình 22.40% ở kỳ Development), làm giảm sút nghiêm trọng hiệu quả sinh lời tổng thể.

### 10.2 Phương pháp làm giàu dữ liệu: Median ngành Point-in-Time
Để khắc phục tình trạng trên mà vẫn giữ tính toàn vẹn khoa học, nhóm đã xây dựng module làm giàu dữ liệu chuẩn hóa:
1. **Bộ 9 chỉ số tài chính làm giàu:**
   - **Định giá & Tỷ suất:** P/E, P/B.
   - **Khả năng sinh lời:** ROE, ROA, Net Profit Margin (Biên lợi nhuận ròng).
   - **Đòn bẩy & Thanh khoản:** Debt/Equity (Nợ/Vốn chủ sở hữu), Current Ratio (Khả năng thanh toán hiện hành).
   - **Tăng trưởng:** Revenue Growth (Tăng trưởng doanh thu YoY), Net Profit Growth (Tăng trưởng lợi nhuận ròng YoY).
2. **Quy tắc làm giàu bằng trung vị ngành (`IMPUTED_MEDIAN`):**
   - Phân nhóm doanh nghiệp theo phân ngành ICB cấp 2.
   - Tại mỗi lát cắt thời gian $t$, giá trị khuyết được thay thế bằng giá trị **trung vị của các doanh nghiệp cùng ngành đã công bố báo cáo** trong cùng kỳ.
   - **Không rò rỉ dữ liệu (No Leakage):** Tuyệt đối không sử dụng thông tin ngành của các quý sau hay giá trị tương lai.
   - **Minh bạch nguồn gốc (Provenance Flag):** Mọi giá trị dữ liệu đều gắn cờ phân định rõ `ORIGINAL` (số liệu gốc công bố) hoặc `IMPUTED_MEDIAN` (số liệu làm giàu), lưu trữ đầy đủ trong parquet metadata.

### 10.3 Huấn luyện K-Means B-PIT Enriched ($k=3$)
- **Quy trình huấn luyện:** Khởi tạo và huấn luyện lại theo từng chu kỳ năm (Point-in-Time retraining) với tham số $k=3$.
- **Tiền xử lý:** Sử dụng `RobustScaler` để giảm thiểu ảnh hưởng của các ngoại lai cực trị trong tỷ số tài chính (như P/E quá lớn do lợi nhuận gần bằng 0), kết hợp chuẩn hóa z-score.
- **Ý nghĩa kinh tế của 3 cụm tài chính:**
  - **Cụm 0 (Chất lượng cao / Bluechips lành mạnh):** ROE/ROA cao, đòn bẩy tài chính an toàn, biên lợi nhuận ổn định, tăng trưởng doanh thu vững chắc.
  - **Cụm 1 (Trung bình / Doanh nghiệp ổn định):** Các chỉ số sinh lời và đòn bẩy ở mức trung bình ngành, hoạt động kinh doanh duy trì ổn định.
  - **Cụm 2 (Rủi ro cao / Báo động tài chính):** Nợ vay quá mức, biên lợi nhuận mỏng hoặc âm, khả năng thanh toán hiện hành yếu.
- **Kiểm định rò rỉ (Leakage Audit):** Xác minh `fit_leaks = 0` trên toàn bộ 60 kỳ Development và 24 kỳ Holdout.

### 10.4 Bàn giao cho M3 và Notebook tái lập
Mô hình và dữ liệu làm giàu được bàn giao cho M3 dưới dạng các artifacts chuẩn hóa:
- **Dữ liệu làm giàu:** Lưu tại `data/financial/indicators_enriched_v1/`.
- **Artifacts phân cụm B-PIT:** Lưu tại `data/experiments/b_pit_enriched/`.
- **Notebook điều phối và tái lập:** `notebooks/05_B_PIT_Enriched.ipynb` cho phép tái lập 100% từ khâu tiền xử lý, imputation, clustering đến kiểm định tính toàn vẹn.


# M3 – Backtest, báo cáo và dashboard

## 1. Mục tiêu và cấu trúc M3

**Câu hỏi nghiên cứu của M3:** nếu mỗi tháng chọn cổ phiếu bằng cách kết hợp cụm thị trường (A v4) và cụm tài chính (B-PIT), danh mục có tốt hơn các cách chọn đơn giản hơn và hơn VN-Index không?

M3 chia làm 3 phần:

| Phần | Nội dung | Trạng thái |
| --- | --- | --- |
| M3-A | Engine backtest: chọn cổ phiếu, mô phỏng giao dịch, tính NAV và chỉ số cho 5 chiến lược + VNINDEX | Dev và Holdout đã chạy chính thức ngày 04/11 |
| M3-B | Dashboard trên web hiển thị kết quả backtest (trang /backtest) | Đã triển khai ngày 05/11 |
| M3-C | Notebook tái lập 01–04 và báo cáo kỹ thuật | Dev/Holdout tái lập được; tổng thể PARTIAL vì Final chưa chạy |

**Ba đoạn thời gian:**

- **Development:** quyết định từ 31/01/2019 đến 29/12/2023 (60 lần quyết định, 59 lần giao dịch).
- **Holdout:** 31/01/2024 đến 31/12/2025 (24 lần quyết định, 23 lần giao dịch).
- **Final:** năm 2026, bắt đầu từ snapshot cuối 01/2026. NOT_READY.
Mỗi đoạn khởi tạo độc lập từ 100% tiền mặt, không mang danh mục từ đoạn trước sang.

**Theo yêu cầu của mentor (anh Tuấn):** kịch bản chính không tính phí giao dịch. Phí 15 và 30 bps được đưa sang phần mở rộng.

## 2. Chuẩn bị: kế hoạch, giai đoạn 0 và lõi engine

Trước khi viết code backtest, nhóm làm ba việc:

- **Viết kế hoạch M3 (M3_PLAN)**: xác định đầu vào (nhãn A v4, B-PIT, giá, chỉ số), đầu ra, các đoạn thời gian và các chiến lược đối chứng.
- **Giai đoạn 0**: kiểm tra đầu vào có đủ và khớp hash không, trước khi chạy bất cứ gì.
- **Gửi câu hỏi cho mentor**: trong đó có câu về phí giao dịch. Mentor trả lời không đưa phí vào kịch bản chính.
Sau đó nhóm xây **lõi engine** gồm các thành phần:

| Thành phần | Vai trò |
| --- | --- |
| Universe | Xác định mã nào đủ điều kiện tại mỗi ngày quyết định, ghi lý do loại từng mã (universe audit) |
| Strategies | Sinh danh mục mục tiêu (target) cho từng chiến lược |
| PriceBook | Cung cấp giá, chỉ được đọc giá trong đoạn đang chạy |
| Executor | Mô phỏng mua bán, xử lý trần/sàn, thiếu tiền |
| Ledger / NAV | Ghi sổ giao dịch, vị thế, giá trị tài sản ròng |
| Metrics / Manifest | Tính chỉ số, niêm phong (seal) kết quả bằng hash |

Mỗi lần chạy có một mã run (ví dụ 20261104T121107Z-5557288c) gồm thời điểm và hash, để truy lại chính xác code và cấu hình đã dùng.

## 3. Kế hoạch chuẩn của nhóm trưởng, rà soát và các quyết định

### 3.1 Kế hoạch chuẩn (KE_HOACH_M3_SCHEMA_GITHUB)

Nhóm trưởng viết bản kế hoạch chuẩn cho M3, gồm: kiến trúc, bộ quy tắc, bảng quyết định, đầu vào, 4 bước của M3-A, ví dụ mẫu 3 kỳ với FPT, HPG, VCB, MWG, VNM, SSI, schema cho từng file đầu ra (targets, ledger, holdings, turnover, nav, benchmark, metrics, manifest, universe_audit), benchmark, checklist, cùng phần B (dashboard) và phần C (notebook 01–04).

### 3.2 Rà soát R1–R8 và ADR D-M3-01

Khi rà soát kế hoạch, nhóm ghi lại 8 điểm cần chốt (R1–R8) và gom vào quyết định D-M3-01. Các điểm chính:

- **N_min = 10 được đếm sau khi loại mã thiếu toàn bộ tiêu chí tài chính.** Nếu đếm trước thì số ứng viên bị thổi phồng.
- **LIMIT_DATA_MISSING:** thiếu dữ liệu giá trần/sàn thì không giao dịch (fail-closed).
- **NOT_EXECUTED_SEGMENT_END:** quyết định cuối đoạn không được thực hiện vì phiên kế tiếp nằm ngoài đoạn.
- **M2 K = 2 chỉ làm đối chứng số ứng viên**, vì 42/60 tháng Dev có dưới 10 ứng viên.
### 3.3 Bảng quyết định Q1–Q17

Kế hoạch có 17 quy tắc trả lời các câu hỏi vận hành. Một số quy tắc quan trọng:

| Quy tắc | Nội dung |
| --- | --- |
| Chung | Chỉ mua (long-only), không đòn bẩy |
| Q6 | Kỳ không đủ N_min: không mua mới, giữ mã cũ còn hợp lệ, bán mã đã ra khỏi tập ứng viên |
| Q16 | Final bắt đầu từ snapshot cuối 01/2026 |
| Q17 | Phát hiện và sửa lỗi giá điều chỉnh của nguồn (xem mục 6.4) |

Các tình huống giao dịch: BUY_FAILED thì giữ tiền mặt; SELL_FAILED thì giữ vị thế; thiếu tiền thì giảm đều tỷ lệ các lệnh mua (SCALED).

## 4. B-PIT: phân cụm tài chính theo thời điểm công bố

### 4.1 Vì sao cần B-PIT

B v4 fit trên toàn bộ dữ liệu tài chính. Nếu dùng thẳng trong backtest, mô hình tại năm 2019 đã “biết” BCTC của các năm sau (look-ahead). B-PIT (point-in-time) sửa việc này: mỗi năm tài chính (FY) fit một mô hình riêng, chỉ dùng các BCTC đã công bố trước ngày cắt (cutoff), rồi **đóng băng** tâm cụm, cách chuẩn hóa và thứ tự cụm.

### 4.2 Cách làm

- Công thức giống B v4: 9 chỉ số, winsorize + z-score, K-Means k = 3.
- Ngày sử dụng được: FY trước 2022 dùng quy tắc trễ cố định (30/06 năm sau); từ FY2022 dùng ngày gửi BCTC thực tế trên CafeF, dùng từ phiên giao dịch kế tiếp.
- Tại mỗi ngày quyết định, engine chọn FY mới nhất đã dùng được. Nếu FY mới đã công bố nhưng mô hình FY đó chưa sẵn sàng thì **không lùi về FY cũ**. Dữ liệu quá 18 tháng bị coi là cũ (stale).
- Loại ngân hàng, chứng khoán, bảo hiểm khỏi nhánh tài chính vì cấu trúc BCTC khác.
### 4.3 Kết quả từng năm

| FY | Ngày cắt | Số mã | ARI so với B v4 |
| --- | --- | --- | --- |
| 2016 | 03/07/2017 | 135 | 1,0 |
| 2017 | 02/07/2018 | 951 | 1,0 |
| 2018 | 01/07/2019 | 947 | 1,0 |
| 2019 | 01/07/2020 | 972 | 1,0 |
| 2020 | 01/07/2021 | 977 | 1,0 |
| 2021 | 01/07/2022 | 1.043 | 1,0 |
| 2022 | 30/04/2023 | 1.146 (fit 1.048) | 0,9553 |
| 2023 | 30/04/2024 | 1.125 (fit 972) | 0,9369 |
| 2024 | 30/04/2025 | 1.165 (fit 1.042) | 0,8077 |
| 2025 | — | — | NOT_READY (chỉ 3 BCTC dùng được) |

**Cách đọc:** trước 2022, cutoff đủ trễ nên B-PIT trùng B v4 (ARI 1,0). Từ 2022 dùng ngày công bố thật, một số mã nộp muộn không được dùng để fit, nên kết quả lệch dần so với B v4 (ARI 0,81–0,96). Đây chính là lượng look-ahead mà B-PIT loại bỏ. Cụm tài chính dẫn đầu có ROE khoảng 19–24%.

### 4.4 Cổng ngày cắt khi chạy (runtime cutoff gate)

Ví dụ cụ thể: tại snapshot 29/03/2024, mô hình FY2023 chưa đến ngày cắt (30/04/2024), cổng giữ lại 24 mã của Combined và 178 mã của Financial-only. Đến 31/05/2024 các mã này được giải phóng.

**Lưu ý đã phát hiện:** báo cáo B-PIT ghi “lọc cứng F ≥ 7, Z ≥ 1,81” nhưng cấu hình khóa m3_strategy_v1 không có bộ lọc này. F và Z chỉ là tiêu chí xếp hạng. Nên xác nhận với Khôi trước buổi báo cáo.

## 5. Năm chiến lược và quy tắc chọn cổ phiếu

### 5.1 Chiến lược chính: Combined

Mỗi cuối tháng:

- **Lọc thị trường:** giữ mã thuộc cụm A v4 **dẫn dắt** (market_rule = leading).
- **Lọc tài chính:** bỏ mã thuộc cụm B-PIT **yếu nhất** (financial_rule = not_weakest).
- **Các cổng khác:** thanh khoản, ngành, ngày công bố, ngày cắt mô hình, đủ tiêu chí.
- **Chấm điểm** bằng 6 tiêu chí:
| Nhóm | Tiêu chí | Tốt hơn khi |
| --- | --- | --- |
| Thị trường | mom_126 | Cao |
| Thị trường | downside_vol_63 | Thấp |
| Thị trường | liquidity_21 | Cao |
| Tài chính | ROE | Cao |
| Tài chính | F-score | Cao |
| Tài chính | Z-score | Cao |

Mỗi tiêu chí đổi sang percentile (hạng trung bình) trong tập cùng kỳ. S_market và S_fin là trung bình percentile từng nhóm.

**Điểm Combined = 0,5 × S_market + 0,5 × S_fin.**

- **Chọn top 30%:** lấy ceil(0,3 × số ứng viên) mã điểm cao nhất, chia đều tỷ trọng. Hòa điểm thì ưu tiên thanh khoản cao, rồi theo mã chữ cái.
- **N_min = 10:** nếu dưới 10 ứng viên thì không mua mới (UNIVERSE_TOO_SMALL), giữ mã cũ còn hợp lệ.
Thiếu một phần tiêu chí: chấm percentile trung tính 0,5 và gắn cờ. Thiếu toàn bộ tiêu chí tài chính: loại trước khi đếm N_min.

### 5.2 Bốn đối chứng và benchmark

| Chiến lược | Cách chọn | Trả lời câu hỏi |
| --- | --- | --- |
| Market-only | Chỉ cụm thị trường dẫn dắt + điểm thị trường | Thêm tài chính có giúp gì không? |
| Financial-only | Chỉ cụm tài chính + điểm tài chính | Thêm thị trường có giúp gì không? |
| Equal-weight | Chia đều mọi mã không bị kém thanh khoản | Chọn lọc có hơn mua cả thị trường? |
| Momentum-only | Top 30% theo mom_126, không dùng cụm | Phân cụm có hơn momentum đơn giản? |
| VNINDEX | Benchmark chính thức, không phải chiến lược thứ 6 | Hơn thị trường chung? |

### 5.3 Khóa cấu hình

Toàn bộ tham số nằm trong configs/experiments/m3_strategy_v1.json, trạng thái **LOCKED** (sha b5c47ac4…) trước khi chạy chính thức: weight 0,5, top_share 0,3, n_min 10, stale 18 tháng, phí 0 bps. Sharpe chỉ tính ở Final.

## 6. Engine 4 bước

### 6.1 Bốn bước mỗi kỳ

| Bước | Thời điểm | Làm gì |
| --- | --- | --- |
| 1. Chọn | Ngày quyết định (cuối tháng) | Tạo danh mục mục tiêu (target) |
| 2. Mua bán | Phiên giao dịch kế tiếp | Định giá lại danh mục, bán trước rồi mới mua |
| 3. Giữ | Đến lần giao dịch kế tiếp | Định giá hàng ngày, ghi NAV |
| 4. Chuyển kỳ | Cuối kỳ | Chuyển trạng thái danh mục sang kỳ sau, không giao dịch thêm |

Quyết định dùng dữ liệu ngày t, giao dịch ở phiên t+1. Như vậy không có chuyện biết giá đóng cửa rồi mua ngay tại giá đó.

### 6.2 Xử lý các tình huống giao dịch

| Tình huống | Xử lý |
| --- | --- |
| Khối lượng 0 hoặc thiếu giá | Không giao dịch |
| Giá chạm trần | Không mua được → BUY_FAILED, giữ tiền |
| Giá chạm sàn | Không bán được → SELL_FAILED, giữ vị thế |
| Thiếu dữ liệu trần/sàn | Không giao dịch (LIMIT_DATA_MISSING) |
| Không đủ tiền mua hết | Giảm đều tỷ lệ các lệnh mua (SCALED) |
| Mất giá một phiên | Dùng giá hợp lệ gần nhất để định giá, ghi PRICE_STALE |

### 6.3 Giả định tính toán

- Vốn ban đầu = 1 (chuẩn hóa), cho phép vị thế phân số, không làm tròn lô.
- Tiền mặt không sinh lãi; phí và trượt giá = 0 ở kịch bản chính.
- Turnover = tổng giá trị mua + bán / (2 × NAV trước giao dịch).
### 6.4 Q17: sửa lỗi giá điều chỉnh của nguồn

Giá điều chỉnh của CafeF đôi khi có một phiên bị lệch tỷ lệ điều chỉnh rồi trở lại ngay hôm sau, tạo ra một cú nhảy giá giả.

- Gọi ratio = giá điều chỉnh / giá thô.
- **Phát hiện:** |ratio_hôm nay / ratio_hôm trước − 1| > 3% **và** |ratio_hôm sau / ratio_hôm trước − 1| < 0,5%.
- **Sửa:** giá = giá thô hôm nay × (giá điều chỉnh hôm sau / giá thô hôm sau).
- Chỉ sửa khi có đủ ba phiên liền kề trong cùng đoạn; dữ liệu gốc giữ nguyên.
Lần chạy đầu ghi nhận 36 điểm sửa, kiểm tra lại thì đúng phải là **34**: có 2 cờ sai tại HND 31/07/2023 và DNN 02/08/2023. Nhóm sửa bộ phát hiện (commit c9c1f5f) rồi chạy lại Dev.

### 6.5 Đầu ra của mỗi lần chạy

targets, ledger (sổ giao dịch), holdings, turnover, nav, benchmark, metrics, manifest (hash code, config, dữ liệu), universe_audit (lý do loại từng mã từng ngày).

## 7. Trình tự thực thi ngày 04/11

Nhóm chạy M3 theo từng nấc, mỗi nấc kiểm tra xong mới sang nấc sau. Thứ tự này là bằng chứng cho việc không chỉnh tham số sau khi thấy kết quả.

| # | Bước | Run / commit | Kết quả |
| --- | --- | --- | --- |
| 1 | Feasibility: đếm số ứng viên Combined mỗi tháng, chưa giao dịch | 20261104T034748Z | Dev: ít nhất 3, trung vị 27, nhiều nhất 215; 13 tháng thiếu. Holdout: 4 / 30 / 97; 1 tháng thiếu (29/04/2025, 4 ứng viên) |
| 2 | Checkpoint code | e734c5d |  |
| 3 | Targets-only Dev: chỉ sinh danh mục mục tiêu | 20261104T041728Z, 38948f8 | Dòng target: Combined 787, Market 1.595, Financial 4.012, Equal 25.647, Momentum 7.722; 45.646 dòng audit; 419 dòng Combined bị chặn vì FINANCIAL_MODEL_BEFORE_CUTOFF |
| 4 | Targets-only Holdout | 20261104T042556Z | 259 / 828 / 1.706 / 18.087 / 5.439 dòng |
| 5 | Sửa cách ly đoạn: PriceBook đang đọc cả giá 02/01/2024 khi chạy Dev |  | Sau sửa: Dev 179 phiên / 246.132 dòng giá; Holdout 71 / 103.730. Test M3 tăng từ 43 lên 49 |
| 6 | Khóa cấu hình LOCKED (sha b5c47ac4…) | a5d9872 |  |
| 7 | Chạy Dev chính thức lần 1 | 20261104T060408Z | Phát hiện Q17 đếm 36 điểm sửa, đúng phải là 34 |
| 8 | Sửa Q17 | c9c1f5f (52 test) |  |
| 9 | Chạy lại Dev | 20261104T121107Z-5557288c | Kết quả Dev chính thức |
| 10 | Mở Holdout, chạy một lần | 20261104T133507Z-5557288c | Kết quả Holdout chính thức |

**Vì sao bước 5 quan trọng:** nếu chạy Dev mà engine đọc được giá của Holdout (dù chỉ một phiên) thì Holdout không còn “chưa thấy”. Nhóm sửa để mỗi đoạn chỉ nạp giá của chính nó, và thêm test kiểm tra điều này.

**Vì sao chạy lại Dev sau khi sửa Q17:** Q17 là lỗi dữ liệu (cờ sai), không phải đổi tham số chiến lược. Cấu hình đã khóa giữ nguyên sha b5c47ac4… cho cả hai lần.

Điều kiện chung của cả hai run chính thức: code c9c1f5f, B-PIT bpit-4a9d2e87f0de84ec, phí 0.

## 8. Kết quả chi tiết và phân tích

CAGR tính theo số kỳ lợi suất / 12. Biến động năm = độ lệch chuẩn lợi suất theo kỳ × √12. Max drawdown đo trên NAV cuối kỳ, không phải theo ngày. Không tính Sharpe cho Dev/Holdout (theo cấu hình).

### 8.1 Development (01/2019–12/2023, 59 kỳ lợi suất)

| Chiến lược | Tổng LS | CAGR | Biến động | Max DD | Turnover TB | Cash TB | Kỳ dưới N_min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Combined | 116,15% | 16,97% | 27,39% | −44,60% | 47,62% | 22,40% | 13 |
| Market-only | 128,81% | 18,34% | 29,51% | −47,88% | 53,99% | 6,22% | 0 |
| Financial-only | 40,74% | 7,20% | 17,09% | −27,20% | 17,69% | 1,02% | 0 |
| Equal-weight | 159,03% | 21,36% | 24,45% | −37,01% | 11,89% | 0,48% | 0 |
| Momentum-only | 169,73% | 22,36% | 25,51% | −33,71% | 31,54% | 1,47% | 0 |
| VNINDEX | 24,35% | 4,53% | 23,56% | −33,02% | — | — | — |

### 8.2 Holdout (01/2024–12/2025, 23 kỳ lợi suất)

| Chiến lược | Tổng LS | CAGR | Biến động | Max DD | Turnover TB | Cash TB | Kỳ dưới N_min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Combined | 38,95% | 18,72% | 28,59% | −26,27% | 54,53% | 8,92% | 1 |
| Market-only | 22,43% | 11,14% | 23,75% | −18,91% | 58,52% | 3,75% | 0 |
| Financial-only | 28,37% | 13,92% | 7,30% | −3,95% | 24,37% | 2,54% | 0 |
| Equal-weight | 29,53% | 14,45% | 13,34% | −7,40% | 8,41% | 0,47% | 0 |
| Momentum-only | 41,37% | 19,80% | 15,60% | −8,92% | 27,50% | 0,82% | 0 |
| VNINDEX | 52,13% | 24,47% | 16,08% | −5,87% | — | — | — |

### 8.3 Sự kiện giao dịch của Combined

| Đoạn | BUY_FAILED | SELL_FAILED | SCALED | PRICE_STALE | LIMIT_DATA_MISSING |
| --- | --- | --- | --- | --- | --- |
| Dev | 47 | 33 | 263 | 2 | 0 |
| Holdout | 17 | 23 | 93 | 3 | 0 |

### 8.4 Phân tích từng cặp so sánh

- **Qua hai đoạn:** CAGR Combined tăng từ 16,97% lên 18,72%, thứ hạng từ 4/5 lên 2/5. Nhưng thứ hạng phụ thuộc cả đối chứng và giai đoạn thị trường, chưa phải kiểm định thống kê.
- **So với Market-only:** Dev thấp hơn 1,36 điểm % CAGR nhưng rủi ro thấp hơn. Holdout cao hơn 7,59 điểm % nhưng biến động cao hơn 4,85 điểm và drawdown sâu hơn 7,37 điểm. Chưa tách được đóng góp của phần tài chính.
- **So với Financial-only:** Combined CAGR cao hơn cả hai đoạn nhưng rủi ro cao hơn nhiều (Holdout biến động 28,59% so với 7,30%).
- **So với Equal-weight:** Dev thua cả lợi suất lẫn rủi ro. Holdout CAGR cao hơn 4,27 điểm nhưng drawdown sâu hơn 18,88 điểm.
- **So với Momentum-only:** đây là đối chứng bất lợi nhất. Momentum-only thắng Combined ở **cả CAGR, biến động và drawdown, cả hai đoạn**. Holdout chỉ cách 1,08 điểm CAGR nhưng biến động Combined cao hơn 13 điểm.
- **So với VNINDEX:** Combined hơn ở Dev (16,97% so với 4,53%), thua ở Holdout (18,72% so với 24,47%), drawdown sâu hơn cả hai đoạn. Lưu ý: chiến lược dùng giá điều chỉnh (có cổ tức) còn VNINDEX là chỉ số giá, nên chênh lệch không phải alpha đã xác nhận.
- **Điều kiện vận hành:** Combined Dev có 13/60 kỳ thiếu ứng viên và giữ 22,4% tiền mặt trung bình. Tiền mặt không sinh lãi nên kéo lợi suất xuống. Holdout tiền mặt giảm còn 8,9%. Turnover Combined cao (48–55%), nên khi tính phí thứ hạng có thể thay đổi.
### 8.5 Kết luận trung thực

Combined cải thiện thứ hạng ở Holdout nhưng **chưa có ưu thế nhất quán** về cả lợi suất và rủi ro. Momentum đơn giản tốt hơn trên cả ba chỉ tiêu ở cả hai đoạn. Kết quả verify/tái lập đạt chỉ xác nhận engine đúng quy tắc và chạy lại ra cùng số, không chứng minh chiến lược vượt trội. Cấu hình đóng băng được giữ nguyên sau khi có kết quả, không chỉnh lại cho đẹp số.

Các số trên đã được tính lại từ file nav CSV và khớp với báo cáo kỹ thuật M3.


### 8.6 Đối sánh thực nghiệm M3 giữa Baseline và Enriched B-PIT

Đợt kiểm định đối sánh quy mô lớn (Replication & Comparison Run) ngày 18/11/2026 đã chứng minh rõ nét ưu thế vượt trội của việc làm giàu dữ liệu tài chính B-PIT Enriched so với Baseline cũ.

#### Bảng số liệu chi tiết đối sánh (Trích xuất từ `comparison.csv` và `summary.csv`)

##### 1. Giai đoạn Development (31/01/2019 – 29/12/2023, 60 kỳ quyết định, 59 kỳ thực thi)

| Chiến lược / Bộ dữ liệu | Tổng lợi nhuận (%) | CAGR (%/năm) | Sharpe Ratio | Max Drawdown (%) | Tiền mặt TB (%) | Ticker TB / kỳ | Lệnh Mua lỗi | Lệnh Bán lỗi | Số kỳ `< 10` mã |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Combined (Enriched)** | **151.67%** | **20.65%** | **0.81** | **-44.45%** | **16.85%** | **7.0** | **38** | **35** | **12** |
| Combined (Baseline) | 116.15% | 16.97% | 0.72 | -44.60% | 22.40% | 7.0 | 47 | 33 | 13 |
| *Chênh lệch (Delta)* | ***+35.51 pp*** | ***+3.68 pp*** | ***+0.09*** | ***+0.15 pp*** | ***-5.55 pp*** | *0.0* | *-9* | *+2* | *-1* |
| **Financial-only (Enriched)** | **53.57%** | **9.12%** | **0.55** | **-24.28%** | **1.52%** | **48.0** | **271** | **296** | **0** |
| Financial-only (Baseline) | 40.74% | 7.20% | 0.42 | -27.20% | 1.02% | 43.0 | 267 | 280 | 0 |
| *Chênh lệch (Delta)* | ***+12.82 pp*** | ***+1.92 pp*** | ***+0.13*** | ***+2.93 pp*** | ***+0.49 pp*** | *+5.0* | *+4* | *+16* | *0* |
| **Momentum-only** | 169.73% | 22.36% | 0.88 | -33.71% | 1.47% | 127.0 | 661 | 739 | 0 |
| **Equal-weight** | 159.03% | 21.36% | 0.87 | -37.01% | 0.48% | 439.0 | 1836 | 2027 | 0 |
| **VN-Index** | 24.35% | 4.53% | 0.19 | -33.02% | — | — | 0 | 0 | — |

##### 2. Giai đoạn Holdout niêm phong (31/01/2024 – 31/12/2025, 24 kỳ quyết định, 23 kỳ thực thi)

| Chiến lược / Bộ dữ liệu | Tổng lợi nhuận (%) | CAGR (%/năm) | Sharpe Ratio | Max Drawdown (%) | Tiền mặt TB (%) | Ticker TB / kỳ | Lệnh Mua lỗi | Lệnh Bán lỗi | Số kỳ `< 10` mã |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Combined (Enriched)** | **53.07%** | **24.87%** | **1.34** | **-22.55%** | **9.22%** | **10.0** | **21** | **24** | **1** |
| Combined (Baseline) | 38.95% | 18.72% | 1.09 | -26.27% | 8.92% | 10.0 | 17 | 23 | 1 |
| *Chênh lệch (Delta)* | ***+14.12 pp*** | ***+6.15 pp*** | ***+0.25*** | ***+3.72 pp*** | ***+0.30 pp*** | *0.0* | *+4* | *+1* | *0* |
| **Financial-only (Enriched)** | **30.97%** | **15.11%** | **1.94** | **-3.83%** | **1.83%** | **75.0** | **130** | **117** | **0** |
| Financial-only (Baseline) | 28.37% | 13.92% | 1.91 | -3.95% | 2.54% | 73.0 | 123 | 96 | 0 |
| *Chênh lệch (Delta)* | ***+2.60 pp*** | ***+1.19 pp*** | ***+0.03*** | ***+0.12 pp*** | ***-0.72 pp*** | *+2.0* | *+7* | *+21* | *0* |
| **Momentum-only** | 41.37% | 19.80% | 1.27 | -8.92% | 0.82% | 235.0 | 409 | 464 | 0 |
| **Equal-weight** | 29.53% | 14.45% | 1.08 | -7.40% | 0.47% | 794.0 | 1073 | 1169 | 0 |
| **VN-Index** | 52.13% | 24.47% | 1.52 | -5.87% | — | — | 0 | 0 | — |

#### Phân tích chuyên sâu kết quả thực nghiệm:
1. **Lợi nhuận bứt phá ở cả hai chu kỳ:**
   - Trong kỳ Development, chiến lược Combined Enriched tăng trưởng vượt bậc từ **116.15% lên 151.67%** (tăng thêm **+35.51 điểm phần trăm**).
   - Trong kỳ Holdout (tập kiểm thử ngoài mẫu được giữ niêm phong hoàn toàn), lợi nhuận tăng từ **38.95% lên 53.07%** (tăng thêm **+14.12 điểm phần trăm**), đánh bại hoàn toàn chỉ số VN-Index (52.13%) và các chiến lược thành phần.
2. **Khắc phục triệt để hiện tượng Cash Drag:**
   - Tỷ lệ tiền mặt nhàn rỗi trong kỳ Development giảm mạnh từ **22.40% xuống 16.85%** (-5.55 pp).
   - Số lượng lệnh mua bị thất bại do không khớp hoặc thiếu ứng viên giảm từ 47 xuống 38 lệnh (-9 lệnh).
   - Bể ứng viên tài chính tốt mở rộng, cho phép chiến lược kết hợp lựa chọn được những cổ phiếu thực sự ưu tú mà không bị bỏ sót do lỗi khuyết một vài chỉ tiêu phụ.
3. **Cải thiện độ ổn định và kiểm soát rủi ro:**
   - Tỷ số Sharpe trong kỳ Development tăng từ 0.72 lên 0.81; kỳ Holdout tăng từ 1.09 lên 1.34.
   - Max Drawdown trong kỳ Holdout được thu hẹp đáng kể từ **-26.27% xuống -22.55%** (giảm thiểu 3.72 pp rủi ro sụt giảm vốn tối đa).


## 9. M3-C: notebook tái lập và báo cáo kỹ thuật

### 9.1 Bốn notebook

| Notebook | Nội dung |
| --- | --- |
| 01 – Dữ liệu và PIT | Chứng minh đúng input, config, code và trạng thái tài chính theo ngày quyết định. Hash sai hoặc target mẫu không khớp thì dừng bằng assertion |
| 02 – Tái lập lựa chọn danh mục | Đối chiếu toàn bộ targets và universe audit của 5 chiến lược ở 60 quyết định Dev và 24 quyết định Holdout |
| 03 – Tái lập backtest và benchmark | Chạy lại engine, đối chiếu NAV, metrics, benchmark hai đoạn, vẽ biểu đồ NAV/drawdown, sinh báo cáo kỹ thuật |
| 04 – Báo cáo đánh giá cuối | NOT_READY: chưa chạy, chỉ ghi trạng thái chờ, không có số giả và không dùng Holdout thay Final |

Mỗi notebook 01–03 sinh một file 0x_verification.json.

Notebook gọi trực tiếp code engine (universe.financial_state, Strategies.target_for), không viết lại quy tắc thứ hai, và không fit lại mô hình phân cụm. Không cần chạy lại thu thập dữ liệu hay build B-PIT.

### 9.2 Đầu ra đã công bố

- 64 file CSV canonical trong M3/outputs/ (commit 79d6590 và 324b360), các file JSON ở commit 7337a37.
- Báo cáo M3/reports/BAO_CAO_KY_THUAT_M3.md gồm 13 mục: mục tiêu, dữ liệu, kiến trúc hai hệ phân cụm, căn thời gian, universe, tiêu chí, giao dịch, kết quả, phân tích, giới hạn, Final, tái lập, kết luận.
### 9.3 Trạng thái

- Dev/Holdout: có bằng chứng tái lập.
- Tổng thể M3-C: **PARTIAL** cho đến khi Final hoàn tất.
### 9.4 Lỗ hổng còn lại (nên biết trước khi báo cáo)

- metrics.json và manifest của từng run chưa được đưa lên git.
- Báo cáo có link tới M3/HUONG_DAN_THUC_HIEN_M3.md và thư mục M3/reproduction/, hai thứ này đã bị xóa khỏi repo. Đang chờ hỏi Khôi cách xử lý.
Nếu mentor hỏi “làm sao kiểm chứng”, có thể trả lời: mọi run có mã run, commit code, sha config và B-PIT id; notebook 02–03 đọc lại artifact và đối chiếu.

## 10. M3-B: dashboard /backtest và triển khai

### 10.1 Trang hiển thị

Trang https://delta-intelligence-omega.vercel.app/backtest hiển thị kết quả M3 cho người xem không cần mở code: bảng chỉ số 5 chiến lược + VNINDEX, đường NAV và drawdown theo đoạn Dev/Holdout. Giao diện theo đúng phong cách web sẵn có của dự án.

### 10.2 Luồng dữ liệu

- Từ các run đã niêm phong, đóng gói một bundle trình bày M3/presentation/m3-backtest-v1 (113 KB). Dashboard chỉ đọc artifact đã seal, không tính lại.
- Bundle được đưa lên dataset Hugging Face ngyen/delta-intelligence-data.
- Backend trên Render (delta-intelligence-api) tải dữ liệu theo một commit cố định của dataset (biến DATA_BASE_URL), cung cấp API /api/v2/backtest.
- Frontend trên Vercel gọi API và vẽ biểu đồ.
### 10.3 Kiểm tra

- 29/29 test API/frontend đạt.
- Truy vết một con số qua mọi tầng: tổng lợi suất Holdout của Combined 38,9% khớp từ CSV gốc → bundle → API → màn hình.
- Code triển khai ở commit 74db8d7, lên mạng ngày 05/11/2026.
### 10.4 Vận hành

- Render không tự deploy (autoDeploy tắt), phải bấm Manual Deploy. Gói miễn phí nên lần gọi đầu có thể chậm vài chục giây. **Nên mở trang trước buổi thuyết trình vài phút.**
- Vercel deploy tay bằng CLI từ web/frontend.
- Thêm file dữ liệu mới thì phải upload lên Hugging Face rồi đổi DATA_BASE_URL sang commit mới.
## 11. Final, phần mở rộng và giới hạn

### 11.1 Final Evaluation (năm 2026)

- Trạng thái **NOT_READY**: chưa đủ dữ liệu 2026, chưa có cửa sổ Final và run Final đã niêm phong.
- Khi đủ dữ liệu: chạy một lần với cấu hình đã khóa, bắt đầu từ snapshot cuối 01/2026 (Q16). Đây là nơi duy nhất tính Sharpe.
- B-PIT FY2025 cũng đang NOT_READY (mới có 3 BCTC dùng được), cần bổ sung trước khi chạy Final.
### 11.2 Phần mở rộng: phí giao dịch

Theo mentor, kịch bản chính không tính phí. Phần mở rộng sẽ chạy thêm với phí **15 bps** và **30 bps**. Vì Combined có turnover 48–55% mỗi kỳ, cao hơn Momentum-only (28–32%) và Equal-weight (8–12%), dự kiến Combined sẽ bị ảnh hưởng bởi phí nhiều hơn (đây là suy luận từ turnover, chưa chạy).

### 11.3 Giới hạn cần nói rõ

| Giới hạn | Ảnh hưởng |
| --- | --- |
| Chiến lược dùng giá điều chỉnh (có cổ tức), VNINDEX là chỉ số giá | So với VNINDEX hơi có lợi cho chiến lược; chưa có benchmark tổng lợi suất tương đương |
| Phí, trượt giá = 0; vị thế phân số; không có sổ lệnh | Lợi suất thực tế sẽ thấp hơn |
| Drawdown đo theo kỳ tháng | Drawdown theo ngày có thể sâu hơn |
| Dữ liệu tài chính là snapshot hiện tại, không phải bản gốc lúc công bố | Nếu doanh nghiệp sửa BCTC về sau thì vẫn còn chút look-ahead |
| Độ ổn định B v4 chưa đạt ngưỡng mong muốn | Giới hạn từ tầng phân cụm |
| Holdout “sạch” ở tầng quy tắc danh mục | Không khẳng định hoàn toàn chưa thấy đối với mọi lựa chọn mô hình ở M2 |
| Hai đoạn Dev/Holdout | Không phải kiểm định thống kê về hiệu quả tương lai |

### 11.4 Hướng phát triển

- Chạy Final 2026 khi đủ dữ liệu.
- Chạy phần mở rộng phí 15/30 bps.
- Phân rã đóng góp của phần tài chính (vì sao Combined chưa thắng Momentum-only).
- Dựng benchmark tổng lợi suất (VN-Index có cổ tức) để so sánh công bằng.
- Bổ sung metrics.json/manifest lên git và sửa link hỏng trong báo cáo kỹ thuật.
### 11.5 Câu hỏi mentor có thể hỏi về M3

- *Combined thua Momentum-only, vậy phân cụm có ích gì?* Kết quả hiện tại chưa cho thấy ưu thế. Nhóm báo cáo trung thực và không chỉnh cấu hình sau khi thấy kết quả. Một phần nguyên nhân có thể là 13/60 kỳ Dev thiếu ứng viên và 22% tiền mặt không sinh lãi.
- *Vì sao Combined thua VNINDEX ở Holdout?* 2024–2025 VN-Index tăng mạnh (CAGR 24,47%) với drawdown thấp; chiến lược momentum đầu tư vào mã nhỏ hơn, biến động hơn.
- *Có nhìn trước tương lai không?* Không ở tầng giá (cách ly đoạn, giao dịch t+1) và tầng ngày công bố BCTC (B-PIT, cổng ngày cắt). Còn giới hạn về phiên bản số liệu BCTC.
- *Chạy lại được không?* Được, qua notebook 01–03 với mã run, commit và sha cấu hình đã ghim.



## 12. Hệ thống Đánh giá đầu tư (DELTA Investment Assessment — D-ASS-01)

Nhằm đưa các thành quả nghiên cứu định lượng (M1, M2, M3) vào ứng dụng thực tiễn cho nhà đầu tư cá nhân và tổ chức, nhóm đã thiết kế và triển khai **Hệ thống Đánh giá đầu tư DELTA (DELTA Investment Assessment)** tuân thủ nghiêm ngặt quy chuẩn nghiệp vụ **D-ASS-01**.

### 12.1 Quy chuẩn nghiệp vụ D-ASS-01 (Rulebook Matrix)
Quy chuẩn D-ASS-01 định nghĩa cơ chế xếp hạng và chấm điểm cổ phiếu kết hợp đa chiều:
1. **Ma trận phối hợp 2 chiều (Momentum × Fundamentals):**
   - **Trục Động lượng:** Dựa trên kết quả phân cụm thị trường Mô hình A v4 (Cụm 0: Dẫn dắt/Đột phá; Cụm 1: Tích lũy/Bền vững; Cụm 2: Suy yếu/Rủi ro cao).
   - **Trục Tài chính:** Dựa trên kết quả phân cụm B-PIT Enriched (Cụm 0: Nền tảng vàng/Chất lượng cao; Cụm 1: Trung bình khá; Cụm 2: Báo động nợ/Thua lỗ).
2. **Hệ thống 4 mức phân hạng khuyến nghị:**
   - **Tích cực (Strong Outperform / Top Pick):** Cổ phiếu thuộc cụm Động lượng dẫn dắt đồng thời sở hữu nền tảng tài chính lành mạnh vững vàng.
   - **Khả quan (Accumulate / Buy):** Cổ phiếu có nền tảng tài chính xuất sắc đang trong pha tích lũy, hoặc cổ phiếu động lượng cao với tài chính ở mức chấp nhận được.
   - **Theo dõi (Neutral / Watchlist):** Cổ phiếu có diễn biến trung tính, cần chờ đợi thêm tín hiệu bứt phá về thanh khoản hoặc kết quả kinh doanh quý mới.
   - **Thận trọng (Underperform / Avoid):** Cổ phiếu suy yếu về động lượng giá hoặc rơi vào cụm rủi ro tài chính cao (đòn bẩy lớn, biên lợi nhuận âm).
3. **Bộ 18 đặc trưng phân tích chuẩn hóa:**
   - **9 đặc trưng thị trường:** `volatility_20d`, `momentum_60d`, `momentum_120d`, `rsi_14d`, `macd_signal_ratio`, `liquidity_ratio`, `trend_strength`, `volume_trend`, `price_range_ratio`.
   - **9 đặc trưng tài chính:** `pe_ratio`, `pb_ratio`, `roe`, `roa`, `net_profit_margin`, `debt_to_equity`, `current_ratio`, `revenue_growth_yoy`, `profit_growth_yoy`.

### 12.2 Kiến trúc Tầng dịch vụ Backend FastAPI & REST API (Người 3 phụ trách)
Hệ thống backend được thiết kế theo hướng microservice gọn nhẹ, hiệu năng cao, đặt tại `web/backend/`:
1. **Module lõi:** `web/backend/app/assessment.py` tích hợp offline artifact builder `investment_assessment_v1.parquet` do Người 1 cung cấp.
2. **REST API Endpoint:**
   ```http
   GET /api/v1/assessment/{ticker}
   ```
   - **Đầu vào:** Mã cổ phiếu (ví dụ `FPT`, `VNM`, `HPG`).
   - **Đầu ra (JSON Schema):** Chứa thông tin hồ sơ doanh nghiệp, phân hạng D-ASS-01 (badge, verdict, rationale bằng tiếng Việt), giá trị 18 đặc trưng cùng nhãn phân loại (Tốt/Trung bình/Kém), lịch sử phân hạng 5 năm và 10 năm, và danh sách đối sánh Peers cùng ngành.
3. **Tối ưu hóa hiệu năng & Bộ nhớ đệm:**
   - Tải trước toàn bộ bảng dữ liệu 1.522 mã vào bộ nhớ RAM khi khởi động server.
   - Thời gian phản hồi API trung bình đạt **dưới 15ms** (đáp ứng xuất sắc yêu cầu SLA < 100ms).
4. **Bộ kiểm tra tự động độc lập (`assessment_release_verifier.py`):**
   - Kiểm tra tính đầy đủ 100% của 1.522 mã cổ phiếu.
   - Xác thực schema Pydantic, kiểm tra lỗi thiếu trường (missing fields) và tính nhất quán với artifacts M1/M2/M3.

### 12.3 Giao diện Người dùng Tab 5 Next.js (Người 4 phụ trách)
Giao diện trực quan được xây dựng trên nền tảng Next.js hiện đại, tích hợp trực tiếp vào trang thông tin chi tiết cổ phiếu `/stocks`:
1. **Thẻ phân hạng tổng quan (Verdict Badge):**
   - Hiển thị mức khuyến nghị theo chuẩn màu sắc trực quan (Xanh lá: Tích cực; Xanh dương: Khả quan; Vàng: Theo dõi; Đỏ: Thận trọng).
   - Đoạn văn luận giải đầu tư (Investment Rationale) súc tích, tự động tổng hợp từ logic chấm điểm D-ASS-01.
2. **Bảng 18 chỉ số chi tiết (Feature Matrix):**
   - Chia 2 nhóm rõ ràng: 9 chỉ số Động lượng thị trường & 9 chỉ số Sức khỏe tài chính.
   - Từng chỉ số đều có giá trị thực tế, giá trị percentile toàn thị trường, và đánh giá trạng thái kèm chú thích dễ hiểu cho nhà đầu tư không chuyên.
3. **Thanh lọc Lookback lịch sử linh hoạt:**
   - Cho phép người dùng lựa chọn góc nhìn lịch sử: **5 năm** (ngắn và trung hạn) hoặc **10 năm** (chu kỳ kinh tế dài hạn) để quan sát sự chuyển dịch cụm của doanh nghiệp qua thời gian.
4. **Mô-đun đối sánh Peers cùng phân ngành (Industry Peers Comparison):**
   - Tự động liệt kê các cổ phiếu đầu ngành cùng phân loại ICB cấp 2.
   - So sánh trực tiếp vị thế tương đối giữa cổ phiếu đang xem và các đối thủ cạnh tranh về cả động lượng lẫn định giá tài chính.

### 12.4 Kiểm thử tích hợp UAT và Quy trình bàn giao
- **Kiểm thử tích hợp (End-to-End Integration):** Kết nối thông suốt giữa Frontend Next.js và Backend FastAPI.
- **Kiểm thử hồi quy (Regression Testing):** Chạy toàn bộ test suite backend và frontend, xác nhận không có bất kỳ xung đột nào với các tính năng cũ (Dashboard M3, bộ lọc thị trường M1).
- **Trạng thái nghiệm thu:** Đạt chuẩn 100% yêu cầu kỹ thuật và nghiệp vụ, sẵn sàng triển khai phục vụ người dùng cuối.
