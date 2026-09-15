# Research protocol

## Trạng thái bằng chứng

Project hiện là **monthly snapshot K-Means baseline with temporal tracking**, chưa phải một thuật toán Dynamic Clustering đã được literature/mentor phê duyệt. Engineering core có thể dùng cho product, nhưng kết quả pilot không phải kết luận khóa luận hoặc khuyến nghị đầu tư.

Đã đọc toàn bộ file chỉ đạo 1.266 dòng, toàn bộ mục đích của danh sách 22 paper và các PDF kế hoạch nội bộ. Aslam (2025) đã được đọc toàn văn; Han, Nanda và DBSCAN đã được kiểm tra phần chính; 19 mục còn lại vẫn cần full-text review có page/section trước khi khóa methodology.

| Nhóm | Mục đích | Trạng thái |
|---|---|---|
| Momentum/Vietnam | horizon 3/6/12 tháng, volume, liquidity, down-market caveats | cần full-text |
| Clustering/portfolio | stock selection, pairs, cardinality, comparator | Han/Nanda partial; còn lại cần full-text |
| Algorithms/metrics | K-Means, Ward, DBSCAN, Silhouette, DBI, ARI | DBSCAN primary checked; còn lại cần full-text |
| PCA/visualization | PCA cho correlated features; UMAP downstream visualization | cần full-text |
| Portfolio/backtest | Markowitz, Sharpe/Lo, overfit, purging/embargo | cần full-text |
| Aslam replication | AT/AAT, extreme-price penalty, mu/sigma, annual rebalance | full-text; nhánh riêng |

Danh sách DOI/URL đầy đủ vẫn nằm trong `../TaiLieu/TaiLieuThamKhao/CacBaiBaoLienQuan.txt`; PDF nguồn không bị sửa hoặc sao chép vào code repository.

## Ba nhánh nghiên cứu

1. **Aslam replication:** tái lập đúng biến/cửa sổ/k/rebalance của paper. Chưa triển khai.
2. **Delta baseline:** monthly cross-section, snapshot-only preprocessing, K-Means, label alignment, ARI/transitions. Đã có prototype.
3. **Approved temporal method:** chỉ triển khai sau khi chốt paper, objective và temporal mechanism. Không đổi tên nhánh 2 thành nhánh 3.

## Universe và point-in-time

- Real clustering cần ít nhất ba calendar years của giá usable thực sự quan sát được tới `as_of_date`.
- Thiếu lịch sử: `REFERENCE_ONLY`; lỗi identity/status/required feature: `EXCLUDED`; chỉ `ELIGIBLE_FOR_CLUSTERING` được fit.
- Mọi input phải có `available_at <= decision_at`.
- Financial facts cần `available_at >= published_at >= period_end`; restatement tạo vintage mới.
- Không dùng danh sách ticker hiện tại để suy historical universe; không forward-fill gap hoặc biến NA thành zero.

## Feature protocol

`r_t=P_t/P_(t-1)-1`; tỷ lệ ở dạng thập phân.

| Feature | Định nghĩa | Cửa sổ tối thiểu |
|---|---|---:|
| `mom_21/63/126/252` | `P_t/P_(t-L)-1` | `L+1` prices |
| `vol_63/126` | sample std(returns) × `sqrt(252)` | `L` returns |
| `downside_vol_63` | `sqrt(252*mean(min(r,0)^2))` | 63 returns |
| `mdd_126` | min(`P/running_max(P)-1`) | 126 prices |
| `beta_126` | paired covariance / benchmark variance | 126 paired returns |
| `liquidity_21` | mean verified traded value | 21 values |
| `ram_63` | `mom_63/vol_63` | baseline hypothesis |

`sharpe_*` chỉ tồn tại để đọc artifact cũ và đánh giá portfolio. Sharpe/ROI bị cấm trong clustering inputs, required features, cluster-quality criteria và security selection. Financial ratio mới cần citation, item mapping, period type, denominator, sector treatment, publication timing và restatement rule.

## Preprocessing, models và temporal evaluation

- Winsorize/transform/scale riêng từng snapshot và lưu parameters.
- K-Means có seed, `n_init`, `max_iter`, convergence và tie-breaking xác định.
- `k` được pre-register hoặc chọn bằng cluster criteria trên development set; không chọn bằng backtest return.
- PCA là thí nghiệm `PCA vs no-PCA`; fit sau scaler, không nhìn holdout; lưu loadings/explained variance.
- Ward/DBSCAN chỉ là comparator nếu synthesis giữ lại. UMAP mặc định chỉ để visualization.
- Nhãn cluster phải alignment trên shared identities. ARI/NMI độc lập hoán vị; transitions chỉ diễn giải sau alignment; entered/exited được báo riêng.

## Backtest protocol

Tín hiệu cuối kỳ chỉ khớp từ phiên sau khi dữ liệu khả dụng. Current engine là fractional return-space simulation, không phải share/lot/settlement ledger. Chi phí áp dụng hai chiều; cash, turnover, gross/net và benchmark phải tách rõ.

Cluster quality: inertia, Silhouette, CH, DBI, size/balance. Temporal quality: ARI/NMI, persistence, transitions, centroid drift. Portfolio outcome: CAGR/return, volatility, Sharpe, Sortino, MDD, Calmar, turnover, costs, alpha/beta/information ratio. Không dùng nhóm cuối để hợp thức hóa chất lượng cụm.

Development/validation/holdout, purging/embargo và percentage-vs-top-N policy phải khóa trước final run. Pilot 10 mã 2023–2025 là `LEGACY_NONCOMPLIANT_PILOT`: chỉ kiểm tra plumbing vì early snapshots không đạt warm-up ba năm và universe có survivorship/PIT limitations.

## Research gates còn mở

1. Full-text synthesis 22 paper có page/section.
2. Chốt research question và định nghĩa Dynamic Clustering.
3. Chốt financial feature families và universe lịch sử.
4. Chạy representative pilot 20–50 mã, >=5 năm.
5. Khóa model-selection/holdout protocol trước scale 1.200+.
