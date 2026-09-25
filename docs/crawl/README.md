# DELTA Crawl Documentation

> **START HERE cho M1 data collection.**

## Active CafeF expansion v1

Năm ZIP acquisition ban đầu đã được C7 kiểm tra và lập inventory offline tại
`artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1/`. Bước thu thập
tiếp theo chỉ chạy ba shard trong `configs/data/cafef_supplemental_v1/` bằng
`scripts/run_cafef_supplemental_worker.py`; 452 mã COMPLETE bị loại khỏi plan,
141 mã runnable dùng namespace raw mới và 7 mã FAILED chờ manual review. Runbook
[CAFEF_EXPANSION_5_WORKERS.md](CAFEF_EXPANSION_5_WORKERS.md) mô tả acquisition ban
đầu và cách nhận ZIP, không được dùng để chạy lại các trang đã hoàn tất.

Frozen config ban đầu vẫn ở `configs/data/cafef_expansion_v1/`. Các tài liệu C1, M1-scale/KBS và
`TEAM_CRAWLING.md` là **HISTORICAL / DO NOT USE FOR CAFEF EXPANSION V1**; chúng được
giữ để tái lập C1–C5.

Thư mục này là tài liệu chuẩn cho toàn bộ việc **source discovery → source smoke → representative pilot → scale crawl** của DELTA.

Mục tiêu không chỉ là “crawl được data”, mà là bảo đảm mọi dữ liệu có:

- source semantics rõ ràng;
- unit/timezone/price basis rõ ràng;
- share/capital-structure availability và effective/available timing rõ ràng;
- raw evidence bất biến;
- provenance và checksum;
- cách chia việc thống nhất khi nhiều collector cùng crawl;
- khả năng reconcile CafeF / VietFin / Vnstock hoặc source khác;
- khả năng tái tạo và audit.

## 1. Đọc theo thứ tự

1. [DATA_COLLECTION_GUIDE.md](DATA_COLLECTION_GUIDE.md)  
   Tổng quan dữ liệu cần crawl, lý do cần từng nhóm dữ liệu và nguyên tắc RAW → normalized → canonical.

2. [FIELD_CATALOG.md](FIELD_CATALOG.md)  
   Danh mục field cần thu thập, field nào bắt buộc, field nào optional, field nào chỉ giữ RAW.

3. [SOURCE_DISCOVERY.md](SOURCE_DISCOVERY.md)  
   Cách một user tự khám phá source bằng browser/DevTools trước khi agent tự động hóa.

4. [SOURCE_SMOKE.md](SOURCE_SMOKE.md)  
   Quy trình chạy real `SOURCE_SMOKE` 3–5 mã và tiêu chuẩn PASS/BLOCKED.

5. [REPRESENTATIVE_PILOT.md](REPRESENTATIVE_PILOT.md)
   Official 50–60-symbol pilot path, universe/config contract, dry-run, QC và gate semantics.

6. [TEAM_CRAWLING.md](TEAM_CRAWLING.md)
   Historical M1 scale/KBS runbook; không dùng cho CafeF expansion v1.

7. [HANDOFF_TEMPLATE.md](HANDOFF_TEMPLATE.md)
   Template manifest, collector report và checklist bàn giao.

8. [sources/SOURCE_NOTE_TEMPLATE.md](sources/SOURCE_NOTE_TEMPLATE.md)
   Template ghi semantics riêng cho mỗi source.

9. [AGENT_SOURCE_SMOKE_PROMPT.md](AGENT_SOURCE_SMOKE_PROMPT.md)
   Master prompt cho coding/research agent thực hiện source discovery và real smoke đầu tiên.

## 2. Gate chính

```text
SYNTHETIC_SMOKE
    │
    │ chỉ test plumbing
    ▼
SOURCE_DISCOVERY
    │
    ▼
SOURCE_SMOKE
3–5 mã thật
    │
    │ PASS
    ▼
REPRESENTATIVE_PILOT
50–60 mã, >=5 năm
    │
    │ PASS
    ▼
M1_SCALE
>=300 mã; mỗi mã >=3 năm usable
range thu thập chung 5–15 năm
    │
    ▼
EXTENDED_SCALE
historical eligible universe
5–15 năm, có thể >1.200 mã
```

