# SOURCE_SMOKE Data Manifest

> **Quy tắc sử dụng:** Private/local academic research và non-commercial demo; raw payload không được tái phân phối.  
> **Rights status:** `RIGHTS_NOT_VERIFIED` — `ACCEPTED_RESEARCH_RISK`  
> **Không commit/copy raw provider payload vào repository.**

---

## Thông tin run

| Thuộc tính | Giá trị |
|---|---|
| Run ID chính (canonical) | `source-smoke-20260916T111529Z-af9bc570` |
| Run ID bị loại bỏ (abandoned) | `source-smoke-20260916T111447Z-f4e3a695` |
| Lý do abandoned | Local false-positive guard: transport từ chối JSON của CafeF vì content-type không phải JSON; không phải lỗi provider. Run mới được tạo sau khi sửa parser. |
| Execution policy | `ACCEPTED_RESEARCH_RISK` |
| Concurrency | 1 |
| Min interval | 2.0 s |
| Timeout | 20 s |
| Attempts | 2 |
| Proxy / credential / bypass | Không dùng |

---

## Manifest — Dữ liệu thị trường (Market data)

> **Hướng dẫn đọc cột `Raw hash`:** Hash là SHA-256 của file `.json` tương ứng, lấy từ field `sha256` trong file `.metadata.json` đi kèm.  
> **Cột `Local raw path`:** Đường dẫn tương đối từ gốc workspace, không commit nội dung.  
> **CafeF:** Mỗi symbol có nhiều page artifacts (binary search); hash đại diện là page-001 (first confirmed page).  
> **KBS/Vnstock:** Mỗi symbol × window = 1 artifact.

### Bảng chính

