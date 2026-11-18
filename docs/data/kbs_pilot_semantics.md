# Quyết định ngữ nghĩa dữ liệu KBS cho pilot — 12/09/2026

> **HISTORICAL / LEGACY EVIDENCE — NOT ACTIVE MARKET SOURCE.** Tài liệu này chỉ bảo toàn evidence cho immutable KBS pilot và các tham chiếu lịch sử. Active market source hậu C8 là CafeF `TradeHistoryNew`; các kết luận dưới đây không định nghĩa M2 market eligibility hiện tại.

```text
data_mode = real
```

Các quyết định dưới đây còn hiệu lực khi diễn giải đúng pilot lịch sử đã rà soát; chúng không phải current active-source decision. Bản smoke audit chưa giải quyết trước đó đã được gỡ khi dọn project; vendor snapshots hoàn chỉnh vẫn bất biến.

## Bảng quyết định

| field | meaning | unit | adjustment | evidence | confidence | decision |
|---|---|---|---|---|---|---|
| `open` | Giá mở cửa của phiên, key `o` | KBS API: VND; Vnstock SDK: nghìn VND | Vendor technical adjustment | E1, E2, E3 | Cao về mapping/unit; trung bình về phương pháp adjustment | Kiểm tra OHLC ở staging, giữ nguyên snapshot; không điền `raw_open` |
| `high` | Giá cao nhất của phiên, key `h` | KBS API: VND; Vnstock SDK: nghìn VND | Vendor technical adjustment | E1, E2, E3 | Cao về mapping/unit; trung bình về phương pháp adjustment | Kiểm tra và giữ ở staging; `raw_high=null` |
| `low` | Giá thấp nhất của phiên, key `l` | KBS API: VND; Vnstock SDK: nghìn VND | Vendor technical adjustment | E1, E2, E3 | Cao về mapping/unit; trung bình về phương pháp adjustment | Kiểm tra và giữ ở staging; `raw_low=null` |
| `close` | Giá đóng cửa của phiên, key `c` | KBS API: VND; Vnstock SDK: nghìn VND | `vendor_adjusted` | E1–E4 | Cao về việc không phải raw; trung bình về cách xử lý cash dividend | `adj_close=close*1000`; `raw_close=null` |
| `volume` | Khối lượng cổ phiếu trong phiên, key `v` | Shares | Không có multiplier hoặc adjustment trong SDK | E1, E2, E5 | Cao về unit; chưa chứng nhận matched/total scope cho toàn bộ lịch sử | `volume_multiplier=1`; không dùng làm execution capacity |
| `va` | Field tùy chọn có ý nghĩa gần traded value | Nhiều khả năng là VND nhưng chưa nhất quán qua lịch sử | Không áp dụng | E1, E2, E6 | Chưa đủ bằng chứng về scope và tính nhất quán | `traded_value=null`; `liquidity_21` là optional |
| `time` | Nhãn ngày giao dịch, không phải thời điểm công bố | Calendar date | Không áp dụng | E1, E2, E3 | Cao về trade date; exact vendor timezone chưa được chứng nhận | Normalize nhãn 07:00 theo `+07:00` thành `YYYY-MM-DD` |
| `VNINDEX` | Chỉ số giá thị trường HOSE | Index points | Price index, không phải total-return index | E1, E3, E7 | Cao | Giữ nguyên close; `index_multiplier=1`; `index_basis=price` |

## Evidence từ source và dữ liệu quan sát

