DELTA / RISK-ADJUSTED MOMENTUM CLUSTERING

**KẾ HOẠCH XÂY DỰNG TOOL ĐỀ XUẤT ĐẦU TƯ**

Công cụ hỗ trợ đánh giá mức độ hấp dẫn đầu tư của từng mã cổ phiếu

Đề xuất tích hợp vào website DELTA Intelligence

**TRẠNG THÁI TÀI LIỆU**

| **THUỘC TÍNH**   | **THÔNG TIN**                                                                                                            |
|------------------|--------------------------------------------------------------------------------------------------------------------------|
| Loại tài liệu    | Kế hoạch triển khai Output và tích hợp website DELTA Intelligence — bản đề xuất                                          |
| Phạm vi          | Mục tiêu: đánh giá tại ngày truy cập thực tế; giai đoạn đầu mô phỏng tại ngày 02/01/2026; không dự báo tương lai |
| Repository       | trongnguyen1010/Risk-Adjusted-Momentum-Clustering                                                                        |
| Nhánh khảo sát   | feature/indicators-v1 · HEAD d31fbb5156912fea800f3e540f9bd9bbf76fbed1                                                    |
| Ngày khảo sát ban đầu     | 14/11/2026                                                                                                               |
| Cập nhật kế hoạch bàn giao | 15/11/2026. Chốt ngày demo, phạm vi tra cứu, vai trò Peers, bảng quyết định và dùng bộ B-PIT làm giàu cho Assessment. |
| Chế độ thực hiện | Chỉ phân tích/lập kế hoạch; không chỉnh sửa repository, schema, model hay artifact                                       |

**MỤC TIÊU MỘT CÂU**

Người dùng nhập mã cổ phiếu → hệ thống dùng dữ liệu, kết quả phân cụm M2 và chỉ số hợp lệ tại ngày đánh giá để đề xuất có nên cân nhắc đầu tư, kèm lý do, rủi ro, nguồn và độ tin cậy. Mục tiêu chính thức là đánh giá tại ngày truy cập thực tế; trước mắt sử dụng ngày mô phỏng 02/01/2026 vì dữ liệu hiện hành chưa đầy đủ.

# TÓM TẮT ĐIỀU HÀNH

**Đề xuất chính.** Thêm tab “Đánh giá đầu tư” tại trang /stocks hiện hữu; trình duyệt chỉ hiển thị kết quả, FastAPI chỉ đọc artifact đã phát hành. Không fit K-Means và không crawl khi người dùng nhập mã. Giai đoạn đầu xây dựng một bộ đánh giá theo ngày giả lập 02/01/2026; về lâu dài dùng ngày truy cập thực tế khi nguồn dữ liệu và bản phát hành đủ mới. Cả hai giai đoạn dùng chung Assessment Engine, rulebook và API.

Output trả một trong bốn kết quả: “Đáng cân nhắc đầu tư”, “Cần theo dõi”, “Chưa nên ưu tiên đầu tư” hoặc “Không đủ cơ sở”. Kết luận luôn kèm bằng chứng, các tín hiệu trái chiều và mức độ mới của dữ liệu; không đồng nghĩa lệnh MUA/BÁN, không cam kết lợi suất.

| **CÂU HỎI CỦA NGƯỜI DÙNG**                       | **HỆ THỐNG PHẢI TRẢ LỜI**                                                                                                                                    |
|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FPT thuộc nhóm nào?                              | Nhãn A và B của đúng snapshot/phiên bản; tên, đặc trưng, mức độ phù hợp và cờ chất lượng.                                                                    |
| FPT mạnh/yếu ở đâu? | Đối chiếu chỉ số thực tế với lịch sử chính mã và những cổ phiếu tương đồng theo cụm A v4/B-PIT, trên các chỉ số so sánh hợp lệ. |
| Có đáng cân nhắc đầu tư?                         | Một đề xuất tại ngày đánh giá được công bố rõ (đáng cân nhắc / cần theo dõi / chưa ưu tiên / không đủ cơ sở), kèm tín hiệu và nguồn. |
| Đánh giá còn mới không?                          | Ngày phiên giá, FY, ngày được dùng của BCTC, ngày nhãn A v4/B-PIT, phiên bản model và dữ liệu.                                                                      |
| Kết quả đang đánh giá thời điểm nào?           | Phân biệt ngày truy cập thực tế với ngày đánh giá mô phỏng (nếu có); hiển thị ngày giá, snapshot A, FY và ngày khả dụng của B; kiểm độ mới so với đúng ngày đánh giá. |

**KIẾN TRÚC ĐỀ XUẤT**

> INPUT: mã cổ phiếu (bắt buộc) / lịch sử hiển thị (tùy chọn, mặc định 10 năm)
>
> OFFLINE: dữ liệu có thời điểm hiệu lực + nhãn A v4/B-PIT đã duyệt + 9 đặc trưng A v4 và 9 đặc trưng B-PIT + quy tắc Output
>
> VERSIONED ASSESSMENT ARTIFACT: đánh giá + lý do + QA + manifest
>
> READ-ONLY FASTAPI: truy vấn artifact và khóa revision
>
> NEXT.JS /stocks → “Đánh giá đầu tư”: kết luận tại ngày đánh giá được ghi rõ + giải thích + kiểm chứng

**Ràng buộc triển khai.** Bản mô phỏng ngày 02/01/2026 chỉ phản ánh ngày đánh giá giả lập và phải kiểm chứng dữ liệu theo mốc này; tuyệt đối không gọi là đề xuất tại ngày truy cập thực tế. Chỉ chuyển sang đánh giá hiện tại khi dữ liệu, M2, rulebook và artifact đáp ứng các điều kiện đã duyệt.

# 1. MỤC TIÊU VÀ YÊU CẦU OUTPUT

Output có mục tiêu đánh giá mức độ hấp dẫn đầu tư tương đối của cổ phiếu tại thời điểm người dùng thực sự tra cứu. Để triển khai và kiểm thử với dữ liệu hiện có, trước mắt mô phỏng việc đánh giá tại ngày 02/01/2026; đây là bước triển khai tạm thời, không đổi mục tiêu sản phẩm. Công cụ không chỉ mô tả doanh nghiệp nhưng cũng không đưa chỉ thị “mua ngay tại giá X”. Phải phân biệt đặc điểm tài chính, điều kiện thị trường, rủi ro và độ tin cậy của dữ liệu; không mặc định 18 đặc trưng là mô hình định giá nội tại.

**Chức năng cốt lõi:** Tra cứu mã, giải thích cụm A v4/B-PIT, đối chiếu 18 đặc trưng với Peers theo chính sách tại mục 6.3, đưa ra kết luận có điều kiện và hiển thị lịch sử theo phương án một biểu đồ chuyển đổi chỉ số.

**D-ASS-01 — Bộ quy tắc đánh giá và đề xuất đầu tư của DELTA (định danh phương án kế hoạch, chưa phải thuật toán đã triển khai).** Bộ quy tắc sử dụng A v4, B-PIT và đúng 18 đặc trưng, đưa ra bốn trạng thái kết luận; yêu cầu giá của phiên giao dịch hoàn tất gần nhất tại `as_of`, dùng snapshot A v4 mới nhất hợp lệ theo **chu kỳ cập nhật tháng** (không áp ngưỡng cứng 22 phiên), kiểm PIT của B-PIT và áp dụng chính sách chọn Peers: ưu tiên Peers cùng A v4 và B-PIT; khi thiếu mẫu, so sánh tài chính mở rộng theo B-PIT, so sánh thị trường mở rộng theo A v4; mỗi đặc trưng cần tối thiểu 3 Peers hợp lệ để tính trung vị. Quy tắc kết luận phải có phiên bản và bằng chứng. Các điều kiện định lượng/logic đánh giá chưa đặc tả cần được kiểm chứng trước khi công bố verdict; không dự báo tương lai.

# 2. PHẠM VI, GIỚI HẠN VÀ NGUYÊN TẮC

## 2.1. Bao gồm trong Output

- Người dùng tra cứu một ticker; hệ thống ghi `request_time` và xác định `as_of` theo cấu hình: ngày giả lập 02/01/2026 trong giai đoạn đầu, ngày truy cập thực tế khi đã sẵn sàng dữ liệu cập nhật. Chỉ sử dụng bằng chứng hợp lệ không muộn hơn `as_of`. Người dùng có thể chọn cửa sổ lịch sử 5 hoặc 10 năm để xem đối chứng; không có bộ chọn ngày giả lập hoặc thời hạn dự báo trên giao diện.

- **Phạm vi mã tra cứu:** Bản demo nhận từng mã trong danh mục chứng khoán của bộ dữ liệu đã phát hành. FPT là ca minh họa và kiểm thử. Mỗi mã được xét theo dữ liệu của chính mã đó. Mã có trong danh mục nhưng thiếu bằng chứng bắt buộc vẫn tra cứu được và trả `INSUFFICIENT_EVIDENCE`.

- Chỉ đọc nhãn cụm **A v4** (thị trường) và **B-PIT** (tài chính) hợp lệ tại `as_of`; hiển thị snapshot/FY, phiên bản, profile, cỡ cụm và cờ chất lượng. Không thay bằng nhãn không thuộc hai artifact này.

- Output sử dụng kết quả phân cụm A v4 và B-PIT cùng 18 đặc trưng đầu vào tương ứng, gồm 9 đặc trưng thị trường và 9 đặc trưng tài chính. Các đặc trưng này được sử dụng để phân tích tình trạng cổ phiếu tại ngày đánh giá, đối chiếu với những cổ phiếu có đặc điểm phân cụm tương đồng và xây dựng đề xuất đầu tư theo rulebook đã được phê duyệt.

- Chọn Peers theo chính sách tại mục 6.3: ưu tiên các mã đồng thời cùng cụm A v4 và B-PIT; nếu không đủ mẫu, đặc trưng **tài chính** so với mã cùng B-PIT, đặc trưng **thị trường** so với mã cùng A v4. Chỉ tính trung vị khi có tối thiểu 3 Peers hợp lệ **cho từng đặc trưng**, ghi rõ `peer_basis`, số mã và thời điểm.

- Đưa ra nhận định định tính dựa trên quy tắc versioned, giải thích các tín hiệu thuận/lệch, rủi ro và hạn chế.

- Hiển thị nhãn thời điểm dữ liệu, chất lượng coverage, ngày usable của BCTC và link tới chi tiết số liệu gốc.

- Hỗ trợ mã thiếu dữ liệu / mới niêm yết với trạng thái “Không đủ cơ sở”, không cần tạo số giả.

## 2.2. Không bao gồm trong phạm vi này

- Không dự báo giá đích, lợi suất, xác suất tăng giá hoặc lời/lỗ ở bất kỳ khoảng thời gian nào trong tương lai. Không xây dựng mô hình định giá nội tại hay khẳng định cổ phiếu đang rẻ/đắt chỉ dựa vào 18 đặc trưng phân cụm.

- Không đặt lệnh mua/bán, quản lý danh mục cá nhân, gợi ý tỷ trọng theo khẩu vị rủi ro từng người.

- Không fit/refit M2, không thay k/cụm, không chỉnh methodology M3 trong request web.

- Không dùng nhãn phân cụm từ các nguồn ngoài A v4/B-PIT trong Assessment; giữ nguyên những chức năng nghiên cứu hiện có của website.

- Không tự tạo dữ liệu cho ngày đánh giá hoặc khoảng lịch sử 5/10 năm bằng hồi quy, điền 0 hay nội suy khi thiếu chứng cứ.

## 2.3. Nguyên tắc bất biến

| **NGUYÊN TẮC**        | **RÀNG BUỘC TRIỂN KHAI**                                                                           |
|-----------------------|----------------------------------------------------------------------------------------------------|
| Evidence before label | Kết luận phụ thuộc data/QA/decision policy; không được dựa độc lập vào A0/B0 hoặc nhãn “cụm mạnh”. |
| Time validity         | Dữ liệu dùng được tại as_of; FY, usable_from_date, cutoff và freshness phải đi kèm câu trả lời.    |
| Immutability          | Không ghi đè M2/M3/artifacts đã seal; mỗi lần build output mới có ID/manifest/hash riêng.          |
| Read-only product     | Product, FastAPI, Next.js chỉ đọc artifact; feature calculation và model fit chạy offline.         |
| No false precision    | Thiếu dữ liệu → null và giải thích; số liệu mô tả không biến thành lợi suất dự báo.                |
| Methodology approval  | Ngưỡng kết luận, điểm số, peers và quy tắc gán cụm mới cần owner phê duyệt và test.                |

# 3. HIỆN TRẠNG DELTA VÀ MỨC TÁI SỬ DỤNG

## 3.1. Kết quả audit trực tiếp tại branch feature/indicators-v1

| **THÀNH PHẦN** | **ĐÃ CÓ / ĐÃ KIỂM CHỨNG TỪ REPO**                                                         | **HÀNH ĐỘNG CHO OUTPUT**                                                            |
|----------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| A v4 | Mô hình phân cụm thị trường k=3, snapshot theo tháng và 9 đặc trưng, theo hướng chính thức D-DIR-01. | Là nguồn nhãn **thị trường duy nhất** của Output; đọc snapshot, đặc trưng, profile và phiên bản đã phát hành. |
| B-PIT | Có baseline M3 đã seal. Kế hoạch làm giàu FY2017–FY2024 dự kiến tạo phiên bản riêng. | Dùng **bản B-PIT sau làm giàu** làm nguồn nhãn tài chính của Assessment. Đọc nhãn theo FY và cutoff tại `as_of` từ run được bàn giao ở mục 6.4. |
| Website DELTA hiện hữu | Các trang/bản đồ nghiên cứu cũ có thể hiển thị A/B/C; API `/overview` và `/peers` hiện có dùng nhãn legacy. | **Giữ nguyên website hiện hữu**, nhưng Output phải truy xuất A v4 + B-PIT bằng đường dữ liệu riêng, tuyệt đối không kế thừa nhãn tài chính/cụm C từ API legacy. |
| Financial indicators | Có SQLite Indicators v1 baseline. Giai đoạn C của kế hoạch làm giàu dự kiến xuất SQLite dẫn xuất và bằng chứng theo từng ô điền. | Đọc 9 đặc trưng tài chính từ **đúng SQLite được pin bởi phiên bản B-PIT đã chọn**. Giữ giá trị, trạng thái và provenance theo từng chỉ số. |
| Web stock      | /stocks có 4 tab và nguồn API overview, fundamentals, scores/{year}, peers.               | Thêm tab đánh giá, tái dùng component và điều hướng URL.                            |
| Web stack      | Next.js/React/TypeScript + FastAPI read-only + bundle SQLite/manifest.                    | Thêm endpoint và artifact adapter; không làm ML trong browser/backend.              |
| M3 backtest    | Development và Holdout đã seal; Final NOT_READY, returns basis có hạn chế.                | Dùng làm bằng chứng rủi ro/giới hạn; không lấy backtest làm kết luận cho mã.        |

## 3.2. Phân biệt “có trong code” với “sẵn sàng sản phẩm”

