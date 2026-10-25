# M3 — Câu hỏi cần mentor/owner chốt (26/10/2026)

Các quyết định dưới đây chặn bước chạy backtest có lợi suất. Mọi số liệu trong tài liệu là **đếm số mã**, chưa có
lợi suất nào được tính (`configs/experiments/m3_strategy_v1.json` đang ở trạng thái `PROPOSED`; `scripts/run_m3.py`
từ chối chạy backtest cho tới khi chuyển sang `LOCKED`). Mỗi câu có phương án đề xuất; mentor chỉ cần ghi
"Đồng ý" hoặc phương án khác vào dòng **Trả lời**. Chi tiết: `docs/M3_PLAN.md` mục 4.

Bối cảnh: A = mô hình thị trường bundle v4 (k=3, học trên mã có giao dịch); B = mô hình tài chính bundle v4 (k=3,
doanh nghiệp phi tài chính); Development = 60 kỳ 2019-01 → 2023-12; Holdout = 24 kỳ 2024-01 → 2025-12.

---

## Nhóm 1 — Quy tắc chọn mã (ưu tiên cao nhất)

### Q5/Q6. Tập ứng viên quá nhỏ với quy tắc gốc

Quy tắc gốc (plan V5.1): Candidate Universe = mã thuộc *cụm dẫn dắt* thị trường ∩ mã thuộc *cụm dẫn dắt* tài chính.
Cụm dẫn dắt chọn cơ học từ profile (thị trường: trung vị động lượng 6 tháng cao nhất; tài chính: trung vị ROE cao
nhất), không dùng lợi suất. Đếm từng tháng (`scripts/m3_feasibility_variants.py`):

| Phương án | Development: trung vị / min ứng viên | Tháng < 10 mã | Mã được chọn (30%, trung vị) | Holdout: trung vị ứng viên | Holdout tháng < 10 |
|---|---|---|---|---|---|
| **V0** cụm mạnh nhất ∩ cụm mạnh nhất (gốc) | 8 / 0 | **38/60** | 3 | 19 | 3/24 |
| **Va** cụm mạnh nhất ∩ tài chính *không thuộc cụm yếu nhất* | 26 / 3 | 13/60 | 8,5 | 40 | 0/24 |
| **Vb** *2 cụm mạnh nhất* ∩ cụm mạnh nhất | 61 / 7 | 1/60 | 18,5 | 111 | 0/24 |
| **Vab** 2 cụm mạnh nhất ∩ không thuộc cụm yếu nhất | 112 / 15 | 0/60 | 34 | 173,5 | 0/24 |

Nhận xét: A chỉ có 3 cụm, nên "2 cụm mạnh nhất" (Vb, Vab) đã gần bằng 2/3 thị trường có giao dịch — mất tính chọn lọc
của phân cụm. **Va** giữ được ý tưởng "cụm dẫn dắt thị trường" và chỉ nới điều kiện tài chính thành "loại cụm yếu
nhất"; Development còn 13/60 tháng dưới 10 mã.

Ngưỡng tối thiểu `N_min`: tháng có ít ứng viên hơn ngưỡng thì **giữ danh mục hiện có**, chỉ bán mã đã rời tập ứng
viên (không mua mới).

- **Đề xuất:** Va + `N_min = 10`. (Nếu mentor muốn ít tháng "đứng yên" hơn: Va + `N_min = 5`, còn 4/60 tháng.)
- **Trả lời:**

### Q7. Ba tiêu chí thị trường (xếp hạng trong tập ứng viên, percentile)

- **Đề xuất:** MC1 = động lượng 6 tháng (cao tốt); MC2 = biến động giảm 63 phiên (thấp tốt); MC3 = giá trị giao dịch
  21 phiên (cao tốt). Đều có sẵn trong snapshot A tại ngày quyết định.
- **Trả lời:**

### Q8. Ba tiêu chí tài chính

- **Đề xuất:** FC1 = ROE; FC2 = F-score (0–9); FC3 = Z-score — lấy từ năm tài chính mới nhất đã công bố tại ngày quyết
  định. Thiếu một tiêu chí → percentile trung tính 0,5 và gắn cờ; thiếu cả ba → loại. Lưu ý: F-score trước 2022 chỉ
  phủ khoảng 50% số mã (2017: 89 mã), nên ở Development nhiều mã dùng giá trị trung tính cho FC2.
- **Trả lời:**

### Q9. Gộp hai nhánh thành thứ hạng cuối

- **Đề xuất:** điểm = 0,5 × trung bình percentile 3 tiêu chí thị trường + 0,5 × trung bình percentile 3 tiêu chí tài
  chính. Bằng điểm → giá trị giao dịch cao hơn → mã A→Z. Chọn `ceil(30% × N)` mã, trọng số bằng nhau.
- **Trả lời:**

### Q4. Ngân hàng, chứng khoán, bảo hiểm

B không có nhãn cho nhóm ngành tài chính, nên các mã này không thể vào chiến lược Combined.

- **Đề xuất:** loại khỏi Combined (lý do `FINANCIAL_SECTOR_NO_B`, báo cáo tỷ lệ mỗi tháng); vẫn có mặt trong các đối
  chứng Market-only, Equal-weight, Momentum-only.
- **Trả lời:**

---

## Nhóm 2 — Mô hình và dữ liệu đầu vào

### Q1. Mô hình thị trường cho M3

- **Đề xuất:** A v4 (k=3). Bàn giao M2 K=2 của nhóm chạy như một đối chứng. Lý do: cùng tập mã và cùng không gian, A v4
  có silhouette 0,24 so với 0,11, cụm nhỏ nhất 14% so với 3,7%; chọn lại chỉ trên 2019–2023 vẫn ra k=3
  (`artifacts/reports/m2-vs-rework-v1/report.md`). M2 K=2 chỉ có trung vị 4,5 ứng viên/tháng ở Development.
