# DELTA Provider-aware Source Comparison

## 1. Scope

Tài liệu này so sánh ba **acquisition path** đã được discovery/re-verification trong phạm vi DELTA M1 Data V2:

1. CafeF direct: `provider=cafef`, `acquisition_client=direct/public web request`.
2. TCBS via VietFin: `provider=tcbs`, `acquisition_client=vietfin`.
3. KBS via Vnstock: `provider=kbs`, `acquisition_client=vnstock`.

Đây là so sánh theo từng domain, không phải xếp hạng một “overall winner”. Kết luận chỉ xác định technical role và execution readiness. Nó không cấp quyền thu thập dữ liệu, không phê duyệt production, không thay thế source note, không triển khai adapter và không cho phép SOURCE_SMOKE khi P0 gap còn mở.

Nguồn bằng chứng duy nhất của phép so sánh là `CAFEF.md`, `VIETFIN.md`, `VNSTOCK.md` cùng các discovery-result tương ứng và các project contract đã chỉ định. Không có discovery mới, network request mới hay crawl lịch sử trong công việc này.

## 2. Compared acquisition paths

| Acquisition path | Provider | Client | Trạng thái quan sát | Phạm vi mạnh nhất đã quan sát | Ràng buộc chính |
|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct/public web request | Public access đã test; không yêu cầu login trong các request đã quan sát | Current security, current shares, historical market payload, corporate-action evidence, financial display | Automation/data rights `NOT_VERIFIED`; price basis chưa rõ; historical identity/shares và financial PIT còn thiếu |
| KBS via Vnstock | `kbs` | `vnstock` | Public KBS response đã test; Vnstock client có license restriction | Adjusted daily OHLCV, current board fields, financial structure/metadata, VNINDEX | KBS provider rights `NOT_VERIFIED`; thiếu historical ref/ceil/floor, traded value và trading status; financial PIT/revision chưa đủ |
| TCBS via VietFin | `tcbs` | `vietfin` | Client/docs đọc được; live provider route gặp access challenge và đã dừng | Interface/docs cho security, OHLCV, corporate actions, financials, VNINDEX | `BLOCKED_ACCESS`; provider rights, units, price basis và PIT đều chưa xác minh |

Mỗi record tương lai phải giữ riêng `provider` và `acquisition_client`; không được ghi VietFin hoặc Vnstock như thể đó là data provider gốc.

## 3. Decision vocabulary

Technical role chỉ dùng:

- `PRIMARY`: acquisition path có bằng chứng mạnh nhất cho domain cụ thể.
- `SECONDARY`: path có thể bổ sung dữ liệu hoặc metadata cho primary.
- `CROSS_CHECK`: path chỉ dùng để kiểm tra chéo, không tự động ghi đè canonical value.
- `DEFERRED`: path được giữ lại nhưng chưa đưa vào active work package.
- `UNRESOLVED`: chưa đủ bằng chứng để chọn technical role.

Execution readiness chỉ dùng:

- `READY`
- `BLOCKED_RIGHTS`
- `BLOCKED_ACCESS`
- `BLOCKED_SEMANTICS`
- `BLOCKED_MISSING_FIELDS`
- `DEFERRED`

Technical role không đồng nghĩa với execution approval. Khi nhiều path cùng có dữ liệu, conflict không được giải quyết bằng averaging, majority vote hoặc silent fallback.

## 4. Security comparison

### 4.1 Current security identity

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Có trên FPT, VNM, PVS, ACV | Ticker, company name, current exchange, industry và listing date có UI evidence | Không có stable provider security ID; status/delisting không đầy đủ | PRIMARY | BLOCKED_RIGHTS |
| KBS via Vnstock | `kbs` | `vnstock` | Có trên cả bốn symbol | Ticker, exchange và listing date nhất quán qua live response | Exact company name chưa xác minh; provider ID chỉ là candidate | SECONDARY | BLOCKED_RIGHTS |
| TCBS via VietFin | `tcbs` | `vietfin` | Docs/profile evidence hạn chế; live route bị chặn | Ticker, legal name, exchange, industry có trong interface/docs sample | Không xác minh live coverage bốn symbol; thiếu listing date và stable ID | DEFERRED | BLOCKED_ACCESS |

### 4.2 Historical security identity

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Không tìm thấy series lịch sử | Current exchange/listing metadata là mốc tham khảo | Không có ticker/exchange/status interval; không được suy ngược lịch sử từ profile hiện tại | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| KBS via Vnstock | `kbs` | `vnstock` | Không tìm thấy series lịch sử | Current identity có thể hỗ trợ đối chiếu hiện tại | Không có effective interval, rename/transfer/delisting history | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh được | Không có strength đủ để promote | Live access bị chặn và docs không chứng minh identity history | DEFERRED | BLOCKED_ACCESS |

## 5. Shares comparison