API `/overview` và `/peers` của website hiện hữu đang phục vụ dữ liệu/nhãn A/B/C theo hợp đồng cũ. Những endpoint đó **không phải nguồn phân cụm của Output**. Output phải đọc đúng artifact A v4 và B-PIT đã pin, kiểm ngày khả dụng, nguồn và hash; tuyệt đối không dùng nhãn B mô tả/C kết hợp chỉ vì API cũ đã có. Artifact B-PIT cần được kiểm chứng nguồn và đóng gói/phát hành để backend đọc được, vì không thể coi nó đã có sẵn trong bundle web. Repository chưa có Assessment Engine hoàn chỉnh hoặc kết quả đánh giá đầu tư đã kiểm thử; giai đoạn đầu dùng `as_of` mô phỏng có đủ bằng chứng, không khẳng định đó là đánh giá hiện tại.

**Kiến trúc website hiện hành:** versioned research artifacts → `terminal_export.py` → `terminal.sqlite` + manifest → FastAPI read-only → Next.js. Dữ liệu local trong `data/` phần lớn không nằm trong Git. Kiểm tra deployment runtime và dữ liệu production là một gate riêng.

# 4. LUỒNG SỬ DỤNG CHO NHÀ ĐẦU TƯ

## 4.1. Hành trình người dùng (user journey)

1.  Người dùng mở DELTA → Tra cứu cổ phiếu → nhập một mã trong danh mục, ví dụ FPT.

2.  Người dùng chọn “Đánh giá đầu tư” cho mã vừa nhập. Hệ thống chọn ngày đánh giá theo cấu hình phát hành: ngày giả lập 02/01/2026 ở giai đoạn đầu, ngày truy cập thực tế khi triển khai đầy đủ. Cửa sổ lịch sử mặc định 10 năm; không yêu cầu chọn ngày giả lập hay thời hạn dự báo.

3.  Hệ thống kiểm tra định danh mã, trạng thái chứng khoán, điều kiện tham gia M2, độ đầy đủ dữ liệu và nguồn/phiên bản đã pin.

4.  Lấy snapshot A không muộn hơn `as_of` và kiểm độ mới so với chính `as_of`; chỉ dùng báo cáo tài chính, FY và nhãn B-PIT khả dụng tại ngày đánh giá. Không dùng dữ liệu sinh sau mốc giả lập chỉ vì hiện nay đã biết kết quả.

5.  Chọn Peers tại `as_of` theo chính sách ở mục 6.3: ưu tiên cùng cả hai cụm; khi thiếu mẫu, **đặc trưng tài chính** mở rộng cùng B-PIT và **đặc trưng thị trường** mở rộng cùng A v4. So sánh theo từng đặc trưng hợp lệ (ít nhất 3 mã để tính trung vị), kèm trung vị, nguồn và lịch sử chính mã.

6.  Áp dụng policy đánh giá versioned; có thể trả về “Không đủ cơ sở” do model stale, thiếu B-PIT hoặc dữ liệu bất hợp lệ.

7.  Trình bày đánh giá có giải thích, nguồn, ngày dữ liệu, rủi ro, nhãn cụm và đường dẫn “Xem bằng chứng”; nếu đang mô phỏng, hiển thị rõ ngày giả lập và khẳng định đây không phải đề xuất cho ngày truy cập thực tế.

## 4.2. Các trường hợp sử dụng ưu tiên

| **MÃ / TÌNH HUỐNG**                            | **HÀNH VI ĐÚNG**                                                                               |
|------------------------------------------------|------------------------------------------------------------------------------------------------|
| Mã trong danh mục có dữ liệu hợp lệ tại ngày mô phỏng 02/01/2026 | Trả đánh giá theo `as_of` giả lập + profile + peers + provenance cho mã đã tra cứu. FPT là một ví dụ. |
| FPT khi dữ liệu hiện tại đã được cập nhật      | Trả đánh giá theo ngày truy cập thực tế nếu vượt qua các gate; không dùng bản mô phỏng thay thế. |
| FPT ngày 14/11/2026 nhưng model A chỉ đến 2025 | Trả lịch sử gần nhất với STALE/HISTORICAL_ONLY; không gắn nhãn “đầu tư hôm nay”.               |
| Ticker mới chưa có ≥3 năm history | Hiện facts và coverage; chỉ gán nhãn/đánh giá khi các điều kiện eligibility, đặc trưng và nguồn đã chốt được đáp ứng; không suy dữ liệu thiếu. |
| Mã không thuộc tập được B-PIT hỗ trợ | Nếu không có nhãn B-PIT hợp lệ theo protocol, chỉ hiển thị dữ liệu A v4 đã xác minh để tham khảo; kết luận tổng hợp là **“Không đủ cơ sở đánh giá”** và nêu rõ nguyên nhân. Không thay bằng mô hình khác. |
| Ticker đổi tên/chuyển sàn hoặc delist          | Tra cứu danh tính lịch sử theo interval/security_id; nếu không đủ thì từ chối gán sai.         |

# 5. HỢP ĐỒNG INPUT VÀ NGỮ NGHĨA THỜI ĐIỂM ĐÁNH GIÁ

## 5.1. Input của người dùng và tham số do hệ thống tự xác định

| **TRƯỜNG** | **KIỂU / MẶC ĐỊNH ĐỀ XUẤT** | **QUY TẮC** |
|---|---|---|
| `ticker` | string, viết hoa, bắt buộc | Người dùng nhập mã; xác minh ký tự, định danh chứng khoán và tính hợp lệ tại `as_of`. |
| `lookback_years` | 5 hoặc 10; mặc định 10, tùy chọn hiển thị | Chỉ xác định khoảng dữ liệu lịch sử được vẽ/liệt kê tính ngược từ `as_of`; không thay ngày đánh giá, kết quả Assessment, nhãn A v4/B-PIT, rulebook hoặc tham số tính đặc trưng M2. Khoảng không đủ dữ liệu phải báo coverage thực tế. |
| `request_time` | datetime, tự ghi | Thời điểm thực tế gọi API; dùng để ghi log và kiểm soát đánh giá hiện tại. Không đồng nghĩa với `as_of` trong giai đoạn mô phỏng. |
| `as_of` | date, hệ thống tự chọn | Ngày đánh giá hiển thị. Bản demo dùng `2026-01-02` cố định từ cấu hình phát hành. Khi vận hành thực tế, lấy ngày theo múi giờ giao dịch từ `request_time`. |
| `evidence_cutoff_at` | datetime có múi giờ, có thể `null` | Trong chế độ đánh giá hiện tại, ghi mốc chốt bằng chứng của artifact. Bản demo dùng ngày cố định và nguồn đã pin, trường này có thể là `null`. |
| `required_price_session` | date, hệ thống tự xác định | Phiên giá đã hoàn tất gần nhất theo lịch. Bản demo dùng `2025-12-31`. |
| `assessment_context` | `SIMULATED_AS_OF` / `CURRENT_AS_OF`, cấu hình nội bộ | Phân biệt ngữ cảnh mô phỏng và đánh giá hiện tại; là metadata kết quả, không phải một lựa chọn của người dùng. |
| `peer_basis` | không là input công khai trong phiên bản đầu | Backend dùng chính sách tại mục 6.3: ưu tiên cùng A v4 và B-PIT; nếu dưới 3 mã hợp lệ cho đặc trưng đang xét, tài chính dùng cùng B-PIT, thị trường dùng cùng A v4. Ghi `peer_basis` **riêng cho từng đặc trưng** và số mã thực tế. |
| `revision` | token từ artifact catalog | Không trộn A v4/B-PIT/Indicators/Assessment không tương thích hoặc khác revision trong cùng response. |

**Quy ước lịch sử:** Chỉ có **5 hoặc 10 năm, mặc định 10 năm**, tính lùi từ `as_of` thay vì từ ngày mở website. **Một vùng biểu đồ duy nhất** cho phép chuyển giữa 18 đặc trưng của A v4/B-PIT hoặc nhóm có cùng đơn vị và tần suất; tài chính theo FY, thị trường theo phiên/snapshot đã kiểm chứng. Giá cổ phiếu có thể xem tại chức năng hiện hữu để tham khảo, không trở thành đặc trưng thứ 19. Nếu chọn 10 năm nhưng chỉ có 7 năm hợp lệ thì chỉ hiển thị 7 năm, nêu rõ phần thiếu; không tự điền số, nội suy hoặc dùng FY chưa khả dụng tại `as_of`. Chuyển đặc trưng hoặc 5/10 năm **chỉ đổi nội dung biểu đồ và bảng lịch sử**, không đổi `as_of`, nhãn A v4/B-PIT, rulebook, bằng chứng kết luận hay mức đề xuất.

## 5.2. Các mốc thời gian phải lưu tách biệt

- **`request_time`:** Ngày giờ người dùng thực sự truy cập hoặc gửi yêu cầu tới API, luôn ghi theo múi giờ xác định.
- **`as_of`:** Ngày đánh giá hiển thị. Bản `SIMULATED_AS_OF` dùng ngày **02/01/2026**. Bản `CURRENT_AS_OF` dùng ngày tại múi giờ giao dịch.
- **Mốc chốt và phiên giá:** Trong chế độ hiện tại, lưu `evidence_cutoff_at` có giờ và múi giờ. Dùng `request_time` và lịch sàn để xác định `required_price_session`. Giá thực dùng có `last_price_date` trùng phiên yêu cầu. Trước khi phiên đóng cửa, dùng phiên hoàn tất trước đó. Nếu phiên đã kết thúc mà giá mới chưa được kiểm chứng hoặc phát hành, trả trạng thái thiếu dữ liệu với lý do đang chờ giá phiên mới. `market_snapshot_date` theo nhịp tháng của A v4 và được hiển thị riêng với ngày giá.
- **Thời điểm tài chính:** FY, `published_date`, `usable_from_date` và cutoff B-PIT được lưu riêng; không coi ngày kết thúc FY là ngày báo cáo đã được biết.

**Mốc demo đã chốt:** `as_of=2026-01-02`, `required_price_session=2025-12-31`. Dùng giá và snapshot A v4 ngày 31/12/2025. B-PIT được chọn theo FY mới nhất khả dụng của từng mã tại `as_of`, theo mục 7.3. Ví dụ, ca FPT dùng FY2024. Bộ pin tài chính lấy từ bàn giao làm giàu ở mục 6.4. Ngày 02/01 là ngày nghỉ giao dịch. Demo chỉ cần ngày đánh giá, phiên giá và pin của các nguồn để khóa mốc. Giao diện ghi rõ đây là mô phỏng hồi cứu.

## 5.3. Quy tắc chọn dữ liệu và giới hạn mô phỏng

Bản mô phỏng đọc trực tiếp các nhãn và đặc trưng của mã tra cứu trong artifact A v4/B-PIT đã pin cho mốc ở mục 5.2. Khi đánh giá hiện tại, chọn dữ liệu được phép dùng tại mốc chốt bằng chứng và giá của phiên hoàn tất gần nhất. A v4 dùng snapshot mới nhất hợp lệ theo chu kỳ tháng. Ghi kỳ, ngày sử dụng và hạn phát hành kỳ tiếp theo theo lịch đã nghiệm thu. Khi kỳ bắt buộc đã đến hạn mà chưa có snapshot được kiểm chứng, chỉ hiển thị dữ liệu cũ để tham khảo. Lịch phát hành theo tháng cần có trước khi triển khai đánh giá hiện tại. Giá cập nhật theo phiên, còn đặc trưng A cập nhật theo snapshot tháng.

Mô phỏng cần phân biệt **dữ liệu thực sự có thể biết ở thời điểm lịch sử** với **artifact/mô hình được xây dựng hồi cứu về sau**. Chỉ tuyên bố tái lập quyết định có sẵn tại ngày lịch sử nếu đã kiểm chứng cả thời điểm dữ liệu và phương pháp/mô hình. Nếu chỉ đủ điều kiện nghiên cứu hồi cứu, hiển thị rõ giới hạn này, không khẳng định nhà đầu tư khi đó đã có mô hình hoặc nhãn tương ứng. Tuyệt đối không lấy FY2025 trước ngày công bố hoặc bất kỳ feature sử dụng thông tin tương lai.
A v4 và B-PIT có thể được xây dựng sau ngày mô phỏng. Với demo hồi cứu, kiểm soát phạm vi và thời điểm khả dụng của các đầu vào theo mốc đánh giá. Ngày build của mô hình được ghi riêng.

# 6. DỮ LIỆU, CHẤT LƯỢNG VÀ SO SÁNH THEO CỤM

## 6.1. Bản đồ dữ liệu đầu vào

