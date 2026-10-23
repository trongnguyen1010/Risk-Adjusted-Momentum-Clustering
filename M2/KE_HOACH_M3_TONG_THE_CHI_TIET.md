# KẾ HOẠCH TỔNG THỂ M3 V5 — KẾT HỢP DỮ LIỆU THỊ TRƯỜNG VÀ TÀI CHÍNH, BACKTEST, DASHBOARD VÀ BÁO CÁO TÁI LẬP

**Dự án:** DELTA — Phân cụm động lượng điều chỉnh theo rủi ro cho cổ phiếu Việt Nam  
**Kho mã nguồn:** `trongnguyen1010/Risk-Adjusted-Momentum-Clustering`  
**Nhánh tham chiếu:** `m2-clustering-experiment`  
**Phiên bản kế hoạch:** V5 — viết lại từ V4 theo tiếng Việt tự nhiên, giữ nguyên logic nghiên cứu  
**Trạng thái:** KẾ HOẠCH CHI TIẾT — CHƯA THỰC THI M3  
**Phạm vi:** M3-A Danh mục và backtest + M3-B Dashboard + M3-C Báo cáo và khả năng tái lập

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

## 1.1. Kế hoạch tổng thể DELTA

`docs/DELTA_UNIFIED_PROJECT_PLAN.md`

Phải giữ các nguyên tắc:

- M3 là tầng danh mục và backtest nằm sau M2;
- không dùng kết quả danh mục để quay lại chọn lại mô hình M2;
- quy ước chiến lược phải được khóa trước khi mở đánh giá cuối;
- đối chuẩn, giai đoạn đánh giá và nguồn dữ liệu phải có phiên bản rõ ràng;
- không được gọi một giai đoạn đã từng được xem là “đánh giá cuối hoàn toàn chưa từng thấy”.

## 1.2. Quy ước đánh giá và backtest

`docs/EVALUATION_AND_BACKTEST.md`

Phải giữ:

- chất lượng phân cụm, độ ổn định theo thời gian và hiệu quả danh mục là ba lớp đánh giá khác nhau;
- không dùng chỉ số danh mục để thay đổi kết luận M2;
- xử lý thiếu giá, không giao dịch được và tiền mặt phải minh bạch;
- cơ sở tính lợi suất phải được xác nhận trước khi dùng.

## 1.3. Quy ước dữ liệu

`docs/DATA_CONTRACT.md`

Phải giữ:

- nguyên tắc PIT;
- không dùng thông tin tương lai;
- không lọc tập cổ phiếu lịch sử bằng trạng thái ở thời điểm cuối;
- không tạo giả hoặc nội suy các quan sát không tồn tại;
- phải phân biệt rõ giá thô, giá điều chỉnh và chuỗi tổng lợi suất.

## 1.4. Bộ bàn giao kết quả phân cụm thị trường từ M2

Tối thiểu kiểm tra:

- `M2/artifacts/m2-final-handoff-v1/m2_cluster_labels_for_m3.csv`
- `M2/artifacts/m2-final-handoff-v1/m2_cluster_profiles_for_m3.csv`
- `M2/artifacts/m2-final-handoff-v1/m2_transition_turnover_reference.csv`
- `M2/artifacts/m2-final-handoff-v1/m2_to_m3_handoff_manifest.json`
- `M2/models/final_selected_model/`

## 1.5. Bộ bàn giao kết quả phân cụm tài chính

Không được tự giả định tên tệp nếu quy trình phân cụm tài chính chưa phát hành bộ bàn giao chính thức.

Bộ bàn giao tối thiểu phải có:

- nhãn phân cụm tài chính theo từng mã cổ phiếu;
- `financial_snapshot_date` hoặc mốc dữ liệu tài chính tương đương;
- `period_end` nếu có;
- `available_at`;
- `financial_cluster_label`;
- hồ sơ mô tả ý nghĩa của từng cụm tài chính;
- `K_financial`;
- thông tin phiên bản và lịch sử điều chỉnh;
- phiên bản dữ liệu đầu vào;
- tệp kê khai và mã băm.

Nếu thiếu `available_at` hoặc không truy nguyên được nhãn tài chính về đúng phiên bản dữ liệu, M3 vẫn có thể chuẩn bị mã nguồn và cấu trúc tệp, nhưng **không được chạy backtest kết hợp chính thức**.

## 1.6. Lớp sản phẩm và dashboard

`docs/PRODUCT.md`

Ưu tiên bộ công nghệ đã có trong kho mã nguồn:

- Python trong `src/delta_t1/`;
- `src/delta_t1/product/builder.py` để tạo gói dữ liệu phục vụ hiển thị;
- `src/delta_t1/product/repository.py` để đọc gói dữ liệu;
- `src/delta_t1/product/server.py` để cung cấp API chỉ đọc và phục vụ tệp web tĩnh;
- backend hiện dùng `BaseHTTPRequestHandler` và `ThreadingHTTPServer` của thư viện chuẩn Python;
- giao diện hiện có trong `web/index.html`, `web/app.js`, `web/styles.css`;
- giao diện dùng HTML/CSS/JavaScript thuần.

Không tự chuyển sang React, FastAPI, Django hoặc một bộ công nghệ khác nếu chưa có quyết định riêng.

## 1.7. Khả năng tái lập

`docs/REPRODUCIBILITY.md`

Phải giữ:

- kết quả đã hoàn tất phải bất biến;
- thay phương pháp hoặc nguồn dữ liệu thì tạo phiên bản mới;
- không sửa kết quả cũ chỉ để vượt qua kiểm tra;
- mọi kết quả phải truy ngược được về đầu vào, cấu hình, mã nguồn và lần chạy đã tạo ra nó.

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
Xác định mã đủ điều kiện ở cả hai hệ
        ↓
Tính 3 tiêu chí thị trường + 3 tiêu chí tài chính
        ↓
Áp dụng quy tắc xếp hạng kết hợp đã được khóa
        ↓
Tạo tập ứng viên kết hợp
        ↓
Chọn 30% số mã đứng đầu, làm tròn lên
        ↓
Phân bổ trọng số bằng nhau
        ↓
Mô phỏng giao dịch ở giá đóng cửa của phiên hợp lệ kế tiếp
        ↓
Backtest danh mục
```

## 2.3. Vai trò của ba chiến lược

### Chiến lược chính — Kết hợp thị trường và tài chính

Đây là chiến lược nghiên cứu chính của M3-A.

### Đối chứng 1 — Chỉ dùng tín hiệu thị trường

Dùng để đo hiệu quả khi chỉ sử dụng hệ phân cụm và tiêu chí thị trường.

### Đối chứng 2 — Chỉ dùng tín hiệu tài chính

Dùng để đo hiệu quả khi chỉ sử dụng hệ phân cụm và tiêu chí tài chính.

Hai đối chứng này không được “cộng kết quả” để tạo chiến lược kết hợp. Chiến lược kết hợp phải được hình thành **trước khi backtest**, bằng cách sử dụng đồng thời trạng thái phân cụm của hai hệ.

### Đối chuẩn chính thức

M3 hiện chỉ sử dụng **VNINDEX** làm benchmark chính thức để so sánh với kết quả backtest của chiến lược Combined.

Market-only và Financial-only, nếu được chạy, là **đối chứng nghiên cứu**, không phải benchmark.

Không sử dụng benchmark bổ sung khác trong kế hoạch hiện tại.

---

# 3. QUY TẮC CHỌN 30% SỐ MÃ

**Đã được chủ dự án duyệt.**

Trình tự đúng:

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

Nếu một mã đã được chọn nhưng không giao dịch được tại phiên thực hiện giao dịch:

- phần vốn của mã đó chuyển thành tiền mặt;
- không chọn mã khác thay thế;
- không chia lại phần vốn đó cho các mã còn lại.

---

# 4. SÁU TIÊU CHÍ CHỌN MÃ

## 4.1. Ba tiêu chí thị trường

Có đúng 3 tiêu chí riêng cho dữ liệu thị trường, ký hiệu tạm thời `MC1`, `MC2`, `MC3`.

## 4.2. Ba tiêu chí tài chính

Có đúng 3 tiêu chí riêng cho dữ liệu tài chính, ký hiệu tạm thời `FC1`, `FC2`, `FC3`.

Hai bộ tiêu chí phải khác nhau về nội dung vì chúng đo hai nhóm thông tin khác nhau.

## 4.3. Không tự đặt công thức khi mentor chưa cung cấp

Mỗi tiêu chí chỉ cần mô tả bằng các trường sau:

| Trường | Ý nghĩa |
|---|---|
| `criterion_id` | mã tiêu chí, ví dụ `MC1`–`MC3` hoặc `FC1`–`FC3` |
| `name` | tên tiêu chí |
| `description` | mô tả tiêu chí đo điều gì |
| `formula` | công thức tính chính xác |
| `source_fields` | các trường dữ liệu đầu vào cần dùng |
| `source_artifact` | tệp hoặc artifact nguồn chứa dữ liệu |
| `missing_rule` | cách xử lý khi thiếu dữ liệu |
| `tie_rule` | cách xử lý khi các mã có cùng điểm hoặc cùng thứ hạng |


## 4.4. Hai kết quả xếp hạng riêng trước khi kết hợp

```text
MC1 + MC2 + MC3
→ điểm hoặc thứ hạng của nhánh thị trường
```

và:

```text
FC1 + FC2 + FC3
→ điểm hoặc thứ hạng của nhánh tài chính
```

## 4.5. Quy tắc xếp hạng kết hợp

Cách gộp kết quả của hai nhánh thành một thứ hạng cuối cùng **chưa được tự chọn**. Đây là quyết định cần mentor/chủ dự án phê duyệt.

Có thể cân nhắc các kiểu sau, nhưng không được tự động coi kiểu nào là phương án chính thức:

1. điểm chuẩn hóa có trọng số cố định;
2. xếp hạng hai giai đoạn theo thứ tự ưu tiên;
3. tổng hợp thứ hạng;
4. tài chính dùng để lọc, thị trường dùng để xếp hạng;
5. thị trường dùng để lọc, tài chính dùng để xếp hạng.

Khi chưa khóa quy tắc này, không được tạo danh mục chính thức.

---

# 5. MÔ HÌNH THỜI GIAN VÀ PIT CHO CHIẾN LƯỢC KẾT HỢP

## 5.1. Lịch ra quyết định

M3 dùng lịch ra quyết định hàng tháng dựa trên các mốc dữ liệu thị trường hợp lệ.

## 5.2. Dữ liệu tài chính có lịch công bố riêng

Dữ liệu tài chính có thể cập nhật theo quý, nửa năm hoặc năm và luôn có độ trễ công bố. Vì vậy không được ép mốc tài chính phải trùng ngày với mốc thị trường.

## 5.3. Ghép theo thông tin mới nhất đã thực sự tồn tại tại thời điểm quyết định

Tại `decision_date = t`:

```text
market_cluster = nhãn phân cụm thị trường tại t

financial_cluster = nhãn phân cụm tài chính mới nhất
                    thỏa available_at <= t
```

Không được thay điều kiện `available_at <= t` bằng `period_end <= t`.

## 5.4. Quy tắc về độ cũ của dữ liệu tài chính

Một nhãn tài chính không được mặc định có hiệu lực vô hạn. Cần khóa:

- cách tính tuổi dữ liệu tài chính;
- ngưỡng hoặc quy tắc xác định dữ liệu quá cũ;
- cách xử lý mã không có trạng thái tài chính hợp lệ.

Không tự chọn mốc 3, 6 hoặc 12 tháng chỉ vì thuận tiện.

---

# 6. CÁC QUYẾT ĐỊNH ĐÃ KHÓA VÀ CÒN MỞ

| Hạng mục | Trạng thái |
|---|---|
| Chỉ mua, không bán khống | ĐÃ KHÓA |
| Không dùng đòn bẩy | ĐÃ KHÓA |
| Thị trường và tài chính phân cụm riêng | ĐÃ DUYỆT |
| Kết hợp ở bước ra quyết định danh mục, không phân cụm lại đặc trưng thô | ĐÃ DUYỆT |
| Có 3 tiêu chí thị trường | ĐÃ DUYỆT |
| Có 3 tiêu chí tài chính khác 3 tiêu chí thị trường | ĐÃ DUYỆT |
| Chọn 30% sau khi đã có tập ứng viên kết hợp | ĐÃ DUYỆT |
| 30% làm tròn lên | ĐÃ KHÓA |
| Trọng số bằng nhau | ĐÃ KHÓA |
| Tái cân bằng hàng tháng | ĐÃ KHÓA |
| Giao dịch ở giá đóng cửa phiên hợp lệ kế tiếp | ĐÃ KHÓA |
| Mã không giao dịch được → phần vốn chuyển thành tiền mặt | ĐÃ KHÓA |
| Không chọn mã thay thế | ĐÃ KHÓA |
| Không phân bổ lại phần vốn bị lỗi khớp lệnh | ĐÃ KHÓA |
| Lợi suất tiền mặt = 0 | ĐÃ KHÓA |
| Chi phí giao dịch chính = 0 | ĐÃ KHÓA |
| Trượt giá chính = 0 | ĐÃ KHÓA |
| Không dùng Sharpe | ĐÃ KHÓA |
| Đánh giá cuối dùng dữ liệu mới sau 28/08/2026 | ĐÃ KHÓA NGUYÊN TẮC |
| Công thức MC1..MC3 | CHỜ MENTOR |
| Công thức FC1..FC3 | CHỜ MENTOR |
| Market eligibility: dữ liệu hợp lệ + quyết định có/không cluster filter | CHỜ QUYẾT ĐỊNH |
| Financial eligibility: PIT/staleness/missing + quyết định có/không cluster filter | CHỜ QUYẾT ĐỊNH |
| Cách tạo tập ứng viên kết hợp | CHỜ QUYẾT ĐỊNH |
| Cách gộp hai nhánh thành thứ hạng cuối | CHỜ QUYẾT ĐỊNH |
| Quy tắc về độ cũ của dữ liệu tài chính | CHỜ QUYẾT ĐỊNH |
| Ngày kết thúc chính xác của giai đoạn đánh giá cuối | CHỜ QUYẾT ĐỊNH |

---

# 7. KHUNG DỮ LIỆU CHUNG

## 7.1. Đầu vào từ hệ thị trường

Tối thiểu:

- nhãn phân cụm thị trường;
- hồ sơ mô tả các cụm thị trường;
- dữ liệu dịch chuyển giữa các cụm;
- các đặc trưng thị trường theo mốc thời gian;
- giá cổ phiếu hằng ngày;
- danh mục chứng khoán và định danh;
- lịch giao dịch;
- trạng thái có/không thể giao dịch;
- VNINDEX;
- bằng chứng về cơ sở tính lợi suất và xử lý sự kiện doanh nghiệp;
- dữ liệu đầu vào cho MC1..MC3.

## 7.2. Đầu vào từ hệ tài chính

Tối thiểu:

- nhãn phân cụm tài chính;
- hồ sơ mô tả các cụm tài chính;
- `available_at`;
- `period_end` nếu có;
- chuỗi phiên bản và lịch sử điều chỉnh;
- dữ liệu đầu vào cho FC1..FC3;
- tệp kê khai và mã băm của bộ bàn giao tài chính.

## 7.3. Bảng dữ liệu sau khi căn chỉnh hai hệ

Tối thiểu cần có:

```text
decision_date
security_id
ticker

market_snapshot_date
market_cluster_label
market_cluster_semantic

financial_snapshot_date
financial_available_at
financial_cluster_label
financial_cluster_semantic
financial_age_days
financial_staleness_status

market_eligible
financial_eligible
combined_eligible
exclusion_reason
```

## 7.4. Hai đoạn dữ liệu lịch sử dùng cho backtest M3

Backtest lịch sử của M3 phải sử dụng và báo cáo **hai đoạn dữ liệu tách biệt** đã được M2 bàn giao:

| Đoạn | Vai trò gốc trong M2 | Khoảng thời gian | Cách dùng trong M3 |
|---|---|---|---|
| **Đoạn A** | **M2 Development** | **30/11/2023 → 24/01/2025** | Chạy backtest lịch sử của chiến lược đã khóa trên đoạn phát triển của M2; kết quả phải được báo cáo riêng. |
| **Đoạn B** | **M2 Holdout** | **27/02/2026 → 28/08/2026** | Chạy backtest lịch sử riêng trên đoạn holdout của M2; không được thay quy tắc sau khi xem kết quả Đoạn A. |

Khoảng thời gian **25/01/2025 → 26/02/2026** nằm giữa hai đoạn trên là **khoảng trống dữ liệu** trong thiết kế hiện tại. M3 không được:

- tạo giả các snapshot hàng tháng trong khoảng trống;
- nối NAV của Đoạn A và Đoạn B thành một chuỗi liên tục như thể không có khoảng trống;
- tính chuyển cụm, turnover hoặc rebalance xuyên qua khoảng trống nếu không có dữ liệu hợp lệ;
- dùng Đoạn B để sửa lại quy tắc sau khi đã xem kết quả Đoạn A.

Kết quả backtest phải được lưu và trình bày theo cấu trúc:

```text
Đoạn A — M2 Development
30/11/2023 → 24/01/2025
        ↓
Backtest riêng
        ↓
Kết quả A

25/01/2025 → 26/02/2026
KHOẢNG TRỐNG — KHÔNG NỐI GIẢ

Đoạn B — M2 Holdout
27/02/2026 → 28/08/2026
        ↓
Backtest riêng
        ↓
Kết quả B
```

Dữ liệu **sau 28/08/2026** không thuộc Đoạn A hoặc Đoạn B. Đây là dữ liệu mới dành cho giai đoạn đánh giá sau khi chiến lược đã được khóa, được xử lý riêng ở các nhiệm vụ đánh giá cuối.

---

# PHẦN A — M3-A: BACKTEST THEO 4 BƯỚC, BẮT ĐẦU TỪ DỮ LIỆU M2

# 8. ĐIỂM BẮT ĐẦU CỦA M3-A

M3-A bắt đầu khi đã có **bộ bàn giao M2 Market clustering** và, để chạy chiến lược Combined, phải có thêm **bộ bàn giao Financial clustering** tương ứng.

Đầu vào Market từ M2 hiện được kỳ vọng gồm:

```text
M2/artifacts/m2-final-handoff-v1/
├── m2_cluster_labels_for_m3.csv
├── m2_cluster_profiles_for_m3.csv
├── m2_transition_turnover_reference.csv
└── m2_to_m3_handoff_manifest.json
```

Financial clustering phải có bộ bàn giao tương đương về:
- cluster label;
- cluster profile;
- cấu hình/model version;
- `available_at` hoặc thông tin PIT tương đương;
- manifest/hash/provenance.

Tên file Financial cụ thể phải lấy từ bộ bàn giao thật; không tự invent tên nếu upstream chưa seal.

M3-A **không chạy lại M2 clustering**. M3 chỉ sử dụng kết quả đã bàn giao.

---

# 9. LUỒNG HOẠT ĐỘNG DUY NHẤT CỦA BACKTEST

Từ lúc có dữ liệu M2, toàn bộ M3-A được tổ chức theo đúng 4 bước:

```text
ĐIỂM BẮT ĐẦU
Có dữ liệu M2 Market + Financial clustering
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

