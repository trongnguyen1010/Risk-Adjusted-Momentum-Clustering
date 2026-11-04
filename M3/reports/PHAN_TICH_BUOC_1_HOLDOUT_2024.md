# Phân tích Bước 1 và giao dịch — đợt giảm Holdout 2024

## 1. Phạm vi và cách đọc

Phân tích đợt giảm từ **2024-05-02 đến 2024-11-01**, tức đỉnh–đáy max drawdown của Combined đã quan sát. NAV giảm từ 1,122223 xuống 0,827391, tương ứng -26,27%. VNINDEX trong đúng khoảng này có lợi suất 3,17%. Đây là cửa sổ được chọn sau khi xem kết quả để giải thích tổn thất, không phải một mẫu đánh giá mới.

Đóng góp từng mã = giá trị vị thế sau giao dịch × biến động mark đến kỳ kế tiếp. Cộng PnL theo đơn vị vốn đầu=1 rồi chia NAV tại đầu cửa sổ để ra điểm phần trăm của đợt giảm; không cộng trực tiếp các tỷ suất tháng. Tái sử dụng revalue/rebalance chính thức và đối chiếu toàn bộ Holdout với run sealed.

## Nhận định chính

**Bước 1 là phần đáng chú ý chính trong đợt giảm này:** trên cùng đường vốn thực tế, phần phân bổ theo goal đóng góp -23,70 điểm phần trăm, còn lệch phân bổ sau giao dịch đóng góp thêm -2,57 điểm phần trăm vào mức giảm -26,27%. Vì phần goal đã âm lớn, tổn thất không thể giải thích chỉ bằng lệnh thất bại. Đây là phép phân rã PnL, không phải tỷ lệ nguyên nhân hay lợi suất của một backtest giả định đã fill mọi lệnh.

**Rủi ro tập trung xuất hiện ngay trong target:** kỳ đầu cửa sổ chỉ chọn 4 mã từ 12 ứng viên, goal mỗi mã 25,00%. Kỳ 2024-07-01 → 2024-08-01 giữ 6 mã, giảm -15,24%, trong khi VNINDEX giảm 2,20%; lệch thực thi kỳ đó chỉ 0,00 điểm phần trăm. Như vậy kỳ lỗ nặng nhất phát sinh ngay cả khi thực giữ khớp goal. N_min áp dụng cho số ứng viên, không bảo đảm danh mục thực giữ ít nhất mười mã.

**Tổn thất tập trung vào CID, CAG, VTK:** ba mã này đóng góp lần lượt -7,10, -5,79, -4,33 điểm phần trăm, tương ứng 65,51% mức lỗ ròng của cửa sổ. Điều này gắn phần giảm lớn với các vị thế cụ thể, chưa chứng minh một filter riêng lẻ là sai.

**Thực thi vẫn có ảnh hưởng riêng:** BUY_FAILED làm bỏ lỡ một số mức tăng; SELL_FAILED giữ vị thế cần giảm. Riêng CID ở kỳ 01/10 → 01/11 có tỷ trọng vượt goal do bán thất bại và tiếp tục giảm giá. Một số BUY_FAILED lại giúp tránh lỗ, nên cần cộng cả tác động có lợi và bất lợi thay vì coi mọi lệnh thất bại đều gây thiệt hại.

**Có mã tăng bị loại ở cả gate cụm và xếp hạng:** CDR ở kỳ 01/07 → 01/08 thuộc Candidate Universe nhưng xếp hạng 9, ngoài top 6, rồi tăng 97,98%. Kỳ sau, mã này được giữ với tỷ trọng 9,09% và giảm 30,10%. Trường hợp này minh họa việc vào sau một đợt tăng rồi gặp đảo chiều, chưa chứng minh đây là quy luật chung của chiến lược. Đây là minh họa sau khi biết kết quả, không chứng minh có thể biết trước để chọn hoặc rằng nên sửa rule sau Holdout. Chưa đủ bằng chứng để quy riêng nguyên nhân cho Market filter, Financial filter hay cách chấm điểm.

## 2. Những mã đóng góp tổn thất lớn nhất

| Mã | PnL vốn chuẩn hóa | Đóng góp (điểm phần trăm) | Tỷ trọng thực giữ lớn nhất | Số khoảng quan sát |
|---|---:|---:|---:|---:|
| CID | -0,079641 | -7,10 | 16,67% | 4 |
| CAG | -0,064922 | -5,79 | 25,00% | 1 |
| VTK | -0,048595 | -4,33 | 16,67% | 3 |
| CDR | -0,025265 | -2,25 | 9,09% | 1 |
| CKA | -0,025186 | -2,24 | 9,09% | 2 |
| DRI | -0,013200 | -1,18 | 11,11% | 1 |
| CNT | -0,012114 | -1,08 | 9,09% | 1 |
| NTP | -0,011912 | -1,06 | 9,09% | 2 |
| SAS | -0,009098 | -0,81 | 9,09% | 2 |
| ACV | -0,008717 | -0,78 | 16,67% | 1 |
| KSV | -0,006988 | -0,62 | 9,09% | 2 |
| PHN | -0,006626 | -0,59 | 9,09% | 1 |