| **NHÓM** | **FIELD / NGUỒN** | **RÀNG BUỘC** |
|---|---|---|
| Identity | `ticker`, `security_id`, exchange, status, effective interval | Không nối mã lịch sử bằng ticker hiện tại khi chưa xác minh identity. |
| **Market — A v4 (9)** | `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `downside_vol_63`, `mdd_126`, `beta_126`, `liquidity_21` | Lấy từ artifact/feature snapshot A v4 đúng phiên bản, ngày hợp lệ và price basis; không điền dữ liệu thiếu. |
| **Financial — B-PIT (9)** | `roe`, `roa`, `gross_margin`, `net_margin`, `debt_to_equity`, `current_ratio`, `asset_turnover`, `revenue_growth`, `cfo_to_ni` | Lấy đúng feature vector B-PIT đã xác minh theo FY, `usable_from_date`, cutoff, trạng thái và phạm vi áp dụng; không thay bằng bộ B mô tả. |
| Cluster | Nhãn A v4/B-PIT, snapshot/FY, model version, profile, centroid/transform | Chỉ đọc kết quả và thông tin phiên bản đã pin; không fit hoặc tính đặc trưng trong request. |
| PIT | `published_date`, `usable_from_date`, cutoff, nguồn xác nhận ngày khả dụng | Không sử dụng dữ liệu tương lai hoặc FY chưa khả dụng tại `as_of`. |
| QA | missing/status, conflict, coverage, hashes, data age | Fail-closed khi thiếu bằng chứng cốt lõi; phân biệt `NOT_APPLICABLE` và `MISSING_INPUT`. |

**Danh sách đóng (whitelist):** Chỉ **18 trường được nêu ở hai dòng Market/Financial** được sử dụng làm tín hiệu trực tiếp cho rulebook, bằng chứng kết luận và so sánh đặc trưng trong tab Đánh giá đầu tư. Các trường định danh, giá nguồn, ngày dữ liệu, metadata/model version và QA vẫn cần cho vận hành nhưng không phải đặc trưng đánh giá bổ sung. Các chỉ số khác trên website hiện hữu không được tự động đưa vào Assessment; các tab hiện tại vẫn giữ nguyên.

## 6.2. Kiểm tra chất lượng dữ liệu và thông tin hiển thị cùng biểu đồ

**Mục đích:** Bảo đảm nhà đầu tư hiểu chỉ số đang xem có dữ liệu đến thời điểm nào, có thiếu kỳ hay không và có đủ cơ sở để so sánh hay không. **Không xây dựng một màn hình/dashboard chất lượng dữ liệu riêng.** Những thông tin cần thiết xuất hiện ngay bên dưới **một biểu đồ chuyển đổi đặc trưng** đã chọn ở mục 11.2; chi tiết kỹ thuật đặt trong phần mở rộng “Nguồn và chất lượng dữ liệu”.

| **Thông tin trên giao diện** | **Cách hiển thị khi người dùng chọn một đặc trưng** |
|---|---|
| Chỉ số đang xem | Tên tiếng Việt, đơn vị đo, thuộc A v4 hay B-PIT; ví dụ ROE (%), `mom_126` (%). |
| Thời điểm dữ liệu | A v4: ngày snapshot và kỳ thị trường; B-PIT: năm tài chính và ngày báo cáo bắt đầu được sử dụng. Không gộp hai trục thời gian. |
| Số kỳ có dữ liệu | Ví dụ “7/10 năm” khi chọn 10 năm nhưng chỉ có 7 năm hợp lệ; báo các khoảng trống, không vẽ nối hoặc nội suy qua dữ liệu thiếu gây hiểu lầm. |
| Trạng thái dữ liệu | “Hợp lệ”, “Thiếu dữ liệu”, “Không áp dụng” hoặc “Chưa đủ cơ sở”; hiện giải thích bằng tiếng Việt, giữ mã kỹ thuật như `OK`, `MISSING_INPUT`, `NOT_APPLICABLE` khi mở chi tiết. |
| So sánh với Peers | Theo chính sách tại mục 6.3: nêu tập so sánh của **đặc trưng đang chọn** (cùng A+B, cùng B-PIT nếu tài chính, hoặc cùng A v4 nếu thị trường); chỉ hiện trung vị khi có **ít nhất 3 Peers hợp lệ**. Nếu dưới 3 thì không tính trung vị; ghi “Chưa đủ 3 mã để tính trung vị” và vẫn có thể hiển thị giá trị của từng Peer hiện có. |
| Nguồn và thời điểm đánh giá | Nêu `as_of`, ngày giá, ngày snapshot A hoặc FY/usable của B-PIT phù hợp với đặc trưng; cho mở thông tin nguồn/phiên bản khi cần. |

**Quy tắc tương tác (phương án 2):** Chuyển đặc trưng trong bộ chọn hoặc chuyển lịch sử **5/10 năm** chỉ cập nhật đường biểu đồ và phần giải thích chất lượng đi kèm; **không tính lại nhãn cụm hoặc thay đổi đề xuất đầu tư**. Một vùng biểu đồ có thể vẽ nhiều đường **chỉ khi cùng đơn vị, tần suất và trục thời gian**.

**Kiểm tra phía hệ thống:** Xác minh giá của phiên hoàn tất gần nhất, lịch snapshot A v4 theo tháng, FY/`usable_from_date`/cutoff của B-PIT, tình trạng thiếu dữ liệu, tính áp dụng của đặc trưng, phiên bản/hash và số Peers hợp lệ. Mã chứng cứ phải truy vết được đến dữ liệu đã kiểm chứng. Nếu thiếu dữ liệu cốt lõi, chặn kết luận theo rulebook thay vì chỉ hiển thị cảnh báo rồi tiếp tục đánh giá.

## 6.3. Chính sách chọn cổ phiếu tương đồng (Peers)

**Peers** là những cổ phiếu dùng để đối chiếu một đặc trưng cụ thể với mã đang tra cứu. Output chọn Peers dựa trên A v4 và B-PIT theo quy tắc dưới đây. Mỗi phép so sánh có tập Peers và số lượng hợp lệ riêng; không dùng danh sách của API `/peers` hiện hữu.

**Điều kiện đầu vào:** Mã đang tra cứu cần có cả nhãn **A v4 và B-PIT hợp lệ tại `as_of`** để chọn Peers và đánh giá kết hợp. Nếu không có B-PIT, **không lập danh sách Peers**, không âm thầm chuyển sang chính sách chỉ dựa vào A v4; vẫn có thể hiển thị các đặc trưng thị trường riêng của mã dưới dạng tham khảo, không lập thống kê Peers hoặc đưa ra kết luận đầu tư hai chiều.

**Cách chọn Peers cho từng đặc trưng:**

1. **Ưu tiên cùng cả hai cụm:** Tìm các mã có **cùng A v4 và cùng B-PIT** với mã tra cứu, cùng thời điểm/phiên bản có thể đối chiếu. Nếu có **từ 3 Peers hợp lệ cho đặc trưng đang xét**, sử dụng tập này và ghi `peer_basis=SAME_A_AND_B_PIT`.
2. **Nếu chưa đủ 3, mở rộng theo đúng loại đặc trưng:**
   - **9 đặc trưng tài chính B-PIT** (ví dụ ROE, ROA, D/E, CFO/NI): chọn **toàn bộ mã cùng B-PIT** hợp lệ; không bắt buộc cùng A v4. Ghi `peer_basis=SAME_B_PIT` nếu đạt tối thiểu 3 Peers hợp lệ.
   - **9 đặc trưng thị trường A v4** (ví dụ momentum, downside volatility, beta, thanh khoản): chọn **toàn bộ mã cùng A v4** hợp lệ; không bắt buộc cùng B-PIT. Ghi `peer_basis=SAME_A_V4` nếu đạt tối thiểu 3 Peers hợp lệ. Việc mở rộng thị trường theo A v4 **chỉ xảy ra khi mã đang tra cứu đã có đủ A v4 và B-PIT để thực hiện so sánh Peers**; không dùng riêng A v4 để chọn Peers khi thiếu B-PIT.
3. **Lọc dữ liệu theo từng đặc trưng:** Loại mã đang tra cứu, bản ghi trùng, định danh sai, giá trị `null`/`NOT_APPLICABLE`, dữ liệu chưa khả dụng tại `as_of` hoặc không tương thích về định nghĩa, đơn vị, kỳ, snapshot, kiểu báo cáo và nguồn. Số Peers hợp lệ của ROE có thể khác số Peers hợp lệ của `mom_126` hoặc CFO/NI.
4. **Chỉ so sánh khi đủ mẫu:** Với **ít nhất 3 Peers hợp lệ cho chính đặc trưng**, tính và hiển thị trung vị (cùng các thống kê phù hợp nếu có), trả `peer_basis`, `peer_count`, kỳ dữ liệu và nguồn theo từng đặc trưng. Nếu sau khi mở rộng vẫn chỉ có **0–2 Peers hợp lệ**, **không tính trung vị nhóm**: hiển thị giá trị của mã đang tra cứu và giá trị từng Peer có sẵn (nếu có), kèm thông báo **“Chưa đủ 3 mã tương đồng để tính trung vị”**. Không tự bổ sung mã không đạt điều kiện. **Không chia Peers thành nhóm nhỏ/nhóm lớn**; chỉ công khai số mã thực tế. Việc không đủ 3 Peers cho một đặc trưng **không tự động làm mất hiệu lực kết luận đầu tư** nếu các bằng chứng bắt buộc khác vẫn đáp ứng rulebook.

**Ví dụ minh họa (không phải dữ liệu thực tế của FPT):** Giả sử FPT thuộc A1 và B0. Trong tập A1+B0 chỉ có 2 Peers hợp lệ cho ROE → mở rộng sang toàn bộ B0 có 8 mã hợp lệ, so sánh ROE với 8 mã và ghi `SAME_B_PIT`. Với `mom_126`, nếu tập A1+B0 chỉ có 2 mã nhưng toàn bộ **A1** có 9 mã hợp lệ, so sánh momentum với 9 mã và ghi `SAME_A_V4`. Nếu CFO/NI chỉ có 2 mã hợp lệ trong B0 thì **không** tính trung vị CFO/NI; nếu có đúng 3 mã hợp lệ thì **được tính** trung vị.

**Giới hạn phương pháp:** Cùng cụm không bảo đảm mọi cổ phiếu có rủi ro hoặc triển vọng giống nhau. Chỉ so sánh các đặc trưng có cùng định nghĩa, kỳ dữ liệu và điều kiện áp dụng; thiếu Peers chỉ làm thiếu bằng chứng so sánh của đặc trưng tương ứng và **không tự động chặn kết luận đầu tư**; các điều kiện đánh giá khác vẫn phải đáp ứng rulebook đã kiểm chứng.

## 6.4. Đầu vào triển khai sau khi làm giàu B-PIT

**Quyết định nguồn ngày 15/11/2026:** Owner chốt Assessment dùng **B-PIT sau làm giàu và SQLite chỉ số dẫn xuất đi cùng**. Thành viên bắt đầu S1 sau **Giai đoạn F — Đối sánh và bàn giao** của [kế hoạch làm giàu dữ liệu B-PIT và backtest M3](KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md). Kế hoạch làm giàu giới hạn ở **FY2017–FY2024**. Các đường dẫn `<run_id>` dưới đây là đường dẫn đầu ra dự kiến. Điền run ID và SHA256 thực tế từ manifest khi nhận bàn giao.

| Đầu vào | File hoặc thông tin phải nhận | Assessment dùng để làm gì |
|---|---|---|
| Thị trường A v4 | `data/web/delta-intelligence-v4/terminal.sqlite` và `manifest.json` đi cùng | Đọc định danh theo phạm vi bundle, giá phiên 31/12/2025, nhãn/snapshot A v4 cùng ngày, 9 đặc trưng thị trường và dữ liệu lịch sử để hiển thị. Giai đoạn làm giàu tài chính dùng lại nguồn A v4 này. |
| Lịch phiên C8 v2 | `artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/trading_calendar.jsonl`, pin theo manifest ở Giai đoạn B | Đối chiếu phiên giá và lịch sử. Mốc demo 02/01/2026 và phiên giá 31/12/2025 lấy từ cấu hình đã chốt ở mục 5.2. |
| Chỉ số tài chính sau làm giàu — Giai đoạn C | `data/financial/indicators_enriched_v1/<run_id>/` gồm `indicators.sqlite`, `imputed_cells.csv`, `medians_by_year_metric.csv`, `imputation_summary.csv`, `manifest.json` | Đọc 9 chỉ số tài chính từ SQLite khớp pin đầu vào của B-PIT. Dùng hồ sơ từng ô để truy vết giá trị quan sát và giá trị điền trung vị. File báo cáo trung vị là bằng chứng của giai đoạn làm giàu, khác với trung vị Peers do Assessment tính theo mục 6.3. |
| B-PIT sau làm giàu — Giai đoạn D | `data/financial/b_pit_enriched_v1/<run_id>/` gồm `labels.csv`, `models.json`, `audit.json`, `manifest.json` | Đọc nhãn, FY, cutoff, profile và trạng thái kiểm chứng. Nhãn của mã tra cứu và Peers lấy từ `labels.csv` của run bàn giao. Một số mã có thể đổi nhãn khi B-PIT được fit lại. |
| Ngày khả dụng BCTC — Giai đoạn B, pin lại trong C/D | `data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv` theo hash mà manifest B-PIT và SQLite đã pin | Chọn FY mới nhất được phép dùng tại `as_of` và kiểm cutoff. Áp dụng mục 7.3 nếu FY mới nhất chưa có mô hình. Giai đoạn làm giàu giữ nguyên `usable_from_date`. |
| Biên bản bàn giao — Giai đoạn F | Kết quả đối sánh, trạng thái nghiệm thu, commit, đường dẫn tải có quyền truy cập, run ID và SHA256 của bộ làm giàu bàn giao cho Assessment | Khóa pin theo run đã bàn giao trước S1. Cấu hình và kết quả Development/Holdout là bằng chứng nghiệm thu thử nghiệm M3. Assessment builder và API không dùng NAV, giao dịch hay lợi suất của hai run để tính nhãn đầu tư. |

**Cách kiểm bộ đầu vào khi nhận bàn giao**

1. Pin **cùng một cặp** B-PIT làm giàu và SQLite chỉ số dẫn xuất đúng như manifest. Kiểm hash của nhãn, model, SQLite và availability. Áp dụng cùng phiên bản tài chính cho mã tra cứu, tất cả Peers và phần lịch sử xuất từ cặp nguồn đó.
2. Nếu chưa có đủ tệp bàn giao hoặc pin không khớp, ghi rõ tệp hay hash đang thiếu và dừng build Assessment đến khi đối chiếu xong. Bộ B-PIT và Indicators baseline phục vụ đối chứng M3. Assessment không tự chuyển sang baseline.
3. Giữ provenance của ô điền trung vị, chẳng hạn `IMPUTED_MEDIAN` theo artifact bàn giao. Điều kiện cho các ô đó tham gia rulebook, so sánh Peers hay chỉ hiển thị phải được ghi trong policy Assessment đã duyệt. Opt-in của loader thử nghiệm M3 không quyết định cách Product dùng các ô đó. Nếu một ô bắt buộc chưa được phép sử dụng, xử lý theo mục 8.3.
4. Ghi các pin đã chọn và nơi lấy dữ liệu vào cấu hình/manifest Assessment. Thành viên dùng tệp đã đối chiếu SHA256 hoặc tải đúng revision theo bàn giao. Giá C8 nén, VNINDEX và baseline M3 phục vụ giai đoạn đối chứng M3 theo kế hoạch làm giàu. Phạm vi demo Assessment dùng nguồn giá và snapshot A v4 đã pin ở bảng trên.

# 7. CHIẾN LƯỢC DÙNG MÔ HÌNH M2

## 7.1. Chu trình offline và online

**OFFLINE — chỉ khi xây dựng/cập nhật artifact:** thu thập/QA dữ liệu, tính features, fit hoặc áp dụng phiên bản mô hình theo protocol được duyệt, gán nhãn, tạo profiles, tính phần so sánh và assessment policy, verify, seal/publish.

**ONLINE — khi người dùng tra cứu một mã:** resolve ticker và truy vấn kết quả đã tính cho đúng mã, rồi trả JSON để giao diện hiển thị. Không crawl, không fit K-Means và không tính lại feature/model.

## 7.2. Ba trường hợp gán cụm

| **TÌNH HUỐNG**                                              | **XỬ LÝ ĐỀ XUẤT**                                                                                                                                       |
|-------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| Ticker đã có nhãn đúng as_of                                | Lấy nhãn, profile và version đã pin; hiển thị như kết quả quan sát.                                                                                     |
| Ticker có dữ liệu mới nhưng chưa có nhãn                    | Một job offline riêng có thể transform bằng tham số đã fit và nearest-centroid nếu policy/compatibility được duyệt; version mới phải ghi rõ infer-only. |
| Ticker thiếu lịch sử, không đủ features hoặc ngoài universe | Không suy nhãn; assessment trả NO_EVIDENCE/NOT_ELIGIBLE và cung cấp facts sẵn có.                                                                       |

## 7.3. Sử dụng B-PIT tại thời điểm đánh giá

Nhãn phân cụm tài chính chỉ được sử dụng khi chứng minh **dữ liệu báo cáo đã khả dụng tại ngày `as_of`**. B-PIT xử lý vấn đề thời điểm bằng `usable_from_date`, cutoff theo FY và phép gán nhãn dựa trên các tham số/tâm cụm đã cố định của M3; không coi ngày kết thúc FY là ngày nhà đầu tư đã biết kết quả.

**Lựa chọn đã thống nhất:** Output chỉ sử dụng **A v4 + B-PIT** tại `as_of`, không có đường dữ liệu phân cụm khác hoặc fallback sang nhãn từ API website hiện hữu. Lý do: A v4 cung cấp bối cảnh thị trường, B-PIT kiểm soát thời điểm khả dụng của tài chính; kết hợp giúp hạn chế sai lệch dùng dữ liệu tương lai.

**Quy trình chọn dữ liệu B-PIT:**

- Xác định `as_of` theo cấu hình giai đoạn đánh giá tại mục 5; chỉ đọc dữ liệu có ngày khả dụng không muộn hơn `as_of` (không mặc định lấy ngày truy cập khi đang mô phỏng).
- Chọn FY mới nhất đã khả dụng của doanh nghiệp; kiểm tra cutoff của mô hình B-PIT tương ứng đã đến và model/artifact đã được xác thực.
- Nếu FY mới nhất đã khả dụng nhưng mô hình tương ứng chưa sẵn sàng, không tự lùi về mô hình năm cũ để tạo một kết luận có vẻ hợp lệ; ghi lý do không đủ cơ sở. Quy tắc này phù hợp cách kiểm soát runtime M3 đã ghi trong `docs/DECISIONS.md`.
- Kiểm tra quy tắc hết hiệu lực của dữ liệu tài chính (mốc 18 tháng trong M3), trạng thái chỉ số, kiểu báo cáo tài chính và điều kiện áp dụng của B-PIT trước khi dùng cho Assessment.
- Nếu mã không có B-PIT hợp lệ, nêu rõ lý do và trả `INSUFFICIENT_EVIDENCE` cho đánh giá kết hợp.

**Ranh giới triển khai:** Assessment đọc cặp B-PIT làm giàu và SQLite chỉ số dẫn xuất được bàn giao theo mục 6.4. Artifact, cutoff, nhãn và dữ liệu nguồn đã seal được giữ nguyên. Kết quả làm giàu FY2017–FY2024 không bổ sung model FY2025. Việc mở rộng sang FY mới thuộc một thay đổi riêng.

## 7.4. Không suy “cụm 0 = mạnh”

Nhãn phân cụm chỉ là định danh, không phải xếp hạng đầu tư. Với **A v4**, nhận diện đặc trưng thị trường dựa trên profile đã xác minh; với **B-PIT**, tham chiếu thứ tự nhóm theo median ROE giảm và D/E tie-break của ADR D-M3-01 khi đúng phiên bản/phạm vi. Thứ tự này chỉ là đặc trưng tài chính tương đối, không bảo đảm lợi suất; mỗi kết luận vẫn cần chỉ số mã riêng, dữ liệu hợp lệ và cờ chất lượng cụm.

# 8. CHÍNH SÁCH ĐỀ XUẤT ĐẦU TƯ OUTPUT — TẠI THỜI ĐIỂM TRA CỨU

## 8.1. Cấu trúc đánh giá theo bộ quy tắc D-ASS-01

**D-ASS-01** là bộ quy tắc đánh giá và đề xuất đầu tư của DELTA. Bản demo dùng kết quả A v4/B-PIT đã pin và **18 đặc trưng ở mục 6.1**. Bảng ở mục 8.3 chốt logic bản đầu để thành viên triển khai và kiểm thử. Kết quả dùng một mốc `as_of`, theo các điều kiện dữ liệu tại G1.

| **LỚP**                     | **CÂU HỎI**                                                      | **OUTPUT THÀNH PHẦN**                                                   |
|-----------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------|
| G1. Eligibility & freshness | Có đủ dữ liệu hợp lệ và mới để đưa ra nhận định không?           | PASS / HISTORICAL_ONLY / NOT_READY / DATA_MISSING                       |
| G2. Financial health | 9 đặc trưng B-PIT (sinh lời, biên lợi nhuận, đòn bẩy, thanh toán, hiệu quả, tăng trưởng, dòng tiền) cho thấy điều gì? | Favorable / Mixed / Caution / Unknown + bằng chứng từ B-PIT |
| G3. Market condition | 9 đặc trưng A v4 (động lượng, biến động, downside risk, MDD, beta, thanh khoản) cho thấy điều gì? | Favorable / Mixed / Caution / Unknown + bằng chứng từ A v4 |
| G4. Relative position | Theo chính sách tại mục 6.3, đặc trưng tài chính/thị trường của mã cao hay thấp hơn nhóm so sánh phù hợp? | Trung vị/IQR, vị trí tương đối, `peer_basis` và `peer_count` **theo từng đặc trưng**; tài chính mở rộng cùng B-PIT, thị trường mở rộng cùng A v4 khi cần. |
| G5. Risk & evidence consistency | Có xung đột, rủi ro, tín hiệu bất lợi hoặc bằng chứng chưa vững giữa A v4 và B-PIT không? | Cờ rủi ro, bằng chứng trái chiều và điều kiện chặn từ 18 đặc trưng, không suy định giá nội tại. |
| G6. Conclusion              | Tín hiệu đồng thuận, trái chiều hay thiếu cơ sở?                 | Đáng cân nhắc đầu tư / Cần theo dõi / Chưa nên ưu tiên / Không đủ cơ sở |
**Vai trò của Peers trong G4**

| Vai trò | Ý nghĩa trong bản demo |
|---|---|
| So sánh | Cho biết giá trị của từng chỉ số cao hơn, thấp hơn hay bằng trung vị Peers khi có đủ mẫu hợp lệ. |
| Giải thích | Cho thấy điểm mạnh, điểm yếu tương đối của cổ phiếu theo từng chỉ số có thể đối chiếu. |
| Bổ sung bằng chứng | Đưa phép so sánh vào phần lý do cùng đặc trưng A v4/B-PIT và cảnh báo rủi ro. Bảng quyết định dùng bằng chứng của mã để xác định nhãn. |

Luôn áp dụng cách chọn và kiểm tra tương thích tại mục 6.3. Với dưới 3 Peers hợp lệ cho chỉ số, hiển thị “Chưa đủ đối chứng”. Kết quả so sánh và sự thiếu Peers không làm đổi nhãn demo. Ví dụ, một mã có thể cao hơn trung vị ROE và vẫn nhận nhãn “Cần theo dõi” theo bảng quyết định.

## 8.2. Ma trận diễn giải tín hiệu — không thay thế rulebook chi tiết

| **A (THỊ TRƯỜNG)** | **B (TÀI CHÍNH)**     | **TÓM TẮT ĐƯỢC PHÉP NÓI**                                                          |
|--------------------|-----------------------|------------------------------------------------------------------------------------|
| Thuận lợi          | Thuận lợi             | Hai chiều tương đối thuận lợi; vẫn phải kiểm tra rủi ro, thanh khoản, tín hiệu trái chiều và tính hợp lệ dữ liệu theo rulebook. |
| Thuận lợi          | Bất lợi               | Giá/hành vi thị trường mạnh nhưng nền tảng tài chính yếu; thận trọng với xung đột. |
| Bất lợi            | Thuận lợi             | Doanh nghiệp có điểm tài chính tốt, nhưng xu hướng thị trường chưa hỗ trợ.         |
| Bất lợi            | Bất lợi               | Các chiều tín hiệu đều kém; ưu tiên cảnh báo rủi ro/thiếu bằng chứng tích cực.     |
| Bất kỳ             | Không có B-PIT hợp lệ | Không xuất nhận định đầu tư chính thức nếu policy yêu cầu đủ hai chiều.            |

## 8.3. Bốn trạng thái đầu ra đã chọn

| **STATUS CODE**       | **NHÃN HIỂN THỊ**       | **QUY TẮC ĐIỀU KIỆN**                                                                                                                  |
|-----------------------|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| RESEARCH_FAVORABLE | Đáng cân nhắc đầu tư | Xu hướng và tài chính đều thuận lợi, đủ dữ liệu bắt buộc và không có cảnh báo. |
| WATCH | Cần theo dõi | Các trường hợp đủ dữ liệu còn lại, gồm tín hiệu trái chiều, dòng tiền bằng 0 và cảnh báo theo dõi. |
| CAUTION | Chưa nên ưu tiên đầu tư | Có cảnh báo trọng yếu, hoặc cả xu hướng thị trường và sinh lời đều bất lợi. |
| INSUFFICIENT_EVIDENCE | Không đủ cơ sở đánh giá | Thiếu hoặc không xác minh được dữ liệu bắt buộc tại `as_of`. |
**Điều kiện đầu vào và vai trò của 18 đặc trưng**

- **Bắt buộc:** nhãn A v4 và B-PIT hợp lệ, giá đúng phiên yêu cầu, cờ thanh khoản của A v4, bốn đặc trưng momentum, `roa` và `net_margin`. `cfo_to_ni` bắt buộc khi lợi nhuận làm mẫu số của tỷ lệ là dương. Lấy trạng thái hợp lệ và dấu của mẫu số từ bằng chứng nguồn đã pin. Chỉ dùng dấu của `cfo_to_ni` để đọc dấu dòng tiền khi mẫu số dương và tỷ lệ hợp lệ.
- **Bổ sung:** 18 đặc trưng là danh sách được phép dùng và có vai trò như bảng dưới. Với đặc trưng ngoài nhóm bắt buộc, nếu dữ liệu thiếu hoặc không áp dụng thì ghi rõ trạng thái và bỏ qua phép kiểm tương ứng. Một so sánh thiếu bằng chứng không được hiển thị như giá trị bằng 0.

| Nhóm | Cách đánh giá tại mốc demo |
|---|---|
| Xu hướng | Thuận lợi khi `mom_63 > 0` và `mom_126 > 0`, đồng thời `mom_21 > 0` hoặc `mom_252 > 0`. Bất lợi khi điều kiện đối xứng theo chiều âm đúng. Các tổ hợp còn lại là chưa đồng thuận. |
| Sinh lời và dòng tiền | Tài chính thuận lợi khi `roa > 0`, `net_margin > 0` và dòng tiền kinh doanh dương theo `cfo_to_ni` hợp lệ. Sinh lời bất lợi khi cả `roa` và `net_margin` âm. Dòng tiền bằng 0 chưa đủ để kết luận tài chính thuận lợi. |
| Cảnh báo trọng yếu | Cờ `ILLIQUID` của A v4, hoặc lợi nhuận dương nhưng dòng tiền kinh doanh âm. |
| Cảnh báo theo dõi | **Chỉ cần một** dấu hiệu hợp lệ: `gross_margin < 0`, `current_ratio < 1` hoặc `revenue_growth < 0`. Ba dấu hiệu lần lượt là biên gộp âm, tài sản ngắn hạn thấp hơn nợ ngắn hạn và doanh thu giảm. |
| Bằng chứng giải thích | `vol_63`, `downside_vol_63`, `mdd_126`, `beta_126`, `liquidity_21`, `roe`, `debt_to_equity` và `asset_turnover` cung cấp bối cảnh. Vai trò của Peers theo G4. |

**Thứ tự áp dụng** là `INSUFFICIENT_EVIDENCE` → `CAUTION` → `RESEARCH_FAVORABLE` → `WATCH`. Dừng ở nhãn đầu tiên thỏa điều kiện. Khi một mã có xu hướng và tài chính thuận lợi, chỉ cần một cảnh báo theo dõi để trả `WATCH`. Nếu đồng thời có cảnh báo trọng yếu thì `CAUTION` được ưu tiên. Demo áp dụng bảng này trên dữ liệu tại mốc 02/01/2026. Lịch sử được trình bày để đối chiếu khi người dùng cần.

## 8.4. Nguyên tắc đánh giá và độ tin cậy của bằng chứng

**Kết luận đầu tư và độ tin cậy là hai thông tin khác nhau.**

- **Kết luận đánh giá:** Một trong bốn trạng thái tại mục 8.3, được xác định bằng điều kiện logic đã duyệt trên nhãn A v4/B-PIT và 18 đặc trưng; phản ánh mức độ đáng cân nhắc theo bằng chứng tại `as_of`, **không dự báo xác suất tăng giá**.
- **Độ tin cậy của bằng chứng:** Cho biết nguồn có đủ, đúng thời điểm, đúng phiên bản và truy vết được hay không; phản ánh chất lượng dữ liệu và mức độ hỗ trợ của các phép so sánh, **không phải xác suất cổ phiếu sinh lời**. Trước mắt có thể hiển thị trạng thái và lý do bằng chữ (ví dụ “Đủ dữ liệu”, “Thiếu đối chứng”, “Dữ liệu chỉ để tham khảo”), không tự tạo một tỷ lệ phần trăm confidence nếu chưa có phương pháp chuẩn hóa.
- **Không xây điểm tổng hợp 0–100:** Không cộng số đặc trưng “tốt” rồi chia 18, vì các biến có thể trùng lặp thông tin (ví dụ `mom_63` với `mom_126`, ROE với ROA). Quy tắc phải chỉ rõ khi nào các chiều tài chính/thị trường đồng thuận, mâu thuẫn, hoặc có cảnh báo chặn; phải được kiểm thử trước khi sử dụng để ra kết luận.

**Ví dụ:** Nếu một mã có dữ liệu A v4/B-PIT đầy đủ, kiểm tra chất lượng có thể đạt nhưng thị trường và tài chính vẫn cho tín hiệu trái chiều; khi đó kết luận có thể là “Cần theo dõi” theo rulebook. Ngược lại, nếu thiếu B-PIT hợp lệ thì phải trả “Không đủ cơ sở”, dù momentum tích cực. **Dữ liệu đầy đủ không đồng nghĩa cổ phiếu chắc chắn tăng giá.**

## 8.5. Cách chứng minh rule

- Chạy replay từng as_of trên data lịch sử, không dùng data publish sau as_of.

- Đo độ ổn định kết luận theo thay đổi snapshot, peer cohort, xung đột chỉ số và cohort size.

- Nếu muốn kiểm chứng khả năng dự báo đầu tư bằng returns sau thời điểm t, đó là nghiên cứu dự báo mới với train/dev/holdout riêng; không tận dụng M3 holdout đã xem kết quả để tùy ý chọn rule.

- Không chọn k/cluster bằng Sharpe/ROI/return; giữ độc lập cluster quality và portfolio performance theo AGENTS.md.

- Hiện thực và kiểm chứng bảng quyết định mục 8.3 trước khi phát hành. Thử các ca đủ và thiếu dữ liệu, hai mặt trái chiều, giá trị bằng ngưỡng, nhiều cảnh báo cùng xuất hiện và cụm chất lượng thấp.

# 9. KIẾN TRÚC KỸ THUẬT ĐỀ XUẤT

## 9.1. Kiến trúc end-to-end

> Nguồn market + financial + disclosure dates + security identity
>
> ↓ Offline ingestion & QA (hiện có; mở rộng nếu cần)
>
> 9 đặc trưng từ bundle A v4 + 9 đặc trưng từ SQLite chỉ số đúng pin B-PIT làm giàu, cùng nhãn, profile, availability và provenance theo mục 6.4
>
> ↓ Offline assessment builder (rule engine đã duyệt, no fit/no crawl)
>
> data/product/assessment_v1/\<run_id\>/{manifest,assessments,peers,coverage,verification}
>
> ↓ Read-only adapter + FastAPI /api/v2/stocks/{ticker}/assessment
>
> Next.js /stocks?ticker=FPT&tab=assessment → dashboard giải thích

## 9.2. Vị trí file đề xuất (CHƯA tạo trong repo)

| **ĐƯỜNG DẪN DỰ KIẾN**                                | **VAI TRÒ**                                                                             |
|------------------------------------------------------|-----------------------------------------------------------------------------------------|
| configs/product/assessment_policy_v1.json            | Ngưỡng/eligibility/peer basis/nhãn/status; ghi policy version và quyết định owner.      |
| src/delta_t1/experiments/investment_assessment_v1.py | Orchestrator, deterministic rule evaluation từ input artifacts pinned, không fit model. |
| scripts/build_investment_assessment_v1.py            | CLI build offline; xuất run mới, manifest, coverage và summary QA.                      |
| scripts/verify_investment_assessment_v1.py           | Verifier độc lập: checksum, as-of validity, reproducibility, no future leakage.         |
| src/delta_t1/product/assessment_repository.py        | Chỉ đọc artifact đã phát hành để phục vụ product.                                       |
| web/backend/app/assessment.py                        | Validation + read-only response mapper; không crawl/fit.                                |
| web/backend/app/main.py                              | Khai báo route mới dưới /api/v2, middleware revision hiện có.                           |
| web/backend/app/schemas.py                           | Response schema Pydantic có status, evidence, provenance.                               |
| web/frontend/components/stock/assessment-panel.tsx   | Màn hình kết luận, card cụm, chỉ số, peers, nguồn và cảnh báo.                          |
| web/frontend/app/stocks/page.tsx                     | Thêm tab thứ 5 “Đánh giá đầu tư” và trạng thái URL.                                     |
| web/frontend/lib/types.ts                            | Types cho assessment response, enum states.                                             |
| tests/unit/...; tests/integration/...                | Bộ tests offline builder, API, policy, UI và bất biến research.                         |

Các đường dẫn trên là thiết kế dự kiến; việc triển khai cần tuân thủ D-ASS-01 và các bước kiểm thử. Không sửa artifact M3 đã seal hoặc thay đổi hợp đồng endpoint `/overview` hiện có.

## 9.3. Artifact contract đề xuất

| **FILE**            | **CHỨC NĂNG**                                                                  | **TÍNH CHẤT**                                             |
|---------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------|
| manifest.json | Ghi `run_id`, `as_of`, `required_price_session`, `evidence_cutoff_at` (nếu áp dụng), `assessment_context`, whitelist 18 đặc trưng, `generated_at` và trạng thái. Pin A v4, B-PIT, SQLite chỉ số đi cùng, availability và policy theo mục 6.4. | Immutable, SHA256, reference run sources. |
| assessments.jsonl | Mỗi ticker × `as_of` × policy → nhãn + evidence/status chỉ từ 18 đặc trưng. | Deterministic; không chấp nhận `driver` ngoài whitelist hay nhận định không có nguồn. |
| peer_benchmarks.csv | Trung vị/IQR/count cho **18 đặc trưng theo chính sách tại mục 6.3**: ưu tiên giao A v4+B-PIT; nếu thiếu mẫu, tài chính mở rộng cùng B-PIT, thị trường mở rộng cùng A v4. | Lưu `peer_basis`, `peer_count` **cho từng đặc trưng**, FY/snapshot, nguồn và phiên bản; không trộn kỳ/đơn vị khác nhau. |
| coverage.csv | Coverage theo ticker, kỳ dữ liệu, market/financial/cluster/peer. | Công khai missing, null và số Peers hợp lệ theo metric. |
| feature_history.jsonl | Chuỗi quan sát lịch sử đã xác minh của 18 đặc trưng theo ticker, ngày/snapshot hoặc FY, `usable_from_date`, status và nguồn. | Chỉ phục vụ **một biểu đồ có bộ chọn chỉ số**; đọc artifact đã kiểm chứng, không tính lại đặc trưng khi nhận request. |
| verification.json | Independent QA summary, PIT tests, đối chiếu whitelist 18 trường, status. | PASS/FAIL/PARTIAL với chứng cứ; không tự nâng trạng thái. |

# 10. THIẾT KẾ API READ-ONLY

## 10.1. Endpoint mới đề xuất

**GET /api/v2/stocks/{ticker}/assessment?lookback_years=10&revision=...**

Endpoint chỉ đọc artifact Assessment đã phát hành; backend ghi `request_time` và xác định `as_of` theo cấu hình phát hành. Ở giai đoạn đầu, `as_of` là ngày mô phỏng cố định `2026-01-02` theo mục 5.2 và gắn `assessment_context=SIMULATED_AS_OF`. Khi hệ thống được chuyển sang đánh giá hiện tại, `as_of`, `required_price_session` và `evidence_cutoff_at` được xử lý theo mục 5.2 và gắn `CURRENT_AS_OF`. Hai ngữ cảnh sử dụng cùng rulebook và schema. Giao diện không có nút chọn chế độ/ngày giả lập; API công khai không cho người dùng ghi đè `as_of` (replay lịch sử chỉ dùng giao diện nội bộ kiểm thử nếu được duyệt). Backend chỉ lấy đánh giá có đúng `as_of`, phiên giá yêu cầu, context và revision; không lấy kết quả mô phỏng để trả thành đề xuất đầu tư hôm nay. `lookback_years` chỉ nhận **5 hoặc 10** (mặc định 10); giá trị 20 hoặc giá trị khác trả HTTP 422, không được đổi kết luận theo tham số này.

## 10.2. Response schema logic (không phải số liệu FPT thật)

| **FIELD**                          | **Ý NGHĨA / VÍ DỤ AN TOÀN**                                                                                                               |
|------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| ticker / request_time / as_of      | Ticker do người dùng nhập; `request_time` là lúc gọi API; `as_of` là ngày thực sự được đánh giá và có thể là ngày giả lập. |
| `evidence_cutoff_at` / `required_price_session` | Mốc chốt có múi giờ khi đánh giá hiện tại và phiên giá yêu cầu. Bản demo có `evidence_cutoff_at=null` và `required_price_session=2025-12-31`. |
| assessment_context                   | `SIMULATED_AS_OF` / `CURRENT_AS_OF`; metadata từ cấu hình phát hành, không phải input UI. |
| effective_evidence_dates           | Ngày giá của phiên đã hoàn tất gần nhất, ngày/kỳ snapshot A v4, FY/`usable_from_date` B-PIT tách riêng; kèm cờ thiếu kỳ cập nhật A khi có.                                                              |
| availability_status                | READY \| HISTORICAL_ONLY \| STALE \| NOT_ELIGIBLE \| NOT_FOUND \| DATA_MISSING                                                            |
| assessment_status                  | RESEARCH_FAVORABLE (Đáng cân nhắc) \| WATCH (Theo dõi) \| CAUTION (Chưa ưu tiên) \| INSUFFICIENT_EVIDENCE (Không đủ cơ sở)                |
| market_cluster / financial_cluster | `market_cluster` **chỉ từ A v4**; `financial_cluster` **chỉ từ B-PIT**; mỗi nguồn gồm `{id, model_version, date_or_fy, profile, quality_flags, source_revision}` hoặc `null`. Nhãn A phải kèm kỳ snapshot và trạng thái chu kỳ cập nhật; chỉ nhận nhãn từ các artifact đã pin.                                                                        |
| drivers / risks / counter_evidence | Tín hiệu quyết định chỉ tham chiếu một trong **18 đặc trưng** được phép, kèm `value`, `status`, `unit`, kỳ dữ liệu, `peer_median` (nếu đủ mẫu), `evidence_ref` và chiều tác động. |
| feature_history | Chuỗi quan sát đã xác minh cho bộ chọn **một biểu đồ**, chỉ thuộc 18 đặc trưng; gồm feature_id, mốc thời gian, giá trị, đơn vị, status, provenance và coverage; lọc theo `lookback_years`. Chỉ là dữ liệu trình bày, không tham gia tính lại verdict. |
| peer_method / peer_count | Chính sách chọn Peers tại mục 6.3 và số Peers hợp lệ **theo từng đặc trưng** tại `as_of`; cho biết tập đã dùng: `SAME_A_AND_B_PIT`, `SAME_B_PIT` hoặc `SAME_A_V4`. |
| confidence / coverage              | Số liệu độ phủ + hạn chế; không biến confidence thành xác suất tăng giá.                                                                  |
| references                         | Input file hash, manifest, model pins, assessment_policy_version.                                                                         |
| scope                              | `AS_OF_ASSESSMENT_ONLY`; chỉ đánh giá tại ngày `as_of`, không có giá mục tiêu, lợi suất kỳ vọng hoặc thời hạn dự báo. |

## 10.3. Quy tắc HTTP/compatibility

- HTTP `200` với mã có thật khi dịch vụ đã có artifact phát hành. Nếu riêng mã đó thiếu dữ liệu cần thiết, trả `assessment_status=INSUFFICIENT_EVIDENCE` kèm lý do. Mã không tồn tại trả `404`. Revision không khớp trả `409`. Tham số không hợp lệ trả `422`. Nếu dịch vụ chưa có artifact phát hành, trả `503`.

- Stock Overview/Fundamentals/Scores/Peers hiện có vẫn hoạt động, không thay meaning của trường cũ.

- Hiển thị explicit empty states cho ticker có trong universe nhưng không có assessment hợp lệ.

- Không phản hồi text tự do mà thiếu evidence_ref; `drivers`/`risks` và thống kê Peers không được viện dẫn metric ngoài whitelist 18 trường. `feature_history` có thể thiếu kỳ nhưng không được sinh giá trị giả; tránh đưa citation tuyệt đối đến dữ liệu nội bộ nhạy cảm.

- Cache key gồm ticker + `assessment_context` + `as_of` + `required_price_session` + `evidence_cutoff_at` (nếu áp dụng) + lookback + policy_revision + bundle_revision; invalidate khi thay cấu hình ngày đánh giá, model, dữ liệu hoặc rule. Không tái dùng cache mô phỏng như đánh giá hiện tại.
- Dùng `request_time` để chọn phiên yêu cầu và ghi thời gian gọi API cho từng request. Khi đọc artifact hiện tại, `evidence_cutoff_at` của artifact phải không muộn hơn `request_time`. Cache nội dung đánh giá và ghi riêng metadata của request.

- Kiểm tra chống path traversal, SQL injection, oversized ticker, bogus dates, stale source và mismatch manifest.

# 11. ĐỀ XUẤT TÍCH HỢP WEBSITE

## 11.1. Vị trí trải nghiệm người dùng

Phương án ưu tiên: tích hợp trực tiếp vào trang “Tra cứu cổ phiếu” đã có. Người dùng tìm FPT → /stocks?ticker=FPT&tab=assessment; backend xác định `as_of` theo cấu hình phát hành. Giai đoạn đầu hiển thị ngày giả lập 02/01/2026, không để người dùng hiểu là nhận định tại ngày truy cập. Khi chuyển sang dữ liệu cập nhật, hệ thống dùng ngày truy cập thực tế. Menu trái giữ nguyên 6 mục; không thêm nút chọn chế độ/ngày giả lập hoặc trang dự báo.

| **HIỆN TẠI**              | **BỔ SUNG**                                                                      |
|---------------------------|----------------------------------------------------------------------------------|
| Tab 1 — Tổng quan         | Giữ nguyên.                                                                      |
| Tab 2 — Chỉ số tài chính  | Giữ nguyên, link từ reasoning.                                                   |
| Tab 3 — Điểm sức khỏe     | Giữ nguyên, link từ reasoning.                                                   |
| Tab 4 — So sánh cùng nhóm | Giữ nguyên hoặc gắn bộ lọc peers do assessment nêu rõ; không âm thầm sửa policy. |
| Tab 5 — Đánh giá đầu tư   | Mới: kết luận có điều kiện, bằng chứng, cờ dữ liệu và mô hình; preview/warnings. |

## 11.2. Wireframe nội dung trang mới

| **KHỐI UI**        | **NỘI DUNG CHÍNH**                                                                                               | **NGUYÊN TẮC HIỂN THỊ**                                                        |
|--------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| Header             | FPT \| ngày truy cập \| ngày đánh giá `as_of` \| ngày dữ liệu \| lịch sử 5/10 năm; nếu mô phỏng phải có chữ “Mô phỏng tại ngày ...”. | Không gộp ngày truy cập, `as_of` và ngày chứng cứ. |
| Decision summary   | Đề xuất tại `as_of` (đáng cân nhắc / theo dõi / chưa ưu tiên / không đủ cơ sở) + 1–2 câu lý do + giới hạn sử dụng. | Khi mô phỏng, không viết “đề xuất hiện tại”; không trưng bày lệnh “MUA”. |
| Dual-cluster cards | **A v4**: tên/đặc trưng + snapshot thị trường; **B-PIT**: tên/đặc trưng + FY, cutoff và ngày dữ liệu khả dụng.                                                          | Hiển thị bản chất nhóm, cỡ nhóm và stability cờ.                               |
| Evidence drivers   | Tín hiệu thuận, bất lợi, chưa rõ; từng metric dẫn đến bảng gốc.                                                  | Không bỏ qua tín hiệu trái chiều.                                              |
| Peer comparison | So sánh theo **chính sách tại mục 6.3**, ưu tiên cùng A v4+B-PIT; thiếu mẫu thì đặc trưng tài chính mở rộng cùng B-PIT, đặc trưng thị trường mở rộng cùng A v4. | Cho thấy nhóm so sánh, `peer_count`, trung vị và kỳ/phiên bản **của từng đặc trưng**. |
| **Biểu đồ lịch sử chuyển đổi chỉ số** | **Chỉ một vùng biểu đồ** với bộ chọn trong 18 đặc trưng A v4/B-PIT; có thể chọn nhóm cùng đơn vị như ROE/ROA, gross/net margin, volatility/downside volatility. Chọn lịch sử 5/10 năm (mặc định 10). | Tại một thời điểm chỉ render **một biểu đồ**; trục thị trường theo phiên/snapshot, tài chính theo FY; không ghép khác đơn vị hoặc khác trục kỳ. Chỉ vẽ điểm quan sát đã khả dụng tại `as_of`, giữ khoảng trống, không dự báo hoặc đổi verdict khi chuyển chỉ số/lookback. |
| **Bảng chi tiết 18 đặc trưng** | Danh sách 9 trường A v4 + 9 trường B-PIT, giá trị kỳ hợp lệ, đơn vị, status, đối chiếu trung vị Peers khi đủ 3 mã và link nguồn. | Có thể mở rộng/thu gọn; chỉ trình bày 18 đặc trưng trong phạm vi Assessment. |
| Thông tin dữ liệu của biểu đồ | Chỉ số đang chọn, đơn vị, mốc thời gian, số kỳ hợp lệ trong 5/10 năm, tình trạng dữ liệu và số Peers đủ mẫu. | Gắn ngay với **một biểu đồ** theo mục 6.2; thông tin kỹ thuật mở trong “Nguồn và chất lượng dữ liệu”, không tạo dashboard QA riêng. |

**Phương án UI đã chọn — một biểu đồ chuyển đổi chỉ số (phương án 2):** Mặc định hiển thị một đặc trưng/nhóm dễ hiểu (ví dụ ROE/ROA); dùng dropdown để đổi sang bất kỳ đặc trưng nào trong 18 trường, và dùng bộ chọn 5/10 năm cho khoảng lịch sử. Những đường vẽ chung phải có **cùng đơn vị, cách tính, tần suất và trục thời gian**; nếu không tương thích, tách thành lựa chọn riêng trong **cùng vùng biểu đồ**, không mở nhiều biểu đồ song song. Bên dưới là bảng chi tiết 18 đặc trưng và thông tin Peers/nguồn. Với mọi điểm hiển thị phải ghi kỳ/phiên, status, basis, coverage và ngày khả dụng không muộn hơn `as_of`; không đủ 10 năm thì chỉ hiển thị dữ liệu thực có. Giá lịch sử nếu cần xem chỉ là bối cảnh qua tab hiện hữu, không tham gia bộ 18 tín hiệu của Assessment.

**Ranh giới với website hiện hữu:** Tab “Đánh giá đầu tư” chỉ trình bày **A v4** và **B-PIT**. Giữ nguyên các tab và API hiện hữu. Nếu thiếu artifact B-PIT hợp lệ tại `as_of`, Output hiển thị lý do thiếu bằng chứng.

## 11.3. Ba trạng thái giao diện bắt buộc theo độ hợp lệ dữ liệu

- READY: Có dữ liệu và nhãn **A v4 + B-PIT** hợp lệ tại `as_of`, rule đã duyệt; cho hiển thị một trong ba mức nhận định chính. Nếu `assessment_context=SIMULATED_AS_OF`, kết quả READY vẫn là **đánh giá tại ngày mô phỏng**, không phải hiện tại.

- HISTORICAL_ONLY / STALE: Giá không phải của phiên đã hoàn tất gần nhất tại `as_of`, hoặc A v4 thiếu snapshot tháng **đã đến hạn theo lịch được duyệt**, hoặc nguồn B-PIT hết hiệu lực; chỉ hiển thị tham khảo, không đưa kết luận cho ngày đó. Không đánh dấu snapshot A là STALE chỉ vì khoảng cách 23 phiên. Kết quả mô phỏng hợp lệ không bị đánh dấu STALE chỉ do `request_time` muộn hơn.

- UNAVAILABLE / INSUFFICIENT: Không có dữ liệu/model/rule hợp lệ; hiện rõ nguyên nhân, ngày có dữ liệu cuối cùng và đường dẫn tới chỉ số đang có; không tạo verdict giả.

## 11.4. Giữ đồng bộ UX với website

- Tái sử dụng Shell, WorkspaceTabs, TickerFinder, Panel, StockCards, Chart, InfoTip, ErrorState, Skeleton và chế độ dark/light.

- Đồng bộ URL query khi đổi ticker, **đặc trưng đang xem trên biểu đồ**, khoảng lịch sử và tab; `as_of`/context do backend xác định từ bản phát hành. Bộ chọn chỉ chấp nhận field thuộc 18 đặc trưng, không làm thay đổi kết luận đầu tư. Back/Forward phải phục hồi mã được chọn nhưng không dùng kết quả hay ngữ cảnh đã hết hiệu lực.

- Giữ cache/revision protection hiện có, nhưng không giữ kết quả FPT khi chuyển sang ticker khác.

- Không thêm biểu đồ màu xanh/đỏ như khẳng định lợi nhuận. Dùng nhãn và bảng dẫn chứng dễ hiểu, khả dụng trên mobile.

- Giao diện tiếng Việt, hướng dẫn thuật ngữ “cụm”, “trung vị”, “PIT”, “độ tươi dữ liệu” bằng tooltip.

# 12. QUY TRÌNH CẬP NHẬT DỮ LIỆU VÀ RELEASE

## 12.1. Mục đích và lộ trình hai giai đoạn

**Giai đoạn đầu — mô phỏng ngày 02/01/2026:** Build và kiểm chứng artifact Assessment cho danh mục mã hỗ trợ tại mốc hồi cứu này. Từng mã dùng giá phiên 31/12/2025, snapshot A v4 cùng ngày và FY B-PIT phù hợp theo mục 5.2 và 7.3. Website nhận mã tra cứu và ghi rõ ngày mô phỏng.

**Giai đoạn tiếp theo — đánh giá tại ngày truy cập thực tế:** Khi pipeline dữ liệu và phát hành nhãn A v4/B-PIT đủ mới, chuyển cấu hình ngày đánh giá sang ngày truy cập thực tế; giữ nguyên Assessment Engine, API và quy tắc bằng chứng. Không được tự động chuyển chỉ vì đã sang một ngày mới: cần kiểm chứng toàn bộ nguồn và phê duyệt bản phát hành.

Trạng thái chất lượng dữ liệu được kiểm tra **theo `as_of` của từng giai đoạn**: đủ điều kiện thì trả nhận định; thiếu, quá cũ hoặc chưa đủ PIT thì chỉ hiển thị dữ liệu tham khảo và lý do. `SIMULATED_AS_OF` / `CURRENT_AS_OF` là metadata vận hành, **không phải hai sản phẩm hoặc nút chọn trên giao diện**.

## 12.2. Pipeline cập nhật dữ liệu (chạy trước khi người dùng tra cứu)

Trong giai đoạn mô phỏng, nhận và xác minh bộ đầu vào mục 6.4 sau khi bàn giao làm giàu, rồi thực hiện các bước 4–7. Các bước 1–3 là công việc upstream để cung cấp dữ liệu và nhãn đã kiểm chứng. Khi chuyển sang vận hành thực tế, áp dụng đầy đủ chu kỳ cập nhật dữ liệu và nhãn theo các bước 1–7.

| **Bước** | **Công việc thực hiện** | **Kết quả cần có** |
|---|---|---|
| 1. Cập nhật thị trường | Thu thập giá và giao dịch; kiểm tra phiên, dữ liệu thiếu và price basis; tính đặc trưng A theo kỳ đã duyệt. | Dữ liệu/feature thị trường có ngày và trạng thái chất lượng. |
| 2. Cập nhật tài chính | Upstream nhận báo cáo mới, xác minh nguồn/ngày công bố và chuẩn bị đúng 9 đặc trưng theo protocol B-PIT. Assessment đọc SQLite đúng pin của B-PIT theo mục 6.4. | Vector tài chính theo FY kèm `usable_from_date`, cutoff, status và provenance của từng chỉ số. |
| 3. Cập nhật nhãn cụm | Cập nhật/gán nhãn **A v4** theo protocol thị trường và **B-PIT** theo FY/cutoff/khả năng dùng báo cáo; nếu cần phiên bản mô hình mới phải có stage và kiểm chứng riêng. Không dùng artifact ngoài A v4/B-PIT làm nguồn thay thế. | Nhãn A v4 và B-PIT có model version, as-of provenance và trạng thái kiểm chứng; không ghi đè artifact đã seal. |
| 4. Xây dựng Assessment | Truy xuất đúng ngày và **18 đặc trưng**, chọn Peers theo policy, kiểm chất lượng và áp dụng rulebook đã duyệt; dựng chuỗi feature-history đọc-only cho biểu đồ. | Kết quả + lý do + cảnh báo + lịch sử kiểm chứng cho từng mã; mã thiếu dữ liệu có trạng thái rõ ràng. |
| 5. Kiểm chứng | Đối chiếu PIT, nguồn/hash, **whitelist 18 đặc trưng** trong evidence/Peers/lịch sử, nhãn, trường hợp biên và tính độc lập của bộ chọn biểu đồ. | Báo cáo PASS/BLOCKED và manifest. |
| 6. Phát hành | Tạo artifact mới, không ghi đè bản cũ; sau khi được duyệt, cập nhật pointer cho backend. | Version mới, khả năng truy vết/rollback. |
| 7. Kiểm thử website | Tra FPT và ca thiếu dữ liệu/đổi mã/sai revision; kiểm ngày, nhãn, đề xuất, **một biểu đồ chuyển đổi 18 đặc trưng + 5/10 năm**, bảng chi tiết và mobile. | Kết quả UAT trước khi công bố. |

Khi người dùng nhập mã: Next.js gọi FastAPI để đọc kết quả đã phát hành theo đúng `as_of`/`assessment_context` và kiểm tra các gate so với `as_of`. Không crawl, không fit K-Means và không tạo đánh giá mới trực tiếp trong request. Kết quả mô phỏng phải gắn ngày giả lập; không có kết quả hiện tại hợp lệ thì API không được âm thầm dùng bản mô phỏng làm kết luận hôm nay.

## 12.3. Hạ tầng triển khai và rollback

Giữ kiến trúc hiện có: versioned artifact (có thể phát hành trên Hugging Face Dataset) → Render/FastAPI read-only → Vercel/Next.js. Dữ liệu Assessment được lưu riêng với manifest/hash và nguồn model/Indicators/policy; chỉ cập nhật pointer sang bản mới sau khi kiểm chứng. Backend kiểm hash khi mở dữ liệu; nếu phát hành lỗi thì trỏ lại bản đã được kiểm chứng, không sửa artifact cũ.

Lịch vận hành đã chọn cho giai đoạn đánh giá thực tế: cập nhật giá sau phiên giao dịch hoàn tất, A theo kỳ tháng của M2, tài chính khi có báo cáo công bố, B-PIT theo FY/cutoff và build Assessment khi nguồn sẵn sàng. Đây là bước triển khai sau bản mô phỏng đầu tiên, chưa phải chức năng tự động đang hoạt động. Các ngưỡng và cách phát hành theo mục 16.1 phải được chuyển thành cấu hình có phiên bản, kiểm thử và nghiệm thu trước khi chạy thực tế.

# 13. KIỂM THỬ VÀ ĐIỀU KIỆN NGHIỆM THU

## 13.1. Danh sách test bắt buộc

| **ID** | **TEST / GATE**                          | **KỲ VỌNG**                                                                                                 |
|--------|------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| T01 | Tra cứu nhiều mã có dữ liệu hợp lệ tại `as_of` | Kiểm tra FPT và ít nhất một mã khác có dữ liệu hợp lệ. Mỗi lượt trả đúng ticker, nhãn, chỉ số và bằng chứng của mã được yêu cầu, theo đúng pin model/indicators. |
| T02    | as_of trước khi có FY report             | Không dùng FY tương lai; thử boundary cutoff/usable_from_date.                                              |
| T03    | `CURRENT_AS_OF` tháng 11/2026 nhưng A chỉ đến 2025 | HISTORICAL_ONLY/STALE, không kết luận đầu tư hiện tại; không tự thay bằng bản mô phỏng. |
| T04    | Fiscal FY2025 tại 31/12/2025             | Không dùng nhãn B-PIT FY2025 khi FY hoặc mô hình chưa đạt usable/cutoff.                                                         |
| T05    | Mã mới thiếu feature/history             | INSUFFICIENT_EVIDENCE; không suy nhãn hoặc zeros.                                                           |
| T06 | Mã không thuộc phạm vi B-PIT | Chỉ hiện A v4 hợp lệ để tham khảo và trả `INSUFFICIENT_EVIDENCE`; phân biệt mô hình không hỗ trợ với trường hợp thiếu dữ liệu đầu vào; không tự sử dụng mô hình thay thế. |
| T07 | Chọn Peers: ngưỡng 3 Peers cho từng đặc trưng | Có ≥3 mã cùng A+B thì dùng `SAME_A_AND_B_PIT`; nếu dưới 3, **ROE** mở rộng cùng B-PIT (`SAME_B_PIT`), **mom_126** mở rộng cùng A v4 (`SAME_A_V4`). Có đúng 3 mã hợp lệ thì tính trung vị; với 0–2 mã sau mở rộng thì không tính trung vị, chỉ hiển thị giá trị có sẵn; không phân nhóm nhỏ/lớn. `peer_basis` và `peer_count` đúng riêng từng đặc trưng; thiếu Peers không tự động trả `INSUFFICIENT_EVIDENCE`. |
| T08    | Model cluster yếu/nhỏ hoặc unstable      | Quality flags và confidence gate; không biến cluster number thành rank.                                     |
| T09 | `debt_to_equity` không hợp lệ, `cfo_to_ni` thiếu, ROE âm, momentum/giá nguồn thiếu | Không tính giá trị ngoài đặc trưng phân cụm, không đảo chiều tín hiệu hoặc điền 0; trạng thái chất lượng đúng. |
| T10    | Dữ liệu hai nguồn conflict, hash sai     | Fail closed, không fallback sang số unverified.                                                             |
| T11    | Revision URL và API mismatch             | HTTP 409, UI reset trạng thái cũ.                                                                           |
| T12    | Chuyển ticker A → B rồi Back             | Không flash kết luận của ticker trước, URL restore đúng.                                                    |
| T13 | Đổi lịch sử 5/10 năm | Chỉ thay dữ liệu **một biểu đồ** và bảng lịch sử; không thay `as_of`, assessment_status, rulebook, nhãn A v4/B-PIT, peer_basis hay evidence kết luận. Báo coverage thực tế, không điền 0/nội suy; không sử dụng FY chưa khả dụng tại `as_of`. |
| T14    | Không có tham số dự báo / gọi API Output | Không có horizon trong query/UI/schema; chỉ trả đánh giá theo `as_of` và không dự báo giá/lợi suất. |
| T15 | Replay cùng inputs và policy | Cùng đầu vào và rulebook cho cùng nội dung đánh giá và SHA256 của nội dung đánh giá. `run_id`, `generated_at` và metadata vận hành được phép khác. |
| T16    | Mobile, keyboard, dark/light             | Không tràn layout; accessible headings/tables/tooltip.                                                      |
| T17    | API payload invalid/ticker injection     | Trả lỗi validation; không query file path tùy ý.                                                            |
| T18    | Upgrade bundle old/new                   | No silent cross-version comparison hoặc overwrite sealed files.                                             |
| T19 | Demo `SIMULATED_AS_OF` ngày 02/01/2026 | FPT nhận đúng ngày demo và giá phiên 31/12/2025. Response và UI ghi rõ đây là mô phỏng hồi cứu. Không yêu cầu giờ chốt demo. |
| T20    | Truy cập năm 2026, `as_of` mô phỏng cũ hơn | Đánh giá độ mới so với `as_of` giả lập, không so với `request_time`; không tự chuyển thành nhãn hiện tại. |
| T21    | Đổi bản phát hành từ mô phỏng sang hiện tại | Cùng engine/rulebook; thay đúng context, `as_of`, artifact/cache; chỉ bật hiện tại nếu đủ gate. |
| T22 | Tách nguồn dữ liệu của Output khỏi API hiện hữu | Assessment chỉ đọc artifact A v4 + B-PIT được xác minh; không sử dụng nhãn khác từ `/overview` hoặc `/peers` và không thay đổi các API hiện hữu. |
| T23 | Giới hạn đặc trưng trong rulebook và evidence | Từ chối/đánh dấu lỗi nếu rulebook, `drivers`, Peers hoặc lịch sử biểu đồ dùng field ngoài danh sách **9 A v4 + 9 B-PIT**; trường ngoài danh sách phải bị chặn, không dùng làm tín hiệu Assessment. |
| T24 | Một biểu đồ chuyển đổi chỉ số | Chọn lần lượt 18 đặc trưng và cửa sổ 5/10 năm; tại một thời điểm chỉ một chart, chỉ ghép line cùng đơn vị/tần suất, không đổi verdict/evidence; báo thiếu kỳ và PIT đúng. |
| T25 | Giá phiên hoàn tất gần nhất | Trước lúc đóng cửa dùng phiên hoàn tất trước đó; sau lúc phiên mới hoàn tất yêu cầu dữ liệu phiên mới. Thiếu giá của phiên vừa kết thúc thì **không có verdict mới**, dù chỉ trễ 1 phiên. Nghỉ cuối tuần/lễ không bị tính là phiên chưa cập nhật. |
| T26 | Snapshot A cách 22/23 phiên | Hai snapshot đều **không bị loại chỉ do số phiên**; kiểm kỳ snapshot, khả dụng tại `as_of`, phiên bản và lịch phát hành thay vì một ngưỡng 22 phiên. |
| T27 | Thiếu snapshot tháng đến hạn | Khi lịch phát hành đã nghiệm thu xác định kỳ A v4 mới **đã đến hạn** nhưng chưa có artifact hợp lệ, gắn cờ thiếu kỳ, chỉ hiển thị nhãn cũ tham khảo và không xuất verdict. Trước thời hạn phát hành hợp lệ, vẫn dùng snapshot gần nhất. |
| T28 | Không có B-PIT, chỉ có A v4 | Không chọn Peers chỉ theo A; không lập danh sách Peers, không sử dụng `/peers` legacy, trả `INSUFFICIENT_EVIDENCE` cho kết luận kết hợp. |
| T29 | Quy tắc bốn nhãn và cảnh báo theo dõi | Thử riêng từng điều kiện `gross_margin < 0`, `current_ratio < 1` và `revenue_growth < 0` trên ca vốn thuận lợi. Chỉ cần một điều kiện đúng để trả `WATCH`. Các giá trị bằng ngưỡng không kích hoạt cảnh báo. Nếu đồng thời có cảnh báo trọng yếu thì trả `CAUTION`. Thử cả ca đủ điều kiện `RESEARCH_FAVORABLE` và ca thiếu trường bắt buộc. |
| T30 | Peers trong bản demo | Giữ nguyên dữ liệu dùng để quyết định nhãn. Thay giá trị Peers làm thay đổi trung vị hoặc giảm số Peers xuống dưới 3. Phần giải thích thay đổi theo G4, nhãn vẫn giữ nguyên. |
| T31 | Phân biệt mã thiếu dữ liệu và mã không tồn tại | Mã có thật thiếu B-PIT hoặc dữ liệu bắt buộc trả `200 + INSUFFICIENT_EVIDENCE`. Mã không tồn tại trả `404`. Artifact chưa phát hành trả `503`. |
| T32 | Bộ pin tài chính sau làm giàu | Fixture dùng đúng cặp nhãn B-PIT và SQLite chỉ số của cùng bản bàn giao. Thử đổi sang SQLite baseline khi nhãn đang pin bản làm giàu và kiểm build từ chối mismatch. Với ô điền trung vị, giữ trạng thái/provenance và áp dụng đúng policy Assessment đã chọn. |

## 13.2. Gate nghiệm thu theo loại

- GATE A — Data & PIT: 100% case boundary thuộc test set không lộ future data; mismatch provenance bị fail-closed.

- GATE B — Assessment policy: kiểm thử bảng điều kiện và thứ tự ưu tiên bản demo ở mục 8.3. Ghi version rulebook, phân biệt tín hiệu, chất lượng dữ liệu và độ tin cậy của bằng chứng.

- GATE C — Backend: có schema, targeted unit/integration tests, contract 200/404/409/422/503; API read-only.

- GATE D — UI: 5 tab đúng, **một biểu đồ có selector trong 18 đặc trưng + 5/10 năm**, bảng 18 đặc trưng, mobile/desktop và các empty state; bản mô phỏng ghi rõ ngày giả lập, không trộn ticker hoặc ngày đánh giá khi điều hướng.

- GATE E — Release: SHA256/manifest verify; giữ nguyên M2/M3 frozen; cập nhật `docs/DECISIONS.md` và CHANGELOG **khi triển khai repository**, không ghi là đã làm ở bước sửa kế hoạch.

- GATE F — Review: bằng chứng, smoke và link từ đề xuất đến chỉ số gốc được kiểm tra trên các nhóm case nghiệm thu.

## 13.3. Bộ lệnh kiểm thử kế thừa

Theo AGENTS.md, khi thay code cần targeted tests của subsystem, python -m compileall -q src tests scripts run.py và synthetic smoke từ configs/data/synthetic_smoke.example.json; thay web cần build/typecheck frontend và script kiểm tra UI phù hợp. Full repository gate nếu phạm vi thay đổi đòi hỏi; không được diễn giải targeted PASS là full suite PASS.

# 14. KẾ HOẠCH TRIỂN KHAI THEO GIAI ĐOẠN

Ước lượng là thứ tự phụ thuộc kỹ thuật, không phải cam kết lịch hoàn thành. Ưu tiên tạo bản mô phỏng ngày 02/01/2026 để nghiệm thu Assessment Engine; pipeline đánh giá tại ngày truy cập thực tế được triển khai tiếp khi dữ liệu đủ mới. Chỉ mở stage tiếp theo khi gate trước được chấp nhận; không tự động sửa methodology hay commit.

**Điểm bắt đầu của thành viên triển khai:** nhận bộ pin làm giàu ở mục 6.4 từ bàn giao Giai đoạn F, sau đó bắt đầu S1. Mốc demo của S0 đã chốt. Dùng run B-PIT làm giàu và SQLite đi cùng để kiểm độ phủ của danh mục và đối chiếu các ca mẫu, gồm FPT.

| **STAGE**                         | **CÔNG VIỆC CHI TIẾT**                                                                                                  | **ĐẦU RA / ĐIỀU KIỆN DỪNG**                                      |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| S0 — Audit & freeze scope | Đã chốt mốc demo hồi cứu ngày 02/01/2026, giá phiên 31/12/2025 và phạm vi A v4 + B-PIT. FPT là mã kiểm tra mốc trong audit. | Handoff phạm vi và audit evidence. Khoá bộ pin tài chính theo mục 6.4 sau làm giàu. |
| S1 — Data contract & eligibility | Nhận và kiểm bộ pin mục 6.4. Mã hóa thời điểm đánh giá, phiên giá, cutoff, whitelist 18 đặc trưng, coverage và Peers theo mục 6.3. Kiểm bộ dữ liệu theo danh mục hỗ trợ và chuẩn bị fixtures FPT, một mã khác đủ dữ liệu, VCB và mã mới. | Contract + fixtures + tests. Dừng nếu pin không khớp hoặc không xác minh được provenance cấp nguồn. Mã riêng lẻ thiếu dữ liệu có trạng thái theo mục 8.3. |
| S2 — Cụ thể hóa rulebook D-ASS-01 | Chuyển bảng điều kiện bản demo ở mục 8.3 thành cấu hình versioned và kiểm thử ca biên, thiếu dữ liệu, ưu tiên nhãn, Peers và replay. | Rulebook/config có version + bảng test. Chỉ phát verdict khi kiểm thử và nghiệm thu đạt. |
| S3 — Offline builder & QA         | Build artifact Assessment theo từng mã trong danh mục hỗ trợ tại ngày mô phỏng. Pin source/model/policy và kiểm replay, hash, coverage. | Demo artifact + verifier PASS + coverage report. |
| S4 — Backend read-only            | Adapter + response Pydantic + endpoint GET + revision lock, contract tests.                                             | API fixture PASS trên 200/404/409/422/503.                       |
| S5 — Frontend stocks tab | Thêm tab, status, evidence drivers/Peers, **một vùng biểu đồ với selector 18 đặc trưng**, lookback 5/10, bảng chi tiết, link nguồn, mobile, URL state. | UI tests/screenshots FPT + test chuyển chỉ số không đổi verdict. |
| S6 — UAT, publish, handoff        | Smoke/UAT theo `as_of` giả lập, kiểm nhãn mô phỏng, công bố giới hạn và bản release; ghi điều kiện mở rộng đánh giá thực tế. | Bản mô phỏng được nghiệm thu; vận hành thực tế là bước tiếp theo có gate riêng. |



# 15. THÔNG TIN CẦN CÔNG BỐ KHI NGHIỆM THU

Tài liệu nghiệm thu cần nêu: số ticker có đánh giá hợp lệ/chỉ xem lịch sử/không đủ cơ sở; độ phủ dữ liệu của 18 đặc trưng và số năm thực có (5/10 năm); trạng thái giá của phiên hoàn tất gần nhất, kỳ/ngày snapshot A và việc có thiếu kỳ cập nhật tháng hay không; FY/ngày khả dụng của B-PIT; số Peers hợp lệ theo từng đặc trưng; phiên bản nguồn/model/rulebook và các giới hạn đã phát hiện. Không chỉ đưa vài ảnh FPT rồi suy rộng toàn thị trường. Đây là **nội dung bằng chứng nghiệm thu**, không phải dashboard chất lượng dữ liệu riêng cho nhà đầu tư.

# 16. RỦI RO, GIẢM THIỂU VÀ QUYẾT ĐỊNH ĐÃ CHỌN

| **RỦI RO**                              | **TÁC ĐỘNG**                         | **BIỆN PHÁP**                                                                   |
|-----------------------------------------|--------------------------------------|---------------------------------------------------------------------------------|
| Nhầm nhãn M2 với sức mạnh đầu tư        | Tạo khuyến nghị sai cơ sở.           | Separate descriptive cluster vs investment policy; notes cảnh báo.              |
| Snapshot A v4 chưa theo kịp kỳ đánh giá | Dễ nhầm nhãn mô tả quá khứ với kết luận tại ngày hiện tại, đặc biệt khi thiếu kỳ phát hành tháng. | Hiển thị ngày/kỳ snapshot, xác minh lịch phát hành, chỉ dùng bản mới nhất hợp lệ; thiếu kỳ đến hạn thì không phát verdict. Tách `as_of` mô phỏng với ngày truy cập. |
| Output đọc nhầm nhãn legacy B/C | Có nguy cơ dùng kết quả ex-post hoặc sai mô hình, gây look-ahead bias và kết luận sai. | Đọc riêng A v4/B-PIT, kiểm FY/cutoff/usable và revision; test chặn mọi fallback từ `/overview` hoặc `/peers` cũ. |
| Chất lượng/cỡ cụm B-PIT không đáp ứng | Có thể làm so sánh thiếu ổn định hoặc kết luận quá mạnh. | Đánh giá profile/cỡ cụm/cờ chất lượng của B-PIT theo artifact hợp lệ; hạ confidence hoặc không ra verdict. |
| Chỉ số không tương thích giữa các mẫu BCTC | So sánh lệch hoặc đánh giá sai khi metric `NOT_APPLICABLE`. | Chỉ so cùng định nghĩa/kỳ/đối tượng áp dụng; thiếu dữ liệu thì hạ/khóa kết luận. |
| Thiếu dữ liệu lịch sử/mã mới                | So sánh méo, phân nhóm không hợp lệ. | Coverage disclosure; NOT_READY; không imputation tự ý.                          |
| Khác price basis raw/adjusted           | So sánh / tính return lệch.          | Field-level basis/provenance, không mix.                                        |
| Tối ưu rule sau khi xem M3 holdout      | Overfit và sai kết luận về hiệu quả. | V1 rule pre-registered; đánh giá forecast sau bằng dữ liệu kiểm định tách biệt. |
| Lệch version web/bundle/indicator       | Chồng dữ liệu không đồng nhất.       | Hash-pinned pointer + API 409 + cache invalidation.                             |
| Giải thích AI tự sinh không có nguồn    | Ngôn ngữ khẳng định vô căn cứ.       | Template-based evidence-first; text chỉ từ facts verified.                      |

## 16.1. D-ASS-01 — phương án đã thống nhất trong kế hoạch

Các lựa chọn dưới đây áp dụng cho kế hoạch Output. Mốc demo hồi cứu và logic bốn nhãn bản đầu được chốt ở mục 5.2 và 8.3. Khi triển khai, khóa các pin, rulebook và quy tắc dữ liệu bằng cấu hình có phiên bản. Lịch phát hành A theo tháng cần nghiệm thu trước khi bật chế độ đánh giá hiện tại. Việc chốt trong kế hoạch là đầu vào để triển khai và kiểm thử.

| **HẠNG MỤC** | **QUYẾT ĐỊNH ÁP DỤNG** | **LÝ DO** |
|---|---|---|
| Phạm vi Output và cách diễn đạt | Mục tiêu chính thức: đánh giá tại ngày truy cập thực tế; trước mắt dùng `as_of` mô phỏng ngày 02/01/2026. Giữ **4 trạng thái** (`RESEARCH_FAVORABLE`, `WATCH`, `CAUTION`, `INSUFFICIENT_EVIDENCE`); không dự báo hay đưa lệnh giao dịch. | Có thể thực hiện bản mô phỏng trước, không thay mục tiêu dài hạn và không ngụy trang kết quả lịch sử thành đề xuất hôm nay. |
| Ngày mô phỏng giai đoạn đầu | **02/01/2026**, phiên giá **31/12/2025**. Áp dụng cho danh mục mã hỗ trợ. FPT là ca mẫu dùng snapshot A v4 31/12/2025 và B-PIT FY2024. Lưu ngày và phiên giá trong cấu hình/manifest demo. | Giữ một mốc hồi cứu cố định, có bằng chứng truy vết. |
| Mô hình phân cụm | Output dùng **A v4 (thị trường) và B-PIT sau làm giàu (tài chính)** hợp lệ tại `as_of`. Pin đúng run và SQLite đi cùng theo mục 6.4 sau bàn giao. | Nhãn và đặc trưng khớp đúng bản nguồn, các artifact đã seal có thể truy vết. |
| Độ mới dữ liệu | **Giá:** phải có giá của **phiên giao dịch đã hoàn tất gần nhất tại `as_of`**, không cho phép thiếu một phiên đã kết thúc; trước khi phiên hôm nay kết thúc, phiên trước đó là phiên hoàn tất gần nhất. **A v4:** chọn snapshot tháng mới nhất hợp lệ và có thể sử dụng tại `as_of`, **không loại chỉ vì cách 23 hay hơn 22 phiên**; ghi kỳ/ngày snapshot và kiểm lịch phát hành kỳ tiếp theo đã được nghiệm thu. Nếu snapshot bắt buộc đã đến hạn mà chưa có bản xác minh thì gắn cờ thiếu kỳ và chặn verdict; chỉ cho xem tham khảo. **B-PIT:** kiểm FY, `usable_from_date`, cutoff và giới hạn hiệu lực 18 tháng của M3 khi áp dụng. | Giá có nhịp cập nhật theo phiên, A v4 theo tháng, B-PIT theo FY; áp điều kiện riêng đúng tần suất, tránh ranh giới máy móc 22/23 phiên và tránh công bố đề xuất từ nguồn thiếu kỳ cập nhật. |
| Chọn Peers | **Áp dụng chính sách chọn Peers tại mục 6.3:** mã tra cứu cần cả A v4 và B-PIT hợp lệ. Ưu tiên Peers đồng thời cùng A v4+B-PIT; nếu dưới **3 Peers hợp lệ cho đặc trưng**, **tài chính** mở rộng cùng B-PIT, **thị trường** mở rộng cùng A v4. Chỉ tính trung vị khi đủ 3 Peers hợp lệ cho từng đặc trưng; dưới 3 thì hiển thị dữ liệu riêng của mã và từng Peer hiện có (nếu có), không tính trung vị. Luôn lưu `peer_basis`/`peer_count`; không phân loại nhóm nhỏ/lớn và thiếu Peers không tự động chặn đánh giá đầu tư. **Không có B-PIT → không lập danh sách Peers** và không dùng kết quả Peers từ nguồn khác. | Một chính sách duy nhất nhưng chọn tập đối chứng đúng theo tính chất tài chính/thị trường; không ép mọi đặc trưng mở rộng cùng B-PIT. |
| Phạm vi chỉ số và đối tượng áp dụng | **Chỉ 18 đặc trưng đã dùng trong phân cụm**: 9 A v4 (`mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `downside_vol_63`, `mdd_126`, `beta_126`, `liquidity_21`) và 9 B-PIT (`roe`, `roa`, `gross_margin`, `net_margin`, `debt_to_equity`, `current_ratio`, `asset_turnover`, `revenue_growth`, `cfo_to_ni`). Đây là tập đặc trưng duy nhất tham gia rulebook và bằng chứng đề xuất; xác minh đầy đủ điều kiện sử dụng của từng đặc trưng tại `as_of`. | Tránh mở rộng thành hệ thống chấm điểm tài chính khác, bám sát chính tập đặc trưng phân cụm và kiểm soát sự tương thích giữa các kiểu BCTC. |
| Quy tắc đề xuất | Dùng điều kiện và thứ tự bốn nhãn tại mục 8.3. G4 dùng Peers để giải thích. Chỉ cần một cảnh báo theo dõi để hạ kết quả vốn thuận lợi xuống `WATCH`. Cảnh báo trọng yếu ưu tiên `CAUTION`. | Có thể triển khai và kiểm thử riêng từng điều kiện. |
| Giao diện biểu đồ lịch sử | **Phương án 2 đã chọn:** một vùng biểu đồ, dropdown chuyển chỉ số/nhóm chỉ số trong 18 đặc trưng, 5/10 năm (mặc định 10); bên dưới là bảng 18 đặc trưng. Đổi lựa chọn chỉ thay dữ liệu hiển thị, không thay assessment/verdict. | Gọn, không render 18 biểu đồ; vẫn giải thích được đủ các đặc trưng A v4 và B-PIT. |
| Kiểm chứng trước khi công bố | Bắt buộc replay/PIT boundary, kiểm whitelist 18 đặc trưng, chất lượng cụm/Peers, sai nguồn/hash, mã thiếu dữ liệu, bộ chọn một biểu đồ và 4 trạng thái; chỉ xuất verdict khi các gate QA PASS. | Chặn thông tin tương lai, sai số liệu và sai lệch artifact–API–giao diện. |
| Cập nhật và phát hành | Trước mắt phát hành **artifact mô phỏng** theo `as_of` đã audit. Khi có dữ liệu mới: giá sau phiên, A theo tháng, tài chính theo công bố, B-PIT theo FY/cutoff; build Assessment offline, QA rồi cập nhật pointer phiên bản. | Có thể triển khai bản demo sớm mà không phải dựng toàn bộ cơ chế cập nhật liên tục trước; hỗ trợ rollback và tái lập. |
| Dữ liệu xuất bản và hosting | Chỉ phát hành dữ liệu dẫn xuất đủ quyền phân phối; manifest/hash/nguồn được pin, backend chỉ đọc; kiểm dung lượng bundle và cold start trước deploy, giữ rollback. | Hạn chế rủi ro quyền dữ liệu và sai lệch revision khi triển khai trên Hugging Face, Render, Vercel. |

