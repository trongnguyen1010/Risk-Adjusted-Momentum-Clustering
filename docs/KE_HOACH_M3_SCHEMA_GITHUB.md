# KẾ HOẠCH TỔNG THỂ M3 — KẾT HỢP DỮ LIỆU THỊ TRƯỜNG VÀ TÀI CHÍNH, BACKTEST, DASHBOARD VÀ BÁO CÁO TÁI LẬP

**Dự án:** DELTA — Phân cụm động lượng điều chỉnh theo rủi ro cho cổ phiếu Việt Nam  
**Kho mã nguồn:** `trongnguyen1010/Risk-Adjusted-Momentum-Clustering`  
**Nhánh M3 tham chiếu:** `feature/indicators-v1`  
**Nhánh M2/handoff tham chiếu:** `m2-clustering-experiment`  
**Phiên bản kế hoạch:** cập nhật output contract + input contract theo GitHub và các quyết định của chủ dự án ngày 26/10/2026  
**Trạng thái:** KẾ HOẠCH CHI TIẾT — ENGINE/TARGETS-ONLY ĐÃ CÓ; CHƯA CHẠY OFFICIAL M3 BACKTEST CÓ RETURN  
**Phạm vi:** M3-A Danh mục và backtest + M3-B Dashboard + M3-C Báo cáo và khả năng tái lập

## CẬP NHẬT QUYẾT ĐỊNH M3-A

Các decision M3-A đã được owner phê duyệt có ưu tiên cao hơn các proposal hoặc mô tả cũ trong tài liệu.

Các điểm chính hiện hành:

- A v4 là Market model chính thức cho M2/M3; B v4 là Financial model hiện hành; M2 K=2 giữ làm legacy/research control.
- Market và Financial là hai hệ clustering độc lập; M3 chỉ kết hợp ở tầng strategy/portfolio.
- Combined Candidate Universe sử dụng `Market Eligible Pool ∩ Financial Eligible Pool`.
- Leading/allowed cluster phải xác định từ profile/semantic theo rule đã khóa; không suy trực tiếp từ numeric label.
- Financial data phải tuân theo PIT tại `decision_date`; dữ liệu chưa usable không được sử dụng.
- Execution sử dụng phiên giao dịch hợp lệ kế tiếp; BUY/SELL failure và scaling tuân theo execution contract đã khóa.
- Development = 60 snapshots `2019-01-31 → 2023-12-29`; Holdout = 24 snapshots `2024-01-31 → 2025-12-31`.
- VNINDEX là benchmark chính thức.
- Final Evaluation chỉ dùng dữ liệu sau `2025-12-31` và exact window phải được khóa trước khi xem Final performance.

Các proposal chưa có owner/mentor decision vẫn giữ trạng thái `OPEN/PROPOSED` và không được tự coi là methodology đã khóa.

Chi tiết decision status xem **Mục 38 — Trạng thái hiện tại**; methodology chi tiết xem các mục tương ứng phía dưới.

## CẬP NHẬT OUTPUT CONTRACT M3-A

M3-A sử dụng bộ output theo kiến trúc GitHub hiện hành làm **canonical output contract**.

Mỗi run được lưu tại:

```text
data/experiments/m3/<segment>/<run_id>/
```

Canonical outputs gồm:

```text
targets_<strategy>.csv
trade_ledger_<strategy>.csv
holdings_<strategy>.csv
turnover_<strategy>.csv
nav_<strategy>.csv
benchmark_vnindex.csv
metrics.json
manifest.json
```

Các phép PIT, eligibility, ranking, current-vs-target, valuation và rebalance vẫn được thực hiện trong engine nhưng không nhất thiết persist thành file riêng.

Các extension/semantics hiện hành gồm:

- `holdings_<strategy>.csv` sử dụng schema theo GitHub hiện hành:

```text
date
ticker
weight
```

- turnover sử dụng:

```text
(executed BUY + executed SELL)
/
(2 × pre_trade_NAV)
```

với trạng thái:

```text
OWNER DECISION — PENDING GIT SYNC
```

- manifest.json phải tuân theo schema GitHub hiện hành và ghi đúng metadata của run.
- M3-B và M3-C chỉ được dựa vào canonical/sealed outputs.

Schema chi tiết của tám output xem **Mục 16 — Canonical Output Schema**; execution semantics xem **Mục 10**.


## CẬP NHẬT INPUT CONTRACT M3-A

Main M3-A runtime sử dụng sáu logical input artifact theo implementation GitHub hiện hành:

```text
1. data/web/delta-intelligence-v4/terminal.sqlite

2. data/financial/indicators_v1/results/
   indicators-2c4a24e3830d325f/indicators.sqlite

3. data/financial/disclosure_dates_v1/
   availability-4f0f83108e761dae/availability.csv

4. artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/
   prices_daily.jsonl

5. artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/
   trading_calendar.jsonl

6. artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/
   benchmark_daily.jsonl
```

Vai trò tổng quát:

```text
terminal.sqlite
→ Market/Financial states + market prices

indicators.sqlite
→ Financial indicators/sector metadata

availability.csv
→ Financial PIT usable_from_date

prices_daily.jsonl
→ price-limit/tradability information

trading_calendar.jsonl
→ valid trading sessions

benchmark_daily.jsonl
→ VNINDEX benchmark
```

Các M2 handoff CSV cũ chỉ còn là reference/research control khi strategy/config yêu cầu; chúng không phải main runtime prerequisite của M3-A.

Runtime config không phải dataset input nhưng phải được version/hash và pin trong `manifest.json` trước official run.

Schema, field requirements, PIT semantics và coverage requirements chi tiết xem **Mục 5 — Khung dữ liệu chung**. Điều kiện để M3-A bắt đầu xem **Mục 6**.

---

# 0. CÁCH ĐỌC TÀI LIỆU

Tài liệu dùng các trạng thái sau:

- **ĐÃ KHÓA / KẾ THỪA:** đã có căn cứ từ M1, M2, kho mã nguồn hoặc quyết định trước đó; không được tự đổi.
- **ĐÃ ĐƯỢC CHỦ DỰ ÁN DUYỆT:** quyết định đã được chốt cho M3.
- **ĐỀ XUẤT:** phương án triển khai hợp lý nhưng chưa được coi là quyết định cuối.
- **CẦN QUYẾT ĐỊNH CỦA CHỦ DỰ ÁN / MENTOR:** chưa đủ căn cứ để tự chọn; nhiệm vụ liên quan phải dừng nếu quyết định này ảnh hưởng trực tiếp đến kết quả.

Mỗi nhiệm vụ đều có:

1. Mục tiêu;
2. Trạng thái / căn cứ quyết định;
3. Đầu vào bắt buộc;
4. Đầu ra mong đợi;
5. Công cụ / tệp liên quan;
6. Các bước thực hiện theo thứ tự;
7. Kiểm tra / xác nhận;
8. Điều kiện chuyển bước;
9. Bàn giao sang nhiệm vụ tiếp theo.

Không được bỏ qua điều kiện chuyển bước chỉ vì mã nguồn “vẫn chạy được”.

---

# 1. TÀI LIỆU NGUỒN BẮT BUỘC

M3 ưu tiên các tài liệu và decision được cập nhật gần nhất trên nhánh M3 hiện hành.

Khi các tài liệu có nội dung khác nhau, áp dụng thứ tự ưu tiên:

```text
Owner decision / DECISIONS.md
        ↓
M3_PLAN.md
        ↓
M3_MENTOR_QUESTIONS.md
        ↓
config đã LOCKED
        ↓
tài liệu kế hoạch tổng hợp này
```

Tài liệu kế hoạch tổng hợp này không được tự ghi đè owner decision hoặc M3 decision mới hơn trên Git.

## 1.1. `docs/DECISIONS.md`

Đây là nơi ghi các quyết định đã được owner phê duyệt.

Các decision M3 mới hơn phải được ưu tiên hơn proposal cũ trong plan.

Hiện đã có:

```text
D-DIR-01 — 26/10/2026
```

Theo đó:

- A v4 là Market clustering model chính thức cho M2/M3;
- B v4 là Financial clustering model hiện hành;
- M2 K=2 được giữ làm legacy/research control;
- historical artifacts cũ không bị xóa;
- các giới hạn của model phải được báo cáo minh bạch.

Một nội dung đã được ghi thành owner decision trong `DECISIONS.md` không được tiếp tục trình bày như một câu hỏi chưa chốt trong kế hoạch M3.

## 1.2. `docs/M3_PLAN.md`

Đây là tài liệu M3 chính để xác định:

- phạm vi M3-A, M3-B, M3-C;
- Development / Holdout / Final Evaluation;
- strategy definitions;
- Candidate Universe;
- portfolio construction;
- execution assumptions;
- benchmark;
- decision queue Q1–Q17;
- trình tự triển khai M3.

Các nội dung trong `M3_PLAN.md` có trạng thái proposal/open không được tự coi là đã khóa.

## 1.3. `docs/M3_MENTOR_QUESTIONS.md`

Tài liệu này chứa các câu hỏi còn cần mentor/owner quyết định trước official backtest có return.

Phải phân biệt:

```text
Proposal
≠
Approved decision
```

Khi một câu được chốt:

```text
Mentor/Owner answer
        ↓
DECISIONS.md / ADR
        ↓
config
        ↓
status = LOCKED
```

Không được lấy phương án đề xuất trong file này làm methodology chính thức khi chưa có decision tương ứng.

## 1.4. `configs/experiments/m3_strategy_v1.json`

Đây là config thực thi của strategy M3.

Config phải phản ánh các decision đã được khóa.

Nếu:

```text
status = PROPOSED
```

thì không được chạy official backtest có return.

Chỉ khi:

```text
status = LOCKED
```

và config hash đã được pin thì mới được sử dụng cho official Development/Holdout run.

## 1.5. Tài liệu M3-B hiện hành

M3-B phải bám kiến trúc product/web hiện hành của repository:

```text
web/frontend
→ Next.js

web/backend
→ FastAPI
```

M3-B là read-only product/presentation layer.

Không dùng tài liệu hoặc implementation dashboard legacy để ghi đè kiến trúc M3-B hiện hành.

## 1.6. Nguyên tắc precedence

Nếu phát hiện khác biệt giữa:

```text
kế hoạch tổng hợp hiện tại
vs
Git M3 mới hơn
```

thì:

1. xác định trạng thái của nội dung trên Git;
2. nếu là owner-approved decision → cập nhật kế hoạch theo decision đó;
3. nếu chỉ là proposal → giữ trạng thái OPEN/PROPOSED;
4. không tự biến proposal thành decision;
5. không dùng tài liệu Git cũ hơn để ghi đè decision M3 mới hơn.

---

# 2. KIẾN TRÚC NGHIÊN CỨU M3

## 2.1. Hai hệ phân cụm độc lập

```text
DỮ LIỆU THỊ TRƯỜNG
    ↓
Tiền xử lý dữ liệu thị trường
    ↓
Phân cụm thị trường
    ↓
K_market
    ↓
Nhãn phân cụm thị trường
```

và:

```text
DỮ LIỆU TÀI CHÍNH
    ↓
Tiền xử lý dữ liệu tài chính
    ↓
Phân cụm tài chính
    ↓
K_financial
    ↓
Nhãn phân cụm tài chính
```

M3 không được làm:

```text
Đặc trưng thị trường thô
+
Đặc trưng tài chính thô
→ gộp thành một bộ đặc trưng
→ phân cụm lại
→ chọn một K chung
```

## 2.2. Phần kết hợp nằm ở bước ra quyết định danh mục

```text
Nhãn phân cụm thị trường tại ngày t
        +
Nhãn phân cụm tài chính mới nhất đã thực sự có tại ngày t
        ↓
Căn chỉnh theo thời gian và PIT
        ↓
Chọn Market cluster dẫn dắt / giá trị cao theo profile
        +
Chọn Financial cluster dẫn dắt / giá trị cao theo profile
        ↓
Market Eligible Pool ∩ Financial Eligible Pool
        ↓
CANDIDATE UNIVERSE
        ↓
Tính 3 tiêu chí thị trường + 3 tiêu chí tài chính
        ↓
Áp dụng quy tắc xếp hạng kết hợp đã được khóa
        ↓
Chọn 30% số mã đứng đầu, làm tròn lên
        ↓
Phân bổ trọng số bằng nhau
        ↓
Mô phỏng giao dịch ở giá đóng cửa của phiên hợp lệ kế tiếp
        ↓
Backtest danh mục
```

Candidate Universe phải được tạo **trước** khi tính MC1–MC3 và FC1–FC3. Sáu tiêu chí dùng để xếp hạng các mã đã đủ điều kiện, không dùng để tự định nghĩa eligibility.

## 2.3. Vai trò của năm chiến lược

### Chiến lược chính — Kết hợp thị trường và tài chính

Combined kết hợp Market và Financial theo PIT, eligibility, scoring và ranking đã khóa.

Candidate Universe:

```text
Market Eligible Pool
∩
Financial Eligible Pool

```

### Đối chứng 1 — Market-only: Chỉ dùng tín hiệu thị trường

Market-only dùng tín hiệu thị trường để lựa chọn/xếp hạng cổ phiếu.

### Đối chứng 2 — Financial-only: Chỉ dùng tín hiệu tài chính

Financial-only dùng tín hiệu tài chính để lựa chọn/xếp hạng cổ phiếu.

Universe phải đồng thời thuộc tập mã có giao dịch tại thời điểm tương ứng.

Market leading cluster không được dùng làm điều kiện chọn mã.

### Đối chứng 3 — Equal-weight

Equal-weight sử dụng toàn bộ universe có giao dịch theo contract của strategy.

Không sử dụng Market/Financial ranking và không chọn top 30%.

Toàn bộ mã hợp lệ được phân bổ equal weight.

### Đối chứng 4 — Momentum-only

Momentum-only sử dụng universe có giao dịch và mom_126 hợp lệ.

Các mã được xếp hạng theo mom_126, chọn top 30% và phân bổ equal weight.

Financial signal/ranking không tham gia tạo Target Portfolio.

### Đối chuẩn chính thức

M3 hiện chỉ sử dụng **VNINDEX** làm benchmark chính thức để so sánh với kết quả backtest của chiến lược Combined.

VNINDEX là benchmark, không phải strategy thứ sáu.

Năm strategy M3 hiện tại gồm:
```
combined
market_only
financial_only
equal_weight
momentum_only
```
---

# 3. CÁC QUY TẮC

Phần này tập hợp và chuẩn hóa các quy tắc vận hành của M3 thành một hệ thống thống nhất, bao gồm: tính toàn vẹn thời gian và dữ liệu tài chính (PIT, Staleness), điều kiện thanh khoản, eligibility theo từng strategy, tiêu chí chấm điểm, quy tắc chọn top 30%, ngưỡng quy mô tối thiểu, quy tắc khớp lệnh thực thi và quy tắc kết thúc segment/run.

Các giá trị thuộc decision queue vẫn ở trạng thái OPEN/PROPOSED phải được phân biệt với rule đã được owner/mentor khóa. Việc một proposal đã được hiện thực trong code hoặc có mặt trong config không tự làm proposal đó trở thành official methodology.

---

## 3.1. Quy tắc thời gian và Point-in-Time (PIT)

### 3.1.1. Lịch ra quyết định hàng tháng

M3 dùng lịch ra quyết định hàng tháng dựa trên các mốc dữ liệu thị trường hợp lệ.

### 3.1.2. Dữ liệu tài chính có lịch công bố riêng

Dữ liệu tài chính có thể cập nhật theo quý, nửa năm hoặc năm và luôn có độ trễ công bố. Vì vậy không được ép mốc tài chính phải trùng ngày với mốc thị trường.

### 3.1.3. Ghép theo Financial state hợp lệ tại thời điểm quyết định

`decision_date` là ngày ra quyết định của M3.

Tại mỗi `decision_date = t`:

```text
market_cluster
= nhãn phân cụm thị trường tại t

usable_financial_years
= mọi fiscal_year có usable_from_date <= decision_date

selected_fiscal_year
= max(usable_financial_years)

financial_cluster
= Financial state tương ứng với selected_fiscal_year
```

Nếu không có `fiscal_year` nào thỏa:

```text
usable_from_date <= decision_date
```

thì:

```text
FINANCIAL_NOT_AVAILABLE
```

Financial PIT của M3 thực hiện theo thứ tự:

```text
usable_from_date <= decision_date
↓
lọc các fiscal_year đã usable
↓
selected_fiscal_year = max(fiscal_year)
↓
lấy Financial state tương ứng
```

Ý nghĩa của hai trường thời gian:

```text
usable_from_date
→ xác định fiscal_year đã được phép sử dụng tại decision_date hay chưa

fiscal_year
→ xác định năm tài chính mới nhất
   trong số các năm đã được phép sử dụng
```

Ví dụ:

```text
FY2022
usable_from_date = 2023-03-13

FY2023
usable_from_date = 2024-03-11
```

Tại:

```text
decision_date = 2024-03-08
```

thì:

```text
usable_financial_years = {2022}
selected_fiscal_year = 2022
```

Tại:

```text
decision_date = 2024-03-11
```

thì:

```text
usable_financial_years = {2022, 2023}
selected_fiscal_year = 2023
```

Không dùng `period_end` thay cho `usable_from_date` để xác định Financial data đã được phép sử dụng tại `decision_date` hay chưa.

---

## 3.2. Quy tắc về độ cũ của dữ liệu tài chính (Financial Staleness — CHỜ QUYẾT ĐỊNH)

Một nhãn tài chính không được mặc định có hiệu lực vô hạn. 

Proposal hiện tại trên Git:
- stale_months = 18
- FY t không được sử dụng quá 18 tháng sau period_end
- proposal này hiện có trong config nhưng chưa phải quyết định LOCKED.

Runtime official phải đọc giá trị từ config đã khóa,
không hard-code 18 tháng trong implementation.

---

## 3.3. Quy tắc thanh khoản / ILLIQUID — Q2

Một mã được upstream gắn trạng thái:

```text
ILLIQUID
```

theo liquidity rule hiện hành.

ILLIQUID trực tiếp ảnh hưởng đến Market Eligible Pool.

Do đó, nếu Q2 được khóa theo proposal hiện hành:

```text
Combined
→ Market leg sử dụng Market Eligible Pool
→ ILLIQUID không thuộc Market Eligible Pool

Market-only
→ sử dụng Market Eligible Pool
→ ILLIQUID không thuộc Market Eligible Pool
```

Tuy nhiên không được tự suy rằng cùng Market eligibility filter phải được áp cho tất cả strategy.

Đối với:

```text
Financial-only
Equal-weight
Momentum-only
```

universe phải tuân theo definition riêng của strategy:

```text
Financial-only
→ Financial Eligible Pool ∩ traded universe

Equal-weight
→ traded universe

Momentum-only
→ traded universe ∩ mom_126 hợp lệ
```

Do đó:

```text
Market Eligible Pool
≠
traded universe
```

---

## 3.4. Quy tắc eligibility theo từng strategy

Các strategy M3 không bắt buộc sử dụng cùng một eligibility universe.

Mỗi strategy sử dụng đúng universe được định nghĩa trong strategy contract.

### 3.4.1. Combined

Combined yêu cầu cả hai nhánh:

```text
Market Eligible Pool
+
Financial Eligible Pool
```

Candidate Universe:

```text
Combined Candidate Universe
=
Market Eligible Pool
∩
Financial Eligible Pool
```

Financial Eligible Pool phải tuân theo:

- Financial PIT;
- Financial availability;
- Financial staleness nếu rule đã khóa;
- Financial B coverage;
- Financial data-quality requirements;
- Financial cluster/selection rule tương ứng.

Nếu Financial B không hỗ trợ:

```text
Bank
Securities
Insurance
```

thì các mã thuộc nhóm đó không thể vào Combined trong cấu hình yêu cầu Financial B.

### 3.4.2. Market-only

Market-only sử dụng:

```text
Market Eligible Pool
```

Market-only không yêu cầu:

- Financial B label;
- Financial PIT state;
- Financial staleness;
- Financial sector coverage;
- ROE;
- F-score;
- Z-score;
- Financial ranking.

Do đó Bank / Securities / Insurance vẫn có thể tham gia Market-only nếu thỏa Market eligibility.

Luồng:

```text
Market snapshot
↓
Market eligibility
↓
Market allowed/leading cluster
↓
Market ranking
↓
Top 30%
↓
Equal weight
```

### 3.4.3. Financial-only

Financial-only sử dụng:

```text
Financial Eligible Pool
∩
traded universe
```

Financial-only yêu cầu Financial PIT và Financial state hợp lệ.

Market leading cluster không được dùng làm điều kiện chọn mã.

Luồng:

```text
traded universe
+
Financial PIT-safe state
↓
Financial eligibility
↓
Financial allowed cluster
↓
Financial ranking
↓
Top 30%
↓
Equal weight
```

Nếu một sector không có Financial B state cần thiết thì sector đó không thể tham gia Financial-only theo definition này.

### 3.4.4. Equal-weight

Equal-weight sử dụng:

```text
traded universe
```

Không yêu cầu:

- Financial B coverage;
- Financial PIT;
- Financial eligibility;
- Market leading cluster;
- Financial leading cluster;
- Market ranking;
- Financial ranking.

Luồng:

```text
traded universe
↓
lấy toàn bộ ticker hợp lệ
↓
Equal weight
```

Không chọn top 30%.

Bank / Securities / Insurance không bị loại chỉ vì không có Financial B.

### 3.4.5. Momentum-only

Momentum-only sử dụng:

```text
traded universe
∩
mom_126 hợp lệ
```

Luồng:

```text
traded universe
↓
loại mã không có mom_126 hợp lệ
↓
rank mom_126 giảm dần
↓
Top 30%
↓
Equal weight
```

Không yêu cầu Financial B coverage hoặc Financial PIT.

Bank / Securities / Insurance không bị loại chỉ vì không có Financial B.

### 3.4.6. Nguyên tắc sector coverage

Khi Financial B không hỗ trợ Bank / Securities / Insurance:

```text
Combined
→ không thể sử dụng mã đó nếu Financial B là requirement

Financial-only
→ không thể sử dụng mã đó nếu không có Financial state cần thiết

Market-only
→ không bị loại chỉ vì thiếu Financial B

Equal-weight
→ không bị loại chỉ vì thiếu Financial B

Momentum-only
→ không bị loại chỉ vì thiếu Financial B
```

Financial coverage không được dùng để thu hẹp Market-only, Equal-weight hoặc Momentum-only.

### 3.4.7. Nguyên tắc tổng quát