**Không có gate nào được skip.**

Current state: `SOURCE_SMOKE=PASS`; `REPRESENTATIVE_PILOT=PASS`; M1 raw acquisition/canonical mapping/EDA đã hoàn tất cho 500 mã. Sau QC có 500/500 mã >=3 năm và 484/500 mã >=5 năm. `M1_SCALE` feature gate vẫn `FAIL` vì chỉ 168/500 latest rows feature-complete trước identity review, dưới ngưỡng 300; report `m1-scale-quality-20260918T130735Z-54038c13` kết luận `PARTIAL`. Financial vẫn `PIT_UNRESOLVED / RAW_ONLY`.

## 3. Quy tắc bất biến

- Không crawl lớn trước khi `SOURCE_SMOKE` và `REPRESENTATIVE_PILOT` pass.
- Không bypass login, paywall, anti-bot, CAPTCHA, access control hoặc rate limit.
- Không commit token/cookie/API key.
- Không tự suy multiplier từ magnitude.
- Không forward-fill missing.
- Không đổi missing thành zero.
- Không trộn raw price và adjusted price.
- Không dùng current ticker list làm historical universe.
- Không giả định các share counts bằng nhau hoặc backfill current share count về lịch sử.
- Không sửa raw file đã checkpoint.
- Không coi data vendor-computed feature là canonical feature.
- Không average conflict giữa hai source để “cho khớp”.
- Không cho một collector tự sửa mapping/semantics mà không review/version bump.

## 4. Storage

Git lưu:

- code;
- schemas;
- configs;
- docs;
- source semantics;
- assignment manifests nhỏ;
- decision records.

Git **không** lưu:

- large raw market history;
- licensed source dumps;
- hàng triệu row canonical real data;
- secrets.

Real data nên sống trong immutable local/shared data workspace theo run/batch và có checksum.

## 5. Quan hệ với tài liệu khác

- `docs/DATA_CONTRACT.md`: canonical tables nghĩa là gì.
- `docs/DATA_PIPELINE.md`: data đi qua các stage như thế nào.
- `docs/crawl/*`: con người/agent thu thập dữ liệu như thế nào.
- `docs/FEATURE_SYSTEM.md`: canonical data biến thành research features như thế nào.

## Continue current execution

Để tiếp tục initiative từ stage hiện tại, dùng:

[CONTINUE_NEXT_STAGE_PROMPT.md](CONTINUE_NEXT_STAGE_PROMPT.md)

Prompt này đọc `Execution Progress / Handoff` trong Master Plan,
thực hiện đúng một next eligible stage, verify, update progress và STOP.
Project đang tiếp tục theo initiative **M1 Data Enrichment & Universe Expansion**.

Trước khi làm gì, hãy đọc theo thứ tự:

1. `AGENTS.md`

   * quy tắc agent, methodology, data invariants, model routing.

2. `docs/crawl/M1_DATA_ENRICHMENT_AND_UNIVERSE_EXPANSION_MASTER_PLAN.md`

   * source of truth cho toàn bộ initiative.
   * xem mục `Execution Progress / Handoff` để biết:

     * stage gần nhất đã hoàn thành,
     * kết quả/verifier,
     * artifact/run mới nhất,
     * blocker còn lại,
     * `Next allowed stage`.

3. `docs/crawl/CONTINUE_NEXT_STAGE_PROMPT.md`

   * paste nguyên prompt này vào một Codex session mới ở root repo.
   * agent sẽ tự đọc progress, thực hiện đúng **một stage tiếp theo**, verify, update handoff rồi STOP.

Nếu cần kiểm tra evidence của stage trước, mở artifact/report được link trong `Execution Progress / Handoff`.

Không tự nhảy stage và không cần đọc lại lịch sử chat cũ.