Bốn bước này được lặp lại cho đến hết Đoạn A hoặc Đoạn B.

Sau khi đã chạy xong 4 bước trên cho toàn bộ lịch sử mới tính các performance metrics và so sánh benchmark.

---

# 10. TỔNG QUAN NHIỆM VỤ NẰM TRONG 4 BƯỚC

## BƯỚC 1 — CHỌN CỔ PHIẾU

Gồm 7 nhiệm vụ con:

```text
1.1  Xác minh dữ liệu M2 Market
1.2  Xác minh dữ liệu Financial clustering
1.3  Căn chỉnh Market và Financial theo thời gian/PIT
1.4  Tạo Candidate Universe
1.5  Tính 3 tiêu chí Market + 3 tiêu chí Financial
1.6  Xếp hạng Combined
1.7  Chọn top 30% và tạo Target Portfolio
```

Kết quả Bước 1:

```text
target_portfolio tại một decision_date
```

---

## BƯỚC 2 — GIẢ LẬP MUA/BÁN

Gồm 7 nhiệm vụ con:

```text
2.1  Tìm phiên giao dịch hợp lệ kế tiếp
2.2  Xác định danh mục đang nắm giữ
2.3  So danh mục hiện tại với Target Portfolio
2.4  Tạo BUY / SELL / HOLD
2.5  Kiểm tra khả năng thực hiện giao dịch
2.6  Xử lý giao dịch thất bại và Cash
2.7  Chốt Executed Portfolio và Trade Ledger
```

Kết quả Bước 2:

```text
danh mục thực tế sau giao dịch
```

---

## BƯỚC 3 — GIỮ VÀ TÍNH LỜI/LỖ

Gồm 6 nhiệm vụ con:

```text
3.1  Xác định thời gian nắm giữ
3.2  Tính lợi suất từng cổ phiếu
3.3  Tính đóng góp lợi suất từng cổ phiếu
3.4  Tính lợi suất toàn danh mục
3.5  Cập nhật NAV
3.6  Tính trọng số cuối kỳ
```

Kết quả Bước 3:

```text
portfolio_return
NAV
pre_trade_weight cho tháng tiếp theo
```

---

## BƯỚC 4 — THÁNG SAU TÁI CÂN BẰNG

Gồm 6 nhiệm vụ con:

```text
4.1  Sang decision_date tiếp theo
4.2  Chạy lại Bước 1 với dữ liệu mới nhưng rule cũ
4.3  Nhận Target Portfolio mới
4.4  So Target mới với pre_trade_weight
4.5  Tính turnover và bắt đầu giao dịch mới
4.6  Quay lại Bước 2 và lặp chu kỳ
```

Kết quả Bước 4:

```text
một vòng backtest mới bắt đầu
```

---

# 11. BƯỚC 1 — CHỌN CỔ PHIẾU

Mục tiêu của toàn Bước 1:

> Tại một `decision_date`, xác định chính xác chiến lược muốn nắm những mã nào và tỷ trọng mục tiêu của từng mã.

Bước 1 kết thúc khi tạo được:

```text
target_portfolios_combined.csv
```

và hai danh mục đối chứng nếu cần:

```text
target_portfolios_market_only.csv
target_portfolios_financial_only.csv
```

---

# 11.1. NHIỆM VỤ 1.1 — XÁC MINH DỮ LIỆU M2 MARKET

## Mục đích

Xác nhận dữ liệu Market mà M3 sắp dùng đúng là kết quả M2 đã khóa.

## Đầu vào

```text
m2_cluster_labels_for_m3.csv
m2_cluster_profiles_for_m3.csv
m2_transition_turnover_reference.csv
m2_to_m3_handoff_manifest.json
```

## Thực hiện cụ thể

### Việc 1 — Đọc manifest trước

Không mở một file CSV bất kỳ rồi dùng luôn.

Trước tiên đọc:

```text
m2_to_m3_handoff_manifest.json
```

để biết:
- version;
- hash;
- `K_market`;
- model;
- feature set;
- khoảng thời gian;
- file nào là canonical.

### Việc 2 — Kiểm tra hash

Hash của file thực tế phải khớp manifest.

Nếu không khớp:

```text
MARKET_HANDOFF_READY = FALSE
```

và dừng.

### Việc 3 — Kiểm tra K và model

M2 hiện được bàn giao với model đã freeze.

M3 không được:
- chọn lại K;
- chạy lại K-Means;
- thay scaling;
- chọn cluster khác vì backtest đẹp hơn.

### Việc 4 — Kiểm tra từng `decision_date`

Với mỗi ngày M2 có snapshot:
- mỗi mã có tối đa một Market cluster label;
- không duplicate key;
- cluster label nằm trong tập hợp hợp lệ.

### Việc 5 — Xác nhận hai đoạn lịch sử

```text
A: 30/11/2023 → 24/01/2025
B: 27/02/2026 → 28/08/2026
```

Khoảng giữa:

```text
25/01/2025 → 26/02/2026
```

là gap, không được tự lấp.

## Đầu ra

```text
market_handoff_validation.json
MARKET_HANDOFF_READY = TRUE|FALSE
```

## Sang nhiệm vụ tiếp theo khi

```text
MARKET_HANDOFF_READY = TRUE
```

---

# 11.2. NHIỆM VỤ 1.2 — XÁC MINH DỮ LIỆU FINANCIAL CLUSTERING

## Mục đích

Xác nhận mỗi Financial cluster state có thể được sử dụng an toàn tại đúng thời điểm lịch sử.

## Đầu vào

Bộ bàn giao Financial clustering đã seal.

Tối thiểu phải có:
- ticker/security id;
- Financial cluster label;
- profile;
- model/version;
- `period_end`;
- `available_at`;
- revision/vintage nếu có;
- manifest/hash.

## Thực hiện cụ thể

### Việc 1 — Phân biệt các mốc thời gian

Không được nhầm:

```text
period_end
financial_snapshot_date
available_at
```

Trong M3, mốc quan trọng để tránh look-ahead là:

```text
available_at
```

### Việc 2 — Kiểm tra `available_at`

Mỗi record chính thức phải có thể xác định được thời điểm thông tin thực sự có sẵn.

Nếu thiếu:

```text
FINANCIAL_HANDOFF_READY = FALSE
```

### Việc 3 — Kiểm tra revision

Nếu cùng một kỳ có:
- bản gốc;
- bản điều chỉnh;

phải giữ được lineage/vintage.

Không được gộp hết thành một giá trị mới nhất rồi áp ngược vào quá khứ.

### Việc 4 — Kiểm tra cluster label

- không duplicate trái quy tắc;
- nhãn nằm trong tập hợp hợp lệ;
- truy được về model/config đã tạo ra nhãn.

## Đầu ra

```text
financial_handoff_validation.json
FINANCIAL_HANDOFF_READY = TRUE|FALSE
```

## Sang nhiệm vụ tiếp theo khi

Cả hai:

```text
MARKET_HANDOFF_READY = TRUE
FINANCIAL_HANDOFF_READY = TRUE
```

---

# 11.3. NHIỆM VỤ 1.3 — CĂN CHỈNH MARKET VÀ FINANCIAL THEO PIT

## Mục đích

Tại mỗi `decision_date` của Market, xác định:

> Financial clustering snapshot nào đã thực sự tồn tại và được phép sử dụng tại thời điểm đó?

Nhiệm vụ này chỉ **căn chỉnh hai kết quả phân cụm theo thời gian**.

Nhiệm vụ 1.3:

```text
KHÔNG chọn mã
KHÔNG lấy danh sách ticker
KHÔNG giao hai danh sách mã
KHÔNG tạo Candidate Universe
```

Việc lấy danh sách mã và tạo Candidate Universe chỉ bắt đầu ở **Nhiệm vụ 1.4**.

---

## Đầu vào

### Market clustering

Các Market clustering snapshot đã được M2 bàn giao, tối thiểu xác định được:

```text
decision_date
market_snapshot_id
market_snapshot_date
```

### Financial clustering

Các Financial clustering snapshot đã được xác minh, tối thiểu xác định được:

```text
financial_snapshot_id
financial_period_end
financial_available_at
```

Trong đó:

```text
financial_available_at
```

là thời điểm Financial snapshot đã thực sự có thể được biết và sử dụng.

---

## Luồng thực hiện

```text
BẮT ĐẦU TẠI MỘT decision_date
        ↓
Xác định Market clustering snapshot
ứng với decision_date
        ↓
Tìm các Financial clustering snapshot
đã available tại thời điểm đó
        ↓
Chỉ giữ Financial snapshot thỏa:
financial_available_at <= decision_date
        ↓
Nếu có nhiều Financial snapshot hợp lệ
→ chọn snapshot phù hợp theo
PIT/revision rule đã khóa
        ↓
Ghép:
Market snapshot
+
Financial snapshot
        ↓
Tạo cặp snapshot đã căn PIT
        ↓
Bàn giao sang Nhiệm vụ 1.4
```

---

## Thực hiện cụ thể

### Việc 1 — Xác định Market snapshot

Với mỗi:

```text
decision_date
```

xác định Market clustering snapshot tương ứng.

Ví dụ:

```text
decision_date = 30/04/2024

market_snapshot_id = MARKET_20240430
```

Ở bước này chưa đọc danh sách cổ phiếu bên trong cluster.

---

### Việc 2 — Tìm các Financial snapshot đã tồn tại

Tìm các Financial clustering snapshot có:

```text
financial_available_at <= decision_date
```

Ví dụ:

```text
decision_date = 30/04/2024
```

có:

```text
Financial snapshot A
available_at = 25/03/2024

Financial snapshot B
available_at = 20/05/2024
```

Kết quả:

```text
25/03/2024 <= 30/04/2024
→ snapshot A được phép sử dụng

20/05/2024 > 30/04/2024
→ snapshot B là thông tin tương lai
→ không được sử dụng
```

---

### Việc 3 — Chọn Financial snapshot được sử dụng

Nếu chỉ có một Financial snapshot hợp lệ:

```text
→ sử dụng snapshot đó
```

Nếu có nhiều Financial snapshot cùng thỏa:

```text
financial_available_at <= decision_date
```

thì chọn snapshot theo **PIT/revision rule đã được khóa của Financial pipeline** (tạm thời chưa có rule).

Không tự tạo quy tắc revision mới trong M3.

---

### Việc 4 — Tạo cặp Market–Financial snapshot

Sau khi xác định được hai phía, lưu:

```text
Market snapshot tại decision_date
+
Financial snapshot hợp lệ theo PIT
```

Ví dụ:

```text
decision_date = 30/04/2024

market_snapshot_id
= MARKET_20240430

financial_snapshot_id
= FINANCIAL_20240325

financial_available_at
= 25/03/2024

alignment_status
= PIT_ALIGNED
```

---

### Việc 5 — Không có Financial snapshot hợp lệ

Nếu tại một `decision_date` chưa có Financial clustering snapshot nào thỏa:

```text
financial_available_at <= decision_date
```

thì ghi:

```text
NO_PIT_FINANCIAL_SNAPSHOT
```

Không sử dụng Financial snapshot trong tương lai để lấp vào.

---

## Đầu ra

```text
aligned_market_financial_snapshots.csv
```

Mỗi dòng tối thiểu có:

```text
decision_date

market_snapshot_id
market_snapshot_date

financial_snapshot_id
financial_period_end
financial_available_at

alignment_status
```

Ví dụ:

```text
decision_date          30/04/2024
market_snapshot_id     MARKET_20240430
market_snapshot_date   30/04/2024

financial_snapshot_id  FINANCIAL_20240325
financial_period_end   31/12/2023
financial_available_at 25/03/2024

alignment_status       PIT_ALIGNED
```

---

## Kiểm tra bắt buộc

Mọi Financial snapshot được ghép phải thỏa:

```text
financial_available_at <= decision_date
```

Không được có:

```text
financial_available_at > decision_date
```

Nếu có thì đó là lỗi look-ahead.

Ngoài ra:

```text
- không lấy ticker tại bước này;
- không chọn cluster tại bước này;
- không lấy member của cluster;
- không lọc cổ phiếu;
- không tạo Candidate Universe.
```

---

## Điều kiện hoàn thành

Nhiệm vụ 1.3 hoàn thành khi, với mỗi `decision_date`, có thể xác định rõ:

```text
Market snapshot nào được dùng?
+
Financial snapshot nào đã available và được phép dùng?
```

và tạo được cặp:

```text
Market snapshot
↔
Financial snapshot PIT-safe
```

---

## Bàn giao sang Nhiệm vụ 1.4

Nhiệm vụ 1.3 bàn giao các cặp snapshot đã căn PIT cho Nhiệm vụ 1.4.

Nhiệm vụ 1.4 mới bắt đầu:

```text
Mở Market clustering snapshot
        ↓
Lấy danh sách mã theo rule Market
        ↓
Mở Financial clustering snapshot
        ↓
Lấy danh sách mã theo rule Financial
        ↓
Tạo Candidate Universe
```

Tóm lại:

```text
1.3
CĂN MARKET VÀ FINANCIAL THEO THỜI GIAN/PIT

        ↓

1.4
MỚI LẤY DANH SÁCH MÃ
VÀ TẠO CANDIDATE UNIVERSE
```

---

# 11.4. NHIỆM VỤ 1.4 — TẠO CANDIDATE UNIVERSE

## Mục đích

Tại mỗi `decision_date`, xác định các mã đủ điều kiện ở cả Market và Financial, sau đó kết hợp hai tập để tạo Candidate Universe.

## Luồng thực hiện

```text
BẮT ĐẦU TẠI decision_date
        ↓
Lấy Market cluster state từ M2
        ↓
Áp rule chọn Market cluster
(nếu chiến lược có quy định chọn cluster)
        ↓
Market Eligible Pool
        │
        │
        │
Lấy Financial cluster state
        ↓
Chỉ sử dụng Financial state thỏa:
available_at <= decision_date
        ↓
Áp rule chọn Financial cluster
(nếu chiến lược có quy định chọn cluster)
        ↓
Financial Eligible Pool
        │
        ↓
Market Eligible Pool
        ∩
Financial Eligible Pool
        ↓
CANDIDATE UNIVERSE
```

## Điều kiện phía Market

Một mã được đưa vào `Market Eligible Pool` khi:

```text
- có Market cluster state tại decision_date;
- security_id hợp lệ;
- thỏa rule chọn Market cluster đã được khóa.
```

Nếu chưa có quy định chọn Market cluster thì phải ghi:

```text
MARKET_CLUSTER_SELECTION_RULE = PENDING
```

Không tự chọn cluster lớn nhất, cluster 0 hay cluster có profile tốt nhất.

## Điều kiện phía Financial

Một mã được đưa vào `Financial Eligible Pool` khi:

```text
- có Financial cluster state;
- available_at <= decision_date;
- security_id map được với Market;
- thỏa rule chọn Financial cluster đã được khóa.
```

Nếu chưa có quy định chọn Financial cluster thì ghi:

```text
FINANCIAL_CLUSTER_SELECTION_RULE = PENDING
```

## Tạo Candidate Universe

Sau khi có hai tập:

```text
Market Eligible Pool
Financial Eligible Pool
```

thực hiện:

```text
Candidate Universe
=
Market Eligible Pool
∩
Financial Eligible Pool
```

Ví dụ:

```text
Market Eligible Pool:
FPT
HPG
VNM
MWG
VCB

Financial Eligible Pool:
FPT
HPG
VCB
ACB

Candidate Universe:
FPT
HPG
VCB
```

## Ghi lại mã bị loại

Cần lưu lý do đối với các mã không được đưa vào Candidate Universe, ví dụ:

```text
MARKET_STATE_MISSING
FINANCIAL_STATE_MISSING
FINANCIAL_NOT_AVAILABLE_AT_DECISION_DATE
ID_MAPPING_FAILED
MARKET_CLUSTER_NOT_SELECTED
FINANCIAL_CLUSTER_NOT_SELECTED
```

## Đầu ra

```text
combined_candidates.csv
candidate_eligibility_audit.csv
```

Trong đó `combined_candidates.csv` tối thiểu gồm:

```text
decision_date
security_id
ticker
market_cluster_label
financial_cluster_label
```

## Điều kiện hoàn thành

Phải chứng minh được tại từng `decision_date`:

```text
Candidate Universe
=
Market Eligible Pool
∩
Financial Eligible Pool
```

và giải thích được vì sao từng mã được đưa vào hoặc bị loại.

## Bàn giao sang nhiệm vụ tiếp theo

Candidate Universe được chuyển sang nhiệm vụ tiếp theo để:

```text
Tính MC1 MC2 MC3
+
Tính FC1 FC2 FC3
        ↓
Combined Ranking
        ↓
Top 30%
```

---

# 11.5. NHIỆM VỤ 1.5 — TÍNH 6 TIÊU CHÍ

## Mục đích

Đánh giá các mã đã nằm trong Candidate Universe.

6 tiêu chí:

```text
Market:
MC1
MC2
MC3

Financial:
FC1
FC2
FC3
```

## Vai trò

```text
Eligibility
→ mã có được vào Candidate Universe hay không

6 tiêu chí
→ mã đã vào thì mạnh/yếu ra sao để xếp hạng
```

## Trước khi tính

Mỗi tiêu chí phải có contract:

```text
criterion_id
name
description
formula
source_fields
source_artifact
missing_rule
tie_rule
```

Nếu mentor chưa cung cấp công thức thật:

```text
RANKING BLOCKED
```

Không tự sáng tác.

## Tính MC1..MC3

Chỉ dùng dữ liệu Market đã tồn tại tại `decision_date`.

Không dùng giá phiên t+1.

## Tính FC1..FC3

Chỉ dùng Financial state đã căn PIT.

Không dùng revision công bố sau `decision_date`.

## Đầu ra

```text
decision_features.csv
```

Mỗi dòng có tối thiểu:

```text
decision_date
ticker
MC1
MC2
MC3
FC1
FC2
FC3
criterion_status
```

---

# 11.6. NHIỆM VỤ 1.6 — XẾP HẠNG COMBINED

## Mục đích

Từ 6 tiêu chí, tạo thứ hạng cuối cùng trong Candidate Universe.

## Điều bắt buộc phải có trước

```text
combined_ranking_rule
```

