# Báo cáo M2 - Nhiệm vụ 9: Đánh giá độ ổn định thời gian (PCA + K-Means)

## 1. Trực quan hóa Xu hướng Ổn định

### Biểu đồ 9.1: Tương đồng cấu trúc và Độ bền luân chuyển
![Temporal Trends](../artifacts/m2-evaluation-pca-kmeans/temporal_trends.png)

### Biểu đồ 9.2: Heatmap Ma trận chuyển đổi cụm
![Transition Heatmap](../artifacts/m2-evaluation-pca-kmeans/transition_heatmap.png)

## 2. Khung kết luận 3 phần bắt buộc (Stability Rubrics)

### Phần A (Phán quyết độ ổn định):
Cấu trúc phân cụm của PCA + K-Means thể hiện mức độ tương đồng cấu trúc cao qua các tháng với **Median ARI = 0.845** và **Median NMI = 0.77**. Mức điểm này vượt xa ngưỡng kỳ vọng > 0.70. Việc sử dụng PCA giảm chiều giúp khử nhiễu đa cộng tuyến, giúp phân hoạch không gian cụm kiên cố và hạn chế tình trạng trôi dạt (drifting) ngẫu nhiên.

### Phần B (Độ bền dòng tiền & Tác động Turnover):
**Quán tính (Persistence)** đạt ngưỡng tuyệt vời ở mức **Median 98.9%**, tương ứng với tỷ lệ luân chuyển cụm **(Migration) chỉ ~1.02%**. Điều này thỏa mãn "Kịch bản Vận hành an toàn" (Migration <= 15%). Sự bám dính siêu hạng này khẳng định rằng các cổ phiếu ngoại lai (Cụm 0) và đại trà (Cụm 1) duy trì rõ bản chất cốt lõi của chúng xuyên suốt toàn chu kỳ thị trường. Tác động Turnover cực kỳ thấp đồng nghĩa với việc tối ưu hóa chi phí giao dịch tối đa ở Milestone M3.

### Phần C (Handoff cho Nhiệm vụ 10):
Với các chỉ số học thuật xuất sắc và tính nhất quán gần như tuyệt đối, phương án PCA + K-Means chứng minh rằng nó không tạo ra cụm "ảo" mà phát hiện cấu trúc thật, bền vững với thời gian. Mô hình này hoàn toàn làm chủ được thử thách Temporal Stability và vô cùng nặng ký để bước vào vòng đối đầu trực diện quyết định (Winner Selection) ở Nhiệm vụ 10 cùng với Ward và K-Means Baseline.