### 5.1 Current shares

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Current snapshot trên cả bốn symbol | Listed shares và outstanding shares có nhãn/đơn vị; PVS và ACV cho thấy hai khái niệm không luôn bằng nhau | Không có effective date/available date; thiếu issued/treasury | PRIMARY | BLOCKED_RIGHTS |
| KBS via Vnstock | `kbs` | `vnstock` | Current board snapshot | Listed shares `LS` có response evidence | Không có outstanding/issued/treasury và timing semantics | SECONDARY | BLOCKED_RIGHTS |
| TCBS via VietFin | `tcbs` | `vietfin` | Candidate fields trong docs | Có candidate `outstandingShare` và `issueShare` | Unit, timing, live value và field distinction chưa xác minh | DEFERRED | BLOCKED_ACCESS |

### 5.2 Shares history

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Không có verified historical series | Current snapshot có thể dùng làm evidence riêng biệt | Không có effective date, available date hay change history | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| KBS via Vnstock | `kbs` | `vnstock` | Không có verified historical share-count series | Charter-capital history đã được phân biệt khỏi share-count history | Không được quy đổi charter capital thành shares nếu thiếu denomination/effective semantics | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không có verified series | Không có | Access bị chặn; docs chỉ gợi ý current fields | DEFERRED | BLOCKED_ACCESS |

Kết luận domain: `CURRENT_SNAPSHOT_ONLY`. Không path nào được phép backfill current count vào lịch sử.

## 6. Daily market comparison

### 6.1 Historical OHLCV

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Live evidence trên FPT, VNM, PVS, ACV | Trade date, OHLC và volume; raw KBS price là VND/share, Vnstock stock normalization chia 1,000; volume là shares | Rights chưa xác minh; exact adjustment method không được mô tả | PRIMARY | BLOCKED_RIGHTS |
| CafeF direct | `cafef` | direct | Public paged history trên cả bốn symbol | Trade date, OHLC, close/adjusted-close candidates, volume và value fields; newest-first pagination được quan sát | Price basis chưa phân loại; không được map raw/adjusted | CROSS_CHECK | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Interface/docs only | OHLCV interface tồn tại | Live access bị chặn; unit và basis chưa xác minh | DEFERRED | BLOCKED_ACCESS |

### 6.2 Price basis

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Có explicit client documentation | `VENDOR_ADJUSTED`; canonical transform từ normalized stock price là `× 1,000` VND/share | Không đủ bằng chứng để gọi là split-adjusted hoặc total-return | PRIMARY | BLOCKED_RIGHTS |
| CafeF direct | `cafef` | direct | Raw fields hiển thị được | Có close và adjusted-close candidates | `UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET` | UNRESOLVED | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Docs interface only | Không có | Price basis và multiplier chưa xác minh | DEFERRED | BLOCKED_ACCESS |

### 6.3 Historical reference / ceiling / floor

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Current snapshot only | Current labels được quan sát | Không có historical fields trong payload đã xác minh | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| KBS via Vnstock | `kbs` | `vnstock` | Current board only | `RE`, `CL`, `FL` có current response evidence | Không có trong historical daily response | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Docs OHLCV không chứng minh các fields này; live blocked | DEFERRED | BLOCKED_ACCESS |

### 6.4 Historical traded value

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Có historical matched và negotiated values | Source unit được quan sát là billion VND; matched và negotiated tách riêng | Chưa có canonical policy: `traded_value` là matched-only hay total; không được cộng ngầm | PRIMARY | BLOCKED_SEMANTICS |
| KBS via Vnstock | `kbs` | `vnstock` | Current board only | `TV` và `PTV` có current evidence | Không có historical traded value trong daily response | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Docs OHLCV không đủ; live blocked | DEFERRED | BLOCKED_ACCESS |

### 6.5 Historical trading status

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Current status only | Có current display evidence | Không có per-date historical status | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| KBS via Vnstock | `kbs` | `vnstock` | Current board code only | Current `MS` code được quan sát | Code semantics và historical series chưa xác minh | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Live blocked; docs không chứng minh field | DEFERRED | BLOCKED_ACCESS |

### 6.6 Matched vs put-through semantics

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Historical payload tách matched và negotiated | Volume/value của hai nhóm có keys riêng và observed units | Chưa xác minh canonical inclusion policy và không được tự cộng | PRIMARY | BLOCKED_SEMANTICS |
| KBS via Vnstock | `kbs` | `vnstock` | Current board tách `PTQ`/`PTV` khỏi current totals | Có thể cross-check current snapshot | Historical daily response thiếu put-through fields | CROSS_CHECK | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Live blocked; docs không đủ | DEFERRED | BLOCKED_ACCESS |