Rule phải nói rõ:
- Ba tiêu chí thị trường phải được kết hợp ra sao để biết một mã có vị trí Market tốt hay xấu?
- Ba tiêu chí tài chính phải được kết hợp ra sao để biết một mã có vị trí Financial tốt hay xấu?
- Sau khi đã có kết quả riêng của Market và Financial, phải kết hợp hai kết quả đó như thế nào để tạo một thứ hạng cuối cùng?
- nếu hai mã bằng điểm hoặc bằng thứ hạng thì ưu tiên mã nào?

Không được tự chọn:
- weighted score;
- rank average;
- lexicographic;
- filter + rank;

nếu chưa được duyệt.

## Thực hiện

Ví dụ về output:

```text
Ticker  Combined Rank
FPT     1
VNM     2
HPG     3
MWG     4
...
```

## Đầu ra

```text
combined_ranking.csv
```

---

# 11.7. NHIỆM VỤ 1.7 — CHỌN TOP 30% VÀ TẠO TARGET PORTFOLIO

## Mục đích

Chuyển ranking thành danh mục mà chiến lược muốn nắm.

## Thực hiện

### Việc 1 — Đếm số ứng viên

Ví dụ:

```text
N_candidates = 11
```

### Việc 2 — Tính số lượng cần chọn

```text
n_select
=
ceil(0.30 × N_candidates)
```

Ví dụ:

```text
ceil(0.30 × 11)
=
4
```

### Việc 3 — Chọn rank cao nhất

Chọn rank:

```text
1
2
3
4
```

### Việc 4 — Gán equal weight

```text
target_weight
=
1 / n_select
```

4 mã:

```text
25% mỗi mã
```

## Ví dụ cần PASS

```text
8  → 3
10 → 3
11 → 4
15 → 5
20 → 6
```

## Đầu ra cuối Bước 1

```text
target_portfolios_combined.csv
```

Ví dụ:

```text
decision_date  ticker  rank  target_weight
30/04/2024    FPT     1     0.25
30/04/2024    VNM     2     0.25
30/04/2024    HPG     3     0.25
30/04/2024    MWG     4     0.25
```

## Bước 1 hoàn thành khi

Người thực hiện trả lời được:

> Tại ngày này chiến lược muốn nắm mã nào và target weight là bao nhiêu?

---

# 12. BƯỚC 2 — GIẢ LẬP MUA/BÁN

Mục tiêu:

> Chuyển Target Portfolio của Bước 1 thành danh mục thực tế sau khi xét phiên giao dịch và khả năng thực hiện.

---

# 12.1. NHIỆM VỤ 2.1 — TÌM PHIÊN GIAO DỊCH HỢP LỆ KẾ TIẾP

## Câu hỏi mà 2.1 trả lời

> Sau khi quyết định danh mục, chính xác ngày nào ta thực hiện giao dịch?

## Đầu vào

```text
decision_date
trading calendar
```

## Yêu cầu thực hiện

Tìm phiên đầu tiên thỏa:

```text
execution_date > decision_date
```

## Tại sao phải làm như vậy?

Vì ngày `decision_date` là lúc chiến lược đưa ra quyết định.

Nếu vừa dùng dữ liệu đóng cửa ngày `30/04` để quyết định danh mục, rồi lại giả sử mình mua được ngay chính giá đóng cửa đó, có nguy cơ tạo ra giả định thực thi không hợp lý.

Nên logic là:

```text
30/04: Đọc dữ liệu + ra quyết định
  ↓ (phiên hợp lệ kế tiếp)
02/05: Thực hiện giao dịch
```

## Ví dụ

Giả sử:
- `decision_date = 30/04/2024`

Nhưng:
- `01/05/2024`: ngày nghỉ
- `02/05/2024`: có giao dịch

Thì:
- `execution_date = 02/05/2024`

Chứ không được:
- `decision_date = 30/04` → lấy luôn giá đóng cửa `30/04` để mua (nếu methodology quy định phải giao dịch ở phiên hợp lệ kế tiếp).

## Đầu ra của 2.1

Một mapping như:

```text
decision_date → execution_date
```

Ví dụ:

```text
30/04/2024 → 02/05/2024
```

Sau đó giao cho 2.2–2.5 sử dụng.

---

# 12.2. NHIỆM VỤ 2.2 — XÁC ĐỊNH DANH MỤC ĐANG NẮM GIỮ

## Lần đầu của một segment

```text
stocks = 0
cash = 100%
```

## Các tháng sau

Dùng:

```text
pre_trade_weight
```

từ cuối Bước 3 của tháng trước.

Không reset equal-weight.

---

# 12.3. NHIỆM VỤ 2.3 — SO DANH MỤC HIỆN TẠI VỚI TARGET

## Câu hỏi mà 2.3 trả lời

> So với cái đang có, danh mục mới yêu cầu thay đổi những mã nào?

## Yêu cầu thực hiện

Tạo union (tập hợp) của:
- Các mã hiện đang giữ (`pre_trade_weight`);
- Các mã có trong Target mới (`target_weight`).

## Tại sao cần union?

Nếu chỉ lấy các mã trong Target mới, HPG sẽ biến mất.

Nhưng HPG đang được giữ 22%.

Nếu HPG không còn trong Target, điều đó có nghĩa:

```text
HPG target = 0% → phải SELL
```

Vì vậy mọi mã ở cả hai phía đều phải được đưa vào bảng so sánh.

## Ví dụ

Giả sử:
- **Danh mục hiện tại:**
  - FPT: 28%
  - HPG: 22%
  - MWG: 27%
- **Target mới:**
  - FPT: 25%
  - MWG: 25%
  - VNM: 25%
  - SSI: 25%

Phải tạo bảng:

| Mã (`ticker`) | Hiện tại (`pre_trade_weight`) | Target (`target_weight`) |
| :--- | :--- | :--- |
| **FPT** | 28% (0.28) | 25% (0.25) |
| **HPG** | 22% (0.22) | 0% (0.00) |
| **MWG** | 27% (0.27) | 25% (0.25) |
| **VNM** | 0% (0.00) | 25% (0.25) |
| **SSI** | 0% (0.00) | 25% (0.25) |

Hoặc dạng dữ liệu:

```text
ticker  pre_trade_weight  target_weight
FPT     0.28              0.25
HPG     0.22              0.00
MWG     0.27              0.25
VNM     0.00              0.25
SSI     0.00              0.25
```

## Đầu ra của 2.3

Một bảng gồm:

```text
ticker
pre_trade_weight
target_weight
```

Đây là đầu vào trực tiếp cho Nhiệm vụ 2.4.

---

# 12.4. NHIỆM VỤ 2.4 — TẠO BUY / SELL / HOLD

Tính:

```text
delta_weight
=
target_weight - pre_trade_weight
```

Quy tắc:

```text
delta > 0 → BUY
delta < 0 → SELL
delta = 0 → HOLD
```

---

# 12.5. NHIỆM VỤ 2.5 — KIỂM TRA KHẢ NĂNG GIAO DỊCH

## Mục đích

Nhiệm vụ 2.5 trả lời câu hỏi:

> Tại `execution_date`, các lệnh BUY/SELL được tạo ở 2.4 có thực sự thực hiện được hay không?

Ở đây chưa xử lý hậu quả khi giao dịch thất bại. Nhiệm vụ 2.5 chỉ có nhiệm vụ **kiểm tra** và **phân loại** kết quả thực thi.

Luồng tổng thể:

```text
Target Portfolio
        ↓
2.2 – 2.4: Xác định cần BUY / SELL / HOLD
       ↓
2.5: Kiểm tra trạng thái giao dịch từng lệnh tại execution_date
        ↓
Nếu mã KHÔNG giao dịch được theo rule đã khóa
        → EXECUTION_FAILED
        → sang 2.6 xử lý

Nếu mã giao dịch được
        ↓
Việc 3 — Kiểm tra execution price / price basis
        ↓
Nếu giá hợp lệ + price basis hợp lệ
        → SUCCESS

Nếu thiếu giá hoặc price basis chưa được chứng nhận
        → BACKTEST_BLOCKED
        → dừng, KHÔNG sang 2.6
```

File quy định: Kiểm tra `ticker`, `execution_date`, trạng thái giao dịch (`trading_status`) và `execution price/basis`; đồng thời **không được forward-fill** hoặc **tự tạo giá** khi thiếu.

## Đầu vào

Tối thiểu cần:
- `execution_date` (từ 2.1);
- `ticker`;
- `action` (từ 2.4: `BUY`, `SELL`, `HOLD`);
- `delta_weight`;
- Trạng thái giao dịch (`trading_status`) tại `execution_date`;
- Dữ liệu giá thực thi (`execution_price`);
- Price basis đã được khóa / chứng nhận;
- Các rule về khả năng giao dịch.

Ví dụ đầu vào:

```text
execution_date = 02/05/2024

FPT: action = BUY,  delta_weight = +25%
HPG: action = SELL, delta_weight = -20%
VCB: action = HOLD, delta_weight = 0%
```

## Các việc thực hiện chi tiết

### Việc 1 — Xác định mã nào thực sự cần kiểm tra execution

Các mã có hành động:
- `BUY`
- `SELL`

bắt buộc phải được kiểm tra khả năng giao dịch.

Nếu là `HOLD`:
- Không phát sinh lệnh mua/bán mới, nên thông thường không cần kiểm tra execution như một trade mới.
- Tuy nhiên, mã `HOLD` vẫn tiếp tục tồn tại trong danh mục nắm giữ (`holdings`) và chuyển sang Bước 3 bình thường.

Ví dụ:
```text
FPT BUY   → Cần kiểm tra execution
HPG SELL  → Cần kiểm tra execution
VCB HOLD  → Không phát sinh trade mới
```

### Việc 2 — Kiểm tra trạng thái giao dịch tại execution_date

Với từng lệnh `BUY` / `SELL`, phải xác định tại đúng ngày thực thi:
- Mã có được giao dịch hay không;
- Có bị đình chỉ / tạm ngừng (`SUSPENDED`) không;
- Có phiên hợp lệ hay không;
- Có dữ liệu đủ để mô phỏng giao dịch không.

Ví dụ:
- `FPT` tại `02/05/2024`: `trading_status = NORMAL` → Tiếp tục kiểm tra giá.
- `MWG` tại `02/05/2024`: `trading_status = SUSPENDED` → Không thể thực thi trade → `EXECUTION_FAILED`.

> [!IMPORTANT]
> **Điểm quan trọng:** Không được thấy ngày đó không giao dịch rồi tự ý chuyển sang ngày khác nếu methodology chưa có rule như vậy.

### Việc 3 — Kiểm tra giá thực thi

Nếu mã giao dịch bình thường, phải xác định có `execution_price` hợp lệ hay không.

Theo kế hoạch hiện tại, logic tổng thể đang dùng:
> Giá đóng cửa của phiên giao dịch hợp lệ kế tiếp (`execution_date`).

Nhưng price series sử dụng phải được xác minh đúng contract:
- Lấy `close` tại đúng `execution_date` với price basis hợp lệ → Có thể thực thi.

Tuyệt đối **KHÔNG ĐƯỢC**:
- Lấy giá ngày trước;
- Lấy giá ngày sau;
- Forward-fill giá thiếu;
- Tự tạo / nội suy giá;
- Đổi sang loại giá khác vì dữ liệu hiện tại thiếu.

Nếu price basis chưa được chứng nhận → Phải kích hoạt `BACKTEST_BLOCKED`.

### Việc 4 — Phân biệt rõ SUCCESS, EXECUTION_FAILED và BACKTEST_BLOCKED

Khóa rất rõ 3 trạng thái phân loại:

#### A. SUCCESS
- **Ý nghĩa:** Dữ liệu và methodology đều đầy đủ, và giao dịch có thể thực hiện.
- **Ví dụ:**
  ```text
  FPT: BUY 25%, execution_date = 02/05, trading_status = NORMAL, execution price hợp lệ
  → SUCCESS
  ```
- **Xử lý:** Lệnh đi thẳng sang Nhiệm vụ 2.7 để ghi nhận executed trade.

#### B. EXECUTION_FAILED
- **Ý nghĩa:** Methodology đã rõ, nhưng tại `execution_date` giao dịch cụ thể không thể thực hiện được trong thực tế.
- **Ví dụ:**
  - `MWG`: `BUY 25%`, `trading_status = SUSPENDED` → `EXECUTION_FAILED`
  - `HPG`: `SELL`, mã không giao dịch được theo rule đã khóa → `EXECUTION_FAILED`
- **Xử lý:** Trường hợp này **không dừng toàn bộ backtest ngay**, mà chuyển sang **Nhiệm vụ 2.6 — Xử lý giao dịch thất bại và Cash**.

#### C. BACKTEST_BLOCKED
- **Ý nghĩa:** Chưa đủ rule hoặc chưa đủ dữ liệu / chứng nhận contract để biết phải mô phỏng giao dịch như thế nào cho đúng phương pháp luận.
- **Ví dụ:**
  - Chưa rõ dùng `raw close` hay `adjusted close`;
  - `execution price basis` chưa được chứng nhận.
- **Xử lý:** Đây không phải "giao dịch thất bại" của thị trường, mà là **backtest chưa đủ điều kiện để chạy**. Khi đó:
  ```text
  BACKTEST_BLOCKED → DỪNG BACKTEST NGAY
  ```
  **Không được** biến nó thành `FAILED` rồi chuyển vốn sang Cash, vì làm như vậy sẽ che giấu lỗi phương pháp luận (methodology flaw).

### Việc 5 — Ghi rõ lý do (Failure Reason)

Mỗi lệnh `BUY`/`SELL` phải ghi nhận tối thiểu:
- `execution_status`
- `failure_reason`

Ví dụ:

| Ticker | Action | Status | Failure Reason |
| :--- | :--- | :--- | :--- |
| **FPT** | `BUY` | `SUCCESS` | — |
| **MWG** | `BUY` | `EXECUTION_FAILED` | `TRADING_SUSPENDED` |
| **HPG** | `SELL` | `EXECUTION_FAILED` | `NO_EXECUTABLE_TRADE` |
| **VNM** | `BUY` | `BACKTEST_BLOCKED` | `PRICE_BASIS_UNCERTIFIED` |

Lý do phải cụ thể để phục vụ kiểm toán (audit). Không được chỉ ghi chung chung là `FAILED` mà không rõ nguyên nhân.

### Việc 6 — Chuyển kết quả đúng nơi tiếp nhận

Sau Nhiệm vụ 2.5:
- **Nếu `SUCCESS`:** Ghi nhận giao dịch thực hiện được → Chuyển sang Nhiệm vụ 2.7.
- **Nếu `EXECUTION_FAILED`:** Chuyển sang Nhiệm vụ 2.6 để áp dụng rule xử lý failed execution (chuyển Cash hoặc giữ tiếp).
- **Nếu `BACKTEST_BLOCKED`:** Dừng backtest ngay; không tạo Executed Portfolio chính thức.

## Đầu ra đề xuất của 2.5

Tạo bảng kiểm tra thực thi: `execution_check.csv` với các cột tối thiểu:

```text
decision_date
execution_date
ticker
pre_trade_weight
target_weight
delta_weight
action
trading_status
execution_price
price_basis
execution_status
failure_reason
```

Ví dụ bản ghi:
- `FPT`: `BUY`, `+25%`, `NORMAL`, price hợp lệ → `SUCCESS`
- `MWG`: `BUY`, `+25%`, `SUSPENDED` → `EXECUTION_FAILED`
- `VNM`: `BUY`, `+25%`, price basis chưa chứng nhận → `BACKTEST_BLOCKED`

## Điều kiện hoàn thành nhiệm vụ 2.5

2.5 chỉ hoàn thành khi mọi trade cần thực hiện đều được phân loại dứt khoát thành:
- `SUCCESS` hoặc
- `EXECUTION_FAILED`

và **không còn bất kỳ trường hợp `BACKTEST_BLOCKED` nào**.

Nếu vẫn còn dù chỉ 1 trường hợp `BACKTEST_BLOCKED` ảnh hưởng đến backtest chính thức thì **chưa được chuyển sang Nhiệm vụ 2.7**.

## Cách hiểu đơn giản nhất

```text
2.4: "Tôi cần mua/bán gì?"
  ↓
2.5: "Những lệnh đó tại execution_date có thực hiện được không?"
  ↓
  ├── SUCCESS          → Thực hiện được → sang 2.7
  ├── EXECUTION_FAILED → Không thực hiện được → sang 2.6 xử lý
  └── BACKTEST_BLOCKED → Chưa biết cách mô phỏng đúng → DỪNG
```

---

# 12.6. NHIỆM VỤ 2.6 — XỬ LÝ GIAO DỊCH THẤT BẠI VÀ CASH

## Mục đích

Nhiệm vụ 2.6 xử lý các lệnh đã được 2.5 xác định là:

```text
EXECUTION_FAILED
```

Tức là:
- Methodology đã đầy đủ;
- Đã đến `execution_date`;
- Biết rõ lệnh cần `BUY` hay `SELL`;
- Nhưng giao dịch thực tế không thực hiện được (do cổ phiếu tạm ngừng, không có thanh khoản, v.v.).

Nhiệm vụ 2.6 trả lời câu hỏi:

> Nếu BUY hoặc SELL thất bại thì danh mục thực tế và Cash sẽ thay đổi như thế nào?

> [!WARNING]
> **Lưu ý quan trọng:** `BACKTEST_BLOCKED` **không** đi vào Nhiệm vụ 2.6. Nếu 2.5 phát hiện `BACKTEST_BLOCKED`, toàn bộ backtest phải dừng để xử lý nguyên nhân phương pháp luận.

## Các việc thực hiện chi tiết

### Việc 1 — Phân loại EXECUTION_FAILED

Mỗi lệnh thất bại phải kiểm tra `action` từ 2.4 để phân nhánh xử lý:
- `action = BUY` → `BUY_FAILED`
- `action = SELL` → `SELL_FAILED`

Hai trường hợp này có bản chất và cách xử lý vốn hoàn toàn khác nhau.

---

### Việc 2 — Xử lý BUY_FAILED

**Tình huống:** Chiến lược muốn mua một mã nhưng tại `execution_date` không mua được.

Ví dụ: Target gồm 4 mã equal-weight (25% mỗi mã): FPT, HPG, MWG, VCB.
- `MWG`: `BUY 25%` → `EXECUTION_FAILED` → `BUY_FAILED`.

**Quy tắc đã khóa (Rule đã khóa):**
Phần vốn dự kiến dùng để mua mã đó: **tiếp tục giữ ở Cash**.

Tuyệt đối **KHÔNG**:
- Chọn mã khác thay thế;
- Chuyển tiền cho mã có rank kế tiếp;
- Chia lại tiền cho những mã còn lại.

Ví dụ kết quả:
- `FPT`: `BUY SUCCESS` → `25%`
- `HPG`: `BUY SUCCESS` → `25%`
- `MWG`: `BUY FAILED` → `0%`
- `VCB`: `BUY SUCCESS` → `25%`
- `Cash` = `25%`

Danh mục thực tế sau đó:

```text
FPT:  25%
HPG:  25%
VCB:  25%
Cash: 25%
```

---

### Việc 3 — Xử lý SELL_FAILED

**Tình huống:** Chiến lược muốn bán bớt hoặc bán hết một mã nhưng tại `execution_date` không bán được.

Ví dụ:
```text
HPG: pre_trade_weight = 25%, target_weight = 0%
     delta_weight = -25% → SELL
```
Nhưng tại `execution_date`: HPG không giao dịch được → `EXECUTION_FAILED` → `SELL_FAILED`.

**Cách hiểu bắt buộc:**
- Khi SELL thất bại: **Không được coi cổ phiếu đã bán**.
- Do đó: **HPG vẫn tiếp tục nằm trong danh mục nắm giữ (`holdings`)**.
- Và: **`SELL_FAILED` KHÔNG tạo ra Cash**.

> [!CAUTION]
> **Tuyệt đối không được làm:**
> Coi `HPG 25% → SELL_FAILED → HPG 0% và Cash +25%`. Tiền bán đó thực tế chưa hề thu được!

**Trạng thái của mã SELL_FAILED:**
Mã đó sẽ được ghi nhận:
- `execution_status = SELL_FAILED`
- `holding_status = FORCED_HOLD` *(Thuật ngữ đề xuất)*

`FORCED_HOLD` có nghĩa là: Chiến lược muốn thoát vị thế, nhưng do không bán được nên buộc phải tiếp tục nắm giữ.

Ví dụ:
```text
HPG: target_weight = 0%, executed_weight > 0%
     execution_status = SELL_FAILED, holding_status = FORCED_HOLD
```

*(Lưu ý: Tên `FORCED_HOLD` hiện là đề xuất, chưa phải terminology đã khóa vĩnh viễn trong file).*

---

### Việc 4 — Tính lại Cash thực sự khả dụng

Đây là bước cực kỳ quan trọng sau khi có lệnh SELL thất bại.

Cash thực sự có thể dùng để thực hiện các lệnh BUY chỉ gồm:

```text
Cash khả dụng = Cash có sẵn trước giao dịch + Cash thu được từ SELL thành công
```

**Tuyệt đối không cộng tiền từ SELL thất bại.**

Ví dụ trước giao dịch:
- Danh mục: FPT 25%, HPG 25%, VCB 25%, Cash 25% (tổng NAV 100 triệu)
- Cần: `SELL HPG 25 triệu`, `SELL VCB 25 triệu`
- Kết quả:
  - `HPG` → `SELL_FAILED`
  - `VCB` → `SELL_SUCCESS`

Cash thực có để mua:
```text
  Cash ban đầu:     25 triệu
+ SELL VCB:         25 triệu
+ SELL HPG:          0 triệu (thất bại)
---------------------------------------
= Available Cash:   50 triệu (không phải 75 triệu)
```

---

### Việc 5 — So Cash khả dụng với tổng nhu cầu BUY

Giả sử Target mới cần mua 3 mã mới:
- `BUY MWG`: 25 triệu
- `BUY VNM`: 25 triệu
- `BUY SSI`: 25 triệu
- **Tổng nhu cầu BUY:** 75 triệu

Nhưng Cash thực có (`available_cash`) chỉ có: **50 triệu**.

Khi đó:
```text
available_cash < total_required_buy_cash (50 triệu < 75 triệu)
```
→ Không thể thực hiện toàn bộ các lệnh BUY theo đúng Target. Đây là hậu quả trực tiếp bắt nguồn từ `SELL_FAILED`.

---

### Việc 6 — Xử lý trường hợp Cash vẫn đủ

Nếu:
```text
available_cash >= total_required_buy_cash
```
thì các lệnh BUY còn lại vẫn thực hiện bình thường theo đúng tỷ trọng dự kiến.

Ví dụ:
- Cash thực có = 60 triệu
- Tổng BUY cần = 50 triệu
- Đủ tiền → Mua bình thường, lượng tiền mặt dư còn lại (10 triệu) tiếp tục giữ ở Cash.

---

### Việc 7 — Xử lý trường hợp Cash không đủ

Nếu:
```text
available_cash < total_required_buy_cash
```
thì hiện file kế hoạch chưa có rule chính thức được phê duyệt từ cấp trên.

**Phương án đề xuất để đưa ra chốt:**
Giảm tất cả các lệnh BUY theo cùng một tỷ lệ (`execution_scale`), thay vì tự tiện chọn mã nào được mua trước.

Công thức tính tỷ lệ điều chỉnh:
```text
execution_scale = available_cash / total_required_buy_cash
```

Ví dụ:
- Cash có: 50 triệu
- Cash cần: 75 triệu
- `execution_scale = 50 / 75 = 66.67%`

Mỗi lệnh BUY dự kiến sẽ được phân bổ lại:
- `MWG`: 25 triệu × 66.67% ≈ 16.67 triệu
- `VNM`: 25 triệu × 66.67% ≈ 16.67 triệu
- `SSI`: 25 triệu × 66.67% ≈ 16.67 triệu
- **Tổng mua:** ≈ 50 triệu

Nguyên tắc tuân thủ:
- Không sử dụng margin / đòn bẩy;
- Không tự ý chọn 2 mã rồi bỏ mã thứ 3;
- Không thay đổi thứ tự ranking;
- Không chọn mã khác thay thế.

> [!NOTE]
> **Trạng thái:** Phần này hiện vẫn phải coi là **PENDING (CẦN QUYẾT ĐỊNH)** cho đến khi chủ dự án / mentor phê duyệt chính thức.

---

### Việc 8 — Đưa mã SELL_FAILED vào danh mục thực tế

Mã `SELL_FAILED` vẫn phải xuất hiện đầy đủ trong Executed Portfolio.

Ví dụ cơ cấu danh mục thực tế (NAV = 100 triệu):
```text
FPT:   25.00 triệu
HPG:   25.00 triệu   ← SELL_FAILED / FORCED_HOLD
MWG:   16.67 triệu
VNM:   16.67 triệu
SSI:   16.67 triệu
Cash:   0.00 triệu
---------------------
Tổng: 100.00 triệu
```

HPG không còn nằm trong Target nhưng vẫn nằm trong Executed Portfolio, vì thực tế chưa bán được.

---

### Việc 9 — Mã SELL_FAILED vẫn sang Bước 3 bình thường

Vì danh mục vẫn đang thực tế sở hữu cổ phiếu đó nên nó phải tiếp tục:
- Được định giá theo giá thị trường;
- Tính return hàng ngày / theo kỳ;
- Ảnh hưởng trực tiếp đến NAV tổng;
- Ảnh hưởng đến trọng số cuối kỳ (`pre_trade_weight`).

Ví dụ: Kỳ tiếp theo `HPG return = -8%` thì danh mục vẫn phải chịu đầy đủ khoản lỗ đó. Tuyệt đối không được bỏ HPG khỏi tính toán return chỉ vì Target trước đó muốn loại bỏ nó.

---

### Việc 10 — Xử lý ở kỳ rebalance tiếp theo

Sang tháng sau, mã `SELL_FAILED` vẫn nằm trong `pre_trade_weight`.

Nếu Target của tháng mới vẫn yêu cầu:
```text
HPG target = 0%
```
thì:
```text
pre_trade_weight > 0
target_weight = 0
→ delta_weight < 0 → Tạo lại lệnh SELL một lần nữa
```
Sau đó lại kiểm tra khả năng giao dịch tại `execution_date` mới của kỳ đó.

Không tự động thử bán (retry) mỗi ngày giữa hai kỳ rebalance nếu chưa có rule retry riêng được phê duyệt.

## Đầu ra của 2.6

Sau khi xử lý các failed execution, cần xác định được tối thiểu:

```text
ticker
action
execution_status
failure_reason
target_weight
executed_weight
cash_effect
holding_status
```

Đồng thời xác định rõ:

```text
available_cash
```

thực sự còn bao nhiêu trước khi chốt Executed Portfolio ở Nhiệm vụ 2.7.

## Điều kiện chuyển sang 2.7

Chỉ chuyển sang 2.7 khi tất cả các lệnh:
- `SUCCESS` và
- `EXECUTION_FAILED`

đã được xử lý đầy đủ bằng rule hợp lệ.

Sau đó Nhiệm vụ 2.7 mới chốt: **Executed Portfolio** — danh mục thực tế cuối cùng sẽ được đưa sang Bước 3.

## Tóm gọn luồng Nhiệm vụ 2.6

```text
EXECUTION_FAILED
        ↓
   action là gì?
     /       \
   BUY       SELL
    ↓          ↓
BUY_FAILED   SELL_FAILED
    ↓          ↓
Tiền vẫn     Mã vẫn giữ (FORCED_HOLD)
ở Cash       Không tạo ra Cash
               ↓
        Tính Cash thực có
               ↓
       Cash đủ cho BUY?
          /          \
        Có           Không
        ↓              ↓
   BUY bình thường   Áp rule thiếu Cash (hiện PENDING)
               ↓
       Chuyển kết quả sang 2.7
```

---

# 12.7. NHIỆM VỤ 2.7 — CHỐT EXECUTED PORTFOLIO

Sau execution:

```text
Σ stock_weight + cash_weight = 1
```

Tạo:

```text
executed_portfolios.csv
trade_ledger.csv
failed_executions.csv
cash_weight.csv
```

`trade_ledger` tối thiểu:

```text
decision_date
execution_date
ticker
pre_trade_weight
target_weight
delta_weight
action
execution_status
failure_reason
executed_weight
cash_effect
```

## Bước 2 hoàn thành khi

Người thực hiện trả lời được:

> Sau khi mua/bán ở phiên kế tiếp, thực tế đang giữ mã nào và bao nhiêu cash?

---

# 13. BƯỚC 3 — GIỮ VÀ TÍNH LỜI/LỖ

Mục tiêu:

> Tính danh mục đã thực hiện ở Bước 2 lời/lỗ bao nhiêu trong kỳ nắm giữ.

---

# 13.1. NHIỆM VỤ 3.1 — XÁC ĐỊNH THỜI GIAN NẮM GIỮ

Với mỗi lần rebalance cần:

```text
holding_start
holding_end
```

`holding_start` gắn với execution hiện tại.

`holding_end` theo return/execution convention đã khóa trước kỳ tái cân bằng tiếp theo.

---

# 13.2. NHIỆM VỤ 3.2 — TÍNH LỢI SUẤT TỪNG CỔ PHIẾU

Dùng certified return series.

Ví dụ:

```text
FPT +8%
HPG -4%
VCB +6%
```

Không tự gán:

```text
missing return = 0
```

nếu contract không cho phép.

Đầu ra:

```text
security_period_returns.csv
```

---

# 13.3. NHIỆM VỤ 3.3 — TÍNH ĐÓNG GÓP LỢI SUẤT

Công thức:

```text
return_contribution_i
=
start_weight_i × security_return_i
```

Ví dụ:

```text
FPT:
25% × 8% = +2.0%

HPG:
25% × -4% = -1.0%
```

Cash:

```text
cash_return = 0
```

---

# 13.4. NHIỆM VỤ 3.4 — TÍNH LỢI SUẤT TOÀN DANH MỤC

```text
portfolio_return
=
Σ return_contribution
+
cash contribution
```

Ví dụ:

```text
+2.0%
-1.0%
+1.5%
+0
=
+2.5%
```

---

# 13.5. NHIỆM VỤ 3.5 — CẬP NHẬT NAV

Khởi tạo ví dụ:

```text
NAV = 100
```

Công thức:

```text
NAV_end
=
NAV_start × (1 + portfolio_return)
```

Ví dụ:

```text
100 × 1.025
=
102.5
```

---

# 13.6. NHIỆM VỤ 3.6 — TÍNH TRỌNG SỐ CUỐI KỲ

Do giá thay đổi, weight bị drift.

Ví dụ đầu kỳ:

```text
FPT 25
HPG 25
VCB 25
Cash 25
```

Sau return:

```text
FPT 27
HPG 24
VCB 26.5
Cash 25
```

Tổng:

```text
102.5
```

Trọng số mới:

```text
FPT  = 27 / 102.5
HPG  = 24 / 102.5
VCB  = 26.5 / 102.5
Cash = 25 / 102.5
```

Lưu dưới tên:

```text
pre_trade_weight
```

để dùng cho Bước 4.

## Đầu ra Bước 3

```text
holdings_timeline.csv
security_period_returns.csv
security_return_contributions.csv
portfolio_returns.csv
portfolio_nav.csv
pre_rebalance_weights.csv
```

## Bước 3 hoàn thành khi

Người thực hiện trả lời được:

> Kỳ này từng mã lời/lỗ bao nhiêu, danh mục lời/lỗ bao nhiêu, NAV mới là bao nhiêu và tỷ trọng cuối kỳ là gì?

---

# 14. BƯỚC 4 — THÁNG SAU TÁI CÂN BẰNG

Mục tiêu:

> Sang tháng mới, dùng dữ liệu mới có tại thời điểm đó để chọn lại danh mục, sau đó điều chỉnh danh mục cũ sang danh mục mới.

---

# 14.1. NHIỆM VỤ 4.1 — CHUYỂN SANG `decision_date` TIẾP THEO

Ví dụ:

```text
31/03/2024
↓
30/04/2024
```

Không tạo ngày giả trong gap A/B.

---

# 14.2. NHIỆM VỤ 4.2 — CHẠY LẠI BƯỚC 1

Dùng:
- Market state mới;
- Financial state mới nhất thỏa PIT;
- cùng eligibility rule;
- cùng 6 tiêu chí;
- cùng Combined ranking;
- cùng top 30%.

Không đổi rule chỉ vì kỳ trước lời/lỗ không đẹp.

Kết quả:

```text
Target Portfolio mới
```

---

# 14.3. NHIỆM VỤ 4.3 — NHẬN TARGET PORTFOLIO MỚI

Ví dụ:

Portfolio đang có:

```text
FPT
HPG
VCB
Cash
```

Target mới:

```text
FPT
MWG
VNM
SSI
```

---

# 14.4. NHIỆM VỤ 4.4 — SO TARGET MỚI VỚI `pre_trade_weight`

Dùng weight cuối Bước 3.

Không reset về equal-weight trước khi so.

Từ đây lại tính:

```text
delta_weight
BUY
SELL
HOLD
```

---

# 14.5. NHIỆM VỤ 4.5 — TÍNH TURNOVER

Tính turnover theo đúng formula đã khóa.

Nếu formula turnover chưa được quyết định:

```text
TURNOVER_METRIC = PENDING
```

Không tự chọn công thức.

---

# 14.6. NHIỆM VỤ 4.6 — QUAY LẠI BƯỚC 2

Sau khi có Target mới:

```text
Bước 2
→ giao dịch

Bước 3
→ tính lời/lỗ

Bước 4
→ tháng sau chọn lại
```

Lặp cho đến hết segment.

---

# 15. CHẠY 4 BƯỚC TRÊN ĐOẠN A VÀ ĐOẠN B

## Đoạn A

```text
30/11/2023 → 24/01/2025
```

Khởi tạo:

```text
NAV = 100 hoặc mốc đã khóa
cash = 100%
```

Sau đó:

```text
Bước 1
→ Bước 2
→ Bước 3
→ Bước 4
→ lặp
```

đến hết A.

Seal toàn bộ A trước khi đi tiếp.

---

## Gap

```text
25/01/2025 → 26/02/2026
```

Không:
- tạo selection;
- trade;
- holding;
- return;
- NAV;
- turnover.

---

## Đoạn B

```text
27/02/2026 → 28/08/2026
```

Khởi tạo độc lập:

```text
NAV = initial NAV
cash = 100%
```

Không mang:
- holdings A;
- NAV A;
- turnover A

sang B.

Dùng đúng cùng rule/engine.

---

# 16. CÁC STRATEGY ĐƯỢC CHẠY TRONG CÙNG 4 BƯỚC

## Combined — chiến lược chính

Bước 1 dùng:
- Market;
- Financial;
- 6 tiêu chí;
- Combined ranking.

## Market-only — đối chứng

Bước 1 chỉ dùng:
- Market eligibility;
- MC1..MC3;
- Market ranking.

## Financial-only — đối chứng

Bước 1 chỉ dùng:
- Financial PIT eligibility;
- FC1..FC3;
- Financial ranking.

Sau khi tạo Target Portfolio, cả ba dùng cùng Bước 2–4.

---

# 17. BENCHMARK — VNINDEX

## 17.1. Mục đích

Benchmark của M3 hiện chỉ sử dụng **VNINDEX**.

VNINDEX được dùng để trả lời câu hỏi:

> Sau khi chiến lược Combined đã hoàn thành backtest, hiệu quả của chiến lược khác diễn biến chung của thị trường Việt Nam như thế nào trong cùng giai đoạn?

Đối tượng được đem ra so sánh chính là:

```text
Combined Strategy
= Market clustering
+ Financial clustering
+ Candidate Universe
+ MC1..MC3
+ FC1..FC3
+ Combined Ranking
+ Top 30%
+ Target Portfolio
+ Backtest
```

so với:

```text
VNINDEX
```

VNINDEX **không tham gia** vào:

- tạo Candidate Universe;
- tính MC1..MC3 hoặc FC1..FC3;
- Combined Ranking;
- chọn top 30%;
- tạo Target Portfolio;
- thay đổi BUY / SELL / HOLD;
- thay đổi chiến lược sau khi đã xem kết quả.

Benchmark chỉ được dùng ở tầng **đánh giá kết quả backtest**.

---

## 17.2. Phân biệt benchmark với đối chứng

Trong kế hoạch M3 hiện tại:

```text
Combined
→ chiến lược nghiên cứu chính

Market-only
Financial-only
→ đối chứng nghiên cứu nếu được chạy

VNINDEX
→ benchmark / đối chuẩn chính thức
```

Hai đối chứng Market-only và Financial-only dùng để phân tích vai trò của từng nhánh thông tin.

VNINDEX dùng để so sánh chiến lược Combined với diễn biến chung của thị trường.

Không gọi Market-only hoặc Financial-only là benchmark.

---

## 17.3. Benchmark được chuẩn bị và so sánh khi nào?

Thông tin benchmark phải được xác định trước khi mở kết quả cuối để tránh thay đổi cách so sánh sau khi đã biết chiến lược lời/lỗ thế nào.

Tuy nhiên, việc **so sánh performance** chỉ thực hiện sau khi chiến lược đã chạy xong toàn bộ 4 bước của segment tương ứng.

Luồng:

```text
Khóa strategy và các rule backtest
        ↓
Khóa Đoạn A / Đoạn B
        ↓
Xác định nguồn và contract VNINDEX
        ↓
Chạy đầy đủ 4 bước backtest Combined
        ↓
Có chuỗi return / NAV của Combined
        ↓
Chuẩn bị chuỗi VNINDEX cùng giai đoạn
        ↓
Tính performance theo cùng khung thời gian
        ↓
So sánh Combined với VNINDEX
```