```text
decision_date
      │
      ├── Combined
      │   → Market Eligible ∩ Financial Eligible
      │
      ├── Market-only
      │   → Market Eligible Pool
      │
      ├── Financial-only
      │   → Financial Eligible Pool ∩ traded universe
      │
      ├── Equal-weight
      │   → traded universe
      │
      └── Momentum-only
          → traded universe ∩ mom_126 available
```

---

## 3.5. Sáu tiêu chí chọn mã và xếp hạng kết hợp

Các giá trị cụ thể của Q7–Q9 hiện vẫn thuộc decision queue.

Config hiện tại có:

```text
status = PROPOSED
```

Các criterion và rule dưới đây mô tả proposal/implementation hiện tại.

### 3.5.1. Ba tiêu chí thị trường — Q7

```text
MC1 = mom_126
→ higher is better

MC2 = downside_vol_63
→ lower is better

MC3 = liquidity_21
→ higher is better
```

Các giá trị được lấy từ Market snapshot tại `decision_date`.

### 3.5.2. Ba tiêu chí tài chính — Q8

```text
FC1 = ROE
→ higher is better

FC2 = F-score
→ higher is better

FC3 = Z-score
→ higher is better
```

Financial criteria của ticker được lấy theo:

```text
selected_fiscal_year
```

đã xác định bằng Financial PIT.

### 3.5.3. Missing Financial criterion — Q8

Nếu thiếu một hoặc một phần FC1–FC3:

```text
missing criterion
→ percentile trung tính = 0.5
→ ghi missing flag
```

Nếu toàn bộ:

```text
ROE
F-score
Z-score
```

đều thiếu:

```text
ticker bị loại khỏi Financial scoring result
```

Không biến missing thành 0.

### 3.5.4. Tiêu chuẩn mô tả tiêu chí

| Trường | Ý nghĩa |
|---|---|
| `criterion_id` | mã criterion, ví dụ `MC1`–`MC3`, `FC1`–`FC3` |
| `name` | tên criterion |
| `description` | criterion đo điều gì |
| `formula` | công thức chính xác |
| `source_fields` | các field đầu vào |
| `source_artifact` | artifact nguồn |
| `direction` | `higher` / `lower is better` |
| `missing_rule` | cách xử lý missing |
| `tie_rule` | cách xử lý hòa |

### 3.5.5. Hai kết quả xếp hạng riêng

Market:

```text
MC1 + MC2 + MC3
↓
percentile theo từng criterion
↓
S_market
```

Financial:

```text
FC1 + FC2 + FC3
↓
percentile theo từng criterion
↓
áp missing rule
↓
S_fin
```

Đối với one-sided strategy:

```text
Market-only
→ score = S_market

Financial-only
→ score = S_fin
```

### 3.5.6. Quy tắc xếp hạng Combined — Q9

Config hiện tại sử dụng:

```text
combined_weight_market = 0.5
```

nên:

```text
Combined Score
=
0.5 × S_market
+
0.5 × S_fin
```

Tie-break hiện tại:

```text
Combined Score cao hơn
↓
liquidity_21 cao hơn
↓
ticker A → Z
```

Các rule Q7–Q9 chỉ trở thành official methodology khi decision tương ứng được khóa và config chuyển sang:

```text
status = LOCKED
```

Khi config còn `PROPOSED`, chúng có thể được dùng trong `--targets-only` để audit universe, ranking và picks.

---

## 3.6. Quy tắc chọn 30% số mã và phân bổ tỷ trọng

**Đã được chủ dự án duyệt.**

### 3.6.1. Trình tự 5 bước chọn top 30%

```text
Bước 1: tạo tập ứng viên kết hợp
Bước 2: xếp hạng toàn bộ mã trong tập ứng viên
Bước 3: tính số lượng cần chọn = ceil(30% × số mã ứng viên)
Bước 4: chọn đúng số mã đứng đầu
Bước 5: phân bổ trọng số bằng nhau
```

Không làm:

```text
Thị trường → chọn 30%
Tài chính → chọn 30%
→ ghép hai danh sách
```

Ví dụ: tập ứng viên kết hợp có 11 mã thì `ceil(0.30 × 11) = 4`, vì vậy chọn 4 mã đứng đầu.

### 3.6.2. Phân bổ trọng số mục tiêu (Equal Weight)

Mỗi mã được chọn có tỷ trọng mục tiêu:

```text
target_weight = 1 / n_select
```

---

## 3.7. Quy tắc ngưỡng quy mô danh mục tối thiểu (UNIVERSE_TOO_SMALL — Q6)

Q6 hiện vẫn thuộc decision queue và chưa được coi là official methodology đã khóa.

Config/code Git hiện tại đang hiện thực proposal:

n_min = 10

Proposal này áp dụng cho các strategy đi qua _finish():

Combined
Market-only
Financial-only

và hiện không áp dụng cho:

Equal-weight
Momentum-only

vì hai strategy này không đi qua _finish() trong implementation hiện tại.

Nếu Q6 được khóa theo proposal hiện hành và:

N_candidates < n_min

thì không tạo Target Portfolio mới theo ranking và không mở vị thế mới.

Cơ chế hiện tại:

mã đang nắm
+
vẫn còn trong Candidate Universe
→ giữ

mã đang nắm
+
đã rời Candidate Universe
→ SELL

candidate mới
+
chưa nắm
→ không BUY

Tiền từ SELL thành công được giữ ở Cash, không phân bổ lại cho candidate mới.

Riêng kỳ đầu tiên, nếu:

N_candidates < n_min

thì strategy giữ 100% Cash cho tới kỳ đầu tiên đủ điều kiện theo Q6.

Lý do của proposal: Candidate Universe quá nhỏ có thể làm danh mục tập trung vào quá ít cổ phiếu và khiến kết quả bị chi phối bởi một số lượng mã rất nhỏ.

Khi config còn:

status = PROPOSED

logic này có thể được dùng trong --targets-only để audit candidate count và hành vi hiện tại của implementation, nhưng không được diễn giải là Q6 đã được owner/mentor khóa.

Official Development/Holdout backtest chỉ được sử dụng giá trị Q6 sau khi decision tương ứng được khóa và config chuyển sang:

status = LOCKED

---

## 3.8. Quy tắc khớp lệnh và xử lý giao dịch thất bại

Các quy tắc sau điều khiển cách thức danh mục thực thi chuyển đổi từ Current Holdings sang Target Portfolio:

### 3.8.1. Lịch thực thi
Giao dịch được thực hiện ở giá đóng cửa của phiên hợp lệ kế tiếp:

```text
execution_date = phiên giao dịch hợp lệ đầu tiên sau decision_date (T+1)
```

### 3.8.2. Thứ tự thực thi lệnh
- **SELL luôn được thực hiện trước**: Nhằm giải phóng sức mua và xác định số dư Cash thực tế.
- **BUY được thực hiện sau**: Dựa trên lượng tiền mặt thực tế thu được sau khi hoàn tất các lệnh SELL.

### 3.8.3. Xử lý lệnh mua thất bại (BUY_FAILED)
Phần vốn dự kiến mua mã đó tiếp tục giữ ở Cash; không chọn mã khác thay thế và không chia lại phần vốn của chính `BUY_FAILED` cho mã khác.

### 3.8.4. Xử lý lệnh bán thất bại (SELL_FAILED)
Mã vẫn nằm trong holdings và không tạo Cash.

### 3.8.5. Cơ chế bù trừ vốn tự động (Proportional Scaling khi thiếu Cash do SELL_FAILED)
Nếu vì `SELL_FAILED` mà Cash thực có không đủ cho các lệnh BUY còn lại:
- Áp dụng **proportional scaling** cho toàn bộ các BUY còn lại theo tỷ lệ:
  ```text
  execution_scale = available_cash / total_required_buy_cash
  ```
- Không dùng margin, không thay mã, không đổi ranking.

---

## 3.9. Quy tắc kết thúc segment/run (Đề xuất)

Quy tắc này xác định cách M3 xử lý điểm cuối của một segment/run và phân biệt với trường hợp hệ thống đang được cập nhật liên tục.

### A. Segment/run hữu hạn

Một segment/run hữu hạn phải có `segment_end_date` được xác định trước.

Không được coi snapshot mới nhất hiện có là snapshot cuối chỉ vì chưa có dữ liệu của kỳ tiếp theo.

Khi runner đã tới điểm kết thúc của run:

```text
Actual Holdings đang tồn tại
↓
không mở rebalance mới nếu execution/valuation
sẽ vượt segment_end_date
↓
giữ danh mục tới end_date
↓
revalue tại end_date
↓
PRICE_STALE nếu thiếu giá
↓
tính NAV cuối segment
↓
kết thúc run
```

Trong đó:

```text
end_date
= phiên giao dịch hợp lệ cuối cùng
  không vượt segment_end_date
```

Tại `end_date`:

```text
không mở rebalance mới
không tính delta_weight mới
không BUY
không SELL
không sử dụng dữ liệu giá sau segment_end_date
```

### B. Rolling/live update chưa có ngày kết thúc

Nếu chưa có `segment_end_date`, snapshot mới nhất hiện tại không được coi là snapshot cuối.

Runner tiếp tục xử lý bình thường:

```text
snapshot mới
↓
Bước 1 tạo Target
↓
lưu Target/state
↓
chờ execution_date
↓
tiếp tục chu trình ở kỳ sau
```

Do đó, việc chưa có snapshot tháng tiếp theo không được tự động kích hoạt logic kết thúc run.

---

# 4. CÁC QUYẾT ĐỊNH ĐÃ KHÓA VÀ CÒN MỞ

| Hạng mục | Trạng thái |
|---|---|
| Chỉ mua, không bán khống | ĐÃ KHÓA |
| Không dùng đòn bẩy | ĐÃ KHÓA |
| Thị trường và tài chính phân cụm riêng | ĐÃ DUYỆT |
| Kết hợp ở bước ra quyết định danh mục, không phân cụm lại đặc trưng thô | ĐÃ DUYỆT |
| Market model authority: A v4, k=3, là mô hình Market chính thức cho M2/M3; M2 K=2 giữ làm legacy/control | ĐÃ KHÓA — D-DIR-01 ngày 26/10/2026 |
| Market cluster: chọn cluster dẫn dắt / giá trị cao theo profile/semantic, không theo số label | ĐÃ DUYỆT 24/10/2026 |
| Financial cluster: chọn cluster dẫn dắt / giá trị cao theo profile/semantic, không theo số label | ĐÃ DUYỆT 24/10/2026 |
| Exact leading-cluster selector: field/profile criterion dùng để chọn Market/Financial leading cluster, tie rule và ambiguity handling | CHỜ MENTOR/OWNER |
| Financial PIT: lọc các `fiscal_year` có `usable_from_date <= decision_date`, sau đó chọn `max(fiscal_year)` | OWNER DECISION — PENDING GIT SYNC |
| Candidate Universe = Market Eligible Pool ∩ Financial Eligible Pool | ĐÃ DUYỆT 24/10/2026 |
| Có 3 tiêu chí thị trường | ĐÃ DUYỆT VỀ CẤU TRÚC; EXACT Q7 CHỜ CHỐT |
| Có 3 tiêu chí tài chính khác 3 tiêu chí thị trường | ĐÃ DUYỆT VỀ CẤU TRÚC; EXACT Q8 CHỜ CHỐT |
| Missing một phần Financial criteria → percentile 0.5 + flag; thiếu toàn bộ → loại khỏi Financial scoring | PROPOSED Q8 / IMPLEMENTED |
| Chọn 30% sau khi đã có Candidate Universe đối với strategy có top-selection | ĐÃ DUYỆT |
| 30% làm tròn lên | ĐÃ KHÓA |
| Trọng số bằng nhau | ĐÃ KHÓA |
| Tái cân bằng hàng tháng | ĐÃ KHÓA |
| Giao dịch ở giá đóng cửa phiên hợp lệ kế tiếp | ĐÃ KHÓA |
| Execution boundary cuối segment: Target vẫn tạo và lưu; nếu `execution_date > segment_end` thì không đưa vào execution schedule, không chạy Bước 2 | ĐỀ XUẤT |
| BUY_FAILED: phần vốn dự kiến mua tiếp tục ở Cash, không thay mã/không chia lại | ĐÃ KHÓA |
| SELL_FAILED: mã vẫn nằm trong holdings và không tạo Cash | ĐÃ KHÓA |
| SELL_FAILED làm thiếu Cash cho BUY: scale toàn bộ BUY còn lại theo `execution_scale` | ĐÃ DUYỆT 24/10/2026 |
| Missing-price/SELL_FAILED theo engine GitHub: price thiếu khi valuation → stale mark; price thiếu/non-tradable khi SELL → SELL_FAILED; không bắt buộc external verification gate | ĐÃ ĐƯỢC CHỦ DỰ ÁN CHỌN 26/10/2026 |
| Output canonical M3-A dùng bộ `targets/trade_ledger/holdings/turnover/nav/benchmark/metrics/manifest` theo GitHub | ĐÃ ĐƯỢC CHỦ DỰ ÁN CHỌN 26/10/2026 |
| Lợi suất tiền mặt = 0 | ĐÃ KHÓA |
| Chi phí giao dịch chính = 0 | ĐÃ KHÓA |
| Trượt giá chính = 0 | ĐÃ KHÓA |
| Historical schedule/coverage = 84 snapshots: Development 2019–2023, Holdout 2024–2025; runtime Market input đọc từ `terminal.sqlite` theo GitHub | ĐÃ DUYỆT 24/10/2026 |
| Benchmark chính thức: VNINDEX | ĐÃ DUYỆT |
| Sharpe chỉ tính trên Final Evaluation để báo cáo cuối | ĐÃ DUYỆT 24/10/2026 |
| Final Evaluation dùng dữ liệu sau 31/12/2025 nếu pass readiness + unseen-status audit | ĐÃ KHÓA NGUYÊN TẮC |
| Công thức MC1..MC3 | CHỜ Q7 / MENTOR |
| Công thức FC1..FC3 và final missing rule | CHỜ Q8 / MENTOR |
| Cách gộp hai nhánh thành thứ hạng cuối + tie rule | CHỜ Q9 |
| Quy tắc về độ cũ của dữ liệu tài chính | CHỜ Q10 |
| Return basis cho security/portfolio/VNINDEX | CHỜ Q11 |
| Turnover = `(executed_buy_value + executed_sell_value) / (2 × pre_trade_NAV)` | OWNER DECISION — PENDING GIT SYNC |
| Financial clustering handoff và coverage đủ cho Combined | CHỜ UPSTREAM / Q3 |
| Exact start/end của Final Evaluation | CHỜ DATA READINESS + UNSEEN AUDIT |
| Q17: Adjusted-price one-session glitch handling | CHỜ OWNER/MENTOR |
| Quy tắc xác định usable_from_date cho BCTC năm: FY >= 2022 dùng ngày công bố CafeF; FY < 2022 dùng lag rule 30/06 năm t+1 | CHỜ OWNER/MENTOR |

---

# 5. KHUNG DỮ LIỆU CHUNG

Mục này là nơi duy nhất trong tài liệu mô tả chi tiết **runtime input contract của M3-A**.

Các mục khác chỉ dẫn chiếu về Mục 5, không lặp lại toàn bộ path/schema.

## 5.1. Đầu vào từ hệ Market

M3-A sử dụng hai nhóm input Market/execution.

### A. `terminal.sqlite`

```text
data/web/delta-intelligence-v4/terminal.sqlite
```

Cung cấp:

```text
Market observations
Financial observations
price table
```

Đối với Market observations, M3 cần các thông tin tương ứng với:

```text
date
ticker
cluster
features
liquidity
```

Các Market criteria cần cho strategy như:

```text
mom_126
downside_vol_63
liquidity_21
mdd_126
```

được đọc từ Market state đã được upstream tạo.

M3-A không fit lại Market clustering trong quá trình backtest.

Price data trong `terminal.sqlite` cung cấp tối thiểu:

```text
ticker
date
adj_close
raw_close
volume
```

Vai trò cụ thể của raw/adjusted price đối với return phải tuân theo return-basis decision đã khóa.

### B. C8 canonical Market artifacts

```text
artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/
├── prices_daily.jsonl
├── trading_calendar.jsonl
└── benchmark_daily.jsonl
```

Vai trò:

```text
prices_daily.jsonl
→ raw market information
→ ceiling/floor information
→ tradability support

trading_calendar.jsonl
→ trading calendar
→ xác định phiên hợp lệ kế tiếp

benchmark_daily.jsonl
→ VNINDEX benchmark
```

Các file này không được tự dùng thay thế lẫn nhau nếu semantic khác nhau.

## 5.2. Đầu vào từ hệ Financial

M3-A sử dụng ba thành phần Financial chính.

### A. Financial B state

Financial observations nằm trong:

```text
data/web/delta-intelligence-v4/terminal.sqlite
```

và cung cấp Financial state/cluster theo fiscal year.

M3-A không fit lại Financial B trong quá trình backtest.

Financial state được sử dụng phải tuân theo Financial PIT tại `decision_date`.

### B. Financial indicators

```text
data/financial/indicators_v1/results/
indicators-2c4a24e3830d325f/indicators.sqlite
```

M3 hiện sử dụng Financial criteria:

```text
ROE
F-score
Z-score
```

và metadata:

```text
sector_group
```

khi strategy/eligibility rule yêu cầu.

Theo Q8 proposal hiện tại:

```text
missing một hoặc một phần Financial criteria
→ percentile = 0.5
→ missing flag

missing toàn bộ Financial criteria
→ loại khỏi Financial scoring
```

### C. Financial availability

```text
data/financial/disclosure_dates_v1/
availability-4f0f83108e761dae/availability.csv
```

Tối thiểu cần:

```text
ticker
fiscal_year
usable_from_date
```

Tại:

```text
decision_date = t
```

các fiscal year hợp lệ là:

```text
usable_from_date <= decision_date
```

Sau đó:

```text
selected_fiscal_year
=
max(usable_financial_years)
```

Nếu không có fiscal year hợp lệ:

```text
FINANCIAL_NOT_AVAILABLE
```

Không dùng `period_end` để thay thế thời điểm dữ liệu được phép sử dụng.

## 5.3. Các phép xử lý bắt buộc sau khi đọc input

M3-A vẫn phải thực hiện:

```text
Market state
        +
Financial state PIT-safe
        ↓
Eligibility
        ↓
Strategy-specific Candidate Universe
        ↓
Strategy-specific ranking
        ↓
Target Portfolio
```

Không bắt buộc persist riêng toàn bộ bảng intermediate nếu canonical implementation không yêu cầu.

Kết quả persist đầu tiên của portfolio-selection stage là:

```text
targets_<strategy>.csv
```

Các phép PIT/eligibility/ranking phải có thể tái lập từ:

```text
manifest.json
+
config đã hash
+
version/hash của runtime inputs
+
code commit
```

## 5.4. Historical backtest segments

Historical M3-A sử dụng:

| Segment | Khoảng thời gian | Decision snapshots | Vai trò |
|---|---|---:|---|
| Development | 2019-01-31 → 2023-12-29 | 60 | Historical development evaluation |
| Holdout | 2024-01-31 → 2025-12-31 | 24 | Chạy bằng cùng frozen strategy/config |

Tổng:

```text
84 decision snapshots
```

Development và Holdout phải được chạy/seal riêng.

Không dùng kết quả Development để thay strategy trước khi mở Holdout.

Dữ liệu sau:

```text
2025-12-31
```

thuộc vùng ứng viên Final Evaluation.

Exact Final Evaluation window chỉ được khóa sau khi data readiness và evaluation-status audit đạt yêu cầu.

# PHẦN A — M3-A: BACKTEST THEO 4 BƯỚC, BẮT ĐẦU TỪ CÁC M3 RUNTIME INPUT ĐÃ PIN

# 6. ĐIỂM BẮT ĐẦU CỦA M3-A

Mục này không định nghĩa lại input contract.

Chi tiết sáu logical runtime inputs được giữ duy nhất tại Mục 5 — Khung dữ liệu chung.

M3-A chỉ bắt đầu khi toàn bộ runtime inputs bắt buộc đã:

```text
đặt đúng logical path/version
        +
pass schema audit
        +
pass coverage audit cho segment cần chạy
        +
version/hash được xác minh
        +
được pin vào manifest
```

Nếu một runtime input bắt buộc chưa đạt:

```text
INPUT_NOT_READY
```

thì official backtest phụ thuộc input đó không được chạy.

M3-A không chạy lại:

```text
Market A clustering
Financial B clustering
```

trong backtest.

Hai hệ clustering là upstream state của M3-A.

M2 K=2 cũ chỉ được dùng khi một research/control strategy hoặc config đã khóa yêu cầu; nó không phải runtime prerequisite của main M3-A.

Sau khi input readiness PASS:

```text
Runtime inputs ready
        ↓
Strategy rules/config ready
        ↓
Target Portfolio
        ↓
Execution
        ↓
Holding / valuation
        ↓
Rebalance
        ↓
Canonical outputs
```

Nếu config còn:

```text
status = PROPOSED
```

thì chỉ được thực hiện các bước readiness/targets-only được protocol cho phép.

Official backtest có return chỉ chạy sau khi:

```text
config = LOCKED
```

---

# 7. LUỒNG HOẠT ĐỘNG DUY NHẤT CỦA BACKTEST

Từ lúc sáu GitHub M3 runtime inputs đã audit/pin đầy đủ, toàn bộ M3-A được tổ chức theo đúng 4 bước:

```text
ĐIỂM BẮT ĐẦU
Có đủ GitHub M3 runtime inputs đã audit/pin
        ↓
1. CHỌN CỔ PHIẾU
        ↓
2. GIẢ LẬP MUA/BÁN
        ↓
3. GIỮ VÀ TÍNH LỜI/LỖ
        ↓
4. THÁNG SAU TÁI CÂN BẰNG
        ↓
   quay lại Bước 1
```

Bốn bước này được lặp lại cho đến hết Development hoặc Holdout theo 84 Market snapshots hiện hành trong `terminal.sqlite`, với các input phụ trợ đã pin cùng run.

Sau khi đã chạy xong 4 bước trên cho toàn bộ lịch sử mới tính các performance metrics và so sánh benchmark.

---

## BẢNG CÁC BIẾN DÙNG TRONG 4 BƯỚC M3-A

Ghi chú:

- Bảng chỉ liệt kê các biến có ý nghĩa trực tiếp đối với nghiệp vụ, tính toán hoặc output.
- `values[ticker]` là tên state thực tế trong engine, lưu giá trị phần vốn hiện đang nắm giữ ở ticker.
- `marks[ticker]` là giá gần nhất được dùng để định giá ticker.
- `current_price` tương ứng với giá mà `revalue()` nhận từ `price(ticker, date)`.
- `holdings_<strategy>.csv` không persist `values[ticker]`; output holdings theo Git hiện hành chỉ ghi `date`, `ticker`, `weight`.

