# Roadmap DELTA

**Integration market + financial — 23/10/2026.** Nhánh `integration/market-financial`
kế thừa financial checkpoint `819cd82` và market `340519d`. C8 V2 đã nhập từ
`DELTA_02_ACTIVE_M2_M3.zip`, giữ đúng hashes và path. Market có 84 snapshots
2019–2025, K=2/robust; financial có 1.172 mã × annual 2016–2025, K=3/zscore.
Đây là hai baseline độc lập. Cả hai cần review chất lượng cụm; strict PIT/research/M3
chưa được nghiệm thu. Giao ticker tại cuối 2025 là 1.148 mã, chưa phải historical PIT join.

Chạy `scripts/verify_market_financial_integration.py --publish` để kiểm current
60+24 artifacts và tạo manifest tham chiếu có version; script này không fit.
`verify_m2_task12.py` và `generate_m2_task13_handoff.py` là historical V1,
không dùng chúng để tái tạo current84. Xem `M2/artifacts/market-financial-integration-v1/`.

### Kiểm chứng integration đã thực hiện

- Market:19/19C8outputs,68holdoutoutputs,9frozenpins,84models và75.801assignments PASS;
  kiểm sourceeligibility và nearestcentroid, không refit.
- Financial:1.786inputpins,11.720rows, scaler/assignment/inertia/profiles/checkpoints PASS
  với hai frozen source files đúng hash trong sourceoverlay có version; output review riêng.
- 76 targeted tests: OK,4Streamlittests skipped do thiếu optionaldashboarddependency;
  6 PCAartifacttests PASS. Importer/immutability tests bổ sung PASS.
- compileall, synthetic smoke (`run-20261023T161947Z-e04ef3b8`), `node --check web/app.js` PASS.
- Full repository suite chưa PASS: sandboxtimeout240giây; lượt ngoàisandbox được giới hạn360giây,
  xem `.tmp/integration-full-suite-unsandboxed.json` và log. Không bỏ assertions.
- Plain diffcheck toàn nhánh có inheritedCRLF/Markdownhardbreak warnings từ market artifacts;
  scoped integrationdiffcheck với `cr-at-eol` không có whitespace errors. Không sửa sealedbytes để làm sạch warnings.

## Trạng thái hợp nhất

- [x] Financial Execution56 checkpoint và baseline annual đã chạy.
- [x] Market branch có development60/holdout24 và dashboard chỉ đọc.
- [x] C8 V2 nhập đúng version, không thay source hoặc model đã freeze.
- [x] Targeted regression và independent verification cho integration; full repository gate còn PARTIAL (xem Current status).
- [ ] Review chất lượng cụm market và financial từ actual metrics.
- [ ] Historical identity, financial publication/vintages và availability-aware join.
- [ ] Protocol model kết hợp hoặc final M3; không tự triển khai từ việc merge code.

## Roadmap lịch sử từ hai nhánh

Các checklist dưới đây ghi milestone tại thời điểm cũ; current status ở trên có ưu tiên.

# Roadmap DELTA

**Execution56 đã execute:** baseline financial 1.172 mã/10 năm, 70.320 core ratios
tính lại, k=3/zscore/no winsorization. [Report](../artifacts/reports/financial-full10-baseline-v1/report.md).
Technical verification PASS; mọi năm có cụm nhỏ, nên cần review outliers/preprocessing
trước bước methodology tiếp theo. M2 research freeze/PIT/M3 chưa hoàn tất.

**Cleanup53 trước M2 đã hoàn tất:**2.889filesđãgỡ, evidencecầnthiết giữarchive/hash;
[handoff hiện hành](../data/handoffs/financial-reference-2016-2025/README.md).
Chưa chạy/refitphâncụm; bước tiếp làbaselinefinancial-only trêncohort1.172mã.

**Financial reference checkpoint50 (23/10/2026):**1.172candidates đủannual2016–2025/13.529rows;[report/bàn giao](../artifacts/reports/financial-dstock-remaining-v1/report.md). Remaining API cases đã thử;761heldkỳ. Chỉ core-ratio reference, không M2/M3researchPASS hoặc thayprotocol/model.

## M1 — Market Data Foundation

M1 market foundation đã hoàn tất cho **market-only experiment preparation**; strict research gate vẫn `NOT READY`.

- [x] C5 baseline 500 securities được giữ trong lineage bất biến.
- [x] CafeF-primary migration/validation chấp nhận `TradeHistoryNew` và `AdjustPrice × 1000` như `vendor_adjusted` proxy với giới hạn được ghi rõ.
- [x] C6 freeze/acquisition contract và five-shard expansion foundation.
- [x] C7 thu được 452 complete expansion securities; 148 còn `DEFERRED_EXPANSION_ACQUISITION`.
- [x] C8 complete-only chạy trên 952 candidates tại snapshot `2026-08-28`.
- [x] C8-VERIFY xác minh offline hashes và lineage, không rebuild feature.
- [x] R1 hợp nhất active repository mà không thay dữ liệu, methodology hoặc kết quả.
- [x] M1-REPORT tạo artifact `artifacts/reports/m1-market-foundation-v1/` và notebook inspection.

Kết quả khóa: 922 `feature_complete`, 905 `market_feature_ready_v2`, 47 market-readiness failures, 30 latest-253 incomplete, 0 `historical_identity_ready` và 0 `research_ready`. 905 chỉ là latest-snapshot count, không phải final historical universe.

Supplemental acquisition cho 148 deferred rows là optional future stage, không phải điều kiện để bắt đầu M2-PREP. Financial taxonomy/PIT, historical identity authority và final research sample-size/density vẫn là workstream riêng, fail-closed.

## Financial PIT workstream

