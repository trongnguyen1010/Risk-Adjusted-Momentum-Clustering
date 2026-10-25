# Kế hoạch M3 — Danh mục, backtest, dashboard và báo cáo tái lập

**Phiên bản:** v1.0 (25/10/2026). Viết lại từ bản "Kế hoạch tổng thể M3 V5.1" của nhóm, đối chiếu với trạng thái
thật của nhánh `feature/indicators-v1` (bundle web v4, Indicators v1).
**Trạng thái:** KẾ HOẠCH — chưa chạy backtest. Giai đoạn 0 và 2 có thể bắt đầu ngay; giai đoạn 3 trở đi chờ khóa
quyết định ở mục 4.

Quy ước trạng thái trong tài liệu:

- **KẾ THỪA** — đã có trong repo (code, artifact, ADR); M3 không tự đổi.
- **ĐÃ DUYỆT** — owner đã chốt (ghi ngày, nguồn).
- **ĐỀ XUẤT** — phương án mặc định của plan này; chỉ thành quyết định khi owner/mentor ký vào bảng quyết định.
- **MỞ** — chưa có phương án đủ căn cứ; nhiệm vụ phụ thuộc phải dừng.

---

## 1. Mục tiêu M3

1. **M3-A — Backtest:** kiểm tra một chiến lược chỉ mua, tái cân bằng hàng tháng, chọn cổ phiếu bằng trạng thái
   cụm thị trường (A) và cụm tài chính (B) tại từng thời điểm, so với VNINDEX và các đối chứng, không dùng thông tin
   tương lai.
2. **M3-B — Dashboard:** đưa kết quả M3-A lên web hiện có (Next.js + FastAPI, chỉ đọc).
3. **M3-C — Báo cáo và tái lập:** notebook, hướng dẫn chạy lại, báo cáo kỹ thuật; mọi con số truy được về input,
   config, commit và lần chạy.

Ngoài phạm vi: Dynamic Clustering (review chưa duyệt), giao dịch thực, chi phí/thuế chi tiết, đòn bẩy, bán khống,
tối ưu tham số bằng lợi suất.

---

## 2. Tình trạng đầu vào thực tế (25/10/2026)

| Đầu vào | Hiện có | Vị trí | Ghi chú cho M3 |
|---|---|---|---|
| Cụm thị trường A | 84 snapshot tháng 2019-01-31 → 2025-12-31; 9 đặc trưng (thêm `downside_vol_63`); K-Means k=3 học trên mã có giao dịch (lọc nhẹ), mã kém thanh khoản gán vào tâm gần nhất và gắn cờ `ILLIQUID` | `data/web/delta-intelligence-v4/terminal.sqlite` (`observations`, `profiles`, `snapshots` kind=`market`) | Tên/mô tả cụm có sẵn (`profiles.name/description`). Đặc trưng chỉ dùng giá quá khứ → PIT theo ngày snapshot. |
| Cụm tài chính B | 10 năm tài chính 2016–2025; 9 chỉ số (ROE, ROA, biên gộp, biên ròng, D/E, thanh toán hiện hành, vòng quay TS, tăng trưởng DT, CFO/LN); k=3; **chỉ doanh nghiệp phi tài chính** | cùng bundle, kind=`financial` | Độ ổn định lấy mẫu con ARI ≈ 0,50 (đã gắn cảnh báo). Mỗi năm fit trên toàn bộ mặt cắt năm đó. |
| Mô hình C (kết hợp) | 7 năm, k=4 | kind=`combined` | **Không dùng cho M3-A** (M3 kết hợp ở bước chọn danh mục, không gộp đặc trưng). Chỉ hiển thị. |
| Bàn giao M2 cũ | K=2 RobustScaler, 8 đặc trưng, 84 snapshot | nhánh `m2-clustering-experiment`, `M2/artifacts/m2-final-handoff-v1/` | Cụm nhỏ chỉ 2–41 mã/tháng (trung vị 20). Giữ làm đối chứng/tham khảo, xem quyết định Q1. |
| Chỉ số tài chính | EPS, P/E, P/B, ROE, F, M, Z theo năm, 1.510 mã kể cả ngân hàng/CK/bảo hiểm | `data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite` | Nguồn cho FC1–FC3. Công thức theo D-IND-01. |
| Ngày công bố BCTC | Bảng `ticker × năm tài chính → usable_from_date` cho 1.362 mã có nhãn B, 2016–2025 | `data/financial/disclosure_dates_v1/availability-<hash>/` (dựng bằng `scripts/build_financial_availability.py` từ crawl `scripts/crawl_cafef_disclosure_dates.py`) | **Năm tài chính ≥ 2022:** ngày gửi sớm nhất (`CreateDate`, API Công bố thông tin CafeF) của BCTC năm đã kiểm toán (HK/K/MK) → `CAFEF_DISCLOSURE`. **Trước 2022 hoặc không có bản ghi:** 30/06 năm t+1 → `LAG_RULE` (CafeF nhập lại lịch sử ngày 26/11/2022 nên mọi bản ghi cũ mang ngày đó). `usable_from_date` = phiên giao dịch đầu tiên **sau** ngày đó. Ngày CafeF không bao giờ sớm hơn ngày công bố thật (đối chiếu FPT/PVS/ACV: lệch 0 đến +62 ngày). |
| Giá hằng ngày | 1.499 mã, 2016-01-04 → 2025-12-31, `vendor_adjusted` (CafeF AdjustPrice) + `raw_close`, volume | bundle `prices` | Kiểm sơ bộ 25/10: tỷ lệ adj/raw nhảy 1–3,5% tại các ngày GDKHQ cổ tức tiền mặt (VNM, FPT, REE) và 10–20% tại cổ tức cổ phiếu → **giá điều chỉnh đã gồm cổ tức tiền mặt** (gần tổng lợi suất), trong khi VNINDEX là chỉ số giá. Có vài cặp nhảy −9%/+10% liền nhau (FPT, GAS ngày 03–04/02/2025) là lỗi dữ liệu nhà cung cấp. Nhiệm vụ 0.5 xác nhận trên mẫu lớn hơn. |
| VNINDEX | 2.500 phiên 04/01/2016 → 31/12/2025, chỉ số giá (`index_basis=price`), nguồn vnstock_vci; khớp 100% lịch phiên HOSE/HNX/UPCOM | `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/benchmark_daily.jsonl` (+ `trading_calendar.jsonl`) | Chỉ còn pin hash vào manifest M3 (0.1). |
| Giá trần/sàn, khả năng giao dịch | `reference_price`, `ceiling_price`, `floor_price`, `tradability_eligible`, `trading_activity_status` có cho 100% dòng 2019–2025 (2,45 triệu dòng); ~3% phiên có giao dịch đóng ở trần, ~2% ở sàn | `.../canonical/prices_daily.jsonl` (C8, 4,2 GB) | Không có dư mua/bán trần → quy tắc Q12 dùng "đóng cửa = trần ⇒ BUY_FAILED; = sàn ⇒ SELL_FAILED" (bảo thủ). |
| Engine danh mục | `backtest/returns_engine.py` (mô phỏng theo tỷ trọng, có cost/turnover), `evaluation/portfolio_metrics.py` | `src/delta_t1/` | Chưa có xử lý lệnh thất bại, `execution_scale`, sổ lệnh. M3 mở rộng thành engine mới có test (mục 6). |
| Dữ liệu sau 31/12/2025 | Chưa có trong bundle | — | Cần thu thập giá, BCTC, VNINDEX năm 2026 cho Final Evaluation (giai đoạn 5). |