| Bước | Biến / trường | Ý nghĩa | Đơn vị / dạng |
| :---: | :--- | :--- | :--- |
| 1 | `decision_date` | Ngày strategy ra quyết định chọn cổ phiếu | Ngày |
| 1 | `ticker` | Mã cổ phiếu | Chuỗi |
| 1 | `market_cluster` | Cụm thị trường của mã tại decision_date | Nhãn cụm |
| 1 | `fiscal_year` | Năm tài chính của Financial state | Năm |
| 1 | `usable_from_date` | Ngày sớm nhất Financial state được phép sử dụng | Ngày |
| 1 | `usable_financial_years` | Các năm tài chính thỏa `usable_from_date <= decision_date` | Tập năm |
| 1 | `selected_fiscal_year` | `max(usable_financial_years)` | Năm |
| 1 | `financial_cluster` | Cụm tài chính của selected_fiscal_year | Nhãn cụm |
| 1 | `Market Eligible Pool` | Các mã đạt điều kiện nhánh Market | Tập ticker |
| 1 | `Financial Eligible Pool` | Các mã đạt điều kiện nhánh Financial | Tập ticker |
| 1 | `Candidate Universe` | Giao Market Eligible Pool và Financial Eligible Pool | Tập ticker |
| 1 | `N_candidates` / `candidates` | Số mã trong Candidate Universe | Số nguyên |
| 1 | `MC1`, `MC2`, `MC3` | Ba tiêu chí thị trường dùng để ranking | Theo contract |
| 1 | `FC1`, `FC2`, `FC3` | Ba tiêu chí tài chính dùng để ranking | Theo contract |
| 1 | `rank` | Thứ hạng ticker theo strategy ranking | Số nguyên |
| 1 | `n_select` | Số mã được chọn: `ceil(0.30 × N_candidates)` đối với strategy có top-selection | Số nguyên |
| 1 | `target_weight` | Tỷ trọng mục tiêu | Tỷ lệ 0–1 |
| 1 | `Target Portfolio` / `target` | Mapping ticker → target_weight | Dict |
| 1 | `status` trong targets | Trạng thái tạo target | Chuỗi |
| 1–4 | `segment_end_date` | Ngày biên kết thúc tuyệt đối của segment/run; mọi execution/valuation của segment không được vượt ngày này | Ngày |
| 2 | `execution_date` | Phiên giao dịch hợp lệ đầu tiên sau decision_date; với segment/run hữu hạn phải không vượt segment_end_date | Ngày |
| 2–4 | `pf` / `Portfolio` | Object danh mục được giữ xuyên suốt các kỳ | Object |
| 2–4 | `cash` | Tiền mặt hiện có | Value space |
| 2–4 | `values[ticker]` | Giá trị phần vốn hiện đang nắm giữ ở ticker trong internal Portfolio state | Value space |
| 2–4 | `marks[ticker]` | Giá gần nhất dùng để định giá ticker | Giá |
| 2 | `current_price` | Giá ticker tại execution_date theo price basis được dùng | Giá |
| 2 | `price(ticker,date)` | Hàm trả giá cho valuation/execution | Giá hoặc None |
| 2 | `PRICE_STALE` | Thiếu giá khi revalue; giữ nguyên `values[ticker]` và `marks[ticker]` | Cờ |
| 2 | `pre_trade_NAV` / `nav` | NAV sau revalue, trước rebalance | Value space |
| 2 | `pre_weight` | `values[ticker] / pre_trade_NAV` đối với cổ phiếu | Tỷ lệ 0–1 |
| 2 | `delta_weight` / `d` | `target_weight - pre_weight` | Tỷ lệ |
| 2 | `side` | BUY, SELL hoặc HOLD | Chuỗi |
| 2 | `intended` | Giá trị giao dịch dự kiến | Value space |
| 2 | `tradable(...)` | Cho biết BUY/SELL có thể thực hiện hay không | Boolean |
| 2 | `available_cash` | Cash thực tế sau khi xử lý SELL | Value space |
| 2 | `required_buy_cash` / `required` | Tổng intended của các BUY executable | Value space |
| 2 | `execution_scale` / `scale` | Hệ số thu nhỏ BUY khi Cash không đủ | Tỷ lệ 0–1 |
| 2 | `executed` | Giá trị giao dịch thực tế | Value space |
| 2 | `status` trong ledger | EXECUTED, BUY_FAILED, SELL_FAILED, SCALED, HOLD | Chuỗi |
| 2 | `traded` | Tổng giá trị BUY + SELL thực sự executed | Value space |
| 2 | `turnover` | `traded / (2 × pre_trade_NAV)` | Tỷ lệ |
| 2 | `weight` | Tỷ trọng output từ `pf.weights()`; cổ phiếu = `values[ticker] / NAV`, CASH = `cash / NAV` | Tỷ lệ 0–1 |
| 3 | `nav` | Giá trị toàn danh mục tại valuation dates | Value space |
| 3 | `stale` | Danh sách `(date,ticker)` bị PRICE_STALE | Danh sách |
| 3 | `end_date` | Phiên giao dịch hợp lệ cuối cùng dùng để chốt valuation/NAV cuối segment; phải `<= segment_end_date` | Ngày |
| 4 | `schedule` | Chuỗi `(decision_date, execution_date, target)` mà engine lần lượt chạy | Danh sách |
| 4 | `goal` | Target thực tế được dùng tại kỳ hiện tại | Dict |
| 4 | `Current Portfolio` | `cash + values + marks` được carry từ kỳ trước | State |
| 4 | `Target Portfolio mới` | Target được Bước 1 tính lại ở kỳ mới | State |

---

# 8. TỔNG QUAN NHIỆM VỤ NẰM TRONG 4 BƯỚC

## BƯỚC 1 — CHỌN CỔ PHIẾU

```text
1.1  Xác minh dữ liệu Market
1.2  Xác minh dữ liệu Financial clustering
1.3  Căn PIT Market–Financial
1.4  Tạo Candidate Universe
1.5  Tính MC1–MC3 và FC1–FC3
1.6  Xếp hạng Combined
1.7  Chọn top 30% và tạo Target Portfolio
```

Các bước 1.1–1.6 là internal computation/validation. Output persist chính:

```text
targets_<strategy>.csv
```

## BƯỚC 2 — GIẢ LẬP MUA/BÁN

```text
2.1  Map decision_date → execution_date
2.2  Revalue Current Portfolio tại execution_date
2.3  So Current-vs-Target
2.4  Sinh SELL trước, BUY sau, HOLD khi delta≈0
2.5  Kiểm tra price/tradability theo engine GitHub
2.6  Xử lý BUY_FAILED / SELL_FAILED / proportional scaling
2.7  Chốt ledger, holdings và turnover
```

Output persist:

```text
trade_ledger_<strategy>.csv
holdings_<strategy>.csv
turnover_<strategy>.csv
```

## BƯỚC 3 — GIỮ VÀ TÍNH LỜI/LỖ

Portfolio state được giữ trong engine. Tại execution date kế tiếp hoặc `end_date`, engine revalue holdings bằng price basis đã được khóa. Missing price dùng last valid mark và ghi `PRICE_STALE`.

Output persist:

```text
nav_<strategy>.csv
```

Các security return/contribution và pre-rebalance-weight có thể được tính nội bộ hoặc suy từ state nhưng không còn là canonical file riêng.

## BƯỚC 4 — THÁNG SAU TÁI CÂN BẰNG

Không tạo handoff CSV riêng. Portfolio state được carry trực tiếp trong engine:

```text
Actual Holdings kỳ t
→ revalue tại execution_date kỳ t+1
→ Target mới
→ Current-vs-Target
→ rebalance mới
```

Sau khi chạy hết segment mới tính/report metrics và benchmark.

# 9. BƯỚC 1 — CHỌN CỔ PHIẾU VÀ TẠO TARGET PORTFOLIO CHO 5 STRATEGY

Mục tiêu của Bước 1 là tạo **Target Portfolio riêng cho từng strategy tại mỗi `decision_date`**, không sử dụng thông tin tương lai.

Config hiện tại khai báo 5 strategy:

```text
1. combined
2. market_only
3. financial_only
4. equal_weight
5. momentum_only
```

Mỗi strategy:

```text
cùng decision_date
↓
đọc đúng dữ liệu được phép sử dụng tại decision_date
↓
áp dụng các eligibility rule tương ứng
↓
tạo danh sách mã riêng
↓
tạo Target Portfolio riêng
↓
sau đó mới được đưa sang cùng backtest engine ở Bước 2
```

Do đó Bước 1 không tạo một Target Portfolio chung cho toàn bộ M3.

Nó tạo riêng:

```text
Target Combined
Target Market-only
Target Financial-only
Target Equal-weight
Target Momentum-only
```

Điểm quan trọng:

không tồn tại một Financial eligibility gate chung
áp trước cả 5 strategy

Financial eligibility chỉ là prerequisite của strategy thực sự sử dụng Financial state theo contract tương ứng.

Cụ thể:

Combined
→ Market Eligible Pool ∩ Financial Eligible Pool

Market-only
→ Market Eligible Pool

Financial-only
→ Financial Eligible Pool ∩ traded universe

Equal-weight
→ traded universe

Momentum-only
→ traded universe ∩ mom_126 hợp lệ

Do đó việc thiếu:

Financial B label
Financial PIT state
Financial indicator
Financial sector coverage

không tự động loại ticker khỏi:

Market-only
Equal-weight
Momentum-only

Bank / Securities / Insurance vẫn có thể tham gia ba strategy này nếu thỏa universe definition của chính strategy.

Trạng thái decision: config Git hiện vẫn là:

status = PROPOSED

---

## 9.1. Đầu vào chung

### 9.1.1. Market input

Nguồn Market chính:

```text
data/web/delta-intelligence-v4/terminal.sqlite
```

Market snapshot tại mỗi `decision_date` cung cấp tối thiểu:

```text
ticker
cluster
features
liquidity
```

Các market feature được strategy hiện tại sử dụng gồm:

```text
mom_126
downside_vol_63
liquidity_21
```

Config hiện tại:

```text
mom_126
→ higher is better

downside_vol_63
→ lower is better

liquidity_21
→ higher is better
```

Không tự fit lại Market A, không đổi K, không đổi scaling trong M3.

---

### 9.1.2. Financial input

Financial input được sử dụng trực tiếp bởi:

```text
combined
financial_only
```

Nguồn:

```text
terminal.sqlite
→ Financial B labels/state

indicators.sqlite
→ ROE
→ F-score
→ Z-score
→ sector_group

availability.csv
→ ticker
→ fiscal_year
→ usable_from_date
```

Local paths:

```text
data/web/delta-intelligence-v4/terminal.sqlite

data/financial/indicators_v1/results/
indicators-2c4a24e3830d325f/indicators.sqlite

data/financial/disclosure_dates_v1/
availability-4f0f83108e761dae/availability.csv
```

Config PROPOSED hiện tại sử dụng:

```text
ROE
→ higher is better

F-score
→ higher is better

Z-score
→ higher is better
```

Financial data được dùng cho:

```text
Combined
→ Financial eligibility
→ Financial cluster/selection
→ Financial ranking

Financial-only
→ Financial eligibility
→ Financial cluster/selection
→ Financial ranking
```

Q8 proposal hiện tại xử lý missing Financial criteria:

```text
thiếu một hoặc một phần:
ROE / F-score / Z-score

→ percentile trung tính = 0.5
→ ghi missing flag
```

Nếu cả ba đều thiếu:

```text
ticker bị loại khỏi Financial scoring result
```

Không biến missing thành 0.

Đối với:

```text
market_only
equal_weight
momentum_only
```

Financial input không phải eligibility prerequisite.

Do đó việc thiếu:

```text
Financial B label
Financial PIT state
Financial indicator
Financial sector coverage
```

không tự động loại ticker khỏi ba strategy này.

Bank / Securities / Insurance có thể tiếp tục xuất hiện trong Market-only, Equal-weight và Momentum-only nếu thỏa universe definition riêng của strategy.

---

## 9.2. Financial PIT

Financial PIT áp dụng cho:

```text
combined
financial_only
```

Tại:

```text
decision_date = t
```

các fiscal year hợp lệ là:

```text
usable_financial_years
=
mọi fiscal_year có:

usable_from_date <= decision_date
```

Nếu không có fiscal year hợp lệ:

```text
FINANCIAL_NOT_AVAILABLE
```

Nếu có fiscal year hợp lệ:

```text
selected_fiscal_year
=
max(usable_financial_years)
```

Financial B state và Financial indicators được lấy theo:

```text
ticker
+
selected_fiscal_year
```

Ví dụ:

```text
FY2022 usable_from_date = 2023-03-13
FY2023 usable_from_date = 2024-03-11
```

Tại:

```text
decision_date = 2024-03-08
```

thì:

```text
usable_financial_years = {2022}
selected_fiscal_year = 2022
```

Tại:

```text
decision_date = 2024-03-11
```

thì:

```text
usable_financial_years = {2022, 2023}
selected_fiscal_year = 2023
```

Không dùng `period_end` để xác định một fiscal year đã được phép sử dụng hay chưa.

Đối với:

```text
market_only
equal_weight
momentum_only
```

Financial PIT không phải eligibility gate.

---

## 9.3. Tổng quan cách chọn của 5 strategy

| Strategy | Universe | Financial eligibility | Signal / Ranking | Top 30% | Trọng số |
|---|---|:---:|---|:---:|---|
| Combined | Market Eligible ∩ Financial Eligible | Có | Market criteria + Financial criteria | Có | Equal weight |
| Market-only | Market Eligible Pool | Không | Market criteria | Có | Equal weight |
| Financial-only | Financial Eligible Pool ∩ traded universe | Có | Financial criteria | Có | Equal weight |
| Equal-weight | traded universe | Không | Không ranking | Không | Equal weight toàn universe |
| Momentum-only | traded universe ∩ mom_126 hợp lệ | Không | mom_126 | Có | Equal weight top 30% |

### Khái niệm traded universe

Trong implementation Git hiện tại, traded universe ở Bước 1 — selection không đồng nghĩa với việc một lệnh chắc chắn thực thi được tại execution_date.

Ở tầng strategy hiện tại, universe này được xây từ Market snapshot tại decision_date và loại các row có:

```text
liquidity = ILLIQUID
```

theo proposal/code hiện tại.

Ví dụ:

```text
Equal-weight
→ các ticker trong Market snapshot
→ liquidity != ILLIQUID

Momentum-only
→ các ticker trong Market snapshot
→ liquidity != ILLIQUID
→ mom_126 is not None
```

Cần phân biệt với:

```text
tradable(ticker, execution_date, side)
```

ở Bước 2.

tradable(...) là kiểm tra tại ngày thực thi, liên quan đến:

- price tồn tại
- volume > 0
- ceiling/floor rule
- side = BUY hoặc SELL

Do đó:

```text
selection-time traded universe
≠
execution-time tradability
```

Exact selection universe chỉ trở thành official methodology sau khi các decision liên quan như Q2/Q14 được khóa.

Điểm chung:

```text
mỗi strategy
↓
tạo Target Portfolio riêng
↓
cùng execution/backtest engine
```

Điểm khác nhau:

```text
Universe
+
Signal
+
Ranking
+
Selection
```

Không yêu cầu:

```text
Combined universe
=
Market-only universe
=
Financial-only universe
=
Equal-weight universe
=
Momentum-only universe
```

Các strategy đối chứng được thiết kế để kiểm tra các signal/universe khác nhau theo definition của chính strategy đó.

---

## 9.4. STRATEGY 1 — Combined

`Combined` là strategy chính kết hợp:

```text
Market
+
Financial
```

### 9.4.1. Market Eligible Pool

Từ Market snapshot tại `decision_date`:

```text
Market snapshot
↓
áp dụng liquidity rule
↓
xác định Market leading cluster theo market_rule
↓
Market Eligible Pool
```

Không lấy các mã:

```text
ILLIQUID
```

vào Market Eligible Pool theo rule hiện tại.

---

### 9.4.2. Financial Eligible Pool

Tại cùng `decision_date`:

```text
Financial PIT alignment
↓
selected_fiscal_year
↓
áp Financial eligibility
↓
Financial B state
↓
Financial allowed cluster
↓
Financial Eligible Pool
```

Financial cluster được xác định theo profile/rule hiện hành, không chọn trực tiếp theo numeric cluster label.

Ở đây cần phân biệt:

```text
Financial eligibility
→ xác định ticker có đủ điều kiện Financial để tiếp tục xét hay không

Financial allowed cluster
→ Financial signal/selection của strategy sử dụng Financial branch
```

Financial eligibility được sử dụng bởi:

```text
Combined
Financial-only
```

theo contract riêng của hai strategy.

Financial eligibility không phải prerequisite của:

```text
Market-only
Equal-weight
Momentum-only
```

Do đó không được dùng Financial B coverage, Financial PIT hoặc Financial indicator coverage để thu hẹp universe của ba strategy này.

---

### 9.4.3. Candidate Universe của Combined

Rule:

```text
Combined Candidate Universe
=
Market Eligible Pool
∩
Financial Eligible Pool
```

Chỉ các mã nằm trong cả hai pool mới đi tiếp vào ranking.

---

### 9.4.4. Combined criteria

Với mỗi mã trong Candidate Universe:

```text
Market criteria:
mom_126
downside_vol_63
liquidity_21

+

Financial criteria:
ROE
F-score
Z-score
```

Sau đó tính score theo config hiện hành.

Config hiện tại:

```text
combined_weight_market = 0.5
```

tức về cấu trúc:

```text
Combined Score
=
Market component
+
Financial component
```

với trọng số Market hiện được cấu hình là `0.5`.

Không thay đổi trọng số dựa trên kết quả backtest.

---

### 9.4.5. Chọn top 30%

Nếu:

```text
N_candidates >= n_min
```

thì:

```text
n_select
=
ceil(
    top_share × N_candidates
)
```

Hiện tại:

```text
top_share = 0.30
```

nên:

```text
n_select
=
ceil(
    0.30 × N_candidates
)
```

Chọn:

```text
top n_select
```

theo Combined ranking.

Target weight:

```text
target_weight
=
1 / n_select
```

cho mỗi mã được chọn.

---

### 9.4.6. `UNIVERSE_TOO_SMALL`

`Combined` hiện chịu:

```text
n_min = 10
```

Nếu:

```text
N_candidates < n_min
```

thì code không tạo một target mới theo top 30%.

Trạng thái:

```text
UNIVERSE_TOO_SMALL
```

Engine target khi đó tuân theo Q6:

```text
giữ các mã hiện tại
nếu mã đó vẫn nằm trong candidate set

và

bán các mã đã rời candidate set
```

Không tự chọn thêm mã chỉ để đủ số lượng.

---

## 9.5. STRATEGY 2 — Market-only

Market-only chỉ sử dụng Market state và Market signal để lựa chọn/xếp hạng cổ phiếu.

Strategy này không sử dụng:

```text
Financial eligibility
Financial allowed / leading cluster
Financial PIT
ROE
F-score
Z-score
Financial score
Financial ranking
Combined score
```

để tạo Target Portfolio.

Các giá trị chi tiết dưới đây mô tả proposal/implementation Git hiện tại. Những thành phần còn thuộc decision queue chỉ trở thành official methodology sau khi decision tương ứng được khóa.

### 9.5.1. Tạo Market Candidate Universe

Theo implementation hiện tại:

```text
Market snapshot tại decision_date
↓
áp Market liquidity/eligibility rule của config hiện tại
↓
loại ILLIQUID theo proposal Q2 hiện tại
↓
xác định thứ tự Market clusters từ profile
↓
lấy Market allowed cluster theo market_rule
↓
Market-only Candidate Universe
```

Market cluster được order theo profile/rule trong implementation hiện tại, không theo numeric cluster label cố định.

Market-only không yêu cầu ticker phải có Financial B state.

Do đó:

```text
Bank
Securities
Insurance
```

vẫn có thể tham gia Market-only nếu thỏa Market-side universe rule.

Q2, exact cluster selector và các proposal liên quan vẫn phải tuân theo trạng thái decision tại Mục 38.

### 9.5.2. Ranking

Trong Market-only Candidate Universe, config PROPOSED hiện tại sử dụng Market criteria:

```text
mom_126
downside_vol_63
liquidity_21
```

với chiều hiện được cấu hình:

```text
mom_126
→ higher is better

downside_vol_63
→ lower is better

liquidity_21
→ higher is better
```

Không có Financial criteria.

Có thể hiểu về cấu trúc:

```text
Market-only Score
=
Market component
```

Implementation hiện tại gọi cùng ranking framework với:

```text
weight_market = 1.0
```

hoặc semantic tương đương.

Các criteria/tie rule chỉ trở thành official methodology khi decision/config tương ứng được khóa.

### 9.5.3. Chọn Target Portfolio

Với:

```text
N_candidates
```

nếu strategy đủ điều kiện tạo target theo rule/config cuối cùng:

```text
n_select
=
ceil(
    0.30 × N_candidates
)
```

Chọn top:

```text
n_select
```

mã theo Market-only ranking.

Mỗi mã được chọn có:

```text
target_weight
=
1 / n_select
```

Market-only không được bổ sung Financial-eligible ticker hoặc mã thay thế chỉ để tăng Candidate Universe.

### 9.5.4. UNIVERSE_TOO_SMALL

Trong config/code PROPOSED hiện tại, Market-only đi qua `_finish()` và sử dụng:

```text
n_min = 10
```

Nếu:

```text
N_candidates < n_min
```

thì implementation hiện tại trả:

```text
status = UNIVERSE_TOO_SMALL
```

và áp dụng keep-current logic của Q6:

```text
mã đang nắm
+
vẫn còn trong Market Candidate Universe
→ giữ

mã đã rời Market Candidate Universe
→ SELL

candidate mới
→ không BUY
```

Tuy nhiên:

```text
n_min = 10
```

và exact Q6 behavior vẫn là proposal cho tới khi được owner/mentor khóa.

Không được dùng Financial eligibility để tăng hoặc giảm Market-only Candidate Universe.

---

## 9.6. STRATEGY 3 — Financial-only

`Financial-only` chỉ sử dụng Financial signal để lựa chọn/xếp hạng cổ phiếu.

Tuy nhiên nó vẫn cần Market snapshot để xác nhận mã tồn tại trong universe giao dịch và áp dụng liquidity rule.

Nó không sử dụng:

```text
Market leading cluster
```

như một điều kiện chọn mã.

Nó cũng không sử dụng:

```text
mom_126
downside_vol_63
liquidity_21
```

để tính ranking.

---

### 9.6.1. Financial Eligible Pool

Luồng:

```text
Market snapshot tại decision_date
↓
áp dụng liquidity / tradable universe rule
↓
Financial PIT
↓
Financial eligibility
↓
Financial allowed cluster
↓
Financial-only Candidate Universe
```

Ở nhánh này, code cho phép toàn bộ Market clusters thay vì chỉ Market leading cluster.

Do đó về khái niệm:

```text
không hỏi:

mã có nằm trong Market leading cluster không?

mà hỏi:

mã có đủ điều kiện giao dịch
và nằm trong Financial Eligible Pool không?
```

---

### 9.6.2. Financial ranking

Các criteria được dùng:

```text
ROE
F-score
Z-score
```

Không có Market criteria.

Có thể hiểu:

```text
Financial-only Score
=
Financial component
```

Trong implementation:

```text
weight_market = 0.0
```

---

### 9.6.3. Chọn Target Portfolio

Nếu:

```text
N_candidates >= n_min
```

thì:

```text
n_select
=
ceil(
    0.30 × N_candidates
)
```

chọn top `n_select` theo Financial score.

Mỗi mã:

```text
target_weight
=
1 / n_select
```

---

### 9.6.4. `UNIVERSE_TOO_SMALL`

`Financial-only` đi qua `_finish()` nên hiện cũng chịu:

```text
n_min = 10
```

Nếu Candidate Universe nhỏ hơn 10:

```text
status
=
UNIVERSE_TOO_SMALL
```

và áp dụng Q6 keep-current logic.

---

## 9.7. STRATEGY 4 — Equal-weight

Equal-weight là đối chứng đơn giản trên traded universe.

Strategy không sử dụng:

```text
Financial eligibility
Financial PIT
Financial signal
Financial cluster selection
Market leading cluster
Market ranking
Financial ranking
mom_126 ranking
top 30%
```

### 9.7.1. Chọn danh sách mã

Tại mỗi decision_date:

```text
traded universe
↓
lấy toàn bộ ticker hợp lệ
↓
Equal-weight Target Universe
```

Không yêu cầu:

```text
Financial B label
Financial PIT state
Financial sector coverage
```

Bank / Securities / Insurance vẫn được giữ nếu thuộc traded universe.

Nếu có:

```text
N_eligible
```

mã thì toàn bộ `N_eligible` mã được đưa vào Target Portfolio.

### 9.7.2. Target weight

Mỗi mã:

```text
target_weight
=
1 / N_eligible
```

Ví dụ:

```text
N_eligible = 100
```

thì mỗi mã:

```text
1%
```

rank trong output nếu tồn tại chỉ là deterministic output ordering, không mang ý nghĩa chất lượng hay ưu tiên đầu tư.

### 9.7.3. n_min

Equal-weight không tự áp dụng n_min chỉ vì Combined/Market-only/Financial-only sử dụng n_min.

Nếu strategy contract/config hiện hành không có n_min:

```text
UNIVERSE_TOO_SMALL
```

không được tự bổ sung cho Equal-weight.

---

## 9.8. STRATEGY 5 — Momentum-only

Momentum-only chỉ sử dụng mom_126 để xếp hạng cổ phiếu.

Không sử dụng:

```text
Financial eligibility
Financial PIT
Financial allowed / leading cluster
ROE
F-score
Z-score
Financial score
Financial ranking
Combined ranking
```

### 9.8.1. Tạo Momentum Candidate Universe

Tại decision_date:

```text
traded universe
↓
loại ticker không có mom_126 hợp lệ
↓
Momentum Candidate Universe
```

Điều kiện:

```text
ticker thuộc traded universe

AND

mom_126 is not None
```

Không yêu cầu Financial B label.

Do đó Bank / Securities / Insurance vẫn có thể tham gia nếu thỏa traded-universe rule và có mom_126.

### 9.8.2. Momentum ranking

Các mã được sort theo:

```text
mom_126
```

từ cao xuống thấp.

Tie-break phải sử dụng exact rule/config đã khóa.

Không dùng:

```text
downside_vol_63
liquidity_21
ROE
F-score
Z-score
```

để tính Momentum-only ranking, trừ khi một decision mới thay đổi strategy definition.

### 9.8.3. Chọn top 30%

Với `N_momentum` mã trong Momentum Candidate Universe:

```text
n_select
=
ceil(
    0.30 × N_momentum
)
```

Chọn các mã có mom_126 cao nhất.

Target weight:

```text
target_weight
=
1 / n_select
```

### 9.8.4. n_min

Momentum-only không tự áp n_min nếu strategy contract/config hiện hành không quy định.

Không tự thêm:

```text
UNIVERSE_TOO_SMALL
```

theo logic của Combined/Market-only/Financial-only nếu Q14/Q6 không yêu cầu.

---

## 9.9. So sánh trực tiếp cách tạo Target của 5 strategy

Các strategy bắt đầu từ universe riêng:

```text
                           decision_date
                                 │
          ┌──────────────┬───────┼───────────────┬───────────────┐
          │              │       │               │               │
          ▼              ▼       ▼               ▼               ▼
      COMBINED       MARKET-ONLY FINANCIAL-ONLY EQUAL-WEIGHT MOMENTUM-ONLY
          │              │       │               │               │
 Market Eligible     Market     Financial      traded          traded
      ∩              Eligible   Eligible        universe        universe
 Financial Eligible   Pool       ∩                              +
                                  traded                        mom_126
          │              │       │               │               │
          ▼              ▼       ▼               ▼               ▼
       MC + FC           MC      FC            no rank        mom_126
        ranking        ranking  ranking            │            ranking
          │              │       │                 │               │
       Top 30%         Top 30% Top 30%         lấy tất cả      Top 30%
          │              │       │                 │               │
          └──────────────┴───────┴─────────────────┴───────────────┘
                                 ↓
                            Equal Weight
```

Điểm quan trọng:

```text
không có một Financial eligibility gate chung
áp trước cả 5 strategy
```

Mỗi strategy phải sử dụng đúng universe definition của chính nó.

Sau khi Target Portfolio riêng được tạo:

```text
cả 5 strategy
↓
cùng execution/backtest engine
```

---

## 9.10. Điểm mà 5 strategy bắt đầu dùng chung logic

Sau khi Bước 1 tạo được:

```text
Target Portfolio
```

thì cách lựa chọn cổ phiếu kết thúc.

Từ thời điểm này:

```text
Combined
Market-only
Financial-only
Equal-weight
Momentum-only
```

đều được đưa vào:

```text
cùng engine
```

ở Bước 2.

Tức:

```text
Target Portfolio riêng
↓
execution_date
↓
revalue Current Portfolio
↓
Current vs Target
↓
delta_weight
↓
SELL
↓
BUY
↓
HOLD
↓
BUY_FAILED / SELL_FAILED
↓
execution_scale
↓
Actual Holdings
↓
NAV
```

Logic execution phía sau không được thay đổi theo strategy.

---

## 9.11. Output canonical của Bước 1

Runner tạo riêng:

```text
targets_combined.csv
targets_market_only.csv
targets_financial_only.csv
targets_equal_weight.csv
targets_momentum_only.csv
```

Schema chung:

```text
decision_date
ticker
rank
target_weight
candidates
status
```

Trong đó:

- `decision_date`: ngày strategy ra quyết định;
- `ticker`: ticker được chọn;
- `rank`: thứ hạng/output ordering của strategy;
- `target_weight`: trọng số mục tiêu;
- `candidates`: số mã trong universe tương ứng của strategy;
- `status`: trạng thái strategy tại kỳ.

```text
candidates
```

không có cùng semantic giữa năm strategy.

Cụ thể:

```text
Combined
→ số mã trong:
  Market Eligible Pool
  ∩
  Financial Eligible Pool
  sau các selection rule tương ứng

Market-only
→ số mã trong Market-only Candidate Universe
  sau Market eligibility/cluster selection

Financial-only
→ số mã trong:
  Financial Eligible Pool
  ∩
  traded universe
  sau Financial selection

Equal-weight
→ số mã trong traded universe

Momentum-only
→ số mã trong traded universe
  có mom_126 hợp lệ
```

Không dùng Financial coverage count để định nghĩa candidates của Market-only, Equal-weight hoặc Momentum-only.

---

## 9.12. `--targets-only` khi config chưa LOCKED

Config Git hiện tại vẫn:

```text
status = PROPOSED
```

Runner Git cho phép chạy:

```text
python scripts/run_m3.py
--segment development
--targets-only
```

khi config vẫn `PROPOSED`.

Mục đích của `--targets-only` là kiểm tra hành vi của proposal/config hiện tại trước khi mở official backtest có return.

Targets-only có thể kiểm tra:

```text
PIT
strategy-specific universe
eligibility
candidate count
ranking
picks
target_weight
UNIVERSE_TOO_SMALL
```

và tạo:

```text
targets_combined.csv
targets_market_only.csv
targets_financial_only.csv
targets_equal_weight.csv
targets_momentum_only.csv
manifest.json
```

Việc targets-only chạy được không có nghĩa các proposal trong config đã trở thành `LOCKED` decision.

Kết quả targets-only phải được hiểu là:

```text
behavior của current PROPOSED implementation
```

chứ không phải:

```text
official historical backtest
```

Khi config chưa `LOCKED`, không được tính/report:

```text
strategy NAV
portfolio return
turnover từ official backtest
performance metrics của strategy
VNINDEX comparison dùng làm kết luận backtest
```

Full backtest có return chỉ được phép khi:

```text
status = LOCKED
```

và các readiness gate liên quan đã `PASS`.

---

## 9.13. Tóm tắt Bước 1

Có thể hiểu Bước 1:

```text
                       DECISION DATE
                            │
           ┌────────────────┼─────────────────┐
           │                │                 │
     Strategy-specific eligibility / universe
                            │
       ┌───────────┬────────┼────────┬─────────────┐
       │           │        │        │             │
       ▼           ▼        ▼        ▼             ▼
   Combined   Market-only Financial-only Equal-weight Momentum-only
       │           │        │        │             │
 Market+Fin      Market   Financial  no rank       mom_126
   ranking       ranking   ranking      │           ranking
       │           │        │           │             │
    top30%      top30%    top30%     lấy tất cả    top30%
       │           │        │           │             │
       ▼           ▼        ▼           ▼             ▼
   Target A    Target B   Target C    Target D      Target E
       └───────────┴────────┴───────────┴─────────────┘
                            ↓
                  CÙNG BACKTEST ENGINE
```

Điểm cần giữ:

```text
Combined
≠ Market-only
≠ Financial-only
≠ Equal-weight
≠ Momentum-only
```

không chỉ ở signal/ranking mà còn có thể khác nhau ở universe definition.

Nguyên tắc:

```text
strategy-specific universe
↓
strategy-specific signal / ranking
↓
strategy-specific Target Portfolio
↓
cùng execution engine
```

Sau Target Portfolio:

```text
cả 5
→ cùng execution framework
→ cùng BUY / SELL / HOLD framework
→ cùng failed-trade framework
→ cùng valuation framework
```

trừ khi strategy contract cụ thể có decision khác.

---

# 10. BƯỚC 2 — GIẢ LẬP MUA/BÁN THEO ENGINE GITHUB

## 10.1. Map `decision_date` sang `execution_date`

Rule đã khóa:

```text
execution_date = phiên giao dịch hợp lệ đầu tiên sau decision_date
```

Runner dùng trading calendar và `bisect_right`, do đó bắt buộc:

```text
execution_date > decision_date
```

## 10.2. Revalue Current Portfolio trước rebalance

Portfolio state gồm:

```text
cash
values[ticker]
marks[ticker]
```

Trong đó:

```text
cash
= số tiền mặt hiện đang có trong danh mục

values[ticker]
= giá trị hiện tại của phần vốn đang nắm giữ ở từng mã cổ phiếu

marks[ticker]
= mức giá gần nhất đã được dùng để định giá mã cổ phiếu đó
```

Tại `execution_date`, cập nhật lại giá trị của từng mã đang nắm giữ trước khi thực hiện giao dịch:

```text
nếu current_price hợp lệ:

    values[ticker]
    *=
    current_price / marks[ticker]

    marks[ticker]
    =
    current_price

nếu current_price is None:

    values[ticker] giữ nguyên
    marks[ticker] giữ nguyên
    ghi nhận PRICE_STALE
```

Như vậy missing price không tự biến return thành 0; engine giữ nguyên giá trị đang được mark bằng giá hợp lệ gần nhất cho tới khi có giá mới hợp lệ.

Tính `pre_trade_NAV` sau khi revalue:

```text
pre_trade_NAV
=
cash
+
Σ values[ticker]
```

NAV này là giá trị danh mục ngay trước rebalance.

`pre_weight` của từng ticker được tính:

```text
pre_weight_i
=
values[ticker_i] / pre_trade_NAV
```

Đối với Cash:

```text
cash_weight
=
cash / pre_trade_NAV
```


## 10.3. Current-vs-Target

Với union của mã đang nắm và mã trong target:

```text
delta_weight_i = target_weight_i - pre_weight_i
```

- `delta < -EPS` → SELL;
- `delta > EPS` → BUY;
- `|delta| <= EPS` và mã còn trong target → HOLD.

Với EPS = 1e-12, là một ngưỡng kỹ thuật cực nhỏ
để tránh giao dịch do sai số tính toán. 

## 10.4. Tính delta_weight và xác định SELL / BUY / HOLD

Với mỗi ticker:
```
delta_weight_i
=
target_weight_i - pre_weight_i
```
SELL nếu:
```
delta_weight_i < -EPS
```
thì:
```
side = SELL
```
Giá trị SELL dự kiến:
```
intended_sell_value_i
=
-delta_weight_i × pre_trade_NAV
```
Ví dụ:
```
pre_weight_FPT = 40%

target_weight_FPT = 30%

delta_weight_FPT = -10%

pre_trade_NAV = 100 triệu đồng
```
thì:
```
intended_sell_value_FPT
= 10 triệu đồng
```

BUY nếu:
```
delta_weight_i > EPS
```
thì:
```
side = BUY
```
Giá trị BUY dự kiến:
```
intended_buy_value_i
=
delta_weight_i × pre_trade_NAV
```

HOLD nếu:
```
|delta_weight_i| <= EPS
và ticker vẫn nằm trong Target:
```
thì:
```
side = HOLD
intended = 0
executed = 0
status = HOLD
```
Cần phân biệt:
```
pre_weight
target_weight
delta_weight
→ đơn vị tỷ trọng
```
và:
```
intended
executed
→ giá trị trong value space của Portfolio
```

## 10.5. Kiểm tra executability và thực hiện rebalance

### 10.5.1. Điều kiện executable

Một BUY hoặc SELL executable khi:

```text
tradable(ticker, execution_date, side) = True
AND
price(ticker, execution_date) is not None
```

Theo PriceBook hiện hành, tradability kiểm tra:
1. có adjusted price hợp lệ;
2. volume > 0;
3. BUY không ở/tại trên giá trần;
4. SELL không ở/tại dưới giá sàn.

### 10.5.2. Thực hiện SELL trước

Engine xử lý toàn bộ SELL trước BUY.

Với mỗi SELL:

```text
intended_sell_value
=
-delta_weight × pre_trade_NAV
```

Nếu executable:

```text
values[ticker]
-=
intended_sell_value

cash
+=
intended_sell_value

executed
=
intended_sell_value

status
=
EXECUTED
```

Nếu sau SELL:

```text
values[ticker] <= EPS × pre_trade_NAV
```

thì:

```text
xóa ticker khỏi values
xóa marks[ticker]
```

Nếu SELL không executable:

```text
values[ticker] giữ nguyên
cash không tăng
executed = 0
status = SELL_FAILED
```

SELL_FAILED không giải phóng vốn.


### 10.5.3. Xác định Cash thực tế sau SELL

Sau khi xử lý hết SELL:

```text
available_cash
=
Cash thực tế trong Portfolio
```

Nếu có SELL_FAILED:

```text
available_cash
<
Cash dự kiến nếu mọi SELL thành công
```

Engine không dùng margin và không giả định vốn từ SELL_FAILED đã được giải phóng.

### 10.5.4. Kiểm tra BUY

Với mỗi BUY:

```text
intended_buy_value
=
delta_weight × pre_trade_NAV
```

Nếu BUY không executable:
- executed = 0
- status = BUY_FAILED

BUY_FAILED:
- không làm giảm Cash
- không tạo position mới
- không chọn ticker khác thay thế

Chỉ BUY executable mới được tính vào:

```text
required_buy_cash
=
Σ intended_buy_value
của các BUY executable
```

### 10.5.5. Proportional scaling

Nếu:

```text
required_buy_cash <= available_cash
```

thì:

```text
execution_scale = 1
```

Nếu:

```text
required_buy_cash > available_cash
```

thì:

```text
execution_scale
=
available_cash / required_buy_cash
```

Tổng quát:

```text
execution_scale
=
min(
    1,
    available_cash / required_buy_cash
)
```

Tất cả BUY executable dùng cùng một execution_scale.

### 10.5.6. Thực hiện BUY

Với mỗi BUY executable:

```text
executed_buy_value
=
intended_buy_value × execution_scale
```

Sau execution:

```text
cash
-=
executed_buy_value
```

Nếu ticker chưa tồn tại:

```text
values[ticker]
=
executed_buy_value

marks[ticker]
=
price(ticker, execution_date)
```

Nếu ticker đã tồn tại:

```text
values[ticker]
+=
executed_buy_value
```

Nếu:

```text
execution_scale = 1
```

thì:

```text
status = EXECUTED
```

Nếu:

```text
execution_scale < 1
```

thì:

```text
status = SCALED
```


### 10.5.7. HOLD

HOLD không phát sinh giao dịch:

```text
intended = 0
executed = 0
status = HOLD
```

Do đó:
- không thay đổi position
- không thay đổi Cash
- không tạo turnover

### 10.5.8. Missing price theo từng ngữ cảnh

Cần phân biệt:

**VALUATION tại 12.2:**
```text
price is None
→ PRICE_STALE
→ giữ last valid valuation
```

**SELL tại 12.5:**
```text
price is None / non-tradable
→ SELL_FAILED
```

**BUY tại 12.5:**
```text
price is None / non-tradable
→ BUY_FAILED
```

## 10.6. SELL_FAILED và proportional scaling

SELL_FAILED không làm Cash giảm trực tiếp, nhưng ngăn vốn trong vị thế được chuyển thành Cash.

Với các BUY còn lại có thể thực hiện:

```text
required_buy_cash = Σ intended_buy_value của BUY hợp lệ
execution_scale = min(1, available_cash / required_buy_cash)
```

Mỗi BUY hợp lệ:

```text
executed_buy_value = intended_buy_value × execution_scale
```

Nếu `execution_scale < 1`, status của BUY là `SCALED`.

Một SELL_FAILED có thể tồn tại nhiều kỳ nếu mỗi kỳ Target vẫn muốn giảm/bỏ mã đó nhưng mỗi lệnh SELL mới tiếp tục thất bại. **Không carry lệnh SELL cũ**; mỗi kỳ sinh action mới từ Current-vs-Target.

## 10.7. Output canonical Bước 2

### A. `trade_ledger_<strategy>.csv`

Schema canonical theo engine GitHub:

```text
date
ticker
side
pre_weight
target_weight
intended
executed
scale
status
```

Trong đó `date` là `execution_date`.

Status tối thiểu:

```text
EXECUTED
BUY_FAILED
SELL_FAILED
SCALED
HOLD
```

Không tạo `failed_executions.csv`; failed trade được lọc trực tiếp từ `status`.

### B. `holdings_<strategy>.csv`

Schema theo implementation GitHub hiện hành:

```text
date
ticker
weight
```

Ý nghĩa:

- mỗi row phản ánh tỷ trọng Actual Holdings ngay sau rebalance;
- `CASH` là một row;
- đối với cổ phiếu, `weight` được tính từ `values[ticker] / NAV`;
- đối với `CASH`, `weight = cash / NAV`;
- tổng weight phải xấp xỉ 1 theo tolerance;
- giá trị tuyệt đối của vị thế vẫn tồn tại trong internal Portfolio state thông qua `pf.values` và `pf.cash`, nhưng không được persist thành field `position_value` trong `holdings_<strategy>.csv` theo Git hiện hành.

### C. `turnover_<strategy>.csv`

Schema theo GitHub:

```text
date
turnover
```

Công thức:

```text
traded
=
executed_buy_value + executed_sell_value

turnover
=
traded / (2 × pre_trade_NAV)
```

Đây là one-way turnover theo owner decision hiện hành.

Failed/HOLD có:

```text
executed = 0
```

nên không đóng góp turnover.

---

# 11. BƯỚC 3 — HOLDING PERIOD

Sau khi Bước 2 của kỳ hiện tại hoàn tất, Portfolio thực tế được giữ trong engine cho tới execution_date của kỳ kế tiếp.

Bước 3 không phải một hàm xử lý độc lập trong code.

Luồng:

```text
Actual Holdings sau rebalance kỳ t
↓
giữ Portfolio state trong RAM
↓
không rebalance giữa kỳ
↓
đến execution_date kỳ t+1
↓
quay lại Bước 2 kỳ t+1
↓
12.2 revalue Current Portfolio
```

## 11.1. Portfolio state được carry sang kỳ kế tiếp

Sau rebalance kỳ t, engine giữ:

```text
cash
values[ticker]
marks[ticker]
```

Portfolio này không được reset về Cash.

Không tạo lại portfolio mới ở kỳ kế tiếp.

## 11.2. Trong holding period

Trong khoảng thời gian từ:
- `execution_date` kỳ t
- đến `execution_date` kỳ t+1

engine hiện tại:
- không revalue từng ngày;
- không tính NAV từng ngày;
- không tính weight từng ngày;
- không rebalance giữa kỳ;
- không kiểm tra missing price từng ngày.

Portfolio state chỉ được giữ trong bộ nhớ.

## 11.3. Weight drift trong holding period

Trong thực tế, giá các cổ phiếu có thể thay đổi trong thời gian nắm giữ.

Do đó tỷ trọng kinh tế của các mã có thể lệch khỏi tỷ trọng ngay sau rebalance.

Ví dụ sau rebalance:
- FPT = 50%
- VNM = 50%

Trong holding period:
- FPT tăng giá
- VNM giảm giá

thì tỷ trọng thực tế có thể drift thành:
- FPT > 50%
- VNM < 50%

Tuy nhiên engine không cập nhật weight liên tục trong holding period.

Weight drift chỉ được phản ánh khi tới execution_date của kỳ kế tiếp và Mục 10.2 thực hiện revalue().