- [x] FIN-PIT-1A-R5 technical gate và bounded-pilot approval cho `B_OFFICIAL_DATE_D1_V1`.
- [x] FIN-PIT-1 bounded official source/document pilot với 32 unique documents và 40 linkage candidates.
- [x] FIN-PIT-2 offline semantic extraction gate `PARTIAL`: 3 report candidates và 216 balance-sheet instant facts semantic-ready trong text-based PVS subset; scanned/ambiguous documents quarantine, 7 revision relations giữ `UNKNOWN`, canonical/features bằng 0.
- [x] FIN-PIT-2-R1 selective OCR remediation gate `PARTIAL`: 26 documents/209 pages OCR, 205 pages usable; linkage verified 6→27, ambiguous 34→4, 9 scope conflicts được giữ fail-closed, quarantine 29→26, semantic-ready reports 3→6; Q2/Q3 duration vẫn unresolved, canonical/features bằng 0.
- [ ] FIN-PIT-3 chỉ được mở bằng session riêng sau manual scope freeze; với R1 `PARTIAL`, không được claim coverage toàn bounded pilot và chỉ review verified subset có evidence.

## M2 — Clustering Research

- [x] Static K-Means deterministic baseline và label alignment/transition tracking.
- [x] Tách cluster quality khỏi temporal/portfolio metrics ở architecture.
- [x] **M2-PREP audit:** freeze eligibility semantics/feature set/firewall; tái lập 905/952; giải thích readiness gaps; audit implementation/literature và xuất `artifacts/experiments/m2-prep-v1/`. Status `MANUAL_REVIEW_REQUIRED`; không tạo final config hoặc chạy clustering.
- [x] **M2-PREP-REVIEW:** owner review ngày `2026-09-26` chấp thuận Protocol v1 trong Unified Project Plan làm input cho M2-R1; artifact M2-PREP vẫn giữ historical status `MANUAL_REVIEW_REQUIRED`.
- [ ] **M2-R1 Protocol Freeze v1:** materialize development/holdout, minimum eligibility/skip rule, preprocessing, global-`k`, PCA, feature-version compatibility và portfolio firewall thành config, ADR, validation và tests; chưa chạy real clustering.
- [ ] **M2-R2 Market-only Runner Adapter:** thêm explicit `market_only` mode, configurable eligibility field và checksummed C8 input adapter; giữ strict research path không đổi.

- [x] **M2 Nhiệm vụ 1 / protocol freeze:** khóa development/holdout snapshots, minimum 120/skip, 8 features, fail-closed missing, no clipping, Robust Scaling per-snapshot, `k=2..8`, Global K selection firewall, comparator-only PCA và scoped feature-version compatibility. Chưa chạy clustering/holdout/backtest; PCA component rule phải preregister trước comparator execution.
- [x] **M2 Nhiệm vụ 2 / runner preparation:** adapter đọc trực tiếp C8 checksummed feature snapshots, lọc eligibility theo từng snapshot, fail-closed 8 feature, skip dưới 120 và terminal-universe/integration tests; không fit Global K.
- [x] **M2 Nhiệm vụ 11 / Final Holdout (2026-10-04):** Task 10 freeze KMeans Baseline/K=2;
  7 snapshots holdout, 4.624 assignments và 6 cặp tháng; giữ preprocessing/seed,
  không K-scan/comparator, reset gap, checksum manifest và verify-only rerun.
  Chưa thực hiện Task 12 hoặc M3; chi tiết hiện hành ở CURRENT_STATUS.
- [ ] **M2 Nhiệm vụ 3 / Global K:** chạy K-Means `k=2..8` chỉ trên 15 development snapshots và khóa Global K theo protocol; chưa mở holdout.
- [ ] Freeze feature registry và development/validation protocol; active snapshot 1.5 không chứa Sharpe và tách readiness, còn formula market giữ nguyên baseline 1.4.
- [x] Có implementation PCA + K-Means snapshot-only, lưu scaler/PCA parameters và explained variance; chưa có real comparison evidence.
- [x] Có Ward/Agglomerative comparator deterministic; DBSCAN/GMM chờ protocol. Chưa có real comparator evidence.
- [ ] Đánh giá cluster quality: Silhouette, Davies-Bouldin, Calinski-Harabasz, inertia, balance.
- [ ] Đánh giá temporal stability: ARI, NMI, persistence, transition, migration rate, centroid drift.
- [ ] Chỉ triển khai Dynamic Clustering sau explicit approval trong review tương ứng.
- [ ] Thiết kế variable-cluster/noise-label interface trước khi cân nhắc DBSCAN; không ép DBSCAN vào fixed-`k` abstraction.

## M3 — Backtest + Product

- [ ] Freeze methodology trước final backtest và dùng holdout đúng protocol; chỉ M3/frozen config bật `portfolio_evaluation.enabled=true`.
- [ ] So sánh cluster strategy với VNINDEX, equal-weight universe và momentum-only.
- [x] Transaction cost, turnover và return-space portfolio foundation.
- [ ] Báo cáo CAGR, volatility, Sharpe, Sortino, MDD, Calmar, alpha/beta, information ratio theo availability.
- [x] Immutable product bundle, read API và dashboard foundation.
- [ ] Thesis dashboard hoàn chỉnh cho cluster, transitions, feature explanation, PCA/UMAP, quality/provenance.

## Gates chung

Mỗi phase phải chạy tests, compile/static checks, JSON parse, broken link/import check và ghi changed files. Regression chưa giải thích thì dừng. M2-R1 không được promote identity/research readiness, không chạy clustering/backtest, không mở holdout và không chọn model bằng portfolio return. Không mở rộng auth, news/sentiment, watchlist, alert, microservice hoặc database migration trong active stage.