**Hệ quả quan trọng:** M3 đọc trực tiếp các artifact đã có hash ở trên, **không fit lại** A hoặc B, không đổi k,
không đổi chuẩn hóa. Nếu cần một biến thể (ví dụ B fit theo mốc công bố, mục 4 Q3), phải tạo version mới có config,
test và ADR riêng trước khi M3 dùng.

---

## 3. Nguyên tắc bất biến

Kế thừa từ `AGENTS.md`, `docs/EVALUATION_AND_BACKTEST.md`, `docs/DATA_CONTRACT.md`:

1. **Hai hệ cụm độc lập; kết hợp ở bước chọn danh mục.** Không gộp đặc trưng thô để phân cụm lại cho M3.
2. **PIT:** tại `decision_date` t chỉ dùng dữ liệu thị trường đến hết phiên t và bản ghi tài chính có
   `usable_from_date <= t`. Không dùng `period_end` thay cho ngày công bố.
3. **Ba lớp đánh giá tách rời:** chất lượng cụm, ổn định theo thời gian, hiệu quả danh mục. Không chọn k, mô hình,
   cụm "dẫn dắt", tiêu chí hay trọng số bằng lợi suất, Sharpe hay ROI.
4. **Khóa trước khi chạy:** mọi quy tắc danh mục được ghi vào config có hash và ADR **trước** lần chạy Development;
   Holdout chạy bằng đúng config đó; Final Evaluation khóa cửa sổ trước khi xem kết quả.
5. **Không làm đẹp dữ liệu:** không forward-fill giá, không biến thiếu thành 0, không trộn raw/adjusted, không xóa
   kết quả bất lợi.
6. **Bất biến artifact:** mỗi lần chạy có `run_id`, manifest, hash input/config/code; sửa quy tắc → run mới.
7. **Sharpe chỉ ở Final Evaluation** (ĐÃ DUYỆT 24/10/2026). Development/Holdout báo CAGR, volatility, MDD,
   turnover, tỷ lệ tiền mặt, nhưng không Sharpe/Sortino/IR.

---

## 4. Bảng quyết định

### 4.1. Đã duyệt (kế thừa từ plan V5.1, owner 24/10/2026)

| ID | Nội dung |
|---|---|
| D01 | Chỉ mua, không bán khống, không đòn bẩy. |
| D02 | Tái cân bằng hàng tháng tại các ngày snapshot thị trường. |
| D03 | Candidate Universe = Market Eligible Pool ∩ Financial Eligible Pool (tạo trước khi tính tiêu chí). |
| D04 | Chọn `n = ceil(0,30 × N_candidates)` mã đứng đầu, trọng số bằng nhau `1/n`. |
| D05 | Giao dịch tại giá đóng cửa phiên hợp lệ kế tiếp sau `decision_date`. |
| D06 | BUY_FAILED: phần vốn giữ ở tiền mặt, không thay mã, không chia lại. SELL_FAILED: mã vẫn nằm trong danh mục, không tạo tiền. |
| D07 | Thiếu tiền do SELL_FAILED → mọi BUY còn lại nhân `execution_scale = available_cash / total_required_buy_cash` (≤ 1). |
| D08 | Tiền mặt lãi 0; chi phí và trượt giá kịch bản chính = 0 (kịch bản nhạy chi phí báo cáo riêng, mục 7.3). |
| D09 | Cụm "dẫn dắt" chọn theo profile/ngữ nghĩa, không theo số nhãn; mơ hồ → BLOCKED. |
| D10 | Tài chính: nhiều bản ghi hợp lệ → dùng bản có ngày dùng được mới nhất; xung đột cùng ngày → fail-closed. |
| D11 | Development 60 snapshot 2019-01-31 → 2023-12-29; Holdout 24 snapshot 2024-01-31 → 2025-12-31. |
| D12 | Benchmark chính thức: VNINDEX. |
| D13 | Final Evaluation dùng dữ liệu sau 31/12/2025, khóa cửa sổ sau audit sẵn sàng. |

### 4.2. Cần khóa trước Development — có phương án đề xuất