Các lựa chọn phương pháp trên đã được thống nhất **trong tài liệu kế hoạch**. Khi thực thi repository, cần ghi D-ASS-01 vào `docs/DECISIONS.md`, cập nhật cấu hình có phiên bản, tests, changelog và evidence nghiệm thu. Bất kỳ thay đổi kết quả/methodology M2/M3 hoặc mở rộng dữ liệu/mô hình ngoài phạm vi này vẫn cần phê duyệt riêng; **chưa có chỉnh sửa repository ở bước cập nhật tài liệu**.

# 17. KỊCH BẢN KIỂM THỬ OUTPUT

Các tình huống dưới đây mô tả hành vi hệ thống cần kiểm tra. FPT là mã dùng để minh họa. Kiểm tra thêm ít nhất một mã khác đủ dữ liệu theo T01. Tất cả ngày dữ liệu, nhãn cụm, chỉ số và kết luận phải lấy từ fixture hoặc artifact đã xác thực.

## 17.1. Case A — Mô phỏng FPT tại ngày 02/01/2026

- **Đầu vào:** `ticker=FPT`, tùy chọn `lookback_years=10`, `as_of=2026-01-02` và `required_price_session=2025-12-31` từ cấu hình demo. `request_time` là thời gian truy cập thực tế.
- **Thực hiện:** Đọc giá phiên 31/12/2025, snapshot A v4 cùng ngày và B-PIT FY2024 của FPT từ bộ làm giàu đã bàn giao theo mục 6.4. Đối chiếu nhãn FPT với `labels.csv` của run đó. Lấy 18 đặc trưng và Peers, kiểm một biểu đồ với cửa sổ 10 năm. Dùng bảng quyết định mục 8.3 và ghi bối cảnh hồi cứu.
- **Kết quả mong đợi:** Trả kết luận tương ứng với fixture nếu đạt gate, kèm `assessment_context=SIMULATED_AS_OF`, ngày giả lập, nguồn, giới hạn và evidence; chạy lặp cho cùng kết quả. Nếu thiếu dữ liệu, trả “Không đủ cơ sở”, không tự tạo kết luận. Không dùng thông tin tương lai hoặc gọi đây là đề xuất đầu tư hiện tại.

