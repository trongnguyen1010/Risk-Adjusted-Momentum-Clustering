# Kết quả REAL REPRESENTATIVE_PILOT

## Kết luận

`REPRESENTATIVE_PILOT=PASS` qua offline immutable QC replay của real acquisition run `representative-pilot-20260916T185530Z-410ffcba`. Acquisition hoàn tất `839/839` jobs; replay xác minh toàn bộ provider artifact checksum, không gọi network và không sửa raw. PASS chỉ unlock planning `M1_SCALE`; chưa chạy scale, chưa mở financial features và không xác nhận production licensing.

## Identity và coverage

- range: `2020-01-01 .. 2026-09-15`; selected: `55` (`HOSE=40`, `HNX=8`, `UPCOM=7`), `16` sectors;
- config hash: `b248a4771c8077e0a38004c7a672f8e780f88f16f6b9c5c37c6331b2f4c1856e`;
- universe hash: `b343439255eb7854647e84f17afac7e34d484d6790a1d3aca99b6405500ebc4d`;
- SOURCE_SMOKE gate hash: `6ac01c5e3efce8dd818f3e6d6e97ea53f5b4de0544c1972eaa56d32482f71c7e`;
- QC policy hash: `0234a6fc49eb627b1779e334bc05bc3d4bb0b54b2b634fd6fa965bf9c3851261`;
- usable >=5y: `55/55`; usable >=3y clustering: `55/55`; reference-only: `0`;
- failed symbols: `0`; quarantined rows: `51`; provider volume conflicts: `6`;
- VNINDEX: `PASS`, `1667` eligible rows;
- financial PIT: `PIT_UNRESOLVED`; `financial_features_allowed=false`;
- rights/execution: `RIGHTS_NOT_VERIFIED` / `ACCEPTED_RESEARCH_RISK`; raw redistribution disabled.

KBS là primary OHLCV/benchmark và đáp ứng >=5 năm cho toàn bộ universe. CafeF là source phụ cho limits/value/volume semantics; 53 mã có `PARTIAL_SOURCE_EXHAUSTED`, được giữ source-qualified và không dùng làm history-depth của primary series. Không KBS/CafeF averaging hoặc canonical volume merge.

Policy [representative_pilot.qc_policy.v1.json](../../configs/data/representative_pilot.qc_policy.v1.json) chỉ `EXCLUDE_ROW` khi provider, ticker, trade date và SHA-256 exact raw row cùng khớp. Có `21` KBS OHLC-invariant violations (gồm 3 VNINDEX) và `30` CafeF price-band violations. Rule thiếu/thừa, raw thay đổi hoặc invalid row chưa review đều dừng replay; raw evidence vẫn bất biến.

## Per-symbol result

