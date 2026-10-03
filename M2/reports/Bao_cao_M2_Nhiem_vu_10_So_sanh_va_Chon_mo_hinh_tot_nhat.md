# Báo cáo M2 — Nhiệm vụ 10: So sánh và chọn Final Method

## 1. Mục tiêu và rào chắn

Nhiệm vụ 10 chọn một mô hình cuối cùng giữa KMeans Baseline, Ward Hierarchical và PCA + KMeans trên 15 snapshot development, từ 2023-11-30 đến 2025-01-24. Ba phương án dùng cùng universe rule `market_feature_ready_v2`, cùng 8 feature thị trường, Robust Scaling riêng theo từng snapshot và Global K = 2.

Quyết định không dùng Final Holdout, return, CAGR, Sharpe, Sortino, ROI, Calmar, alpha hay backtest. Báo cáo chỉ đánh giá cấu trúc cụm và độ ổn định theo thời gian, không khẳng định hiệu quả đầu tư.

## 2. Nguồn bằng chứng và kiểm định đầu vào

Notebook Task 10 đọc quality summary, profile Task 8, temporal stability, diagnostics K=2 và centroid drift của ba phương án. Mỗi quality summary có 5 metric, 7 cột và đủ 15/15 snapshot. Mỗi temporal file có 14 cặp tháng liên tiếp. Mỗi profile có 30 hàng, tương ứng 15 snapshot × 2 cụm.

Khác biệt schema profile chỉ được chuẩn hóa trong bộ nhớ: KMeans bỏ hậu tố `_mean`; Ward dùng 8 feature trực tiếp; PCA+KMeans giải mã trường `centroid`. Artifact nguồn không bị ghi đè. Mười lăm model KMeans trong `M2/models/final_selected_model/` đã được đối chiếu SHA-256 với nguồn Task 4.

## 3. Chất lượng phân cụm hình học

| Phương án | Median Silhouette | Mean Silhouette | Median DB | Median CH | Median Balance |
| --- | ---: | ---: | ---: | ---: | ---: |
| KMeans Baseline | 0.755722 | 0.791489 | 0.521899 | 316.39 | 0.067669 |
| Ward Hierarchical | 0.755722 | 0.763118 | 0.534333 | 316.39 | 0.067669 |
| PCA + KMeans | 0.771666 | 0.804410 | 0.515502 | 361.53 | 0.067669 |

### Nhận xét bảng chất lượng

- PCA + KMeans dẫn đầu về hình học: Median Silhouette 0.771666, DB 0.515502 và CH 361.53. Lợi thế Silhouette so với KMeans là 0.015945.
- KMeans và Ward có cùng Median Silhouette 0.755722 và cùng Balance 0.067669. KMeans có DB thấp hơn Ward, 0.521899 so với 0.534333, nên Ward không có lợi thế hình học để được ưu tiên.
- Ward biến động hơn theo snapshot: SD Silhouette là 0.157756, cao hơn KMeans 0.112640 và PCA 0.104001. Minimum Silhouette Ward là 0.458851, thấp hơn KMeans 0.636868 và PCA 0.659505.
- Balance thấp giống nhau không có nghĩa hai cụm cân bằng. Nó phản ánh cấu trúc một cụm nhỏ và một cụm lớn ở cả ba phương án; vì vậy cần đọc cùng minimum cluster size.

## 4. Độ ổn định theo thời gian

| Phương án | Median ARI | Median NMI | Median Persistence | Median Migration |
| --- | ---: | ---: | ---: | ---: |
| KMeans Baseline | 0.798251 | 0.661313 | 98.56% | 1.44% |
| Ward Hierarchical | 0.537278 | 0.439157 | 96.23% | 3.77% |
| PCA + KMeans | 0.798251 | 0.661313 | 98.56% | 1.44% |

### Nhận xét bảng ổn định

- KMeans và PCA+KMeans có các chỉ số temporal bằng nhau trong 14 cặp development.
- Ward kém ổn định rõ rệt: thấp hơn KMeans 0.260973 ARI và migration cao hơn 2.33 điểm phần trăm.
- Persistence cao là trung vị trên 14 cặp tháng; nó không phải cam kết từng cổ phiếu luôn giữ nguyên cụm.

## 5. Sanity check, profile và centroid drift

| Phương án | Min cluster size | Biểu diễn profile | Sanity |
| --- | ---: | --- | --- |
| KMeans Baseline | 8 | 8 feature với hậu tố `_mean` | PASS |
| Ward Hierarchical | 6 | 8 feature trực tiếp | PASS |
| PCA + KMeans | 8 | JSON `centroid` | PASS |