| ID | Câu hỏi | Đề xuất | Lý do | Người chốt |
|---|---|---|---|---|
| **Q1** | M3 dùng mô hình thị trường nào? | **A v4** (k=3, 9 đặc trưng, lọc thanh khoản nhẹ). Bàn giao M2 K=2 chạy như đối chứng "Market M2". | A v4 là bản owner duyệt mới nhất; K=2 cho cụm "dẫn dắt" chỉ ~20 mã nên tập ứng viên quá nhỏ. Ghi ADR "A v4 thay M2 K=2 làm input M3". | Owner + mentor |
| **Q2** | Mã `ILLIQUID` có được vào Market Eligible Pool? | **Không.** Mã kém thanh khoản (>50% phiên không khớp hoặc GTGD < 10 triệu/ngày trong 63 phiên) bị loại với lý do `MARKET_ILLIQUID`. | Không mua được thực tế; nhãn được gán bằng tâm gần nhất chứ không học. | Owner |
| **Q3** | B được fit trên cả năm tài chính → tâm cụm dùng cả báo cáo công bố muộn hơn ngày quyết định. Xử lý? | Tạo **B-PIT v1**: mỗi năm tài chính t, fit tại mốc cố định `cutoff(t)` = 30/04/(t+1), chỉ dùng báo cáo có `usable_from_date <= cutoff`; báo cáo đến sau được **gán** vào tâm đã đóng băng từ ngày dùng được của nó. Cùng thuật toán, k, chuẩn hóa như B v4. | Loại rò rỉ ở cấp tâm cụm; vẫn giữ mô hình B. Nếu owner chấp nhận rò rỉ này như giới hạn mô tả thì ghi rõ trong báo cáo và giữ B v4. | Owner + mentor |
| **Q4** | Ngân hàng/CK/bảo hiểm không có nhãn B. | **Đề xuất A:** loại khỏi chiến lược Combined với lý do `FINANCIAL_SECTOR_NO_B`, báo cáo tỷ lệ bị loại mỗi tháng. **Phương án B (nếu muốn giữ):** phân cụm tài chính riêng cho nhóm ngành tài chính (cần mô hình mới, ngoài M3-A). | Ở cụm thanh khoản cao, ~50% là ngân hàng/CK; loại họ thu hẹp tập mạnh — phải đo ở nhiệm vụ 0.4 trước khi chốt. | Owner |
| **Q5** | Quy tắc "cụm dẫn dắt" cụ thể. | Tính từ **profile của chính snapshot đó**, không dùng lợi suất tương lai. **Market:** cụm có trung vị `mom_126` cao nhất trong các cụm học được; hòa → trung vị `mdd_126` cao hơn (sụt giảm nông hơn). **Financial:** cụm có trung vị ROE cao nhất; hòa → trung vị D/E thấp hơn. Mỗi kỳ ghi cụm được chọn và giá trị profile vào `leading_cluster_audit.csv`. | Quy tắc cơ học, kiểm chứng lại được, không phụ thuộc số nhãn. Tên cụm (`profiles.name`) chỉ để hiển thị, không dùng để chọn. | Mentor |
| **Q6** | Tập ứng viên quá nhỏ. | Ngưỡng `N_min = 10`. Tháng có `N_candidates < N_min` → **không mở vị thế mới**: giữ nguyên danh mục đang có (không mua thêm, chỉ bán những mã đã rời tập ứng viên), ghi `UNIVERSE_TOO_SMALL`. Báo cáo số tháng bị ảnh hưởng. | Tránh danh mục 1–2 mã; quy tắc không dựa vào lợi suất. Con số 10 phải được xác nhận bằng phân phối đếm ở nhiệm vụ 0.4 (chỉ đếm, không xem lợi suất). | Owner + mentor |
| **Q7** | MC1–MC3 (xếp hạng thị trường, cao hơn là tốt). | MC1 = `mom_126` (động lượng 6 tháng); MC2 = −`downside_vol_63` (biến động giảm thấp); MC3 = `log(liquidity_21)` (thanh khoản). | Đều là đặc trưng đã có trong snapshot A tại t, không cần tính mới. | Mentor |
| **Q8** | FC1–FC3 (xếp hạng tài chính). | FC1 = ROE; FC2 = F-score (0–9); FC3 = Z-score (an toàn tài chính). Bản ghi tài chính = năm mới nhất dùng được tại t. Thiếu FC nào → percentile của tiêu chí đó = 0,5 (trung tính) và gắn cờ `FC_MISSING`; thiếu cả 3 → loại `FINANCIAL_CRITERIA_MISSING`. | ROE/F/Z đã có QA (Indicators v1, coverage 2025 ≥ 88%); khác bản chất với đặc trưng dùng để phân cụm B (F, Z không nằm trong B). | Mentor |
| **Q9** | Gộp thành thứ hạng cuối. | Trong tập ứng viên: percentile rank từng tiêu chí; `S_market` = trung bình MC1–MC3; `S_fin` = trung bình FC1–FC3; `S = 0,5·S_market + 0,5·S_fin`. Hòa → `liquidity_21` cao hơn → ticker A→Z. Ranh giới top n hòa điểm → áp tie rule, không mở rộng n. | Đơn giản, không có tham số để tối ưu, đối xứng giữa hai nhánh. | Mentor |
| **Q10** | Độ cũ dữ liệu tài chính. | Bản ghi năm t hết hiệu lực khi bản năm t+1 dùng được; giới hạn cứng 18 tháng sau `period_end` (≈ 30/06/t+2). Quá hạn → `FINANCIAL_STALE`. | Với dữ liệu năm, quy tắc tự nhiên là "năm mới nhất đã công bố"; 18 tháng bắt các trường hợp chậm nộp bất thường. | Owner |
| **Q11** | Cơ sở lợi suất. | Kịch bản chính = `adj_close` (đã gồm cổ tức tiền mặt theo kiểm sơ bộ) gọi là "adjusted total-return proxy"; mọi bảng so với VNINDEX ghi rõ VNINDEX là chỉ số giá, kèm dòng ước tính chênh lệch (tỷ suất cổ tức tiền mặt bình quân của danh mục). Kịch bản phụ = lợi suất giá thuần tính từ `raw_close` chỉ điều chỉnh chia tách/cổ tức cổ phiếu, để so ngang VNINDEX. Ngày nhảy bất thường (cặp ±9–10% liền nhau) được đánh dấu và loại khỏi chuỗi lợi suất của ngày đó, không sửa giá gốc. | Không tự trộn raw/adjusted; không cộng cổ tức hai lần. | Owner |
| **Q12** | Khả năng giao dịch tại phiên thực hiện. | Lệnh thực hiện được khi phiên đó có `adj_close` và `volume > 0`. BUY bị chặn nếu giá đóng cửa = giá trần **và** (nếu có dữ liệu) dư mua trần; SELL bị chặn tương tự với giá sàn. Không có dữ liệu trần/sàn → chỉ dùng quy tắc volume, ghi giả định. | Thị trường VN có biên độ giá; giữ quy tắc tối thiểu khi thiếu dữ liệu sổ lệnh. | Owner |
| **Q13** | Turnover. | Turnover một chiều kỳ k = `Σ|giá trị lệnh đã khớp| / (2 × NAV trước giao dịch)`. Chỉ tính lệnh khớp thật (sau `execution_scale`); trôi tỷ trọng do giá không phải giao dịch. | Chuẩn thông dụng; dùng cho kịch bản chi phí. | Owner |
| **Q14** | Đối chứng nghiên cứu. | Combined (chính); Market-only (Market Eligible Pool, xếp hạng MC); Financial-only (Financial Eligible Pool ∩ mã có giao dịch, xếp hạng FC); **Equal-weight toàn bộ mã có giao dịch**; **Momentum-only** (top 30% `mom_126` trong mã có giao dịch); Market M2 (K=2, nếu Q1 chọn A v4). Benchmark chính thức vẫn chỉ VNINDEX. | `EVALUATION_AND_BACKTEST.md` yêu cầu so với equal-weight universe và momentum-only; hai đối chứng này trả lời "phân cụm có thêm gì so với cách đơn giản". | Owner |
| **Q15** | Holdout đã "sạch" tới đâu? | Ghi rõ trong báo cáo: phương pháp A/B v4 được chọn sau khi xem chỉ số cụm trên **cả 84 snapshot** (gồm 2024–2025), nên Holdout **sạch về quy tắc danh mục** (chưa ai xem lợi suất) nhưng **không sạch về lựa chọn mô hình cụm**. Final Evaluation 2026 là đoạn duy nhất sạch cả hai. | Trung thực với người đọc; không đổi kết quả. | Owner |
| **Q16** | Cửa sổ Final Evaluation. | 2026-01-30 → snapshot cuối tháng gần nhất có đủ giá, BCTC (theo ngày công bố), VNINDEX; khóa trước khi chạy. | Hiện mới ~9–10 tháng; Sharpe trên ~9 điểm tháng chỉ mang tính mô tả, báo kèm khoảng tin cậy bootstrap. | Owner |