## 7. Corporate-actions comparison

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Public list/article/source-document evidence | FPT cash-dividend example có event type, publication candidate, ex-date, cash amount và HOSE source PDF | Record/effective/payment dates không đủ trong example; ratio/rights normalization chưa hoàn tất; rights chưa xác minh | PRIMARY | BLOCKED_SEMANTICS |
| KBS via Vnstock | `kbs` | `vnstock` | Event endpoint trả empty cho cả bốn symbol đã kiểm tra | Endpoint behavior được ghi nhận | Không có event row để xác minh field semantics hoặc coverage | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Corporate-action model trong docs | Candidate dates/type/payment fields có schema evidence | Không có live FPT event; cash percentage, rights terms, source document và revision semantics chưa xác minh | DEFERRED | BLOCKED_ACCESS |

CafeF direct là technical primary cho evidence hiện tại, nhưng chưa phải final source-of-truth và chưa đủ để normalize mọi event type.

## 8. Financial-statements comparison

### 8.1 Statement structure and fact coverage

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Quarterly/annual IS, BS, CF; live FPT structure và quarterly IS trên bốn symbol | Explicit report type, period metadata, scope/audit codes và raw fact values | Rights chưa xác minh; stable provider report ID chưa có | PRIMARY | BLOCKED_RIGHTS |
| CafeF direct | `cafef` | direct | Quarterly/annual IS, BS, CF trên UI | Broad raw-fact candidates; four periods/page; unit scale labels | Fact-to-report identity, period boundaries, PIT và revision chưa đủ | SECONDARY | BLOCKED_RIGHTS |
| TCBS via VietFin | `tcbs` | `vietfin` | Interface/docs support ba statements | Fiscal year/quarter fields có docs evidence | Live blocked; scope, timing, currency/unit và report identity chưa xác minh | DEFERRED | BLOCKED_ACCESS |

### 8.2 Period boundaries

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Có start/end month fields | Q2 income-statement example có boundary 2026-04 đến 2026-06 | Q3 chưa xác minh do pagination/duplicate behavior | PRIMARY | BLOCKED_RIGHTS |
| CafeF direct | `cafef` | direct | Period labels có trên UI | Fiscal quarter/year hiển thị | Period start/end chưa sẵn sàng để canonical map | UNRESOLVED | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Fiscal labels only | Year/quarter interface tồn tại | Không có verified period boundaries | DEFERRED | BLOCKED_ACCESS |

### 8.3 Scope / audit metadata

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Explicit response codes | Scope codes `HN`/`DL`/`CTM` và audit status đã quan sát | Meaning/version governance vẫn cần preserve raw codes | PRIMARY | BLOCKED_RIGHTS |
| CafeF direct | `cafef` | direct | Visible trong linked documents | Consolidated/separate và audit evidence có ở document level | Chưa link chắc chắn từng fact row với document metadata | SECONDARY | BLOCKED_RIGHTS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không đủ evidence | Không có | Docs/live evidence không xác minh scope/audit | DEFERRED | BLOCKED_ACCESS |

### 8.4 Currency / unit scale

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Raw values và transform được đối chiếu | Raw monetary values là thousand VND; canonical transform `× 1,000`; currency confidence MEDIUM | Currency chưa có explicit per-report field | PRIMARY | BLOCKED_RIGHTS |
| CafeF direct | `cafef` | direct | UI labels | VND và scale 1e9/1e6 được xác minh theo display | Scale phải gắn từng table/report, không suy rộng im lặng | SECONDARY | BLOCKED_RIGHTS |
| TCBS via VietFin | `tcbs` | `vietfin` | Chưa xác minh | Không có | Currency/unit scale không được chứng minh bởi live response | DEFERRED | BLOCKED_ACCESS |

### 8.5 Publication timing / PIT

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Timestamp candidates có trong response | `DatePubDepartment`, `CreatedDate`, `LastUpdate` được quan sát | Chưa biết field nào là canonical `published_at`/`available_at`; timezone/PIT semantics chưa đủ | UNRESOLVED | BLOCKED_SEMANTICS |
| CafeF direct | `cafef` | direct | Publication/document dates có thể xuất hiện | Có document-level timing candidates | Không đủ để gắn từng report/fact với first-public availability | UNRESOLVED | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Live blocked; docs không chứng minh PIT | DEFERRED | BLOCKED_ACCESS |

### 8.6 Revision / restatement

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | `LastUpdate` candidate only | Có thể lưu raw timestamp | Không có revision ID, version chain hoặc restatement meaning | UNRESOLVED | BLOCKED_SEMANTICS |
| CafeF direct | `cafef` | direct | Không có verified revision chain | Source documents có thể lưu làm evidence | Không xác minh revision/restatement behavior | UNRESOLVED | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Live blocked; docs không đủ | DEFERRED | BLOCKED_ACCESS |