## 17.2. Case B — Đánh giá ngày truy cập thực tế khi nguồn hiện tại đã cũ

- **Đầu vào:** Môi trường kiểm thử đặt `assessment_context=CURRENT_AS_OF`, `request_time` trong tháng 11/2026; fixture giả định A mới nhất chỉ đến 31/12/2025.
- **Thực hiện:** Xác định `as_of` từ ngày/phiên thực tế, kiểm freshness và khả năng sử dụng B-PIT theo mốc đó; không fallback sang artifact mô phỏng.
- **Kết quả mong đợi:** Không xuất nhận định đầu tư hiện tại; trả “Không đủ cơ sở đánh giá” hoặc HISTORICAL_ONLY/STALE kèm lý do và ngày nguồn. Chỉ số và cụm lịch sử có thể xem với nhãn tham khảo.

## 17.3. Case C — Chuyển sang dữ liệu hiện tại hợp lệ

- **Đầu vào:** Fixture hiện tại có giá/snapshot A, FY/B-PIT, Indicators, Peers và rulebook đồng bộ, đủ mới theo `as_of` xác định từ `request_time`.
- **Thực hiện:** Kiểm gate, query `/api/v2/stocks/FPT/assessment` ở ngữ cảnh `CURRENT_AS_OF`; xác minh response không dùng dữ liệu hoặc cache mô phỏng.
- **Kết quả mong đợi:** Nếu hợp lệ, xuất một trong ba mức đề xuất theo rulebook (hoặc “Không đủ cơ sở” khi không đạt gate), kèm giải thích và ngày nguồn. Không tạo số liệu hay kết luận chỉ vì có nhãn A v4/B-PIT.

