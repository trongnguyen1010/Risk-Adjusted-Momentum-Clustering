# Phương pháp nghiên cứu 1.1

Các định nghĩa hiện có được giữ cố định: động lượng đơn trên mức giá điều chỉnh ở
21/63/126/252 phiên; độ biến động và Sharpe mẫu được năm hóa trên 63/126 lợi suất;
MDD trên 126 mức giá; beta trên 126 cặp lợi suất đã căn chỉnh; thanh khoản theo giá
trị giao dịch trong 21 phiên. `FEATURE_SPEC.md` trình bày các công thức gốc. Phiên
bản 1.1 bổ sung `downside_vol_63 = sqrt(252 * mean(min(r,0)^2))` so với 0 và
`ram_63 = mom_63/vol_63` (`null` khi độ biến động bằng 0). RAM là động lượng trên
độ biến động năm, không phải Sharpe năm hóa. Cấu hình chọn các đặc trưng bắt buộc và
đặc trưng dùng cho mô hình; thay đổi công thức của một cửa sổ đã đặt tên phải tăng
phiên bản đặc trưng, không được âm thầm định nghĩa lại.

Mỗi ảnh chụp dữ liệu tự khớp ngưỡng cắt winsor và một trong các phương pháp z-score,
robust, xếp hạng hoặc không co giãn. Co giãn robust dùng IQR; biến hằng dùng hệ số 1
sau khi định tâm. Phương pháp xếp hạng dùng trung hạng cho các giá trị đồng hạng rồi
chia cho n. `log1p` tùy chọn chỉ áp dụng cho các đặc trưng không âm được chỉ định rõ.
JSON mô hình được lưu gồm tham số tiền xử lý, tham chiếu xếp hạng, tâm cụm và
`fit_as_of`. Chưa triển khai PCA; các trường PCA trong kết quả gán cụm vẫn là `null`.

KMeans dùng nhiều lần khởi tạo KMeans++, seed và chỉ số lần khởi tạo cố định,
`n_init`/`max_iter` khai báo rõ, xử lý đồng hạng xác định và chọn inertia thấp nhất
trong các lần hội tụ. Kết quả suy biến hoặc không hội tụ được xem là không khả dụng.
Chẩn đoán gồm silhouette (cụm đơn có giá trị 0), Calinski–Harabasz (`null` khi độ phân
tán nội cụm bằng 0), Davies–Bouldin, inertia và kích thước cụm cho k=2..10 theo cấu
hình. Giá trị k đăng ký trước không bao giờ được tự động chọn theo chỉ tiêu hay lợi
nhuận. Cần xem xét ý nghĩa kinh tế, độ cân bằng và ổn định trên tập phát triển trước
khi khóa tập kiểm định độc lập.

Hồ sơ cụm chứa giá trị trung bình của đặc trưng gốc. Nhãn cao/thấp so sánh từng tâm
cụm với trung vị động lượng/rủi ro trong cùng tháng. Nhãn có thể trùng;
`economic_rank` sắp thứ tự theo động lượng, rủi ro rồi ID gốc. Chiến lược chọn nhãn
ngữ nghĩa đã cấu hình, sau đó chọn đặc trưng xếp hạng cao nhất theo cấu hình. Nếu
không có cụm phù hợp thì giữ tiền mặt, không chuyển sang cụm khác.

ARI và NMI chuẩn hóa theo trung bình số học dùng tập ID chung. Phép gán chi phí tối
thiểu chính xác tối đa hóa phần giao của thành viên chung; quy hoạch động xác định
trên tập con giải cùng mục tiêu gán như thuật toán Hungarian với độ phức tạp
O(k²2^k), giới hạn k<=10. Không thể so sánh trực tiếp các tâm cụm được co giãn độc
lập. Độ trôi được báo cáo theo từng đặc trưng bằng đơn vị gốc sau khi ghép. Vòng quay,
mức duy trì/di chuyển, thay đổi tỷ trọng kích thước và số mã vào/ra đều được ghi rõ.
Mẫu số chuyển cụm loại các ID mới vào hoặc đã rời tập. Các tháng bị thiếu không được
xem là hai kỳ liền kề; thay đổi k phải tạo lần chạy riêng.

Chương trình chỉ đánh giá trong khoảng phát triển đã khai báo. Tập kiểm định độc lập
vẫn bị chặn cho đến khi có quy trình riêng được rà soát. Phân tích độ nhạy chi phí giữ
nguyên mục tiêu; các giai đoạn con theo năm chỉ mang tính mô tả. Bootstrap khối trượt
theo cặp lấy mẫu lại đồng thời các phiên của chiến lược và chỉ số tham chiếu, rồi báo
khoảng phân vị 95% cho chênh lệch lợi suất tích lũy. Phép này không bao gồm bất định
do lựa chọn mô hình và không phải tuyên bố về ý nghĩa thống kê.

Mỗi thí nghiệm lưu cấu hình, mã nguồn, dữ liệu, commit, môi trường, seed, dấu thời gian
và mã băm của các tệp kết quả. Quy trình nghiên cứu dùng thư viện chuẩn, kèm biểu đồ
Matplotlib tùy chọn với phiên bản phụ thuộc được khóa.