### 8.7 Q2/Q3 income-statement semantics

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Partial | Q2 boundary trực tiếp chỉ ra 2026-04 đến 2026-06 cho observed row | Q3 chưa xác minh; không được suy từ arithmetic | CROSS_CHECK | BLOCKED_SEMANTICS |
| CafeF direct | `cafef` | direct | UI có quarterly và 6M views | Sự tồn tại của view riêng là evidence hữu ích | `UNKNOWN — DO NOT MAP YET`; không promote từ arithmetic | UNRESOLVED | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | `UNKNOWN — DO NOT MAP YET`; live blocked | DEFERRED | BLOCKED_ACCESS |

Kết luận liên-provider: `UNKNOWN — DO NOT MAP YET` cho yêu cầu Q2/Q3 đầy đủ.

### 8.8 Q2/Q3 cash-flow semantics

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Structure exists; observed Q2 values empty | Không có strength đủ để promote | Q2 values empty, Q3 chưa xác minh | UNRESOLVED | BLOCKED_SEMANTICS |
| CafeF direct | `cafef` | direct | Quarterly CF display exists | Repeated observation gợi ý cumulative presentation | `UNKNOWN — DO NOT MAP YET`; arithmetic không phải semantic proof | UNRESOLVED | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | `UNKNOWN — DO NOT MAP YET`; live blocked | DEFERRED | BLOCKED_ACCESS |

Kết luận liên-provider: `UNKNOWN — DO NOT MAP YET`.

### 8.9 Weighted-average shares

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Không tìm thấy | Không có | Basic/diluted weighted-average shares chưa có | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| KBS via Vnstock | `kbs` | `vnstock` | Không tìm thấy | Không có | Basic/diluted weighted-average shares chưa có | UNRESOLVED | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không xác minh | Không có | Live blocked; docs không chứng minh fields | DEFERRED | BLOCKED_ACCESS |

## 9. Benchmark / trading-calendar comparison

### 9.1 VNINDEX

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| KBS via Vnstock | `kbs` | `vnstock` | Live historical index levels | Trade dates và point levels được quan sát | Index basis/methodology/PIT chưa xác minh; rights chưa xác minh | PRIMARY | BLOCKED_SEMANTICS |
| CafeF direct | `cafef` | direct | Public history available | Có date/level evidence để cross-check | Basis/methodology còn partial và có observed anomaly cần giữ làm evidence | CROSS_CHECK | BLOCKED_SEMANTICS |
| TCBS via VietFin | `tcbs` | `vietfin` | Interface/docs indicate availability | Có candidate index interface | Live path bị chặn; unit/basis chưa xác minh | DEFERRED | BLOCKED_ACCESS |

### 9.2 Exchange trading calendar

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Document-level holiday notice only | Public HOSE notice có thể làm evidence cho một closure | Không có authoritative structured multi-exchange calendar | CROSS_CHECK | BLOCKED_MISSING_FIELDS |
| KBS via Vnstock | `kbs` | `vnstock` | Client-maintained dictionary partial | Có một số past events | Không phải authoritative provider calendar; không chứng minh future schedule | CROSS_CHECK | BLOCKED_MISSING_FIELDS |
| TCBS via VietFin | `tcbs` | `vietfin` | Không tìm thấy | Không có | Live blocked và docs không chỉ ra calendar | DEFERRED | BLOCKED_ACCESS |

## 10. Rights / access comparison

| Acquisition path | Provider | Client | Availability | Verified strengths | Main gaps | Technical role | Execution readiness |
|---|---|---|---|---|---|---|---|
| CafeF direct | `cafef` | direct | Ordinary public pages/requests hoạt động trong bounded observations | Không cần login/CAPTCHA trong evidence đã ghi | Automation/data reuse rights là `NOT_VERIFIED`; public access không tự động là automation permission | UNRESOLVED | BLOCKED_RIGHTS |
| KBS via Vnstock | `kbs` | `vnstock` | Ordinary public KBS responses hoạt động | Acquisition route và provenance tách được | Vnstock client license là `RESTRICTED`; KBS provider rights `NOT_VERIFIED` | UNRESOLVED | BLOCKED_RIGHTS |
| TCBS via VietFin | `tcbs` | `vietfin` | VietFin client/docs public | Client licensing/docs có thể đọc | Live TCBS route gặp managed challenge; provider rights `NOT_VERIFIED`; không bypass | DEFERRED | BLOCKED_ACCESS |

Không path nào hiện đạt execution readiness `READY` cho automated collection. Silence trong Terms không được diễn giải thành permission.

## 11. Domain selection matrix