Khi một Q được chốt: cập nhật cột "Người chốt" thành ngày + người, chép vào `docs/DECISIONS.md` (ADR M3), và đưa vào
`configs/experiments/m3_strategy_v1.json`.

---

## 5. Luồng xử lý một kỳ

```text
decision_date t (snapshot A)
  │
  ├─ 1. Căn PIT: snapshot A tại t + bản ghi tài chính mới nhất có usable_from_date <= t (B nhãn, ROE/F/Z)
  ├─ 2. Market Eligible Pool: mã có nhãn A tại t, LIQUID, thuộc cụm dẫn dắt (Q5)
  ├─ 3. Financial Eligible Pool: mã có nhãn B dùng được, chưa quá hạn (Q10), thuộc cụm dẫn dắt (Q5)
  ├─ 4. Candidate Universe = (2) ∩ (3); ghi lý do loại cho mọi mã (mục 8.2)
  ├─ 5. N_candidates < N_min? → giữ danh mục (Q6)
  ├─ 6. Tính MC1–3, FC1–3 → S_market, S_fin, S (Q7–Q9)
  ├─ 7. Target = top ceil(30%·N), trọng số 1/n
  │
execution_date e = phiên giao dịch đầu tiên > t
  ├─ 8. Định giá danh mục tại e (trước giao dịch) → pre_trade_weight
  ├─ 9. delta = target − pre_trade_weight trên hợp các mã → SELL trước, BUY sau
  ├─ 10. Kiểm tra khả năng giao dịch (Q12) → SELL_FAILED / BUY_FAILED
  ├─ 11. Tiền sau bán; nếu thiếu → execution_scale cho mọi BUY còn lại (D07)
  ├─ 12. Danh mục thực tế + trade ledger + turnover (Q13)
  │
giữ đến execution_date kỳ sau e'
  └─ 13. Lợi suất từng mã e→e', đóng góp, NAV, tỷ trọng cuối kỳ → đầu vào bước 8 kỳ sau
```

Thiếu giá trong kỳ nắm giữ: dùng giá hợp lệ cuối cùng **chỉ để định giá**, gắn cờ `PRICE_STALE`; nếu mã bị hủy niêm
yết, giá trị bằng giá giao dịch cuối cùng chuyển sang tiền mặt tại phiên đó và ghi `DELISTED_EXIT` (giả định ghi rõ
trong báo cáo). Không forward-fill vào chuỗi giá gốc.

Kỳ đầu mỗi đoạn (Development, Holdout, Final): 100% tiền mặt. Kỳ cuối mỗi đoạn: định giá tại execution_date tiếp
theo nếu nằm trong dữ liệu, ngược lại tại phiên cuối của đoạn; không chuyển danh mục sang đoạn kế tiếp.

---

## 6. Kiến trúc mã nguồn

Logic nằm trong `src/delta_t1/`, notebook chỉ gọi hàm. Không fit mô hình trong M3.

| Module | Trách nhiệm |
|---|---|
| `m3/inputs.py` | Đọc và kiểm hash: snapshot A, nhãn B (v4 hoặc B-PIT), indicators, ngày công bố, giá, VNINDEX. Trả bảng chuẩn. |
| `m3/alignment.py` | Lịch `decision_date → execution_date`, ghép tài chính PIT, độ cũ. |
| `m3/universe.py` | Cụm dẫn dắt (Q5), hai pool, giao, lý do loại. |
| `m3/criteria.py` | MC1–3, FC1–3 theo contract (id, công thức, nguồn, quy tắc thiếu, quy tắc hòa). |
| `m3/ranking.py` | Percentile, điểm gộp, tie rule, top n. |
| `m3/execution.py` | Diff, SELL/BUY, khả năng giao dịch, `execution_scale`, ledger, turnover. |
| `m3/engine.py` | Vòng lặp theo kỳ, NAV, tỷ trọng cuối kỳ; nhận chiến lược như một hàm `targets(t)`. |
| `m3/strategies.py` | Combined, Market-only, Financial-only, Equal-weight, Momentum-only, Market M2. |
| `m3/benchmark.py` | Chuỗi VNINDEX căn cùng execution dates. |
| `evaluation/portfolio_metrics.py` | Tái dùng; thêm cờ `allow_sharpe` chỉ bật ở Final. |
| `scripts/run_m3.py` | `--segment development|holdout|final --config ... --dry-run`; ghi artifact. |

Config: `configs/experiments/m3_strategy_v1.json` (mọi giá trị ở mục 4, kèm hash input). Thiếu khóa nào → dừng.

Artifact: `data/experiments/m3/<segment>/<run_id>/` gồm:

```text
manifest.json                 input/config/code hash, segment, run_id, thời gian
alignment.csv                 decision_date, execution_date, snapshot A, bản ghi tài chính dùng, tuổi dữ liệu
leading_cluster_audit.csv     cụm dẫn dắt mỗi kỳ + giá trị profile
eligibility_audit.csv         mỗi mã × kỳ: market_eligible, financial_eligible, combined, reason
criteria.csv                  MC1–3, FC1–3, percentile, điểm, rank
targets_<strategy>.csv        decision_date, ticker, rank, target_weight
trade_ledger_<strategy>.csv   execution_date, ticker, side, intended, executed, scale, status, reason
holdings_<strategy>.csv       ngày, ticker, weight, value
nav_<strategy>.csv            ngày, NAV, cash, return kỳ
turnover_<strategy>.csv
benchmark_vnindex.csv
metrics.json                  theo segment và chiến lược (Sharpe chỉ khi segment=final)
validation.json               kết quả kiểm tra mục 8
```

Web chỉ đọc artifact đã seal (mục 9), không chạy engine.

---

## 7. Giai đoạn và nhiệm vụ

Mỗi nhiệm vụ: **đầu vào → việc làm → đầu ra → điều kiện PASS**. Một nhiệm vụ FAIL thì dừng, không tự sửa quy tắc.