## 11.4. Kết thúc holding period tại kỳ kế tiếp

Khi tới:

- `execution_date` kỳ t+1

Bước 3 của kỳ t kết thúc.

Engine quay lại Bước 2 của kỳ t+1.

Tại Mục 10.2:

```text
revalue Current Portfolio
↓
cập nhật values[ticker]
↓
cập nhật marks[ticker] khi có giá hợp lệ
↓
xử lý PRICE_STALE nếu thiếu giá
↓
tính pre_trade_NAV
↓
append NAV
```

Sau đó tại Mục 10.3:

```text
pre_weight_i
=
values[ticker_i] / pre_trade_NAV
```

Đối với Cash:

```text
cash_weight
=
cash / pre_trade_NAV
```

rồi mới tiếp tục:

```text
target_weight
↓
delta_weight
↓
SELL / BUY / HOLD
```

Do đó:

```text
NAV cuối holding period kỳ t
=
pre_trade_NAV trước rebalance kỳ t+1
```

Đây là cùng một NAV tại cùng một thời điểm, không phải hai phép tính riêng.

## 11.5. Kỳ cuối của segment

Nếu không còn kỳ rebalance kế tiếp, runner sử dụng:
- `end_date`

để chốt valuation cuối cùng.
```
end_date = phiên giao dịch hợp lệ cuối cùng nằm trong segment.

Không lấy execution_date của decision thuộc segment kế tiếp
để định giá segment hiện tại.
```

Tại end_date:

```text
revalue Current Portfolio
↓
PRICE_STALE nếu thiếu giá
↓
tính NAV cuối segment
↓
append NAV
```

Sau đó:
- không rebalance
- không tính delta
- không BUY
- không SELL

Vì vậy `end_date` chỉ dùng để chốt giá trị cuối danh mục.

---

# 12. BƯỚC 4 — CHUYỂN SANG KỲ TIẾP THEO VÀ LẶP LẠI CHU TRÌNH

Bước 4 được giữ trong kế hoạch để thể hiện rõ **backtest là một vòng lặp qua nhiều kỳ**.

Bước 4 **không phải một hàm xử lý độc lập trong code**. Sau khi kỳ hiện tại hoàn tất, engine không reset danh mục và không tạo một Portfolio mới. Trạng thái Portfolio hiện tại tiếp tục được giữ trong cùng object để sử dụng cho kỳ tiếp theo.

Luồng khái niệm:

```text
Kỳ t

Bước 1
→ tạo Target Portfolio kỳ t

Bước 2
→ revalue Current Portfolio
→ rebalance
→ Actual Holdings kỳ t

Bước 3
→ giữ danh mục

↓
sang kỳ t+1

Bước 4
→ chuyển sang kỳ tiếp theo
→ quay lại Bước 1

Bước 1 kỳ t+1
→ tạo Target Portfolio mới

Bước 2 kỳ t+1
→ revalue Current Portfolio
→ Current-vs-Target
→ rebalance

Bước 3 kỳ t+1
→ tiếp tục nắm giữ

↓
lặp lại cho tới hết segment
```

---

## 12.1. Portfolio state được giữ nguyên khi chuyển kỳ

Sau Bước 2 của kỳ `t`, engine đang giữ:

```text
cash
values[ticker]
marks[ticker]
```

Các giá trị này tiếp tục tồn tại khi vòng lặp chuyển sang kỳ kế tiếp.

Không thực hiện:

```text
- reset Portfolio về 100% Cash;
- tạo Portfolio mới;
- khôi phục lại Target của kỳ trước;
- tạo file handoff riêng giữa hai kỳ.
```

Do đó không tạo:

```text
rebalance_cycle_handoff.csv
```

Portfolio state trong RAM chính là trạng thái được chuyển tiếp sang kỳ kế tiếp.

---

## 12.2. Tại `decision_date` của kỳ tiếp theo, quay lại Bước 1

Khi tới `decision_date` của kỳ `t+1`, chu trình quay lại:

```text
BƯỚC 1 — CHỌN CỔ PHIẾU
```

Strategy sử dụng cùng methodology, config và các rule đã khóa để tính lại Target Portfolio của kỳ mới.

```text
Market state tại decision_date t+1
+
Financial state hợp lệ theo PIT tại decision_date t+1
↓
Candidate Universe mới
↓
ranking mới
↓
top 30% mới
↓
Target Portfolio kỳ t+1
```

Target kỳ mới được tính độc lập từ thông tin hợp lệ tại `decision_date` mới.

Không carry Target hoặc action của kỳ trước.

Ví dụ:

```text
Kỳ t:
VCB target = 0%
SELL VCB → SELL_FAILED
```

VCB vẫn còn trong Current Portfolio.

Đến kỳ `t+1`, Bước 1 tính lại Target:

```text
Trường hợp A:
target_weight_VCB = 0%
→ kỳ mới vẫn muốn loại VCB

Trường hợp B:
target_weight_VCB = 25%
→ kỳ mới lại muốn nắm giữ VCB
```

Action của kỳ `t+1` chỉ được xác định sau khi Current Portfolio mới được so với Target mới.

---

## 12.3. Tại `execution_date` của kỳ tiếp theo, quay lại Bước 2

Sau khi Bước 1 đã tạo Target Portfolio kỳ `t+1`, tới:

```text
execution_date kỳ t+1
```

engine thực hiện lại:

```text
BƯỚC 2 — GIẢ LẬP MUA/BÁN
```

Đầu tiên, thực hiện:

```text
Current Portfolio từ kỳ trước
↓
revalue theo giá tại execution_date kỳ t+1
↓
PRICE_STALE nếu thiếu giá
↓
tính pre_trade_NAV
```

Sau đó:

```text
tính pre_weight
+
Target Portfolio kỳ t+1
↓
delta_weight
↓
SELL / BUY / HOLD
↓
rebalance
↓
Actual Holdings kỳ t+1
```

Như vậy:

```text
Actual Holdings kỳ t
```

không được dùng trực tiếp như một Target mới.

Nó chỉ là:

```text
Current Portfolio đầu vào
```

cho kỳ tiếp theo.

---

## 12.4. Không carry lệnh giao dịch cũ sang kỳ mới

Các action:

```text
BUY
SELL
HOLD
BUY_FAILED
SELL_FAILED
SCALED
```

chỉ thuộc về rebalance của kỳ đã sinh ra chúng.

Sang kỳ mới:

```text
không carry BUY cũ
không carry SELL cũ
không tự retry một order cũ
```

Thay vào đó:

```text
Current Portfolio mới
+
Target Portfolio mới
↓
tính lại delta_weight
↓
sinh action mới
```

Ví dụ:

```text
Kỳ t:
VCB cần SELL
→ SELL_FAILED
→ VCB vẫn còn trong danh mục
```

Kỳ `t+1`:

```text
Target mới vẫn muốn VCB = 0
↓
Current Portfolio vẫn có VCB
↓
delta_weight < 0
↓
sinh một SELL mới
```

Nếu SELL mới tiếp tục không executable:

```text
→ SELL_FAILED mới
```

Đây không phải lệnh cũ được carry sang.

---

## 12.5. Chu trình tiếp tục cho tới kỳ cuối của segment

Vòng lặp nghiệp vụ:

```text
Bước 1 — Chọn cổ phiếu
↓
Bước 2 — Revalue + rebalance
↓
Bước 3 — Nắm giữ
↓
Bước 4 — Chuyển sang kỳ tiếp theo
↓
quay lại Bước 1
```

được lặp cho toàn bộ lịch của segment.

Ví dụ:

```text
kỳ 1
→ kỳ 2
→ kỳ 3
→ ...
→ kỳ cuối
```

Trong code, việc chuyển kỳ xảy ra tự nhiên khi vòng lặp `schedule` chuyển sang phần tử kế tiếp; không có hàm `step4()` hoặc `carry_portfolio()` riêng.

---

## 12.6. Trường hợp kết thúc segment/run

Khi runner đi tới điểm kết thúc của một segment/run, toàn bộ việc xác định kỳ cuối, xử lý end_date, chốt Actual Holdings và NAV cuối segment phải thực hiện theo Quy tắc 3.9 — Quy tắc kết thúc segment/run.

Sau khi toàn bộ segment hoàn tất, runner mới tiếp tục phần tổng hợp kết quả, metrics và benchmark theo output contract của M3.

---

# 13. CHẠY 4 BƯỚC TRÊN DEVELOPMENT VÀ HOLDOUT HIỆN HÀNH

## Development

```text
2019-01-31 → 2023-12-29
60 decision snapshots
```

Chạy cùng frozen config/engine. Sharpe không được báo cáo.

## Holdout

```text
2024-01-31 → 2025-12-31
24 decision snapshots
```

Chỉ chạy bằng đúng rule đã khóa trước khi mở Holdout. Sharpe không được báo cáo.

Tuy nhiên, upstream clustering model A/B đã từng được đánh giá
trên dữ liệu bao gồm giai đoạn 2024–2025 trước khi M3-A chạy.

Vì vậy Holdout phải được mô tả là:
- tách biệt đối với portfolio-rule evaluation;
- không dùng để tune strategy dựa trên return;
- nhưng không được mô tả là hoàn toàn unseen đối với toàn bộ
  quá trình lựa chọn upstream clustering model.

Final Evaluation sau 31/12/2025 là lớp đánh giá tiếp theo
sau khi strategy đã được freeze.

Mỗi segment có run directory độc lập:

```text
data/experiments/m3/<segment>/<run_id>/
```
60 và 24 là decision snapshot count, không đồng nghĩa mọi target đều có execution trong segment:
```
decision_count = số decision snapshots
execution_count = số decision có execution_date hợp lệ trong cùng segment
valuation_end_date = phiên giao dịch cuối cùng của segment
```
---

# 14. CÁC STRATEGY ĐƯỢC CHẠY TRONG CÙNG OUTPUT CONTRACT

## 14.1. Combined — chiến lược chính

Universe:

```text
Market Eligible Pool
∩
Financial Eligible Pool
```

Sử dụng Market + Financial signal/ranking theo config đã khóa.

Nếu đủ điều kiện, chọn top 30% và phân bổ equal weight.

## 14.2. Market-only — đối chứng

Universe:

```text
Market Eligible Pool
```

Chỉ sử dụng Market signal/ranking.

Không yêu cầu Financial eligibility hoặc Financial B coverage.

Nếu đủ điều kiện, chọn top 30% và phân bổ equal weight.

## 14.3. Financial-only — đối chứng

Universe:

```text
Financial Eligible Pool
∩
traded universe
```

Chỉ sử dụng Financial signal/ranking.

Không sử dụng Market leading cluster làm điều kiện lựa chọn.

Nếu đủ điều kiện, chọn top 30% và phân bổ equal weight.

## 14.4. Equal-weight — đối chứng

Universe:

```text
traded universe
```

Không sử dụng Market/Financial ranking.

Không chọn top 30%.

Toàn bộ universe được phân bổ equal weight.

## 14.5. Momentum-only — đối chứng

Universe:

```text
traded universe
∩
mom_126 hợp lệ
```

Ranking:

```text
mom_126
```

Chọn top 30% và phân bổ equal weight.

Không yêu cầu Financial eligibility hoặc Financial B coverage.

Tên strategy từ config được dùng trực tiếp trong output suffix.

VNINDEX là benchmark chính thức, không phải strategy.


# 15. VÍ DỤ MINH HỌA CHI TIẾT QUA 3 KỲ

Ví dụ này chỉ minh họa mechanics của backtest, không phải kết quả nghiên cứu thật.

Đơn vị của:

```text
cash
values[ticker]
intended
executed
NAV
```

trong ví dụ là:

```text
triệu đồng
```

Để dễ tính toán, giả sử danh mục ban đầu có:

```text
cash = 100 triệu đồng
```

Trong code thật, engine khởi tạo:

```text
cash = 1.0
```

Việc dùng `100 triệu đồng` chỉ giúp minh họa dễ đọc hơn; tỷ trọng và logic không thay đổi.

---

## 1. Lịch 3 kỳ

```text
Kỳ 1:
decision_date  = 31/01/2024
execution_date = 01/02/2024

Kỳ 2:
decision_date  = 29/02/2024
execution_date = 01/03/2024

Kỳ 3:
decision_date  = 29/03/2024
execution_date = 01/04/2024

end_date = 29/04/2024
```

Trong cả ba kỳ, giả sử sau khi thực hiện Market–Financial PIT và eligibility:

```text
N_candidates = 11
```

Do đó:

```text
n_select
=
ceil(0.30 × 11)
=
4
```

Vì danh mục phân bổ equal-weight:

```text
target_weight
=
1 / 4
=
25%
```

Mỗi kỳ Target Portfolio chính thức gồm đúng:

```text
4 mã
×
25%
```

---

# KỲ 1

# BƯỚC 1 — CHỌN CỔ PHIẾU

## 1.1. Financial PIT

Ví dụ FPT có:

```text
FY2022:
usable_from_date = 15/03/2023

FY2023:
usable_from_date = 20/02/2024
```

Tại:

```text
decision_date = 31/01/2024
```

ta có:

```text
15/03/2023 <= 31/01/2024

20/02/2024 > 31/01/2024
```

Vì vậy:

```text
usable_financial_years
=
{2022}
```

và:

```text
selected_fiscal_year
=
2022
```

FY2023 chưa được sử dụng vì tại `decision_date` nó chưa đạt `usable_from_date`.

Giả sử CTG không có bất kỳ fiscal year nào thỏa:

```text
usable_from_date <= decision_date
```

thì:

```text
CTG
→ FINANCIAL_NOT_AVAILABLE
```

và CTG không thể đi vào Financial Eligible Pool ở kỳ này.

---

## 1.2. Candidate Universe

Giả sử:

```text
Market Eligible Pool
=
{
 FPT, HPG, MWG, VNM, VCB, SSI,
 GAS, VIC, STB, MSN, VRE,
 CTG, DGC
}
```

Financial Eligible Pool:

```text
{
 FPT, HPG, MWG, VNM, VCB, SSI,
 GAS, VIC, STB, MSN, VRE,
 SAB
}
```

Candidate Universe:

```text
Candidate Universe
=
Market Eligible Pool
∩
Financial Eligible Pool
```

suy ra:

```text
{
 FPT,
 HPG,
 MWG,
 VNM,
 VCB,
 SSI,
 GAS,
 VIC,
 STB,
 MSN,
 VRE
}
```

Do đó:

```text
N_candidates = 11
```

---

## 1.3. Combined Ranking

Do công thức MC1–MC3, FC1–FC3 và Combined Ranking vẫn phải được khóa riêng, ví dụ này không tự đặt công thức.

Giả sử sau khi chạy rule chính thức, kết quả ranking là:

| rank | ticker |
|---:|---|
| 1 | FPT |
| 2 | HPG |
| 3 | MWG |
| 4 | VCB |
| 5 | VNM |
| 6 | SSI |
| 7 | GAS |
| 8 | VIC |
| 9 | STB |
| 10 | MSN |
| 11 | VRE |

Số mã chọn:

```text
n_select
=
ceil(0.30 × 11)
=
4
```

Mỗi mã:

```text
target_weight
=
1 / 4
=
0.25
=
25%
```

Target Portfolio kỳ 1:

| decision_date | ticker | rank | target_weight | candidates | status |
|---|---|---:|---:|---:|---|
| 31/01/2024 | FPT | 1 | 0.25 | 11 | OK |
| 31/01/2024 | HPG | 2 | 0.25 | 11 | OK |
| 31/01/2024 | MWG | 3 | 0.25 | 11 | OK |
| 31/01/2024 | VCB | 4 | 0.25 | 11 | OK |

---

# BƯỚC 2 — GIẢ LẬP MUA/BÁN KỲ 1

## 2.1. Portfolio ban đầu

Trước execution đầu tiên:

```text
cash = 100

values = {}

marks = {}
```

Do chưa có cổ phiếu:

```text
revalue()
→ không có ticker nào để cập nhật
```

Vì vậy:

```text
pre_trade_NAV = 100
```

Pre-weight:

```text
pre_weight_FPT = 0
pre_weight_HPG = 0
pre_weight_MWG = 0
pre_weight_VCB = 0
```

---

## 2.2. Giá tại 01/02/2024

Giả sử:

| ticker | current_price | volume | Trạng thái | BUY executable? |
|---|---:|---:|---|---|
| FPT | 100 | > 0 | bình thường | Có |
| HPG | 50 | > 0 | bình thường | Có |
| MWG | 40 | > 0 | đóng cửa tại giá trần | Không |
| VCB | 80 | > 0 | bình thường | Có |

MWG vẫn có price nhưng:

```text
BUY MWG
→ không executable do giá trần
→ BUY_FAILED
```

---

## 2.3. Current-vs-Target

### FPT

```text
target_weight_FPT
=
25%

pre_weight_FPT
=
0%
```

Do đó:

```text
delta_weight_FPT
=
25% - 0%
=
+25%
```

Vì:

```text
delta_weight_FPT > 0
```

nên:

```text
side = BUY
```

Giá trị BUY dự kiến:

```text
intended_buy_value_FPT
=
delta_weight_FPT × pre_trade_NAV
```

```text
=
25% × 100
=
25 triệu
```

Tương tự:

```text
intended_buy_value_HPG = 25
intended_buy_value_MWG = 25
intended_buy_value_VCB = 25
```

---

## 2.4. Kiểm tra BUY

MWG không executable.

Do đó chỉ các BUY executable được tính vào:

```text
required_buy_cash
=
25 FPT
+
25 HPG
+
25 VCB
=
75
```

Trong khi:

```text
available_cash = 100
```

Do đó:

```text
execution_scale
=
min(
    1,
    available_cash / required_buy_cash
)
```

```text
=
min(
    1,
    100 / 75
)
=
1
```

Không cần scaling.

---

## 2.5. Execution kỳ 1

| ticker | side | pre_weight | target_weight | intended | executed | scale | status |
|---|---|---:|---:|---:|---:|---:|---|
| FPT | BUY | 0 | 0.25 | 25 | 25 | 1 | EXECUTED |
| HPG | BUY | 0 | 0.25 | 25 | 25 | 1 | EXECUTED |
| MWG | BUY | 0 | 0.25 | 25 | 0 | 1 | BUY_FAILED |
| VCB | BUY | 0 | 0.25 | 25 | 25 | 1 | EXECUTED |

Portfolio sau giao dịch:

```text
values[FPT] = 25
marks[FPT]  = 100

values[HPG] = 25
marks[HPG]  = 50

values[VCB] = 25
marks[VCB]  = 80

cash = 25
```

MWG:

```text
không tạo values[MWG]
không tạo marks[MWG]
```

vì BUY thất bại.

---

## 2.6. Actual Holdings kỳ 1

Theo schema GitHub hiện hành, `holdings_<strategy>.csv` chỉ persist:

```text
date
ticker
weight
```

Output holdings tại `execution_date = 01/02/2024`:

| date | ticker | weight |
|---|---|---:|
| 01/02/2024 | FPT | 25% |
| 01/02/2024 | HPG | 25% |
| 01/02/2024 | VCB | 25% |
| 01/02/2024 | CASH | 25% |

Giá trị tuyệt đối của các vị thế vẫn được engine giữ trong internal Portfolio state qua `values[ticker]` và `cash`; chúng không được persist thành field riêng trong holdings output.

Mặc dù Target muốn MWG 25%, Actual Portfolio giữ:

```text
25% Cash
```

do:

```text
MWG BUY_FAILED
```

---

## 2.7. Turnover kỳ 1

Executed BUY:

```text
FPT = 25
HPG = 25
VCB = 25
```

Tổng:

```text
traded
=
75
```

Turnover:

```text
turnover
=
75 / (2 × 100)
=
0.375
=
37.5%
```

---

# BƯỚC 3 — HOLDING PERIOD KỲ 1

Sau rebalance:

```text
cash = 25

values:
FPT = 25
HPG = 25
VCB = 25

marks:
FPT = 100
HPG = 50
VCB = 80
```

Trong holding period:

```text
không revalue mỗi ngày
không tính NAV mỗi ngày
không tính weight mỗi ngày
không rebalance giữa kỳ
không kiểm tra missing price mỗi ngày
```

Portfolio state chỉ được giữ trong RAM.

---

# BƯỚC 4 — CHUYỂN SANG KỲ 2

Không tạo Portfolio mới.

Không reset:

```text
cash
values
marks
```

MWG từng:

```text
BUY_FAILED
```

nhưng lệnh BUY cũ không được carry sang kỳ 2.

Kỳ 2 quay lại Bước 1 và tạo Target mới.

---

# KỲ 2

# BƯỚC 1 — TARGET MỚI

Tại:

```text
decision_date = 29/02/2024
```

FY2023 của FPT đã đạt:

```text
usable_from_date = 20/02/2024
```

vì:

```text
20/02/2024 <= 29/02/2024
```

nên:

```text
usable_financial_years
=
{2022, 2023}
```

và:

```text
selected_fiscal_year
=
2023
```

Như vậy Financial state của cùng một mã có thể thay đổi giữa hai kỳ theo PIT.

---

## Ranking kỳ 2

Giả sử Candidate Universe vẫn có:

```text
11 mã
```

Ranking mới:

| rank | ticker |
|---:|---|
| 1 | FPT |
| 2 | MWG |
| 3 | VNM |
| 4 | SSI |
| 5 | HPG |
| 6 | VCB |
| 7 | GAS |
| 8 | VIC |
| 9 | STB |
| 10 | MSN |
| 11 | VRE |

Target kỳ 2:

```text
FPT = 25%
MWG = 25%
VNM = 25%
SSI = 25%
```

HPG và VCB không còn trong Target:

```text
target_weight_HPG = 0
target_weight_VCB = 0
```

---

# BƯỚC 2 — REVALUE KỲ 2

Ngày:

```text
execution_date = 01/03/2024
```

Giả sử:

```text
FPT current_price = 120
HPG current_price = None
VCB current_price = 88
```

---

## FPT

Trước đó:

```text
values[FPT] = 25
marks[FPT] = 100
```

Revalue:

```text
values[FPT]
=
25 × 120 / 100
=
30
```

Sau đó:

```text
marks[FPT] = 120
```

---

## HPG — missing price

```text
current_price = None
```

Do đó:

```text
values[HPG] giữ nguyên = 25

marks[HPG] giữ nguyên = 50

ghi nhận:
PRICE_STALE(01/03/2024, HPG)
```

Không đặt:

```text
values[HPG] = 0
```

---

## VCB

```text
values[VCB]
=
25 × 88 / 80
=
27.5
```

Sau đó:

```text
marks[VCB] = 88
```

---

