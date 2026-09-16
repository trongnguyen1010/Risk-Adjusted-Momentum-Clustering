# DELTA Crawl Documentation

> **START HERE cho M1 data collection.**

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
   Cách chia batch cho nhiều người mà dữ liệu vẫn thống nhất.

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
>=300 mã, >=5 năm
    │
    ▼
EXTENDED_SCALE
historical eligible universe
5–15 năm, có thể >1.200 mã
```

**Không có gate nào được skip.**

Current state: `SOURCE_SMOKE=PASS`; `REPRESENTATIVE_PILOT=READY TO RUN / NOT YET EXECUTED`; `M1_SCALE=NOT UNLOCKED`; financial `PIT_UNRESOLVED / RAW_ONLY`.

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