### Giai đoạn 0 — Pin đầu vào và đo khả thi (không tính lợi suất)

**0.1 Manifest đầu vào.** Ghi path + sha256 + số dòng của: bundle v4 (`terminal.sqlite`), indicators v1, nguồn
ngày công bố, VNINDEX, bàn giao M2 K=2. PASS: `data/experiments/m3/inputs/manifest.json`, kiểm hash lại được.

**0.2 Crawl và audit ngày công bố.** Theo D-CRAWL-02: smoke 20 mã (gồm FPT, BRC, PVS, ACV để đối chiếu ngày đã
kiểm tay) → crawl toàn bộ mã có nhãn B qua `ajaxcongbothongtin.ashx`, lưu raw/receipt/hash. Lấy bản ghi BCTC năm
(ưu tiên bản đã kiểm toán hợp nhất; giữ riêng bản ban đầu/soát xét), ghép với năm tài chính, tính `usable_from_date`.
Báo cáo: độ phủ theo năm × (mã có nhãn B, mã có ROE/F/Z), phân phối độ trễ công bố, tỷ lệ dùng `LAG_RULE`, độ lệch
so với ngày đã kiểm tay. PASS: ngày CafeF **không sớm hơn** ngày kiểm tay ở mọi mã-năm đối chiếu; mọi mã-năm có
`date_source`. Kịch bản nhạy: chạy lại M3 với `--lag 04-30` (quy tắc trễ sớm hơn) và báo chênh lệch.
**Kết quả crawl 25/10/2026** (`full-20261025`, 1.362/1.362 mã DONE, không bị chặn; bảng
`availability-0c412f60f7c21bd3`, 13.620 mã-năm):

| Năm tài chính | CAFEF_DISCLOSURE | LAG_RULE | Gửi sau 30/04 | Gửi sau 30/06 |
|---|---|---|---|---|
| 2016–2021 | 0 | 1.362/năm | — | — |
| 2022 | 1.310 | 52 | 111 | 47 |
| 2023 | 1.287 | 75 | 152 | 32 |
| 2024 | 1.327 | 35 | 115 | 30 |
| 2025 | 1.257 | 105 | 191 | 25 |

- Độ trễ từ 31/12 đến ngày gửi: trung vị 91 ngày, p95 169 ngày, p99 374 ngày. 56 mã-năm (1%) gửi sau hơn 1 năm (thường
  là tải lên lại muộn) → giữ nguyên ngày muộn, không lấy ngày sớm hơn khi không có bằng chứng.
- 35 mã-năm gửi trước 30 ngày sau 31/12: doanh nghiệp có năm tài chính không kết thúc 31/12 (CTD, CAP, DAC…). Nhãn
  năm của CafeF là năm kết thúc niên độ (CTD FY2024 = niên độ kết thúc 06/2024, gửi 15/10/2024), nên ngày CafeF vẫn
  đúng và quy tắc trễ 30/06 năm sau chỉ làm các mã này "biết" muộn hơn — không rò rỉ. Việc còn lại: thêm cờ
  `non_december_fye` (suy từ ngày gửi rơi vào trong chính năm tài chính, cộng danh sách đã biết CTD/HSG) để báo cáo
  và kiểm thủ công các trường hợp đổi niên độ; không chặn M3.
- Đối chiếu 9 mã-năm đã kiểm tay (FPT 2022–2025, PVS 2024–2025, ACV 2025, BRC 2024–2025): lệch 0 đến +62 ngày,
  **không trường hợp nào sớm hơn** → PASS.
- Quy tắc trễ 30/06 sẽ sớm hơn thực tế với khoảng 2–4% mã-năm (tỷ lệ gửi sau 30/06 ở 2022–2025); mốc 30/04 sai với
  9–15%. Ghi là giới hạn của Development.
- 1.393 mã-năm `CALENDAR_PENDING` (gần hết FY2025 và 31 mã FY2024 gửi sau 31/12/2025): cần lịch phiên 2026 khi mở
  rộng dữ liệu ở giai đoạn 5.

Hệ quả cần ghi trong báo cáo: Development (quyết định 2019–2023) dùng báo cáo năm 2017–2022, phần lớn theo
`LAG_RULE`; Holdout (2024–2025) dùng báo cáo 2022–2024, chủ yếu theo ngày CafeF.

**0.3 VNINDEX.** Pin chuỗi đóng cửa ngày 2016–2025 từ nguồn C8; kiểm lịch phiên khớp lịch giá cổ phiếu. PASS: không
thiếu phiên trong 2019–2025 so với lịch C8.

**0.4 Đếm quy mô tập ứng viên.** Với từng kỳ 2019–2025 và từng phương án Q1/Q2/Q4/Q5: đếm Market pool, Financial
pool, giao, số mã ngân hàng/CK bị loại, số mã chọn. **Chỉ đếm, không đọc giá sau `decision_date`.** Đầu ra:
`feasibility.md` + biểu đồ. PASS: owner/mentor chốt Q1, Q2, Q4, Q5, Q6 dựa trên bảng này.

**0.5 Cơ sở lợi suất.** Chọn 10 sự kiện cổ tức tiền mặt và 10 sự kiện chia tách/thưởng; so `raw_close` và
`adj_close` quanh ngày giao dịch không hưởng quyền. Kết luận giá điều chỉnh có gồm cổ tức tiền mặt hay không. PASS:
ghi kết luận vào Q11.

**Kết quả giai đoạn 0 (25/10/2026)** — `python scripts/m3_stage0.py`, artifact `data/experiments/m3/stage0-*/`
(`feasibility.csv`, `summary.json`), manifest `data/experiments/m3/inputs/manifest.json` (hash bundle v4, indicators,
availability, VNINDEX, lịch phiên, giá C8 4,2 GB, blob M2 K=2). Quy tắc dùng khi đếm = phương án đề xuất Q1/Q2/Q4/Q5/Q10
(A v4, loại mã kém thanh khoản và ngành tài chính; cụm dẫn dắt thị trường = trung vị `mom_126` cao nhất trong mã có
giao dịch; tài chính = trung vị ROE cao nhất, hòa thì D/E thấp hơn).

