# Literature matrix

Matrix này giữ đúng năm primary columns của research note gốc. Mỗi reference có một row riêng. Nội dung chưa được kiểm tra bằng full text hoặc reliable primary material được ghi nguyên văn `PENDING — FULL-TEXT REVIEW`; title/abstract không được dùng để suy ra sample, period, formula hoặc result.

Khi review một item, evidence note phải ghi citation, page/section, sample/data, variables, method, main result, limitations và DELTA decision. Chỉ chuyển trạng thái sang `VERIFIED` khi các trường này có evidence truy vết được.

## A — Momentum và thị trường Việt Nam

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **A1. Jegadeesh & Titman (1993), “Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency”, JF 48(1), 65–91, DOI 10.1111/j.1540-6261.1993.tb04702.x.** Lý do đọc gốc: nền tảng cross-sectional momentum; giải thích horizon 3M/6M/12M. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate rationale cho horizon; chưa khóa formula/sample theo paper. |
| **A2. Vo & Truong (2018), “Does momentum work? Evidence from Vietnam stock market”, JBEF 17, 10–15, DOI 10.1016/j.jbef.2017.12.002.** Lý do đọc gốc: bằng chứng trực tiếp tại Việt Nam và benchmark strategy. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Dùng cho motivation/benchmark sau full-text review; chưa coi là replication evidence. |
| **A3. Phan & Zhou (2012), “Momentum Effect in the Vietnamese Stock Market”, Procedia Economics and Finance 2, 179–190, DOI 10.1016/S2212-5671(12)00078-0.** Lý do đọc gốc: xem momentum có thể yếu sau risk adjustment. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate caveat cho momentum; không suy result trước review. |
| **A4. Le & Bertrand (2023), “Overreaction and momentum in the Vietnamese stock market”, Managerial Finance 49(1), 13–28, DOI 10.1108/MF-01-2022-0013.** Lý do đọc gốc: overreaction, volume và weekly data của hơn 300 cổ phiếu Việt Nam. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate cho motivation/liquidity; chi tiết sample và kết quả chưa xác minh. |
| **A5. Butt, Kolari & Sadaqat (2021), “Revisiting momentum profits in emerging markets”, Pacific-Basin Finance Journal 65, 101486, DOI 10.1016/j.pacfin.2020.101486.** Lý do đọc gốc: bối cảnh emerging/frontier, liquidity risk và down-market states. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate cho downside/liquidity caveat; chưa kích hoạt feature mới. |

**Evidence status nhóm A:** 0/5 item có full-text evidence record trong matrix này.

## B — Phân cụm cổ phiếu và portfolio

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **B6. Han, He & Toh (2023), “Pairs trading via unsupervised learning”, EJOR 307(2), 929–947, DOI 10.1016/j.ejor.2022.09.041.** Lý do đọc gốc: gần với financial clustering; so sánh K-Means, DBSCAN và Agglomerative. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate comparator rationale; không coi summary cũ là methodology approval. |
| **B7. Nanda, Mahanty & Tiwari (2010), “Clustering Indian stock market data for portfolio management”, ESWA 37(12), 8793–8798, DOI 10.1016/j.eswa.2010.06.026.** Lý do đọc gốc: K-Means/SOM/Fuzzy C-Means và portfolio ở emerging market. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate comparator/use-case; portfolio outcome không được dùng chọn cluster. |
| **B8. Ebrahimi, Amini & Liu (2026), “Cardinality-constrained portfolio optimization with clustering”, Annals of Operations Research, DOI 10.1007/s10479-026-07184-z.** Lý do đọc gốc: clustering để giảm chiều selection và gắn cardinality constraint. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Chỉ thuộc candidate M3 downstream use; không thay cluster-quality protocol. |
| **B9. Ban, El Karoui & Lim (2018), “Machine learning and portfolio optimization”, Management Science 64(3), 1136–1154, DOI 10.1287/mnsc.2016.2644.** Lý do đọc gốc: nền tảng ML trong portfolio optimization cho M3/backtest. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate M3; không mở portfolio evaluation trong model development M2. |

**Evidence status nhóm B:** 0/4 item có full-text evidence record trong matrix này.

