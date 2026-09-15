# Literature matrix

Matrix này ghi trạng thái bằng chứng, không biến citation chưa đọc thành approval.

| Nhóm | Vai trò với DELTA | Trạng thái hiện tại | Output cần có |
|---|---|---|---|
| Momentum/Vietnam | horizon, liquidity, down-market caveat | cần full-text synthesis | formula + page/section + decision |
| Clustering/portfolio | baseline/comparator và downstream use | partial review | assumptions + dataset + applicability |
| K-Means/Ward/DBSCAN/GMM | thuật toán và failure modes | DBSCAN partial; còn lại cần review | comparator rationale |
| Silhouette/DBI/CH/ARI/NMI | cluster/temporal metric | cần primary-source lock | exact definition + implementation test |
| PCA/UMAP | reduction vs visualization | cần review | leakage-safe protocol |
| Backtest/overfit | holdout, costs, inference | cần full-text synthesis | frozen evaluation protocol |
| Aslam (2025) | separate replication arm | full-text reviewed | không trộn với DELTA baseline |

Mỗi entry được bổ sung phải có citation, page/section, sample, variable/formula, finding, limitation và quyết định áp dụng/không áp dụng. Danh sách nguồn nội bộ nằm ngoài code repository; không sao chép licensed PDF vào `docs/`.