| Domain | PRIMARY | SECONDARY | CROSS_CHECK | Deferred/Unresolved | Readiness | Reason |
|---|---|---|---|---|---|---|
| Security current | CafeF direct | KBS via Vnstock | — | TCBS via VietFin deferred | BLOCKED_RIGHTS | CafeF có identity labels rộng nhất; KBS xác nhận ticker/exchange/listing date |
| Security historical | UNRESOLVED | — | — | Cả ba path | BLOCKED_MISSING_FIELDS | Không path nào chứng minh effective identity intervals |
| Shares current | CafeF direct | KBS via Vnstock | — | TCBS via VietFin deferred | BLOCKED_RIGHTS | CafeF phân biệt listed và outstanding; KBS chỉ cross-domain bổ sung listed snapshot |
| Shares history | UNRESOLVED | — | — | Cả ba path | BLOCKED_MISSING_FIELDS | Không có effective/available-dated share-count series |
| Daily OHLCV | KBS via Vnstock | CafeF direct | — | TCBS via VietFin deferred | BLOCKED_RIGHTS | KBS có explicit adjusted basis và verified VND/share transform |
| Price basis | KBS via Vnstock | — | CafeF direct sau khi phân loại basis | TCBS via VietFin deferred | BLOCKED_RIGHTS | Chỉ KBS/Vnstock có explicit `VENDOR_ADJUSTED` evidence |
| Historical ref/ceil/floor | UNRESOLVED | — | — | Cả ba path | BLOCKED_MISSING_FIELDS | Chỉ có current snapshot trên CafeF/KBS |
| Historical traded value | CafeF direct | — | KBS current snapshot only | TCBS via VietFin deferred | BLOCKED_SEMANTICS | CafeF có historical matched/negotiated values nhưng canonical inclusion chưa quyết định |
| Historical trading status | UNRESOLVED | — | — | Cả ba path | BLOCKED_MISSING_FIELDS | Không có verified per-date status series |
| Corporate actions | CafeF direct | — | — | KBS unresolved; TCBS deferred | BLOCKED_SEMANTICS | CafeF có FPT evidence nhưng event-date/term normalization chưa hoàn chỉnh |
| Financial structure | KBS via Vnstock | CafeF direct | — | TCBS via VietFin deferred | BLOCKED_RIGHTS | KBS có explicit structure/metadata; CafeF có broad fact display |
| Financial period boundaries | KBS via Vnstock | — | CafeF direct | TCBS via VietFin deferred | BLOCKED_RIGHTS | KBS có observed start/end metadata; CafeF chỉ đủ làm period-label check |
| Financial PIT | UNRESOLVED | — | KBS và CafeF candidates | TCBS via VietFin deferred | BLOCKED_SEMANTICS | Chưa có canonical `published_at`/`available_at` với timezone semantics |
| Financial revision | UNRESOLVED | — | — | Cả ba path | BLOCKED_SEMANTICS | Không có verified revision chain/restatement semantics |
| Q2/Q3 IS semantics | UNRESOLVED | — | KBS Q2 partial; CafeF UI structure | TCBS via VietFin deferred | BLOCKED_SEMANTICS | Q3 chưa được chứng minh; không suy từ arithmetic |
| Q2/Q3 CF semantics | UNRESOLVED | — | CafeF display only | KBS incomplete; TCBS deferred | BLOCKED_SEMANTICS | `UNKNOWN — DO NOT MAP YET` |
| Weighted-average shares | UNRESOLVED | — | — | Cả ba path | BLOCKED_MISSING_FIELDS | Không tìm thấy verified basic/diluted weighted-average shares |
| VNINDEX | KBS via Vnstock | CafeF direct | — | TCBS via VietFin deferred | BLOCKED_SEMANTICS | Có levels nhưng basis/methodology/PIT chưa đủ |
| Trading calendar | UNRESOLVED | — | CafeF notice; Vnstock dictionary | TCBS via VietFin deferred | BLOCKED_MISSING_FIELDS | Không có authoritative structured exchange calendar |

Các lựa chọn trên là technical candidates. Không domain nào được gọi là final source-of-truth trước khi quyền, gap và reconciliation rules tương ứng được giải quyết.

## 12. Gap Register