| Tập ứng viên mỗi tháng | Development (60 tháng) | Holdout (24 tháng) |
|---|---|---|
| Market pool (cụm dẫn dắt, có giao dịch) | min 12 / trung vị 61 / max 266 | 50 / 114,5 / 252 |
| **Candidate Universe (A v4)** | **0 / 8 / 83** | **9 / 19 / 58** |
| Số mã được chọn ceil(30%) | 0 / 3 / 25 | 3 / 6 / 18 |
| Tháng có N < 10 | **38/60** | 3/24 |
| Ngành tài chính bị loại khỏi Market pool | 0 / 6 / 19 | 0 / 2,5 / 45 |
| Nếu giữ mã kém thanh khoản (Q2) | 0 / 13,5 / 134 | 15 / 28,5 / 66 |
| Nếu dùng M2 K=2 (Q1) | 0 / 4,5 / 193; 42/60 tháng N < 10 | 1 / 4 / 235; 22/24 tháng N < 10 |

Lý do loại (tổng mã × tháng): ngoài cụm dẫn dắt thị trường 35.791; kém thanh khoản 32.067; ngoài cụm dẫn dắt tài
chính 4.556; không có nhãn B 1.076; ngành tài chính 692; chưa có BCTC dùng được 66; quá hạn 17. Cụm dẫn dắt tài
chính đổi số nhãn giữa các năm (1 hoặc 2) — xác nhận chọn theo profile, không theo số nhãn.

**Kết luận cho mentor:** với giao của *hai* cụm dẫn dắt, Development có 38/60 tháng dưới 10 ứng viên (trung vị 8 → chỉ
3 mã). M2 K=2 còn nhỏ hơn. Cần chốt lại Q5/Q6 **trước** khi xem lợi suất, ví dụ: (a) điều kiện tài chính đổi thành
"không thuộc cụm yếu nhất" thay vì "thuộc cụm mạnh nhất"; (b) cụm dẫn dắt thị trường = 2 cụm có trung vị `mom_126` cao
nhất khi k ≥ 3; (c) hạ `N_min` xuống 5. Mỗi phương án chạy lại được bằng `m3_stage0.py` (chỉ đếm).

**Cơ sở lợi suất (0.5):** trên 1.499 mã 2019–2025, 984 mã có các bước nhảy nhỏ (0,3–6%) của tỷ lệ adj/raw, trung vị
tổng mỗi mã-năm 4,2% (p90 8,7%) — khớp mức cổ tức tiền mặt → **`adj_close` đã gồm cổ tức tiền mặt** (xác nhận Q11).
4.077 bước lớn (> 6%) là cổ tức cổ phiếu/chia tách. **Lỗi dữ liệu:** 1.030 trường hợp `adj_close` lệch > 3% trong
đúng một phiên rồi quay lại (raw không đổi; ví dụ FPT 03/02/2025 adj 111.338 trong khi 31/01 và 04/02 ≈ 123.000),
135 trường hợp rơi đúng phiên đầu tháng — chính là ngày thực hiện giao dịch. Đề xuất **Q17**: phiên có tỷ lệ adj/raw
lệch > 3% so với phiên trước nhưng phiên sau quay về trong ±0,5% → dùng `raw_close × tỷ lệ của phiên sau` làm giá
điều chỉnh của phiên đó, ghi cờ `ADJ_GLITCH_REPAIRED`; không sửa dữ liệu gốc.

**Giai đoạn 2 (engine) — xong phần lõi:** `src/delta_t1/m3/` gồm `inputs.py`, `universe.py` (PIT, độ cũ, cụm dẫn dắt,
tập ứng viên + lý do loại), `ranking.py` (percentile, điểm gộp, tie rule, ceil 30%), `engine.py` (bán trước mua sau,
BUY_FAILED/SELL_FAILED, `execution_scale`, turnover, giá thiếu → `PRICE_STALE`, mục tiêu dạng hàm cho trường hợp giữ
danh mục). 16 test trong `tests/unit/test_m3_engine.py` PASS. Chưa làm: tái hiện ví dụ 3 kỳ mục 16.1 của plan V5.1
thành fixture, quy tắc trần/sàn và sửa lỗi adj (Q12, Q17) trong hàm giá, `strategies.py`, `benchmark.py`, `run_m3.py`.

**Cập nhật 26/10/2026 — phần không cần mentor đã xong:**

- Engine đủ: `prices.py` (Q17 sửa lỗi adj lệch một phiên, Q12 trần/sàn/khối lượng 0), `strategies.py` (Combined,
  Market-only, Financial-only, Equal-weight, Momentum-only; Q6 giữ danh mục khi tập ứng viên nhỏ), `benchmark.py`
  (VNINDEX), `scripts/run_m3.py` (chỉ cho `--targets-only` khi config chưa `LOCKED`).
- Config `configs/experiments/m3_strategy_v1.json` (status `PROPOSED`, giá trị = các đề xuất).
- 25 test trong `tests/unit/test_m3_engine.py`, gồm tái hiện đúng từng số ví dụ 3 kỳ §16.1 của plan V5.1
  (NAV 100 → 102,5 → 102,218333; `execution_scale` 0,655285; turnover hai chiều 0,75 / 0,739024 / 0,415381).
- Cờ `non_december_fye` (13 mã) trong bảng ngày công bố `availability-4f0f83108e761dae` (ngày dùng được không đổi).
- Phương án Q5/Q6: `scripts/m3_feasibility_variants.py`; câu hỏi gửi mentor: [M3_MENTOR_QUESTIONS.md](M3_MENTOR_QUESTIONS.md).

### Giai đoạn 1 — Khóa chiến lược

**1.1 Nếu Q3 chọn B-PIT:** chạy `scripts/build_financial_pit_clusters.py` (mới) → nhãn B-PIT có version, test
"không bản ghi nào có `usable_from_date` > cutoff được dùng để fit", so ARI với B v4 cho từng năm (chỉ thước đo cụm).
**1.2 Ghi ADR M3** vào `docs/DECISIONS.md`, tạo `m3_strategy_v1.json`, test schema config.
**1.3 Ký khóa:** owner/mentor xác nhận trong chat hoặc issue; ghi hash config vào ADR. Từ đây cấm sửa config cho
Development/Holdout.

### Giai đoạn 2 — Engine và fixture tests (bắt đầu được ngay, song song giai đoạn 0)

Viết `m3/execution.py`, `m3/engine.py`, `m3/ranking.py` với dữ liệu giả. Test bắt buộc:

- `ceil(0,3·N)`: 8→3, 10→3, 11→4, 15→5, 20→6.
- Kỳ đầu 100% tiền mặt; kỳ sau dùng tỷ trọng đã trôi, không reset.
- Diff trên hợp hai tập: mã rời target → SELL toàn bộ; giảm tỷ trọng → SELL một phần; HOLD chỉ khi bằng nhau.
- BUY_FAILED giữ tiền; SELL_FAILED giữ mã; `execution_scale` đúng công thức, ≤ 1, áp cho mọi BUY còn lại.
- NAV: `NAV_e' = Σ w_i·(1+r_i) + cash` khớp tổng giá trị từng dòng (sai số ≤ 1e-9).
- Turnover chỉ tính lệnh khớp.
- PIT: bản ghi tài chính `usable_from_date = t+1` không được dùng tại t.
- Ví dụ 3 kỳ ở mục 16.1 của plan V5.1 tái hiện đúng từng con số.
- Tie rule ổn định khi đổi thứ tự dòng đầu vào.

