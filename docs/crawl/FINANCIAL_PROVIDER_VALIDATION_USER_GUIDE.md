# Pilot đối chiếu nguồn và reference PDF — 19/10/2026

Phạm vi: **BRC, FPT, MWG, GMD, VNM**, annual FY2025 và supporting 2024/2023.
Flow này bổ sung QA cho [pilot5](FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md), dùng lại
PDF/thuyết minh đã review và kiểm hash; không sửa raw, canonical hoặc kết quả cũ.

## Kết quả thực chạy

- **235 reference facts**, 176 phép đối chiếu CafeF/PDF: 164 MATCH và 12 conflicts.
- 12 ô conflict giữ API gốc, chọn reference PDF đã review và ghi provenance.
  152 facts được API corroborate; 71 facts là PDF/notes/derived references bổ sung.
- Tính lại EPS, annual P/E, book-snapshot P/B, F, M, Z: **29/30**, số giữ nguyên.
  VNM F còn original-maturity closing current portion 2024/2025; interval 4–5/9.
- Wheel VietFin **0.2.0** đã tải từ PyPI và kiểm SHA256. Kiểm route từ source
  bằng controlled HTTP client; **chưa chạy VietFin SDK**, chưa cài dependency SDK.
- TCBS: 15 route requests/15 HTTP404. Chưa phân biệt được endpoint cũ, deployment
  hoặc request/header compatibility; không kết luận TCBS không có dữ liệu.
- SSI: catalog route bị HTTP403 sau 1 request public không xác thực; đã dừng.
  Không gửi các placeholder `X-Fiin-*` trong thư viện như credential và không bypass.
- Hai nguồn mới có **0 financial fields đã nhận và QA-accepted**; chưa thể chấm
  độ chính xác số học của chúng hoặc tuyên bố chúng thay PDF.

Hai request tải metadata/wheel được ghi riêng; 16 financial route attempts ở hai
journals riêng theo provider. Browser/web source inspection không được đo trong
script counters. Không download PDF/OCR mới hoặc reset campaign CafeF đã hết hạn.

Kiểm thử:34targeted testsPASS, compile/synthetic smoke/PowerShellreview+verifyPASS.
Full436tests có435PASS/1pre-existingM2-PREP input hash mismatch tại `docs/DECISIONS.md`;
không sửa assertion hoặc frozen evidence để bỏ qua lỗi này.

## Quy tắc chọn số

PDF chỉ được chọn khi reference đã review, đúng kỳ/scope/framework/unit và có
pin/provenance hợp lệ. Bản PDF bất kỳ hoặc OCR tự động không tự thành số đúng.
Phải kiểm phiên bản đính chính và ý kiến kiểm toán khi thay reference về sau.

Giá trị API khớp giúp kiểm chứng reference. Giá trị API lệch bị quarantine;
không dịch row, suy multiplier từ magnitude, đổi missing thành 0 hoặc lấy đa số
nhà cung cấp để quyết định. Quy tắc này chỉ phục vụ **reference arithmetic**,
không tự chấp nhận financial canonical/research/cluster hoặc strict PIT.

P/E dùng EPS năm; P/B dùng equity/shares tại 31/12/2025 và raw price 22/04/2026.
Đây chưa phải current TTM/event-complete ratios. Giá và sự kiện cổ phiếu cần
nguồn riêng ngoài PDF BCTC.

## Chạy lại offline bằng PowerShell

Từ project root:

```powershell
.\scripts\financial_provider_validation.ps1 -Action plan
.\scripts\financial_provider_validation.ps1 -Action review
.\scripts\financial_provider_validation.ps1 -Action verify -Output data/financial/vietfin_pilot5_v1/reviews/25f409691eb0959a02e3
```

Wrapper mặc định dùng bundled Python, có thể truyền `-Python` là đường dẫn Python
khác. `review` tạo immutable output theo semantic hash; `verify` kiểm hash và
tính lại. Đọc `selected-references.json`, `decisions.csv`, `metrics.csv`,
`calculation-details.json` và `summary.json` trong output.

`acquire -Network` và `probe-ssi -Network` là các actions live đã dùng trong lượt
này. **Không chạy lại để retry cùng route:** TCBS tasks đã có receipts và SSI
boundary đang latched. Rerun terminal campaign chỉ đọc cache, không mở budget mới.
Các route/provider tương lai cần evidence/config riêng; không sửa frozen contract
hoặc đặt URL đoán để vượt endpoint/access failure.

## Đầu vào và bước tiếp theo

[Config](../../configs/data/financial_provider_validation_v1.json),
[report thực chạy](../../artifacts/reports/financial-vietfin-pilot5-v1/report.md).

Để tiếp tục kiểm số TCBS/SSI cần route hiện hành đã xác minh hoặc access chính thức
hợp lệ. Sau khi có raw mới, review mapping/unit/scope/vintage trước field QA.
Để đạt 30/30 vẫn cần tài liệu tách rõ VNM closing current portion của khoản vay
originally-long-term ở cả hai ngày cuối năm; thêm một tổng dư nợ khác chưa giải quyết gap.