|Ticker|Exch.|Sector|Min|Max|KBS|CafeF|5y|QC|Volume|
|---|---|---|---|---|---:|---:|---|---|---|
|AAA|HOSE|Chemicals|2020-01-02|2026-09-15|1670|209|Y|PASS|MATCHED|
|ACB|HOSE|Banks|2020-01-02|2026-09-15|1665|29|Y|PASS|MATCHED|
|ACV|UPCOM|Industrial Goods & Services|2020-01-02|2026-09-15|1661|179|Y|PASS|UNRESOLVED|
|ANV|HOSE|Food & Beverage|2020-01-02|2026-09-15|1670|359|Y|PASS|MATCHED|
|BCC|HNX|Construction & Materials|2020-01-02|2026-09-15|1670|509|Y|PASS|MATCHED|
|BCM|HOSE|Real Estate|2020-01-03|2026-09-15|1660|149|Y|PASS|MATCHED|
|BID|HOSE|Banks|2020-01-02|2026-09-15|1670|29|Y|PASS|MATCHED|
|BMP|HOSE|Construction & Materials|2020-01-02|2026-09-15|1670|1664|Y|PASS|MATCHED|
|BVH|HOSE|Insurance|2020-01-02|2026-09-15|1670|659|Y|PASS|MATCHED|
|CII|HOSE|Construction & Materials|2020-01-02|2026-09-15|1670|479|Y|PASS|MATCHED|
|CMG|HOSE|Technology|2020-01-02|2026-09-15|1670|629|Y|PASS|MATCHED|
|CTG|HOSE|Banks|2020-01-02|2026-09-15|1670|659|Y|PASS|MATCHED|
|CTR|HOSE|Construction & Materials|2020-01-02|2026-09-15|1663|269|Y|PASS|MATCHED|
|DCM|HOSE|Chemicals|2020-01-02|2026-09-15|1670|209|Y|PASS|MATCHED|
|DGC|HOSE|Chemicals|2020-01-02|2026-09-15|1664|479|Y|PASS|MATCHED|
|DGW|HOSE|Retail|2020-01-02|2026-09-15|1670|329|Y|PASS|MATCHED|
|DHG|HOSE|Health Care|2020-01-02|2026-09-15|1670|838|Y|PASS|MATCHED|
|DPM|HOSE|Chemicals|2020-01-02|2026-09-15|1670|1049|Y|PASS|MATCHED|
|FPT|HOSE|Technology|2020-01-02|2026-09-15|1670|359|Y|PASS|MATCHED|
|FRT|HOSE|Retail|2020-01-02|2026-09-15|1670|1645|Y|PASS|MATCHED|
|GAS|HOSE|Utilities|2020-01-02|2026-09-15|1670|868|Y|PASS|MATCHED|
|GEX|HOSE|Industrial Goods & Services|2020-01-02|2026-09-15|1670|29|Y|PASS|MATCHED|
|GMD|HOSE|Industrial Goods & Services|2020-01-02|2026-09-15|1670|1257|Y|PASS|MATCHED|
|GVR|HOSE|Chemicals|2020-01-02|2026-09-15|1664|119|Y|PASS|MATCHED|
|HAH|HOSE|Industrial Goods & Services|2020-01-02|2026-09-15|1670|299|Y|PASS|MATCHED|
|HCM|HOSE|Financial Services|2020-01-02|2026-09-15|1670|239|Y|PASS|MATCHED|
|HDB|HOSE|Banks|2020-01-02|2026-09-15|1670|599|Y|PASS|MATCHED|
|HPG|HOSE|Basic Resources|2020-01-02|2026-09-15|1670|629|Y|PASS|MATCHED|
|IDC|HNX|Real Estate|2020-01-02|2026-09-15|1666|59|Y|PASS|MATCHED|
|IMP|HOSE|Health Care|2020-01-02|2026-09-15|1657|689|Y|PASS|MATCHED|
|KDH|HOSE|Real Estate|2020-01-02|2026-09-15|1670|149|Y|PASS|MATCHED|
|LAS|HNX|Chemicals|2020-01-02|2026-09-15|1668|929|Y|PASS|MATCHED|
|MBB|HOSE|Banks|2020-01-02|2026-09-15|1670|1644|Y|PASS|MATCHED|
|MPC|UPCOM|Food & Beverage|2020-01-02|2026-09-15|1669|119|Y|PASS|MATCHED|
|MSN|HOSE|Food & Beverage|2020-01-02|2026-09-15|1670|239|Y|PASS|MATCHED|
|MWG|HOSE|Retail|2020-01-02|2026-09-15|1670|359|Y|PASS|MATCHED|
|NT2|HOSE|Utilities|2020-01-02|2026-09-15|1670|1665|Y|PASS|MATCHED|
|NTP|HNX|Construction & Materials|2020-01-02|2026-09-15|1669|1662|Y|PASS|MATCHED|
|OIL|UPCOM|Oil & Gas|2020-01-02|2026-09-15|1668|388|Y|PASS|UNRESOLVED|
|PLX|HOSE|Oil & Gas|2020-01-02|2026-09-15|1670|59|Y|PASS|MATCHED|
|PNJ|HOSE|Personal & Household Goods|2020-01-02|2026-09-15|1670|59|Y|PASS|MATCHED|
|POW|HOSE|Utilities|2020-01-02|2026-09-15|1670|1019|Y|PASS|MATCHED|
|PVD|HOSE|Oil & Gas|2020-01-02|2026-09-15|1670|1106|Y|PASS|MATCHED|
|PVI|HNX|Insurance|2020-01-02|2026-09-15|1670|689|Y|PASS|MATCHED|
|PVS|HNX|Oil & Gas|2020-01-02|2026-09-15|1670|509|Y|PASS|MATCHED|
|QNS|UPCOM|Food & Beverage|2020-01-02|2026-09-15|1668|778|Y|PASS|UNRESOLVED|
|REE|HOSE|Utilities|2020-01-02|2026-09-15|1670|29|Y|PASS|MATCHED|
|SAS|UPCOM|Retail|2020-01-02|2026-09-15|1659|687|Y|PASS|UNRESOLVED|
|SSI|HOSE|Financial Services|2020-01-02|2026-09-15|1670|1077|Y|PASS|MATCHED|
|TNG|HNX|Personal & Household Goods|2020-01-02|2026-09-15|1670|1409|Y|PASS|MATCHED|
|VCS|HNX|Construction & Materials|2020-01-02|2026-09-15|1669|1259|Y|PASS|MATCHED|
|VEA|UPCOM|Industrial Goods & Services|2020-01-02|2026-09-15|1669|209|Y|PASS|UNRESOLVED|
|VGI|UPCOM|Telecommunications|2020-01-02|2026-09-15|1669|179|Y|PASS|UNRESOLVED|
|VHC|HOSE|Food & Beverage|2020-01-02|2026-09-15|1670|89|Y|PASS|MATCHED|
|VNM|HOSE|Food & Beverage|2020-01-02|2026-09-15|1670|539|Y|PASS|MATCHED|

Tất cả `reference_only=N`. `UNRESOLVED` volume vẫn `KEEP_SOURCE_QUALIFIED`, `canonical_merge_allowed=false`; không silently repair.

## Canonical-readiness audit

Offline mapper đã replay cùng PASS assessment và exact-hash policy trên toàn bộ 55 mã, không network và không sửa raw. Kết quả mapping: `91.768` `prices_daily` candidates, `1.667` `benchmark_daily` rows, `5.009` observed-session calendar rows; standard market schemas, unique keys, calendar relations và latest-21-session traded-value coverage đều PASS.

KBS `VENDOR_ADJUSTED` chỉ map `adj_close`; `raw_open/high/low/close` giữ `null`, KBS `va` chưa promote, CafeF price bands không trộn với adjusted basis. CafeF `traded_value` chỉ gắn theo exact ticker/date với field-level lineage.

Canonical promotion `canonical-pilot-20260917T062832Z-6748ac02` đã verify toàn bộ parent artifact hash và tạo `55` securities, `91.768` prices, `1.667` benchmark rows, `5.009` calendar rows và `4.455` monthly market feature snapshots; latest eligibility đạt `55/55`. Generic clean-table replay có `0` issue và `0` quarantine; network requests bằng `0`.

Company name là current KBS display label đã verify exact 55 ticker/stock/exchange. Identity interval bắt đầu tại first accepted pilot price date, không backdate về listing date, và giữ `provisional_verified_for_pilot` với scope `PILOT_OBSERVED_INTERVAL_ONLY`. Đây là đủ cho market-only pilot feature validation, không phải complete historical-universe master và không đóng `OPEN-04`. Financial vẫn `PIT_UNRESOLVED`, `financial_features_allowed=false`.
