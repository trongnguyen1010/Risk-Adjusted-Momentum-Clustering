# CafeF: ngày gửi báo cáo và các tab tài chính — đính chính discovery

Kiểm trực tiếp ngày **18/10/2026** sau phản hồi và ba ảnh của owner.
[Evidence/report](../../../artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md).
Tài liệu này là **bổ sung bắt buộc trước R1** của
[plan kiểm chứng CafeF](../FINANCIAL_CAFEF_REVALIDATION_PLAN.md). Plan đã seal giữ
nguyên; phần bổ sung sửa những route chưa được kiểm đủ, không sửa lịch sử evidence.

## 1. Kết luận đã xác minh

- Trang Công bố thông tin có ngày gửi **của từng bản ghi**, ID, report type và
  link PDF. Không được tiếp tục mô tả chung là CafeF không có ngày tài liệu.
- Financial detail tabs có route AJAX riêng; LCTT của QNP có JSON dữ liệu thật
  từ endpoint **GetReportLCTT**, không phụ thuộc việc GetReportSummary có trả LCTT.
- Các literal routes này chưa có trong Python crawler hiện tại. Discovery trước
  có ghi nhận tab LCTT và màn Công bố thông tin, nhưng chưa hoàn tất đường đi từ
  UI đến endpoint và dữ liệu. Đây là thiếu sót discovery/integration cần khắc phục.

## 2. Ngày ở cột “Thời gian gửi” đến từ đâu?

