# Literature Matrix — DELTA

> **Mục tiêu:** tổng hợp tài liệu nền cho DELTA theo đúng yêu cầu 5 cột của research note gốc: **Mục đích, Dữ liệu, Phương pháp, Kết quả chính, Áp dụng vào DELTA**.
>
> Matrix này phân biệt nội dung được xác minh từ **primary/full-text** với nội dung chỉ có thể xác minh từ **publisher abstract / primary metadata / section snippets**. Không suy diễn sample, công thức hay kết luận khi nguồn không hỗ trợ.
>
> **Quy ước:** các quyết định “Áp dụng vào DELTA” là quyết định thiết kế hiện tại của project, không nhất thiết là khuyến nghị trực tiếp của paper.

---

## A — Momentum và thị trường Việt Nam

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **A1. [Jegadeesh & Titman (1993) — Returns to Buying Winners and Selling Losers](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x)**. Paper nền tảng cho cross-sectional momentum và các horizon trung hạn. | Cổ phiếu Hoa Kỳ từ CRSP, giai đoạn **1965–1989**; paper xây nhiều danh mục theo lợi suất quá khứ và các kỳ formation/holding khác nhau. | Xếp hạng cổ phiếu theo lợi suất quá khứ, tạo danh mục **winners** và **losers**, sau đó xét chiến lược mua winners/bán losers với các kỳ formation và holding khoảng **3–12 tháng**. | Chiến lược relative-strength/momentum tạo lợi nhuận dương có ý nghĩa ở nhiều cấu hình 3–12 tháng. Kết quả không được giải thích đầy đủ bởi systematic risk hay delayed reaction với common factors; một phần abnormal return đảo chiều trong các năm sau. | Giữ **momentum 3M/6M/12M** là một feature family có cơ sở học thuật. Không biến DELTA thành chiến lược WML thuần túy; momentum chỉ là một chiều của không gian phân cụm. |
| **A2. [Vo & Truong (2018) — Does momentum work? Evidence from Vietnam stock market](https://doi.org/10.1016/j.jbef.2017.12.002)**. Kiểm tra trực tiếp momentum ở Việt Nam. | Cổ phiếu **HOSE**, dữ liệu Bloomberg, khoảng **06/2007–10/2015 hoặc 11/2015** tùy mô tả trong nguồn; loại cổ phiếu giá dưới **5.000 VND**. | Theo tinh thần Jegadeesh–Titman: kết hợp formation period **3/6/9/12 tháng** với holding period **3/6/9/12 tháng**, tạo 16 chiến lược winners-minus-losers và xem xét transaction costs. | Có bằng chứng momentum dương ở **10/16** chiến lược; cấu hình nổi bật là formation 6 tháng / holding 9 tháng, với mức lợi nhuận được báo cáo khoảng **6%/tháng**; kết quả vẫn tồn tại sau transaction costs theo paper. | Dùng làm **Vietnam-specific motivation** cho momentum features và benchmark momentum-only ở M3. Không dùng riêng paper này để quyết định k, clustering method hay cluster quality. |
| **A3. [Nguyen, T. H. (2012) — Momentum Effect in the Vietnamese Stock Market](https://doi.org/10.1016/S2212-5671(12)00078-0)**. Kiểm tra độ bền của momentum Việt Nam sau risk adjustment. | **HOSE**, weekly returns khoảng **2007–2010**; số cổ phiếu tăng từ khoảng **77** đầu mẫu lên khoảng **239** cuối mẫu. Giá được điều chỉnh cho dividend/split; VN-Index dùng làm market proxy và lãi suất trái phiếu Kho bạc 5 năm làm risk-free proxy. | Xếp hạng cổ phiếu theo lợi suất, chia quintile winners/losers, tạo WML; đánh giá bằng raw return, CAPM/Fama–French three-factor adjustment; phân tích theo size, subperiod và market state; theo dõi hiệu ứng đến nhiều tuần sau formation. | Momentum ngắn hạn tồn tại nhưng yếu đáng kể sau kiểm soát rủi ro. Sau Fama–French controls, bằng chứng mạnh chủ yếu ở horizon rất ngắn; kết quả cũng nhạy với size, thời kỳ và market state. | Đây là caveat quan trọng: **không giả định momentum luôn bền vững**. DELTA cần risk/liquidity/context features và backtest nghiêm ngặt. **Lưu ý danh sách đọc ban đầu gán paper này cho “Phan & Zhou (2012)”, nhưng DOI/title được publisher xác minh là paper của Thu Hang Nguyen.** |
| **A4. [Le & Bertrand (2023) — Overreaction and momentum in the Vietnamese stock market](https://doi.org/10.1108/MF-01-2022-0013)**. Tìm quan hệ giữa momentum và overreaction/volume. | Weekly data của **hơn 300 cổ phiếu phi tài chính Việt Nam**, khoảng **2009–2019**. | Xây proxy overreaction kết hợp trading volume và dấu của stock return; so sánh chiến lược overreaction với price momentum, dùng adjusted returns và double sorts để tách hai hiệu ứng. | Momentum tồn tại, nhưng overreaction cũng có sức dự báo đáng kể. Khi kiểm soát overreaction, momentum có thể mất ý nghĩa; kết quả hỗ trợ cách giải thích momentum gắn với behavioral overreaction. | Volume/liquidity có lý do để được giữ trong market feature family. Kết quả cũng nhắc rằng **momentum không phải latent factor duy nhất**; clustering nên dùng nhiều chiều thay vì chỉ risk-adjusted momentum. |
| **A5. [Butt, Kolari & Sadaqat (2021) — Revisiting momentum profits in emerging markets](https://doi.org/10.1016/j.pacfin.2020.101486)**. Đặt momentum trong bối cảnh emerging markets, liquidity risk và down-market states. | **19 emerging markets**, khoảng **01/1991–09/2017**, tổng cộng khoảng **14.672 cổ phiếu**, dữ liệu Thomson Reuters Datastream. | Phân tích cross-sectional/time-series momentum, CAPM/Fama–French controls, market/liquidity/down-market states, volatility-scaled risk management và panel regressions. | Momentum profits ở emerging markets nhìn chung thấp hơn developed markets và có exposure bất lợi với market/liquidity risk, đặc biệt trong down states. Risk management giúp cải thiện risk-adjusted performance trong nhiều trường hợp. | Củng cố việc giữ **volatility, downside volatility, liquidity** và xem xét market regime. Sharpe/risk-adjusted outcome chỉ thuộc **M3 portfolio evaluation**, không phải cluster feature/quality metric. |

---

## B — Phân cụm cổ phiếu và portfolio

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **B6. [Han, He & Toh (2023) — Pairs trading via unsupervised learning](https://doi.org/10.1016/j.ejor.2022.09.041)**. Nghiên cứu unsupervised learning cho việc tìm các cổ phiếu tương đồng/pairs. | Thị trường cổ phiếu Hoa Kỳ, khoảng **01/1980–12/2020**. | Ghép **price information với firm characteristics** và dùng clustering để nhận diện pairs; nghiên cứu so sánh nhiều clustering approaches, gồm K-Means/DBSCAN/Agglomerative trong phần thiết kế thực nghiệm. | Firm characteristics bổ sung đáng kể thông tin so với chỉ dùng giá. Agglomerative-based pair selection cho performance mạnh trong báo cáo thực nghiệm; kết quả vẫn được kiểm tra với transaction costs và robustness/data-snooping controls. | Đây là paper rất phù hợp cho hướng **market + fundamental features** của DELTA. Hỗ trợ K-Means baseline + Agglomerative/DBSCAN comparators. Portfolio performance vẫn là downstream evidence, không phải tiêu chí cluster quality. |
| **B7. [Nanda, Mahanty & Tiwari (2010) — Clustering Indian stock market data for portfolio management](https://doi.org/10.1016/j.eswa.2010.06.026)**. Ví dụ clustering cổ phiếu ở emerging market để hỗ trợ portfolio construction. | **106 cổ phiếu BSE**, fiscal year **2007–2008**, dữ liệu Capitaline Databases Plus; mẫu gồm nhiều sector và market-cap groups. | Dùng stock returns ở các thời điểm khác nhau và **valuation ratios**; so sánh **K-Means, Self-Organizing Map và Fuzzy C-Means**; sau đó chọn cổ phiếu từ các cluster và xây Markowitz portfolio. | K-Means tạo các cluster compact nhất trong thí nghiệm của paper; cluster-based selection được dùng để đa dạng hóa danh mục và giảm rủi ro so với lựa chọn không phân cụm. | Hỗ trợ quyết định **không chỉ dùng market returns mà còn thêm valuation/fundamental characteristics**. K-Means được giữ làm static baseline. |
| **B8. [Ebrahimi, Amini & Liu (2026) — Cardinality-constrained portfolio optimization with clustering](https://doi.org/10.1007/s10479-026-07184-z)**. Dùng clustering để giảm độ phức tạp của portfolio optimization có cardinality constraints. | Các bộ dữ liệu lớn như **S&P 500 và Russell 3000**. | Hierarchical clustering dựa trên tương quan residual returns; chia bài toán cardinality-constrained portfolio thành các subproblems nhỏ hơn, sau đó tối ưu số tài sản và cluster weights. | Framework clustering giúp đơn giản hóa large-scale asset selection và đạt performance cạnh tranh so với các benchmark optimization truyền thống trong nghiên cứu. | Tham khảo cho **M3/commercial portfolio layer** nếu DELTA phát triển selection constraints. Không dùng để quyết định clustering method ở M2. |
| **B9. [Ban, El Karoui & Lim (2018) — Machine learning and portfolio optimization](https://doi.org/10.1287/mnsc.2016.2644)**. Giải quyết estimation error trong portfolio optimization bằng machine-learning style regularization. | Empirical analysis trên **ba Fama–French datasets**. | Đề xuất **Performance-Based Regularization (PBR)** cho mean-variance và mean-CVaR, cùng performance-based cross-validation; paper kết nối regularization với robust optimization. | PBR cải thiện out-of-sample portfolio performance so với một số phương pháp SAA/L1/L2/equal-weight trên phần lớn bộ dữ liệu được thử. | Dùng cho **M3 methodology** về estimation error, regularization và validation. Không dùng làm bằng chứng cho cluster quality hoặc lựa chọn k. |

---

## C — Thuật toán phân cụm và đánh giá cụm

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **C10. [MacQueen (1967) — Some Methods for Classification and Analysis of Multivariate Observations](https://digicoll.lib.berkeley.edu/record/113015)**. Paper nền tảng của K-Means. | Paper phương pháp; không phải nghiên cứu tài chính với một stock dataset cụ thể. | Trình bày phương pháp phân hoạch population/sample trong không gian nhiều chiều thành **k groups**, tối ưu sự gần nhau trong cluster thông qua cập nhật cluster means. | K-Means trở thành một thủ tục đơn giản, hiệu quả để tạo các nhóm có within-cluster variation thấp. | **Static deterministic K-Means** tiếp tục là baseline B0 của DELTA, không được gọi là Dynamic Clustering. |
| **C11. [Ward (1963) — Hierarchical Grouping to Optimize an Objective Function](https://doi.org/10.1080/01621459.1963.10500845)**. Nền tảng cho Ward hierarchical clustering. | Paper phương pháp, có numerical illustration; không phụ thuộc một financial dataset cụ thể. | Bottom-up hierarchical agglomeration: ở mỗi bước chọn phép merge gây **mức tăng loss/objective nhỏ nhất**, tạo toàn bộ hierarchy. | Cho phép hình thành hierarchy các group và theo dõi quantitative loss tại từng bước merge. | Dùng làm **Ward/Agglomerative comparator** trong M2 và hỗ trợ dendrogram/interpretability. |
| **C12. [Ester, Kriegel, Sander & Xu (1996) — DBSCAN](https://aaai.org/papers/kdd96-037-a-density-based-algorithm-for-discovering-clusters-in-large-spatial-databases-with-noise/)**. Tạo cluster theo mật độ và nhận diện noise/outlier. | Synthetic spatial datasets và benchmark **SEQUOIA 2000** trong paper gốc. | DBSCAN dùng hai tham số cốt lõi **Eps** và **MinPts**, xác định core/border/noise points và density reachability; không yêu cầu k từ trước. | Có thể nhận diện cluster có hình dạng tùy ý và noise; paper báo cáo hiệu quả tốt hơn CLARANS trên các bài thử về arbitrary shapes và scalability. | Comparator phù hợp nếu DELTA muốn **không ép mọi cổ phiếu vào cluster**. Code phải hỗ trợ noise label và variable cluster count; không nhét DBSCAN vào fixed-k abstraction. |
| **C13. [Rousseeuw (1987) — Silhouettes](https://doi.org/10.1016/0377-0427(87)90125-7)**. Đánh giá compactness và separation của clustering. | Paper phương pháp với nhiều ví dụ minh họa; không gắn với một financial dataset duy nhất. | Với mỗi observation, silhouette kết hợp mức gần với own cluster và mức xa với nearest alternative cluster; average silhouette width tóm tắt chất lượng partition. | Silhouette hỗ trợ phát hiện observation được cluster tốt, observation ở biên và so sánh các partitions/k khác nhau. | Dùng trong **cluster-quality evaluation** và development diagnostics. Không phải portfolio metric và không nên là tiêu chí duy nhất để chọn model. |
| **C14. [Davies & Bouldin (1979) — A Cluster Separation Measure](https://doi.org/10.1109/TPAMI.1979.4766909)**. Định nghĩa một measure tương đối cho chất lượng partition. | Paper phương pháp; không cần domain-specific dataset. | So sánh within-cluster scatter với between-cluster separation để tạo **Davies–Bouldin index**. | Chỉ số cho phép so sánh tương đối các partitions độc lập với thuật toán tạo partition; trong formulation thông dụng **DBI thấp hơn là tốt hơn**. | Dùng cùng Silhouette/CH/inertia để đánh giá cluster quality, hoàn toàn tách khỏi Sharpe/ROI. |
| **C15. [Hubert & Arabie (1985) — Comparing partitions](https://doi.org/10.1007/BF01908075)**. Nền tảng cho chance-corrected partition comparison/Adjusted Rand Index. | Paper phương pháp, tập trung vào so sánh partitions. | Phân tích Rand index và hiệu chỉnh ảnh hưởng của agreement ngẫu nhiên; trình bày framework so sánh hai partitions/proximity structures. | Cung cấp nền tảng cho **Adjusted Rand Index (ARI)**, giúp so sánh partitions theo cách không phụ thuộc trực tiếp vào nhãn cluster. | ARI dùng cho **temporal stability giữa snapshots**. ARI cao/thấp chỉ mô tả stability; nó không biến rolling K-Means thành Dynamic Clustering. |

---

## D — Giảm chiều và trực quan hóa

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **D16. [Pearson (1901) — On Lines and Planes of Closest Fit to Systems of Points in Space](https://doi.org/10.1080/14786440109462720)**. Nền tảng hình học của PCA. | Paper toán/phương pháp; các systems of points dùng để minh họa, không phải financial dataset. | Tìm line/plane “best fit” bằng cách tối thiểu hóa tổng bình phương khoảng cách vuông góc của các điểm tới không gian con. | Cung cấp nền tảng hình học cho cách biểu diễn dữ liệu theo các direction giữ variation quan trọng, sau này phát triển thành PCA hiện đại. | PCA là preprocessing option khi feature space có tương quan cao. **Scaler/PCA chỉ fit trên development/snapshot hợp lệ**, không fit future/holdout. |
| **D17. [McInnes, Healy & Melville (2018/2020) — UMAP](https://arxiv.org/abs/1802.03426)**. Nonlinear dimensionality reduction cho visualization/scalable embedding. | Paper benchmark trên nhiều dataset như MNIST/Fashion-MNIST, COIL, PenDigits, Shuttle và các biological/text embeddings. | Manifold-learning framework dựa trên Riemannian geometry và algebraic topology; xây fuzzy topological representation rồi tối ưu low-dimensional embedding. | UMAP cho visualization chất lượng cạnh tranh với t-SNE, thường nhanh hơn và có xu hướng giữ thêm global structure; hỗ trợ embedding dimension tùy ý. | Trong DELTA, **UMAP mặc định là visualization tool cho M2–M3/dashboard**, không phải clustering input hay cluster-quality proof nếu chưa có methodology riêng phê duyệt. |

---

## E — Backtest và thiết kế nghiên cứu tài chính

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **E18. [Markowitz (1952) — Portfolio Selection](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)**. Nền tảng mean–variance portfolio theory. | Paper lý thuyết với illustrative examples; không phải một empirical stock dataset duy nhất. | Mô hình hóa expected return và variance/covariance; tối ưu trade-off giữa expected return và portfolio variance, tạo efficient set/frontier. | Diversification phụ thuộc covariance chứ không chỉ số lượng tài sản; nhà đầu tư hợp lý theo mean–variance nên cân bằng expected return và variance. | Dùng cho framing M3, portfolio diversification và interpretation. Không dùng variance/return outcome để quyết định cluster quality. |
| **E19. [Sharpe (1966) — Mutual Fund Performance](https://www.jstor.org/stable/2351741)**. Nền tảng reward-to-variability performance measure. | **34 open-end mutual funds**, annual performance khoảng **1954–1963**; paper cũng xem prior-period evidence để kiểm tra persistence và so với market/index benchmark. | So sánh average excess return với standard deviation qua **reward-to-variability ratio**, tiền thân trực tiếp của Sharpe Ratio hiện đại. | Paper cho thấy có khác biệt đáng kể giữa fund performance; persistence theo ranking không hoàn hảo và phí/expenses ảnh hưởng mạnh tới realized investor performance. | **Original reading rationale:** feature + strategy evaluation. **Current DELTA decision:** Sharpe chỉ thuộc **portfolio evaluation ở M3**, không phải clustering feature, cluster-quality metric hoặc model-selection input. |
| **E20. [Lo (2002) — The Statistics of Sharpe Ratios](https://doi.org/10.2469/faj.v58.n4.2453)**. Làm rõ statistical properties và annualization của Sharpe. | Theoretical derivation cộng empirical mutual/hedge-fund illustrations. | Suy ra asymptotic distribution của Sharpe dưới các assumptions khác nhau; phân tích iid vs stationary serially correlated returns và aggregation across frequencies. | Quy tắc nhân monthly Sharpe với `sqrt(12)` chỉ đúng trong các điều kiện đặc biệt. Serial correlation có thể làm annualized Sharpe bị phóng đại đáng kể và làm thay đổi fund rankings. | Khi báo cáo Sharpe ở M3, DELTA phải ghi rõ return frequency/serial-correlation assumption; không annualize máy móc nếu dữ liệu vi phạm iid. |
| **E21. [Bailey, Borwein, López de Prado & Zhu (2017) — The Probability of Backtest Overfitting](https://doi.org/10.21314/JCF.2016.322)**. Đo xác suất một strategy được chọn vì backtest overfit. | Paper phương pháp với investment simulations / strategy-selection examples hơn là một single-market dataset cố định. | Đề xuất **Probability of Backtest Overfitting (PBO)** và **Combinatorially Symmetric Cross-Validation (CSCV)** để đo nguy cơ strategy selection bị overfit. | Standard holdout có thể không đủ đáng tin khi researcher thử nhiều alternatives; CSCV cho phép ước lượng xác suất strategy “winner” in-sample thất bại out-of-sample. | Củng cố nguyên tắc **M2 không nhìn portfolio performance để tune model**, methodology freeze trước M3/final holdout, và lưu toàn bộ experiment attempts. |
| **E22. [López de Prado (2018) — Advances in Financial Machine Learning](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)**. Tổng hợp các kỹ thuật giảm leakage/backtest bias trong financial ML. | Sách phương pháp, không có một empirical dataset duy nhất. | Các chương về cross-validation in finance, purged K-fold, embargo, feature importance, hyperparameter tuning, backtesting và dangers of backtesting. | Nhấn mạnh rằng time-series/financial labels thường overlap và standard CV có thể leak; purging/embargo giúp giảm overlap leakage khi bài toán có label/holding horizons phù hợp. | Dùng làm protocol reference cho validation/backtest. Chỉ áp dụng purging/embargo khi data/label structure của DELTA thực sự tạo overlap cần xử lý; không áp dụng máy móc. |

---

## F — Dynamic / Temporal Clustering — bổ sung sau mentor review

> Nhóm này **không nằm trong danh sách 22 tài liệu ban đầu**. Nó được bổ sung vì mentor yêu cầu nghiên cứu **Dynamic Clustering**. Việc đưa paper vào matrix **không đồng nghĩa tự động phê duyệt implementation**; `DYNAMIC_CLUSTERING_REVIEW.md` vẫn cần explicit methodology/mentor approval trước khi code concrete model.

| Mục đích | Dữ liệu | Phương pháp | Kết quả chính | Áp dụng vào DELTA |
|---|---|---|---|---|
| **F1. [Chakrabarti, Kumar & Tomkins (2006) — Evolutionary Clustering](https://doi.org/10.1145/1150402.1150467)**. Đặt bài toán clustering khi data thay đổi theo thời gian và yêu cầu cluster không “nhấp nháy” vô lý. | Paper phương pháp với synthetic/real dynamic datasets dùng để minh họa evolutionary clustering. | Tối ưu trade-off giữa **snapshot quality** ở thời điểm hiện tại và **temporal smoothness/history cost** so với clustering trước; paper xây evolutionary variants của K-Means và agglomerative clustering. | Có thể giữ chất lượng partition hiện tại đồng thời tăng consistency/fidelity với historical clustering, giảm các thay đổi cluster không cần thiết. | Là conceptual baseline rất phù hợp để phân biệt **true temporal clustering** với “independent monthly K-Means + ARI”. Hữu ích để thiết kế objective có temporal penalty. |
| **F2. [João, Lucas, Schaumburg & Schwaab (2023) — Dynamic clustering of multivariate panel data](https://doi.org/10.1016/j.jeconom.2022.03.003)**. Mô hình cluster membership thay đổi qua thời gian trong panel data. | Khoảng **299 ngân hàng châu Âu**, quarterly data **2008Q1–2018Q2**, với khoảng **12 indicators** thuộc nhiều nhóm business-model characteristics; paper cũng dùng Monte Carlo experiments. | Cluster parameters thay đổi theo thời gian kết hợp **Hidden Markov Model** cho membership transitions; transition probabilities có thể phụ thuộc lagged distances và economic covariates. | Monte Carlo cho thấy framework có thể ước lượng dynamic clusters/transitions; application cho ngân hàng cho thấy một tỷ lệ nhỏ nhưng đáng kể institutions đổi cluster theo quý và covariates như profitability liên quan đến transitions. | Là một candidate dynamic method mạnh nhưng tương đối phức tạp. Phù hợp làm **advanced reference/alternative** nếu DELTA cần probabilistic transitions và covariate-dependent switching. |
| **F3. [João, Schaumburg, Lucas & Schwaab (2024) — Dynamic Nonparametric Clustering of Multivariate Panel Data](https://doi.org/10.1093/jjfinec/nbac038)**. Giảm cluster “flickering” bằng temporal persistence trong panel clustering. | Empirical application trên khoảng **28 large European insurance firms**, **2010–2020**, với một nhóm accounting ratios; kèm simulation studies. | Mở rộng cross-sectional clustering, bao gồm K-Means-style assignment, bằng **persistence/shrinkage penalty** kéo observation tại thời điểm hiện tại về previous cluster center; penalty có thể chọn data-driven; framework cho phép cluster locations/shapes/composition thay đổi theo thời gian. | Temporal regularization giúp giảm excessive reclassification/flickering trong khi vẫn cho phép genuine structural change; simulations/application cho thấy cluster membership ổn định và diễn giải động tốt hơn static independent re-fitting. | Đây là **candidate gần nhất với kiến trúc hiện tại của DELTA**: static K-Means baseline + temporal persistence. Nên là phương pháp ưu tiên để full-text methodology review trước khi mentor quyết định concrete Dynamic Clustering implementation. |

---

# Tổng hợp quyết định áp dụng vào DELTA

## 1. Feature space

Literature không ủng hộ việc biến DELTA thành một hệ thống chỉ dựa vào `momentum / volatility`.

Feature research nên tách thành các family:

- **Momentum:** 1M / 3M / 6M / 12M;
- **Risk:** volatility, downside volatility, maximum drawdown, beta;
- **Liquidity/activity:** traded value/turnover và các biến đã xác minh semantics;
- **Fundamentals:** profitability, growth, leverage, liquidity, valuation/size sau khi taxonomy và PIT definitions được khóa.

Các paper Việt Nam cho thấy momentum có tồn tại nhưng **không ổn định trong mọi risk/state/period control**, nên feature space đa chiều là hợp lý hơn một momentum-only model.

## 2. Baseline và comparators

M2 nên giữ cấu trúc:

1. **Static K-Means** — baseline chính;
2. **PCA + K-Means** — dimensionality-reduction baseline;
3. **Ward/Agglomerative** — deterministic hierarchical comparator;
4. **DBSCAN** — optional density/noise comparator sau khi interface hỗ trợ noise + variable k;
5. **GMM** — optional comparator nếu covariance/initialization protocol được duyệt;
6. **Dynamic/Temporal model** — chỉ triển khai sau `DYNAMIC_CLUSTERING_REVIEW.md` được approval.

## 3. Dynamic Clustering

Independent K-Means ở từng tháng rồi tính ARI/NMI/transition **không phải Dynamic Clustering**.

Trong ba paper nhóm F:

- **Evolutionary Clustering (2006)** cho conceptual objective “snapshot quality + temporal smoothness”;
- **Dynamic clustering of multivariate panel data (2023)** mạnh về probabilistic/HMM transitions nhưng phức tạp;
- **Dynamic Nonparametric Clustering (2024)** gần DELTA nhất vì có persistence penalty và có thể xây tiếp từ static clustering baseline.

**Khuyến nghị research hiện tại:** ưu tiên đọc sâu F3 để xem có thể biến thành proposed temporal model của DELTA hay không; F2 là advanced alternative/comparator về mặt methodology.

## 4. PCA và UMAP

- **PCA:** có thể dùng preprocessing khi features tương quan cao, nhưng fit phải leakage-safe trong development/snapshot.
- **UMAP:** mặc định chỉ dùng cho visualization/dashboard. Không dùng UMAP embedding như clustering input hoặc bằng chứng cluster quality nếu chưa có protocol riêng.

## 5. Evaluation phải có ba lớp độc lập

### Cluster quality

- Silhouette;
- Davies–Bouldin;
- Calinski–Harabasz;
- inertia;
- cluster balance.

### Temporal stability

- ARI;
- NMI;
- persistence;
- migration rate;
- transition matrix;
- centroid drift;
- entry/exit.

### Portfolio performance

- cumulative return/CAGR;
- volatility;
- Sharpe;
- Sortino;
- maximum drawdown;
- Calmar;
- turnover;
- transaction costs;
- alpha/beta;
- information ratio.

**Sharpe/ROI không được dùng làm clustering feature hoặc cluster-quality metric.**

## 6. Backtest protocol

Literature về Sharpe và backtest overfitting củng cố architecture hiện tại:

```text
M2 model development
    ↓
cluster + temporal evaluation
    ↓
methodology freeze
    ↓
M3 portfolio evaluation
    ↓
final holdout / sensitivity
```

Không chọn:

- `k`;
- feature set;
- PCA component count;
- algorithm;
- temporal penalty

dựa vào portfolio return hoặc Sharpe.

---

# Evidence status

Matrix này được biên soạn từ các nguồn primary/publisher records có thể truy cập tại thời điểm review:

- full-text/primary text khi tài liệu mở;
- publisher abstracts và primary metadata khi full text bị giới hạn;
- table-of-contents/official publisher material cho sách.

Vì vậy “hoàn chỉnh” ở đây có nghĩa là **không còn placeholder `PENDING` cho 22 tài liệu gốc**, nhưng không có nghĩa mọi paper đều được truy cập toàn bộ licensed PDF. Những claim cụ thể về sample/method/result chỉ được đưa vào khi nguồn primary/public material hỗ trợ.

## Bibliographic correction cần cập nhật trong project

Danh sách đọc ban đầu và bản matrix cũ ghi:

> “Phan, D. B. A., & Zhou, J. (2012). Momentum Effect in the Vietnamese Stock Market. DOI 10.1016/S2212-5671(12)00078-0.”

Metadata/publisher record của DOI này xác nhận bài:

> **Nguyen, Thu Hang (2012), “Momentum Effect in the Vietnamese Stock Market.”**

DELTA nên sửa citation A3 để tránh lỗi bibliography trong report/thesis.

---

# Links

### Nhóm A
- Jegadeesh & Titman (1993): https://doi.org/10.1111/j.1540-6261.1993.tb04702.x
- Vo & Truong (2018): https://doi.org/10.1016/j.jbef.2017.12.002
- Nguyen (2012): https://doi.org/10.1016/S2212-5671(12)00078-0
- Le & Bertrand (2023): https://doi.org/10.1108/MF-01-2022-0013
- Butt et al. (2021): https://doi.org/10.1016/j.pacfin.2020.101486

### Nhóm B
- Han et al. (2023): https://doi.org/10.1016/j.ejor.2022.09.041
- Nanda et al. (2010): https://doi.org/10.1016/j.eswa.2010.06.026
- Ebrahimi et al. (2026): https://doi.org/10.1007/s10479-026-07184-z
- Ban et al. (2018): https://doi.org/10.1287/mnsc.2016.2644

### Nhóm C
- MacQueen (1967): https://digicoll.lib.berkeley.edu/record/113015
- Ward (1963): https://doi.org/10.1080/01621459.1963.10500845
- Ester et al. (1996): https://aaai.org/papers/kdd96-037-a-density-based-algorithm-for-discovering-clusters-in-large-spatial-databases-with-noise/
- Rousseeuw (1987): https://doi.org/10.1016/0377-0427(87)90125-7
- Davies & Bouldin (1979): https://doi.org/10.1109/TPAMI.1979.4766909
- Hubert & Arabie (1985): https://doi.org/10.1007/BF01908075

### Nhóm D
- Pearson (1901): https://doi.org/10.1080/14786440109462720
- UMAP: https://arxiv.org/abs/1802.03426

### Nhóm E
- Markowitz (1952): https://doi.org/10.1111/j.1540-6261.1952.tb01525.x
- Sharpe (1966): https://www.jstor.org/stable/2351741
- Lo (2002): https://doi.org/10.2469/faj.v58.n4.2453
- Bailey et al. (2017): https://doi.org/10.21314/JCF.2016.322
- López de Prado (2018): https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086

### Nhóm F
- Chakrabarti et al. (2006): https://doi.org/10.1145/1150402.1150467
- João et al. (2023): https://doi.org/10.1016/j.jeconom.2022.03.003
- João et al. (2024): https://doi.org/10.1093/jjfinec/nbac038