## 17.4. Case D — Thiếu dữ liệu, chỉ số không áp dụng và sai phiên bản

- **Đầu vào:** Fixture cho mã thiếu đặc trưng A v4/B-PIT hoặc không đủ điều kiện áp dụng B-PIT, thiếu Peers, dữ liệu ngoài danh sách 18 trường hay artifact sai phiên bản/hash; kiểm cả hai trường hợp mở rộng nhóm so sánh (ROE theo B-PIT, momentum theo A v4).
- **Kết quả mong đợi:** Nêu rõ nguyên nhân, không thay dữ liệu thiếu bằng 0, không dùng đặc trưng ngoài danh sách 18 trường để kết luận, không tự bổ sung Peers không hợp lệ; sai hash hoặc revision phải chặn kết quả.

## 17.5. Case E — Phân biệt hai ngữ cảnh mà không đổi thuật toán

- **Đầu vào:** Cùng mã và rulebook, lần lượt chạy fixture mô phỏng ngày 02/01/2026 và fixture hiện tại đủ dữ liệu.
- **Kết quả mong đợi:** Dùng cùng Assessment Engine; `as_of`, `assessment_context`, nguồn và cache thay đổi đúng theo artifact phát hành. Website ghi rõ “Mô phỏng tại ngày …” ở bản demo và không hiển thị nhãn đó khi đánh giá hiện tại. Khi chuyển chỉ số hiển thị hoặc 5/10 năm trong **một biểu đồ**, kết luận và bằng chứng ra quyết định không thay đổi.