Đóng góp dương của các mã khác có thể bù một phần tổn thất; tổng đóng góp mọi mã khớp chênh lệch NAV. Số khoảng không phải số lần mua. Tỷ trọng lớn nhất là tỷ trọng thực tế sau giao dịch trong cửa sổ.

## 3. Tập ứng viên và độ tập trung danh mục theo kỳ

| Decision | Khoảng nắm giữ | Ứng viên | N_selected | Mã thực giữ | Goal lớn nhất | Thực giữ lớn nhất | Cash | Return Combined | Return VNINDEX |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 2024-04-26 | 2024-05-02 → 2024-06-03 | 12 | 4 | 3 | 25,00% | VFG: 25,00% | 25,00% | -5,39% | 5,23% |
| 2024-05-31 | 2024-06-03 → 2024-07-01 | 27 | 9 | 8 | 11,11% | VGR: 11,11% | 11,11% | 2,59% | -1,99% |
| 2024-06-28 | 2024-07-01 → 2024-08-01 | 20 | 6 | 6 | 16,67% | VTK: 16,67% | 0,00% | -15,24% | -2,20% |
| 2024-07-31 | 2024-08-01 → 2024-09-04 | 35 | 11 | 9 | 9,09% | SAS: 9,09% | 18,18% | -2,79% | 3,98% |
| 2024-08-30 | 2024-09-04 → 2024-10-01 | 34 | 11 | 10 | 9,09% | VTK: 9,09% | 9,09% | -1,56% | 1,29% |
| 2024-09-30 | 2024-10-01 → 2024-11-01 | 43 | 13 | 14 | 7,69% | CID: 11,97% | 0,00% | -6,35% | -2,89% |

Các gate ở Bước 1 thu hẹp tập mã như sau; đây là số đếm theo từng decision, không phải số mã duy nhất:

| Decision | Market Eligible Pool | Giao Market/Financial trước FC missing | Bị loại vì thiếu toàn bộ FC | Candidate cuối | N_selected |
|---|---:|---:|---:|---:|---:|
| 2024-04-26 | 145 | 12 | 0 | 12 | 4 |
| 2024-05-31 | 88 | 27 | 0 | 27 | 9 |
| 2024-06-28 | 52 | 20 | 0 | 20 | 6 |
| 2024-07-31 | 138 | 35 | 0 | 35 | 11 |
| 2024-08-30 | 101 | 34 | 0 | 34 | 11 |
| 2024-09-30 | 123 | 43 | 0 | 43 | 13 |

Số mã giảm qua gate mô tả cơ chế thu hẹp tập chọn; chưa đo tác động nhân quả của việc nới/bỏ gate. Chi tiết lý do Financial trong Market pool được lưu theo kỳ trong evidence.

## 4. Tách goal ở Bước 1 và sai lệch sau thực thi

Đây là phép phân rã tại từng kỳ trên **cùng NAV thực tế đầu kỳ**, không phải backtest một chiến lược khác. Phần goal = NAV × goal_weight × return của mã; phần sai lệch = NAV × (actual_weight − goal_weight) × return. Hai phần cộng lại bằng PnL thực tế khi đủ mark. Cash có return 0 theo contract. Mark được carry đúng policy cho vị thế cũ PRICE_STALE; thiếu giá của mã chưa nắm giữ không tự thay bằng zero.

- Đóng góp theo goal trên cùng vốn thực tế: **-23,70 điểm phần trăm**.
- Đóng góp do sai lệch phân bổ sau giao dịch: **-2,57 điểm phần trăm**.
- Tổng thực tế: **-26,27%**.
- Số quan sát thiếu return để phân rã goal: **0**.

Các số đóng góp trên quy về một mẫu số chung, không phải lợi suất cộng dồn của danh mục giả định đã fill toàn bộ target. Dấu dương ở phần sai lệch nghĩa là thực thi giúp kết quả ít lỗ hơn so với phần goal được quy đổi trên cùng đường vốn thực tế; dấu âm nghĩa là làm kết quả xấu hơn.

| Trạng thái ledger | Đóng góp của sai lệch so với goal (điểm phần trăm) |
|---|---:|
| BUY_FAILED | -1,36 |
| EXECUTED | 0,00 |
| SCALED | 0,16 |
| SELL_FAILED | -1,38 |

