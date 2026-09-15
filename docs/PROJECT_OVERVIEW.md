# Tổng quan project DELTA

DELTA nghiên cứu cấu trúc tương đồng giữa cổ phiếu Việt Nam và chuyển kết quả nghiên cứu đã kiểm chứng thành product artifact có thể khám phá. Project không đồng nhất “cluster tốt” với “portfolio sinh lời”.

## Research Core

Research Core xây historical universe, multi-source canonical data, point-in-time feature, clustering experiment và ba lớp evaluation độc lập. Quy trình chính thức là M1 Data Foundation, M2 Clustering Research, M3 Backtest + Product.

Static K-Means deterministic là baseline. PCA + K-Means và comparator phù hợp được thêm qua model registry. Temporal tracking của snapshot độc lập chỉ là stability analysis; một phương pháp Dynamic Clustering chỉ được code sau literature review và approval rõ ràng.

## Product Layer

Product Layer hiện có immutable bundle builder, repository, read-only API và web dashboard. Nó hiển thị ticker, market analytics, cluster/peer và provenance từ versioned experiment artifact. Product không fit model, không sửa artifact và không quyết định methodology.

M3 thesis dashboard nằm trong scope. News, sentiment, authentication, watchlist và alerts là commercial extensions tương lai, ngoài scope refactor hiện tại.

## Nguyên tắc kết luận

Synthetic và legacy pilot chỉ chứng minh plumbing/reproducibility. `SOURCE_SMOKE` thật không tự mở scale; M1 chưa hoàn thành cho tới khi source semantics/rights pass, `REPRESENTATIVE_PILOT` 50–60 securities và >=5 năm PASS, rồi target >=300 đạt coverage. DELTA là công cụ nghiên cứu, không phải investment advice.