Không dùng kết quả VNINDEX để quay lại thay đổi:

- M2 clustering;
- Financial clustering;
- 6 tiêu chí;
- Candidate rule;
- Combined Ranking;
- top 30%;
- execution rule.

---

## 17.4. Dữ liệu VNINDEX bắt buộc

Tối thiểu phải xác định được:

```text
date
vnindex_value
source
source_version
return_basis
```

Nếu nguồn có manifest/hash thì phải lưu để truy nguyên.

Dữ liệu VNINDEX phải:

- bao phủ đúng segment đang đánh giá;
- có ngày giao dịch rõ ràng;
- có cơ sở tính lợi suất được chứng nhận;
- không sử dụng dữ liệu tương lai;
- không tự nội suy hoặc tạo giá trị VNINDEX không tồn tại;
- không tự đổi sang một chuỗi chỉ số khác khi thiếu dữ liệu.

Nếu `return_basis` của VNINDEX chưa được chứng nhận thì:

```text
VNINDEX_BENCHMARK_READY = FALSE
```

và chưa được chạy so sánh benchmark chính thức.

---

## 17.5. Căn thời gian với backtest Combined

VNINDEX phải được đánh giá trên đúng hai đoạn lịch sử của M3.

### Đoạn A

```text
30/11/2023 → 24/01/2025
```

So sánh:

```text
Combined — Đoạn A
vs
VNINDEX — Đoạn A
```

### Khoảng trống

```text
25/01/2025 → 26/02/2026
```

Khoảng này không được dùng để nối giả hai chuỗi.

Không được:

- nối NAV Combined qua gap;
- nối chuỗi benchmark qua gap để tạo một đường liên tục giả;
- tính performance A+B như một giai đoạn liên tục nếu methodology không quy định.

### Đoạn B

```text
27/02/2026 → 28/08/2026
```

So sánh:

```text
Combined — Đoạn B
vs
VNINDEX — Đoạn B
```

Đoạn A và Đoạn B phải được tính và báo cáo độc lập.

---

## 17.6. Cách tạo chuỗi lợi suất VNINDEX

Từ chuỗi VNINDEX đã được chứng nhận, tạo lợi suất benchmark theo `return_basis` đã khóa.

Không tự chọn công thức hoặc loại chuỗi khác nếu contract chưa xác nhận.

Nếu cần hiển thị đường tăng trưởng chuẩn hóa để so sánh trực quan với Combined, phải dùng cùng một quy ước chuẩn hóa đã được ghi rõ cho từng segment; không mang giá trị cuối Đoạn A sang làm điểm đầu Đoạn B.

Đầu ra tối thiểu nên cho biết:

```text
segment
date
vnindex_value
vnindex_return
benchmark_status
source_version
```

---

## 17.7. Các chỉ số dùng để so sánh

Sau khi backtest Combined của segment đã hoàn tất, so sánh với VNINDEX bằng cùng bộ performance metrics đã được M3 phê duyệt và có ý nghĩa cho cả hai chuỗi.

Tối thiểu có thể gồm:

```text
Cumulative Return
CAGR nếu hợp lệ
Annualized Volatility
Maximum Drawdown
Calmar nếu hợp lệ
Positive-period Ratio
```

Các chỉ số sau chỉ dùng khi alignment và contract đủ điều kiện:

```text
Beta
Tracking Error
Information Ratio
```

Không dùng Sharpe theo rule hiện tại.

Các chỉ số mang tính vận hành danh mục như:

```text
Turnover
Cash Ratio
Failed Execution Rate
```

vẫn được báo cáo cho Combined khi cần, nhưng không ép VNINDEX phải có các chỉ số không có ý nghĩa tương đương.

---

## 17.8. Giả định thực thi hiện tại

Theo kế hoạch hiện tại của M3-A:

```text
chỉ mua, không bán khống
không dùng đòn bẩy
cash return = 0
chi phí giao dịch chính = 0
trượt giá chính = 0
```

Các giả định này thuộc backtest của chiến lược Combined.

VNINDEX là chuỗi chỉ số tham chiếu, không được giả lập thành một danh mục cổ phiếu nếu methodology không yêu cầu.

Không tự thêm phí giao dịch riêng cho VNINDEX hoặc tự thay đổi giả định chi phí của Combined trong bước benchmark.

---

## 17.9. Kết quả so sánh theo từng segment

### Đoạn A

Tạo tối thiểu:

```text
Combined performance — A
VNINDEX performance — A
Comparison — A
```

### Đoạn B

Tạo tối thiểu:

```text
Combined performance — B
VNINDEX performance — B
Comparison — B
```

Không gộp A và B thành một chuỗi performance duy nhất qua gap.

---

## 17.10. Cách trình bày kết quả

Bảng so sánh chính nên tập trung vào:

```text
Combined vs VNINDEX
```

Ví dụ cấu trúc:

| Chỉ số | Combined | VNINDEX |
|---|---:|---:|
| Cumulative Return | ... | ... |
| CAGR | ... | ... |
| Annualized Volatility | ... | ... |
| Maximum Drawdown | ... | ... |
| Calmar | ... | ... |
| Positive-period Ratio | ... | ... |

Nếu một metric không hợp lệ cho giai đoạn đang xét thì ghi rõ `N/A` hoặc trạng thái tương đương; không tự tính bằng một công thức khác.

Ngoài bảng performance, có thể trình bày biểu đồ tăng trưởng/NAV chuẩn hóa và drawdown nếu các contract tương ứng đã được khóa.

---

## 17.11. Cách diễn giải

Không chỉ nhìn vào lợi suất.

Ví dụ:

```text
Combined Return = 15%
VNINDEX Return  = 13%
```

không đủ để kết luận toàn bộ chiến lược tốt hơn.

Phải xem cùng các yếu tố như:

- volatility;
- maximum drawdown;
- Calmar nếu hợp lệ;
- mức ổn định giữa Đoạn A và Đoạn B;
- các giới hạn dữ liệu và execution của Combined.

Nếu Combined kém VNINDEX ở một segment thì vẫn phải báo cáo đầy đủ.

Không được thay strategy hoặc cách tính benchmark để làm kết quả đẹp hơn.

---

## 17.12. Đánh giá cuối sau 28/08/2026

Khi M3 mở giai đoạn đánh giá cuối bằng dữ liệu mới sau `28/08/2026`, phải tạo VNINDEX benchmark cho đúng cùng khoảng thời gian đánh giá cuối.

Luồng:

```text
Strategy đã khóa
        ↓
Chạy đánh giá cuối Combined
        ↓
Khóa kết quả
        ↓
Lấy VNINDEX cùng giai đoạn
        ↓
Tính cùng bộ metric hợp lệ
        ↓
So sánh Combined cuối với VNINDEX cuối
```

Không được thay strategy sau khi xem kết quả cuối hoặc kết quả VNINDEX.

---

## 17.13. Đầu ra benchmark đề xuất

Tối thiểu:

```text
vnindex_benchmark_returns.csv
vnindex_benchmark_metrics.csv
benchmark_comparison.csv
```

Trong đó phải truy được tối thiểu:

```text
segment
date
benchmark_id = VNINDEX
return
metric
source
source_version
return_basis
```

Không cần tạo `benchmark_target_portfolios.csv` cho VNINDEX nếu VNINDEX chỉ được sử dụng dưới dạng chuỗi chỉ số tham chiếu.

---

## 17.14. Điều kiện hoàn thành benchmark

Benchmark VNINDEX chỉ được coi là hoàn thành khi:

- nguồn VNINDEX đã được xác định rõ;
- version / provenance đủ để truy nguyên;
- `return_basis` được chứng nhận;
- chuỗi được căn đúng Đoạn A và Đoạn B;
- không nối giả qua gap;
- không dùng dữ liệu tương lai;
- cùng bộ metric hợp lệ được áp dụng nhất quán cho Combined và VNINDEX;
- kết quả A và B được báo cáo riêng;
- VNINDEX của giai đoạn đánh giá cuối được căn đúng khi giai đoạn đó được mở;
- mọi con số trong bảng so sánh truy ngược được về output có phiên bản;
- kết quả thuận lợi và bất lợi đều được báo cáo.

---

# 18. SAU KHI CHẠY XONG 4 BƯỚC MỚI TÍNH PERFORMANCE

Đầu vào:

```text
portfolio_returns
portfolio_nav
trade_ledger
turnover
cash_weight
failed_executions
```

Tính:

```text
Cumulative Return
CAGR nếu hợp lệ
Annualized Volatility
Maximum Drawdown
Calmar
Turnover
Cash Ratio
Positive-period Ratio
Failed Execution Rate
```

Beta/Tracking Error/Information Ratio chỉ tính khi alignment đủ chuẩn.

Không tính Sharpe.

---

# 19. VÍ DỤ MỘT VÒNG HOÀN CHỈNH

## Bước 1 — Chọn cổ phiếu

```text
FPT 25%
HPG 25%
MWG 25%
VCB 25%
```

## Bước 2 — Giả lập mua/bán

MWG không mua được:

```text
FPT 25%
HPG 25%
VCB 25%
Cash 25%
```

## Bước 3 — Giữ và tính lời/lỗ

```text
FPT +8%
HPG -4%
VCB +6%
Cash 0
```

Contribution:

```text
+2.0%
-1.0%
+1.5%
0
```

Portfolio:

```text
+2.5%
```

NAV:

```text
100 → 102.5
```

## Bước 4 — Tháng sau tái cân bằng

Target mới:

```text
FPT
MWG
VNM
SSI
```

So với weight cuối kỳ:
- FPT điều chỉnh;
- HPG SELL;
- VCB SELL;
- MWG BUY;
- VNM BUY;
- SSI BUY.

Quay lại Bước 2.

---

# 20. CHECKLIST TOÀN BỘ M3-A THEO 4 BƯỚC

## Bước 1 — Chọn cổ phiếu

```text
[ ] M2 Market handoff validated
[ ] Financial handoff validated
[ ] PIT alignment complete
[ ] eligibility rule frozen
[ ] Candidate Universe created
[ ] MC1 MC2 MC3 calculated
[ ] FC1 FC2 FC3 calculated
[ ] Combined rank created
[ ] top 30% selected
[ ] Target Portfolio created
```

## Bước 2 — Giả lập mua/bán

```text
[ ] execution_date found
[ ] current portfolio known
[ ] delta weights calculated
[ ] BUY/SELL/HOLD created
[ ] tradability checked
[ ] failed execution handled
[ ] Executed Portfolio created
[ ] Trade Ledger created
```

## Bước 3 — Giữ và tính lời/lỗ

```text
[ ] holding period defined
[ ] security returns calculated
[ ] return contributions calculated
[ ] portfolio return calculated
[ ] NAV updated
[ ] end weights calculated
```

## Bước 4 — Tái cân bằng

```text
[ ] next decision_date reached
[ ] Step 1 rerun with same frozen rules
[ ] new Target Portfolio created
[ ] compared with pre_trade_weight
[ ] turnover calculated
[ ] returned to Step 2
```

---

# 21. KHI NÀO BACKTEST ĐƯỢC COI LÀ HOÀN TẤT?

Chỉ khi cả A và B đã hoàn thành toàn bộ vòng:

```text
1. CHỌN CỔ PHIẾU
        ↓
2. GIẢ LẬP MUA/BÁN
        ↓
3. GIỮ VÀ TÍNH LỜI/LỖ
        ↓
4. THÁNG SAU TÁI CÂN BẰNG
        ↓
lặp đến cuối segment
```

và có đầy đủ:
- target portfolios;
- trade ledger;
- executed holdings;
- security returns;
- contribution;
- portfolio returns;
- NAV;
- cash;
- turnover;
- failed executions;
- benchmark results;
- performance metrics.

---

# PHẦN B — M3-B — STREAMLIT DASHBOARD PHÂN CỤM MARKET VÀ FINANCIAL

## 1. MỤC TIÊU

M3-B xây dựng dashboard trực quan hóa hai hệ clustering độc lập:

```text
MARKET CLUSTERING
+
FINANCIAL CLUSTERING
```

Implementation chính:

```text
Python
+
Streamlit
```

M3-B là:

```text
READ-ONLY VISUALIZATION / PRODUCT LAYER
```

Dashboard tiêu thụ kết quả đã được upstream tạo và xác minh.

Dashboard phải cho phép người dùng:

1. Chọn `decision_date`.
2. Xem Market clustering tương ứng.
3. Xem Financial clustering hợp lệ tại cùng `decision_date`.
4. Xem sự phân hóa các Market cluster.
5. Xem Market cluster profile.
6. Xem Financial cluster profile.
7. Xem danh sách ticker thuộc từng cluster.
8. Tìm kiếm ticker.
9. Xem 8 Market features của ticker.
10. Xem Financial features của ticker.
11. Xem Financial timing metadata:
    - `period_end`;
    - `available_at`;
    - revision/vintage/status nếu upstream có.
12. Theo dõi snapshot mới khi upstream publish artifact mới hợp lệ.
13. Giữ provenance từ dashboard về đúng artifact upstream.

---

# 2. MARKET VÀ FINANCIAL LÀ HAI HỆ ĐỘC LẬP

Market clustering và Financial clustering không được hợp nhất thành một cluster mới.

Không làm:

```text
Market cluster
+
Financial cluster
↓
New combined cluster
```

Mà hiển thị song song:

```text
                  decision_date
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
 MARKET CLUSTERING          FINANCIAL CLUSTERING
          │                         │
 Market features            Financial features
          │                         │
          └────────────┬────────────┘
                       ▼
                    Dashboard
```

Hai kết quả có thể được đặt cạnh nhau để người dùng so sánh nhưng semantic phải giữ riêng biệt.

---

# 3. SCIENTIFIC BOUNDARY

Dashboard KHÔNG được:

- chạy lại K-Means;
- fit clustering model;
- predict cluster mới nếu upstream chưa tạo;
- thay đổi `global_k`;
- chọn lại model;
- thay đổi Market methodology;
- thay đổi Financial methodology;
- tính lại Market features;
- tính lại Financial features;
- thay đổi PIT/revision rules;
- tính MC1 / MC2 / MC3;
- tính FC1 / FC2 / FC3;
- tính Combined Rank;
- chọn portfolio;
- backtest;
- đưa ra BUY/SELL recommendation;
- zero-fill missing data;
- tự tạo owner decision;
- tự resolve blocked Financial state;
- sửa verified upstream artifact.

Luồng đúng:

```text
Verified upstream outputs
        ↓
Data loading
        ↓
Validation
        ↓
Time alignment
        ↓
Query layer
        ↓
Visualization
```

---

# 4. MARKET OFFICIAL INPUTS

## 4.1. Ticker cluster assignment

Nguồn:

```text
M2/artifacts/m2-final-handoff-v1/
m2_cluster_labels_for_m3.csv
```

Vai trò:

```text
ticker/security_id
+
snapshot_date
↓
cluster_label
```

Known fields:

```text
snapshot_date
security_id
ticker
cluster_label
membership_period
```

Đây là nguồn authoritative cho Market cluster membership.

---

# 4.2. Market Cluster Profile

Nguồn:

```text
M2/artifacts/m2-final-handoff-v1/
m2_cluster_profiles_for_m3.csv
```

Fields:

```text
snapshot_date
cluster_label
size
size_ratio

mom_21
mom_63
mom_126
mom_252
vol_63
mdd_126
beta_126
liquidity_21

membership_period
```

8 feature trong file này là:

```text
CLUSTER-LEVEL PROFILE
```

không phải feature của từng ticker.

---

# 4.3. Market ticker-level features

Nguồn:

```text
artifacts/cafef_primary/
cafef-c8-complete-only-v2/
canonical/
feature_snapshots.jsonl
```

8 Market features:

```text
mom_21
mom_63
mom_126
mom_252
vol_63
mdd_126
beta_126
liquidity_21
```

Đây là nguồn ticker-level dùng cho:

- scatter coordinates;
- ticker feature table;
- tooltip;
- ticker detail;
- source verification.

Không được lấy cluster-profile value làm ticker value.

---

# 4.4. M2 handoff manifest

Nguồn:

```text
M2/artifacts/m2-final-handoff-v1/
m2_to_m3_handoff_manifest.json
```

Vai trò:

- official M2 → M3 handoff;
- snapshot universe;
- methodology;
- provenance;
- selected algorithm;
- `global_k`;
- development/holdout structure;
- artifact verification.

Current handoff:

```text
selected_algorithm = KMeans_Baseline
global_k = 2
total_snapshots = 22
```

gồm:

```text
15 development snapshots
+
7 holdout snapshots
```

M3-B phải giữ đúng contract này.

---

# 4.5. Selected model

Nguồn:

```text
M2/models/final_selected_model/
```

Vai trò trong dashboard:

```text
REFERENCE
PROVENANCE
AUDIT
```

M3-B không gọi selected model để chạy clustering.

---

# 4.6. Transition reference

Nguồn:

```text
M2/artifacts/m2-final-handoff-v1/
m2_transition_turnover_reference.csv
```

Không phải dependency bắt buộc cho core dashboard.

Có thể dùng sau cho:

- cluster history;
- migration;
- persistence;
- ARI/NMI;
- entered/exited ticker analysis.

---

# 5. FINANCIAL OFFICIAL INPUTS

Financial clustering phải được đọc từ verified Financial clustering artifacts.

Exact paths và schema sẽ được khóa dựa trên output thực tế.

Tối thiểu Financial contract cần cung cấp:

```text
ticker hoặc security_id

financial_cluster

financial_snapshot_id

period_end

available_at

Financial clustering features
```

Nếu upstream cung cấp thêm:

```text
revision
vintage
stale status
missing status
PIT status
blocked status
provenance
```

M3-B phải giữ nguyên.

Dashboard không được tự tái tạo Financial cluster.

---

# 6. MARKET FEATURE CONTRACT

M2 sử dụng đúng:

```text
mom_21
mom_63
mom_126
mom_252
vol_63
mdd_126
beta_126
liquidity_21
```

Có thể nhóm về mặt diễn giải:

```text
Momentum
├── mom_21
├── mom_63
├── mom_126
└── mom_252

Risk
├── vol_63
├── mdd_126
└── beta_126

Liquidity
└── liquidity_21
```

Nhưng clustering vẫn sử dụng exact feature contract M2.

---

# 7. DECISION DATE

## 7.1. Vai trò

`decision_date` là ngày người dùng muốn xem trạng thái Market và Financial.

Một lựa chọn:

```text
decision_date = t
```

sẽ dẫn tới hai phép tra cứu khác nhau:

```text
Market
→ Market snapshot tại t

Financial
→ Financial state hợp lệ theo PIT tại t
```

---

# 7.2. Market decision date

Market sử dụng official M2 snapshot dates.

Ví dụ:

```text
decision_date = 2025-01-24
```

