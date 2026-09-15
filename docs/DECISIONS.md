# Các quyết định còn hiệu lực

Cập nhật 15/09/2026. Git history giữ thảo luận cũ; file này chỉ chứa quyết định đang ràng buộc implementation.

| ID | Quyết định |
|---|---|
| ADR-001 | DELTA có Research Core và Product Layer; research validity là ưu tiên hiện tại. |
| ADR-002 | Product/API/web chỉ đọc immutable projections và không recompute research. |
| ADR-003 | Raw/canonical/model artifact bất biến; missing giữ null/unavailable. |
| ADR-004 | Monthly snapshot K-Means + temporal tracking không phải Dynamic Clustering. |
| ADR-005 | Static K-Means deterministic là baseline; algorithm được chọn qua common registry. |
| ADR-006 | Real clustering cần ba calendar years usable observed history; short history là `REFERENCE_ONLY`. |
| ADR-007 | Sharpe/ROI bị cấm trong clustering input/quality/selection; Sharpe chỉ thuộc portfolio evaluation. |
| ADR-008 | CafeF/VietFin/Vnstock là source candidates; không source nào complete trước khi semantics và rights được verify. |
| ADR-009 | Financial data point-in-time và revision-aware; ratio chờ taxonomy/formula approval. |
| ADR-010 | Raw/vendor-adjusted/total-return price semantics tách biệt; basis change reset window. |
| ADR-011 | KBS 10-symbol pilot là legacy engineering evidence, không phải thesis evidence. |
| ADR-012 | Scale theo gate 3–5 smoke → 50–60 representative pilot → >=300 securities. |
| ADR-013 | Cluster quality, temporal stability và portfolio performance có module/decision riêng. |
| ADR-014 | JSONL dùng cho pilot; large-scale storage chỉ đổi sau M1 evidence. |
| ADR-015 | Tài liệu Markdown viết tiếng Việt, giữ project terms bằng English khi rõ nghĩa hơn. |
| ADR-016 | Không thêm concrete dynamic algorithm trước explicit approval trong `research/DYNAMIC_CLUSTERING_REVIEW.md`. |

## Open decisions

| ID | Cần quyết định |
|---|---|
| OPEN-01 | Final thesis wording và research questions |
| OPEN-02 | Approved Dynamic Clustering objective/method |
| OPEN-03 | Source rights, endpoint semantics và priority rules |
| OPEN-04 | Historical universe/delisted security master authority |
| OPEN-05 | Financial feature taxonomy, sector treatment và citations |
| OPEN-06 | Final development/validation/holdout và purging/embargo |
| OPEN-07 | Comparator set và PCA protocol |
| OPEN-08 | Final portfolio universe/ranking/tie policy |

Quyết định mới ghi: problem → alternatives → choice/reason → evidence → owner/date → affected contract/config/tests → remaining limits.
