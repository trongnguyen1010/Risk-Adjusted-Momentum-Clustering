# DELTA Research/Demo SOURCE_SMOKE Result

## Kết quả

- Run canonical: `source-smoke-20260916T122331Z-79427ec6`; real data, `synthetic=false`.
- Trạng thái: **PASS**. Machine gate `SOURCE_SMOKE` không có blocking reason và chỉ unlock `REPRESENTATIVE_PILOT`.
- Không chạy pilot trong đợt này. Quyền vẫn `RIGHTS_NOT_VERIFIED`; policy là `ACCEPTED_RESEARCH_RISK`, private/local academic research và non-commercial demo; không tái phân phối raw.
- Exactly `FPT` (HOSE), `VNM` (HOSE), `PVS` (HNX), `ACV` (UPCOM) và `VNINDEX` được kiểm tra trên `WINDOW_RECENT=2026-08-22..2026-09-15` và `WINDOW_OLD=2021-09-03..2021-09-27`.

## Provenance và access

- KBS public HTTP: `provider=kbs`, `acquisition_client=delta_public_http`, `endpoint_discovered_via=vnstock`; không tuyên bố đã gọi qua Vnstock SDK.
- CafeF: `provider=cafef`, `acquisition_client=direct`, endpoint trade-history công khai và bounded binary page search.
- Concurrency `1`, minimum interval `2.0s`, timeout `20s`, attempts `2`; không proxy, credential, token, cookie hoặc bypass.
- Canonical run nhận HTTP 200 và không gặp 401/403/429/CAPTCHA/login wall. Run `source-smoke-20260916T120608Z-e1282509` fail-closed do transient JSON retry exhaustion; không unlock gì và không được dùng làm canonical.

## Market checks

| Symbol | Exchange | Recent | Old | Kết quả | Volume semantic |
|---|---|---:|---:|---|---|
| FPT | HOSE | 14 | 16 | PASS | `MATCHED_VOLUME` |
| VNM | HOSE | 14 | 16 raw / 15 eligible | PASS | `MATCHED_VOLUME` |
| PVS | HNX | 14 | 16 | PASS | `MATCHED_VOLUME` |
| ACV | UPCOM | 14 | 16 | PASS | Evidence `UNRESOLVED`; source-qualified storage safe |
| VNINDEX | benchmark | 14 | 16 | PASS | provider volume retained, unit unresolved |

KBS OHLC là `VENDOR_ADJUSTED`; CafeF reference/limit price là VND/share sau multiplier `1,000`. Hai price basis không được so sánh hoặc overwrite. `TotalValue`/`AgreedValue` giữ raw VND; missing không đổi thành zero.

## VNM anomaly resolution

CafeF row `VNM 2021-09-09` có `BasicPrice=85.4`, `Ceiling=223.6`, `Floor=194.4`, `ClosePrice=85.2`, trong khi hai ngày liền kề có price band hợp lệ và KBS cùng ngày có adjusted OHLC/volume bình thường. Bounded evidence loại trừ unit multiplier, date parsing, mapping và corporate-action explanation; classification là `PROVIDER_CORRUPT_ROW`.

Policy chỉ áp dụng khi provider/symbol/date và toàn bộ raw fields khớp evidence đã pin: row được gắn `INVALID_REQUIRED_MARKET_ROW` rồi `EXCLUDE_ROW` khỏi CafeF market-constraint promotion. Raw artifact và finding được giữ nguyên; không sửa giá, không backfill, không xóa KBS OHLCV cùng ngày. Nếu evidence không khớp, policy fail-closed thành `FAIL_SYMBOL_WINDOW`.

## ACV volume resolution

Năm ngày gần nhất được kiểm tra. KBS volume không bằng CafeF matched volume và cũng không bằng matched plus put-through. Approximate numerical similarity không chứng minh semantic; readiness refactor vì vậy ghi classification hiện hành là `UNRESOLVED`. `storage_policy=KEEP_SOURCE_QUALIFIED`, `equality_assumption=false`, `canonical_merge_allowed=false`; KBS volume là explicit canonical candidate có KBS provenance. Vì không merge/average/overwrite, `market_collection_safe=true` và SOURCE_SMOKE PASS không đổi. Immutable run vẫn giữ original classifier output để audit.

## Supporting evidence

- Corporate action: một FPT cash-dividend event, status `PARTIAL`; có announcement/ex-right/source URL nhưng record/payment date chưa có.
- Shares/capital structure: cả bốn mã là `CURRENT_SNAPSHOT_ONLY`; không backfill current shares vào lịch sử.
- Financial raw-only: ba FPT quarterly observations (Q4/2025, Q1/2026, Q2/2026), `RAW_ONLY_PIT_UNRESOLVED`; không dùng trong feature, clustering hoặc backtest.
- Raw inventory: `52` immutable local artifacts (`41` CafeF pages, `10` KBS market responses, `1` KBS financial response) cùng metadata/SHA-256. Raw payload không commit.

## Gate

Machine-readable artifact: `data/raw/source_smoke/source-smoke-20260916T122331Z-79427ec6/gate.json`. Tất cả required checks là `true`, `status=PASS`, `blocking_reasons=[]`, `unlocks=["REPRESENTATIVE_PILOT"]`. Gate chứa hash của config, policy docs và toàn bộ raw evidence. PASS này chỉ mở representative pilot; không mở M1/extended scale.
