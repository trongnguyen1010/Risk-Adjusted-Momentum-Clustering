# Product Layer

## M3 thesis dashboard

Phạm vi M3 là dashboard đọc versioned experiment artifacts để hiển thị ticker detail, market analytics, cluster, peer stocks, transition history, feature explanation, PCA/UMAP visualization, data quality và provenance. Dashboard không đọc raw data trực tiếp và không recompute scaler/model/metric.

Foundation hiện có:

- `product/builder.py`: tạo immutable company bundle từ complete canonical/feature/experiment runs.
- `product/repository.py`: đọc bundle an toàn theo ticker.
- `product/server.py`: read-only API v1 và static web serving.
- `web/`: responsive shell với explicit missing/unavailable states.

API base `/api/v1` hỗ trợ `GET /health`, `GET /companies`, `GET /companies/{ticker}`. Unknown ticker trả 404; nullable/unavailable không được hiển thị thành zero. Payload giữ schema version, as-of date, price basis, warnings và run provenance.

## Future commercial product

News, sentiment, authentication, watchlists, alerts, personalized workspace và production database/cache là extension thương mại tương lai, ngoài scope refactor hiện tại. Chúng chỉ được mở sau rights, privacy, security và product decisions riêng.

Product không được dẫn dắt research methodology. Cluster label không phải bullish/bearish recommendation; giao diện phải phân biệt pilot/synthetic với validated production evidence.