| Provider | Acquisition client | Symbol | Dataset / domain | Window | Rows | Min date | Max date | Missing | Duplicates | Price basis | Units | Raw hash (đại diện) | Local raw path (đại diện) | Fetch status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kbs | vnstock | FPT | market / OHLCV | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `2addb54f8b006d36da5009dd0acc06f0499e8eb513b95cde81b6a7d756842d76` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/FPT-window_recent.json` | HTTP 200 OK |
| kbs | vnstock | FPT | market / OHLCV | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `06303186b5554d1f5e801051d562fafc8fb38e4e914b78635cd077e0de7b4d68` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/FPT-window_old.json` | HTTP 200 OK |
| cafef | direct | FPT | market / reference+limits | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `953a2e4aab1fd0fc7e5c6f3210f596738f96259d5861e148bb8dc825c35af977` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/FPT-page-001.json` | HTTP 200 OK |
| cafef | direct | FPT | market / reference+limits | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `953a2e4aab1fd0fc7e5c6f3210f596738f96259d5861e148bb8dc825c35af977` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/FPT-page-001.json` | HTTP 200 OK |
| kbs | vnstock | VNM | market / OHLCV | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `84b08f7007a7dc09d16910bfd0168625e06644a187636f2493f15cc093ad0bb5` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/VNM-window_recent.json` | HTTP 200 OK |
| kbs | vnstock | VNM | market / OHLCV | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `7024c88c72bac6d993ce65cc4e99eedc9b11248c94cfad3a43439d05807c4e76` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/VNM-window_old.json` | HTTP 200 OK |
| cafef | direct | VNM | market / reference+limits | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `f0e21c1356f2378782593036ec7576b7dbc8b567f3f056e9401bfdb3be0d045c` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/VNM-page-001.json` | HTTP 200 OK |
| cafef | direct | VNM | market / reference+limits — DQ FAIL | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `f0e21c1356f2378782593036ec7576b7dbc8b567f3f056e9401bfdb3be0d045c` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/VNM-page-001.json` | HTTP 200 OK — DQ FAIL |
| kbs | vnstock | PVS | market / OHLCV | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `1d0a4f254b249326355b293b652d0aead4766e4134f8f24e6e83fd21eb5d026b` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/PVS-window_recent.json` | HTTP 200 OK |
| kbs | vnstock | PVS | market / OHLCV | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `50c63ca101ba51baeb4abdc31cd5d0247b816221c62d595209775598e868bfcd` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/PVS-window_old.json` | HTTP 200 OK |
| cafef | direct | PVS | market / reference+limits | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `b26b350f5cd7d105aa657bf45b2f1b8e86081b44bc4e72736f363fbd96953166` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/PVS-page-001.json` | HTTP 200 OK |
| cafef | direct | PVS | market / reference+limits | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `b26b350f5cd7d105aa657bf45b2f1b8e86081b44bc4e72736f363fbd96953166` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/PVS-page-001.json` | HTTP 200 OK |
| kbs | vnstock | ACV | market / OHLCV | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `700d07d18273d927102e3495f46a18ead76fe5e18e59e367148f6b1af56eae8f` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/ACV-window_recent.json` | HTTP 200 OK |
| kbs | vnstock | ACV | market / OHLCV | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `ee5a0406bf69f9414ffcf0e31b843e646c3dd523a410bc9efc4bb703754bef75` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/ACV-window_old.json` | HTTP 200 OK |
| cafef | direct | ACV | market / reference+limits — VALUE_CONFLICT | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `a90cb58d14f72ee51642e480bff99470fa2676a3b5ae379232951e3879a89acb` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/ACV-page-001.json` | HTTP 200 OK — VALUE_CONFLICT |
| cafef | direct | ACV | market / reference+limits | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | REFERENCE x1000 VND/share | VND/share; value: raw VND | `a90cb58d14f72ee51642e480bff99470fa2676a3b5ae379232951e3879a89acb` | `data/raw/cafef/source-smoke-20260916T111529Z-af9bc570/ACV-page-001.json` | HTTP 200 OK |
| kbs | vnstock | VNINDEX | market / OHLC index | WINDOW_RECENT (2026-08-22..2026-09-15) | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | INDEX_POINTS | index points; vol: UNKNOWN | `4887dd267677a7da2ad56e0417b0f8b0842ac34edd459d4b7950e2d292d3f49a` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/VNINDEX-window_recent.json` | HTTP 200 OK |
| kbs | vnstock | VNINDEX | market / OHLC index | WINDOW_OLD (2021-09-03..2021-09-27) | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | INDEX_POINTS | index points; vol: UNKNOWN | `d6c2b8efc0dbd2ca9682995398ad27bc91378adbb9ec3ab7a7238f3f2314fcfe` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/VNINDEX-window_old.json` | HTTP 200 OK |

---

## Manifest — Dữ liệu tài chính (Financial raw-only)

> Chỉ có FPT được crawl financial. Không vào features, clustering hay backtest.

| Provider | Acquisition client | Symbol | Dataset / domain | Window | Rows | Min date | Max date | Missing | Duplicates | Price basis | Units | Raw hash | Local raw path | Fetch status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kbs | vnstock | FPT | financial / KQKD quarterly (raw-only) | 2026-09-16 (snapshot) | 3 obs | Q4/2025 | Q2/2026 | 0 | 0 | N/A | unit=1000 VND | `29a5b8e7f0e4ab8397a01a66505b92d21eac5d05cf2b7e695ee4703f3068ef79` | `data/raw/kbs/source-smoke-20260916T111529Z-af9bc570/FPT-financial-raw-only.json` | HTTP 200 OK — PIT_UNRESOLVED |

---

## Manifest — Abandoned run (bị loại bỏ)

> Run `f4e3a695` bị dừng sớm sau 2 request KBS vì lỗi transport local, không phải lỗi provider.  
> Artifacts vẫn tồn tại local, hash trùng với canonical run (cùng dữ liệu từ cùng một nguồn).

| Provider | Acquisition client | Symbol | Dataset / domain | Window | Rows | Min date | Max date | Missing | Duplicates | Price basis | Units | Raw hash | Local raw path | Fetch status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kbs | vnstock | FPT | market / OHLCV | WINDOW_RECENT | 14 | 2026-08-24 | 2026-09-15 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `2addb54f8b006d36da5009dd0acc06f0499e8eb513b95cde81b6a7d756842d76` | `data/raw/kbs/source-smoke-20260916T111447Z-f4e3a695/FPT-window_recent.json` | HTTP 200 OK (abandoned) |
| kbs | vnstock | FPT | market / OHLCV | WINDOW_OLD | 16 | 2021-09-06 | 2021-09-27 | 0 | 0 | VENDOR_ADJUSTED | VND/share; vol: shares | `06303186b5554d1f5e801051d562fafc8fb38e4e914b78635cd077e0de7b4d68` | `data/raw/kbs/source-smoke-20260916T111447Z-f4e3a695/FPT-window_old.json` | HTTP 200 OK (abandoned) |

---

## Ghi chú về data quality flags

| Flag | Symbol | Provider | Mô tả |
|---|---|---|---|
| DQ FAIL | VNM | cafef | Row 2021-09-09 WINDOW_OLD: `reference_price=85,400` nhưng `floor=194,400` và `ceiling=223,600` VND/share — vi phạm price-band relation. Lỗi required-field, không được sửa hay bỏ qua. |
| VALUE_CONFLICT | ACV | kbs vs cafef | Khối lượng KBS và CafeF không khớp trên 13/14 ngày chung WINDOW_RECENT. Chưa rõ nguyên nhân ngữ nghĩa (put-through volume?). Chưa reconcile. |
| PRICE_BASIS_CONFLICT | Tất cả | kbs vs cafef | KBS cung cấp adjusted OHLC; CafeF cung cấp reference/limit price. Hai basis khác nhau về bản chất — không so sánh trực tiếp, không overwrite. |
| PIT_UNRESOLVED | FPT financial | kbs | `published_at=null`, `available_at=null`; không xác định được PIT chính xác cho dữ liệu KQKD. |

---

## Inventory artifacts theo run

### Run canonical: `source-smoke-20260916T111529Z-af9bc570`

| Provider | Loại artifact | Số lượng file JSON | Số lượng metadata |
|---|---|---|---|
| kbs | market OHLCV (cổ phiếu) | 8 | 8 |
| kbs | market OHLC (index VNINDEX) | 2 | 2 |
| kbs | financial raw-only (FPT KQKD) | 1 | 1 |
| cafef | market pages (binary search) | 41 | 41 |
| **Tổng** | | **52** | **52** |

> Tổng 52 artifacts khớp với báo cáo trong `SOURCE_SMOKE_RESEARCH_DEMO_RESULT.md` ("41 CafeF pages và 11 KBS responses").

### Run abandoned: `source-smoke-20260916T111447Z-f4e3a695`

| Provider | Loại artifact | Số lượng file JSON | Số lượng metadata |
|---|---|---|---|
| kbs | market OHLCV (FPT only) | 2 | 2 |
| **Tổng** | | **2** | **2** |

---

## Phân tách CafeF artifacts theo symbol

> CafeF dùng bounded binary page search — số page artifacts không bằng số rows thực tế.

| Symbol | Pages fetched | Rows trong window | Ghi chú |
|---|---|---|---|
| FPT | 10 | 14 (recent) + 16 (old) | Pages: 001, 002, 005, 010, 020, 040, 042, 045, 050, 060 |
| VNM | 10 | 14 (recent) + 16 (old) | Pages: 001, 002, 005, 010, 020, 040, 042, 045, 050, 060 |
| PVS | 11 | 14 (recent) + 16 (old) | Pages: 001, 002, 005, 010, 020, 040, 041, 042, 045, 050, 060 |
| ACV | 10 | 14 (recent) + 16 (old) | Pages: 001, 002, 005, 010, 020, 040, 042, 045, 050, 060 |
| **Tổng** | **41** | | Khớp với báo cáo |

---

## Summary

| Chỉ số | Giá trị |
|---|---|
| Tổng artifacts (canonical run) | 52 JSON + 52 metadata = 104 files |
| Tổng rows market (KBS cổ phiếu) | 4 symbols x (14 recent + 16 old) = **120 rows** |
| Tổng rows market (KBS VNINDEX) | 14 recent + 16 old = **30 rows** |
| Tổng rows market (CafeF cổ phiếu) | 4 symbols x (14 recent + 16 old) = **120 rows** |
| Tổng rows financial (KBS FPT) | **3 observations** (Q4/2025, Q1/2026, Q2/2026) |
| Symbols | FPT (HOSE), VNM (HOSE), PVS (HNX), ACV (UPCOM), VNINDEX |
| Providers | kbs, cafef |
| Acquisition clients | vnstock (cho kbs), direct (cho cafef) |
| Smoke status | **FAIL** |
| Pilot readiness | **NOT_READY** |
| Blocking issue | VNM CafeF WINDOW_OLD price-band corruption (2021-09-09) |
| Open issue | ACV cross-source volume VALUE_CONFLICT chưa được giải quyết |

---

## Các field còn UNKNOWN

| Field | Artifact | Lý do |
|---|---|---|
| Units (volume) | VNINDEX (kbs) | Metadata không ghi rõ đơn vị volume của index — có thể là lot hoặc derived value |
| Min/Max date CafeF WINDOW_OLD | FPT, VNM, PVS, ACV | CafeF không tách window; date range WINDOW_OLD được xác nhận qua result.json (2021-09-06..2021-09-27) nhưng page-001 hash đại diện cho cả hai window |
| `published_at`, `available_at` | FPT financial | Metadata trả về null từ provider |

---

*File này chỉ ghi metadata và hash — không chứa raw provider payload. Cập nhật lần cuối: 2026-09-16.*