| Gap ID | Severity | Domain | Missing/uncertain item | Why it matters | Current evidence | Blocking stage | Required next action |
|---|---|---|---|---|---|---|---|
| GAP-001 | P0 | Provider/access rights | Automation/data reuse rights cho CafeF và KBS chưa xác minh; Vnstock client restricted | Real SOURCE_SMOKE tạo automated public requests và evidence artifacts; public access không đủ làm permission | CafeF/KBS access hoạt động nhưng source notes ghi `NOT_VERIFIED`; Vnstock ghi `RESTRICTED` | SOURCE_SMOKE | Xác minh public policy/permission áp dụng cho đúng provider/client path hoặc chọn approved source |
| GAP-002 | P0 | Daily market | Historical reference/ceiling/floor | Là exact fields của intended SOURCE_SMOKE và cần cho limit-rule validation | CafeF và KBS chỉ có current snapshot; TCBS blocked | SOURCE_SMOKE | Targeted gap-source discovery cho historical fields, không suy từ close hay price band |
| GAP-003 | P0 | Daily market | Canonical historical `traded_value` definition và matched/put-through inclusion | SOURCE_SMOKE yêu cầu traded value; cộng hoặc chọn sai làm hỏng canonical semantics | CafeF tách matched/negotiated values; KBS chỉ current `TV`/`PTV` | SOURCE_SMOKE | Chốt canonical policy dựa trên explicit provider/exchange evidence và verify unit/transform |
| GAP-004 | P0 | Financial PIT | `published_at`/`available_at`, timezone và first-public semantics | DELTA chỉ dùng fact available trước decision time; SOURCE_SMOKE phải kiểm tra timing | KBS có timestamp candidates; CafeF có document dates; không path nào đủ canonical | SOURCE_SMOKE | Targeted timing discovery trên ít nhất ba quarterly reports và định nghĩa immutable PIT evidence |
| GAP-005 | P1 | Daily market | Historical `trading_status` và code semantics | Cần phân biệt halt/suspension/no-trade khỏi missing data | CafeF chỉ current display; KBS chỉ current `MS`; TCBS blocked | REPRESENTATIVE_PILOT | Tìm explicit per-date status source/codebook; giữ unmapped đến khi xác minh |
| GAP-006 | P1 | Shares | Historical counts với `effective_date` và `available_at` | Current snapshot không tái tạo được denominator lịch sử | Cả CafeF/KBS chỉ current snapshot; TCBS không xác minh | CANONICAL_PROMOTION | Targeted gap-source discovery cho share-count events/series có timing semantics |
| GAP-007 | P1 | Financial revision | Revision/restatement ID, ordering và availability | Không thể bảo đảm PIT và reproducibility khi report đổi | KBS chỉ có `LastUpdate` candidate; CafeF/TCBS không có version chain | CANONICAL_PROMOTION | Xác minh report identity và revision lineage; lưu raw versions, không overwrite |
| GAP-008 | P1 | Financial IS | Q2/Q3 standalone-vs-YTD đầy đủ | Mapping sai làm sai revenue/profit duration facts | KBS chứng minh Q2 boundary partial; Q3 chưa xác minh; CafeF overall unknown | REPRESENTATIVE_PILOT | Quan sát explicit Q2 và Q3 labels/boundaries từ cùng report family |
| GAP-009 | P1 | Financial CF | Q2/Q3 standalone-vs-YTD | Cash-flow duration semantics thường khác income statement và không được suy bằng arithmetic | CafeF chỉ repeated display signal; KBS Q2 empty, Q3 chưa xác minh | REPRESENTATIVE_PILOT | Tìm explicit provider label/docs cho Q2 và Q3 CF; nếu không có, giữ unmapped |
| GAP-010 | P1 | Trading calendar | Authoritative structured HOSE/HNX/UPCOM calendar | Cần xác định expected trading days và tránh coi holiday là missing | CafeF có một notice; Vnstock có client dictionary; TCBS không có | CANONICAL_PROMOTION | Dùng official exchange calendar hoặc official notices với documented construction rules |
| GAP-011 | P1 | Security | Historical ticker/exchange/status identity | Current profile không chứng minh historical universe eligibility | Cả ba path không có effective intervals | CANONICAL_PROMOTION | Targeted identity-history source discovery; không backfill current identity |
| GAP-012 | P1 | Financial identity | Stable provider report ID | Cần deduplicate, link facts và revisions mà không dùng canonical ID thay thế provider ID | KBS/CafeF structures chưa cung cấp verified stable report identifier | CANONICAL_PROMOTION | Xác minh provider-native report/document identity và preserve raw ID |
| GAP-013 | P1 | Corporate actions | Complete canonical dates/terms cho event types | Ex-date/cash example chưa đủ normalize record/effective/payment/rights terms | CafeF FPT example mạnh nhất nhưng thiếu một số dates; KBS empty; TCBS blocked | REPRESENTATIVE_PILOT | Verify one complete event per intended type từ public source document |
| GAP-014 | P1 | Benchmark | VNINDEX basis/methodology/PIT | Levels có thể so được nhưng chưa đủ canonical benchmark semantics | KBS và CafeF có levels; basis/methodology chưa xác minh | CANONICAL_PROMOTION | Xác minh official methodology/basis và publication timing; giữ raw provenance |
| GAP-015 | P1 | Market microstructure | Historical matched-vs-put-through interpretation | Volume/value conflict có thể phát sinh nếu một path báo matched-only và path khác báo total | CafeF tách fields; KBS chỉ current snapshot tách `PTQ`/`PTV` | RECONCILIATION | Xác minh definitions và lưu components riêng; không cộng/average ngầm |
| GAP-016 | P2 | Financial facts | Weighted-average basic/diluted shares | Hữu ích cho per-share analytics nhưng không phải điều kiện tối thiểu của bounded smoke hiện tại | Không path nào tìm thấy verified fields | CANONICAL_PROMOTION | Giữ optional/unmapped; discovery riêng chỉ khi model cần fact này |
| GAP-017 | P2 | Deferred path | TCBS via VietFin live access | Path có thể bổ sung redundancy nhưng không cần để chọn current technical candidates | Managed challenge trên bốn symbols; đã dừng đúng access boundary | DEFERRED_PATH | Chỉ revisit khi có documented legitimate public/API access; không bypass challenge |