PASS: toàn bộ test xanh, `python -m compileall -q src tests scripts run.py` sạch.

### Giai đoạn 3 — Chọn danh mục trên dữ liệu thật (chưa tính lợi suất)

**3.1** Chạy `run_m3.py --segment development --targets-only`. Đầu ra: alignment, leading cluster audit,
eligibility audit, criteria, targets cho mọi chiến lược.
**3.2** Kiểm tra (mục 8.1–8.2). Trình owner xem **danh sách mã và quy mô**, không có lợi suất.
PASS: không vi phạm PIT; mọi mã bị loại có lý do; số kỳ `UNIVERSE_TOO_SMALL` được báo.

### Giai đoạn 4 — Backtest lịch sử

**4.1 Development** (60 kỳ): chạy đầy đủ engine cho mọi chiến lược + VNINDEX. Seal artifact (hash vào manifest).
Báo cáo `development-report.md`: NAV, CAGR, volatility, MDD, turnover, % tiền mặt, số lệnh thất bại; **không Sharpe**.
**4.2 Review Development:** chỉ được sửa **lỗi kỹ thuật** (bug có test chứng minh), không sửa quy tắc. Mọi sửa → run
mới, giữ run cũ.
**4.3 Holdout** (24 kỳ): cùng config hash, cùng code tag. Seal. `holdout-report.md`.
**4.4 So sánh theo đoạn:** bảng riêng Development và Holdout; không gộp thành một con số 2019–2025 làm kết luận chính.
PASS: `validation.json` đạt mục 8; kết quả bất lợi vẫn giữ và báo cáo.

### Giai đoạn 5 — Final Evaluation (dữ liệu 2026)

**5.1 Mở rộng dữ liệu:** giá ngày, VNINDEX, BCTC năm 2025 (công bố 2026) + ngày công bố, theo đúng pipeline và
policy hiện hành; tạo version mới, không ghi đè.
**5.2 Sinh snapshot A tháng 2026** bằng mô hình đã đóng băng: cùng đặc trưng, cùng quy trình theo từng snapshot như
A v4 (không chọn lại k, ngưỡng thanh khoản, thuật toán). Nhãn B năm tài chính 2025 lấy từ mô hình B đã khóa.
**5.3 Audit sẵn sàng:** đủ giá/VNINDEX/ngày công bố cho mọi kỳ trong cửa sổ; xác nhận không ai đã xem lợi suất
chiến lược trên 2026. Ghi `FINAL_EVALUATION_READY`.
**5.4 Khóa cửa sổ** (Q16), chạy một lần, seal, rồi mới tính Sharpe (kèm khoảng tin cậy bootstrap theo khối tháng).
PASS: một run duy nhất được báo là kết quả cuối; nếu phải chạy lại vì lỗi kỹ thuật, báo cả hai.

### Giai đoạn 6 — Dashboard M3-B (trên web hiện có)

Không dựng Streamlit hay dashboard thứ ba. Mở rộng `web/backend` + `web/frontend`:

1. **Gói dữ liệu:** `scripts/build_m3_bundle.py` đọc artifact đã seal → `data/web/m3-v1/m3.sqlite` + manifest hash.
2. **API chỉ đọc:** `/api/v2/m3/runs`, `/api/v2/m3/{segment}/nav`, `/holdings?date=`, `/trades?date=`,
   `/eligibility?date=&ticker=`, `/metrics`.
3. **Trang "Danh mục" (`/portfolio`):** NAV chiến lược vs VNINDEX vs đối chứng theo đoạn; bảng chỉ số; dải thời gian
   chọn kỳ → danh mục mục tiêu, lệnh, mã thất bại, tiền mặt.
4. **Trang cổ phiếu:** thêm "Lịch sử trong chiến lược" (kỳ nào được chọn, vì sao bị loại).
5. **Nhãn trung thực:** mọi trang ghi đoạn (Development/Holdout/Final), giả định chi phí 0, cơ sở lợi suất, câu
   "không phải khuyến nghị đầu tư".
PASS: API tests, `npm run build`, ảnh chụp 1440/390 ở cả hai giao diện, không lỗi JS.

### Giai đoạn 7 — Báo cáo và tái lập M3-C

Notebook trong `notebooks/m3/` (chỉ gọi hàm `src/`):

1. `01_du_lieu_va_pit.ipynb` — manifest, độ phủ ngày công bố, ví dụ căn PIT 3 kỳ.
2. `02_chon_danh_muc.ipynb` — cụm dẫn dắt, tập ứng viên, xếp hạng một kỳ cụ thể từ đầu đến cuối.
3. `03_backtest_va_benchmark.ipynb` — đọc artifact đã seal, vẽ NAV, kiểm lại NAV bằng tính tay một kỳ.
4. `04_danh_gia_cuoi.ipynb` — Final Evaluation, Sharpe kèm khoảng tin cậy.

`docs/M3_RUNBOOK.md`: lệnh chạy lại từng giai đoạn, thời gian dự kiến, các điểm phải dừng.
`artifacts/reports/m3-v1/report.md`: báo cáo kỹ thuật (phương pháp, quyết định Q1–Q16, kết quả từng đoạn, giới hạn).
PASS: một người khác chạy runbook trên máy sạch ra đúng hash artifact.

---

## 8. Kiểm tra bắt buộc

### 8.1. PIT và dữ liệu

- Mọi bản ghi tài chính dùng tại t có `usable_from_date <= t`; test cố tình chèn bản ghi tương lai phải fail.
- Mọi đặc trưng thị trường tại t tính từ dữ liệu ≤ t (kiểm lại ngẫu nhiên 20 mã × 5 kỳ từ giá gốc).
- Không có giá forward-fill trong chuỗi lợi suất; `PRICE_STALE` được đếm và báo.
- `execution_date > decision_date` cho mọi kỳ.

### 8.2. Tập ứng viên

- `combined = market_eligible ∧ financial_eligible` cho mọi dòng audit.
- Mỗi mã bị loại có đúng một lý do chính trong: `MARKET_STATE_MISSING`, `MARKET_ILLIQUID`,
  `MARKET_NOT_IN_LEADING_CLUSTER`, `FINANCIAL_SECTOR_NO_B`, `FINANCIAL_NOT_AVAILABLE`, `FINANCIAL_STALE`,
  `FINANCIAL_NOT_IN_LEADING_CLUSTER`, `FINANCIAL_CRITERIA_MISSING`, `ID_MAPPING_FAILED`, `CLUSTER_PROFILE_AMBIGUOUS`.