Trang: [Công bố thông tin](https://cafef.vn/du-lieu/cong-bo-thong-tin.chn).
Inline script gọi:

```text
GET https://cafef.vn/du-lieu/ajax/ajaxcongbothongtin.ashx
    ?symbol=FPT&pageindex=1&pagesize=20&reporttype=
    &startdate=&enddate=&center=0
```

Response `Data.BctcList` có `Id`, `Symbol`, `Year`, `Quarter`, `ReportType`,
`Content`, `LinkFile`, **`CreateDate`**. UI dùng:

```javascript
moment(e.CreateDate || e.createDate).format("DD/MM/YYYY")
```

Raw response lượt này serialize ngày dạng **`/Date(milliseconds)/`**. Phải giữ
raw string, parse epoch và timezone tường minh; không mặc định chuỗi ISO hoặc
lấy timezone máy chạy. Output DATE_ONLY Vietnam nên đối chiếu UI, không tự gọi
giờ tạo bản ghi là giờ doanh nghiệp công bố lần đầu.

| FPT report | ReportType | Ngày hiển thị đã tái hiện trên UI |
|---|---|---|
|Hợp nhất FY2025 đã kiểm toán|HK|20/03/2026|
|Hợp nhất Q2/2026 bản ban đầu|H|28/07/2026|
|Hợp nhất Q2/2026 đã soát xét|HS|22/08/2026|

FY2025 audited `Id=69bd0630b51797afb2ee4752` **khớp ID và link path** với raw
FileBCTC FY2025 đã lưu trong project. FileBCTC cũ có kỳ/name/link nhưng không có
CreateDate; flow cũ không join sang API Công bố thông tin và giữ `published_at=null`.
Không cần suy ngày từ filename để lấy được các ngày nói trên.

## 3. Sử dụng ngày cho PIT như thế nào?

Lưu riêng `provider_disclosure_created_at`, `provider_disclosure_date`,
`publication_source=CAFEF_DISCLOSURE`, `provider_report_id`, `report_type`, source
URL/raw SHA và attachment URL/PDF SHA khi đã có bytes. Đây là bằng chứng ngày
gắn với một tài liệu cụ thể, mạnh hơn ngày ký/filename proxy.

Trong practical profile, kiểm join đúng tài liệu rồi có thể đánh giá availability
theo **ngày nguồn CafeF ghi nhận**, không chặn numerical work vì thiếu giờ hoặc
chưa tìm thông báo issuer. Nếu dùng DATE_ONLY thì giữ rule phiên quan sát đầu tiên
sau ngày đó; calendar thiếu thì giữ temporal status riêng.

Tách hai khẳng định:

1. CafeF có một ngày CreateDate gắn với report/link: **đã xác minh trên FPT**.
2. CreateDate luôn bằng thời điểm doanh nghiệp/sở công bố lần đầu, hoặc file hiện
   tại không bị thay sau ngày tạo record: **chưa xác minh**.

Không bỏ qua dữ liệu hữu ích vì chưa chứng minh khẳng định2. Cũng không tự đổi
metadata tạo bản ghi thành `ISSUER_FIRST_PUBLIC_VERIFIED`. Historical selection
phải gắn số liệu với đúng version; không dùng bảng current/latest-restated rồi
gán ngày của PDF ban đầu cho mọi value. Bản Q2 ban đầu và bản soát xét phải là
hai vintages; trước22/08 không dùng dữ liệu chỉ có trong bản soát xét.

## 4. LCTT và các tab tài chính có đường dẫn riêng

[QNP financial](https://cafef.vn/du-lieu/hose/qnp-tai-chinh.chn) có tabs:
BCTC tóm tắt, Cân đối kế toán, Kết quả KD, Lưu chuyển tiền tệ, Chỉ số TC,
Chỉ tiêu kế hoạch. UI khi click LCTT gọi:

```text
GET https://cafef.vn/du-lieu/Ajax/FinancialAjax.aspx
    ?isBank=false&isInsurance=false&tab=luuchuyen&symbol=qnp
```

Tab body có script gọi đúng endpoint này (đã fetch thành công):

```text
GET https://apiweb.cafef.vn/api/v1/BCTC/GetReportLCTT
    ?symbol=QNP&pageIndex=1&pageSize=4&reportType=ALL&TypeTime=QUY
```

Response `value.data` có3 groups `HDKD`, `HDDT`, `HDTC`, cùng `templace` để map
code→label. Sample CFO code `HDKD_20` hiện có raw values, UI hiển thị lần lượt
**183,30; −10,65; −45,77;124,04 tỷ** theo headers Q4/2025,Q1/2026,Q2/2026,Q3/2026.
Đây là observations, chưa phải input được nghiệm thu cho score mới.

`TypeTime=QUY` và header quý không chứng minh CFO là quý riêng: bảng QNP cho thấy
những dấu hiệu cumulative/YTD. Phải kiểm actual duration và PDF khi cần, không
cộng bốn cột CFO hoặc cộng rounded EPS một cách máy móc. UI có thể hiển thị `-`
cho raw zero/missing, nên crawler đọc raw JSON và template, không chỉ scrape text.

Tab script còn có path `GetSecurityLcttDetail.ashx` cho securities enrichment;
**chỉ mới quan sát code**, chưa fetch/verify path đó trong lượt này. Agent phải
kiểm theo đúng loại doanh nghiệp nếu cần, không tự lấy Regular mapping cho broker.

## 5. Điều chỉnh ưu tiên cho agent thực thi plan

1. Audit route Công bố thông tin và join CreateDate/Id/LinkFile với FileBCTC cho
   các mã mẫu, lưu đủ bản ban đầu/soát xét/kiểm toán thay vì chỉ latest.
2. Click và trace **từng tab**, không chỉ summary: ghi request thực tế và kiểm
   raw fields. Kiểm riêng GetReportLCTT cùng bảng LCTT mới trước khi gọi là thiếu nguồn.
3. Đối chiếu known LCTT gaps FPT/VNM/PVS/ACV qua route này theo annual/interim,
   pagination và duration. QNP là control bổ sung từ phản hồi owner, không tự
   thay membership12 hoặc tuyên bố đã kiểm đủ lịch sử của các mã khác.
4. Structured first, PDF/OCR cho notes/validation/gaps thật. Chưa dùng proxy DEP,
   issuance hoặc nới công thức trước khi kiểm xem fields cần có đã ở deep tabs chưa.
5. Xuất riêng `SOURCE_ROUTE_PREVIOUSLY_UNCHECKED`, `EXTRACTABLE_NOT_INTEGRATED`,
   `PROVIDER_DATE_AVAILABLE`, `FIRST_PUBLIC_UNVERIFIED`, `VINTAGE_JOIN_PENDING`.
   Không gộp những trường hợp này thành “nguồn không có” hoặc “PIT không lấy được”.

Lượt này kiểm2 UI surfaces,20 FPT disclosure records và1 page LCTT QNP. Chưa xác
minh mọi mã/kỳ, chưa đổi strict calculator/acceptance, chưa chứng minh CafeF có đủ
tất cả inputs và chưa mở financial cluster. Đó là việc của run validation tiếp theo.