| Ngày | Mã | Trạng thái | Goal | Thực giữ | Dữ kiện chặn/giảm lệnh |
|---|---|---|---:|---:|---|
| 2024-05-02 | HGM | BUY_FAILED | 25,00% | 0,00% | raw_close>=ceiling |
| 2024-06-03 | FOX | BUY_FAILED | 11,11% | 0,00% | raw_close>=ceiling |
| 2024-08-01 | CMF | BUY_FAILED | 9,09% | 0,00% | volume=0 |
| 2024-08-01 | FHS | BUY_FAILED | 9,09% | 0,00% | volume=0 |
| 2024-09-04 | NAS | BUY_FAILED | 9,09% | 0,00% | volume=0 |
| 2024-10-01 | CID | SELL_FAILED | 7,69% | 11,97% | volume=0 |
| 2024-10-01 | PTX | SELL_FAILED | 0,00% | 9,23% | Thiếu current_price; Thiếu volume |
| 2024-10-01 | ADP | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |
| 2024-10-01 | DTP | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |
| 2024-10-01 | FOX | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |
| 2024-10-01 | IMP | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |
| 2024-10-01 | LHC | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |
| 2024-10-01 | MCH | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |
| 2024-10-01 | WCS | SCALED | 7,69% | 5,76% | Giảm đồng tỷ lệ do cash không đủ |

## 5. Mã tăng nhưng không nằm trong target

Phạm vi rà soát là các mã không ILLIQUID tại decision, có đủ giá điều chỉnh ở hai đầu khoảng và BUY executable tại đầu khoảng theo Q12. Bảng dưới chọn các quan sát return dương cao nhất **sau khi đã biết kết quả**. Ticker có thể vẫn được giữ từ kỳ trước dù không có trong target; xem cột thực giữ cũ. Lý do là lý do chính trong audit, các gate có thể cùng loại một mã.

| Mã | Khoảng | Return quan sát | Lý do không vào target | Rank nếu có | Thực giữ cũ |
|---|---|---:|---|---:|---|
| CTP | 2024-08-01 → 2024-09-04 | 209,76% | FINANCIAL_NOT_IN_ALLOWED_CLUSTER | — | Không |
| MVN | 2024-06-03 → 2024-07-01 | 142,86% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| API | 2024-05-02 → 2024-06-03 | 126,83% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| ALV | 2024-05-02 → 2024-06-03 | 122,45% | FINANCIAL_MODEL_BEFORE_CUTOFF | — | Không |
| CDR | 2024-07-01 → 2024-08-01 | 97,98% | RANK_BELOW_TOP_SHARE | 9 | Không |
| PIV | 2024-05-02 → 2024-06-03 | 94,44% | FINANCIAL_STATE_MISSING | — | Không |
| PGT | 2024-10-01 → 2024-11-01 | 87,10% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| FCS | 2024-06-03 → 2024-07-01 | 83,87% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| PSB | 2024-06-03 → 2024-07-01 | 83,02% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| APP | 2024-05-02 → 2024-06-03 | 76,19% | FINANCIAL_MODEL_BEFORE_CUTOFF | — | Không |
| MCO | 2024-09-04 → 2024-10-01 | 75,00% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| VLG | 2024-06-03 → 2024-07-01 | 73,77% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| QCG | 2024-10-01 → 2024-11-01 | 70,87% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| VNA | 2024-06-03 → 2024-07-01 | 68,54% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |
| HVN | 2024-05-02 → 2024-06-03 | 68,21% | MARKET_NOT_IN_LEADING_CLUSTER | — | Không |

| Lý do chính | Số mã/kỳ return dương không có trong target |
|---|---:|
| MARKET_NOT_IN_LEADING_CLUSTER | 1601 |
| FINANCIAL_NOT_IN_ALLOWED_CLUSTER | 72 |
| FINANCIAL_MODEL_BEFORE_CUTOFF | 56 |
| RANK_BELOW_TOP_SHARE | 48 |
| FINANCIAL_STATE_MISSING | 23 |
| FINANCIAL_SECTOR_NO_B | 8 |
| FINANCIAL_NOT_AVAILABLE | 4 |
| FINANCIAL_STALE | 3 |

Đây là số quan sát mã/kỳ, không phải số mã duy nhất. Có mã tăng bị loại không tự chứng minh bộ lọc sai hoặc rằng có thể biết trước để mua. Chưa phân rã theo tỷ trọng VNINDEX, chưa kiểm định tác dụng nhân quả của từng filter. Return quan sát vẫn có giới hạn giá điều chỉnh của nhà cung cấp; không dùng bảng này để tune rule sau Holdout.

## 6. Evidence và giới hạn

- Run nguồn: `20261104T133507Z-5557288c`, code `c9c1f5f0c88f2dbb3ebbb50effa47003b24b66cf`.
- Config SHA256: `b5c47ac458cca35e29e99f1cd8cde2827778fbffd8bb2fccf942a6cc9a42e72d`.
- [Phân rã từng kỳ/mã và coverage](../reproduction/20261104T154902950793Z-holdout-diagnosis/analysis.json).
- [Kiểm tra đối chiếu](../reproduction/20261104T154902950793Z-holdout-diagnosis/verification.json).
- Dùng evidence input hash có kiểm tra fingerprint từ phiên M3-C đã chạy; không scan lại C8 không cần thiết.
- Phân tích chỉ giải thích đợt giảm 2024, không giải thích toàn bộ chênh lệch với VNINDEX trong Holdout.
- Giới hạn vendor-adjusted/price index, mark stale, phí/slippage 0 và vintage tài chính tiếp tục áp dụng.
- Không thay config, strategy, target, input hoặc run/seal canonical. Không tạo official backtest mới.