### 8.3. Engine

- Tổng tỷ trọng + tiền = 1 (±1e-9) sau mỗi giao dịch và cuối mỗi kỳ.
- Không có tỷ trọng âm, không có tiền âm.
- `execution_scale ∈ (0, 1]`, chỉ khác 1 khi có SELL_FAILED.
- NAV tái lập từ ledger + giá khớp NAV engine.
- Development và Holdout dùng cùng config hash và cùng commit.

### 8.4. Báo cáo

- Không có Sharpe/Sortino/IR trong Development/Holdout.
- Mỗi bảng ghi đoạn, cơ sở lợi suất, giả định chi phí.
- Kết quả của mọi chiến lược đã chạy đều có mặt, kể cả khi kém hơn VNINDEX.

---

## 9. Chỉ số báo cáo

| Lớp | Development / Holdout | Final Evaluation |
|---|---|---|
| Lợi suất | Tổng lợi suất, CAGR, lợi suất tháng trung bình, tỷ lệ tháng thắng VNINDEX | như bên trái |
| Rủi ro | Volatility năm hóa, MDD, tháng tệ nhất | như bên trái |
| Rủi ro điều chỉnh | — | Sharpe (rf = 0, ghi rõ), khoảng tin cậy bootstrap |
| Vận hành | Turnover, số lệnh thất bại, % tiền mặt trung bình, số mã nắm giữ trung bình, số kỳ `UNIVERSE_TOO_SMALL` | như bên trái |
| Kịch bản chi phí | Lợi suất ròng với 0,15% và 0,30% mỗi chiều (chỉ báo cáo, không dùng chọn quy tắc) | như bên trái |

---

## 10. Thứ tự thực hiện và điểm chờ duyệt

```text
Tuần 1   Giai đoạn 0 (0.1–0.5)          ║  Giai đoạn 2 (engine + test, song song)
         ── DỪNG: owner/mentor chốt Q1–Q16 dựa trên feasibility.md ──
Tuần 2   Giai đoạn 1 (B-PIT nếu chọn, ADR, config hash)
         Giai đoạn 3 (targets-only Development) ── DỪNG: owner xem danh sách mã ──
Tuần 3   Giai đoạn 4 (Development → seal → Holdout → seal)
Tuần 4   Giai đoạn 6 (dashboard) ║ Giai đoạn 5.1–5.3 (mở rộng dữ liệu 2026)
         ── DỪNG: owner xác nhận FINAL_EVALUATION_READY và cửa sổ ──
Tuần 5   5.4 Final Evaluation → Giai đoạn 7 (notebook, runbook, báo cáo)
```

Ước lượng tuần là tham khảo; điểm DỪNG là bắt buộc.

---

## 11. Rủi ro chính

| Rủi ro | Dấu hiệu | Xử lý |
|---|---|---|
| Tập ứng viên quá nhỏ | Nhiều kỳ `N < 10` ở 0.4 | Chốt lại Q2/Q4/Q5 **trước** khi xem lợi suất; không chỉnh sau. |
| B kém ổn định (ARI ≈ 0,5) | Cụm dẫn dắt tài chính đổi thành phần mạnh giữa các năm | Báo cáo độ trùng thành viên cụm dẫn dắt năm-năm; cân nhắc Financial-only làm đối chứng bắt buộc. |
| Thiếu ngày công bố một phần | Độ phủ 0.2 < ngưỡng | Fail-closed theo mã-năm; báo tỷ lệ bị loại; không suy ngày. |
| Cơ sở lợi suất lệch VNINDEX | 0.5 cho thấy có cổ tức tiền mặt | Ghi "proxy tổng lợi suất" và chênh lệch ước tính (tỷ suất cổ tức thị trường) cạnh mọi so sánh. |
| Holdout không sạch về mô hình | Q15 | Ghi rõ; Final Evaluation là kết luận chính. |
| Final Evaluation ngắn | < 12 tháng | Báo khoảng tin cậy; không tuyên bố ý nghĩa thống kê. |
| Rò rỉ qua lựa chọn của người | Có người xem lợi suất trước khi khóa | Artifact lợi suất chỉ sinh sau 1.3; log ai chạy, lúc nào. |

---

## 12. Không làm

- Không chọn k, mô hình, cụm dẫn dắt, tiêu chí, trọng số hoặc ngưỡng bằng lợi suất/Sharpe.
- Không fit lại A/B trong M3 (trừ B-PIT nếu Q3 duyệt, như một version riêng).
- Không dùng mô hình C (gộp đặc trưng) làm tín hiệu chiến lược.
- Không gọi phân cụm độc lập hằng tháng là Dynamic Clustering.
- Không forward-fill giá, không biến thiếu thành 0, không trộn raw/adjusted.
- Không sửa artifact đã seal; không xóa run bất lợi.
- Không dựng dashboard công nghệ khác song song với web hiện có.

---

## 13. Khác biệt so với plan V5.1 của nhóm

| Plan V5.1 | Plan này | Lý do |
|---|---|---|
| Input thị trường = bàn giao M2 K=2 | A v4 (k=3), M2 K=2 làm đối chứng (Q1) | K=2 cho cụm dẫn dắt ~20 mã/tháng. |
| Financial handoff "chờ upstream" | B v4 có sẵn + ngày công bố đã có; thêm phương án B-PIT (Q3) | Phản ánh trạng thái thật; xử lý rò rỉ tâm cụm. |
| MC/FC/ranking để trống | Có phương án đề xuất cụ thể (Q7–Q9), vẫn chờ mentor ký | Để mentor duyệt một phương án thay vì tự nghĩ từ đầu. |
| Không xử lý tập ứng viên nhỏ | `N_min` + đo khả thi trước (Q6, 0.4) | Tránh danh mục 1–2 mã. |
| Không nói về ngân hàng/CK | Q4 | B không có nhãn cho nhóm này. |
| Chỉ VNINDEX | VNINDEX + equal-weight + momentum-only làm đối chứng (Q14) | Theo `EVALUATION_AND_BACKTEST.md`. |
| Dashboard Streamlit / HTML thuần | Mở rộng web Next.js + FastAPI đã deploy | Tránh ba bộ công nghệ song song. |
| ~9.000 dòng, nhiều ví dụ lặp | Bảng quyết định + spec + test | Dễ duyệt; ví dụ 3 kỳ của V5.1 dùng lại làm fixture test. |