## Cash

```text
cash = 25
```

---

## pre_trade_NAV kỳ 2

```text
pre_trade_NAV
=
30
+
25
+
27.5
+
25
=
107.5
```

Do đó:

```text
NAV = 107.5 triệu đồng
```

---

# PRE_WEIGHT KỲ 2

FPT:

```text
pre_weight_FPT
=
30 / 107.5
≈
27.9070%
```

HPG:

```text
pre_weight_HPG
=
25 / 107.5
≈
23.2558%
```

VCB:

```text
pre_weight_VCB
=
27.5 / 107.5
≈
25.5814%
```

Cash:

```text
25 / 107.5
≈
23.2558%
```

Đây là weight drift so với Actual Holdings ngay sau kỳ 1.

---

# CURRENT VS TARGET KỲ 2

Engine không cần tạo một biến trung gian chứa giá trị tiền mục tiêu tuyệt đối.

Mỗi action được xác định trực tiếp từ:

```text
delta_weight_i
=
target_weight_i - pre_weight_i
```

Sau đó:

```text
BUY:
intended_buy_value_i
=
delta_weight_i × pre_trade_NAV
```

hoặc:

```text
SELL:
intended_sell_value_i
=
-delta_weight_i × pre_trade_NAV
```

---

## FPT — SELL bớt

```text
target_weight_FPT
=
25%

pre_weight_FPT
≈
27.9070%
```

Do đó:

```text
delta_weight_FPT
=
25% - 27.9070%
≈
-2.9070%
```

Vì:

```text
delta_weight_FPT < 0
```

nên:

```text
side = SELL
```

Giá trị SELL dự kiến:

```text
intended_sell_value_FPT
=
-delta_weight_FPT × pre_trade_NAV
```

```text
≈
2.9070% × 107.5
=
3.125 triệu
```

---

## HPG — SELL toàn bộ

```text
target_weight_HPG = 0%

pre_weight_HPG
≈
23.2558%
```

Do đó:

```text
delta_weight_HPG
=
0% - 23.2558%
=
-23.2558%
```

```text
intended_sell_value_HPG
=
-delta_weight_HPG × pre_trade_NAV
```

```text
≈
23.2558% × 107.5
=
25 triệu
```

---

## VCB — SELL toàn bộ

```text
target_weight_VCB
=
0%

pre_weight_VCB
≈
25.5814%
```

```text
delta_weight_VCB
=
0% - 25.5814%
=
-25.5814%
```

Do đó:

```text
intended_sell_value_VCB
=
-delta_weight_VCB × pre_trade_NAV
```

```text
≈
25.5814% × 107.5
=
27.5 triệu
```

---

## MWG — BUY

```text
pre_weight_MWG = 0%

target_weight_MWG = 25%
```

```text
delta_weight_MWG
=
25% - 0%
=
+25%
```

Do đó:

```text
intended_buy_value_MWG
=
delta_weight_MWG × pre_trade_NAV
```

```text
=
25% × 107.5
=
26.875 triệu
```

---

## VNM — BUY

```text
pre_weight_VNM = 0%

target_weight_VNM = 25%
```

```text
delta_weight_VNM = +25%
```

Do đó:

```text
intended_buy_value_VNM
=
25% × 107.5
=
26.875 triệu
```

---

## SSI — BUY

```text
pre_weight_SSI = 0%

target_weight_SSI = 25%
```

```text
delta_weight_SSI = +25%
```

Do đó:

```text
intended_buy_value_SSI
=
25% × 107.5
=
26.875 triệu
```

---

# SELL ĐƯỢC THỰC HIỆN TRƯỚC

## FPT

Giả sử SELL executable:

```text
executed_sell_value_FPT
=
3.125
```

```text
status = EXECUTED
```

Sau SELL:

```text
values[FPT]
=
30 - 3.125
=
26.875
```

Cash:

```text
cash
=
25 + 3.125
=
28.125
```

---

## HPG

HPG không có valid price:

```text
price(HPG, 01/03/2024)
=
None
```

Do đó:

```text
SELL_FAILED
```

```text
executed = 0
```

HPG vẫn:

```text
values[HPG] = 25
marks[HPG] = 50
```

Cash không nhận được 25 triệu dự kiến.

---

## VCB

Giả sử SELL executable:

```text
executed_sell_value_VCB
=
27.5
```

```text
status = EXECUTED
```

VCB bị bán hết:

```text
xóa values[VCB]

xóa marks[VCB]
```

Cash trở thành:

```text
cash
=
28.125 + 27.5
=
55.625
```

---

# BUY VÀ PROPORTIONAL SCALING KỲ 2

Ba BUY đều executable:

```text
intended_buy_value_MWG = 26.875

intended_buy_value_VNM = 26.875

intended_buy_value_SSI = 26.875
```

Tổng:

```text
required_buy_cash
=
26.875
+
26.875
+
26.875
=
80.625
```

Nhưng:

```text
available_cash
=
55.625
```

Do:

```text
HPG SELL_FAILED
```

không giải phóng 25 triệu Cash.

Do đó:

```text
execution_scale
=
available_cash / required_buy_cash
```

```text
=
55.625 / 80.625
≈
0.689922
```

Mỗi BUY executable:

```text
executed_buy_value
=
intended_buy_value × execution_scale
```

MWG:

```text
executed_buy_value_MWG
=
26.875 × 0.689922
≈
18.541667
```

VNM:

```text
executed_buy_value_VNM
≈
18.541667
```

SSI:

```text
executed_buy_value_SSI
≈
18.541667
```

---

# LEDGER KỲ 2

| ticker | side | pre_weight | target_weight | intended | executed | scale | status |
|---|---|---:|---:|---:|---:|---:|---|
| FPT | SELL | 27.9070% | 25% | 3.125 | 3.125 | 1 | EXECUTED |
| HPG | SELL | 23.2558% | 0% | 25 | 0 | 1 | SELL_FAILED |
| VCB | SELL | 25.5814% | 0% | 27.5 | 27.5 | 1 | EXECUTED |
| MWG | BUY | 0% | 25% | 26.875 | 18.541667 | 0.689922 | SCALED |
| VNM | BUY | 0% | 25% | 26.875 | 18.541667 | 0.689922 | SCALED |
| SSI | BUY | 0% | 25% | 26.875 | 18.541667 | 0.689922 | SCALED |

---

# ACTUAL HOLDINGS KỲ 2

Theo schema GitHub hiện hành, output holdings tại `execution_date = 01/03/2024` là:

| date | ticker | weight |
|---|---|---:|
| 01/03/2024 | FPT | 25.0000% |
| 01/03/2024 | HPG | 23.2558% |
| 01/03/2024 | MWG | 17.2481% |
| 01/03/2024 | VNM | 17.2481% |
| 01/03/2024 | SSI | 17.2481% |
| 01/03/2024 | CASH | 0% |

Internal Portfolio state tương ứng vẫn giữ:

```text
values[FPT] = 26.875000
values[HPG] = 25.000000
values[MWG] = 18.541667
values[VNM] = 18.541667
values[SSI] = 18.541667
cash = 0
```

NAV tại thời điểm này:

```text
107.5 triệu
```

Actual Portfolio khác Target vì:

```text
HPG SELL_FAILED
+
BUY bị proportional scaling
```

---

# TURNOVER KỲ 2

Executed SELL:

```text
FPT = 3.125
VCB = 27.5
```

Tổng:

```text
executed_sell_value
=
30.625
```

Executed BUY:

```text
MWG = 18.541667
VNM = 18.541667
SSI = 18.541667
```

Tổng:

```text
executed_buy_value
=
55.625
```

Do đó:

```text
traded
=
30.625
+
55.625
=
86.25
```

Turnover:

```text
turnover
=
86.25 / (2 × 107.5)
≈
0.401163
=
40.1163%
```

HPG không đóng góp turnover vì:

```text
SELL_FAILED
executed = 0
```

---

# BƯỚC 3 — HOLDING PERIOD KỲ 2

State được carry:

```text
cash = 0

values:
FPT = 26.875
HPG = 25
MWG = 18.541667
VNM = 18.541667
SSI = 18.541667

marks:
FPT = 120
HPG = 50
MWG = 40
VNM = 80
SSI = 30
```

HPG vẫn:

```text
marks[HPG] = 50
```

vì tại kỳ 2 không có giá mới hợp lệ.

---

# BƯỚC 4 — CHUYỂN SANG KỲ 3

Kỳ 2:

```text
SELL HPG
→ SELL_FAILED
```

Nhưng engine không carry lệnh SELL cũ sang kỳ 3.

Kỳ 3 quay lại Bước 1 và tạo Target mới.

---

# KỲ 3

# BƯỚC 1 — TARGET MỚI

Giả sử Candidate Universe tiếp tục có:

```text
11 mã
```

Ranking:

| rank | ticker |
|---:|---|
| 1 | FPT |
| 2 | HPG |
| 3 | MWG |
| 4 | VCB |
| 5 | VNM |
| 6 | SSI |
| 7 | GAS |
| 8 | VIC |
| 9 | STB |
| 10 | MSN |
| 11 | VRE |

Target kỳ 3:

```text
FPT = 25%
HPG = 25%
MWG = 25%
VCB = 25%
```

Kỳ trước:

```text
HPG target = 0
→ SELL_FAILED
```

Nhưng kỳ này:

```text
HPG target = 25%
```

Do đó engine không tự retry SELL cũ.

Action mới phải được tính lại từ:

```text
Current Portfolio
vs
Target Portfolio mới
```

---

# BƯỚC 2 — REVALUE KỲ 3

Tại:

```text
execution_date = 01/04/2024
```

giả sử:

```text
FPT:
marks = 120
current_price = 120

HPG:
marks = 50
current_price = 55

MWG:
marks = 40
current_price = 40

VNM:
marks = 80
current_price = 80

SSI:
marks = 30
current_price = 30
```

---

## FPT

```text
values[FPT]
=
26.875 × 120 / 120
=
26.875
```

```text
marks[FPT] = 120
```

---

## HPG — giá xuất hiện trở lại sau PRICE_STALE

Trước đó:

```text
marks[HPG] = 50
```

Tại `execution_date` kỳ 3:

```text
current_price_HPG = 55
```

Do đó:

```text
values[HPG]
=
25 × 55 / 50
=
27.5
```

Sau đó:

```text
marks[HPG] = 55
```

Biến động từ last valid mark `50` đến giá mới `55` được phản ánh tại lần revalue này.

---

## MWG

```text
values[MWG]
=
18.541667 × 40 / 40
=
18.541667
```

```text
marks[MWG] = 40
```

---

## VNM

```text
values[VNM]
=
18.541667 × 80 / 80
=
18.541667
```

---

## SSI

```text
values[SSI]
=
18.541667 × 30 / 30
=
18.541667
```

---

# pre_trade_NAV KỲ 3

```text
pre_trade_NAV
=
26.875
+
27.5
+
18.541667
+
18.541667
+
18.541667
=
110
```

Do đó:

```text
NAV = 110 triệu
```

---

# PRE_WEIGHT KỲ 3

FPT:

```text
pre_weight_FPT
=
26.875 / 110
≈
24.4318%
```

HPG:

```text
pre_weight_HPG
=
27.5 / 110
=
25%
```

MWG:

```text
pre_weight_MWG
=
18.541667 / 110
≈
16.8561%
```

VNM:

```text
pre_weight_VNM
≈
16.8561%
```

SSI:

```text
pre_weight_SSI
≈
16.8561%
```

VCB:

```text
pre_weight_VCB
=
0%
```

---

# CURRENT VS TARGET KỲ 3

Target:

```text
FPT = 25%
HPG = 25%
MWG = 25%
VCB = 25%

VNM = 0%
SSI = 0%
```

Engine tiếp tục dùng:

```text
delta_weight_i
=
target_weight_i - pre_weight_i
```

---

## HPG — HOLD

```text
target_weight_HPG
=
25%

pre_weight_HPG
=
25%
```

Do đó:

```text
delta_weight_HPG
=
25% - 25%
=
0
```

Vì:

```text
|delta_weight_HPG| <= EPS
```

và HPG vẫn nằm trong Target:

```text
side = HOLD

intended = 0

executed = 0

status = HOLD
```

Điều này cũng minh họa:

```text
Kỳ 2:
HPG → SELL_FAILED

Kỳ 3:
HPG → HOLD
```

Lệnh SELL cũ không được carry sang.

---

## FPT — BUY thêm

```text
target_weight_FPT
=
25%

pre_weight_FPT
≈
24.4318%
```

Do đó:

```text
delta_weight_FPT
=
25% - 24.4318%
≈
+0.5682%
```

Vì:

```text
delta_weight_FPT > 0
```

nên:

```text
side = BUY
```

Giá trị BUY dự kiến:

```text
intended_buy_value_FPT
=
delta_weight_FPT × pre_trade_NAV
```

```text
≈
0.5682% × 110
=
0.625 triệu
```

---

## MWG — BUY thêm

```text
target_weight_MWG
=
25%

pre_weight_MWG
≈
16.8561%
```

Do đó:

```text
delta_weight_MWG
=
25% - 16.8561%
≈
+8.1439%
```

Giá trị BUY dự kiến:

```text
intended_buy_value_MWG
=
delta_weight_MWG × pre_trade_NAV
```

```text
≈
8.1439% × 110
=
8.958333 triệu
```

---

## VNM — SELL toàn bộ

```text
target_weight_VNM
=
0%

pre_weight_VNM
≈
16.8561%
```

Do đó:

```text
delta_weight_VNM
=
0% - 16.8561%
=
-16.8561%
```

Giá trị SELL dự kiến:

```text
intended_sell_value_VNM
=
-delta_weight_VNM × pre_trade_NAV
```

```text
≈
16.8561% × 110
=
18.541667 triệu
```

Giả sử SELL executable:

```text
executed
=
18.541667

status
=
EXECUTED
```

VNM bị bán hết:

```text
xóa values[VNM]

xóa marks[VNM]
```

---

## SSI — SELL nhưng không executable

```text
target_weight_SSI
=
0%

pre_weight_SSI
≈
16.8561%
```

```text
delta_weight_SSI
=
0% - 16.8561%
=
-16.8561%
```

Do đó:

```text
intended_sell_value_SSI
=
-delta_weight_SSI × pre_trade_NAV
```

```text
≈
16.8561% × 110
=
18.541667 triệu
```

Giả sử tại `execution_date`:

```text
price hợp lệ

volume > 0

raw_close = floor
```

SELL không executable:

```text
executed = 0

status = SELL_FAILED
```

SSI vẫn:

```text
values[SSI]
=
18.541667
```

---

## VCB — BUY mới

VCB hiện không nằm trong danh mục:

```text
pre_weight_VCB
=
0%
```

Target:

```text
target_weight_VCB
=
25%
```

Do đó:

```text
delta_weight_VCB
=
25% - 0%
=
+25%
```

Giá trị BUY dự kiến:

```text
intended_buy_value_VCB
=
delta_weight_VCB × pre_trade_NAV
```

```text
=
25% × 110
=
27.5 triệu
```

Giả sử VCB executable.

---

# SELL ĐƯỢC THỰC HIỆN TRƯỚC

VNM SELL thành công:

```text
cash
=
18.541667
```

SSI:

```text
SELL_FAILED
```

nên không tạo thêm Cash.

Do đó:

```text
available_cash
=
18.541667
```

---

# PROPORTIONAL SCALING KỲ 3

Các BUY executable:

```text
intended_buy_value_FPT
=
0.625

intended_buy_value_MWG
=
8.958333

intended_buy_value_VCB
=
27.5
```

Do đó:

```text
required_buy_cash
=
0.625
+
8.958333
+
27.5
=
37.083333
```

Trong khi:

```text
available_cash
=
18.541667
```

Nên:

```text
execution_scale
=
available_cash / required_buy_cash
```

```text
=
18.541667 / 37.083333
=
0.5
```

Tất cả BUY executable dùng chung:

```text
execution_scale = 0.5
```

---

## FPT

```text
executed_buy_value_FPT
=
intended_buy_value_FPT × execution_scale
```

```text
=
0.625 × 0.5
=
0.3125
```

Sau BUY:

```text
values[FPT]
=
26.875 + 0.3125
=
27.1875
```

---

## MWG

```text
executed_buy_value_MWG
=
8.958333 × 0.5
=
4.479167
```

Sau BUY:

```text
values[MWG]
=
18.541667 + 4.479167
=
23.020834
```

---

## VCB

```text
executed_buy_value_VCB
=
27.5 × 0.5
=
13.75
```

VCB chưa tồn tại trong Portfolio trước BUY này.

Giả sử tại:

```text
execution_date = 01/04/2024
```

giá VCB mà `price()` trả về là:

```text
current_price_VCB
=
price(VCB, 01/04/2024)
=
100
```

Do đó sau BUY:

```text
values[VCB]
=
13.75
```

và:

```text
marks[VCB]
=
current_price_VCB
=
100
```

`marks[VCB] = 100` trở thành giá gần nhất dùng để định giá VCB cho lần `revalue()` tiếp theo.

---

# LEDGER KỲ 3

| ticker | side | pre_weight | target_weight | intended | executed | scale | status |
|---|---|---:|---:|---:|---:|---:|---|
| VNM | SELL | 16.8561% | 0% | 18.541667 | 18.541667 | 1 | EXECUTED |
| SSI | SELL | 16.8561% | 0% | 18.541667 | 0 | 1 | SELL_FAILED |
| HPG | HOLD | 25% | 25% | 0 | 0 | 1 | HOLD |
| FPT | BUY | 24.4318% | 25% | 0.625 | 0.3125 | 0.5 | SCALED |
| MWG | BUY | 16.8561% | 25% | 8.958333 | 4.479167 | 0.5 | SCALED |
| VCB | BUY | 0% | 25% | 27.5 | 13.75 | 0.5 | SCALED |

---

# ACTUAL HOLDINGS SAU KỲ 3

Theo schema GitHub hiện hành, output holdings tại `execution_date = 01/04/2024` là:

| date | ticker | weight |
|---|---|---:|
| 01/04/2024 | FPT | 24.7159% |
| 01/04/2024 | HPG | 25.0000% |
| 01/04/2024 | MWG | 20.9280% |
| 01/04/2024 | SSI | 16.8561% |
| 01/04/2024 | VCB | 12.5000% |
| 01/04/2024 | CASH | 0% |

Internal Portfolio state tương ứng vẫn giữ:

```text
values[FPT] = 27.187500
values[HPG] = 27.500000
values[MWG] = 23.020833
values[SSI] = 18.541667
values[VCB] = 13.750000
cash = 0
```

NAV tại thời điểm này:

```text
110 triệu
```

Tổng weight:

```text
100%
```

Actual Holdings vẫn khác Target do:

```text
SSI SELL_FAILED
+
các BUY bị proportional scaling
```

---

# TURNOVER KỲ 3

Executed SELL:

```text
VNM
=
18.541667
```

SSI:

```text
SELL_FAILED

executed = 0
```

Executed BUY:

```text
FPT = 0.3125

MWG = 4.479167

VCB = 13.75
```

Tổng BUY:

```text
18.541667
```

Tổng:

```text
traded
=
18.541667
+
18.541667
=
37.083334
```

Turnover:

```text
turnover
=
37.083334 / (2 × 110)
≈
0.168561
=
16.8561%
```

---

# BƯỚC 3 — HOLDING PERIOD SAU KỲ 3

Portfolio state:

```text
cash = 0

values:
FPT = 27.1875
HPG = 27.5
MWG = 23.020833
SSI = 18.541667
VCB = 13.75

marks:
FPT = 120
HPG = 55
MWG = 40
SSI = 30
VCB = 100
```

Không còn kỳ rebalance thứ tư trong ví dụ.

Danh mục được giữ tới:

```text
end_date = 29/04/2024
```

---

# END_DATE — CHỐT NAV CUỐI

Giả sử tại:

```text
end_date = 29/04/2024
```

có:

| ticker | marks hiện tại | current_price |
|---|---:|---:|
| FPT | 120 | 132 |
| HPG | 55 | `None` |
| MWG | 40 | 44 |
| SSI | 30 | 27 |
| VCB | 100 | 105 |

---

## FPT

```text
values[FPT]
=
27.1875 × 132 / 120
=
29.90625
```

Sau đó:

```text
marks[FPT] = 132
```

---

## HPG — missing price tại end_date

```text
current_price
=
None
```

Do đó:

```text
values[HPG] giữ nguyên
=
27.5
```

```text
marks[HPG] giữ nguyên
=
55
```

Ghi nhận:

```text
PRICE_STALE(29/04/2024, HPG)
```

---

## MWG

```text
values[MWG]
=
23.020833 × 44 / 40
≈
25.322917
```

Sau đó:

```text
marks[MWG] = 44
```

---

## SSI

```text
values[SSI]
=
18.541667 × 27 / 30
=
16.6875
```

Sau đó:

```text
marks[SSI] = 27
```

---

## VCB

Lần BUY đầu tiên kỳ 3 đã lưu:

```text
marks[VCB] = 100
```

Tại `end_date`:

```text
current_price_VCB = 105
```

Do đó:

```text
values[VCB]
=
13.75 × 105 / 100
=
14.4375
```

Sau đó:

```text
marks[VCB] = 105
```

---

# NAV CUỐI

```text
NAV_end
=
29.90625
+
27.5
+
25.322917
+
16.6875
+
14.4375
```

suy ra:

```text
NAV_end
≈
113.854167 triệu đồng
```

Tại `end_date`:

```text
không tạo Target mới

không tính delta_weight

không BUY

không SELL

không rebalance

không tạo turnover mới

không tạo holdings sau rebalance mới
```

Chỉ thực hiện:

```text
revalue
↓
PRICE_STALE nếu thiếu giá
↓
tính NAV cuối
↓
append NAV
```

---

# NAV XUYÊN SUỐT 3 KỲ

`nav_<strategy>.csv`:

| date | nav |
|---|---:|
| 01/02/2024 | 100.000000 |
| 01/03/2024 | 107.500000 |
| 01/04/2024 | 110.000000 |
| 29/04/2024 | 113.854167 |

Lợi suất có thể được suy từ chuỗi NAV:

```text
01/02 → 01/03:

107.5 / 100 - 1
=
+7.50%
```

```text
01/03 → 01/04:

110 / 107.5 - 1
≈
+2.3256%
```

```text
01/04 → 29/04:

113.854167 / 110 - 1
≈
+3.5038%
```

Engine không tính return hằng ngày trong holding period.

---

# TỔNG HỢP CÁC TRƯỜNG HỢP ĐÃ MINH HỌA