## C — Thuật toán phân cụm và đánh giá cụm

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **C10. MacQueen (1967), “Some Methods for Classification and Analysis of Multivariate Observations”, Fifth Berkeley Symposium 1, 281–297.** Lý do đọc gốc: paper nền tảng K-Means. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Citation candidate cho static K-Means baseline; cần page/section trước methodology freeze. |
| **C11. Ward (1963), “Hierarchical Grouping to Optimize an Objective Function”, JASA 58(301), 236–244, DOI 10.1080/01621459.1963.10500845.** Lý do đọc gốc: Ward linkage và dendrogram. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Citation candidate cho Ward comparator; implementation hiện tại chưa thay evidence review. |
| **C12. Ester, Kriegel, Sander & Xu (1996), “A Density-Based Algorithm for Discovering Clusters in Large Spatial Databases with Noise”, KDD 1996.** Lý do đọc gốc: DBSCAN, outlier/noise thay vì ép mọi mã vào cluster. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | DBSCAN chưa triển khai; cần protocol cho noise label, variable cluster count và temporal handling. |
| **C13. Rousseeuw (1987), “Silhouettes: A graphical aid to the interpretation and validation of cluster analysis”, JCAM 20, 53–65, DOI 10.1016/0377-0427(87)90125-7.** Lý do đọc gốc: nền tảng Silhouette Score. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate cluster-quality metric; không dùng portfolio return để thay thế. |
| **C14. Davies & Bouldin (1979), “A Cluster Separation Measure”, IEEE TPAMI PAMI-1(2), 224–227, DOI 10.1109/TPAMI.1979.4766909.** Lý do đọc gốc: nền tảng Davies-Bouldin Index. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate cluster-quality comparator; exact definition cần evidence lock. |
| **C15. Hubert & Arabie (1985), “Comparing partitions”, Journal of Classification 2, 193–218, DOI 10.1007/BF01908075.** Lý do đọc gốc: nền tảng Adjusted Rand Index cho rolling-window stability. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | ARI thuộc temporal stability, không biến independent K-Means thành Dynamic Clustering. |

**Evidence status nhóm C:** 0/6 item có full-text evidence record trong matrix này.

## D — Giảm chiều và trực quan hóa

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **D16. Pearson (1901), “On Lines and Planes of Closest Fit to Systems of Points in Space”, Philosophical Magazine 2(11), 559–572, DOI 10.1080/14786440109462720.** Lý do đọc gốc: nền tảng PCA cho feature tương quan cao. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PCA phải fit snapshot/development-only; citation/page còn chờ review. |
| **D17. McInnes, Healy & Melville (2018/2020), “UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction”, arXiv:1802.03426, DOI 10.48550/arXiv.1802.03426.** Lý do đọc gốc: visualization 2D/3D cho dashboard M2–M3. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | UMAP mặc định chỉ visualization; không làm clustering input nếu methodology chưa duyệt. |

**Evidence status nhóm D:** 0/2 item có full-text evidence record trong matrix này.

## E — Backtest và thiết kế nghiên cứu tài chính

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **E18. Markowitz (1952), “Portfolio Selection”, The Journal of Finance 7(1), 77–91, DOI 10.1111/j.1540-6261.1952.tb01525.x.** Lý do đọc gốc: nền tảng risk-return và portfolio cho M3. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate M3 framing; không dùng portfolio metric chứng minh cluster quality. |
| **E19. Sharpe (1966), “Mutual Fund Performance”, The Journal of Business 39(1), 119–138, DOI 10.1086/294846.** **Original reading rationale:** feature + strategy evaluation. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | **Current DELTA decision:** portfolio evaluation only. Sharpe không phải clustering feature, cluster-quality metric hoặc model-selection input; rationale gốc vẫn được giữ để bảo toàn decision history. |
| **E20. Lo (2002), “The Statistics of Sharpe Ratios”, Financial Analysts Journal 58(4), 36–52, DOI 10.2469/faj.v58.n4.2453.** Lý do đọc gốc: cảnh báo diễn giải Sharpe khi return autocorrelated/non-normal. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate limitation cho M3 portfolio report; không đi vào feature snapshot. |
| **E21. Bailey, Borwein, Lopez de Prado & Zhu (2017), “The Probability of Backtest Overfitting”, Journal of Computational Finance 20(4), 39–69, DOI 10.21314/JCF.2016.322.** Lý do đọc gốc: overfitting khi thử nhiều strategy/backtest. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate cho frozen protocol/multiple-testing control; M2 mặc định tắt portfolio evaluation. |
| **E22. de Prado (2018), “Advances in Financial Machine Learning”, Wiley.** Lý do đọc gốc: purging/embargo, backtest leakage và financial-ML workflow. | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | PENDING — FULL-TEXT REVIEW | Candidate protocol reference; chưa áp dụng exact procedure khi chưa có page/chapter evidence. |

**Evidence status nhóm E:** 0/5 item có full-text evidence record trong matrix này.

## F — Dynamic / Temporal Clustering — added after mentor review

Danh sách 22 reference gốc không có dedicated Dynamic Clustering primary-method section. Hiện chưa có paper nào ở nhóm F có đủ full-text methodology evidence trong repository để thêm row mà không suy diễn. Vì vậy nhóm F chưa có entry, và [DYNAMIC_CLUSTERING_REVIEW.md](DYNAMIC_CLUSTERING_REVIEW.md) tiếp tục ở trạng thái **NOT APPROVED**.

Khi có paper thực sự được review, row mới vẫn phải dùng đúng năm cột trên và evidence note phải chỉ ra temporal objective/state update, initialization, entry/exit/missing handling, comparator, leakage control và limitation. Việc thêm citation không tự động phê duyệt implementation.