Dashboard đọc Market:

```text
snapshot_date = 2025-01-24
```

từ:

```text
m2_cluster_labels_for_m3.csv

m2_cluster_profiles_for_m3.csv

ticker feature artifact tương ứng
```

Không tự chọn:

- nearest date;
- previous date;
- next date.

Không tạo snapshot giả.

---

# 7.3. Decision-date selector

Danh sách ngày phải được derive từ official Market handoff/artifacts.

Không hard-code danh sách ngày trong UI.

Concept:

```text
Official M2 snapshot universe
        ↓
list_decision_dates()
        ↓
Streamlit selector
```

---

# 7.4. Systemic gap

Nếu M2 có systemic gap:

```text
development
↓
GAP
↓
holdout
```

M3-B không:

- interpolate;
- forward-fill;
- backward-fill;
- tạo cluster state giả.

Chỉ official M2 snapshots được hiển thị.

---

# 8. FINANCIAL TIME SEMANTICS

Financial có ít nhất ba trường thời gian quan trọng:

```text
period_end
available_at
decision_date
```

---

## 8.1. `period_end`

Trả lời:

> Dữ liệu tài chính phản ánh kỳ kết thúc khi nào?

Ví dụ:

```text
period_end = 2023-12-31
```

---

## 8.2. `available_at`

Trả lời:

> Từ khi nào thông tin này thực sự có thể được biết?

Ví dụ:

```text
available_at = 2024-03-25
```

---

## 8.3. `decision_date`

Trả lời:

> Tại thời điểm nào dashboard đang đánh giá cổ phiếu?

Ví dụ:

```text
decision_date = 2024-06-30
```

---

# 9. FINANCIAL PIT RULE

Hard rule:

```text
available_at <= decision_date
```

Nếu:

```text
available_at > decision_date
```

Financial state đó không được sử dụng.

Ví dụ:

```text
period_end    = 2023-12-31
available_at  = 2024-03-25
decision_date = 2024-02-29
```

→ không hợp lệ.

Nếu:

```text
decision_date = 2024-06-30
```

→ có thể hợp lệ.

---

# 10. MULTIPLE FINANCIAL STATES

Nếu nhiều Financial states cùng thỏa:

```text
available_at <= decision_date
```

M3-B phải áp dụng đúng Financial upstream contract.

Không tự quyết định:

- quarterly tốt hơn annual;
- revision nào ưu tiên;
- vintage nào được chọn;
- có backfill hay không.

Nếu upstream chưa resolve được:

```text
MANUAL_REVIEW
/
BLOCKED
```

Dashboard giữ đúng trạng thái đó.

---

# 11. FINANCIAL REVISION

Revised data không được back-propagate.

Ví dụ:

```text
FY2023 original
available_at = 2024-03-25

FY2023 revised
available_at = 2024-05-10
```

Tại:

```text
decision_date = 2024-04-30
```

chỉ original có thể được dùng.

---

# 12. DATA COVERAGE VS SCOPE

Nếu artifact ticker feature tại một thời điểm chưa cập nhật đầy đủ trong khi official clustering output đã tồn tại:

```text
cluster labels      ✅
cluster profiles    ✅
ticker features     ❌
```

đó là:

```text
SOURCE DATA NOT YET UPDATED
```

Không được tự biến thành thay đổi scope.

Không được:

- giảm official snapshot universe;
- bỏ holdout;
- đổi methodology;
- lấy feature cũ hơn thay thế;
- tự tính feature trong dashboard.

Dashboard phải báo trạng thái rõ ràng, ví dụ:

```text
MARKET_FEATURES_NOT_FOUND
```

---

# 13. DASHBOARD ARCHITECTURE

```text
Market verified outputs
+
Financial verified outputs
        ↓
Data Loading
        ↓
Validation
        ↓
Time Alignment
        ↓
Query Layer
        ↓
Visualization Layer
        ↓
Streamlit
```

Implementation ban đầu có thể nằm trong:

```text
m3_dashboard.py
```

Không bắt buộc:

```text
builder.py
repository.py
server.py
index.html
app.js
styles.css
REST API
```

---

# 14. CODE STRUCTURE

Dù một file, phải tổ chức rõ:

```text
1. CONFIG / CONSTANTS
2. DATA LOADING
3. VALIDATION
4. TIME ALIGNMENT
5. QUERY LAYER
6. VISUALIZATION
7. STREAMLIT UI
8. MAIN
```

Ví dụ:

```python
load_market_labels()
load_market_profiles()
load_market_features()
load_m2_manifest()

load_financial_data()

validate_market_contract()
validate_financial_contract()

list_decision_dates()
list_tickers()

select_market_snapshot()
select_financial_state()

get_market_overview()
get_financial_overview()

get_market_ticker()
get_financial_ticker()

render_market()
render_financial()

main()
```

---

# 15. FULL DASHBOARD LAYOUT

Desktop:

```text
┌──────────────────────────────────────────────────────────────┐
│                   M3-B CLUSTERING DASHBOARD                  │
├──────────────────────────────────────────────────────────────┤
│ Decision date: [ ... ▼ ]           Ticker: [ Search... ]    │
├──────────────────────────────┬───────────────────────────────┤
│            MARKET            │           FINANCIAL           │
│                              │                               │
│ Cluster visualization        │ Cluster visualization         │
│ Cluster profile              │ Cluster profile               │
│ Members                      │ Members                       │
│ Market features              │ Financial features            │
│                              │ period_end                    │
│                              │ available_at                  │
└──────────────────────────────┴───────────────────────────────┘
```

Màn hình hẹp:

```text
MARKET
↓
FINANCIAL
```

---

# 16. MARKET SCATTER PLOT

Market phải có scatter plot giúp trực quan hóa sự phân hóa giữa:

```text
Cluster 0
Cluster 1
```

Current M2:

```text
global_k = 2
```

Do đó:

- mỗi điểm = một ticker;
- màu = `cluster_label`;
- không tạo Cluster 2;
- không chạy clustering từ scatter.

---

# 17. MARKET X/Y SELECTION

Trước khi khóa scatter visualization phải thực hiện một audit riêng.

Nguồn chính:

```text
m2_cluster_profiles_for_m3.csv
```

Mục tiêu:

> Xác định hai Market features đại diện phù hợp nhất để trực quan hóa sự phân hóa Cluster 0 và Cluster 1.

Audit phải:

1. So sánh profile Cluster 0 và Cluster 1 trên toàn bộ 8 Market features.
2. Xem sự khác biệt đó qua các snapshot.
3. Xác định feature nào giúp giải thích cluster differentiation tốt.
4. Đề xuất:

```text
RECOMMENDED_X = ...
RECOMMENDED_Y = ...
```

5. Hai feature phải:
   - có ý nghĩa kinh tế rõ;
   - trực quan;
   - giúp quan sát sự phân hóa cluster;
   - ổn định đủ để dùng làm trục dashboard.

6. Chọn **một cặp X/Y cố định** cho toàn dashboard.

7. Không thay X/Y theo từng snapshot.

8. Không tạo feature mới.

9. Không chạy lại M2.

10. Không thay đổi cluster assignment.

---

# 18. NGUỒN DỮ LIỆU MARKET SCATTER

Cluster/màu:

```text
m2_cluster_labels_for_m3.csv
```

Tọa độ từng ticker:

```text
feature_snapshots.jsonl
```

Không dùng:

```text
m2_cluster_profiles_for_m3.csv
```

làm tọa độ ticker.

Profile chỉ dùng để:

- mô tả cluster;
- hỗ trợ lựa chọn/trình bày trục X/Y;
- bảng cluster profile.

---

# 19. SCATTER KHÔNG QUYẾT ĐỊNH CLUSTER

Dashboard phải làm rõ:

```text
M2
+
8 Market features
↓
cluster_label
```

Còn:

```text
2 representative features
↓
scatter visualization
```

Do đó X/Y chỉ giải thích cluster đã tồn tại.

---

# 20. MARKET SCATTER TOOLTIP

Hover nên hiển thị:

```text
ticker
cluster_label
X feature
X value
Y feature
Y value
```

Có thể thêm:

```text
security_id
```

nếu hữu ích.

---

# 21. MARKET CLUSTER PROFILE

Nguồn:

```text
m2_cluster_profiles_for_m3.csv
```

Hiển thị:

```text
cluster_label
size
size_ratio

mom_21
mom_63
mom_126
mom_252
vol_63
mdd_126
beta_126
liquidity_21
```

---

# 22. MARKET CLUSTER INTERPRETATION

Canonical labels:

```text
Cluster 0
Cluster 1
```

Không tự đổi thành:

```text
Dẫn dắt
Đại trà
```

nếu chưa được profile/evidence hỗ trợ.

Nếu sau analysis có đủ bằng chứng để diễn giải:

```text
Cluster 0 — ...
Cluster 1 — ...
```

thì có thể dùng UI alias.

Canonical `cluster_label` vẫn giữ nguyên.

---

# 23. MARKET MEMBER LIST

Có filter/tab:

```text
[ Cluster 0 ] [ Cluster 1 ]
```

Bảng có thể gồm:

```text
ticker
company name nếu source có
cluster

mom_21
mom_63
mom_126
mom_252
vol_63
mdd_126
beta_126
liquidity_21
```

Có:

```text
search
pagination / bounded rendering
```

---

# 24. FINANCIAL CLUSTER VISUALIZATION

Financial phải có khu vực trực quan hóa clustering tương ứng.

Hình thức cụ thể phụ thuộc Financial clustering output.

Có thể gồm:

```text
Financial cluster distribution

Financial cluster profile

Financial member table

Financial ticker detail
```

Nếu exact Financial features hỗ trợ một scatter plot có ý nghĩa và upstream contract cho phép, có thể dùng scatter.

Không bắt buộc ép Financial clustering vào cùng kiểu biểu đồ Market nếu semantic không phù hợp.

---

# 25. FINANCIAL CLUSTER PROFILE

Hiển thị:

```text
financial_cluster
size
size_ratio
Financial feature profile
```

Exact feature columns phải lấy từ Financial clustering contract thực tế.

Không tự chọn feature ngoài contract.

---

# 26. FINANCIAL MEMBER LIST

Cho phép xem các ticker thuộc từng Financial cluster.

Bảng tối thiểu:

```text
ticker
financial_cluster
period_end
available_at
Financial features
status
```

Nếu có revision/vintage:

```text
revision
vintage
```

có thể hiển thị khi cần.

---

# 27. TICKER SEARCH / DETAIL

Có selector/search:

```text
Ticker: [ FPT ]
```

Khi chọn ticker + decision_date, dashboard trả về hai vùng.

## Market

```text
ticker
Market cluster
Market snapshot
8 Market features
```

## Financial

```text
ticker
Financial cluster
Financial snapshot
period_end
available_at
Financial features
PIT/status metadata
```

Không merge hai cluster.

---

# 28. MISSING / BLOCKED STATES

Market:

```text
SNAPSHOT_NOT_FOUND
TICKER_NOT_FOUND
MARKET_CLUSTER_NOT_FOUND
MARKET_FEATURES_NOT_FOUND
CLUSTER_PROFILE_NOT_FOUND
DATA_CONTRACT_BLOCKED
```

Financial:

```text
FINANCIAL_CLUSTER_NOT_FOUND
FINANCIAL_FEATURES_NOT_FOUND
NO_VALID_FINANCIAL_STATE
NOT_PIT_ELIGIBLE
BLOCKED
STALE
MANUAL_REVIEW
```

Không zero-fill.

Không substitute snapshot khác.

---

# 29. PROVENANCE

## Market cluster

```text
ticker
↓
decision_date
↓
m2_cluster_labels_for_m3.csv
```

## Market cluster profile

```text
cluster
↓
decision_date
↓
m2_cluster_profiles_for_m3.csv
```

## Market ticker features

```text
ticker
↓
decision_date
↓
feature_snapshots.jsonl
```

## Market authority

```text
m2_to_m3_handoff_manifest.json
```

## Financial

```text
Financial UI value
↓
Financial snapshot
↓
verified Financial artifact
↓
Financial provenance/manifest
```

---

# 30. DATA-DRIVEN DESIGN

Dashboard không được hard-code:

- số snapshot;
- specific snapshot dates;
- ticker universe;
- cluster membership.

Các danh sách phải derive từ artifacts.

Ví dụ:

```text
official artifact
↓
discover available snapshots
↓
decision-date selector
```

Khi upstream có artifact mới hợp lệ:

```text
new snapshot
↓
artifact updated/published
↓
dashboard reload
↓
new snapshot becomes available
```

không cần sửa business logic của dashboard.

---

# 31. CACHING

Có thể dùng:

```python
@st.cache_data
```

nhưng khi artifact thay đổi, dashboard phải có thể phát hiện/reload dữ liệu mới.

Có thể dựa vào:

- file modification;
- version;
- manifest;
- reload control.

Không để stale cache che dữ liệu mới.

---

# 32. FUTURE AUTOMATION ARCHITECTURE

Automation không phải scientific logic của dashboard.

Market target:

```text
NEW MARKET DATA
        ↓
DETECT NEW SNAPSHOT
        ↓
BUILD 8 MARKET FEATURES
        ↓
VALIDATE
        ↓
RUN APPROVED M2
        ↓
VALIDATE
        ↓
PUBLISH VERIFIED ARTIFACT
        ↓
DASHBOARD DISCOVERS SNAPSHOT
```

Financial target:

```text
NEW FINANCIAL INFORMATION
        ↓
PIT / REVISION PROCESS
        ↓
FINANCIAL FEATURES
        ↓
APPROVED FINANCIAL CLUSTERING
        ↓
VALIDATE
        ↓
PUBLISH VERIFIED ARTIFACT
        ↓
DASHBOARD
```

---

# 33. AUTOMATION KHÔNG NẰM TRONG `m3_dashboard.py`

Không:

```text
Dashboard
↓
run M2
```

Mà:

```text
Upstream pipeline
↓
verified artifact
↓
Dashboard
```

Dashboard vẫn read-only.

---

# 34. PUBLISH GATES

Không publish partial result.

Concept:

```text
INPUT
↓
VALIDATE
↓ PASS

PROCESS
↓
VALIDATE
↓ PASS

PUBLISH
```

Nếu fail:

```text
STOP
NO PUBLISH
```

Dashboard chỉ tiêu thụ verified artifacts.

---

# 35. OPTIONAL PRODUCTIZATION

Không phải completion requirement của M3-B.

Nếu sau này cần:

```text
builder.py
repository.py
server.py
index.html
app.js
styles.css
REST API
```

có thể tách từ architecture hiện tại.

Nhưng không thay đổi:

- Market methodology;
- Financial methodology;
- PIT;
- feature definitions;
- cluster outputs.

---

# 36. KẾ HOẠCH THỰC HIỆN

M3-B gồm các work unit sau.

---

## TASK 01 — LOCK MARKET DATA CONTRACT

Inspect:

```text
m2_cluster_labels_for_m3.csv
m2_cluster_profiles_for_m3.csv
feature_snapshots.jsonl
m2_to_m3_handoff_manifest.json
```

Khóa:

- exact schema;
- snapshot date field;
- ticker/security_id;
- cluster label;
- join key;
- uniqueness;
- 8 features;
- official snapshot universe.

Gate:

```text
MARKET_DATA_CONTRACT_PASS
```

---

## TASK 02 — LOCK FINANCIAL DATA CONTRACT

Inspect verified Financial clustering outputs.

Khóa:

```text
ticker/security_id
financial_cluster
financial_snapshot
period_end
available_at
Financial features
revision/vintage
status
```

Gate:

```text
FINANCIAL_DATA_CONTRACT_PASS
```

---

## TASK 03 — MARKET X/Y AUDIT

Dùng:

```text
m2_cluster_profiles_for_m3.csv
```

để xác định:

```text
RECOMMENDED_X
RECOMMENDED_Y
```

Yêu cầu:

- fixed across snapshots;
- có ý nghĩa kinh tế;
- giải thích cluster tốt;
- không tạo feature;
- không thay đổi M2.

Gate:

```text
MARKET_X_Y_CONTRACT_PASS
```

---

## TASK 04 — DATA LOADING

Implement:

```python
load_market_labels()
load_market_profiles()
load_market_features()
load_m2_manifest()

load_financial_data()
```

---

## TASK 05 — VALIDATION

Market:

```text
required columns
8 features
duplicates
join cardinality
snapshot integrity
```

Financial:

```text
required fields
time fields
features
cluster integrity
revision/vintage/status
```

Không silent-fix.

---

## TASK 06 — TIME ALIGNMENT

Market:

```text
decision_date
→ exact official M2 snapshot
```

Financial:

```text
decision_date
→ PIT-safe Financial state
```

Hard Financial rule:

```text
available_at <= decision_date
```

---

## TASK 07 — QUERY LAYER

Implement functions như:

```python
list_decision_dates()
list_tickers()

get_market_overview()
get_market_cluster_profiles()
get_market_cluster_members()
get_market_ticker()

get_financial_overview()
get_financial_cluster_profiles()
get_financial_cluster_members()
get_financial_ticker()

get_company()
```

UI không trực tiếp thực hiện business joins.

---

## TASK 08 — STREAMLIT FRAMEWORK

Tạo:

```text
m3_dashboard.py
```

Main UI:

```text
decision_date selector
ticker search

Market area
Financial area

missing/error states
```

---

## TASK 09 — MARKET VISUALIZATION

Implement:

```text
Market scatter
Cluster Profile
Cluster Member List
Ticker Detail
```

Scatter:

```text
point = ticker
color = cluster_label
X/Y = fixed representative Market features
```

---

## TASK 10 — FINANCIAL VISUALIZATION

Implement:

```text
Financial cluster view
Financial cluster profile
Financial members
Financial ticker detail
period_end
available_at
status
```

Visualization phải theo exact Financial contract.

---

## TASK 11 — RESPONSIVE LAYOUT

Desktop:

```text
MARKET | FINANCIAL
```

Narrow:

```text
MARKET
↓
FINANCIAL
```

Không làm mất semantic dữ liệu.

---

## TASK 12 — TESTING + END-TO-END VERIFICATION

### Market

Test:

- development snapshot;
- holdout snapshot;
- systemic gap;
- labels;
- profiles;
- ticker features;
- scatter coordinates;
- missing ticker feature.

### Financial

Test:

```text
available_at < decision_date
available_at = decision_date
available_at > decision_date
multiple eligible states
revision
no valid state
blocked state
```

### Cross-system

Chọn:

```text
ticker
+
decision_date
```

và xác minh đồng thời:

```text
Market output
+
Financial PIT-safe output
```

### Streamlit

Smoke test server.

### Source consistency

UI value phải bằng exact upstream source value.

---

# 37. MANUAL RUN INSTRUCTIONS

Sau implementation phải cung cấp exact Windows commands.

Ví dụ:

```powershell
cd "C:\Users\HP\Downloads\Phân cụm động lượng TTCK"
```

Kiểm tra Streamlit:

```powershell
python -m streamlit --version
```

Run:

```powershell
python -m streamlit run <EXACT_PATH_TO_M3_DASHBOARD>
```

Expected:

```text
http://localhost:8501
```

Stop:

```text
Ctrl + C
```

---

# 38. MANUAL TEST CHECKLIST

Người dùng phải được hướng dẫn kiểm tra:

1. Chọn `decision_date`.
2. Market scatter cập nhật.
3. Market cluster profile cập nhật.
4. Market members cập nhật.
5. Search một ticker.
6. Kiểm tra 8 Market features.
7. Kiểm tra Financial cluster.
8. Kiểm tra Financial features.
9. Kiểm tra `period_end`.
10. Kiểm tra `available_at`.
11. Thử date chưa có Financial PIT-safe state.
12. Thử missing data.
13. Đối chiếu ít nhất một ticker/date với raw source artifacts.

---

# 39. DEFINITION OF DONE

M3-B chỉ COMPLETE khi:

1. Streamlit dashboard chạy được.
2. Market và Financial đều được tích hợp.
3. `decision_date` hoạt động đúng.
4. Market dùng official M2 snapshots.
5. Financial tuân thủ PIT.
6. Market cluster đúng official labels.
7. Market profile đúng artifact.
8. Market ticker features đúng source.
9. Market X/Y được audit và khóa.
10. Market scatter hoạt động.
11. Financial cluster đúng verified Financial output.
12. Financial features đúng source.
13. `period_end` hiển thị.
14. `available_at` hiển thị.
15. revision/vintage/status được preserve khi có.
16. Market và Financial vẫn độc lập.
17. Không tạo combined cluster.
18. Không look-ahead.
19. Không zero-fill.
20. Không chạy lại clustering.
21. Không tính lại feature.
22. Có ticker search.
23. Có cluster member views.
24. Có missing/error states.
25. Có provenance.
26. Dashboard data-driven.
27. Snapshot mới có thể được nhận khi upstream publish artifact mới.
28. E2E verification PASS.
29. Có exact run instructions.
30. Có manual testing instructions.

---

# 40. FINAL ARCHITECTURE

```text
                         decision_date
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
        MARKET ARTIFACTS             FINANCIAL ARTIFACTS
               │                             │
               ▼                             ▼
          Data Loading                  Data Loading
               │                             │
               ▼                             ▼
          Validation                    Validation
               │                             │
               ▼                             ▼
      Exact Market Snapshot      PIT-safe Financial State
               │                             │
               └──────────────┬──────────────┘
                              ▼
                          Query Layer
                              │
                              ▼
                         Visualization
                              │
                              ▼
                           Streamlit
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    M3-B DASHBOARD                            │
│                                                              │
│              MARKET       |       FINANCIAL                  │
│                                                              │
│  Cluster visualization    |  Cluster visualization           │
│  Cluster profile          |  Cluster profile                 │
│  Members                  |  Members                         │
│  Market features          |  Financial features              │
│                           |  period_end / available_at        │
└──────────────────────────────────────────────────────────────┘
```

Future automation remains external:

```text
New data
↓
Upstream processing
↓
Clustering
↓
Validation
↓
Verified artifact
↓
Dashboard automatically discovers new state
```

---

# PHẦN C — M3-C: BÁO CÁO KỸ THUẬT VÀ NOTEBOOK TÁI LẬP KẾT QUẢ

# 48. MỤC TIÊU M3-C

M3-C bám đúng yêu cầu:

> **Báo cáo kỹ thuật + notebook tái lập được kết quả.**

M3-C **không tạo phương pháp mới** và **không làm lại vai trò của M3-A hoặc M3-B**.

M3-C phải thực hiện ba việc chính:

1. **Báo cáo kỹ thuật** toàn bộ kết quả nghiên cứu M3, trọng tâm là kết quả M3-A gồm chiến lược kết hợp, hai đối chứng và benchmark VNINDEX;
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

# 49. KẾ HOẠCH NOTEBOOK M3-C

M3-C sử dụng **4 notebook chính**:

```text
M3/notebooks/
├── 01_Du_Lieu_Va_PIT.ipynb
├── 02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb
├── 03_Tai_Lap_Backtest_Va_Benchmark.ipynb
└── 04_Bao_Cao_Danh_Gia_Cuoi.ipynb
```

Bốn notebook này có vai trò khác với M3-A:

```text
M3-A
→ tạo kết quả nghiên cứu chính thức

M3-C
→ đọc đúng đầu vào / kết quả đã khóa
→ tái lập các phép tính và phần trình bày cần thiết
→ đối chiếu với kết quả chính thức
→ phục vụ báo cáo và khả năng kiểm tra lại
```

Không bắt buộc toàn bộ phép tính phải được viết trực tiếp trong notebook. Notebook nên ưu tiên gọi các mô-đun Python chính thức đã được kiểm thử trong repo.

Mỗi notebook phải ghi rõ:

- mục tiêu;
- phạm vi;
- đầu vào chính xác;
- phiên bản / mã băm đầu vào nếu có;
- phiên bản mã nguồn / mô-đun được gọi;
- đầu ra cần tái lập;
- các bước thực hiện;
- bảng / biểu đồ cần tạo;
- cách đối chiếu với kết quả chính thức;
- kết luận `ĐẠT` / `KHÔNG ĐẠT`;
- điều kiện dừng nếu thiếu dependency.

---

# 50. M3-C NHIỆM VỤ 01 — NOTEBOOK DỮ LIỆU VÀ PIT

## Mục tiêu

Giúp người đọc xác định đúng dữ liệu mà M3 sử dụng và kiểm tra được rằng việc ghép Market–Financial không sử dụng thông tin tương lai.

Notebook này **không thay thế** Nhiệm vụ 1.1–1.3 của M3-A và không tự tạo lại một quy tắc PIT mới.

## Đầu vào bắt buộc

Tối thiểu gồm:

- manifest / thông tin phiên bản của bộ bàn giao Market;
- kết quả xác minh bộ bàn giao Market;
- manifest / thông tin phiên bản của bộ bàn giao Financial;
- kết quả xác minh bộ bàn giao Financial;
- `aligned_market_financial_snapshots.csv` hoặc output chính thức tương đương từ M3-A 1.3;
- định nghĩa Đoạn A, khoảng trống dữ liệu và Đoạn B;
- quy tắc PIT / revision đã thực sự được phê duyệt tại thời điểm chạy.

Nếu quy tắc chọn Financial snapshot khi có nhiều snapshot hợp lệ vẫn chưa được khóa thì notebook không được tự quyết định thay M3-A.

## Đầu ra mong đợi

- bảng tóm tắt nguồn dữ liệu và phiên bản;
- bảng tóm tắt Đoạn A / gap / Đoạn B;
- ví dụ một số `decision_date` và cặp Market–Financial snapshot đã được M3-A căn chỉnh;
- kiểm tra điều kiện:

```text
financial_available_at <= decision_date
```

- thống kê các trạng thái căn chỉnh như `PIT_ALIGNED`, `NO_PIT_FINANCIAL_SNAPSHOT` hoặc trạng thái chính thức tương đương;
- kết luận notebook có khớp output căn chỉnh chính thức hay không.

## Các bước thực hiện theo thứ tự

1. Đọc manifest và kết quả xác minh của hai hệ.
2. Hiển thị phiên bản, mã băm và giai đoạn dữ liệu.
3. Đọc output căn chỉnh PIT chính thức của M3-A.
4. Kiểm tra mọi Financial snapshot được dùng đều thỏa `financial_available_at <= decision_date`.
5. Chọn một số mốc thời gian làm ví dụ trực quan.
6. Chứng minh notebook **đọc và kiểm chứng** kết quả căn chỉnh, không tự chọn lại snapshot bằng một rule khác.
7. Đối chiếu số dòng / trạng thái với artifact chính thức.

## Kiểm tra / xác nhận

- không có Financial snapshot từ tương lai;
- không tự điền snapshot tương lai cho mốc thiếu dữ liệu;
- không tự thay đổi revision rule;
- kết quả notebook khớp output M3-A 1.3.

## Điều kiện hoàn thành

`ĐẠT` khi người đọc có thể trả lời:

> M3 đang dùng bộ dữ liệu nào, ở phiên bản nào, và tại mỗi mốc Market thì Financial snapshot nào đã được phép sử dụng theo PIT?

## Bàn giao

Bàn giao cho Notebook 02.

---

# 51. M3-C NHIỆM VỤ 02 — NOTEBOOK TÁI LẬP QUÁ TRÌNH CHỌN DANH MỤC

## Mục tiêu

Tái lập và giải thích được đường đi từ dữ liệu đã căn PIT đến **Target Portfolio** tại một `decision_date`.

Notebook phải giúp người đọc trả lời:

> Vì sao một mã được đưa vào Candidate Universe, được xếp hạng ở vị trí đó và cuối cùng được chọn hoặc không được chọn vào top 30%?

## Đầu vào bắt buộc

Tối thiểu gồm các output chính thức của M3-A:

- cặp snapshot đã căn PIT;
- `combined_candidates.csv`;
- `candidate_eligibility_audit.csv`;
- contract / quyết định chính thức của MC1–MC3;
- contract / quyết định chính thức của FC1–FC3;
- `decision_features.csv`;
- quy tắc xếp hạng kết hợp đã khóa;
- `combined_ranking.csv`;
- `target_portfolios_combined.csv`;
- target portfolio Market-only / Financial-only nếu hai đối chứng đã được tạo.

Nếu MC1–MC3, FC1–FC3, Candidate rule hoặc Combined Ranking rule còn `PENDING`, notebook này chưa đủ điều kiện chạy chính thức.

## Đầu ra mong đợi

- ví dụ tạo Candidate Universe tại một hoặc một vài `decision_date`;
- bảng giải thích mã được giữ / loại và lý do;
- bảng MC1–MC3 và FC1–FC3;
- bảng xếp hạng kết hợp;
- minh họa:

```text
n_select = ceil(0.30 × N_candidates)
```

- Target Portfolio cuối cùng và `target_weight`;
- đối chiếu kết quả tái lập với artifact chính thức.

## Các bước thực hiện theo thứ tự

1. Chọn một `decision_date` có đủ dữ liệu làm ví dụ.
2. Đọc đúng cặp Market–Financial snapshot đã được M3-A 1.3 khóa cho ngày đó.
3. Đọc hoặc tái lập Candidate Universe bằng đúng mô-đun / rule chính thức.
4. Hiển thị lý do vào / loại của một số mã mẫu.
5. Tái lập MC1–MC3 và FC1–FC3 bằng đúng contract đã khóa.
6. Tái lập Combined Ranking bằng đúng rule đã khóa.
7. Tính `ceil(30% × N_candidates)`.
8. Tạo lại Target Portfolio.
9. So sánh với output M3-A chính thức.

## Kiểm tra / xác nhận

- không thử thêm công thức tiêu chí mới;
- không đổi Candidate rule;
- không đổi Combined Ranking rule;
- không đổi tỷ lệ 30%;
- kết quả phải khớp artifact M3-A hoặc nằm trong tolerance số học đã được định nghĩa.

## Điều kiện hoàn thành

`ĐẠT` khi người đọc có thể lần theo đầy đủ:

```text
Cặp snapshot PIT-safe
        ↓
Candidate Universe
        ↓
6 tiêu chí
        ↓
Combined Ranking
        ↓
Top 30%
        ↓
Target Portfolio
```

## Bàn giao

Bàn giao cho Notebook 03.

---

# 52. M3-C NHIỆM VỤ 03 — NOTEBOOK TÁI LẬP BACKTEST VÀ SO SÁNH BENCHMARK

## Mục tiêu

Tái lập các kết quả backtest và tạo lại các bảng / biểu đồ chính dùng để đánh giá chiến lược trên cùng một khung so sánh.

Đây là notebook trọng tâm của M3-C.

## Đầu vào bắt buộc

Tối thiểu gồm các output đã được M3-A niêm phong:

- Target Portfolio của Combined;
- Target Portfolio của Market-only;
- Target Portfolio của Financial-only;
- `trade_ledger`;
- executed holdings / executed portfolios;
- security period returns;
- return contributions;
- portfolio returns;
- portfolio NAV;
- cash weights;
- turnover;
- failed executions;
- kết quả benchmark VNINDEX đã được căn đúng theo từng segment;
- định nghĩa Đoạn A, gap và Đoạn B;
- bộ chỉ số performance đã được duyệt.

## Đầu ra mong đợi

Theo từng đoạn A và B riêng biệt:

- bảng kết quả Combined;
- bảng kết quả Market-only;
- bảng kết quả Financial-only;
- bảng kết quả benchmark VNINDEX;
- biểu đồ NAV;
- biểu đồ drawdown nếu đã được định nghĩa;
- bảng turnover;
- cash ratio;
- failed execution rate;
- các performance metrics đã được duyệt;
- bảng so sánh tổng hợp.

Không nối NAV Đoạn A và Đoạn B qua khoảng trống dữ liệu.

## Các bước thực hiện theo thứ tự

1. Xác nhận đúng version/hash của kết quả backtest đã niêm phong.
2. Đọc riêng Đoạn A.
3. Tái tạo các bảng / chỉ số / biểu đồ của Đoạn A.
4. So sánh Combined với Market-only và Financial-only.
5. So sánh Combined với VNINDEX.
6. Đọc riêng Đoạn B bằng đúng cách tính tương tự.
7. Tái tạo kết quả Đoạn B.
8. Không nối A–B thành một chuỗi NAV liên tục.
9. Báo cả kết quả thuận lợi và bất lợi.
10. Không dùng Sharpe nếu contract M3 hiện tại vẫn khóa `không dùng Sharpe`.

## Kiểm tra / xác nhận

- số liệu không nhập tay;
- mọi số trong bảng / biểu đồ truy ngược được về tệp nguồn;
- cùng bộ metric được áp dụng nhất quán giữa chiến lược và benchmark khi metric đó có ý nghĩa;
- các kết quả tái lập khớp với kết quả M3-A đã niêm phong.

## Điều kiện hoàn thành

`ĐẠT` khi người đọc có thể chạy notebook từ các input đã khóa và tạo lại được các kết quả chính dùng trong phần backtest của báo cáo kỹ thuật.

## Bàn giao

Bàn giao cho Notebook 04 và Báo cáo kỹ thuật M3.

---

# 53. M3-C NHIỆM VỤ 04 — NOTEBOOK BÁO CÁO ĐÁNH GIÁ CUỐI

## Mục tiêu

Trình bày và tái tạo phần báo cáo của **đánh giá cuối** sau khi M3-A đã:

```text
khóa chiến lược
        ↓
thu thập / nhận dữ liệu đánh giá cuối
        ↓
chạy đúng quy trình đã khóa
        ↓
niêm phong kết quả đánh giá cuối
```

Notebook này **không tự mở một giai đoạn đánh giá mới** và không dùng kết quả cuối để điều chỉnh lại chiến lược.

## Đầu vào bắt buộc

- quy ước giai đoạn đánh giá cuối;
- mã băm / phiên bản strategy đã khóa trước khi mở dữ liệu cuối;
- output đánh giá cuối đã được M3-A niêm phong;
- VNINDEX tương ứng với đúng giai đoạn đánh giá cuối;
- cùng bộ metric đã dùng cho phần đánh giá lịch sử, nếu metric đó hợp lệ cho giai đoạn cuối.

## Đầu ra mong đợi

- bảng kết quả đánh giá cuối;
- biểu đồ cần thiết;
- bảng so sánh với VNINDEX;
- bảng so sánh với Đoạn A và Đoạn B ở mức phù hợp;
- phần ghi nhận kết quả bất lợi;
- giới hạn dữ liệu và giới hạn diễn giải.

## Các bước thực hiện theo thứ tự

1. Xác nhận strategy hash / config version đã được khóa trước khi mở dữ liệu cuối.
2. Xác nhận output đánh giá cuối đúng là output đã niêm phong.
3. Đọc kết quả cuối, không thay rule.
4. Tạo lại các bảng / biểu đồ theo cùng chuẩn báo cáo với giai đoạn lịch sử.
5. So sánh với VNINDEX của giai đoạn cuối.
6. So sánh thận trọng với kết quả lịch sử.
7. Ghi rõ mọi giới hạn và kết quả không thuận lợi.

## Kiểm tra / xác nhận

- không thay strategy sau khi xem kết quả cuối;
- không thay metric chỉ vì kết quả xấu;
- notebook khớp output đánh giá cuối đã niêm phong;
- không gọi giai đoạn đã từng được xem trước là “hoàn toàn chưa từng thấy”.

## Điều kiện hoàn thành

`ĐẠT` khi phần đánh giá cuối có thể được trình bày lại từ output đã khóa, với nguồn và phiên bản rõ ràng.

## Bàn giao

Bàn giao cho Báo cáo kỹ thuật M3.

---

# 54. BÁO CÁO KỸ THUẬT M3

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
9. Kết quả Combined.
10. Hai đối chứng Market-only và Financial-only.
11. Benchmark chính thức: VNINDEX.
12. Kết quả lịch sử Đoạn A và Đoạn B trình bày tách biệt.
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

# 55. `HUONG_DAN_THUC_HIEN_M3.md` — HƯỚNG DẪN TÁI LẬP

Tài liệu này phục vụ yêu cầu **“notebook tái lập được kết quả”** bằng cách chỉ rõ cách một người mới đi từ repo và các input đã version hóa đến đúng notebook / mô-đun cần chạy.

## 55.1. Mỗi bước phải ghi

- mục đích;
- tệp cần đọc;
- phiên bản / mã băm cần kiểm tra;
- lệnh cần chạy;
- mô-đun / notebook được gọi;
- đầu ra cần tạo hoặc kiểm tra;
- cách đối chiếu với kết quả chính thức;
- điều kiện dừng;
- bước tiếp theo.

## 55.2. Luồng tái lập tổng quát

```text
Kiểm tra repo / commit / môi trường
        ↓
Kiểm tra manifest và input versions
        ↓
Notebook 01 — Dữ liệu và PIT
        ↓
Notebook 02 — Tái lập lựa chọn danh mục
        ↓
Notebook 03 — Tái lập backtest và benchmark
        ↓
Notebook 04 — Báo cáo đánh giá cuối
        ↓
Đối chiếu với artifact chính thức
        ↓
Tạo / cập nhật Báo cáo kỹ thuật
```

Nếu cần tái chạy **toàn bộ pipeline nghiên cứu** chứ không chỉ notebook báo cáo, hướng dẫn phải trỏ về đúng command / module chính thức của M3-A và M3-B; không copy lại business logic vào notebook.

## 55.3. Các trường hợp phải dừng

Phải ghi rõ **DỪNG** nếu:

- thiếu input / manifest bắt buộc;
- hash hoặc phiên bản không khớp;
- Market / Financial handoff chưa đạt;
- quy tắc PIT / revision cần thiết cho output đang tái lập chưa được khóa;
- MC1–MC3 hoặc FC1–FC3 chưa được duyệt;
- Candidate rule hoặc Combined Ranking rule chưa được duyệt;
- cơ sở tính lợi suất / execution chưa được chứng nhận;
- artifact backtest chính thức chưa được niêm phong;
- benchmark VNINDEX chưa được xác định đầy đủ;
- giai đoạn đánh giá cuối chưa được khóa hoặc kết quả cuối chưa được niêm phong;
- notebook tạo kết quả không khớp artifact chính thức mà chưa giải thích được nguyên nhân.

## 55.4. Kiểm tra môi trường tối thiểu

Có thể giữ các lệnh kiểm tra repo / test hiện có, ví dụ:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short

.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

Lệnh chạy notebook hoặc mô-đun cụ thể chỉ được ghi sau khi đường dẫn / command thực tế đã được xác minh trong repo.

---

# 56. RANH GIỚI TRÁCH NHIỆM CỦA M3-C

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

# 57. ĐẦU RA BÀN GIAO M3-C

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

# 58. ĐIỀU KIỆN HOÀN THÀNH NỘI BỘ M3-C

M3-C chỉ được coi là hoàn tất khi:

- 4 notebook chính chạy được với đầu vào đã version hóa;
- mỗi notebook ghi rõ input, code version và output;
- Notebook 01 chứng minh được PIT/no-look-ahead từ output chính thức;
- Notebook 02 tái lập được Candidate → 6 tiêu chí → ranking → top 30% → Target Portfolio;
- Notebook 03 tái lập được các bảng / metric / biểu đồ backtest và benchmark theo từng đoạn;
- Notebook 04 trình bày lại được đánh giá cuối từ output đã niêm phong mà không thay strategy;
- Báo cáo kỹ thuật lấy số liệu từ tệp / notebook, không nhập tay;
- `HUONG_DAN_THUC_HIEN_M3.md` chỉ rõ thứ tự, command và điều kiện dừng;
- mọi số liệu chính truy ngược được về input, config, code version và artifact nguồn;
- không có notebook riêng lặp lại nhiệm vụ xây / kiểm thử dashboard của M3-B.

---

# 59. CẤU TRÚC THƯ MỤC M3 ĐỀ XUẤT

```text
M3/
├── KE_HOACH_M3_TONG_THE_CHI_TIET_V10_BACKTEST_CHI_TIET.md
├── HUONG_DAN_THUC_HIEN_M3.md
│
├── data/
│   ├── input_manifest/
│   ├── aligned/
│   ├── execution_support/
│   ├── benchmark/
│   └── final_unseen/
│
├── decisions/
│   ├── market_criteria/
│   ├── financial_criteria/
│   ├── financial_staleness/
│   ├── combined_strategy/
│   ├── return_basis/
│   └── final_evaluation/
│
├── notebooks/
│   ├── 01_Du_Lieu_Va_PIT.ipynb
│   ├── 02_Tai_Lap_Lua_Chon_Danh_Muc.ipynb
│   ├── 03_Tai_Lap_Backtest_Va_Benchmark.ipynb
│   └── 04_Bao_Cao_Danh_Gia_Cuoi.ipynb
│
├── artifacts/
│   ├── m3-a/
│   │   ├── alignment/
│   │   ├── selection/
│   │   ├── executions/
│   │   ├── historical/
│   │   └── final/
│   ├── m3-b/
│   │   ├── bundle/
│   │   └── verification/
│   └── m3-c/
│
└── reports/
    └── BAO_CAO_KY_THUAT_M3.md
```

Mã nguồn dùng lại nhiều lần nên ưu tiên đặt trong `src/delta_t1/`; không nhét logic nghiệp vụ chính vào notebook.

---

# 60. THỨ TỰ THỰC HIỆN TOÀN DỰ ÁN

## Giai đoạn 0 — Khóa các quyết định còn thiếu

Trước backtest chính thức phải có:

1. MC1;
2. MC2;
3. MC3;
4. FC1;
5. FC2;
6. FC3;
7. điều kiện đủ của cụm thị trường;
8. điều kiện đủ của cụm tài chính;
9. quy tắc tạo tập ứng viên kết hợp;
10. quy tắc gộp hai nhánh thành thứ hạng cuối;
11. quy tắc độ cũ dữ liệu tài chính.

Thiếu một quyết định có ảnh hưởng trực tiếp đến lựa chọn mã → **BỊ CHẶN**.

## Giai đoạn 1 — Đầu vào và căn chỉnh

12. Kiểm kê đầu vào.
13. Xác minh bộ bàn giao thị trường.
14. Xác minh bộ bàn giao tài chính.
15. Căn chỉnh thời gian/PIT.
16. Xác nhận cơ sở tính lợi suất.
17. Xác nhận khả năng giao dịch.

## Giai đoạn 2 — Khóa chiến lược

18. Khóa 3 tiêu chí thị trường.
19. Khóa 3 tiêu chí tài chính.
20. Khóa quy tắc kết hợp.
21. Khóa toàn bộ chiến lược.

## Giai đoạn 3 — Xây danh mục và chuẩn bị giao dịch

22. Tạo bảng 6 tiêu chí.
23. Tạo tập ứng viên kết hợp.
24. Xếp hạng và chọn 30%.
25. Tạo đối chứng chỉ thị trường.
26. Tạo đối chứng chỉ tài chính.
27. Tạo danh mục mục tiêu theo từng `decision_date`.
28. Xác định phiên giao dịch hợp lệ kế tiếp.
29. So sánh danh mục hiện tại với danh mục mục tiêu.
30. Sinh BUY / SELL / HOLD theo chênh lệch tỷ trọng.
31. Kiểm tra khả năng thực hiện giao dịch.
32. Tạo danh mục thực tế và phần tiền mặt.
33. Ghi `trade_ledger`.

## Giai đoạn 4 — Backtest

34. Khóa hai đoạn lịch sử: A = M2 Development `30/11/2023 → 24/01/2025`; B = M2 Holdout `27/02/2026 → 28/08/2026`.
35. Đánh dấu khoảng trống `25/01/2025 → 26/02/2026`; không nối giả A và B.
36. Xây benchmark.
37. Hoàn thiện backtest engine dùng chung.
38. Chạy fixture test cho BUY / SELL / HOLD / cash / return / NAV / rebalance.
39. Chạy Đoạn A:
    - thực hiện giao dịch;
    - nắm giữ;
    - tính lợi suất từng mã;
    - tính đóng góp lợi suất;
    - tính lợi suất danh mục;
    - cập nhật NAV;
    - tính tỷ trọng trước tái cân bằng;
    - tái cân bằng hàng tháng.
40. Khóa toàn bộ kết quả Đoạn A; không sửa quy tắc.
41. Chạy Đoạn B bằng đúng cùng engine và cùng quy tắc.
42. Khóa toàn bộ kết quả Đoạn B.
43. Tính chỉ số và so sánh theo từng đoạn.
44. Lưu `trade_ledger`, holdings, return, NAV, turnover, cash và báo cáo đối chiếu.

> **Lưu ý:** các số thứ tự trong runbook là trình tự thao tác, không phải số hiệu Nhiệm vụ M3-A/M3-B/M3-C.

## Giai đoạn 5 — Dashboard

45. Khóa schema hiển thị.
46. Tạo gói dữ liệu hiển thị.
47. Mở rộng lớp đọc dữ liệu sản phẩm.
48. Mở rộng API backend.
49. Xây khung giao diện.
50. Xây màn hình tổng quan.
51. Xây màn hình dịch chuyển cụm.
52. Xây màn hình chi tiết cổ phiếu.
53. Kiểm tra giao diện.
54. Kiểm tra từ đầu đến cuối.

## Giai đoạn 6 — Đánh giá cuối

55. Thu thập dữ liệu thị trường và tài chính mới.
56. Chạy hai quy trình phân cụm đã khóa.
57. Khóa giai đoạn cuối.
58. Căn chỉnh PIT.
59. Chạy cùng quy tắc chọn mã.
60. Chạy cùng bộ máy backtest.
61. Niêm phong kết quả.

## Giai đoạn 7 — Báo cáo và tái lập

62. Hoàn thiện notebook.
63. Hoàn thiện `HUONG_DAN_THUC_HIEN_M3.md`.
64. Hoàn thiện báo cáo kỹ thuật.
65. Kiểm tra truy nguyên nguồn.
66. Niêm phong bộ bàn giao M3 cuối.

---

# 61. CÁC ĐIỀU TUYỆT ĐỐI KHÔNG LÀM

1. Không gộp đặc trưng thị trường và tài chính để tạo một K mới trong M3.
2. Không chọn 30% riêng ở thị trường và tài chính rồi ghép.
3. Không lấy kết quả của hai backtest riêng để “tính” chiến lược kết hợp.
4. Không thay `K_market` vì kết quả M3.
5. Không thay `K_financial` vì kết quả M3.
6. Không dùng `period_end` thay `available_at`.
7. Không giữ trạng thái tài chính cũ vô hạn khi chưa có quy tắc độ cũ.
8. Không dùng bản điều chỉnh tài chính công bố sau ngày t cho quyết định tại t.
9. Không dùng giá phiên t+1 để xếp hạng ở ngày t.
10. Không lọc tập cổ phiếu lịch sử bằng tập ở thời điểm cuối.
11. Không tạo giả các tháng/snapshot trong khoảng `25/01/2025 → 26/02/2026` giữa Đoạn A — M2 Development (`30/11/2023 → 24/01/2025`) và Đoạn B — M2 Holdout (`27/02/2026 → 28/08/2026`).
12. Không đổi tỷ lệ 30% sau khi xem hiệu quả.
13. Không đổi 6 tiêu chí hoặc trọng số sau khi xem hiệu quả.
14. Không đổi quy tắc kết hợp sau khi xem hiệu quả.
15. Không tự chọn mã thay cho mã không giao dịch được.
16. Không phân bổ lại phần vốn của mã không giao dịch được.
17. Không tự chọn loại giá thực thi nếu return basis chưa khóa.
18. Không tự đặt quy tắc xử lý một giao dịch BUY/SELL thất bại nếu hợp đồng chưa quy định.
19. Không tự đặt lại trọng số về equal-weight trong giữa kỳ nắm giữ; chỉ tái cân bằng tại mốc hợp lệ.
20. Không nối NAV của Đoạn A và Đoạn B.
21. Không dùng Sharpe.
22. Không xóa hoặc che kết quả không thuận lợi.
23. Dashboard không tính lại logic nghiên cứu.
24. Không gộp Market và Financial thành một cluster mới trên dashboard.
25. Không ép Financial thành dữ liệu hàng tháng nếu thực tế không có trạng thái mới.
26. Giao diện không tự thực hiện ghép PIT.
27. Giao diện không tự tính điểm/tiêu chí.
28. API chỉ đọc không được biến thành bộ máy nghiên cứu.
29. Không hiển thị dữ liệu thiếu thành 0.
30. Không gọi một cặp `(market_cluster, financial_cluster)` là “một cụm mới” nếu đó chỉ là tổ hợp của hai nhãn độc lập.
31. Không biến nhãn phân cụm thành khuyến nghị mua/bán.

---

# 62. ĐIỀU KIỆN HOÀN THÀNH M3-A

M3-A chỉ hoàn tất khi:

- bộ bàn giao thị trường đã được xác minh;
- bộ bàn giao tài chính đã được xác minh;
- căn chỉnh PIT đạt;
- quy tắc độ cũ tài chính đã được duyệt;
- cơ sở tính lợi suất đã được chứng nhận;
- bảng khả năng giao dịch đã sẵn sàng;
- MC1/MC2/MC3 đã được duyệt;
- FC1/FC2/FC3 đã được duyệt;
- điều kiện đủ và xếp hạng kết hợp đã được duyệt;
- chiến lược đã khóa;
- top 30% được áp dụng sau khi tạo tập ứng viên kết hợp;
- hai đối chứng đã được định nghĩa;
- benchmark VNINDEX đã được định nghĩa và đủ điều kiện sử dụng;
- kiểm thử mẫu đạt;
- các đoạn lịch sử đã được đánh giá;
- đánh giá cuối đã được thực hiện;
- không có điều chỉnh lại chiến lược sau khi mở kết quả cuối.

# 63. ĐIỀU KIỆN HOÀN THÀNH M3-B

M3-B hoàn tất khi:

- schema hiển thị đã có phiên bản;
- gói dữ liệu hiển thị bất biến;
- backend chỉ đọc gói dữ liệu;
- kiểm thử API đạt;
- giao diện tiếp tục dùng HTML/CSS/JavaScript thuần hiện có;
- màn hình tổng quan phân biệt rõ hai hệ;
- ngày thị trường và `available_at` tài chính hiển thị riêng;
- màn hình dịch chuyển tôn trọng tần suất cập nhật khác nhau;
- màn hình chi tiết cho thấy lịch sử của cả hai hệ;
- trạng thái thiếu/quá cũ hiển thị rõ;
- không có tính toán nghiên cứu trong dashboard;
- không có khuyến nghị danh mục;
- kiểm tra desktop/mobile đạt;
- truy nguyên từ nguồn → gói → API → giao diện đạt.

# 64. ĐIỀU KIỆN HOÀN THÀNH M3-C

M3-C hoàn tất khi:

- 4 notebook chính hoặc bộ tương đương tái lập được các kết quả nghiên cứu cần dùng trong báo cáo;
- mỗi notebook ghi rõ đầu vào, phiên bản mã nguồn, đầu ra và cách đối chiếu với artifact chính thức;
- Notebook 01 kiểm tra được dữ liệu/PIT mà không tự tạo rule mới;
- Notebook 02 tái lập được quá trình chọn danh mục đến Target Portfolio;
- Notebook 03 tái lập được backtest, benchmark và các bảng/biểu đồ chính theo từng đoạn;
- Notebook 04 trình bày lại được đánh giá cuối từ kết quả đã niêm phong, không tuning lại strategy;
- báo cáo kỹ thuật đọc số liệu từ tệp/notebook có phiên bản, không nhập tay;
- `HUONG_DAN_THUC_HIEN_M3.md` có thứ tự thực hiện, command, cách kiểm tra và điều kiện dừng;
- báo cáo kỹ thuật trình bày chiến lược kết hợp, hai đối chứng, benchmark VNINDEX, kết quả lịch sử và kết quả đánh giá cuối;
- phần dashboard nếu được nhắc trong báo cáo chỉ mang tính mô tả/tham chiếu; việc xây và kiểm thử dashboard vẫn thuộc M3-B;
- mọi số liệu chính truy ngược được về nguồn, phiên bản, cấu hình, mã nguồn và mã băm.

---

# 65. TRẠNG THÁI HIỆN TẠI SAU KHI CẬP NHẬT

## Đã chốt

- hai hệ phân cụm độc lập;
- `K_market` và `K_financial` độc lập;
- M3 không phân cụm lại bộ đặc trưng thô kết hợp;
- kết hợp xảy ra ở bước xây danh mục;
- thị trường có 3 tiêu chí;
- tài chính có 3 tiêu chí khác thị trường;
- top 30% chỉ được chọn sau khi có tập ứng viên kết hợp;
- chỉ thị trường và chỉ tài chính là hai đối chứng;
- chỉ mua, không bán khống;
- không dùng đòn bẩy;
- trọng số bằng nhau;
- tái cân bằng hàng tháng;
- giao dịch tại giá đóng cửa phiên hợp lệ kế tiếp;
- mã không giao dịch được → phần vốn chuyển thành tiền mặt;
- không chọn mã thay thế;
- không phân bổ lại phần vốn lỗi;
- tiền mặt có lợi suất 0;
- chi phí chính 0;
- trượt giá chính 0;
- không dùng Sharpe;
- đánh giá cuối dùng dữ liệu mới sau 28/08/2026;
- dashboard dùng Python Product Layer + HTML/CSS/JavaScript thuần và API chỉ đọc.

## Còn phải quyết định trước lần chạy kết hợp chính thức

1. định nghĩa chính xác MC1;
2. định nghĩa chính xác MC2;
3. định nghĩa chính xác MC3;
4. định nghĩa chính xác FC1;
5. định nghĩa chính xác FC2;
6. định nghĩa chính xác FC3;
7. điều kiện đủ của cụm thị trường;
8. điều kiện đủ của cụm tài chính;
9. cách tạo tập ứng viên kết hợp;
10. cách gộp điểm/thứ hạng hai nhánh;
11. quy tắc độ cũ dữ liệu tài chính;
12. ngày kết thúc chính xác của giai đoạn đánh giá cuối;

Không để người lập trình tự quyết các mục này.

---

# 66. KẾT LUẬN

Luồng M3 chính:

```text
PHÂN CỤM THỊ TRƯỜNG                 PHÂN CỤM TÀI CHÍNH
        ↓                                   ↓
Nhãn phân cụm thị trường           Nhãn phân cụm tài chính
        │                                   │
        └──────────────┬────────────────────┘
                       ↓
             CĂN CHỈNH THEO PIT
                       ↓
        XÁC ĐỊNH MÃ ĐỦ ĐIỀU KIỆN KẾT HỢP
                       ↓
       3 TIÊU CHÍ THỊ TRƯỜNG + 3 TIÊU CHÍ TÀI CHÍNH
                       ↓
            QUY TẮC XẾP HẠNG ĐÃ KHÓA
                       ↓
               TẬP ỨNG VIÊN KẾT HỢP
                       ↓
          CHỌN 30% SỐ MÃ ĐỨNG ĐẦU
                       ↓
              TRỌNG SỐ BẰNG NHAU
                       ↓
      GIAO DỊCH Ở PHIÊN HỢP LỆ KẾ TIẾP
                       ↓
               BACKTEST
                       ↓
      ┌────────────────┼──────────────────┐
      ↓                ↓                  ↓
   KẾT HỢP       CHỈ THỊ TRƯỜNG     CHỈ TÀI CHÍNH
 chiến lược chính      đối chứng          đối chứng
      │                │                  │
      └────────────────┼──────────────────┘
                       ↓
        VNINDEX
                       ↓
     ĐÁNH GIÁ LỊCH SỬ A/B RIÊNG + ĐÁNH GIÁ CUỐI
                       ↓
             BÁO CÁO + DASHBOARD
```

Điểm cần nhớ:

> **Chiến lược kết hợp không phải là gộp dữ liệu thô, không phải cộng kết quả của hai lần backtest, và không phải chọn 30% ở hai nhánh rồi ghép.**

Chiến lược kết hợp dùng hai nhãn phân cụm đã được tạo độc lập, căn chỉnh chúng theo PIT, áp dụng hai bộ tiêu chí riêng, tạo tập ứng viên chung rồi mới xếp hạng và chọn 30% số mã đứng đầu.