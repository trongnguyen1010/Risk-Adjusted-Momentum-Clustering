# Product Layer

## M3 thesis dashboard

Phạm vi M3 là dashboard đọc versioned experiment artifacts để hiển thị ticker detail, market analytics, cluster, peer stocks, transition history, feature explanation, PCA/UMAP visualization, data quality và provenance. Dashboard không đọc raw data trực tiếp và không recompute scaler/model/metric.

Foundation hiện có:

- `product/builder.py`: tạo immutable company bundle từ complete canonical/feature/experiment runs.
- `product/repository.py`: đọc bundle an toàn theo ticker.
- `product/server.py`: read-only API v1 và static web serving.
- `web/`: responsive shell với explicit missing/unavailable states.

API base `/api/v1` hỗ trợ `GET /health`, `GET /companies`, `GET /companies/{ticker}`. Unknown ticker trả 404; nullable/unavailable không được hiển thị thành zero. Payload giữ schema version, as-of date, price basis, warnings và run provenance.

Market cap, BVPS, P/E, P/B, Piotroski F-Score, Beneish M-Score và Altman Z-Score variants chỉ được compute/version sau khi source semantics và formula được duyệt; vendor-derived values chỉ là comparison evidence. EPS không được suy từ end-of-period outstanding shares khi thiếu weighted-average basic/diluted shares hoặc documented vendor EPS basis. Composite scores cũng không tự động trở thành clustering inputs vì có thể double-count underlying facts.

## Future commercial product

Company profile/logo/description/website, news, sentiment, authentication, watchlists, alerts, personalized workspace và production database/cache là extension thương mại tương lai, ngoài M1 hiện tại. Chúng chỉ được mở sau rights, privacy, security và product decisions riêng.

Product không được dẫn dắt research methodology. Cluster label không phải bullish/bearish recommendation; giao diện phải phân biệt pilot/synthetic với validated production evidence.