**E1 — Vnstock source.** Bản cài Vnstock **4.0.6**, file `vnstock/explorer/kbs/quote.py` và `const.py`, cho thấy `t/o/h/l/c/v` được map trực tiếp. `quote.py:250–283` gọi endpoint KBS `data_day`; `quote.py:320–345` parse `t` mà không localize timezone, cast volume sang `int64`, chia equity OHLC cho **1.000**, nhưng không chia index. Code path này không tự tính corporate action, nên adjusted values đến từ upstream. Source copy và hash được lưu tại `data/vendor/evidence-kbs-20260912/`. [Upstream source](https://raw.githubusercontent.com/thinh-vu/vnstock/main/vnstock/explorer/kbs/quote.py) chỉ là nguồn hỗ trợ; hash của source cài trên máy là bằng chứng được pin cho run.

**E2 — KBS array trước khi Vnstock chuyển đổi.** `Quote.history(to_df=False)` cho kết quả:

| FPT date | API close | SDK close | API/SDK volume |
|---|---:|---:|---:|
| 2025-07-17 | 107847 | 107.847 | 8.334.200 |
| 2025-07-18 | 106997 | 106.997 | 6.494.600 |
| 2025-07-21 | 107681 | 107.681 | 7.563.700 |
| 2025-07-22 | 109438 | 109.438 | 6.889.600 |

Trường `t` ngày 18/07 là `2025-07-18 07:00`; ngày vẫn giữ nguyên sau SDK conversion. Event sample không có key `va`. Các file `fpt-event-api.json` và `fpt-unit-api.json` là array lấy qua SDK, không được tuyên bố là raw HTTP wire bytes.

**E3 — Đối chiếu giá thực tế.** [Bản tin thị trường Pinetree ngày 18/07/2025](https://pinetree.vn/post/20250718/ban-tin-thi-truong-18-07-2025/) ghi FPT **126.000 VND** và VNINDEX **1497,28 points**. KBS historical close của FPT là 106.997 VND, vì vậy việc gán chuỗi này là raw price chắc chắn sai.

**E4 — Hành vi quanh corporate action.** [Thông báo HOSE 1286/TB-SGDHCM ngày 15/07/2025](https://static2.vietstock.vn/vietstock/2025/7/16/20250715___fpt___tb_ngay_dkcc_phat_hanh_cp_de_tang_von_tu_nv_csh.pdf) quy định ex-date FPT là **21/07/2025**, thưởng cổ phiếu **20:3**. KBS adjusted series thay đổi khoảng **+0,639%** (`107681/106997-1`), trong khi raw close đương thời từ 126.000 xuống 110.300, khoảng **-12,46%**. Hành vi này phù hợp với split/bonus adjustment. Các tỷ lệ khác trong lịch sử cho thấy có adjustment ngoài sự kiện này, nhưng evidence chưa đủ để kết luận split-only hay cash-dividend reinvestment. Vì vậy contract dùng `vendor_adjusted`, không ép thành `unadjusted`, `split_adjusted` hoặc `total_return`.

[Tài liệu Vnstock về dữ liệu giao dịch](https://www.vnstocks.com/docs/vnstock-data/du-lieu-giao-dich) mô tả historical chart prices là technically adjusted. Tài liệu liên quan Sponsor package nên chỉ dùng để corroborate; source cài đặt và observed KBS behavior là evidence chính.

**E5 — Đối chiếu volume.** [Lịch sử FPT của Cophieu68](https://www.cophieu68.vn/quote/history.php?cP=3&id=fpt) ghi **6.494.600 shares** ngày 18/07/2025 và **7.563.700 shares** ngày 21/07/2025, trùng chính xác với KBS `v`. Cột giá của nguồn này cũng đã điều chỉnh nên không được dùng làm raw-price reference.

**E6 — Nghiên cứu `va`.** Ở endpoint gần thời điểm nghiên cứu, KBS ngày **10/09/2026** trả `o/h/l/c=72300/74800/72200/74500`, `v=11936600`, `va=882200140000`. [Nguồn giá cùng ngày](https://m.tinnhanhchungkhoan.vn/fpt-chot-quyen-chia-co-phieu-thuong-ty-le-101-post397426.html) ghi close **74.500 VND** và khoảng 11,9 triệu shares. Điều này xác nhận API dùng VND và SDK dùng nghìn VND. `va/v≈73.908 VND`, nằm trong OHLC, phù hợp với turnover theo VND. Tuy nhiên smoke sample cũ có `va/v` ngoài OHLC và một số response lịch sử không có `va`; scope matched/total chưa được chứng minh. Pilot bỏ field này thay vì block hoặc tạo dữ liệu giả.

**E7 — Đối chiếu VNINDEX.** [Thông báo thị trường cuối năm của SSC](https://ssc.gov.vn/webcenter/portal/ubck/pages_r/l/chitit?dDocName=APPSSCGOVVN1620162884) ghi VNINDEX **1784,49 points** ngày 31/12/2025. Pilot đối chiếu mức này và E3 với benchmark đã tải; index không dùng equity price multiplier.

Endpoint SAS thay thế do SDK khai báo, `/sas/kbsv-stock-data-store/stock/FPT/historical-quotes`, cũng đã được kiểm tra và trả HTTP 404. Việc này không cản pilot dùng adjusted-price; pipeline không tái dựng raw price.

## Research assumptions được khai báo rõ và không blocking

- `available_at_method=research_assumption`: trade date tại 15:00 cộng safety delay 120 phút. Đây không phải khẳng định về last matching-auction timestamp. Monthly decision lúc 17:00; execution tại close của phiên kế tiếp. `fetched_at` giữ thời điểm retrieval thật năm 2026. Historical corrections sau này không phải point-in-time data.
- `calendar_method=benchmark_derived`: dùng VNINDEX session dates, kiểm tra weekday, phần bù calendar và month-end maxima; không suy luận từ một cổ phiếu riêng lẻ. Việc HOSE/HNX đồng bộ ngày giao dịch là bounded pilot assumption. Calendar availability lúc 08:00 là giả định được ghi rõ.
- [Thông báo nghỉ giao dịch HNX 2025 do VietSC đăng lại](https://vietsc.vn/public/contents/vsc-ve-viec-cong-bo-lich-nghi-giao-dich-trong.pdf) và [thông báo của VIX](https://vixs.vn/thong-bao-nghi-giao-dich-nhan-dip-tet-am-lich-nam-2025.html) xác nhận đóng cửa 27–31/01 và mở lại 03/02. Toàn bộ giai đoạn 2023–2025 vẫn dùng `benchmark_derived`.
- `identity_status=provisional_verified_for_pilot`: dùng thông báo VSD có ngày từ năm 2023, observed history và current KBS listing. Phạm vi chỉ `[2023-01-01, 2026-01-01)`. Giả định không có ticker/exchange change trong khoảng này; đây chưa phải nationwide historical security master hoàn chỉnh. Listing date, sector và industry để `null` thay vì backfill dữ liệu hiện tại.
- `trading_status=normal` chỉ áp dụng khi quan sát thấy positive-volume EOD bar; điều này chỉ cho biết bar đủ điều kiện nghiên cứu giá, không đảm bảo mọi order có thể execute.
- `risk_free_method=assumption`, `rf_annual=0`; `corporate_actions` và `risk_free_rate` có thể rỗng. Không cộng thêm dividend cash flows vào adjusted level.
- Universe cố định gồm 10 mã còn tồn tại là selected universe, chưa phải survivorship-free market sample. `k=3`, features và costs được cố định trước khi xem performance.

Backtest là **vendor-adjusted price-return proxy**, dùng fractional units, transaction costs và cash. Kết quả chưa được chứng nhận là total return hoặc executable share accounting. Contract vẫn hỗ trợ pilot raw-price tương lai bằng `raw_close=close*price_multiplier`, `adj_close=null`, `adjustment_basis=unadjusted`; evidence KBS hiện tại không cho phép dùng mapping đó.

Chỉ corrupt OHLC, thiếu identity/trade date, integrity mismatch và required-table/QC failure mới block promotion. Các metadata tùy chọn về value, corporate action, risk-free hoặc publication time không block khi assumptions trên đã được khai báo.