Không phương án nào sinh cụm dưới 5 mã. Cả ba vượt ngưỡng sanity của kế hoạch, nhưng balance thấp vẫn là giới hạn cần nêu khi diễn giải các cụm.

| Phương án | Median abs(delta) centroid |
| --- | ---: |
| KMeans Baseline | 0.039946 |
| Ward Hierarchical | 0.043980 |
| PCA + KMeans | 0.039946 |

Centroid drift chỉ là bằng chứng bổ sung. Các feature có đơn vị khác nhau, đặc biệt `liquidity_21`, nên mean/max drift tổng hợp bị chi phối bởi thang đo thanh khoản và không được dùng để xếp hạng chính. Median drift Ward cao hơn KMeans/PCA, phù hợp với tín hiệu Ward kém ổn định hơn nhưng không thay thế ARI, NMI và Migration.

## 6. Ma trận quyết định năm tầng

| Tầng | Bằng chứng thực tế | Phán quyết |
| --- | --- | --- |
| 1. Silhouette | PCA: 0.771666, cao nhất | PCA dẫn đầu nhẹ về hình học |
| 2. Davies–Bouldin | PCA: 0.515502; KMeans: 0.521899; Ward: 0.534333 | PCA tốt nhất; KMeans tốt hơn Ward |
| 3. Sanity check | Cả ba PASS; min size 8/6/8 | Không loại phương án nào |
| 4. Temporal stability | KMeans = PCA; cả hai tốt hơn Ward | Ward không có lợi thế độ bền |
| 5. Occam | Chênh PCA–KMeans = 0.015945, nhỏ hơn 0.03 | Chọn KMeans, pipeline Low complexity |

Occam không phủ nhận chất lượng PCA. Quy tắc được khóa trước: lợi ích của phương án phức tạp phải đạt ít nhất 0.03 Silhouette để vượt KMeans, nếu KMeans không thất bại ở sanity hoặc temporal stability.

## 7. Luận điểm 1 — Vì sao chọn KMeans Baseline?

### Kết luận cần hiểu trước

KMeans được chọn **không phải vì đứng đầu tất cả chỉ số**. PCA + KMeans có chất lượng hình học nhỉnh hơn một chút. KMeans được chọn vì khi nhìn toàn bộ thứ tự tiêu chí đã khóa, phần hơn của PCA chưa đủ lớn để đánh đổi với một pipeline phức tạp hơn, trong khi KMeans vẫn tốt hơn Ward và ổn định ngang PCA.

### So sánh với Ward: KMeans tốt hơn ở đâu?

Hãy hiểu hai chỉ số đầu tiên như sau: **Silhouette cao hơn** nghĩa là các cổ phiếu trong cùng cụm giống nhau hơn và hai cụm tách rõ hơn; **Davies–Bouldin (DB) thấp hơn** nghĩa là cụm gọn hơn và ít chồng lấp hơn.

KMeans và Ward có cùng Median Silhouette `0.755722`, nên Ward không tạo ra ranh giới cụm rõ hơn KMeans. Khi hai phương án hòa ở chỉ số chính, DB dùng để phân biệt: KMeans đạt `0.521899`, thấp hơn Ward `0.534333`, tức cấu trúc KMeans gọn hơn một chút.

Kết quả theo thời gian cũng nghiêng về KMeans. ARI của KMeans là `0.798251`, cao hơn Ward `0.537278`; nói đơn giản, cách KMeans giữ các cổ phiếu chung trong cùng nhóm qua tháng kế tiếp nhất quán hơn. Migration của KMeans là `1.44%`, thấp hơn Ward `3.77%`; tức ít cổ phiếu đổi cụm hơn. Vì Ward không hơn KMeans về chất lượng hình học, quy mô cụm hay độ ổn định, không có lý do thực chứng để chọn pipeline hierarchical phức tạp hơn.

### So sánh với PCA + KMeans: vì sao không chọn phương án có điểm hình học cao hơn?

PCA + KMeans thực sự tốt hơn nhẹ về hình học: Silhouette `0.771666` so với `0.755722`, và DB `0.515502` so với `0.521899`. Khoảng cách Silhouette là `0.015945`.

Tuy nhiên, kế hoạch đã khóa quy tắc Occam trước khi xem kết quả: nếu KMeans và phương án phức tạp chênh dưới `0.03` Silhouette, ưu tiên KMeans nếu KMeans không thất bại ở sanity check hoặc ổn định thời gian. Khoảng cách thực tế `0.015945` nhỏ hơn `0.03`.