Không gap nào được coi là resolved trong tài liệu này.

## 13. Reconciliation plan

Reconciliation chỉ áp dụng sau khi path liên quan được quyền sử dụng và field semantics đủ rõ. Mọi raw record phải giữ `provider`, `acquisition_client`, request metadata, observation time và evidence hash.

| Domain | Primary field source | Secondary / cross-check | Comparison fields | Expected conflict types | Fields never averaged |
|---|---|---|---|---|---|
| Security current | CafeF direct | KBS via Vnstock | ticker, current exchange, listing date; company name chỉ so khi exact source label có mặt | IDENTITY_CONFLICT, TIMING_CONFLICT, MISSING_ON_SOURCE | Ticker, exchange, company name, listing date, provider ID |
| Shares current | CafeF direct | KBS via Vnstock | Listed shares trên cùng observation date; outstanding chỉ so khi source thứ hai có đúng semantics | VALUE_CONFLICT, TIMING_CONFLICT, MISSING_ON_SOURCE | Listed, outstanding, issued, treasury shares |
| Daily OHLCV | KBS via Vnstock | CafeF direct chỉ như raw cross-check cho date/volume; price chờ CafeF basis | Trade date, volume; OHLC chỉ so sau khi unit và basis cùng loại | VALUE_CONFLICT, UNIT_CONFLICT, PRICE_BASIS_CONFLICT, TIMING_CONFLICT, MISSING_ON_SOURCE | Mọi price, volume và value field |
| Historical traded value | CafeF direct sau GAP-003 | KBS current snapshot không dùng thay historical | Matched value, negotiated value và total chỉ so theo cùng definition/date | VALUE_CONFLICT, UNIT_CONFLICT, MISSING_ON_SOURCE | Matched value, negotiated value, total traded value |
| Financial structure/facts | KBS via Vnstock | CafeF direct | Report type, fiscal labels, period boundaries, scope, audit, unit/currency và same-line facts sau khi align report identity | VALUE_CONFLICT, UNIT_CONFLICT, TIMING_CONFLICT, IDENTITY_CONFLICT, MISSING_ON_SOURCE | Financial facts, dates, scope/audit flags, revision values |
| VNINDEX | KBS via Vnstock | CafeF direct | Date và level chỉ sau khi basis/methodology tương thích | VALUE_CONFLICT, PRICE_BASIS_CONFLICT, TIMING_CONFLICT, MISSING_ON_SOURCE | Index level |

Conflict handling:

- `VALUE_CONFLICT`: giữ cả raw observations, không chọn bằng average; chỉ promote sau khi tìm được provider definition/timing phù hợp.
- `UNIT_CONFLICT`: dừng mapping cho đến khi có explicit unit và transform evidence.
- `PRICE_BASIS_CONFLICT`: không so hoặc merge raw/adjusted series; giữ series tách biệt.
- `TIMING_CONFLICT`: so `effective_at` và `available_at` riêng; không dùng timestamp mới hơn để sửa ngược PIT row.
- `IDENTITY_CONFLICT`: không majority vote; cần authoritative identity interval hoặc source document.
- `MISSING_ON_SOURCE`: không zero-fill và không forward-fill; ghi missing theo provenance.

Corporate actions chưa có hai usable paths nên không đặt reconciliation rule liên-provider. CafeF evidence được giữ nguyên, không dùng KBS empty response để phủ định event.

## 14. Adapter work packages

Các work package dưới đây chỉ là bounded technical decomposition. Tất cả vẫn `BLOCKED`; không work package nào là quyền triển khai ngay.

| WP | Provider/client path | Domain | What to implement | Preconditions | Must stay fail-closed for | Status |
|---|---|---|---|---|---|---|
| WP-A | `provider=kbs`, `acquisition_client=vnstock` | Adjusted daily OHLCV và VNINDEX raw ingest | Bounded request wrapper, explicit VND/share transform, provenance manifest, raw payload/hash preservation | Resolve GAP-001; pin/record client version; define request/date/pagination contract | Historical ref/ceil/floor, historical traded value/status, unknown index basis, any non-adjusted interpretation | BLOCKED |
| WP-B | `provider=cafef`, `acquisition_client=direct` | Current security, current shares, corporate-action evidence và historical value components | Resolve GAP-001; resolve GAP-003 trước canonical traded value; define event/report IDs and request contract | Historical identity/shares, unknown price basis, missing corporate-action dates/terms, financial PIT | BLOCKED |
| WP-C | `provider=kbs`, `acquisition_client=vnstock` | Financial report structure/metadata raw ingest | Resolve GAP-001; establish provider report identity; preserve raw scope/audit/unit/timestamps | Canonical `available_at`, revisions, Q3 IS semantics, Q2/Q3 CF semantics, weighted-average shares | BLOCKED |