**Bằng chứng nghiệm thu:** Kết quả test cho từng case, response JSON, ảnh giao diện desktop/mobile và nguồn/phiên bản artifact được kiểm chứng. Không cần tạo một kết luận đầu tư giả để làm đẹp bản demo.

# 18. TIÊU CHÍ HOÀN THÀNH VÀ HƯỚNG HÀNH ĐỘNG

## 18.1. Definition of Done cho Output

- [x] Đã thống nhất phạm vi Output: A v4 + B-PIT với **18 đặc trưng**, mô phỏng ngày 02/01/2026, bốn trạng thái, **một biểu đồ chuyển đổi chỉ số** và không dự báo tại D-ASS-01 (cấp kế hoạch; chưa phải dấu nghiệm thu release).

- [ ] Nhận bàn giao cặp B-PIT làm giàu và SQLite chỉ số đi cùng. Kiểm run ID và SHA256 theo mục 6.4. Ghi lại chỉ số quan sát/điền trung vị theo policy được duyệt.

- [ ] Tạo cấu hình D-ASS-01 có version và tests: **whitelist 18 đặc trưng**, **quy tắc chọn Peers** (ưu tiên giao A+B; tài chính mở rộng theo B-PIT, thị trường mở rộng theo A v4; ≥3 Peers/đặc trưng để tính trung vị, không tự động chặn verdict nếu thiếu), PIT, giá phiên hoàn tất gần nhất, lịch snapshot A theo tháng và hiệu lực tài chính 18 tháng; hiện thực bảng quyết định mục 8.3 và kiểm thử trước verdict.

