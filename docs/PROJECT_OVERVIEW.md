# Tổng quan project DELTA

DELTA nghiên cứu cấu trúc tương đồng giữa cổ phiếu Việt Nam và chuyển kết quả nghiên cứu đã kiểm chứng thành product artifact có thể khám phá. Project không đồng nhất “cluster tốt” với “portfolio sinh lời”.

## Research Core

Research Core xây historical universe, multi-source canonical data, point-in-time feature, clustering experiment và ba lớp evaluation độc lập. Quy trình chính thức là M1 Data Foundation, M2 Clustering Research, M3 Backtest + Product.

Static K-Means deterministic là baseline. PCA + K-Means và comparator phù hợp được thêm qua model registry. Temporal tracking của snapshot độc lập chỉ là stability analysis; một phương pháp Dynamic Clustering chỉ được code sau literature review và approval rõ ràng.

## Product Layer

Product Layer hiện có immutable bundle builder, repository, read-only API và web dashboard. Nó hiển thị ticker, market analytics, cluster/peer và provenance từ versioned experiment artifact. Product không fit model, không sửa artifact và không quyết định methodology.

M3 thesis dashboard nằm trong scope. News, sentiment, authentication, watchlist và alerts là commercial extensions tương lai, ngoài scope refactor hiện tại.

## Nguyên tắc kết luận

Synthetic và legacy SDK pilot chỉ chứng minh plumbing/reproducibility. Real `SOURCE_SMOKE` đã PASS; official `REPRESENTATIVE_PILOT` dùng KBS direct HTTP + CafeF direct đã ready nhưng chưa thực thi. SOURCE_SMOKE không tự mở scale; chỉ real pilot PASS mới mở `M1_SCALE` planning. Financial hiện `RAW_ONLY_PIT_UNRESOLVED` và bị cấm khỏi historical analytics. DELTA là công cụ nghiên cứu, không phải investment advice.