Điểm quan trọng là PCA không cải thiện các phần còn lại: Balance, ARI, NMI, Persistence và Migration của PCA + KMeans bằng KMeans. Nói cách khác, PCA cho một lợi ích hình học nhỏ, nhưng không làm cấu trúc ổn định hơn theo tháng. KMeans làm việc trực tiếp trên 8 feature gốc; PCA cần thêm bước giảm chiều và phải giải mã centroid để quay lại giải thích các feature này. Vì vậy KMeans là lựa chọn đơn giản hơn mà không đánh đổi một cải thiện đủ lớn đã được quy định trước.

### Kết luận của luận điểm 1

KMeans vượt Ward bằng bằng chứng chất lượng và ổn định. PCA + KMeans vượt KMeans nhẹ về hình học, nhưng không vượt ngưỡng Occam và không cải thiện temporal stability. Đây là lý do KMeans được chọn theo quy tắc đã khóa, thay vì chọn theo cảm giác hoặc theo một chỉ số riêng lẻ.

## 8. Luận điểm 2 — Vì sao loại các comparator?

### Ward Hierarchical

Ward không bị loại vì thuật toán phân cấp “không tốt”; nó bị loại vì trên dữ liệu development hiện có, lợi ích của nó không xuất hiện trong các chỉ số cần thiết. Ward hòa KMeans ở Silhouette, kém hơn ở DB, có minimum Silhouette thấp hơn và biến động Silhouette lớn hơn. Sang kiểm tra thời gian, Ward có ARI/NMI thấp hơn, Persistence thấp hơn và Migration cao hơn.

Vì vậy, nếu chọn Ward thì nhóm phải chấp nhận một pipeline Medium complexity nhưng không nhận được chất lượng cụm hay độ bền tốt hơn. Quyết định loại Ward là kết luận từ số liệu, không phải đánh giá chung rằng Ward không thể phù hợp với dữ liệu khác.

### PCA + KMeans

PCA + KMeans là comparator mạnh nhất về metric hình học, nên cần diễn giải thận trọng hơn. Nó không bị loại vì kết quả kém; ngược lại, Silhouette, DB và CH đều tốt nhất trong ba phương án.

Lý do loại là **đánh đổi không đủ lớn**. Lợi thế Silhouette chỉ `0.015945`, thấp hơn ngưỡng `0.03` đã định trước. Đồng thời PCA không cải thiện Balance hay bốn chỉ số temporal. Nếu không có ngưỡng Occam, việc chọn PCA chỉ vì điểm hình học cao nhất có thể hợp lý; nhưng làm như vậy sẽ phá vỡ quy tắc đã khóa trước khi nhìn kết quả. Giữ nguyên quy tắc làm quyết định có thể tái lập và tránh việc thay đổi tiêu chí để ưu ái phương án có lợi thế nhỏ.

## 9. Luận điểm 3 — Freeze, tái lập và giới hạn

### Freeze có nghĩa là gì?

Freeze nghĩa là sau Task 10, nhóm không còn được mở lại cuộc thi giữa ba phương án. Mô hình đã chọn là **KMeans Baseline** với **Global K = 2**. Cùng với thuật toán và K, nhóm cũng khóa 8 feature, universe rule `market_feature_ready_v2`, Robust Scaling riêng cho từng snapshot và 15 JSON model development đã chọn.

### Khi sang Final Holdout, nhóm được và không được làm gì?

Task 11 chỉ chạy KMeans Baseline trên 7 snapshot holdout. Nhóm được phép ghi nhận trung thực nếu Silhouette, stability hoặc profile giảm. Nhóm không được dùng kết quả đó để quay lại đổi K, thêm PCA, đổi feature, đổi scaler hoặc gọi lại Ward/PCA để tìm kết quả tốt hơn. Hai comparator vẫn được lưu làm bằng chứng development, nhưng không được chạy lại để chọn lại Final Method.

### Giới hạn của kết luận

Kết luận này không nói KMeans sẽ tạo lợi nhuận cao hơn, dự báo giá tốt hơn hay tạo danh mục tốt hơn. M2 chỉ trả lời câu hỏi về cấu trúc nhóm cổ phiếu. Đánh giá lợi nhuận, rủi ro danh mục, chi phí giao dịch và benchmark thuộc Milestone M3 và phải được thực hiện tách biệt.

## 10. Artifact tham chiếu

- `M2/notebooks/10_model_comparison.ipynb`
- `M2/artifacts/m2-evaluation/methodology_comparison.csv`
- `M2/artifacts/m2-evaluation/methodology_metric_statistics.csv`
- `M2/artifacts/m2-evaluation/profile_sanity_check.csv`
- `M2/artifacts/m2-evaluation/method_selection_trace.csv`
- `M2/artifacts/m2-evaluation/model_comparison_radar_or_bar.png`
- `M2/artifacts/m2-evaluation/final_method_decision.json`
- `M2/models/final_selected_model/`