- **Trả lời:**

### Q3. Rò rỉ ở tâm cụm tài chính

B được học trên toàn bộ báo cáo của mỗi năm tài chính, kể cả báo cáo của các mã công bố muộn hơn ngày quyết định.

- **Phương án 1 (đề xuất):** dựng B-PIT — mỗi năm học tại mốc 30/04 năm sau chỉ với báo cáo đã công bố tới mốc đó, báo
  cáo đến sau được gán vào tâm cụm đã cố định. Cùng thuật toán, k, chuẩn hóa như B.
- **Phương án 2:** giữ B hiện tại và ghi rõ đây là giới hạn trong báo cáo.
- **Trả lời:**

### Q-date. Ngày công bố báo cáo năm

Ngày gửi trên CafeF chỉ tin được từ năm tài chính 2022 (CafeF nhập lại toàn bộ lịch sử ngày 26/11/2022). Trước đó dùng
quy tắc trễ: báo cáo năm t dùng được từ phiên đầu tiên sau **30/06 năm t+1**. Theo dữ liệu 2022–2025, 2–4% mã-năm gửi
báo cáo sau 30/06 (9–15% gửi sau 30/04) → ở Development, vài phần trăm mã có thể bị coi là đã có báo cáo sớm hơn thực
tế. Có 13 mã có năm tài chính không kết thúc 31/12 (CTD, HSG, CAP, …): quy tắc trễ làm các mã này "biết" muộn hơn thực
tế, không rò rỉ.

- **Đề xuất:** dùng như trên, kèm một kịch bản kiểm tra độ nhạy với mốc 30/04.
- **Trả lời:**

### Q10. Báo cáo tài chính quá cũ

- **Đề xuất:** bản năm t hết hiệu lực khi bản năm t+1 dùng được; giới hạn cứng 18 tháng sau 31/12 năm t.
- **Trả lời:**

---

## Nhóm 3 — Giả định giao dịch và đo lường

### Q11. Cơ sở lợi suất

Giá điều chỉnh của CafeF đã gồm cổ tức tiền mặt (kiểm trên 1.499 mã: bước nhảy nhỏ của tỷ lệ adj/raw tổng trung vị
4,2%/năm), còn VNINDEX là chỉ số giá — so thẳng thì danh mục được cộng thêm cổ tức.

- **Đề xuất:** kịch bản chính dùng giá điều chỉnh, ghi rõ chênh lệch; kèm kịch bản phụ lợi suất giá thuần để so ngang
  VNINDEX.
- **Trả lời:**

### Q17. Lỗi giá điều chỉnh lệch một phiên

Có 1.030 phiên giá điều chỉnh lệch > 3% rồi quay lại ngay hôm sau trong khi giá gốc không đổi (ví dụ FPT 03/02/2025);
135 trường hợp rơi đúng phiên đầu tháng — ngày thực hiện giao dịch.

- **Đề xuất:** sửa giá phiên đó theo tỷ lệ adj/raw của phiên kế tiếp, gắn cờ, không sửa dữ liệu gốc (đã cài và có test).
- **Trả lời:**

### Q12. Giá trần/sàn

- **Đề xuất:** đóng cửa bằng giá trần → lệnh mua coi như không khớp; bằng giá sàn → lệnh bán không khớp; khối lượng 0 →
  không khớp cả hai chiều (không có dữ liệu dư mua/bán).
- **Trả lời:**

### Q13. Công thức turnover

Plan V5.1 tính *(giá trị mua + giá trị bán đã khớp) / NAV* (ví dụ kỳ 1 = 0,75). Plan hiện tại đề xuất một chiều
*(mua + bán) / (2 × NAV)* (= 0,375), cách phổ biến khi báo cáo chi phí. Engine tái hiện đúng cả ba kỳ của ví dụ V5.1.

- **Đề xuất:** báo cáo một chiều, ghi kèm số hai chiều.
- **Trả lời:**

### Q14. Đối chứng

- **Đề xuất:** benchmark chính thức VNINDEX; đối chứng nghiên cứu: Market-only, Financial-only, Equal-weight (mọi mã có
  giao dịch), Momentum-only (top 30% động lượng 6 tháng), M2 K=2.
- **Trả lời:**

### Q15. Holdout có còn "sạch" không

Mô hình A/B được chọn sau khi xem thước đo cụm trên cả 2019–2025; chọn lại chỉ trên 2019–2023 vẫn ra k=3. Quy tắc danh
mục thì chưa ai xem lợi suất.

- **Đề xuất:** ghi trong báo cáo: Holdout sạch về quy tắc danh mục và về lựa chọn k; Final Evaluation 2026 là kết luận
  chính.
- **Trả lời:**

### Q16. Cửa sổ Final Evaluation

- **Đề xuất:** từ snapshot cuối tháng 01/2026 tới tháng gần nhất có đủ giá, VNINDEX và ngày công bố BCTC năm 2025; khóa
  trước khi chạy. Sharpe chỉ tính ở đây, kèm khoảng tin cậy vì mới khoảng 9–10 tháng.
- **Trả lời:**

---

## Sau khi có câu trả lời

1. Ghi các câu trả lời vào `docs/DECISIONS.md` (ADR M3) và `configs/experiments/m3_strategy_v1.json`, đổi `status`
   thành `LOCKED`, ghi hash config.
2. `python scripts/run_m3.py --segment development --targets-only` → owner xem danh sách mã từng tháng.
3. `python scripts/run_m3.py --segment development` → seal; rồi `--segment holdout` với cùng config.