| Trường hợp | Kỳ | Kết quả |
|---|---|---|
| `N_candidates = 11` | Cả 3 kỳ | `ceil(30% × 11) = 4` |
| Equal-weight allocation của Target minh họa | Cả 3 kỳ | 4 mã × 25% |
| Financial PIT | Kỳ 1 → 2 | FPT chuyển FY2022 → FY2023 khi `usable_from_date` cho phép |
| `FINANCIAL_NOT_AVAILABLE` | Kỳ 1 | CTG không vào Financial Eligible Pool |
| Portfolio ban đầu 100% Cash | Kỳ 1 | `revalue()` không có ticker để xử lý |
| BUY thành công | Kỳ 1 | FPT, HPG, VCB |
| BUY_FAILED do giá trần | Kỳ 1 | MWG |
| BUY_FAILED giữ Cash | Kỳ 1 | 25 triệu còn ở Cash |
| Weight drift | Kỳ 2 | FPT từ 25% → khoảng 27.907% |
| `PRICE_STALE` | Kỳ 2 | HPG thiếu giá |
| Giữ last valid mark | Kỳ 2 | `marks[HPG] = 50` |
| SELL một phần | Kỳ 2 | FPT có `intended_sell_value = 3.125` |
| SELL toàn bộ thành công | Kỳ 2 | VCB bị xóa khỏi `values/marks` |
| SELL_FAILED do thiếu price | Kỳ 2 | HPG |
| SELL_FAILED làm thiếu Cash | Kỳ 2 | Không nhận được 25 triệu từ HPG |
| Proportional scaling | Kỳ 2 | MWG/VNM/SSI cùng scale ≈ 0.689922 |
| Giá xuất hiện lại sau stale | Kỳ 3 | HPG được revalue từ mark 50 → 55 |
| Không carry action cũ | Kỳ 3 | HPG từ SELL_FAILED → HOLD |
| HOLD | Kỳ 3 | HPG có `delta_weight = 0` |
| SELL toàn bộ thành công | Kỳ 3 | VNM |
| SELL_FAILED do giá sàn | Kỳ 3 | SSI |
| Nhiều BUY cùng scale | Kỳ 3 | FPT/MWG/VCB cùng scale = 0.5 |
| Position mới | Kỳ 3 | `values[VCB]=13.75`, `marks[VCB]=current_price tại execution_date` |
| Portfolio không reset | Cả 3 kỳ | `cash`, `values`, `marks` được carry |
| Missing price tại `end_date` | Cuối kỳ 3 | HPG tiếp tục `PRICE_STALE` |
| `end_date` không rebalance | Cuối kỳ 3 | Chỉ revalue + append NAV |
| Failed/HOLD không tạo turnover | Cả 3 kỳ | `executed = 0` nên không đi vào `traded` |

---

# TÓM TẮT VÒNG LẶP

```text
KỲ 1

Bước 1
→ 11 candidates
→ top 4
→ FPT / HPG / MWG / VCB
→ mỗi mã 25%

Bước 2
→ BUY FPT
→ BUY HPG
→ MWG BUY_FAILED
→ BUY VCB

Bước 3
→ giữ FPT + HPG + VCB + Cash

Bước 4
→ sang kỳ 2
        ↓

KỲ 2

Bước 1
→ 11 candidates
→ FPT / MWG / VNM / SSI

Bước 2
→ revalue
→ FPT weight drift
→ HPG PRICE_STALE
→ FPT SELL một phần
→ HPG SELL_FAILED
→ VCB SELL toàn bộ
→ MWG / VNM / SSI BUY bị SCALED

Bước 3
→ giữ Actual Portfolio

Bước 4
→ sang kỳ 3
        ↓

KỲ 3

Bước 1
→ 11 candidates
→ FPT / HPG / MWG / VCB

Bước 2
→ revalue
→ HPG có giá trở lại
→ HPG HOLD
→ VNM SELL thành công
→ SSI SELL_FAILED
→ FPT / MWG / VCB BUY bị SCALED
→ VCB là position mới
→ marks[VCB] lấy current_price tại execution_date

Bước 3
→ giữ Actual Portfolio tới end_date

Bước 4
→ không còn kỳ tiếp theo
→ revalue tại end_date
→ HPG PRICE_STALE
→ append NAV cuối
→ kết thúc segment
```

---

# 16. SCHEMA CANONICAL M3-A THEO OUTPUT GITHUB

## 16.1. `targets_<strategy>.csv`

```text
decision_date
ticker
rank
target_weight
candidates
status
```

Trả lời: strategy **muốn nắm gì** tại decision date?

## 16.2. `trade_ledger_<strategy>.csv`

```text
date
ticker
side
pre_weight
target_weight
intended
executed
scale
status
```

Trả lời: engine **muốn giao dịch gì và thực tế executed bao nhiêu**?

## 16.3. `holdings_<strategy>.csv`

```text
date
ticker
weight
```

Trả lời: sau rebalance thực tế portfolio có tỷ trọng như thế nào?
CASH là một row.

## 16.4. `turnover_<strategy>.csv`

```text
date
turnover
```

Với:

```text
turnover = (executed BUY + executed SELL) / (2 × pre_trade_NAV)
```

## 16.5. `nav_<strategy>.csv`

```text
date
nav
```

Trả lời: giá trị toàn portfolio thay đổi thế nào qua thời gian?

## 16.6. `benchmark_vnindex.csv`

```text
date
nav
```

VNINDEX được căn theo execution/evaluation dates tương ứng và chuẩn hóa NAV để so sánh.

## 16.7. `metrics.json`

Tối thiểu theo runner GitHub:

```text
periods
total_return
cagr
volatility_annual
max_drawdown
avg_turnover
avg_cash_after_trading
failed_buys
failed_sells
scaled_buys
price_stale
```

Ngoài ra có summary cho `vnindex` và số lỗi adjusted-price đã repair nếu module price ghi nhận.

Sharpe chỉ xuất khi segment nằm trong `sharpe_allowed_segments`, theo quyết định hiện tại là Final Evaluation.

## 16.8. `manifest.json`

`manifest.json` sử dụng schema theo implementation GitHub hiện hành.

Các trường hiện tại gồm:

```text
config
config_sha256
status
segment
run_id
targets_only
counts
```

Ý nghĩa:

```text
config
→ đường dẫn config được sử dụng cho run

config_sha256
→ SHA-256 của config

status
→ trạng thái config tại thời điểm chạy

segment
→ development / holdout / final

run_id
→ định danh của run

targets_only
→ xác định run chỉ tạo target hay chạy full backtest

counts
→ thống kê theo strategy của run
```

Không tự bổ sung field mới vào canonical manifest nếu implementation GitHub hiện hành chưa định nghĩa field đó.

Quan hệ giữa manifest và output:

```text
run
↓
run_id + segment + config
↓
canonical outputs
↓
manifest.json
```


## 16.9. Quan hệ giữa các output

```text
inputs + config + PIT + strategy
        ↓
targets_<strategy>.csv
        ↓
engine execution
        ↓
trade_ledger_<strategy>.csv
        ├──→ holdings_<strategy>.csv
        └──→ turnover_<strategy>.csv
                  ↓
         carry portfolio state
                  ↓
            nav_<strategy>.csv

VNINDEX
↓
benchmark_vnindex.csv

all outputs + run metadata
↓
metrics.json + manifest.json
```

---

# 17. BENCHMARK — VNINDEX

## 17.1. Vai trò

VNINDEX là benchmark chính thức hiện hành. Market-only, Financial-only, Equal-weight và Momentum-only là research controls, không phải benchmark.

## 17.2. Căn thời gian

VNINDEX phải được căn đúng các evaluation/execution dates của từng segment, không tạo gap legacy và không dùng ngày tương lai để thay cho quan sát thiếu.

## 17.3. Return basis

Q11 vẫn phải được khóa/certify. Nếu main portfolio dùng adjusted total-return proxy trong khi VNINDEX là price index thì báo cáo phải ghi rõ basis mismatch và, nếu proposal được duyệt, có secondary price-only scenario.

## 17.4. Output canonical

```text
benchmark_vnindex.csv
```

Schema:

```text
date
nav
```

Performance của VNINDEX được ghi vào `metrics.json` dưới key `vnindex`; không tạo `vnindex_benchmark_metrics.csv` hay `benchmark_comparison.csv` bắt buộc.

## 17.5. Metrics

Development/Holdout tối thiểu có thể báo cáo:

```text
Total/Cumulative Return
CAGR nếu hợp lệ
Annualized Volatility
Maximum Drawdown
Turnover (strategy only)
Cash ratio (strategy only)
failed execution counts (strategy only)
```

Các metric bổ sung chỉ dùng khi contract đủ điều kiện. Sharpe không dùng trong Development/Holdout; Final Evaluation mới được phép báo cáo Sharpe.

## 17.6. Final Evaluation

Chỉ mở khi dữ liệu sau `2025-12-31` pass readiness + unseen-status audit và exact window đã khóa trước khi xem performance.

# 18. SAU KHI CHẠY XONG 4 BƯỚC MỚI TÍNH PERFORMANCE

Đầu vào canonical:

```text
nav_<strategy>.csv
turnover_<strategy>.csv
holdings_<strategy>.csv
trade_ledger_<strategy>.csv
benchmark_vnindex.csv
```

Runner/reporting tạo `metrics.json` với tối thiểu:

```text
periods
total_return
cagr
volatility_annual
max_drawdown
avg_turnover
avg_cash_after_trading
failed_buys
failed_sells
scaled_buys
price_stale
```
Sharpe chỉ ở Final Evaluation.

Kịch bản chính có transaction cost = 0 và slippage = 0,
do đó gross return và net return của base scenario là tương đương.

Nếu chạy cost-sensitivity scenario, báo cáo phải phân biệt rõ:
- gross return trước chi phí;
- transaction cost / slippage;
- net return sau chi phí.

Cost-sensitivity chỉ là secondary reporting;
không overwrite base scenario và không được dùng để tune strategy.

---

# 19. CHECKLIST TOÀN BỘ M3-A THEO 4 BƯỚC

## Bước 1 — Chọn cổ phiếu

```text
[ ] Market input/version/hash validated
[ ] Financial input/version/hash validated
[ ] PIT rule frozen
[ ] Candidate rule frozen
[ ] MC1–MC3 frozen
[ ] FC1–FC3 frozen
[ ] Combined ranking/tie frozen
[ ] targets_<strategy>.csv created
```

## Bước 2 — Giả lập mua/bán

```text
[ ] execution_date > decision_date
[ ] execution_date phải nằm trong boundary của segment hiện tại
[ ] Current Portfolio revalued
[ ] Current-vs-Target calculated
[ ] SELL executed before BUY
[ ] missing price/non-tradable classified by GitHub semantics
[ ] BUY_FAILED / SELL_FAILED / SCALED handled
[ ] trade_ledger_<strategy>.csv created
[ ] holdings_<strategy>.csv có đúng schema date + ticker + weight
[ ] CASH được biểu diễn như một row trong holdings
[ ] turnover_<strategy>.csv uses / (2 × pre_trade_NAV)
```

## Bước 3 — Giữ và tính lời/lỗ

```text
[ ] portfolio state carried, not reset
[ ] missing valuation price uses stale mark
[ ] price_stale counted
[ ] NAV revalued at next execution/end date
[ ] nav_<strategy>.csv created
[ ] valuation_end_date phải nằm trong boundary của segment hiện tại
```

## Bước 4 — Tái cân bằng

```text
[ ] next Target recomputed with same frozen rules
[ ] no old action carried forward
[ ] weight drift enters next Current Portfolio
[ ] loop continues to segment end
```

## Segment boundary validation

```text
[ ] Development không sử dụng execution/valuation price sau 31/12/2023
[ ] Holdout không sử dụng execution/valuation price sau 31/12/2025
[ ] segment trước không sử dụng dữ liệu giá của segment kế tiếp để hoàn tất return
```

## Reproducibility

```text
[ ] benchmark_vnindex.csv created
[ ] metrics.json created
[ ] manifest.json được tạo đúng schema GitHub hiện hành
```


---

# PHẦN B — M3-B: DASHBOARD / PRODUCT LAYER

M3-B đưa các kết quả đã được upstream tạo và xác minh lên
web application hiện hành của repository.

Kiến trúc hiện hành:

web/frontend
→ Next.js frontend

web/backend
→ FastAPI read-only backend

M3-B là presentation/product layer, không phải research engine.

Các nguyên tắc bắt buộc:

- chỉ đọc versioned/sealed research artifacts;
- không fit lại Market/Financial clustering;
- không recompute research features/metrics nếu upstream đã cung cấp;
- không tự thực hiện PIT alignment riêng;
- không forward-fill hoặc biến missing thành 0;
- không biến cluster label thành khuyến nghị mua/bán;
- nếu hiển thị M3-A, phải truy được run/config/input/provenance tương ứng;
- frontend/backend chỉ trình bày kết quả, không được dẫn dắt methodology.

Chi tiết nhiệm vụ triển khai M3-B được giữ tại tài liệu M3-B riêng.
Master plan này chỉ giữ phạm vi, dependency và acceptance boundary.

---

# PHẦN C — M3-C: BÁO CÁO KỸ THUẬT VÀ NOTEBOOK TÁI LẬP KẾT QUẢ

# 22. MỤC TIÊU M3-C

M3-C bám đúng yêu cầu:

> **Báo cáo kỹ thuật + notebook tái lập được kết quả.**

M3-C **không tạo phương pháp mới** và **không làm lại vai trò của M3-A hoặc M3-B**.

M3-C phải thực hiện ba việc chính:

1. **Báo cáo kỹ thuật** toàn bộ kết quả nghiên cứu M3, trọng tâm là kết quả M3-A gồm strategy chính Combined, bốn đối chứng Market-only, Financial-only, Equal-weight, Momentum-only và benchmark chính thức VNINDEX;
2. cung cấp các **notebook tái lập kết quả chính**, để từ đúng đầu vào, cấu hình và mã nguồn đã khóa có thể tạo lại các bảng, chỉ số và biểu đồ quan trọng dùng trong báo cáo;
3. ghi lại **kết quả đánh giá cuối** sau khi M3-A đã chạy, khóa và niêm phong kết quả đó.

M3-C có thể mô tả ngắn kiến trúc M3-B trong báo cáo kỹ thuật, nhưng:

- không tạo lại gói dữ liệu dashboard;
- không kiểm thử lại API/frontend thay cho M3-B;
- không cần notebook riêng cho dashboard;
- mọi xác minh nguồn → gói → API → giao diện thuộc trách nhiệm hoàn thành của M3-B.

Khái niệm **tái lập được kết quả** trong M3-C nghĩa là:

```text
Đúng đầu vào đã khóa
+
Đúng cấu hình / quy tắc đã khóa
+
Đúng phiên bản mã nguồn
        ↓
Chạy notebook hoặc mô-đun chính thức
        ↓
Tạo lại được các bảng / chỉ số / biểu đồ chính
        ↓
Khớp với kết quả đã được M3-A niêm phong
```

Notebook không được viết một phiên bản business logic thứ hai chỉ để cho ra cùng kết quả. Nếu logic đã nằm trong mô-đun Python được kiểm thử, notebook phải gọi lại mô-đun đó hoặc đọc output chính thức rồi tái tạo phần trình bày/đối chiếu.

---

# 23. KẾ HOẠCH NOTEBOOK M3-C

M3-C giữ 4 notebook chính:

```text
M3/notebooks/
├── 01_Du_Lieu_Va_PIT.ipynb
├── 02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb
├── 03_Tai_Lap_Backtest_Va_Benchmark.ipynb
└── 04_Bao_Cao_Danh_Gia_Cuoi.ipynb
```

Notebook **không viết lại business logic**. Nó đọc sealed run hoặc gọi đúng module chính thức với cùng config/hash để kiểm chứng.

Bộ output canonical được M3-C phép phụ thuộc:

```text
targets_<strategy>.csv
trade_ledger_<strategy>.csv
holdings_<strategy>.csv
turnover_<strategy>.csv
nav_<strategy>.csv
benchmark_vnindex.csv
metrics.json
manifest.json
```

# 24. M3-C NHIỆM VỤ 01 — NOTEBOOK DỮ LIỆU VÀ PIT

## Mục tiêu

Chứng minh run dùng đúng input/version/hash và PIT contract mà **không cần** `aligned_market_financial_snapshots.csv`.

## Đầu vào

```text
manifest.json
config đã hash
Market/Financial handoff hoặc database input đã pin
availability/PIT artifact đã pin
targets_<strategy>.csv
```

## Cách làm

1. Đọc `manifest.json` để xác định run_id, segment,
config, config hash, status, targets_only và counts.
2. Đọc config và code commit.
3. Với một mẫu `decision_date`, gọi **chính module PIT/strategy chính thức** hoặc truy nguyên cùng input để kiểm tra `usable_from_date <= decision_date`; không viết rule PIT thứ hai trong notebook.
4. Đối chiếu target tái tạo với `targets_<strategy>.csv`.
5. Báo PASS/FAIL và mọi discrepancy.

Không tạo một alignment CSV canonical mới.

# 25. M3-C NHIỆM VỤ 02 — NOTEBOOK TÁI LẬP LỰA CHỌN DANH MỤC

## Mục tiêu

Tái lập đúng logic tạo Target Portfolio của từng strategy bằng module chính thức và đối chiếu `targets_<strategy>.csv`.

## Đầu vào

```text
manifest.json
config
inputs đã pin
targets_<strategy>.csv
```

## Đầu ra notebook

- một số bảng minh họa internal computation trong notebook;
- đối chiếu `decision_date/ticker/rank/target_weight/candidates/status` với `targets_<strategy>.csv`;
- không persist `combined_candidates.csv`, `decision_features.csv`, `combined_ranking.csv` thành canonical artifact.

# 26. M3-C NHIỆM VỤ 03 — NOTEBOOK TÁI LẬP BACKTEST VÀ BENCHMARK

## Đầu vào

```text
trade_ledger_<strategy>.csv
holdings_<strategy>.csv
turnover_<strategy>.csv
nav_<strategy>.csv
benchmark_vnindex.csv
metrics.json
manifest.json
```

## Kiểm tra bắt buộc

- `holdings_<strategy>.csv` có đúng schema date/ticker/weight;
- `CASH` được biểu diễn đúng như một row khi phù hợp;
- tổng weight của holdings tại mỗi snapshot hợp lệ theo tolerance;
- failed trade có `executed=0` đúng semantics;
- `SCALED` khớp `scale`;
- turnover khớp `(executed BUY + executed SELL)/(2 × pre_trade_NAV)` khi tái tính từ ledger/NAV;
- NAV curve khớp output sealed;
- metrics tái tính từ NAV/turnover/holdings/ledger khớp `metrics.json` trong tolerance;
- VNINDEX dùng exact segment/window;
- Development/Holdout không tính Sharpe.

# 27. M3-C NHIỆM VỤ 04 — NOTEBOOK BÁO CÁO ĐÁNH GIÁ CUỐI

Chỉ chạy sau khi Final Evaluation đã sealed. Notebook đọc đúng bộ output canonical của run Final, tái tạo bảng/biểu đồ báo cáo và Sharpe nếu segment Final được phép. Không thay config, không tune lại và không mở một output intermediate legacy để thay thế canonical run.

---

# 28. RANH GIỚI TRÁCH NHIỆM CỦA M3-C

Để tránh lặp việc, giữ ranh giới sau:

```text
M3-A
→ tạo và niêm phong kết quả nghiên cứu / backtest

M3-B
→ tạo và kiểm thử dashboard
→ chịu trách nhiệm truy nguyên nguồn → gói → API → giao diện

M3-C
→ tái lập các kết quả chính cần cho báo cáo
→ đối chiếu với artifact M3-A
→ viết báo cáo kỹ thuật
→ viết hướng dẫn tái lập
```

M3-C không làm lại:

- xác minh chính thức Market/Financial handoff thay M3-A;
- lựa chọn methodology mới;
- chạy lại clustering để chọn K mới;
- tạo Candidate / ranking bằng một logic khác M3-A;
- xây lại dashboard package;
- kiểm thử API/frontend thay M3-B;
- mở lại dữ liệu đánh giá cuối để tuning strategy.

---

# 29. ĐẦU RA BÀN GIAO M3-C

M3-C tối thiểu bàn giao:

```text
M3/notebooks/
├── 01_Du_Lieu_Va_PIT.ipynb
├── 02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb
├── 03_Tai_Lap_Backtest_Va_Benchmark.ipynb
└── 04_Bao_Cao_Danh_Gia_Cuoi.ipynb

M3/HUONG_DAN_THUC_HIEN_M3.md

M3/reports/
└── BAO_CAO_KY_THUAT_M3.md
```

Ngoài ra phải có bằng chứng đối chiếu cho biết các bảng / chỉ số / biểu đồ trong notebook và báo cáo được sinh từ version/hash nào của input và code.

Không bắt buộc tạo một bản sao mới của toàn bộ artifact M3-A/M3-B trong thư mục M3-C.

---

# 30. ĐIỀU KIỆN HOÀN THÀNH NỘI BỘ M3-C

M3-C chỉ được coi là hoàn tất khi:

- 4 notebook chính chạy được với đầu vào đã version hóa;
- mỗi notebook ghi rõ input, code version và output;
- Notebook 01 chứng minh được PIT/no-look-ahead từ manifest + input đã pin + module chính thức và đối chiếu `targets_<strategy>.csv`;
- Notebook 02 tái lập được Candidate → 6 tiêu chí → ranking → top 30% và khớp `targets_<strategy>.csv`;
- Notebook 03 tái lập được `ledger/holdings/turnover/nav/benchmark/metrics` theo từng đoạn;
- Notebook 04 trình bày lại được đánh giá cuối từ output đã niêm phong mà không thay strategy;
- Báo cáo kỹ thuật lấy số liệu từ tệp / notebook, không nhập tay;
- `HUONG_DAN_THUC_HIEN_M3.md` chỉ rõ thứ tự, command và điều kiện dừng;
- mọi số liệu chính truy ngược được về input, config, code version và artifact nguồn;
- không có notebook riêng lặp lại nhiệm vụ xây / kiểm thử dashboard của M3-B.

---

# 31. BÁO CÁO KỸ THUẬT M3

Báo cáo kỹ thuật là đầu ra chính của yêu cầu **“Báo cáo kỹ thuật”** trong M3-C.

Báo cáo tối thiểu nên có:

1. Mục tiêu nghiên cứu M3.
2. Nguồn dữ liệu và các phiên bản chính được sử dụng.
3. Kiến trúc hai hệ phân cụm độc lập.
4. Cách căn chỉnh Market–Financial theo thời gian/PIT.
5. Quy tắc tạo Candidate Universe.
6. Ba tiêu chí Market và ba tiêu chí Financial.
7. Quy tắc xếp hạng Combined và chọn top 30%.
8. Cơ chế thực hiện giao dịch, tiền mặt và tái cân bằng.
9. Kết quả strategy chính Combined.
10. Kết quả bốn đối chứng nghiên cứu:

- Market-only;

- Financial-only;

- Equal-weight;

- Momentum-only.
11. Benchmark chính thức: VNINDEX.
12. Kết quả lịch sử Development và Holdout trình bày tách biệt.
13. Các chỉ số hiệu quả / rủi ro / turnover / cash / failed execution đã được duyệt.
14. Kết quả đánh giá cuối.
15. Giới hạn dữ liệu và giới hạn phương pháp.
16. Khả năng tái lập: input version, config version, code version, hash và notebook tương ứng.
17. Phần mô tả ngắn về M3-B và đường dẫn / bằng chứng sang kết quả dashboard nếu cần cho tài liệu tổng thể.

Báo cáo không được:

- nhập tay các con số mà không truy ngược được về tệp nguồn;
- thay phương pháp để làm kết quả đẹp hơn;
- biến nhãn phân cụm thành khuyến nghị đầu tư;
- trình bày dashboard như bằng chứng thay thế cho kết quả nghiên cứu gốc.

---

# 32. HƯỚNG DẪN TÁI LẬP

Tài liệu `HUONG_DAN_THUC_HIEN_M3.md` phục vụ yêu cầu **tái lập và kiểm chứng được kết quả M3**.

Mục tiêu là để một người mới có thể đi từ:

```text
Repository + đúng commit
        +
Runtime inputs đã version hóa
        +
Config đã khóa
        +
Module chính thức
        ↓
Tái lập / kiểm chứng kết quả M3
        ↓
Đối chiếu với canonical artifacts
```

Không viết lại business logic M3 trong tài liệu hoặc notebook.

Nếu logic đã tồn tại trong:

```text
src/delta_t1/m3/
scripts/run_m3.py
```

thì phải sử dụng lại module/command chính thức đó.

---

## 32.1. Mỗi bước trong hướng dẫn phải ghi

Mỗi bước tối thiểu phải có:

- mục đích;
- input/tệp cần dùng;
- path thực tế;
- version/hash cần kiểm tra;
- config sử dụng;
- code commit;
- command hoặc module chính thức;
- output cần tạo hoặc kiểm tra;
- cách đối chiếu với canonical output;
- điều kiện PASS;
- điều kiện FAIL/DỪNG;
- bước tiếp theo.

Không ghi command cho notebook/module chưa tồn tại hoặc chưa được xác minh trên repository.

---

## 32.2. Luồng tái lập tổng quát

```text
Kiểm tra repository / branch / commit / môi trường
        ↓
Kiểm tra config
        ↓
Kiểm tra manifest
        ↓
Kiểm tra 6 logical runtime inputs
        ↓
Kiểm tra version / hash / schema / coverage
        ↓
Notebook 01 — Dữ liệu và PIT
        ↓
Notebook 02 — Tái lập lựa chọn danh mục
        ↓
Notebook 03 — Tái lập backtest và benchmark
        ↓
Final Evaluation đã verified + sealed?
        │
        ├── CHƯA
        │     ↓
        │   Notebook 04 = NOT_READY
        │
        └── RỒI
              ↓
        Notebook 04 — Báo cáo đánh giá cuối
              ↓
Đối chiếu canonical artifacts
              ↓
Hoàn thiện Báo cáo kỹ thuật M3
```

Notebook có nhiệm vụ:

```text
đọc
tái lập
đối chiếu
trình bày
```

không tạo một implementation M3 thứ hai.

Nếu cần chạy lại toàn bộ M3-A, phải gọi đúng `scripts/run_m3.py` và các module chính thức.

---

## 32.3. Các trường hợp phải DỪNG

Phải DỪNG nếu xảy ra ít nhất một trường hợp:

- thiếu runtime input bắt buộc;
- path input không đúng;
- hash/version không khớp;
- schema thực tế không đáp ứng loader contract;
- coverage không đủ cho segment cần chạy;
- Market/Financial/PIT input chưa đạt readiness;
- code commit không xác định được;
- config cần cho official backtest chưa ở trạng thái `LOCKED`;
- decision ảnh hưởng Candidate/Ranking/Execution/Return chưa được khóa;
- canonical backtest artifact chưa tồn tại hoặc chưa được verify;
- notebook tái lập không khớp canonical output mà chưa giải thích được;
- VNINDEX không có đúng segment/window;
- Final window chưa được khóa;
- Final input chưa đạt readiness;
- Final run chưa sealed nhưng Notebook 04 được yêu cầu chạy.

Không sửa methodology/config chỉ để làm notebook khớp kết quả.

---

## 32.4. Kiểm tra repository và môi trường

Chạy tối thiểu:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short

.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

Ghi lại:

```text
BRANCH
HEAD
WORKTREE STATUS
CONFIG PATH
CONFIG SHA256
```

Nếu local và remote diverge:

```text
LOCAL_HEAD
REMOTE_HEAD
DIVERGENCE
```

Không tự reset local theo remote.

---

## 32.5. Command M3-A hiện được GitHub hỗ trợ

Runner chính thức:

```text
scripts/run_m3.py
```

### Khi config còn `PROPOSED`

Chỉ chạy targets-only:

```powershell
python scripts/run_m3.py --segment development --targets-only
```

Targets-only dùng để kiểm tra:

```text
PIT
Candidate Universe
candidate count
UNIVERSE_TOO_SMALL
ranking/picks
target_weight
status
```

Không tính return.

Không coi targets-only là official backtest.

---

### Khi config đã `LOCKED`

Có thể chạy:

```powershell
python scripts/run_m3.py --segment development
python scripts/run_m3.py --segment holdout
```

Official historical backtest không được chạy khi config vẫn `PROPOSED`.

---

## 32.6. Phân biệt output theo loại run

### Targets-only

Tạo tối thiểu:

```text
targets_<strategy>.csv
manifest.json
```

Không yêu cầu:

```text
trade_ledger
holdings
turnover
nav
benchmark
metrics
```

---

### Full backtest

Tạo:

```text
targets_<strategy>.csv
trade_ledger_<strategy>.csv
holdings_<strategy>.csv
turnover_<strategy>.csv
nav_<strategy>.csv
benchmark_vnindex.csv
metrics.json
manifest.json
```

Hướng dẫn phải xác định loại run trước khi kiểm tra output.

---

# 33. THỨ TỰ THỰC HIỆN TOÀN DỰ ÁN

Mục này chỉ quy định **thứ tự thực hiện**. Chi tiết methodology, input contract, output contract và execution semantics được định nghĩa tại các mục tương ứng phía trên và không lặp lại tại đây.

## Giai đoạn 0 — Khóa decision queue và config

Trước official backtest có return:

- resolve toàn bộ decision còn ảnh hưởng Candidate Universe, Ranking, Target Portfolio, Execution, Return và Benchmark;
- ghi quyết định vào decision record/ADR;
- cập nhật config;
- chuyển `status = LOCKED`;
- pin config hash.

Không thay strategy rule dựa trên return sau khi đã khóa.

## Giai đoạn 1 — Audit và pin runtime inputs

Xác minh toàn bộ runtime inputs theo **Mục 5 — Khung dữ liệu chung**:

- đúng path/version;
- đúng schema;
- đủ coverage cho segment;
- hash đã xác minh;
- provenance đã pin.

Nếu một input bắt buộc chưa PASS thì không chuyển sang official backtest.

## Giai đoạn 2 — Hoàn thiện output writer và manifest

Trước official run phải bảo đảm:

- canonical output contract đã sẵn sàng;
- `holdings_<strategy>.csv` được tạo đúng schema GitHub hiện hành:
  ```text
  date
  ticker
  weight
  ```
- `manifest.json` được tạo đúng schema GitHub hiện hành;
- execution semantics và turnover contract đã được kiểm thử.

## Giai đoạn 3 — Targets-only readiness

Khi input đã sẵn sàng nhưng config còn `PROPOSED`, chỉ chạy targets-only để kiểm tra:

- PIT;
- eligibility;
- Candidate Universe;
- ranking;
- picks;
- target weights;
- trạng thái như `UNIVERSE_TOO_SMALL`.

Targets-only không tính return và không được coi là official backtest.

## Giai đoạn 4 — Historical backtest

Chỉ chạy khi:

```text
config = LOCKED
+
runtime inputs PASS
+
writer/manifest PASS
+
tests PASS
```

Thứ tự:

```text
Development
2019-01-31 → 2023-12-29
60 decision snapshots
        ↓
Verify + Seal
        ↓
Holdout
2024-01-31 → 2025-12-31
24 decision snapshots
        ↓
Verify + Seal
```

Holdout sử dụng đúng frozen config/engine của Development và không được dùng để tune strategy.

## Giai đoạn 5 — Final Evaluation

Chỉ mở khi dữ liệu sau `2025-12-31` đạt readiness.

Trước khi xem Final performance:

1. audit Market/Financial/PIT/prices/execution/VNINDEX;
2. khóa exact Final start/end;
3. pin config/version/hash;
4. chạy bằng strategy rules và engine đã frozen;
5. verify;
6. seal;
7. mới thực hiện đánh giá Final theo contract đã khóa.

Không dùng Final result để quay lại chỉnh strategy.

## Giai đoạn 6 — M3-B

Sau khi các artifact upstream cần thiết đã sẵn sàng, M3-B đọc các versioned/sealed artifacts để trình bày trên product/dashboard layer.

M3-B không fit model, không recompute research logic và không thay methodology.

Chi tiết xem tài liệu M3-B riêng.

## Giai đoạn 7 — M3-C

Sau khi các canonical run cần thiết đã tồn tại:

- tái lập dữ liệu/PIT;
- tái lập lựa chọn danh mục;
- tái lập backtest/benchmark;
- lập báo cáo đánh giá cuối;
- đối chiếu kết quả với sealed canonical artifacts.

Notebook không tạo một implementation business logic thứ hai.

Luồng tổng quát:

```text
LOCK DECISIONS
      ↓
AUDIT + PIN INPUTS
      ↓
WRITER / MANIFEST READY
      ↓
TARGETS-ONLY
      ↓
DEVELOPMENT
      ↓
HOLDOUT
      ↓
FINAL EVALUATION
      ↓
M3-B + M3-C
```

---

# 34. CÁC ĐIỀU TUYỆT ĐỐI KHÔNG LÀM

Các nguyên tắc dưới đây là ranh giới bất biến của M3.

**Không gộp Market và Financial thành một mô hình phân cụm mới trong M3.**  
Market Clustering và Financial Clustering là hai hệ độc lập; M3 chỉ kết hợp chúng tại tầng strategy/portfolio theo rule đã khóa.

**Không dùng thông tin tương lai.**  
Không dùng Financial data chưa usable tại `decision_date` và không dùng giá sau `decision_date` để tính signal/ranking tại ngày đó.

**Không dùng `period_end` thay cho Financial availability/PIT timing.**  
Financial state chỉ được sử dụng khi `usable_from_date <= decision_date`.

**Không thay dữ liệu lịch sử bằng trạng thái hiện tại.**  
Market state và Financial state của mỗi `decision_date` phải được lấy từ dữ liệu tương ứng với thời điểm đó.

**Không thay methodology/strategy sau khi xem performance.**  
Không thay cluster authority, eligibility, tiêu chí MC/FC, trọng số, top-share, tie rule, `N_min`, execution rule hoặc return basis chỉ vì kết quả backtest không thuận lợi.

**Không tạo hoặc che dữ liệu để làm kết quả đẹp hơn.**  
Không forward-fill/bịa observation, không biến missing thành 0, không xóa kết quả bất lợi và không sửa artifact đã sealed chỉ để làm gate PASS.

**Không tự thay đổi execution semantics.**  
Không tự chọn mã thay thế cho `BUY_FAILED`/`SELL_FAILED`; không tự tạo Cash từ `SELL_FAILED`; thiếu Cash phải xử lý theo scaling rule đã khóa.

**Không làm mất ranh giới evaluation.**  
Development, Holdout và Final Evaluation phải giữ đúng segment boundary; không dùng Holdout hoặc Final để tune lại strategy. Sharpe chỉ được sử dụng ở segment được decision/config cho phép.

**Không dùng artifact sai vai trò.**  
Official run phải sử dụng canonical/versioned inputs và outputs theo manifest.

**Dashboard không được trở thành research engine hoặc investment recommender.**  
M3-B chỉ đọc và trình bày versioned/sealed artifacts; không fit model, không recompute methodology, không tự thực hiện PIT/ranking và không biến cluster label thành khuyến nghị mua/bán.

---

# 35. ĐIỀU KIỆN HOÀN THÀNH M3-A

M3-A chỉ hoàn tất khi:

- input Market/Financial/PIT/prices/calendar/VNINDEX đã được version/hash;
- các decision ảnh hưởng target/return đã khóa;
- config official là `LOCKED`;
- missing-price/BUY_FAILED/SELL_FAILED/scaling khớp semantics GitHub đã chốt;
- turnover khớp `(BUY+SELL)/(2×pre_trade_NAV)`;
- Development và Holdout đã chạy/seal riêng;
- mỗi official run có đủ 8 loại output canonical;
- `manifest.json` đủ để truy code/config/input provenance;
- benchmark/metrics khớp exact segment;
- Sharpe không xuất ở Development/Holdout;
- Final Evaluation chỉ chạy sau readiness + unseen audit và exact-window lock.

# 36. ĐIỀU KIỆN HOÀN THÀNH M3-B

M3-B hoàn tất khi:

- schema hiển thị đã có phiên bản;
- gói dữ liệu hiển thị bất biến;
- nếu dashboard đọc M3-A thì chỉ đọc sealed/versioned M3-A artifacts theo `manifest.json`;
- backend hiện hành sử dụng `web/backend` với FastAPI theo mô hình read-only;
- frontend hiện hành sử dụng `web/frontend` với Next.js;
- frontend/backend không fit model, không recompute research methodology và không tự tạo một PIT/ranking implementation riêng;
- kiểm thử API đạt;
- frontend build/test cần thiết đạt;
- màn hình tổng quan phân biệt rõ Market và Financial là hai hệ clustering độc lập;
- thời điểm Market observation và Financial PIT/usable_from_date được thể hiện đúng semantic, không làm người dùng hiểu hai loại dữ liệu có cùng thời điểm;
- màn hình dịch chuyển/lịch sử tôn trọng tần suất cập nhật khác nhau giữa Market và Financial;
- màn hình chi tiết cho thấy lịch sử và provenance cần thiết;
- trạng thái missing/unavailable/stale hiển thị rõ, không biến thành zero;
- nếu hiển thị kết quả M3-A, phải truy được segment, run, config, input và provenance tương ứng;
- không có tính toán nghiên cứu trong dashboard;
- không biến cluster label hoặc strategy output thành khuyến nghị đầu tư;
- kiểm tra desktop/mobile đạt;
- truy nguyên từ source artifact → presentation bundle → API → frontend đạt.

Các implementation HTML/CSS/JavaScript hoặc dashboard legacy được repository giữ lại vì compatibility/history không được coi là active M3-B architecture và không được dùng để ghi đè `web/frontend` + `web/backend`.

# 37. ĐIỀU KIỆN HOÀN THÀNH M3-C

M3-C hoàn tất khi:

- 4 notebook hoặc bộ tương đương đọc đúng canonical output;
- Notebook 01 kiểm tra PIT bằng manifest + pinned inputs + official module, không cần alignment CSV legacy;
- Notebook 02 khớp target output;
- Notebook 03 khớp ledger/holdings/turnover/nav/benchmark/metrics;
- Notebook 04 chỉ báo cáo Final sealed run;
- turnover được kiểm tra theo:

```text
(executed BUY + executed SELL)
/
(2 × pre_trade_NAV)
```

- report không nhập tay số liệu và không phụ thuộc CSV intermediate đã bỏ;
- mọi kết quả truy được về `manifest.json`, config, code commit và input hashes.

---

# 38. TRẠNG THÁI HIỆN TẠI

Mục này chỉ theo dõi trạng thái decision/dependency.

Không định nghĩa methodology mới.

## 38.1. Đã khóa / đã có owner decision

Market và Financial là hai hệ clustering độc lập.

A v4 là Market clustering model chính thức cho M2/M3 theo D-DIR-01 ngày 26/10/2026.

B v4 là Financial clustering model hiện hành; giới hạn của B phải được báo cáo.

M2 K=2 giữ làm legacy/research control.

Long-only.

Không leverage.

Monthly rebalance.

Top share = 30% đối với strategy có top-selection.

Số mã được chọn dùng:

```text
ceil(0.30 × N)
```

Target Portfolio dùng equal weight sau selection.

Execution dùng phiên hợp lệ kế tiếp sau `decision_date`.

BUY_FAILED không chọn mã thay thế; phần vốn tương ứng ở Cash.

SELL_FAILED không tạo Cash; position chưa bán vẫn được giữ.

Missing valuation price sử dụng stale-mark semantics hiện hành.

Turnover:

```text
(executed BUY + executed SELL)
/
(2 × pre_trade_NAV)
```

Trạng thái:

```text
OWNER DECISION — PENDING GIT SYNC
```

Canonical outputs:

```text
targets
trade_ledger
holdings
turnover
nav
benchmark_vnindex
metrics
manifest
```

`holdings_<strategy>.csv` theo Git hiện hành có:

```text
date
ticker
weight
```

`CASH` được biểu diễn như một row trong holdings.

Giá trị vị thế tuyệt đối được engine giữ trong internal state `pf.values` và `pf.cash`, không phải field canonical của holdings output.

Cash return base scenario = 0.

Main transaction cost/slippage = 0.

Development:

```text
2019-01-31 → 2023-12-29
60 snapshots
```

Holdout:

```text
2024-01-31 → 2025-12-31
24 snapshots
```

VNINDEX là benchmark.

Final Evaluation chỉ mở sau readiness audit và exact-window lock.


## 38.2. Strategy universe theo Git Q14 — hiện phải theo dõi trạng thái proposal/decision

Definition hiện hành trên Git:

```text
Combined
→ Market Eligible ∩ Financial Eligible

Market-only
→ Market Eligible Pool

Financial-only
→ Financial Eligible Pool ∩ traded universe

Equal-weight
→ traded universe

Momentum-only
→ traded universe ∩ mom_126 hợp lệ
```

Sector treatment:

Bank / Securities / Insurance

```text
Combined
→ bị loại nếu Financial B là requirement và B không có coverage

Financial-only
→ không thể sử dụng nếu Financial state bắt buộc không tồn tại

Market-only
→ không bị loại chỉ vì thiếu Financial B

Equal-weight
→ không bị loại chỉ vì thiếu Financial B

Momentum-only
→ không bị loại chỉ vì thiếu Financial B
```

Nếu Q14/Q4 chưa được owner/mentor lock:

```text
status = PROPOSED / OPEN
```

không được tự ghi thành LOCKED.

## 38.3. Leading-cluster rule

Nguyên tắc đã xác định:

```text
không suy leading/weak cluster chỉ từ numeric label
```

Cluster phải được xác định từ profile/semantic theo rule đã khóa.

Exact mechanical selector, tie rule và ambiguity handling phải theo decision/config cuối cùng.

## 38.4. Còn phải quyết định trước full official Combined backtest

Tối thiểu kiểm tra trạng thái mới nhất của:

- Q2 ILLIQUID / Market eligibility;
- Q3 Financial B vs B-PIT / timing leakage;
- Q4 Financial-sector treatment;
- Q5 exact leading/allowed-cluster rule;
- Q6 N_min / UNIVERSE_TOO_SMALL;
- Q-date — quy tắc xác định usable_from_date / availability lag trước FY2022;
- MC1–MC3;
- FC1–FC3;
- Combined score / weights / tie rule;
- Financial staleness;
- Q11 return basis;
- Q12 tradability / ceiling-floor rule;
- Q14 exact control-strategy definitions;
- Q17 adjusted-price one-session glitch handling;
- Financial handoff/coverage readiness;
- exact Final Evaluation window.

Không để implementation tự quyết một mục vẫn OPEN.

## 38.5. Dependency kỹ thuật trước official run

Official run còn yêu cầu:

- runtime inputs PASS;
- config chuyển LOCKED;
- config hash được pin;
- output writer PASS;
- `holdings_<strategy>.csv` đúng schema date/ticker/weight theo Git hiện hành;
- `manifest.json` đúng schema GitHub hiện hành;
- execution/turnover tests PASS;
- segment boundary PASS.

Luồng trạng thái:

```text
DECISION QUEUE
      +
INPUT READINESS
      +
OUTPUT READINESS
      ↓
TARGETS-ONLY
      ↓
LOCKED CONFIG
      ↓
DEVELOPMENT
      ↓
VERIFY / SEAL
      ↓
HOLDOUT
      ↓
VERIFY / SEAL
      ↓
FINAL EVALUATION
```


# 39. KẾT LUẬN

M3 giữ **Market Clustering** và **Financial Clustering** là hai hệ độc lập.

M3-A sử dụng các Market/Financial state đã được upstream tạo, sau đó áp dụng các rule PIT, eligibility, strategy, ranking, execution và evaluation đã được khóa để xây dựng và backtest danh mục.

Luồng tổng quát:

```text
Market state            Financial state
     │                         │
     └──────────┬──────────────┘
                ↓
         PIT / Eligibility
                ↓
      Strategy-specific Universe
                ↓
        Ranking / Selection
                ↓
         Target Portfolio
                ↓
            Execution
                ↓
       Holding / Rebalance
                ↓
        NAV / Performance
                ↓
             VNINDEX
```

Các strategy phải tuân theo definition và config đã được khóa.

Proposal hoặc câu hỏi chưa được owner/mentor chốt không được tự biến thành official methodology.

Historical evaluation được tách thành:

```text
Development
→ Verify / Seal

Holdout
→ Verify / Seal

Final Evaluation
→ chỉ mở sau readiness audit
→ khóa exact evaluation window trước khi xem performance
```

M3-B là read-only product/presentation layer trên kiến trúc web hiện hành; không fit lại model và không recompute research methodology.

M3-C đảm bảo kết quả có thể được tái lập, đối chiếu và truy nguyên về:

```text
input artifacts
+
config
+
code commit
+
manifest
+
sealed run
```

Chi tiết methodology, input contract, output contract, execution semantics, decision status và acceptance criteria được định nghĩa tại các mục tương ứng phía trên.

**Mục 39 chỉ tổng kết luồng M3 và không tạo thêm methodology, rule hoặc decision mới.**