TCBS via VietFin không có active WP vì path đang `BLOCKED_ACCESS` và chưa đủ rights/semantics evidence. Không tạo một mega-adapter gộp provider/client provenance.

## 15. SOURCE_SMOKE readiness

| Requirement | Status | Evidence/source | Blocking gap |
|---|---|---|---|
| Legitimate automation/data rights | BLOCKED | CafeF/KBS rights `NOT_VERIFIED`; Vnstock client `RESTRICTED`; TCBS access blocked | GAP-001 |
| 3–5 symbols across exchanges | READY | FPT/VNM/PVS/ACV đã có bounded evidence qua HOSE/HNX/UPCOM trên CafeF và KBS | — |
| >=5y requested history capability | PARTIAL | Vnstock docs ghi daily capability khoảng tám năm; chưa chạy real five-year request trong task này | Sau P0 mới được exercise trong SOURCE_SMOKE |
| OHLC semantics | READY | KBS raw VND/share + Vnstock `×1,000` inverse normalization; `VENDOR_ADJUSTED` | — |
| Reference/ceiling/floor | BLOCKED | Chỉ current snapshot, không có historical series | GAP-002 |
| Volume/traded_value | PARTIAL | Volume=shares verified; CafeF historical value components có unit nhưng canonical inclusion chưa chốt | GAP-003 |
| Trading_status | BLOCKED | Current-only evidence; không có historical code/series | GAP-005 |
| Price basis | READY | KBS via Vnstock là `VENDOR_ADJUSTED`; không gọi split/total-return | — |
| Provenance | PARTIAL | Provider/client attribution đã xác định; adapter manifest/raw evidence hash chưa được triển khai | WP-A/WP-B/WP-C |
| Corporate-action evidence | READY | CafeF có public FPT cash-dividend example và source document | GAP-013 chỉ chặn canonical normalization đầy đủ |
| >=3 quarterly financial reports | READY | CafeF display có bốn quý liên tiếp; KBS có quarterly statement structure/live rows | — |
| Financial timing/PIT | BLOCKED | Timestamp candidates chưa thành canonical `available_at` | GAP-004 |

**SOURCE_SMOKE final status: NOT_READY.** Bốn P0 gap còn mở; đặc biệt quyền, historical limit fields, traded-value semantics và financial PIT không thể được xử lý bằng giả định trong smoke.

## 16. Deferred paths

| Path | Status | Reason | Revisit trigger |
|---|---|---|---|
| TCBS via VietFin | DEFERRED | Live provider route `BLOCKED_ACCESS`; rights/unit/basis/PIT chưa xác minh | Có documented legitimate public/API route và rights evidence; không bypass challenge |
| KBS corporate actions via Vnstock | DEFERRED | Event endpoint empty trên bốn symbols nên chưa có semantic sample | Provider/client trả public event row có thể cross-check bằng source document |
| CafeF historical prices as canonical OHLC | DEFERRED | Price basis `UNKNOWN — DO NOT MAP AS RAW/ADJUSTED YET` | Explicit CafeF definition hoặc direct UI-response evidence phân loại basis |
| Current shares snapshot used as history | DEFERRED | Không có effective/available dates; backfill sẽ tạo look-ahead error | Verified historical series hoặc event-derived counts với timing evidence |
| Vnstock calendar dictionary as canonical calendar | DEFERRED | Client-maintained partial past events, không authoritative/future-complete | Official exchange evidence và documented construction procedure |

Deferred không có nghĩa là evidence bị xóa. Raw notes và access-boundary observations vẫn phải được bảo toàn để tránh lặp lại request hoặc diễn giải sai.

## 17. Final conclusions

- CafeF direct là technical `PRIMARY` cho current security, current shares, corporate-action evidence và historical traded-value components; chưa `READY` vì rights và semantic gaps.
- KBS via Vnstock là technical `PRIMARY` cho adjusted daily OHLCV, financial structure/metadata và VNINDEX; chưa `READY` vì rights cùng các required historical/PIT gaps.
- TCBS via VietFin là `DEFERRED` do `BLOCKED_ACCESS`; không có active adapter work package.
- Historical security, shares history, historical ref/ceil/floor, historical trading status, financial PIT/revision, complete Q2/Q3 semantics, weighted-average shares và authoritative trading calendar vẫn `UNRESOLVED`.
- Không path nào là final source-of-truth cho toàn bộ DELTA. Không average conflict, không forward-fill current facts vào history và không trộn price basis.
- Adapter implementation và SOURCE_SMOKE đều chưa được phép tiếp tục theo trạng thái hiện tại; phải giải quyết P0 gaps trước.

