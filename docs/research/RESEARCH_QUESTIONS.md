# Research questions

Các câu hỏi dưới đây là working questions, chưa phải final thesis wording:

1. Required market features tạo ra cấu trúc nào trong `market_experiment_eligible(t)` theo từng snapshot?
2. PCA + K-Means và các comparator được M2-PREP phê duyệt khác static K-Means baseline thế nào về cluster quality, balance và robustness?
3. Membership/profile thay đổi qua các snapshot có mức ARI/NMI, persistence, migration và centroid drift ra sao, kể cả khi universe size thay đổi?
4. Kết luận market-structure nhạy thế nào với development window, preprocessing, `k` policy và các giai đoạn readiness gián đoạn?

Bốn câu hỏi trên thuộc M2 market-only development; không dùng return, Sharpe, ROI hoặc portfolio outcome để chọn model. Point-in-time financial features là extension tương lai sau taxonomy/PIT approval. Portfolio comparison với VNINDEX/equal-weight/momentum-only thuộc M3 sau methodology freeze. Dynamic Clustering chưa được phê duyệt và không phải tên gọi cho monthly static fits cộng temporal diagnostics.