- [ ] Có offline deterministic build + độc lập verify và manifest checksum.

- [ ] Mỗi response chứng minh được ticker, `request_time`, `as_of`, `assessment_context`, cluster model version, FY/usable date, peer basis và input source.

- [ ] Không đưa verdict khi dữ liệu stale/invalid; **Output chỉ sử dụng A v4 + B-PIT**, không thay thế bằng nhãn từ nguồn khác; bảo toàn các chức năng website hiện hữu.

- [ ] Tab /stocks hoạt động desktop/mobile với **một biểu đồ có bộ chọn 18 đặc trưng + 5/10 năm**, bảng chi tiết 18 trường, link evidence và URL share; chuyển lựa chọn không thay verdict.

- [ ] API tests + targeted regression + compileall + UI build/test pass; sealed M2/M3 không đổi.

- [ ] Demo ngày 02/01/2026 đạt UAT khi tra FPT và ít nhất một mã khác đủ dữ liệu. Ca current-stale, current-ready, mã ngoài phạm vi B-PIT và mã thiếu lịch sử cũng đạt theo kịch bản.

- [ ] Báo cáo coverage/limitations và changelog được bàn giao; release production chỉ sau approval.

## 18.2. Thứ tự triển khai sau khi đã thống nhất phương án

Mốc demo hồi cứu đã chốt ở S0, với FPT làm ca minh họa. Sau bàn giao Giai đoạn F của kế hoạch làm giàu, nhận bộ đầu vào mục 6.4 và chạy S1 để triển khai hợp đồng dữ liệu và Peers cho danh mục mã hỗ trợ. S2 hiện thực và kiểm thử bảng quyết định ở mục 8.3. Sau đó mới S3 builder offline và lịch sử feature, S4 API, S5 một biểu đồ chuyển đổi chỉ số, S6 QA/release. Đánh giá theo thời điểm truy cập là bước mở rộng khi dữ liệu hiện hành đủ mới.

# 19. PHỤ LỤC — NGUỒN VÀ TÌNH TRẠNG XÁC MINH

## 19.1. Tài liệu yêu cầu

Tài liệu nguồn: “Phien_am_noi_dung_buoi_bao_cao (1).docx”. Các yêu cầu được đưa vào kế hoạch gồm tra cứu mã, giải thích phân cụm, so sánh chỉ số, hiển thị lịch sử và đề xuất đầu tư.

## 19.2. Repository — nguồn khảo sát mã trực tiếp

**• README.md / AGENTS.md / docs/DECISIONS.md / docs/CURRENT_STATUS.md:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/tree/feature/indicators-v1/docs

**• web/README.md:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/web/README.md

**• web/frontend/app/stocks/page.tsx:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/web/frontend/app/stocks/page.tsx

**• web/frontend/components/shell.tsx:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/web/frontend/components/shell.tsx

**• web/backend/app/main.py:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/web/backend/app/main.py

**• web/backend/app/fundamentals.py:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/web/backend/app/fundamentals.py

**• src/delta_t1/m3/bpit.py:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/src/delta_t1/m3/bpit.py

**• configs/product/indicators_v1.json:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/configs/product/indicators_v1.json

**• docs/m3/KE_HOACH_M3_SCHEMA_GITHUB.md:** https://github.com/trongnguyen1010/Risk-Adjusted-Momentum-Clustering/blob/feature/indicators-v1/docs/m3/KE_HOACH_M3_SCHEMA_GITHUB.md

## 19.3. Trạng thái bằng chứng

| **CÓ BẰNG CHỨNG TRỰC TIẾP**                                                                         | **CHƯA KIỂM CHỨNG TRONG LƯỢT NÀY**                                                                         |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| Cây thư mục nhánh, Next.js/FastAPI routes, Indicators pointer, A v4, B-PIT code và quyết định. | Chưa chạy full suite hoặc xác nhận toàn bộ artifact B-PIT đã có trên hosting; chưa bảo đảm dữ liệu 2026 trong bản phát hành. |
| M3 sealed, B-PIT cutoff/availability và cơ chế A v4; website hiện hữu có dữ liệu/nhãn A/B/C riêng. | Chưa kiểm tra độc lập toàn bộ raw local hoặc build log deployment; phân biệt rõ kết quả nghiên cứu website cũ và đầu vào Output. |
| Trang /stocks 4 tab, model labels latest; /peers hiện có cách xếp theo cluster/cap.                 | Không có engine Output đã phê duyệt; file path và API mới đều là đề xuất.                                  |
