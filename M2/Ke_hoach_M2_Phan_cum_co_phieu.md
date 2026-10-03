Tài liệu trình bày workflow M2 theo đúng cấu trúc nhiệm vụ, làm rõ phần việc chung, quá trình chọn Global K, các phương án phân cụm, đánh giá theo thời gian và final holdout.

# Mục tiêu chung của M2

M2 sử dụng các đặc trưng thị trường đã được chuẩn bị từ M1 để nghiên cứu cấu trúc phân nhóm cổ phiếu tại từng thời điểm cuối tháng.

M2 cần trả lời các câu hỏi chính:

- tại mỗi tháng, các cổ phiếu có thể được chia thành các nhóm có đặc điểm thị trường tương đồng hay không;

- nên sử dụng bao nhiêu cụm để các tháng và các phương án có thể so sánh nhất quán;

- K-Means tạo ra cấu trúc cụm như thế nào;

- Ward có cho cấu trúc tương tự hay khác biệt so với K-Means;

- PCA trước K-Means có làm thay đổi cấu trúc cụm hay không;

- chất lượng cụm tại từng tháng có tốt không;

- các cụm có ổn định qua thời gian không;

- cổ phiếu có thường xuyên chuyển cụm không;

- đặc điểm đại diện của cụm có thay đổi theo thời gian không.

M2 chỉ đánh giá chất lượng cấu trúc cụm, khả năng diễn giải cụm và độ ổn định theo thời gian.

M2 không sử dụng các chỉ số sau để lựa chọn số cụm, thuật toán, PCA hay cách chuẩn hóa:

- lợi nhuận tương lai

- CAGR

- Sharpe

- Sortino

- ROI

- Calmar

- hiệu quả danh mục

- alpha danh mục

Các chỉ số đầu tư thuộc M3.

# Cách M2 xử lý dữ liệu

## Mục đích của phần này

Giúp tất cả thành viên hiểu đúng đơn vị xử lý của M2 trước khi bắt đầu. M2 không ghép toàn bộ dữ liệu nhiều năm thành một bảng rồi phân cụm một lần.

Đơn vị xử lý là một snapshot, tức một ảnh chụp thị trường tại một thời điểm cuối tháng.

30/11/2023  
↓  
các cổ phiếu đủ điều kiện tại 30/11/2023  
↓  
8 đặc trưng của từng cổ phiếu  
↓  
chuẩn hóa riêng snapshot này  
↓  
phân cụm

29/12/2023  
↓  
xác định lại các cổ phiếu đủ điều kiện  
↓  
lấy lại 8 đặc trưng  
↓  
chuẩn hóa lại bằng dữ liệu tháng 12  
↓  
phân cụm riêng

Như vậy, mỗi snapshot được lọc, chuẩn hóa và phân cụm độc lập. Không chuẩn hóa toàn bộ các tháng một lượt rồi mới chia về từng tháng.

# Dữ liệu đầu vào chung của M2

## Mục đích của phần này

Thống nhất dữ liệu đầu vào để các phương án có thể so sánh công bằng. M2 v1 sử dụng đúng 8 đặc trưng:

| **Nhóm**          | **Đặc trưng**                               |
|-------------------|---------------------------------------------|
| Động lượng        | khoảng 1 tháng                              |
| Động lượng        | khoảng 3 tháng                              |
| Động lượng        | khoảng 6 tháng                              |
| Động lượng        | khoảng 12 tháng                             |
| Rủi ro            | biến động khoảng 3 tháng                    |
| Rủi ro            | mức giảm giá cực đại khoảng 6 tháng         |
| Rủi ro thị trường | Beta khoảng 6 tháng                         |
| Thanh khoản       | giá trị giao dịch trung bình khoảng 1 tháng |

Tên trong repo:

mom_21  
mom_63  
mom_126  
mom_252  
vol_63  
mdd_126  
beta_126  
liquidity_21

Ví dụ một snapshot:

| **Mã** | **Động lượng 1T** | **Động lượng 3T** | **Động lượng 6T** | **Động lượng 12T** | **Biến động** | **MDD** | **Beta** | **Thanh khoản** |
|--------|-------------------|-------------------|-------------------|--------------------|---------------|---------|----------|-----------------|
| AAA    | ...               | ...               | ...               | ...                | ...           | ...     | ...      | ...             |
| BBB    | ...               | ...               | ...               | ...                | ...           | ...     | ...      | ...             |
| CCC    | ...               | ...               | ...               | ...                | ...           | ...     | ...      | ...             |

Số lượng mã có thể khác nhau giữa các tháng.

11/2023 → 240 mã  
12/2023 → 265 mã  
01/2024 → 310 mã

Không lấy cố định 905 mã của snapshot 08/2026 áp ngược toàn bộ lịch sử.

# QUY ƯỚC ĐƯỜNG DẪN OUTPUT VÀ CẤU TRÚC THƯ MỤC M2

Để quản lý thống nhất giữa các thành viên, toàn bộ mã nguồn mô hình, mô hình đã huấn luyện, tài liệu báo cáo và kết quả thực nghiệm của M2 được phân bổ theo quy ước chuẩn:

- **Code model / Thực thi (Lưu trữ thống nhất trong `M2/notebooks/`)**:
  - Toàn bộ file mã nguồn thực thi mô hình, đánh giá chất lượng, so sánh phương án, kiểm định holdout, kiểm toán hệ thống và tổng kết bàn giao M2 đều được lưu trữ thống nhất dưới dạng Jupyter Notebooks (`.ipynb`) từ Nhiệm vụ 4 đến Nhiệm vụ 13.
  - Mỗi notebook bắt buộc phải có đầy đủ các ô code thực thi, bảng số liệu thống kê xuất xưởng và ô Markdown biện luận học thuật (diagnostic rubrics) đối chiếu 100% với dữ liệu thực chứng trước khi xuất artifacts.
- **Mô hình / Trọng số (Fitted models & objects)**: Lưu trữ trong thư mục `M2/models/` (các file đối tượng mô hình đã fit, scalers, weights, centroids, linkages, PCA transformers được lưu trữ tuần tự theo nhiệm vụ và thuật toán, bao gồm thư mục `M2/models/final_selected_model/` cho 1 mô hình tốt nhất được chọn sau Nhiệm vụ 10).
- **Báo cáo (Reports & Documents)**: Lưu trữ trong thư mục `M2/reports/` (các báo cáo chuyên đề Markdown `.md` và tài liệu nghiệm thu kỹ thuật của từng nhiệm vụ và toàn bộ M2).
- **Artifacts thực nghiệm chuẩn hóa (System & Pipeline Artifacts)**: Lưu trữ trong thư mục `M2/artifacts/` (các artifact bất biến do hệ thống runner ghi nhận: `assignments.jsonl`, `diagnostics.jsonl`, `profiles.jsonl`, `manifest.json`, `metric_matrix.csv` theo protocol đã freeze; lưu tại `M2/artifacts/` để không bị `.gitignore` chặn và có thể push lên GitHub phục vụ phối hợp giữa các thành viên).

# HƯỚNG DẪN NHỜ AI GIẢI NÉN VÀ THIẾT LẬP DỮ LIỆU NỀN TẢNG (DELTA_01_ACTIVE_M2_M3.zip)

Giai đoạn M2 và M3 kế thừa toàn bộ dữ liệu nền tảng thị trường chuẩn hóa từ M1 (C8 complete-only canonical market dataset, feature snapshots, và M2-PREP baseline configurations). File nén lưu trữ dữ liệu này là `DELTA_01_ACTIVE_M2_M3.zip`.

Để đơn giản hóa và giúp bất kỳ thành viên nào trong nhóm (trên Windows, macOS hoặc Linux) đều có thể thiết lập nhanh mà không cần gõ lệnh thủ công hay phụ thuộc vào đường dẫn máy cá nhân, bạn chỉ cần nhờ **Trợ lý AI (AI Coding Assistant)** tự động định vị, giải nén và đưa vào đúng thư mục repository.

### 1. Vị trí file nén trên máy tính
- File zip thường được tải về từ kênh chia sẻ của nhóm và nằm trong thư mục tải về của máy (ví dụ: trong thư mục `Downloads`, hoặc thư mục `Team DELTA/data/DELTA_01_ACTIVE_M2_M3.zip`).

### 2. Cấu trúc dữ liệu bên trong file zip
File zip chứa sẵn cấu trúc chuẩn:
```text
DELTA_01_ACTIVE_M2_M3.zip
├── artifacts/
│   ├── cafef_primary/       # Dữ liệu thị trường C8 canonical (prices_daily, feature_snapshots, securities...)
│   ├── experiments/        # Baseline configs và artifacts của M2-PREP
│   └── reports/            # M1 market foundation report và plots
└── configs/
    └── data/               # Cấu hình dữ liệu C8 complete-only và identity review
```
Khi được giải nén trực tiếp vào **thư mục gốc của repository**, các file sẽ tự động khớp chính xác vào các thư mục `artifacts/` và `configs/` hiện tại mà không làm sai lệch cấu trúc dự án.

### 3. Câu lệnh mẫu (Prompt) nhờ AI thực hiện tự động
Bạn chỉ cần gửi một trong các câu lệnh sau vào khung chat của Trợ lý AI (AI sẽ tự động nhận diện hệ điều hành và đường dẫn repository tương ứng trên máy của bạn):

#### Prompt mẫu 1 (Ngắn gọn, tự động tìm kiếm):
> *"Hãy tìm file `DELTA_01_ACTIVE_M2_M3.zip` trên máy của tôi (trong thư mục Downloads hoặc thư mục dữ liệu nhóm), sau đó giải nén trực tiếp vào thư mục gốc của repository này và kiểm tra dữ liệu trong `artifacts/` và `configs/` giúp tôi."*

#### Prompt mẫu 2 (Nếu bạn đã tải file zip về một vị trí cụ thể):
> *"Tôi đã tải file `DELTA_01_ACTIVE_M2_M3.zip` về máy. Hãy giải nén file này vào đúng thư mục gốc của repository để cập nhật các tệp dữ liệu vào `artifacts/` và `configs/`, sau đó xác nhận file `artifacts/cafef_primary/cafef-c8-complete-only-v1/canonical/feature_snapshots.jsonl` đã sẵn sàng."*

### 4. Quy trình AI sẽ tự động xử lý ngầm
Khi nhận được yêu cầu trên, Trợ lý AI sẽ:
1. Tự động dò tìm vị trí file `DELTA_01_ACTIVE_M2_M3.zip` tương thích với hệ điều hành và tài khoản người dùng hiện hành.
2. Tự động giải nén nội dung trực tiếp vào thư mục gốc repo (giữ nguyên cấu trúc `artifacts/` và `configs/`).
3. Tự động kiểm tra tính toàn vẹn của các file dữ liệu then chốt (`feature_snapshots.jsonl`, `manifest.json`, `cafef_c8_complete_only_v1.json`).
4. Báo cáo hoàn tất để thành viên có thể bắt đầu nghiên cứu ngay mà không phải cấu hình thủ công.


# NHIỆM VỤ 1 — KHÓA TOÀN BỘ QUY TẮC THỰC NGHIỆM

## Mục đích của Nhiệm vụ 1

Thống nhất cách toàn bộ M2 sẽ được thực hiện trước khi nhìn kết quả phân cụm thật. Điều này nhằm tránh chạy mô hình trước rồi thay đổi preprocessing, K hoặc PCA chỉ vì kết quả chưa đẹp. Sau Nhiệm vụ 1, các thành viên không được tự ý thay đổi quy tắc của riêng mình.

## Đầu vào của Nhiệm vụ 1

- kết quả M2-PREP;

- DELTA_UNIFIED_PROJECT_PLAN.md;

- các quyết định methodology còn mở;

- tài liệu phương pháp trong repo.

## Phần 1.1 — Khóa giai đoạn development

### Mục đích

Xác định giai đoạn được phép dùng để thử K, chọn Global K, chạy các phương án, xem chất lượng cụm và hoàn thiện methodology.

30/11/2023 → 24/01/2025  
15 snapshot liên tục

## Phần 1.2 — Khóa final holdout

### Mục đích

Giữ lại một giai đoạn chưa dùng trong quá trình lựa chọn methodology.

27/02/2026 → 28/08/2026  
7 snapshot

- Không dùng holdout để chọn K;

- Không dùng holdout để đổi scaler;

- Không dùng holdout để đổi PCA;

- Không dùng holdout để đổi thuật toán.

## Phần 1.3 — Khóa số lượng mã tối thiểu

### Mục đích

Tránh chạy phân cụm khi một snapshot có quá ít cổ phiếu.

n_eligible \>= 120  
142 mã → chạy  
119 mã → bỏ qua

## Phần 1.4 — Khóa tập đặc trưng

### Mục đích

Đảm bảo các phương án sử dụng cùng dữ liệu đầu vào. Không được để K-Means, Ward và PCA + K-Means sử dụng các tập feature khác nhau.

## Phần 1.5 — Khóa xử lý dữ liệu thiếu

### Mục đích

Không tạo dữ liệu giả. Không điền trung bình, median, forward-fill, backward-fill, interpolation hoặc đổi missing thành 0. Mã không đủ điều kiện tại snapshot nào thì không đưa vào snapshot đó.

## Phần 1.6 — Khóa xử lý outlier

### Mục đích

Thống nhất cách xử lý giá trị cực đoan. Baseline v1 không winsorize và không clipping.

## Phần 1.7 — Khóa chuẩn hóa

### Mục đích

Đưa các đặc trưng về thang đo phù hợp trước khi chạy các thuật toán dựa trên khoảng cách.

Mặc định: Robust Scaling theo từng snapshot.

**x_scaled = (x − Median) / IQR**

Trong đó, Median là trung vị và IQR là khoảng tứ phân vị của chính feature đó trong snapshot đang xử lý.

11/2023  
→ tính Median/IQR tháng 11  
→ scale tháng 11  
  
12/2023  
→ tính Median/IQR mới  
→ scale tháng 12

Không fit một scaler chung cho toàn development.

## Phần 1.8 — Khóa khoảng K cần thử

### Mục đích

Xác định phạm vi số cụm cần kiểm tra.

K = 2, 3, 4, 5, 6, 7, 8

## Phần 1.9 — Khóa nguyên tắc chọn Global K

### Mục đích

Chọn một số cụm chung để các tháng có thể so sánh và K-Means, Ward, PCA + K-Means có thể so sánh công bằng.

1.  ưu tiên Median Silhouette cao nhất;

2.  nếu gần nhau, xem Median Davies–Bouldin thấp hơn;

3.  Calinski–Harabasz và cluster balance dùng kiểm tra bổ sung;

4.  không dùng return hay Sharpe.

## Phần 1.10 — Khóa vai trò PCA

### Mục đích

Làm rõ PCA không phải bước chung cho toàn bộ M2. PCA chỉ thuộc phương án PCA + K-Means.

Robust Scaling  
↓  
PCA  
↓  
K-Means

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file \`.py\` riêng lẻ; thông thường \`runner.py\` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**\`src/delta_t1/experiments/m2_prep.py\`** — file đã có; dùng làm nguồn kiểm tra trước M2.

> Mục đích: Audit trạng thái sẵn sàng của M2: eligibility theo snapshot, feature set, preprocessing, thuật toán, metric, gap dữ liệu và các điểm runner còn thiếu.
>
> Cách dùng trong nhiệm vụ này: Không chạy file này để tạo cluster. Đọc kết quả/audit của nó để biết những quyết định nào cần được khóa trong Protocol v1.

**\`src/delta_t1/experiments/protocol.py\`** — file đã có; dùng để kiểm tra config.

> Mục đích: Xác nhận file cấu hình experiment có đủ trường bắt buộc và không vi phạm contract nghiên cứu.
>
> Cách dùng trong nhiệm vụ này: Sau khi tạo config M2 v1, dùng validator trong file này để kiểm tra development window, clustering config, preprocessing/PCA và các rule liên quan. Nếu config M2 có field mới chưa được validator hỗ trợ thì bổ sung validation tại đây.

**\`configs/experiments/m2_market_only_v1.json\`** — file cần tạo mới ở Nhiệm vụ 1.

> Mục đích: Biến toàn bộ quyết định methodology thành một cấu hình có phiên bản để các nhiệm vụ sau đọc lại.
>
> Cách dùng trong nhiệm vụ này: Ghi vào file các rule đã khóa: development/holdout, eligibility field, minimum eligible, 8 feature, scaling, K range, PCA policy, thuật toán và \`portfolio_evaluation=false\`.
>
> Kết quả liên quan: Đây là đầu vào cấu hình chung cho Nhiệm vụ 2 trở đi.

### Cách các file phối hợp

> m2_prep.py + tài liệu phương pháp → chốt rule → tạo m2_market_only_v1.json → protocol.py kiểm tra → bàn giao config cho Nhiệm vụ 2.

## Kết quả cần đạt của Nhiệm vụ 1

- config M2;

- development window;

- final holdout;

- feature set;

- missing policy;

- outlier policy;

- scaling policy;

- K range;

- K selection rule;

- PCA policy.

## Vị trí trong repo

- DELTA_UNIFIED_PROJECT_PLAN.md §6

- METHODOLOGY.md

- EXPERIMENT_PROTOCOL.md

- m2-prep-v1/unresolved_decisions.csv

- m2-prep-v1/preprocessing_matrix.csv

# NHIỆM VỤ 2 — CHUẨN BỊ VÀ KIỂM THỬ RUNNER M2

## Mục đích của Nhiệm vụ 2

Xây và kiểm tra công cụ đưa dữ liệu từng snapshot vào pipeline M2 đúng cách. Nhiệm vụ này chưa chạy toàn bộ experiment thật.

Nhiệm vụ 1 = quy định cách làm  
Nhiệm vụ 2 = xây công cụ thực hiện  
Nhiệm vụ 3 trở đi = chạy dữ liệu thật

## Đầu vào của Nhiệm vụ 2

- config từ Nhiệm vụ 1;

- dữ liệu M1;

- logic market readiness;

- 8 feature.

## Phần 2.1 — Nhận snapshot

### Mục đích

Runner phải biết snapshot nào cần xử lý.

Ví dụ: snapshot_date = 30/11/2023.

## Phần 2.2 — Lọc universe theo snapshot

### Mục đích

Đảm bảo mỗi tháng chỉ sử dụng các mã đủ điều kiện của chính tháng đó.

Ví dụ:

30/11/2023 có 240 mã

29/12/2023 có 265 mã

28/08/2026 có 905 mã

Không được dùng 905 mã cho các tháng trước.

## Phần 2.3 — Kiểm tra 8 feature

### Mục đích

Đảm bảo dữ liệu đưa vào mô hình đúng schema.

Kiểm tra đủ 8 feature, giá trị hữu hạn và không có dữ liệu không hợp lệ.

## Phần 2.4 — Kiểm thử terminal universe

### Mục đích

Ngăn lỗi nhìn trước tương lai.

Phải chứng minh 905 mã ở 08/2026 không được áp ngược lịch sử.

## Phần 2.5 — Kiểm thử tích hợp

### Mục đích

Đảm bảo output runner có thể truyền trực tiếp vào clustering pipeline.

Output gồm snapshot_date + danh sách mã hợp lệ + 8 feature.

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file \`.py\` riêng lẻ; thông thường \`runner.py\` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**\`src/delta_t1/experiments/runner.py\`** — file đã có; cần chỉnh cho M2 market-only.

> Mục đích: Là bộ điều phối chính của một experiment: đọc config, đọc \`features/monthly.jsonl\`, chia dữ liệu theo snapshot, gọi thuật toán, theo dõi temporal và lưu artifact.
>
> Cách dùng trong nhiệm vụ này: Sửa chỗ đang phụ thuộc \`row\["eligibility"\]\` để runner lấy eligibility field và minimum eligible từ config M2. Runner phải skip snapshot theo đúng rule và không tự fallback về legacy eligibility.

**\`src/delta_t1/clustering/base.py\`** — file đã có; cần đồng bộ với runner.

> Mục đích: Chứa logic chung khi xử lý một snapshot clustering: lọc row, chuẩn bị feature/preprocessing, tạo diagnostics/profile và model result.
>
> Cách dùng trong nhiệm vụ này: Đổi phần lọc legacy eligibility sang field được truyền từ config. Mục tiêu là runner và base luôn lọc cùng một universe.

**\`src/delta_t1/experiments/protocol.py\`** — file đã có; có thể cần bổ sung validation.

> Mục đích: Chặn config sai trước khi chạy experiment.
>
> Cách dùng trong nhiệm vụ này: Bổ sung kiểm tra cho market-only mode, eligibility field, minimum eligible và các field M2 v1 nếu các rule này chưa được validator hiện tại hỗ trợ.

**\`src/delta_t1/experiments/m2_prep.py\`** — file đã có; chỉ dùng để đối chiếu.

> Mục đích: Cung cấp evidence về market-readiness và các gap mà M2-R2 phải tôn trọng.
>
> Cách dùng trong nhiệm vụ này: Không dùng làm runner. Chỉ đối chiếu rule/đếm readiness khi viết test cho runner.

### Cách các file phối hợp

> m2_market_only_v1.json → protocol.py → runner.py → base.py → lọc market_feature_ready_v2 + kiểm tra min_eligible + 8 feature → test → dữ liệu sẵn sàng cho Nhiệm vụ 3.

## Kết quả cần đạt của Nhiệm vụ 2

- runner market-only;

- lọc đúng universe;

- không fallback sang eligibility cũ;

- test pass;

- dữ liệu sẵn sàng cho Nhiệm vụ 3.

## Vị trí trong repo

- DELTA_UNIFIED_PROJECT_PLAN.md → M2-R2

- CURRENT_STATUS.md

- src/delta_t1/experiments/

- src/delta_t1/features/

# NHIỆM VỤ 3 — CHỌN GLOBAL K

## Mục đích của Nhiệm vụ 3

Dùng K-Means trên development với K=2..8 để chọn ra một Global K duy nhất cho toàn bộ M2. K-Means ở Nhiệm vụ 3 dùng để chọn số cụm, chưa phải mục đích hoàn thiện baseline chính thức. Sau khi Global K được chọn, K-Means, Ward và PCA + K-Means đều dùng cùng K.

## Đầu vào của Nhiệm vụ 3

- 15 development snapshots;

- runner;

- 8 feature;

- Robust Scaling;

- K=2…8;

- K-selection rule.

## Phần 3.1 — Lấy snapshot đầu tiên

### Mục đích

Tạo dữ liệu thật cho một tháng.

Ví dụ 30/11/2023 → lọc universe → lấy 8 feature. Giả sử còn 240 mã.

## Phần 3.2 — Chuẩn hóa snapshot

### Mục đích

Đưa dữ liệu về thang đo phù hợp.

240 × 8 → Median/IQR → Robust Scaling → 240 × 8 đã chuẩn hóa.

## Phần 3.3 — Chạy K=2

### Mục đích

Đánh giá nếu thị trường được chia thành 2 cụm.

Lưu Silhouette, Davies–Bouldin, Calinski–Harabasz, inertia và cluster balance.

## Phần 3.4 — Chạy K=3 đến K=8

### Mục đích

So sánh các số cụm trên cùng snapshot.

Chạy K=3,4,5,6,7,8 trên cùng dữ liệu đã chuẩn hóa.

## Phần 3.5 — Sang snapshot tiếp theo

### Mục đích

Đánh giá mỗi K trên nhiều trạng thái thị trường.

Ví dụ 29/12/2023 → lọc universe mới → scale lại → K=2..8.

## Phần 3.6 — Lặp toàn development

### Mục đích

Tạo evidence đủ rộng để chọn K ổn định.

15 snapshot × 7 K = 105 lần chạy K-Means.

## Phần 3.7 — Tạo bảng chi tiết

### Mục đích

Lưu toàn bộ kết quả để audit quyết định chọn K.

Bảng có các cột Snapshot, K, Silhouette, DB, CH, Inertia, Balance.

## Phần 3.8 — Tổng hợp theo K

### Mục đích

Không chọn K theo một tháng riêng lẻ.

Với mỗi K, tính median các metric trên toàn development.

<img src="/mnt/data/m2_code_md/media/image1.png" style="width:6.9in;height:1.71736in" />

## Phần 3.9 — Chọn Global K

### Mục đích

Chọn một số cụm dùng thống nhất cho toàn M2.

Ưu tiên Median Silhouette cao nhất; nếu gần nhau thì xem Median DB thấp hơn.

## Phần 3.10 — Khóa Global K

### Mục đích

Ngăn mỗi phương án chọn K riêng.

Ví dụ Global K=4 thì K-Means=4, Ward=4, PCA+K-Means=4.

## Phần 3.11 — Giữ artifact K-Means của Global K

### Mục đích

Tránh chạy lại cùng kết quả.

Nếu Nhiệm vụ 3 đã lưu đầy đủ output của Global K thì có thể tái sử dụng làm development result của K-Means baseline.

| **Snapshot** | **K** | **Silhouette** | **DB** | **CH** | **Inertia** | **Balance** |
|--------------|-------|----------------|--------|--------|-------------|-------------|
| 11/2023      | 2     | ...            | ...    | ...    | ...         | ...         |
| 11/2023      | 3     | ...            | ...    | ...    | ...         | ...         |
| ...          | ...   | ...            | ...    | ...    | ...         | ...         |

| **K** | **Median Silhouette** | **Median DB** | **Median CH** | **Balance** |
|-------|-----------------------|---------------|---------------|-------------|
| 2     | ...                   | ...           | ...           | ...         |
| 3     | ...                   | ...           | ...           | ...         |
| 4     | ...                   | ...           | ...           | ...         |

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file \`.py\` riêng lẻ; thông thường \`runner.py\` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**\`src/delta_t1/experiments/runner.py\`** — file đã có; dùng làm điều phối.

> Mục đích: Lặp qua 15 development snapshots và gọi thuật toán trên từng snapshot.
>
> Cách dùng trong nhiệm vụ này: Chạy experiment bằng config phát triển; mỗi snapshot được runner chuyển vào pipeline rồi diagnostics được lưu lại.

**\`src/delta_t1/clustering/base.py\`** — file đã có; dùng làm logic chung cho một snapshot.

> Mục đích: Chuẩn bị dữ liệu snapshot và gọi preprocessing/algorithm theo cấu hình.
>
> Cách dùng trong nhiệm vụ này: Đảm bảo mỗi K được đánh giá trên cùng rows eligible và cùng feature set.

**\`src/delta_t1/features/preprocessing.py\`** — file đã có; dùng Robust Scaling.

> Mục đích: Chuẩn hóa các feature theo từng snapshot trước K-Means.
>
> Cách dùng trong nhiệm vụ này: Dùng chế độ robust để tính median/IQR của chính snapshot; không dùng PCA trong Nhiệm vụ 3.

**\`src/delta_t1/clustering/kmeans.py\`** — file đã có; dùng để chạy K-Means.

> Mục đích: Thực hiện K-Means deterministic cho một snapshot.
>
> Cách dùng trong nhiệm vụ này: Runner/base gọi implementation này lần lượt với K=2..8. Không cần tự chạy file này bằng tay.

**\`src/delta_t1/evaluation/cluster_metrics.py\`** — file đã có; dùng để tính metric.

> Mục đích: Tính Silhouette, Davies–Bouldin, Calinski–Harabasz, inertia và cluster balance.
>
> Cách dùng trong nhiệm vụ này: Lấy metric cho từng tổ hợp snapshot × K, sau đó tổng hợp median theo K để chọn Global K.

### Cách các file phối hợp

> runner.py → base.py → preprocessing.py (Robust Scaling) → kmeans.py (K=2..8) → cluster_metrics.py → diagnostics từng snapshot × K → aggregate → Global K.

## Kết quả cần đạt của Nhiệm vụ 3

- metric theo snapshot × K;

- aggregate theo K;

- Global K;

- decision artifact;

- K-Means artifact của Global K nếu đầy đủ.

## Vị trí trong repo

- DELTA_UNIFIED_PROJECT_PLAN.md §6.7

- DELTA_UNIFIED_PROJECT_PLAN.md → M2-EXEC-A

- metric_matrix.csv

- METHODOLOGY.md

# NHIỆM VỤ 4 — CHẠY PHƯƠNG ÁN A: K-MEANS BASELINE

## Mục đích của Nhiệm vụ 4

Mục đích là tạo kết quả phân cụm K-Means chính thức trên toàn bộ giai đoạn development sau khi Global K đã được chọn và khóa ở Nhiệm vụ 3.

Khác với Nhiệm vụ 3:
- **Nhiệm vụ 3:** K-Means K=2..8 → dùng để chọn Global K.
- **Nhiệm vụ 4:** chỉ dùng Global K đã khóa → tạo kết quả baseline K-Means chính thức.

Kết quả của Nhiệm vụ 4 phải đủ để sử dụng tiếp cho:
- Nhiệm vụ 7 → đánh giá chất lượng
- Nhiệm vụ 8 → phân tích hồ sơ cụm
- Nhiệm vụ 9 → temporal stability
- Nhiệm vụ 10 → so sánh phương án

## Đầu vào của Nhiệm vụ 4

- Global K từ Nhiệm vụ 3 (Global K = 2);
- toàn bộ development snapshots;
- runner market-only từ Nhiệm vụ 2;
- cùng universe rule đã khóa (`market_feature_ready_v2 = true`);
- đúng 8 feature;
- Robust Scaling theo từng snapshot;
- missing/outlier policy đã khóa;
- artifact K-Means Global K từ Nhiệm vụ 3 nếu có thể tái sử dụng.

Ví dụ:
Global K = 2 (đã khóa từ Nhiệm vụ 3)

Snapshot:
30/11/2023

Universe:
240 mã đủ điều kiện

Input:
240 × 8 feature

## Phần 4.1 — Lấy dữ liệu của từng snapshot

### Mục đích

Tạo đúng tập dữ liệu đầu vào của K-Means tại từng tháng.

Ví dụ:
30/11/2023  
↓  
runner xác định các mã đủ điều kiện  
↓  
lọc đúng market-only universe  
↓  
lấy 8 feature

Giả sử còn: 240 mã  
thì dữ liệu đầu vào là: 240 × 8

Không được lấy cố định universe của snapshot cuối rồi áp ngược cho các tháng trước.

## Phần 4.2 — Kiểm tra dữ liệu trước khi phân cụm

### Mục đích

Đảm bảo snapshot đủ điều kiện để chạy mô hình.

Cần kiểm tra:
- số mã >= minimum eligible (n_eligible >= 120)
- đủ đúng 8 feature
- không có NaN
- không có Inf
- không có feature ngoài protocol

Ví dụ:
- 240 mã >= 120 → được chạy
- Nếu 110 mã < 120 → skip snapshot và phải ghi lại lý do skip.

## Phần 4.3 — Robust Scaling theo snapshot

### Mục đích

Đưa 8 feature về cùng thang đo trước khi K-Means tính khoảng cách.

Với snapshot 30/11/2023:
240 × 8  
↓  
tính Median của từng feature  
↓  
tính IQR của từng feature  
↓  
Robust Scaling  
↓  
240 × 8 đã chuẩn hóa

Công thức:
`x_scaled = (x - Median) / IQR`

Scaler chỉ thuộc snapshot này. Sang tháng tiếp theo phải tính scaler mới.  
Không: tính scaler tháng 11 rồi dùng lại cho tháng 12.

## Phần 4.4 — Chạy K-Means với Global K

### Mục đích

Tạo kết quả phân cụm chính thức cho snapshot.

Ví dụ:
Global K = 2 (đã khóa từ Nhiệm vụ 3)

thì:
240 × 8 đã scale  
↓  
K-Means  
↓  
Global K  
↓  
K cluster

Không chạy lại: K=2..8 vì việc lựa chọn K đã hoàn tất ở Nhiệm vụ 3.

## Phần 4.5 — Lưu cluster assignment

### Mục đích

Biết mỗi mã cổ phiếu được K-Means gán vào cụm nào.

Ví dụ:

| Snapshot | Mã | Cụm |
| :--- | :--- | :--- |
| 30/11/2023 | AAA | 0 |
| 30/11/2023 | BBB | 2 |
| 30/11/2023 | CCC | 1 |

Đây là dữ liệu quan trọng cho temporal analysis ở Nhiệm vụ 9.

## Phần 4.6 — Lưu tâm cụm

### Mục đích

Có đại diện số học của từng cụm K-Means.

Ví dụ:
- Cluster 0 centroid
- Cluster 1 centroid
- Cluster 2 centroid
- Cluster 3 centroid

Centroid được sử dụng để:
- mô tả cụm
- so sánh cụm
- theo dõi centroid drift
- hỗ trợ temporal analysis

## Phần 4.7 — Xây cluster profile

### Mục đích

Chuyển kết quả số học thành mô tả dễ hiểu.

Ví dụ Cluster 0:
- Momentum 1M cao
- Momentum 3M cao
- Volatility thấp
- MDD thấp
- Liquidity cao

Có thể tổng hợp: median, mean hoặc statistic mà pipeline đã quy định cho từng feature trong từng cluster.

Không diễn giải: "Cluster 0 là cụm tốt nhất để mua" vì hiệu quả đầu tư thuộc M3.

## Phần 4.8 — Tính quality metrics

### Mục đích

Đánh giá chất lượng K-Means tại từng snapshot.

Lưu:
- Silhouette
- Davies–Bouldin
- Calinski–Harabasz
- Inertia
- Cluster balance

Ví dụ:

| Snapshot | Silhouette | DB | CH | Inertia | Balance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 11/2023 | ... | ... | ... | ... | ... |

## Phần 4.9 — Lặp lại cho toàn bộ development

### Mục đích

Tạo baseline K-Means đầy đủ cho tất cả snapshot development.

11/2023 → K-Means  
12/2023 → K-Means  
...  
01/2025 → K-Means

Mỗi snapshot đều làm lại:
lọc universe  
↓  
kiểm tra input  
↓  
Robust Scaling mới  
↓  
K-Means Global K  
↓  
assignment  
↓  
centroid  
↓  
profile  
↓  
metrics

## Phần 4.10 — Lưu artifact K-Means

### Mục đích

Đảm bảo kết quả có thể kiểm tra và tái lập.

Cần lưu tối thiểu:
- snapshot_date
- eligible universe
- feature set
- scaler parameters
- Global K
- cluster assignments
- centroids
- cluster sizes
- cluster profiles
- quality metrics
- config
- model/run metadata

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file `.py` riêng lẻ; thông thường `runner.py` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**`src/delta_t1/experiments/runner.py`** — file đã có; file điều phối.
> Mục đích: Chạy baseline qua toàn bộ development window và ghi artifact.  
> Cách dùng trong nhiệm vụ này: Đọc config K-Means đã khóa, duyệt từng snapshot và gọi thuật toán qua registry/base.

**`src/delta_t1/clustering/registry.py`** — file đã có; bộ chọn thuật toán.
> Mục đích: Ánh xạ tên thuật toán trong config sang implementation tương ứng.  
> Cách dùng trong nhiệm vụ này: Khi config khai báo K-Means, runner gọi registry để lấy K-Means thay vì import/chạy thủ công từng file.

**`src/delta_t1/clustering/kmeans.py`** — file đã có; thuật toán chính của Nhiệm vụ 4.
> Mục đích: Phân cụm snapshot bằng Global K đã khóa.  
> Cách dùng trong nhiệm vụ này: Chỉ chạy Global K, không thử lại K=2..8.

**`src/delta_t1/features/preprocessing.py`** — file đã có; chuẩn hóa dữ liệu.
> Mục đích: Áp dụng Robust Scaling theo từng snapshot.  
> Cách dùng trong nhiệm vụ này: Tạo dữ liệu đã scale rồi chuyển sang K-Means.

**`src/delta_t1/clustering/base.py`** — file đã có; tạo snapshot result.
> Mục đích: Gom logic chung về rows, diagnostics, profile/centroid và model output.  
> Cách dùng trong nhiệm vụ này: Dùng để đảm bảo artifact K-Means có cấu trúc chuẩn cho các nhiệm vụ sau.

**`src/delta_t1/evaluation/cluster_metrics.py`** — file đã có; đánh giá chất lượng.
> Mục đích: Tính các quality metrics của K-Means tại từng snapshot.  
> Cách dùng trong nhiệm vụ này: Metric được lưu cùng artifact để Nhiệm vụ 7 và 10 sử dụng.

### Cách các file phối hợp

> runner.py → registry.py → base.py → preprocessing.py → kmeans.py (Global K) → cluster_metrics.py → assignments/profiles/diagnostics.

## Kết quả cần đạt của Nhiệm vụ 4

- K-Means assignments cho toàn bộ development;
- centroids;
- cluster sizes;
- cluster profiles;
- scaler parameters theo snapshot;
- quality metrics;
- artifact theo từng snapshot;
- dữ liệu sẵn sàng cho Nhiệm vụ 7, 8, 9 và 10.

## Vị trí trong repo & Đường dẫn output

- **Code model / Thực thi**: `M2/notebooks/04_kmeans_baseline.ipynb` (phối hợp `src/delta_t1/clustering/kmeans.py` và `src/delta_t1/experiments/runner.py`)
- **Mô hình / Trọng số (Models & Centroids)**: `M2/models/kmeans/` (lưu trữ model K-Means fitted, centroids và snapshot scaler parameters)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_4_KMeans_Baseline.md`
- **Artifacts thực nghiệm chuẩn hóa**: `M2/artifacts/m2-task4-kmeans-baseline-v1/` (chứa `assignments.jsonl`, `profiles.jsonl`, `diagnostics.jsonl`, `manifest.json`; lưu trong M2 để push lên GitHub)

# NHIỆM VỤ 5 — CHẠY PHƯƠNG ÁN B: WARD

## Mục đích của Nhiệm vụ 5

Mục đích là tạo kết quả phân cụm Ward chính thức trên toàn bộ development để so sánh với K-Means.

Ward phải sử dụng:
- cùng snapshot
- cùng universe
- cùng 8 feature
- cùng Robust Scaling
- cùng Global K

Điều duy nhất thay đổi chính là:
K-Means  
↓ thay bằng  
Ward hierarchical clustering

Như vậy mới có thể đánh giá sự khác biệt do thuật toán.

## Đầu vào của Nhiệm vụ 5

- Global K từ Nhiệm vụ 3 (Global K = 2);
- toàn bộ development snapshots;
- runner market-only;
- cùng universe rule;
- đúng 8 feature;
- Robust Scaling;
- missing/outlier policy;
- protocol đã freeze.

Ví dụ:
Global K = 2 (đã khóa từ Nhiệm vụ 3)

Snapshot:
30/11/2023

Universe:
240 mã

Input:
240 × 8

## Phần 5.1 — Lấy dữ liệu của từng snapshot

### Mục đích

Tạo đúng tập dữ liệu đầu vào Ward tại từng tháng.

30/11/2023  
↓  
lọc universe  
↓  
lấy 8 feature

Ví dụ: 240 mã × 8 feature.

Universe phải giống phương án K-Means tại cùng snapshot.

## Phần 5.2 — Kiểm tra dữ liệu trước khi phân cụm

### Mục đích

Đảm bảo Ward chỉ chạy trên snapshot hợp lệ.

Kiểm tra:
- n_eligible >= minimum (n_eligible >= 120)
- đủ 8 feature
- không NaN
- không Inf
- đúng schema

Ví dụ: 240 >= 120 → chạy  
Nếu không đủ điều kiện: skip + ghi rõ lý do.

## Phần 5.3 — Robust Scaling theo snapshot

### Mục đích

Đảm bảo Ward sử dụng cùng không gian đầu vào với K-Means.

240 × 8  
↓  
Median/IQR từng feature  
↓  
Robust Scaling  
↓  
240 × 8 đã chuẩn hóa

Không được dùng:
Ward → Z-score trong khi K-Means → Robust Scaling nếu protocol chung đang khóa Robust Scaling.

## Phần 5.4 — Chạy Ward với Global K

### Mục đích

Tạo kết quả phân cụm Ward.

Ví dụ:
Global K = 2 (đã khóa từ Nhiệm vụ 3)

Pipeline:
dữ liệu đã scale  
↓  
Ward hierarchical clustering  
↓  
cắt cây thành K cluster  
↓  
assignment

Không chọn lại K riêng cho Ward.  
Nếu Global K = 2 thì: K-Means = 2, Ward = 2, PCA + K-Means = 2.

## Phần 5.5 — Lưu cluster assignment

### Mục đích

Biết mỗi mã được Ward gán vào cụm nào.

Ví dụ:

| Snapshot | Mã | Cụm Ward |
| :--- | :--- | :--- |
| 30/11/2023 | AAA | 1 |
| 30/11/2023 | BBB | 3 |
| 30/11/2023 | CCC | 0 |

Assignment này được dùng tiếp ở:
- Nhiệm vụ 7
- Nhiệm vụ 8
- Nhiệm vụ 9
- Nhiệm vụ 10

## Phần 5.6 — Xây đại diện cụm và cluster profile

### Mục đích

Có mô tả thống nhất để Ward cũng có thể được phân tích như K-Means.

Ward không có centroid theo cơ chế tối ưu giống K-Means.
Tuy nhiên sau khi đã có assignment, pipeline có thể tổng hợp đặc trưng của các thành viên trong từng cụm để tạo:
- cluster representative
- cluster profile

Ví dụ Ward Cluster 0:
- Momentum cao
- Volatility thấp
- MDD thấp
- Liquidity cao

Phần này phải sử dụng cùng quy tắc tổng hợp profile như K-Means.  
Không tự thiết kế một kiểu profile riêng cho Ward.

## Phần 5.7 — Tính quality metrics

### Mục đích

Đánh giá Ward tại từng snapshot.

Lưu:
- Silhouette
- Davies–Bouldin
- Calinski–Harabasz
- Cluster balance

Inertia không phải metric chính để so sánh Ward với K-Means.

Ví dụ:

| Snapshot | Silhouette | DB | CH | Balance |
| :--- | :--- | :--- | :--- | :--- |
| 11/2023 | ... | ... | ... | ... |

## Phần 5.8 — Lặp lại cho toàn bộ development

### Mục đích

Tạo kết quả Ward đầy đủ trên đúng giai đoạn development.

11/2023 → Ward  
12/2023 → Ward  
...  
01/2025 → Ward

Mỗi snapshot đều:
lọc universe  
↓  
kiểm tra dữ liệu  
↓  
Robust Scaling mới  
↓  
Ward Global K  
↓  
assignment  
↓  
cluster representative/profile  
↓  
metrics

## Phần 5.9 — Lưu artifact Ward

### Mục đích

Đảm bảo có đầy đủ dữ liệu để kiểm tra, phân tích và temporal tracking.

Cần lưu:
- snapshot_date
- eligible universe
- feature set
- scaler parameters
- Global K
- cluster assignments
- cluster sizes
- cluster representatives
- cluster profiles
- quality metrics
- config
- run metadata

Đặc biệt phải có đủ dữ liệu để Nhiệm vụ 9 tính:
- ARI
- NMI
- persistence
- migration
- transition matrix
- cluster representative drift
- entry / exit

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file `.py` riêng lẻ; thông thường `runner.py` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**`src/delta_t1/experiments/runner.py`** — file đã có; điều phối Ward qua các snapshot.
> Mục đích: Giữ cùng development window, universe và Global K như K-Means.  
> Cách dùng trong nhiệm vụ này: Đọc config Ward rồi duyệt từng snapshot như baseline.

**`src/delta_t1/clustering/registry.py`** — file đã có; chọn implementation Ward.
> Mục đích: Cho phép runner chọn thuật toán từ config.  
> Cách dùng trong nhiệm vụ này: Config Ward được chuyển qua registry để lấy implementation hierarchical/Ward.

**`src/delta_t1/clustering/hierarchical.py`** — file đã có; thuật toán Ward/Agglomerative.
> Mục đích: Tạo cụm phân cấp với số cụm bằng Global K.  
> Cách dùng trong nhiệm vụ này: Nhận dữ liệu đã Robust Scale và trả assignment/model result.

**`src/delta_t1/features/preprocessing.py`** — file đã có; chuẩn hóa.
> Mục đích: Đảm bảo Ward dùng đúng cùng preprocessing với K-Means.  
> Cách dùng trong nhiệm vụ này: Áp dụng Robust Scaling per snapshot trước Ward.

**`src/delta_t1/clustering/base.py`** — file đã có; contract snapshot chung.
> Mục đích: Giữ schema output và logic chung tương thích với baseline.  
> Cách dùng trong nhiệm vụ này: Dùng để tạo profile/diagnostics tương đương K-Means.

**`src/delta_t1/evaluation/cluster_metrics.py`** — file đã có; đánh giá Ward.
> Mục đích: Tính quality metrics có thể so sánh giữa các phương án.  
> Cách dùng trong nhiệm vụ này: Lưu metric cho Nhiệm vụ 7 và 10.

### Cách các file phối hợp

> runner.py → registry.py → base.py → preprocessing.py → hierarchical.py (Ward, Global K) → cluster_metrics.py → artifact Ward.

## Kết quả cần đạt của Nhiệm vụ 5

- Ward assignments cho toàn bộ development;
- cluster sizes;
- cluster representatives;
- cluster profiles;
- scaler parameters;
- quality metrics;
- artifact theo snapshot;
- dữ liệu sẵn sàng cho Nhiệm vụ 7, 8, 9 và 10.

## Vị trí trong repo & Đường dẫn output

- **Code model / Thực thi**: `M2/notebooks/05_ward_hierarchical.ipynb` (phối hợp `src/delta_t1/clustering/hierarchical.py` và `src/delta_t1/experiments/runner.py`)
- **Mô hình / Trọng số (Models & Linkages)**: `M2/models/ward/` (lưu trữ ma trận linkage, cluster representatives, scaler parameters)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_5_Ward.md`
- **Artifacts thực nghiệm chuẩn hóa**: `M2/artifacts/m2-task5-ward-v1/` (chứa `assignments.jsonl`, `profiles.jsonl`, `diagnostics.jsonl`, `manifest.json`; lưu trong M2 để push lên GitHub)

# NHIỆM VỤ 6 — CHẠY PHƯƠNG ÁN C: PCA + K-MEANS

## Mục đích của Nhiệm vụ 6

Mục đích là tạo kết quả phân cụm PCA + K-Means chính thức trên toàn bộ development và kiểm tra việc giảm chiều trước K-Means có làm thay đổi cấu trúc cụm hay không.

Pipeline của phương án này khác hai phương án trước ở bước:
Robust Scaling  
↓  
PCA  
↓  
K-Means

PCA chỉ thuộc phương án C, không áp dụng chung cho K-Means baseline hoặc Ward. Đây cũng là cách kế hoạch hiện tại định nghĩa PCA.

## Đầu vào của Nhiệm vụ 6

- Global K từ Nhiệm vụ 3 (Global K = 2);
- toàn bộ development snapshots;
- runner market-only;
- cùng universe rule;
- cùng 8 feature;
- Robust Scaling;
- PCA rule đã freeze;
- missing/outlier policy;
- protocol M2.

Ví dụ:
Global K = 2 (đã khóa từ Nhiệm vụ 3)

Snapshot:
30/11/2023

Universe:
240 mã

Input:
240 × 8

## Phần 6.1 — Lấy dữ liệu của từng snapshot

### Mục đích

Đảm bảo PCA + K-Means sử dụng cùng dữ liệu đầu vào với hai phương án còn lại.

30/11/2023  
↓  
lọc universe  
↓  
lấy 8 feature

Ví dụ: 240 × 8.

Universe không được thay đổi riêng cho phương án PCA.

## Phần 6.2 — Kiểm tra dữ liệu trước xử lý

### Mục đích

Đảm bảo input hợp lệ trước khi chạy PCA.

Kiểm tra:
- n_eligible >= minimum (n_eligible >= 120)
- đủ 8 feature
- không NaN
- không Inf
- đúng schema

Nếu không đủ: skip snapshot + lưu lý do.

## Phần 6.3 — Robust Scaling theo snapshot

### Mục đích

PCA nhạy với thang đo nên phải chuẩn hóa trước.

240 × 8  
↓  
Median/IQR từng feature  
↓  
Robust Scaling  
↓  
240 × 8 đã scale

Đây vẫn là cùng bước preprocessing chung với K-Means và Ward.

## Phần 6.4 — Áp dụng PCA

### Mục đích

Biểu diễn 8 feature bằng một số thành phần ít hơn nhưng vẫn giữ phần lớn thông tin.

Protocol đề xuất:
chọn số component nhỏ nhất sao cho cumulative explained variance >= 90%.

Ví dụ:
8 feature  
↓ PCA  
PC1, PC2, PC3, PC4  
và: PC1 + PC2 + PC3 + PC4 >= 90% explained variance.

Số component cuối cùng phải được freeze trên development theo protocol, không tùy ý thay đổi mỗi lần chạy sau khi methodology đã khóa.

## Phần 6.5 — Lưu thông tin PCA

### Mục đích

Đảm bảo bước giảm chiều có thể kiểm tra và tái lập.

Cần lưu:
- n_components
- explained variance từng component
- cumulative explained variance
- PCA components/loadings
- các tham số cần thiết của PCA

Ví dụ:

| Component | Explained variance | Cumulative |
| :--- | :--- | :--- |
| PC1 | ... | ... |
| PC2 | ... | ... |
| PC3 | ... | ... |
| PC4 | ... | 0.91 |

## Phần 6.6 — Chạy K-Means với Global K trong không gian PCA

### Mục đích

Tạo phân cụm chính thức sau khi giảm chiều.

Ví dụ:
PCA output: 240 × 4  
↓  
K-Means  
↓  
Global K  
↓  
K cluster

Không chọn lại K riêng sau PCA.

## Phần 6.7 — Lưu cluster assignment

### Mục đích

Biết mỗi cổ phiếu thuộc cụm nào trong phương án PCA + K-Means.

Ví dụ:

| Snapshot | Mã | Cụm PCA+KMeans |
| :--- | :--- | :--- |
| 30/11/2023 | AAA | 2 |
| 30/11/2023 | BBB | 0 |
| 30/11/2023 | CCC | 3 |

## Phần 6.8 — Lưu centroid trong không gian PCA

### Mục đích

Có đại diện số học của từng cụm mà K-Means tạo ra sau PCA.

Ví dụ Cluster 0:
- PC1 = ...
- PC2 = ...
- PC3 = ...
- PC4 = ...

Centroid PCA có thể phục vụ:
- kiểm tra mô hình
- theo dõi drift trong không gian PCA
- tái lập kết quả

Tuy nhiên việc diễn giải ý nghĩa kinh tế của cụm nên quay lại 8 feature gốc, không chỉ nhìn PC1, PC2.

## Phần 6.9 — Xây cluster profile theo 8 feature gốc

### Mục đích

Đảm bảo phương án PCA vẫn có thể diễn giải và so sánh trực tiếp với K-Means và Ward.

Sau khi có assignment từ PCA + K-Means:
cluster assignment + 8 feature gốc của các mã  
↓  
tổng hợp profile

Ví dụ PCA+KMeans Cluster 0:
- Momentum cao
- Volatility thấp
- MDD trung bình
- Liquidity cao

Như vậy Nhiệm vụ 10 có thể so sánh profile giữa ba phương án trên cùng hệ feature gốc.

## Phần 6.10 — Tính quality metrics

### Mục đích

Đánh giá chất lượng phương án PCA + K-Means tại từng snapshot.

Lưu:
- Silhouette
- Davies–Bouldin
- Calinski–Harabasz
- Inertia
- Cluster balance

Các metric phân cụm cần được tính nhất quán trên không gian mà phương án thực sự dùng để clustering, đồng thời profile vẫn diễn giải bằng feature gốc.

## Phần 6.11 — Lặp lại cho toàn bộ development

### Mục đích

Tạo kết quả PCA + K-Means đầy đủ cho toàn bộ development.

11/2023 → PCA + K-Means  
12/2023 → PCA + K-Means  
...  
01/2025 → PCA + K-Means

Pipeline mỗi snapshot:
lọc universe  
↓  
kiểm tra dữ liệu  
↓  
Robust Scaling  
↓  
PCA  
↓  
K-Means Global K  
↓  
assignment  
↓  
centroid  
↓  
profile bằng feature gốc  
↓  
metrics

## Phần 6.12 — Lưu artifact PCA + K-Means

### Mục đích

Lưu đầy đủ cả thông tin preprocessing, PCA và clustering.

Cần lưu:
- snapshot_date
- eligible universe
- 8 feature
- scaler parameters
- PCA parameters
- n_components
- explained variance
- PCA-transformed representation cần thiết
- Global K
- cluster assignments
- centroids
- cluster sizes
- cluster profiles
- quality metrics
- config
- run metadata

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file `.py` riêng lẻ; thông thường `runner.py` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**`src/delta_t1/experiments/runner.py`** — file đã có; điều phối nhánh PCA + K-Means.
> Mục đích: Chạy pipeline comparator theo từng snapshot.  
> Cách dùng trong nhiệm vụ này: Đọc config của nhánh PCA, gọi preprocessing rồi K-Means và ghi artifact.

**`src/delta_t1/features/preprocessing.py`** — file đã có; file trọng tâm của Nhiệm vụ 6.
> Mục đích: Đã hỗ trợ Robust Scaling và PCA.  
> Cách dùng trong nhiệm vụ này: Trước hết scale snapshot, sau đó thực hiện PCA theo số component đã freeze. Trên holdout không được chọn lại số component.

**`src/delta_t1/clustering/kmeans.py`** — file đã có; clustering sau PCA.
> Mục đích: Phân cụm vector PCA bằng Global K.  
> Cách dùng trong nhiệm vụ này: Nhận đầu vào đã giảm chiều từ preprocessing và chạy K-Means.

**`src/delta_t1/clustering/base.py`** — file đã có; chuẩn hóa contract output.
> Mục đích: Giúp nhánh PCA+KMeans trả assignment/profile/diagnostics theo cấu trúc thống nhất.  
> Cách dùng trong nhiệm vụ này: Dùng để kết quả có thể so sánh với K-Means và Ward.

**`src/delta_t1/evaluation/cluster_metrics.py`** — file đã có; quality metrics.
> Mục đích: Đánh giá cụm tạo ra sau PCA.  
> Cách dùng trong nhiệm vụ này: Lưu metric và dùng ở Nhiệm vụ 7/10.

### Cách các file phối hợp

> runner.py → base.py → preprocessing.py (Robust Scaling → PCA) → kmeans.py (Global K) → cluster_metrics.py → PCA/model/assignment artifact.

## Kết quả cần đạt của Nhiệm vụ 6

- PCA parameters;
- số component đã freeze;
- explained variance;
- PCA-transformed data/artifact cần thiết;
- K-Means assignments;
- centroids;
- cluster sizes;
- cluster profiles trên 8 feature gốc;
- scaler parameters;
- quality metrics;
- artifact theo snapshot;
- dữ liệu sẵn sàng cho Nhiệm vụ 7, 8, 9 và 10.

## Vị trí trong repo & Đường dẫn output

- **Code model / Thực thi**: `M2/notebooks/06_pca_kmeans.ipynb` (kết hợp PCA trong `src/delta_t1/features/preprocessing.py` và `src/delta_t1/clustering/kmeans.py`)
- **Mô hình / Trọng số (Models & Transformers)**: `M2/models/pca_kmeans/` (lưu trữ PCA transformer objects, explained variance ratios, fitted KMeans models theo từng snapshot)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_6_PCA_KMeans.md`
- **Artifacts thực nghiệm chuẩn hóa**: `M2/artifacts/m2-task6-pca-kmeans-v1/` (chứa `assignments.jsonl`, `profiles.jsonl`, `diagnostics.jsonl`, `pca_diagnostics.jsonl`, `manifest.json`; lưu trong M2 để push lên GitHub)


# NHIỆM VỤ 7 — ĐÁNH GIÁ CHẤT LƯỢNG CỤM (CLUSTER QUALITY EVALUATION)

## Mục đích của Nhiệm vụ 7

Đánh giá chất lượng hình học và độ phân tách toán học của các cụm cổ phiếu được tạo ra trên 15 snapshots của Cửa sổ phát triển (11/2023 – 01/2025) bằng 5 chỉ số chất lượng nội bộ độc lập (Internal Cluster Quality Metrics):
- **Đánh giá chuyên sâu cấu hình tối ưu K=2:** Tập trung phân tích chất lượng của cấu hình K=2 (đã được khóa từ Nhiệm vụ 3) xuyên suốt 15 tháng để nhận diện độ chặt chẽ nội cụm và mức độ tách biệt giữa các nhóm cổ phiếu.
- **Theo dõi biến thiên qua chuỗi thời gian:** Đánh giá độ ổn định của 5 chỉ số chất lượng qua từng tháng, phát hiện các giai đoạn thị trường biến động mạnh hoặc xuất hiện hiện tượng phân mảnh cụm (fragmentation / outlier clusters).
- **Thống nhất chuẩn đầu ra:** Đảm bảo cả 3 phương án (**K-Means Baseline**, **Ward Hierarchical**, **PCA + K-Means**) đều có cùng cấu trúc trình bày trong Notebook, cùng định dạng bảng biểu, cùng hệ thống biểu đồ và cùng schema file xuất xưởng ra đĩa.
- **Tuân thủ ranh giới nghiên cứu M2:** Đánh giá chất lượng cụm hoàn toàn bằng các thước đo khoảng cách không gian đặc trưng, tuyệt đối không sử dụng tỷ suất sinh lời, Sharpe ratio hay các chỉ số đầu tư danh mục (thuộc M3).

## File code sử dụng trong nhiệm vụ và cách dùng

Nhiệm vụ 7 tuân thủ nguyên tắc cốt lõi của DELTA: **Tầng đánh giá chất lượng chỉ đọc dữ liệu chẩn đoán (diagnostics) đã được tạo ra từ pipeline huấn luyện ở Nhiệm vụ 4, 5, 6, không huấn luyện lại mô hình**.

> **RÀO CHẮN KỸ THUẬT QUAN TRỌNG CHO NGƯỜI THỰC HIỆN / AI:**  
> - Notebook của Nhiệm vụ 7 hoạt động **hoàn toàn độc lập**, chỉ sử dụng các thư viện chuẩn của Python (`pandas`, `matplotlib`, `os`).
> - **TUYỆT ĐỐI KHÔNG import hoặc copy code từ 3 module backend** (`cluster_metrics.py`, `base.py`, `runner.py`). Toàn bộ tính toán mô hình và khoảng cách vector đã được các module này xử lý xong ở các nhiệm vụ trước.
> - Các module backend bên dưới chỉ được liệt kê với vai trò **tài liệu tham chiếu nguồn gốc dữ liệu (provenance reference)** để phục vụ công tác kiểm toán học thuật.

### Các module hệ thống tham chiếu nguồn gốc (Backend Reference Modules)
- **`src/delta_t1/evaluation/cluster_metrics.py`** — Tài liệu tham chiếu công thức: Cung cấp định nghĩa toán học chuẩn của dự án cho 5 chỉ số (Silhouette, DB, CH, Inertia, Balance) mà pipeline đã sử dụng để tính toán. Người làm Nhiệm vụ 7 **không gọi lại hàm này**.
- **`src/delta_t1/clustering/base.py`** — Tài liệu tham chiếu cấu trúc: Định nghĩa cấu trúc từ điển `diagnostics` gắn liền với từng snapshot.
- **`src/delta_t1/experiments/runner.py`** — Bộ tạo dữ liệu: Đã điều phối quá trình fit mô hình trên 15 snapshots và xuất xưởng file kết quả `diagnostics.csv`.

### Các file code thực thi chính của Nhiệm vụ 7 (Notebooks)
Người thực hiện từng phương án mở và thực thi trực tiếp notebook tương ứng trong thư mục `M2/notebooks/`:
- **Phương án 1 (K-Means Baseline):** `M2/notebooks/07_cluster_quality_evaluation_kmeans.ipynb`
- **Phương án 2 (Ward Hierarchical):** `M2/notebooks/07_cluster_quality_evaluation_ward.ipynb`
- **Phương án 3 (PCA + K-Means):** `M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb`

### Quy trình phối hợp 5 bước (Workflow)
1. **Bước 1 (Đọc dữ liệu chẩn đoán đầu vào):** Sử dụng `pandas` đọc trực tiếp file `diagnostics.csv` từ thư mục artifact chuẩn hóa của phương án tương ứng:
   - K-Means: `M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv`
   - Ward: `M2/artifacts/m2-task5-ward-v1/diagnostics.csv`
   - PCA + K-Means: `M2/artifacts/m2-task6-pca-kmeans-v1/diagnostics.csv`
2. **Bước 2 (Trích xuất & Xuất file tóm tắt chất lượng đầu ra):** Lọc lấy 15 dòng dữ liệu ứng với cấu hình K=2, dùng các hàm thống kê mô tả cơ bản của pandas để tính Mean, Median, Min, Max cho 5 chỉ số và tự động xuất ra file `quality_summary.csv` vào đúng đường dẫn đích:
   - K-Means: `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv`
   - Ward: `M2/artifacts/m2-evaluation-ward/quality_summary.csv`
   - PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv`
3. **Bước 3 (Hiển thị 2 Bảng chuẩn):** Hiển thị Bảng tổng hợp (Bảng 1) và Bảng chi tiết 15 snapshots (Bảng 2) dưới dạng bảng HTML tương tác (`display()`).
4. **Bước 4 (Trực quan hóa 5 Biểu đồ đường):** Dùng `matplotlib` vẽ 5 biểu đồ chuỗi thời gian cho 5 chỉ số chất lượng từ Mục 7.1 đến 7.5 kèm đường tham chiếu Median nét đứt màu đỏ.
5. **Bước 5 (Soạn thảo Nhận định kinh tế & Rào chắn học thuật):** Trình bày phân tích hiện tượng thị trường và giới hạn toán học trực tiếp vào các ô Markdown trong Notebook, sau đó tổng hợp thành file báo cáo Markdown độc lập:
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans.md`

## Quy chuẩn Dữ liệu Đầu vào (Input Contract)

Nhiệm vụ 7 chỉ nhận duy nhất file kết quả chẩn đoán **`diagnostics.csv`** (chính là `per-snapshot diagnostics` theo quy chuẩn `DELTA_UNIFIED_PROJECT_PLAN.md`) đã được pipeline sinh ra sẵn từ Nhiệm vụ 4, 5, 6:
- **K-Means:** `M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv`
- **Ward:** `M2/artifacts/m2-task5-ward-v1/diagnostics.csv`
- **PCA + K-Means:** `M2/artifacts/m2-task6-pca-kmeans-v1/diagnostics.csv`

*(Lưu ý về quy mô dữ liệu: File chẩn đoán gốc lưu trữ toàn bộ các mức K khảo sát ban đầu từ 2 đến 8 gồm 105 dòng. **Nhiệm vụ 7 chỉ trích xuất và phân tích duy nhất 15 dòng ứng với cấu hình tối ưu K=2 đã khóa ở Nhiệm vụ 3**).*

Cấu trúc các cột bắt buộc phải có trong file diagnostics: `snapshot_date`, `k`, `silhouette`, `davies_bouldin`, `calinski_harabasz`, `inertia`, `cluster_balance`, `cluster_sizes`, `converged`.

## Quy chuẩn File Artifacts xuất ra đĩa (Disk Output Contract)

Sau khi chạy xong Notebook, code bắt buộc phải tự động lưu **duy nhất 1 file CSV** đại diện cho **`quality metrics`** của mô hình tại K=2 vào đúng thư mục evaluation chuẩn của từng phương án:
- **K-Means:** `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv`
- **Ward:** `M2/artifacts/m2-evaluation-ward/quality_summary.csv`
- **PCA + K-Means:** `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv`

### Schema cố định gồm đúng 7 cột:
Tất cả các file `quality_summary.csv` xuất xưởng của cả 3 mô hình bắt buộc phải có đúng 7 cột với tên và thứ tự như sau:
1. `metric` (String: Tên 5 chỉ số lần lượt theo hàng: `silhouette`, `davies_bouldin`, `calinski_harabasz`, `inertia`, `cluster_balance`)
2. `n_total` (Int: Tổng số snapshots đánh giá = 15)
3. `n_available` (Int: Số snapshots có giá trị hợp lệ = 15)
4. `mean` (Float: Giá trị trung bình qua 15 tháng)
5. `median` (Float: Giá trị trung vị qua 15 tháng — *Thước đo chính để Nhiệm vụ 10 so sánh xếp hạng mô hình*)
6. `minimum` (Float: Giá trị nhỏ nhất trong 15 tháng)
7. `maximum` (Float: Giá trị lớn nhất trong 15 tháng)

## Các phần thực hiện chi tiết trong Notebook & Bảng Output chuẩn

Cả 3 notebook đều phải trình bày cấu trúc thống nhất qua 5 chỉ số và xuất ra **2 bảng số liệu chuẩn**:

### Bảng Output chuẩn 1 — Tóm tắt thống kê chất lượng cụm K=2 (Kích thước 5 dòng x 7 cột)
Hiển thị ở phần đầu notebook qua hàm `display()`:

| Cột dữ liệu | Kiểu dữ liệu | Ý nghĩa |
| :--- | :--- | :--- |
| `metric` | String | Tên chỉ số (`silhouette`, `davies_bouldin`, `calinski_harabasz`, `inertia`, `cluster_balance`) |
| `n_total` | Int | Tổng số snapshot đánh giá (15) |
| `n_available` | Int | Số snapshot có dữ liệu hợp lệ (15) |
| `mean` | Float | Giá trị trung bình 15 tháng |
| `median` | Float | Giá trị trung vị 15 tháng (Thước đo chính xếp hạng mô hình ở Nhiệm vụ 10) |
| `minimum` | Float | Giá trị thấp nhất ghi nhận |
| `maximum` | Float | Giá trị cao nhất ghi nhận |

### Bảng Output chuẩn 2 — Chi tiết chất lượng qua 15 Snapshots tại K=2 (Kích thước 15 dòng x 6 cột)
Hiển thị chi tiết diễn biến từng tháng của cấu hình K=2 qua hàm `display()`:

| Tên cột | Kiểu dữ liệu | Ý nghĩa |
| :--- | :--- | :--- |
| `Snapshot` | String | Ngày chốt dữ liệu (2023-11-30 đến 2025-01-24) |
| `Silhouette` | Float | Điểm Silhouette tại snapshot |
| `DB` | Float | Chỉ số Davies-Bouldin tại snapshot |
| `CH` | Float | Chỉ số Calinski-Harabasz tại snapshot |
| `Inertia` | Float | Quán tính nội cụm tại snapshot |
| `Balance` | Float | Tỷ số kích thước cụm (`min_size / max_size`) |

## Quy chuẩn Trực quan hóa (Visualization Contract)

Cả 3 notebook bắt buộc phải vẽ **đầy đủ 5 biểu đồ đường (Line plots)** tương ứng với 5 tiểu mục 7.1 đến 7.5:

1. **Biểu đồ 7.1 — Silhouette Score qua 15 tháng:**
   - Trục hoành: 15 ngày snapshot; Trục tung: Điểm Silhouette.
   - Bắt buộc vẽ **đường nét đứt màu đỏ** thể hiện `Median` của Silhouette kèm nhãn giá trị cụ thể.
   - Định hướng: Điểm càng cao càng tốt (ngưỡng chấp nhận > 0.5; ngưỡng xuất sắc > 0.7).
2. **Biểu đồ 7.2 — Davies-Bouldin Index qua 15 tháng:**
   - Trục hoành: 15 ngày snapshot; Trục tung: Giá trị DB Index.
   - Bắt buộc vẽ đường nét đứt màu đỏ thể hiện `Median`.
   - Định hướng: Giá trị càng thấp càng tốt (các cụm cách xa nhau và gọn gàng).
3. **Biểu đồ 7.3 — Calinski-Harabasz Index qua 15 tháng:**
   - Trục hoành: 15 ngày snapshot; Trục tung: Điểm CH Index.
   - Bắt buộc vẽ đường nét đứt màu đỏ thể hiện `Median`.
   - Định hướng: Giá trị càng cao càng tốt (phương sai liên cụm vượt trội phương sai nội cụm).
4. **Biểu đồ 7.4 — Quán tính nội cụm (Inertia) qua 15 tháng:**
   - Trục hoành: 15 ngày snapshot; Trục tung: Quán tính Inertia.
   - Ghi chú rõ trên biểu đồ hoặc tiêu đề: Biến thiên tỷ lệ thuận với số lượng cổ phiếu quan sát N.
5. **Biểu đồ 7.5 — Tỷ số cân bằng cụm (Cluster Balance) qua 15 tháng:**
   - Trục hoành: 15 ngày snapshot; Trục tung: Tỷ số cân bằng (`min_size / max_size`).
   - Bắt buộc vẽ đường nét đứt màu đỏ thể hiện `Median` và **đường nét chấm đỏ đậm thể hiện ngưỡng tối thiểu 5% (0.05)** để cảnh báo hiện tượng phân mảnh.

*Quy cách đồ thị: Kích thước chuẩn `figsize=(10, 3.8)`, xoay nhãn ngày 45 độ, lưới mờ `alpha=0.5`.*

## Nhận định kinh tế tài chính & Rào chắn học thuật (Academic Invariants & Diagnostic Rubrics)

> **RÀO CHẮN HỌC THUẬT BẮT BUỘC VỀ KỊCH BẢN GIẢ ĐỊNH & RÀNG BUỘC THỰC CHỨNG (EVIDENCE-FIRST RULE):**
> 1. **Các kịch bản chỉ mang tính chất GIẢ ĐỊNH HƯỚNG DẪN (Hypothetical-Only Scenarios):** Các kịch bản (Kịch bản A, B...) và các ngưỡng số liệu nêu dưới đây thuần túy là bộ quy tắc phân tích theo điều kiện (Diagnostic Rubrics) để định hướng tư duy học thuật. AI / người thực hiện **TUYỆT ĐỐI KHÔNG ĐƯỢC sao chép các kịch bản này làm kết luận định kiến (hindsight bias)**, không được tự suy đoán hoặc xem các giả định là kết quả đã có sẵn.
> 2. **Ràng buộc số liệu thực tế (Ground-Truth Binding):** Mọi phán quyết, đánh giá và kết luận bắt buộc phải căn cứ 100% vào số liệu thực tế thu được từ file `quality_summary.csv` và 2 bảng thống kê, 5 biểu đồ được sinh ra trong chính Notebook thực thi. Khi đưa ra bất kỳ kết luận nào, bắt buộc phải trích dẫn chính xác con số thực tế đi kèm (ví dụ: Median Silhouette = ..., Cluster Balance = ...).
> 3. **Quy tắc tổng hợp 3 tầng (Three-tier Synthesis):** Tuyệt đối không chỉ đọc lại các con số cơ học. Bắt buộc phải biện luận qua 3 tầng: Hiện tượng toán học quan sát được -> Nguyên nhân bản chất thị trường chứng khoán Việt Nam -> Ý nghĩa thực tế và tác động đến các nhiệm vụ tiếp theo.

Sau khi chạy code hiển thị 2 bảng và 5 biểu đồ, người thực hiện **bắt buộc phải tạo các ô Markdown trong Notebook** để trình bày phân tích học thuật theo đúng 2 phần nội dung chuẩn hóa dưới đây:

### 1. Bộ quy tắc phân tích theo điều kiện (Diagnostic Rubrics)

#### Quy tắc kiểm định mức độ cân bằng cụm (Balance Diagnostic Test):
- **Công thức tính:** Tỷ trọng cụm nhỏ trên toàn thị trường `pct_small = min_size / N` và tỷ số cân bằng cụm `Cluster Balance = min_size / max_size`.
- **Kịch bản A (Nếu Balance < 0.10 hoặc cụm nhỏ chiếm < 10% thị trường):**
  - **Kết luận bắt buộc:** Phải khẳng định đây là hiện tượng "Phân cụm bất đối xứng / Cô lập nhóm ngoại lai" (Asymmetric Outlier Isolation). Thuật toán không chia thị trường thành 2 nửa cân bằng, mà đang gom đại đa số thị trường vào 1 Cụm lớn và tách một nhóm nhỏ các mã cực đoan vào Cụm nhỏ.
  - **Giải thích nguyên nhân:** Do thị trường chứng khoán Việt Nam có tính đầu cơ cao, tạo ra các cổ phiếu "siêu động lượng" hoặc biến động cực đại (heavy tails). Do dự án thống nhất không dùng Clipping/Winsorization nên các quan sát ngoại lai này hút tâm cụm.
  - **Cảnh báo học thuật:** Điểm Silhouette cao trong trường hợp này phản ánh khoảng cách hình học xa của nhóm ngoại lai, không đồng nghĩa với việc thị trường có 2 chế độ cân bằng.
- **Kịch bản B (Nếu Balance >= 0.30):**
  - **Kết luận:** Thị trường có sự phân hóa tương đối đồng đều thành 2 chế độ vận động song song (Dual-regime market).

#### Quy tắc kiểm định Quán tính nội cụm (Inertia Caveat Rule):
- **Nguyên tắc:** Quán tính Inertia tỷ lệ thuận với số lượng cổ phiếu quan sát N.
- **Kết luận bắt buộc:** Tuyệt đối không so sánh Inertia tuyệt đối giữa các tháng có quy mô mã khác nhau (ví dụ không so sánh tháng có 140 mã với tháng có gần 800 mã). Inertia chỉ có giá trị khi so sánh các cấu hình K trong cùng một tháng.

#### Phân cấp ưu tiên tiêu chí theo DELTA_UNIFIED_PROJECT_PLAN.md:
- **Tiêu chí cấp 1 (Primary Criterion):** `Median Silhouette cao nhất`. Đây là cơ sở toán học cao nhất để chứng minh K=2 tạo ra ranh giới tách biệt rõ ràng nhất giữa các nhóm cổ phiếu trên thị trường Việt Nam.
- **Tiêu chí phá vỡ thế cân bằng (Secondary Tie-breaker):** `Median Davies-Bouldin thấp hơn`. Dùng khi Silhouette giữa các phương án xấp xỉ nhau.
- **Tiêu chí kiểm định an toàn (Sanity Diagnostics):** `Calinski-Harabasz` và `Cluster Balance` dùng để kiểm tra độ tin cậy, cảnh báo nguy cơ phân cụm bị chi phối bởi các cổ phiếu dị biệt.

#### Ranh giới phương pháp luận nghiêm ngặt:
- **Nghiêm cấm tối ưu hóa bằng lợi nhuận:** Không được đưa Return, Sharpe hay ROI vào Nhiệm vụ 7 để chọn mô hình có chất lượng "tốt hơn". Đánh giá chất lượng cụm độc lập hoàn toàn với bài toán danh mục M3.

---

### 2. Khung kết luận 3 phần bắt buộc ở Cell cuối Notebook 7:

Cuối Notebook 7, bắt buộc phải có một ô Markdown tổng kết phán quyết học thuật gồm đầy đủ 3 phần:
- **Phần A (Phán quyết Kỹ thuật):** Tóm tắt điểm mạnh toán học (độ phân tách Silhouette, độ gọn DB theo số liệu thực chứng) và điểm yếu cố hữu (mức độ mất cân bằng tỷ trọng Cluster Balance).
- **Phần B (Bản chất thị trường):** Cấu trúc cụm phản ánh đặc trưng gì về hành vi dòng tiền và phân phối dữ liệu thị trường Việt Nam (tính phân hóa dòng tiền, hiện tượng cô lập cổ phiếu cực đoan).
- **Phần C (Handoff cho Nhiệm vụ 10):** Đánh giá xem mô hình có đủ tiêu chuẩn chất lượng hình học để bước vào vòng so sánh đối đầu ở Nhiệm vụ 10 hay không.

## Kết quả cần đạt & Đường dẫn bàn giao (Deliverables)

Mỗi mô hình khi hoàn thành Nhiệm vụ 7 phải có đầy đủ bộ sản phẩm:
1. **Notebook thực thi hoàn chỉnh:**
   - K-Means: `M2/notebooks/07_cluster_quality_evaluation_kmeans.ipynb`
   - Ward: `M2/notebooks/07_cluster_quality_evaluation_ward.ipynb`
   - PCA + K-Means: `M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb`
2. **File Artifact xuất ra đĩa chuẩn hóa:**
   - K-Means: `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv` (7 cột chuẩn)
   - Ward: `M2/artifacts/m2-evaluation-ward/quality_summary.csv` (7 cột chuẩn)
   - PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv` (7 cột chuẩn)
3. **Báo cáo chuyên đề Markdown:**
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans.md`

# NHIỆM VỤ 8 — PHÂN TÍCH HỒ SƠ CỤM (CLUSTER PROFILING)

## Mục đích của Nhiệm vụ 8

Khắc họa và nhận diện rõ nét tính chất kinh tế của 2 cụm cổ phiếu (K=2) dựa trên 8 đặc trưng tài chính cốt lõi (Unscaled Features).
- Hiểu rõ động lực phân tách của các cụm qua các khía cạnh: Động lượng (Momentum), Rủi ro hệ thống (Beta), Biến động & Sụt giảm (Vol, MDD) và Thanh khoản (Liquidity).
- Đảm bảo tính nhất quán tuyệt đối về cấu trúc số liệu, bảng biểu và đồ thị giữa 3 phương án: **K-Means Baseline**, **Ward Hierarchical** và **PCA + K-Means**.
- Tuân thủ ranh giới nghiên cứu M2: Đánh giá thuần túy cấu trúc vi mô, không biến hồ sơ cụm thành khuyến nghị đầu tư danh mục (thuộc M3).

## File code sử dụng trong nhiệm vụ và cách dùng

Nhiệm vụ 8 tuân thủ nguyên tắc cốt lõi của DELTA: **Tầng đánh giá & phân tích hồ sơ chỉ tiêu thụ artifacts đã đóng băng, không chạy lại quy trình huấn luyện hay trích xuất đặc trưng**.

### Các module hệ thống tham chiếu (Backend Modules)
- **`src/delta_t1/experiments/runner.py`** — Module điều phối thực nghiệm: Đã thực thi ở Nhiệm vụ 4, 5, 6 để huấn luyện mô hình, tính toán tâm cụm và xuất xưởng file artifact `cluster_profiles.csv` (13 cột chuẩn). Người làm Nhiệm vụ 8 **không gọi lại runner.py**.
- **`src/delta_t1/clustering/base.py`** — Module cơ sở phân cụm: Đóng vai trò là tài liệu tham chiếu định nghĩa hồ sơ cụm (`ClusterProfile`) và thuật toán căn chỉnh nhãn (`aligned_cluster_id`) giữa các tháng.
- **`src/delta_t1/features/preprocessing.py`** — Module tiền xử lý đặc trưng: Cung cấp tham số chuẩn hóa RobustScaler (median và IQR) được lưu trong file model JSON để hỗ trợ vẽ biểu đồ Radar trên thang Robust Z-Score.

### Các file code thực thi chính của Nhiệm vụ 8 (Notebooks)
Người thực hiện từng phương án mở và chạy trực tiếp notebook tương ứng của mình trong thư mục `M2/notebooks/`:
- **Phương án 1 (K-Means Baseline):** `M2/notebooks/08_cluster_profiling_kmeans.ipynb`
- **Phương án 2 (Ward Hierarchical):** `M2/notebooks/08_cluster_profiling_ward.ipynb`
- **Phương án 3 (PCA + K-Means):** `M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb`

### Quy trình phối hợp (Workflow)
1. **Bước 1 (Đọc dữ liệu hồ sơ cụm đầu vào):** Pipeline huấn luyện tự động xuất ra file `cluster_profiles.csv` (13 cột chuẩn) vào thư mục artifact tương ứng, Notebook sẽ đọc trực tiếp từ:
   - K-Means: `M2/artifacts/m2-task4-kmeans-baseline-v1/cluster_profiles.csv`
   - Ward: `M2/artifacts/m2-task5-ward-v1/cluster_profiles.csv`
   - PCA + K-Means: `M2/artifacts/m2-task6-pca-kmeans-v1/cluster_profiles.csv`
2. **Bước 2 (Nạp dữ liệu vào DataFrame):** Notebook nạp file CSV tương ứng từ đường dẫn trên bằng lệnh `pd.read_csv()`.
3. **Bước 3 (Tổng hợp số liệu & Trực quan hóa):** Chạy code pandas để xuất ra 3 Bảng số liệu chuẩn và 2 Biểu đồ chuẩn (Radar Chart, Heatmap).
4. **Bước 4 (Viết nhận định & Báo cáo):** Soạn thảo nhận định tài chính và giới hạn học thuật vào các ô Markdown trong Notebook, sau đó tổng hợp thành file báo cáo Markdown độc lập:
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_PCA_KMeans.md`

## Quy chuẩn Dữ liệu Đầu vào (Input Contract)

Nhiệm vụ 8 chỉ nhận duy nhất file kết quả **`cluster_profiles.csv`** gồm đúng **13 cột chuẩn** đã được tạo ra từ Nhiệm vụ 4, 5, 6:
- K-Means: `M2/artifacts/m2-task4-kmeans-baseline-v1/cluster_profiles.csv`
- Ward: `M2/artifacts/m2-task5-ward-v1/cluster_profiles.csv`
- PCA + K-Means: `M2/artifacts/m2-task6-pca-kmeans-v1/cluster_profiles.csv` (đã được ánh xạ ngược inverse transform về 8 chiều gốc ngay từ Nhiệm vụ 6, không chứa chuỗi JSON thô).

*(Cấu trúc 13 cột chuẩn: `snapshot_date`, `raw_cluster_id`, `aligned_cluster_id`, `size`, `size_ratio`, `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21`).*

## Các phần thực hiện chi tiết trong Notebook & Bảng Output chuẩn

### Phần 8.1 — Tổng hợp hồ sơ đặc trưng theo cụm (Cluster Profiles)

**Mục đích:** Xác định chân dung điển hình của từng cụm xuyên suốt toàn bộ 15 tháng phát triển (2023-11-30 đến 2025-01-24).

**Quy tắc thống kê:**
- **Độ đo chính:** Tính **Giá trị trung bình (Mean)** của 8 đặc trưng gốc và quy mô `size` theo từng cụm qua 15 tháng.
- **Độ đo kiểm chứng:** Bổ sung dòng **Trung vị (Median)** ngay dưới dòng Mean để đánh giá mức độ ảnh hưởng của các quan sát ngoại lai.
- **Chuẩn hóa đơn vị:** Cột thanh khoản `liquidity_21` bắt buộc quy đổi sang đơn vị **tỷ VNĐ/phiên** (chia cho 10^9).

**Bảng Output chuẩn 1 (Kích thước 4 dòng x 10 cột):**

| Cột dữ liệu | Kiểu dữ liệu | Ý nghĩa |
| :--- | :--- | :--- |
| `aligned_cluster_id` | String | Nhãn cụm: Cụm 0 (Mean), Cụm 0 (Median), Cụm 1 (Mean), Cụm 1 (Median) |
| `size` | Float / Int | Số lượng cổ phiếu bình quân thuộc cụm |
| `liquidity_21_ty_vnd` | Float | Thanh khoản bình quân 21 phiên (tỷ VNĐ/phiên) |
| `beta_126` | Float | Hệ số rủi ro thị trường 126 phiên so với VNINDEX |
| `vol_63` | Float | Độ biến động lịch sử 63 phiên |
| `mdd_126` | Float | Mức sụt giảm tối đa 126 phiên (giá trị âm) |
| `mom_21` | Float | Động lượng giá 1 tháng |
| `mom_63` | Float | Động lượng giá 3 tháng |
| `mom_126` | Float | Động lượng giá 6 tháng |
| `mom_252` | Float | Động lượng giá 12 tháng (1 năm) |

### Phần 8.2 — So sánh đối đầu và chuỗi thời gian

**Mục đích:** Đo lường mức độ phân tách giữa 2 cụm và theo dõi độ ổn định về quy mô và thanh khoản qua 15 tháng. Cả 3 notebook đều phải xuất ra **2 bảng so sánh chuẩn**:

**Bảng Output chuẩn 2: So sánh đối đầu giữa Cụm 0 và Cụm 1 (Kích thước 9 dòng x 4 cột):**

| Tên cột | Ý nghĩa |
| :--- | :--- |
| `Đặc trưng` | Lần lượt 9 dòng: size, liquidity_21 (tỷ VND), beta_126, vol_63, mdd_126, mom_21, mom_63, mom_126, mom_252 |
| `Cụm 0 (Mean)` | Giá trị trung bình 15 tháng của Cụm 0 |
| `Cụm 1 (Mean)` | Giá trị trung bình 15 tháng của Cụm 1 |
| `Chênh lệch (Cụm 0 - Cụm 1)` | Hiệu số giữa Cụm 0 và Cụm 1 để chỉ rõ động lực phân cụm chính |

**Bảng Output chuẩn 3: Chuỗi thời gian quy mô và thanh khoản qua 15 Snapshots (Kích thước 15 dòng x 5 cột):**

| Tên cột | Ý nghĩa |
| :--- | :--- |
| `Snapshot` | Ngày chốt dữ liệu (2023-11-30 đến 2025-01-24) |
| `Size Cụm 0` | Số lượng cổ phiếu của Cụm 0 tại snapshot |
| `Size Cụm 1` | Số lượng cổ phiếu của Cụm 1 tại snapshot |
| `Liquidity Cụm 0 (tỷ VND)` | Thanh khoản trung bình Cụm 0 tại snapshot |
| `Liquidity Cụm 1 (tỷ VND)` | Thanh khoản trung bình Cụm 1 tại snapshot |

### Phần 8.3 — Trực quan hóa chuẩn hóa (Visualization Contract)

Cả 3 notebook bắt buộc phải sinh ra **cùng 2 biểu đồ** trực quan:

#### Biểu đồ 1: Radar Chart (Biểu đồ mạng nhện đa trục)
- **Hệ trục:** Trục tọa độ cực (polar plot) với 8 đỉnh tương ứng 8 đặc trưng: `mom_21`, `mom_63`, `mom_126`, `mom_252`, `vol_63`, `mdd_126`, `beta_126`, `liquidity_21`.
- **Thang đo:** Sử dụng giá trị chuẩn hóa **Robust Z-Score** giới hạn trong biên độ [-3, 3].
- **Đường tham chiếu:** Bắt buộc vẽ đường tròn nét đứt màu xám tại `y = 0` đại diện cho **Trung vị thị trường (Market Median)**.
- **Tương tác:** Có Dropdown widget cho phép chọn xem từng snapshot hoặc hiển thị snapshot gần nhất.

#### Biểu đồ 2: Heatmap 2D (Bản đồ nhiệt ma trận đặc trưng)
- **Cấu trúc:** Ma trận kích thước 2 hàng (Cụm 0, Cụm 1) x 8 cột (8 đặc trưng).
- **Màu sắc:** Bảng màu chuẩn hóa `cmap='RdBu_r'`, điểm trung hòa tại `center = 0`.
- **Hiển thị số:** Bật hiển thị số thực trực tiếp trên các ô (`annot=True`, định dạng 2 chữ số thập phân).

### Phần 8.4 — Nhận định kinh tế tài chính & Rào chắn học thuật (Profiling Rubrics & Academic Invariants)

> **RÀO CHẮN HỌC THUẬT BẮT BUỘC VỀ KỊCH BẢN GIẢ ĐỊNH & RÀNG BUỘC THỰC CHỨNG (EVIDENCE-FIRST RULE):**
> 1. **Các kịch bản chỉ mang tính chất GIẢ ĐỊNH HƯỚNG DẪN (Hypothetical-Only Scenarios):** Các định danh nhóm và quy tắc điều kiện dưới đây thuần túy là bộ khung phương pháp luận (Profiling Rubrics) để hướng dẫn tư duy phân tích. AI / người thực hiện **TUYỆT ĐỐI KHÔNG ĐƯỢC sao chép các kịch bản này làm kết luận định kiến**, không tự suy đoán hoặc gán ghép kết quả nếu chưa kiểm tra số liệu thực tế.
> 2. **Ràng buộc số liệu thực tế (Ground-Truth Binding):** Mọi nhận định về hồ sơ đặc trưng bắt buộc phải căn cứ 100% vào số liệu thực tế từ file `cluster_profiles.csv`, 3 bảng thống kê và 2 biểu đồ (Radar Chart, Heatmap) được xuất ra trong chính Notebook thực thi. Khi nhận định, bắt buộc phải trích dẫn giá trị Mean/Median và Robust Z-Score cụ thể của từng đặc trưng.
> 3. **Quy tắc tổng hợp 3 tầng (Three-tier Synthesis):** Phân tích qua 3 tầng: Mức chênh lệch đặc trưng thực tế -> Bản chất hành vi dòng tiền và khẩu vị rủi ro trên TTCK Việt Nam -> Ý nghĩa thực tế đối với bài toán phân bổ vốn ở Milestone M3.

Sau khi chạy code hiển thị bảng và biểu đồ, người thực hiện **bắt buộc phải tạo các ô Markdown trong Notebook** để trình bày phân tích học thuật theo đúng các nội dung chuẩn hóa dưới đây:

#### 1. Bộ quy tắc phân tích theo điều kiện (Profiling Rubrics)

##### Quy tắc xác định Động lực phân cụm chính (Primary Driver Test):
- **Cách đo lường:** Tính độ chênh lệch chuẩn hóa (Delta trên thang Robust Z-Score) giữa Cụm 0 và Cụm 1 trên cả 8 đặc trưng.
- **Kết luận bắt buộc:** Căn cứ vào độ chênh lệch cực đại từ số liệu thực tế, chỉ rõ đặc trưng nào (Thanh khoản `liquidity_21`, Động lượng ngắn hạn `mom_21`, hay Rủi ro hệ thống `beta_126`) là "Động lực phân tách chi phối số 1" khiến thuật toán chia tách thị trường.

##### Quy tắc định danh Chân dung kinh tế (Economic Persona Mapping):
- **Cơ chế đối chiếu:** Đối chiếu vị trí tâm cụm với đường tham chiếu Trung vị thị trường (đường tròn nét đứt `y = 0` trên biểu đồ Radar Chart):
  - **Kịch bản Cụm dẫn dắt / Thu hút dòng tiền:** Nếu Cụm có Thanh khoản và Động lượng vượt trội dương (`> 0` trên thang Robust Z-Score) -> Gán nhãn học thuật chuẩn mực (ví dụ: "Nhóm Cổ phiếu Dẫn dắt / Thu hút dòng tiền tích cực").
  - **Kịch bản Cụm đại trà / Dòng tiền thờ ơ:** Nếu Cụm có Thanh khoản thấp và Động lượng âm hoặc mờ nhạt (`< 0` trên thang Robust Z-Score) -> Gán nhãn học thuật chuẩn mực (ví dụ: "Nhóm Cổ phiếu Đại trà / Dòng tiền thờ ơ / Phòng thủ").

##### Quy tắc kiểm tra tính nhất quán theo thời gian (Profile Temporal Consistency):
- Đánh giá xem qua 15 tháng, Cụm dẫn dắt có giữ vững được đặc tính động lượng cao hay không, hay vào những giai đoạn thị trường giảm mạnh (như tháng 04/2024 hoặc 07/2024), Cụm này lại trở thành nhóm sụt giảm mạnh nhất do có hệ số Beta cao?

#### 2. Giới hạn diễn giải học thuật (Academic Invariants & Boundaries)
- **Mean nhạy với quan sát cực đoan:** Giá trị trung bình của cụm không đại diện cho phân phối của từng cổ phiếu đơn lẻ bên trong cụm; cần đối chiếu thêm với dòng Trung vị (Median).
- **Tuyệt đối không khuyến nghị đầu tư:** Sự vượt trội về thanh khoản hay động lượng ở giai đoạn M2 chỉ mô tả đặc tính nhóm trong quá khứ, không suy diễn thành khuyến nghị "nên mua cổ phiếu thuộc Cụm dẫn dắt".
- **Duy trì nhãn trung tính:** Giữ nguyên tên gọi kỹ thuật trung tính "Cụm 0" và "Cụm 1", không tùy tiện gán nhãn chủ quan như "siêu cổ phiếu", "tinh hoa" hay "penny".
- **Ranh giới M2 và M3:** Đánh giá tỷ suất sinh lời hay Sharpe ratio thuộc về bước Backtest (Milestone M3), nghiêm cấm đưa các chỉ số lợi nhuận vào Nhiệm vụ 8.

---

#### 3. Khung kết luận 3 phần bắt buộc ở Cell cuối Notebook 8:

Cuối Notebook 8, bắt buộc phải có một ô Markdown tổng kết phán quyết học thuật gồm đầy đủ 3 phần:
- **Phần A (Chân dung kinh tế):** Định danh bản chất kinh tế rõ ràng của 2 cụm dựa trên các số liệu thực chứng (không dùng từ ngữ cảm tính).
- **Phần B (Động lực phân tách chính):** Khẳng định yếu tố cốt lõi nào tạo nên sự khác biệt giữa 2 cụm (dòng tiền thanh khoản hay tốc độ tăng giá động lượng).
- **Phần C (Tính khả thi cho M3):** Nhận định xem cụm dẫn dắt có đủ thanh khoản thực tế để quỹ đầu tư giải ngân mà không bị trượt giá lớn ở giai đoạn Backtest M3 hay không.

## Kết quả cần đạt & Đường dẫn bàn giao (Deliverables)

Mỗi mô hình khi hoàn thành Nhiệm vụ 8 phải có đầy đủ bộ bàn giao gồm:
1. **Notebook thực thi hoàn chỉnh:**
   - K-Means: `M2/notebooks/08_cluster_profiling_kmeans.ipynb`
   - Ward: `M2/notebooks/08_cluster_profiling_ward.ipynb`
   - PCA + K-Means: `M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb`
2. **Hình ảnh biểu đồ xuất xưởng (lưu vào đúng thư mục evaluation của từng mô hình):**
   - K-Means: `M2/artifacts/m2-evaluation-kmeans/radar_chart.png`, `M2/artifacts/m2-evaluation-kmeans/heatmap.png`
   - Ward: `M2/artifacts/m2-evaluation-ward/radar_chart.png`, `M2/artifacts/m2-evaluation-ward/heatmap.png`
   - PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/radar_chart.png`, `M2/artifacts/m2-evaluation-pca-kmeans/heatmap.png`
3. **Báo cáo chuyên đề Markdown:**
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_8_Ho_so_cum_PCA_KMeans.md`

# NHIỆM VỤ 9 — ĐÁNH GIÁ ĐỘ ỔN ĐỊNH THEO THỜI GIAN (TEMPORAL STABILITY)

## Mục đích của Nhiệm vụ 9

Đánh giá mức độ ổn định của cấu trúc phân cụm 2 nhóm (K=2) qua 14 cặp snapshot hàng tháng liên tiếp trong khung thời gian phát triển (Development Window: từ 2023-11-30 đến 2025-01-24).
- **Ổn định nhãn và thông tin:** Đo lường mức độ tương đồng giữa các phân hoạch qua chỉ số Adjusted Rand Index (ARI) và Normalized Mutual Information (NMI).
- **Tính bền vững thành viên:** Đánh giá xác suất cổ phiếu giữ nguyên cụm (Persistence) và tỷ lệ chuyển cụm (Migration) giữa các tháng.
- **Dịch chuyển dòng tiền:** Lập ma trận chuyển dịch cụm (Transition Matrix) 2x2 để xác định hướng luân chuyển giữa Cụm 0 và Cụm 1.
- **Độ trôi tâm cụm (Centroid Drift):** Đo lường mức độ dịch chuyển tọa độ tâm cụm trên 8 đặc trưng gốc qua thời gian.
- **Kiểm soát nhiễu Universe & Reset Gap:** Quản lý số lượng cổ phiếu mới vào hoặc rớt khỏi tập nghiên cứu (Entry/Exit) và kiểm tra cơ chế ngắt chuỗi tại điểm đứt gãy dữ liệu (Gap).
- **Chuẩn hóa đối sánh:** Đảm bảo cả 3 phương án K-Means Baseline, Ward và PCA + K-Means đều xuất ra cùng một bộ 4 Bảng số liệu chuẩn và 2 Biểu đồ chuẩn để so sánh chéo ở Nhiệm vụ 10.

## File code sử dụng trong nhiệm vụ và cách dùng

Nhiệm vụ 9 tuân thủ nguyên tắc cốt lõi của DELTA: **Tầng đánh giá & phân tích chỉ tiêu thụ artifacts đã đóng băng, không chạy lại quy trình huấn luyện mô hình**.

### Các module hệ thống tham chiếu (Backend Modules)
- **`src/delta_t1/evaluation/temporal_metrics.py`** — Module tính toán độ ổn định chuỗi thời gian: Đã được gọi tự động ở Nhiệm vụ 4, 5, 6 để so sánh từng cặp tháng liên tiếp và sinh ra các file artifact temporal. Người làm Nhiệm vụ 9 **không gọi lại file này**.
- **`src/delta_t1/experiments/runner.py`** — Module điều phối thực nghiệm: Đã kiểm soát tính liên tục của các snapshot và tự động ngắt chuỗi (reset gap) khi khoảng cách giữa 2 snapshot vượt quá 1 tháng.
- **`src/delta_t1/clustering/base.py`** — Module cơ sở phân cụm: Đóng vai trò là tài liệu tham chiếu định nghĩa thuật toán khớp nhãn giữa 2 tháng liên tiếp (Hungarian matching).

### Các file code thực thi chính của Nhiệm vụ 9 (Notebooks)
Người thực hiện từng phương án mở và chạy trực tiếp notebook tương ứng của mình trong thư mục `M2/notebooks/`:
- **Phương án 1 (K-Means Baseline):** `M2/notebooks/09_temporal_stability_kmeans.ipynb`
- **Phương án 2 (Ward Hierarchical):** `M2/notebooks/09_temporal_stability_ward.ipynb`
- **Phương án 3 (PCA + K-Means):** `M2/notebooks/09_temporal_stability_pca_kmeans.ipynb`

### Quy trình phối hợp (Workflow)
1. **Bước 1 (Đọc dữ liệu độ ổn định thời gian đầu vào):** Pipeline huấn luyện tự động xuất ra bộ 3 file CSV chuẩn gồm `temporal_stability.csv`, `transition_matrices.csv` và `centroid_drift.csv` vào thư mục artifact evaluation tương ứng, Notebook sẽ đọc trực tiếp từ:
   - K-Means: `M2/artifacts/m2-evaluation-kmeans/`
   - Ward: `M2/artifacts/m2-evaluation-ward/`
   - PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/`
2. **Bước 2 (Nạp dữ liệu vào Notebook):** Notebook đọc trực tiếp 3 file CSV từ các đường dẫn trên bằng lệnh `pd.read_csv()`.
3. **Bước 3 (Tổng hợp số liệu & Trực quan hóa):** Chạy code pandas để xuất ra đúng 4 Bảng số liệu chuẩn và 2 Biểu đồ chuẩn (Đồ thị xu hướng đa panel và Heatmap ma trận chuyển dịch).
4. **Bước 4 (Viết nhận định & Báo cáo):** Soạn thảo nhận định tài chính và giới hạn học thuật vào các ô Markdown trong Notebook, sau đó tổng hợp thành file báo cáo Markdown độc lập:
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_PCA_KMeans.md`

## Quy chuẩn Dữ liệu Đầu vào (Unified Input Contract)

Nhiệm vụ 9 của cả 3 mô hình đều đọc vào **bộ 3 file CSV phẳng** có cấu trúc cột cố định từ thư mục artifact evaluation của từng mô hình:
- K-Means: `M2/artifacts/m2-evaluation-kmeans/`
- Ward: `M2/artifacts/m2-evaluation-ward/`
- PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/`

### Chi tiết cấu trúc 3 file input:
1. **`temporal_stability.csv` (10 cột chuẩn, 14 dòng = 14 cặp tháng liên tiếp):**
   - Cột: `from_date`, `to_date`, `n_common`, `ari`, `nmi`, `persistence_probability`, `migration_rate`, `entered_count`, `exited_count`, `status`.
2. **`transition_matrices.csv` (6 cột chuẩn, 56 dòng = 14 cặp tháng x 4 ô ma trận 2x2):**
   - Cột: `from_date`, `to_date`, `from_cluster`, `to_cluster`, `count`, `rate`.
3. **`centroid_drift.csv` (7 cột chuẩn, 224 dòng = 14 cặp tháng x 2 cụm x 8 feature):**
   - Cột: `from_date`, `to_date`, `aligned_cluster_id`, `feature`, `value_from`, `value_to`, `delta`.

*(Nghiêm cấm để cột dạng chuỗi JSON thô trong file CSV nạp vào notebook).*

## Các phần thực hiện chi tiết trong Notebook & Bảng Output chuẩn

### Phần 9.1 & 9.2 — Đánh giá tương đồng cấu trúc nhãn (ARI & NMI)
- **Mục đích:** Đo lường mức độ trùng khớp của cấu trúc phân cụm giữa tháng t và tháng t+1 trên tập các cổ phiếu chung (giao tập hợp), loại trừ ảnh hưởng của hiện tượng hoán đổi nhãn ngẫu nhiên.
- **Tiêu chuẩn học thuật:** Trị số ARI và NMI càng gần 1 càng chứng tỏ cấu trúc cụm ổn định cao (ngưỡng chấp nhận tốt trong tài chính: ARI > 0.70).

### Phần 9.3 & 9.4 — Tính bền vững thành viên (Persistence & Migration Rate)
- **Mục đích:** Đánh giá xác suất một cổ phiếu tiếp tục ở lại cụm cũ trong tháng tiếp theo (Persistence probability) và tỷ lệ cổ phiếu bị chuyển dịch sang cụm khác (Migration rate = 1 - Persistence).
- **Tiêu chuẩn học thuật:** Cấu trúc phân cụm tốt cần có Persistence cao (> 95%) để hạn chế chi phí đảo danh mục trong thực tế.

**Bảng Output chuẩn 1: Tổng hợp các chỉ số Temporal toàn kỳ (Kích thước 4 dòng x 6 cột):**

| Chỉ số (Metric) | Số cặp quan sát | Trung bình (Mean) | Trung vị (Median) | Nhỏ nhất (Min) | Lớn nhất (Max) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ARI` | 14 | Float | Float | Float | Float |
| `NMI` | 14 | Float | Float | Float | Float |
| `Persistence (%)` | 14 | Float (%) | Float (%) | Float (%) | Float (%) |
| `Migration (%)` | 14 | Float (%) | Float (%) | Float (%) | Float (%) |

### Phần 9.5 — Ma trận chuyển dịch cụm tích lũy (Transition Matrix)
- **Mục đích:** Xác định hướng dịch chuyển của cổ phiếu giữa Cụm 0 và Cụm 1 qua toàn bộ 14 cặp tháng.

**Bảng Output chuẩn 2: Ma trận chuyển dịch tích lũy 2x2 (Kích thước 4 dòng x 5 cột):**

| Từ Cụm (From) | Sang Cụm (To) | Tổng số lượt (Count) | Tổng số cơ sở (Denominator) | Tỷ lệ xác suất (Rate %) |
| :---: | :---: | :---: | :---: | :---: |
| Cụm 0 | Cụm 0 (Giữ nguyên) | Int | Int | Float (%) |
| Cụm 0 | Cụm 1 (Chuyển cụm) | Int | Int | Float (%) |
| Cụm 1 | Cụm 1 (Giữ nguyên) | Int | Int | Float (%) |
| Cụm 1 | Cụm 0 (Chuyển cụm) | Int | Int | Float (%) |

### Phần 9.6 — Độ trôi dạt tâm cụm (Centroid Drift)
- **Mục đích:** Đo lường mức độ biến động tọa độ tâm cụm của từng đặc trưng giữa các tháng để kiểm tra xem bản chất của cụm có bị thay đổi theo thời gian hay không.

**Bảng Output chuẩn 3: Độ lệch tâm tuyệt đối trung bình trên 8 đặc trưng (Kích thước 8 dòng x 3 cột):**

| Đặc trưng | Độ lệch tuyệt đối Cụm 0 (Mean \|Delta\|) | Độ lệch tuyệt đối Cụm 1 (Mean \|Delta\|) |
| :--- | :---: | :---: |
| `liquidity_21` (tỷ VND) | Float | Float |
| `beta_126` | Float | Float |
| `vol_63` | Float | Float |
| `mdd_126` | Float | Float |
| `mom_21` | Float | Float |
| `mom_63` | Float | Float |
| `mom_126` | Float | Float |
| `mom_252` | Float | Float |

### Phần 9.7 — Biến động Universe (Entry / Exit)
- **Mục đích:** Tách bạch rõ các cổ phiếu mới lọt vào Universe (Entry) hoặc bị loại khỏi Universe (Exit) để bảo đảm việc tính toán ARI/NMI chỉ thực hiện trên tập cổ phiếu chung (`n_common`).

**Bảng Output chuẩn 4: Theo dõi biến động Universe qua 14 cặp tháng (Kích thước 14 dòng x 5 cột):**

| Cặp Snapshot (From -> To) | Số mã chung (n_common) | Số mã mới (Entry) | Số mã rớt (Exit) | Tỷ lệ luân chuyển (%) |
| :---: | :---: | :---: | :---: | :---: |
| 2023-11 -> 2023-12 | Int | Int | Int | Float (%) |
| ... (14 dòng) | ... | ... | ... | ... |

### Phần 9.8 — Cơ chế Reset Temporal Chain tại Gap
- **Mục đích:** Kiểm tra và khẳng định nguyên tắc bất biến: **Không tạo liên kết giả qua khoảng dữ liệu bị đứt gãy**.
- **Yêu cầu thực hiện:** In dòng thông báo kiểm tra xác nhận chuỗi 15 snapshot trong Development Window (2023-11-30 đến 2025-01-24) hoàn toàn liên tục từng tháng và chuỗi được ngắt an toàn tại điểm đứt gãy hệ thống tháng 02/2025.

### Phần 9.9 — Trực quan hóa chuẩn hóa (Visualization Contract)

Cả 3 notebook bắt buộc phải sinh ra **cùng 2 biểu đồ chuẩn**:

#### Biểu đồ 1: Biểu đồ đường xu hướng ổn định đa bảng (Multi-panel Temporal Trends)
- Kích thước đồ thị: Gồm 2 đồ thị con xếp dọc (`figsize=(12, 8)`):
  - **Đồ thị trên:** Biến thiên của **ARI** và **NMI** qua 14 cặp tháng. Trục tung từ 0 đến 1. Bắt buộc vẽ 2 đường nét đứt biểu diễn giá trị trung vị của ARI và NMI.
  - **Đồ thị dưới:** Biến thiên của **Persistence** (xác suất giữ cụm) và **Migration** (tỷ lệ chuyển cụm). Có đường nét đứt trung vị.
- Trục hoành hiển thị rõ nhãn của 14 cặp tháng (ví dụ: `11->12`, `12->01`,...).

#### Biểu đồ 2: Heatmap Ma trận chuyển đổi cụm (Transition Matrix Heatmap)
- Ma trận kích thước 2 hàng x 2 cột thể hiện xác suất dịch chuyển giữa Cụm 0 và Cụm 1.
- Bảng màu chuẩn hóa `cmap='Blues'`, bật hiển thị phần trăm trên các ô (`fmt='.2f%'`).

### Phần 9.10 — Nhận định tài chính & Rào chắn học thuật (Stability Rubrics & Academic Invariants)

> **RÀO CHẮN HỌC THUẬT BẮT BUỘC VỀ KỊCH BẢN GIẢ ĐỊNH & RÀNG BUỘC THỰC CHỨNG (EVIDENCE-FIRST RULE):**
> 1. **Các kịch bản chỉ mang tính chất GIẢ ĐỊNH HƯỚNG DẪN (Hypothetical-Only Scenarios):** Các ngưỡng số liệu (>= 80%, < 60%, <= 15%, > 25%...) và tình huống nêu dưới đây thuần túy là bộ khung quy tắc điều kiện (Stability Rubrics) để định hướng tư duy phân tích. AI / người thực hiện **TUYỆT ĐỐI KHÔNG ĐƯỢC sao chép các kịch bản này làm kết luận định kiến**, không tự suy đoán nếu chưa đối chiếu số liệu tính toán thực tế.
> 2. **Ràng buộc số liệu thực tế (Ground-Truth Binding):** Mọi nhận định về độ ổn định bắt buộc phải căn cứ 100% vào số liệu thực tế từ 3 file input CSV (`temporal_stability.csv`, `transition_matrices.csv`, `centroid_drift.csv`), 4 bảng thống kê và 2 biểu đồ (Temporal Trends, Transition Heatmap) được xuất ra trong chính Notebook thực thi. Bắt buộc phải trích dẫn giá trị Mean/Median của ARI, NMI, Persistence, Migration Rate cụ thể.
> 3. **Quy tắc tổng hợp 3 tầng (Three-tier Synthesis):** Phân tích qua 3 tầng: Điểm số ổn định thực tế quan sát được -> Bản chất luân chuyển dòng tiền và hành vi cổ phiếu qua các chu kỳ thị trường -> Tác động trực tiếp đến chi phí giao dịch danh mục và tính khả thi khi vận hành chiến lược ở Milestone M3.

Sau khi hiển thị bảng và biểu đồ, người thực hiện **bắt buộc phải tạo ô Markdown trong Notebook** để trình bày phân tích học thuật theo đúng các nội dung chuẩn hóa dưới đây:

#### 1. Bộ quy tắc phân tích theo điều kiện (Stability Rubrics)

##### Quy tắc đánh giá Quán tính cụm (Persistence Diagnostic Rule):
- **Kịch bản Quán tính cao (Nếu Persistence >= 80%):** Kết luận cấu trúc phân cụm có độ bám dính cao, phân loại cụm có tính bền vững qua các tháng; các mã cổ phiếu không bị xáo trộn ngẫu nhiên.
- **Kịch bản Xáo trộn ngẫu nhiên (Nếu Persistence < 60%):** Cảnh báo hiện tượng xáo trộn ngẫu nhiên (Cluster Churning / Noise), ranh giới giữa các cụm không ổn định và không đủ độ bền làm tín hiệu phân loại cho các chiến lược tiếp theo.

##### Quy tắc đánh giá Chi phí giao dịch tiềm tàng ở M3 (Turnover Impact Rule):
- **Nguyên lý kết nối M2 - M3:** Tỷ lệ nhảy cụm hàng tháng (`Migration Rate = 1 - Persistence`) tương ứng trực tiếp với tỷ lệ tái cơ cấu danh mục tối thiểu (Turnover) mỗi tháng ở giai đoạn Backtest M3.
- **Kịch bản Vận hành an toàn (Nếu Migration <= 15%):** Kết luận mức độ luân chuyển danh mục ở ngưỡng an toàn, chi phí giao dịch và thuế ước tính ở M3 sẽ ở mức thấp, bảo toàn hiệu quả danh mục.
- **Kịch bản Cảnh báo rủi ro bào mòn lợi nhuận (Nếu Migration > 25%):** Bắt buộc phải đưa ra kết luận cảnh báo nguy cơ: "Chi phí giao dịch và thuế ở M3 sẽ bào mòn lợi nhuận thực tế" do danh mục đầu tư phải mua/bán tái cơ cấu quá nhiều mỗi tháng.

##### Quy tắc giải mã cú sốc thị trường (Market Shock Analysis):
- Xác định các tháng có điểm ARI hoặc NMI sụt giảm bất thường (ví dụ ARI < 0.50):
- Đối chiếu với bối cảnh thực tế của thị trường chung VN-Index tại các tháng đó để rút ra kết luận: Khi thị trường đảo chiều hoặc gãy xu hướng mạnh (ví dụ các đợt điều chỉnh sâu trong năm 2024), cấu trúc phân cụm bị biến động ra sao?

#### 2. Giới hạn học thuật bất biến (Academic Invariants)
- **Không phải Dynamic Clustering:** Phân cụm độc lập từng snapshot tháng rồi nối lại đo lường ARI và ma trận chuyển dịch chỉ là phương pháp đánh giá độ bền chuỗi thời gian (Temporal Stability Diagnostic), **tuyệt đối không được gọi đây là thuật toán Dynamic Clustering**.
- **Không tối ưu hóa theo lợi nhuận:** Không được phép dùng chỉ số ổn định thời gian để suy diễn cụm nào sinh lời tốt hơn hay can thiệp vào việc chọn mã đầu tư (thuộc Milestone M3).

---

#### 3. Khung kết luận 3 phần bắt buộc ở Cell cuối Notebook 9:

Cuối Notebook 9, bắt buộc phải có một ô Markdown tổng kết phán quyết học thuật gồm đầy đủ 3 phần:
- **Phần A (Phán quyết độ ổn định):** Đánh giá mức độ ổn định tổng thể của cấu trúc cụm (dựa trên giá trị ARI, NMI trung vị thực chứng).
- **Phần B (Độ bền dòng tiền & Tác động Turnover):** Nhận định về mức độ luân chuyển cổ phiếu (Persistence / Migration thực tế) và cảnh báo rủi ro chi phí giao dịch đối với nhà đầu tư ở M3.
- **Phần C (Handoff cho Nhiệm vụ 10):** Đánh giá xem mô hình có đạt chuẩn về độ bền chuỗi thời gian để bước vào bảng so sánh đối đầu toàn diện ở Nhiệm vụ 10 hay không.

## Kết quả cần đạt & Đường dẫn bàn giao (Deliverables)

Mỗi mô hình khi hoàn thành Nhiệm vụ 9 phải có đầy đủ bộ bàn giao gồm:
1. **Notebook thực thi hoàn chỉnh:**
   - K-Means: `M2/notebooks/09_temporal_stability_kmeans.ipynb`
   - Ward: `M2/notebooks/09_temporal_stability_ward.ipynb`
   - PCA + K-Means: `M2/notebooks/09_temporal_stability_pca_kmeans.ipynb`
2. **Hình ảnh biểu đồ xuất xưởng (lưu vào đúng thư mục evaluation của từng mô hình):**
   - K-Means: `M2/artifacts/m2-evaluation-kmeans/temporal_trends.png`, `M2/artifacts/m2-evaluation-kmeans/transition_heatmap.png`
   - Ward: `M2/artifacts/m2-evaluation-ward/temporal_trends.png`, `M2/artifacts/m2-evaluation-ward/transition_heatmap.png`
   - PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/temporal_trends.png`, `M2/artifacts/m2-evaluation-pca-kmeans/transition_heatmap.png`
3. **Báo cáo chuyên đề Markdown:**
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_PCA_KMeans.md`

# NHIỆM VỤ 10 — SO SÁNH CÁC PHƯƠNG ÁN VÀ CHỌN RA 1 MÔ HÌNH TỐT NHẤT (FINAL METHOD SELECTION)

## Mục đích của Nhiệm vụ 10

Tổng hợp toàn diện kết quả của K-Means Baseline, Ward Hierarchical và PCA + K-Means trên cùng protocol development (15 snapshots, Global K = 2, 8 market features), và **chính thức lựa chọn duy nhất 1 mô hình phân cụm tốt nhất (Final Method)** để đóng băng trước khi mở Final Holdout (Nhiệm vụ 11) và chuyển giao cho Milestone M3.

Hai phương án còn lại không bị loại bỏ mà được lưu trữ đầy đủ trong toàn bộ artifacts và báo cáo dưới vai trò các phương án đối chứng (comparator baselines) để chứng minh tính chặt chẽ của quá trình thực nghiệm.

## Vị trí của bước chọn phương án trong workflow

Bước lựa chọn 1 mô hình tốt nhất diễn ra ngay tại Nhiệm vụ 10 (sau khi đã hoàn tất đánh giá chất lượng, hồ sơ cụm, độ ổn định thời gian) và **bắt buộc phải hoàn tất trước khi mở Nhiệm vụ 11 — Final Holdout**:

Development (15 snapshots: 2023-11-30 đến 2025-01-24)  
↓  
Chạy độc lập: K-Means Baseline / Ward Hierarchical / PCA + K-Means  
↓  
Nhiệm vụ 7 — Đánh giá chất lượng cụm (Cluster Quality: Silhouette, DB, CH, Balance)  
↓  
Nhiệm vụ 8 — Lập và diễn giải hồ sơ cụm (Cluster Profiles: 8 đặc trưng gốc)  
↓  
Nhiệm vụ 9 — Đánh giá độ ổn định chuỗi thời gian (Temporal Stability: ARI, NMI, Migration)  
↓  
Nhiệm vụ 10 — So sánh đối đầu 3 phương án trên 5 tiêu chí học thuật  
↓  
**CHỌN VÀ ĐÓNG BĂNG DUY NHẤT 1 MÔ HÌNH PHÂN CỤM TỐT NHẤT (FINAL METHOD)**  
↓  
Nhiệm vụ 11 — Mở và chạy Final Holdout (CHỈ CHẠY DUY NHẤT 1 MÔ HÌNH ĐÃ CHỌN)  
↓  
Nhiệm vụ 12 — M2 Verify (Audit rào chắn học thuật, không rò rỉ dữ liệu)  
↓  
Nhiệm vụ 13 — Handoff cho Milestone M3 (Portfolio / Backtest)

## Nguyên tắc bất biến khi lựa chọn mô hình (Selection Invariants)

- **Quyết định hoàn toàn trên tập Development:** Việc chọn phương án chỉ được dựa trên kết quả giai đoạn development (15 snapshots). Final holdout tuyệt đối không được mở trước khi final method đã được quyết định và đóng băng thành artifact.
- **Cấm tuyệt đối dùng chỉ số đầu tư:** Không dùng future return, CAGR, Sharpe, Sortino, ROI, Calmar, alpha hoặc kết quả backtest để chọn thuật toán M2 (tuân thủ nghiêm ngặt docs/DELTA_UNIFIED_PROJECT_PLAN.md mục 4.5 và mục 8).
- **Quy tắc một chiều (No Hindsight Bias):** Không được nhìn kết quả holdout rồi quay lại thay đổi phương án hoặc retune siêu tham số.
- **Môi trường so sánh đồng nhất (Ceteris Paribus):** Ba phương án phải được so sánh trên cùng development window (15 snapshots), cùng universe rule (market_experiment_eligible), cùng 8 feature gốc và cùng Global K = 2 đã khóa.

## Phần 10.1 — So sánh chất lượng phân cụm hình học (Cluster Quality Comparison)

So sánh trực diện chất lượng phân tách cấu trúc cụm giữa 3 phương án dựa trên 15 snapshots:
- **Median Silhouette Score:** Chỉ số quyết định chính. Đánh giá độ chặt chẽ nội cụm và khoảng cách phân tách giữa các cụm. Giá trị cao hơn thể hiện ranh giới rõ ràng hơn.
- **Median Davies-Bouldin Index:** Chỉ số xác nhận (tie-breaker). Đánh giá tỷ lệ phân tán nội cụm so với khoảng cách giữa các tâm cụm. Giá trị thấp hơn thể hiện chất lượng tốt hơn.
- **Median Calinski-Harabasz Index:** Chỉ số bổ trợ hình học. Đánh giá tỷ số giữa phương sai liên cụm và phương sai nội cụm.
- **Median Cluster Balance (min_size / max_size):** Kiểm tra mức độ cân bằng phân bổ, phát hiện nguy cơ cô lập nhóm ngoại lai cực đoan.

## Phần 10.2 — So sánh độ ổn định chuỗi thời gian (Temporal Stability Comparison)

So sánh độ bền vững của cấu trúc phân cụm qua 14 cặp tháng liên tiếp:
- **Median Adjusted Rand Index (ARI):** Đánh giá mức độ nhất quán của việc phân nhóm giữa snapshot t và t+1 trên tập cổ phiếu chung.
- **Median Normalized Mutual Information (NMI):** Đo lường lượng thông tin chung được bảo toàn giữa hai snapshot liên tiếp.
- **Median Persistence Probability:** Xác suất cổ phiếu giữ nguyên cụm cũ ở tháng tiếp theo.
- **Median Migration Rate:** Tỷ lệ cổ phiếu nhảy cụm giữa hai tháng liên tiếp (phản ánh trực tiếp chi phí tái cơ cấu danh mục tiềm tàng ở Milestone M3).
- **Centroid Drift:** Đo lường mức độ trôi dạt của tọa độ tâm cụm trong không gian đặc trưng qua thời gian.

## Phần 10.3 — So sánh khả năng diễn giải kinh tế và Sanity Check

- **Sanity Check mức độ cân bằng:** Loại trừ phương án sinh ra cụm suy biến (cụm rác có kích thước nhỏ hơn 5 mã hoặc phân mảnh bất thường).
- **Khả năng diễn giải kinh tế (Economic Interpretability):** Đánh giá hồ sơ tâm cụm của phương án nào phân hóa rõ nét nhất trên 8 đặc trưng động lượng và thanh khoản gốc (Momentum, Volatility, Liquidity, Drawdown, Beta).
- **Đánh đổi của PCA (PCA Trade-off):** Đối với nhánh PCA + K-Means, kiểm tra xem việc giảm chiều có thực sự mang lại cấu trúc cụm vượt trội hay chỉ làm phức tạp hóa pipeline và gây khó khăn khi diễn giải ngược về 8 đặc trưng gốc.

## Phần 10.4 — Ma trận đánh đổi 5 tiêu chí và Dao cạo Occam (Decision Matrix & Occam's Razor)

> **RÀO CHẮN HỌC THUẬT BẮT BUỘC VỀ KỊCH BẢN GIẢ ĐỊNH & RÀNG BUỘC THỰC CHỨNG (EVIDENCE-FIRST RULE):**
> 1. **Các kịch bản chỉ mang tính chất GIẢ ĐỊNH HƯỚNG DẪN (Hypothetical-Only Scenarios):** Các ngưỡng số liệu (ví dụ chênh lệch Silhouette < 0.03, ARI > 0.60...) và các tình huống so sánh dưới đây thuần túy là bộ khung quy tắc điều kiện (Decision Rubrics) để định hướng tư duy phân tích. AI / người thực hiện **TUYỆT ĐỐI KHÔNG ĐƯỢC sao chép các kịch bản này làm kết luận định kiến**, không được khẳng định trước mô hình nào thắng nếu chưa tổng hợp bảng đối đầu từ kết quả thực tế của Nhiệm vụ 7, 8, 9.
> 2. **Ràng buộc số liệu thực tế (Ground-Truth Binding):** Quyết định chọn mô hình bắt buộc phải dựa 100% trên bảng tổng hợp đối đầu từ các file artifact đã xuất xưởng (quality_summary.csv, cluster_profiles.csv, temporal_stability.csv của cả 3 mô hình). Mọi luận điểm lựa chọn hay loại bỏ đều phải trích dẫn số liệu trung vị đối chiếu cụ thể.
> 3. **Quy tắc tổng hợp 3 tầng (Three-tier Synthesis):** Phân tích đối đầu qua 3 tầng: Chênh lệch số liệu toán học giữa 3 phương án -> Ý nghĩa thực tế về mặt cấu trúc và hành vi thị trường -> Quyết định chọn mô hình tối ưu nhất về mặt vận hành và ứng dụng.

Thứ tự ưu tiên quyết định tuân thủ nghiêm ngặt hệ thống 5 tầng theo docs/DELTA_UNIFIED_PROJECT_PLAN.md mục 6.7:

| Thứ tự ưu tiên | Nhóm tiêu chí | Chỉ số thực chứng | Mục đích & Rào chắn học thuật | Vai trò quyết định |
| :---: | :--- | :--- | :--- | :--- |
| **Tầng 1** | **Chất lượng phân cụm** | Median Silhouette Score | Đánh giá độ chặt chẽ nội cụm và khoảng cách phân tách hình học | **Tiêu chí quyết định tiên quyết** |
| **Tầng 2** | **Xác nhận chất lượng** | Median Davies-Bouldin | Giải quyết trường hợp điểm Silhouette tương đương (Tie-breaker) | **Tiêu chí xác nhận thứ hai** |
| **Tầng 3** | **Kiểm tra suy biến** | Min Cluster Size, Cluster Balance | Loại trừ mô hình có cụm suy biến, cô lập quá mức (< 5 mã) | **Sanity check bắt buộc** |
| **Tầng 4** | **Độ ổn định chuỗi thời gian** | Median ARI, Median Migration Rate | Đánh giá độ bền cấu trúc và chi phí tái cơ cấu danh mục ở M3 | **Tiêu chí kiểm tra độ bền** |
| **Tầng 5** | **Dao cạo Occam (Occam's Razor)** | Độ phức tạp pipeline, tính tái lập | Ưu tiên mô hình đơn giản hơn nếu chất lượng toán học tương đương | **Nguyên lý phán quyết cuối cùng** |

### Nguyên lý Dao cạo Occam (Occam's Razor Principle):
- **Quy tắc thực thi:** Nếu sự chênh lệch về Median Silhouette giữa mô hình đơn giản (K-Means Baseline) và mô hình phức tạp hơn (Ward hoặc PCA + K-Means) là không đáng kể (chênh lệch tuyệt đối nhỏ hơn 0.03), thì mô hình đơn giản hơn, dễ tái lập hơn và giải thích trực tiếp trên dữ liệu gốc bắt buộc phải được ưu tiên lựa chọn.
- **Rào chắn chống phức tạp hóa:** Không chấp nhận đưa thêm bước chuyển đổi PCA làm méo mó không gian đặc trưng hoặc thuật toán phân cấp Ward nặng về tính toán nếu không chứng minh được sự vượt trội áp đảo và bền vững trên dữ liệu thực tế.

## Phần 10.5 — Quy trình thực thi 5 bước trong Notebook 10

Quy trình thực thi trong notebook `M2/notebooks/10_model_comparison.ipynb` gồm đúng 5 bước tuần tự:

- **Bước 1: Nạp và kiểm định tính toàn vẹn của dữ liệu đầu vào (Input Ingestion & Integrity Check)**
  Nạp 9 file artifacts đã đóng băng từ Nhiệm vụ 7, 8, 9 của cả 3 mô hình:
  - 3 file chất lượng: `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv`, `M2/artifacts/m2-evaluation-ward/quality_summary.csv`, `M2/artifacts/m2-evaluation-pca-kmeans/quality_summary.csv`
  - 3 file hồ sơ cụm: `M2/artifacts/m2-evaluation-kmeans/cluster_profiles.csv`, `M2/artifacts/m2-evaluation-ward/cluster_profiles.csv`, `M2/artifacts/m2-evaluation-pca-kmeans/cluster_profiles.csv`
  - Notebook Nhiệm vụ 10 chuẩn hóa schema của ba file trong bộ nhớ trước khi so sánh: K-Means bỏ hậu tố `_mean`; Ward giữ 8 cột feature; PCA + K-Means giải mã `centroid` JSON. Không sao chép ngược hoặc sửa artifact nguồn trong `m2-task4/5/6-*-v1`.
  - 3 file ổn định thời gian: `M2/artifacts/m2-evaluation-kmeans/temporal_stability.csv`, `M2/artifacts/m2-evaluation-ward/temporal_stability.csv`, `M2/artifacts/m2-evaluation-pca-kmeans/temporal_stability.csv`
  - Bổ sung chỉ đọc để kiểm chứng: ba `diagnostics.csv` của Nhiệm vụ 4/5/6 (lọc `K=2`, tính Std và đối chiếu `quality_summary.csv`) và ba `centroid_drift.csv` trong `m2-evaluation-*` (so sánh Centroid Drift theo Phần 10.2).
  Kiểm tra xác nhận đủ 15 snapshots và 14 cặp tháng cho cả 3 mô hình trước khi tính toán.

- **Bước 2: Tổng hợp các chỉ số thống kê trung tâm (Metrics Aggregation)**
  Tính toán các giá trị thống kê: Median, Mean, Min, Max, Độ lệch chuẩn cho từng chỉ số (Silhouette, Davies-Bouldin, Calinski-Harabasz, Balance, ARI, NMI, Persistence, Migration Rate) của từng mô hình.

- **Bước 3: Lập bảng so sánh đối đầu toàn diện (Comparative Matrix Construction)**
  Tổng hợp thành file bảng dữ liệu chuẩn hóa `M2/artifacts/m2-evaluation/methodology_comparison.csv` gồm đúng 12 cột:
  - `method`: Tên phương án (`KMeans_Baseline`, `Ward_Hierarchical`, `PCA_KMeans`)
  - `global_k`: Giá trị K toàn cục (`2`)
  - `median_silhouette`: Trung vị Silhouette
  - `mean_silhouette`: Trung bình Silhouette
  - `median_davies_bouldin`: Trung vị Davies-Bouldin
  - `median_calinski_harabasz`: Trung vị Calinski-Harabasz
  - `median_cluster_balance`: Trung vị tỷ số cân bằng cụm
  - `median_ari`: Trung vị Adjusted Rand Index
  - `median_nmi`: Trung vị Normalized Mutual Information
  - `median_persistence`: Trung vị xác suất giữ nguyên cụm
  - `median_migration_rate`: Trung vị tỷ lệ chuyển cụm
  - `pipeline_complexity`: Mức độ phức tạp pipeline (`Low`, `Medium`, `High`)

- **Bước 4: Thực thi thuật toán lựa chọn theo 5 tầng tiêu chí (Decision Logic Execution)**
  Áp dụng bộ tiêu chí 5 tầng tại Phần 10.4 để xác định duy nhất 1 mô hình chiến thắng (Winner Method). Đối chiếu chi tiết với Dao cạo Occam để biện luận thuyết phục về việc lựa chọn mô hình chiến thắng và loại bỏ 2 phương án đối chứng.

- **Bước 5: Đóng băng quyết định, lưu trữ trọng số và xuất tài liệu bàn giao (Decision Freeze & Artifact Export)**
  - Xuất file artifact quyết định chuẩn hóa `M2/artifacts/m2-evaluation/final_method_decision.json`.
  - Sao chép các tệp mô hình đã huấn luyện của phương án chiến thắng vào thư mục mô hình chính thức `M2/models/final_selected_model/`.
  - Xuất biểu đồ so sánh chuẩn hóa `M2/artifacts/m2-evaluation/model_comparison_radar_or_bar.png` (Biểu đồ cột nhóm so sánh đa tiêu chí giữa 3 mô hình).
  - Duy trì báo cáo chuyên đề `M2/reports/Bao_cao_M2_Nhiem_vu_10_So_sanh_va_Chon_mo_hinh_tot_nhat.md` độc lập với notebook; notebook không tự xuất hoặc ghi đè file này.

## Phần 10.6 — Cấu trúc chuẩn hóa của file `final_method_decision.json`

File artifact quyết định bắt buộc phải tuân thủ đúng cấu trúc JSON gồm 8 trường thông tin sau:

```json
{
  "decision_timestamp": "ISO-8601 Timestamp",
  "selected_method": "Tên mô hình chiến thắng (ví dụ: KMeans_Baseline)",
  "comparator_methods": ["Tên mô hình đối chứng 1", "Tên mô hình đối chứng 2"],
  "global_k": 2,
  "decision_criteria_rank": [
    "1. Median Silhouette (Primary)",
    "2. Median Davies-Bouldin (Confirmation / Tie-breaker)",
    "3. Cluster Balance (Sanity check)",
    "4. Temporal Stability (ARI / Migration)",
    "5. Occam's Razor (Simplicity & direct interpretability)"
  ],
  "selection_rationale": "Tóm tắt 3 luận điểm cốt lõi lựa chọn mô hình chiến thắng",
  "rejection_rationales": {
    "Mo_hinh_doi_chung_1": "Lý do loại bỏ dựa trên số liệu thực chứng",
    "Mo_hinh_doi_chung_2": "Lý do loại bỏ dựa trên số liệu thực chứng"
  },
  "frozen_artifacts_manifest": {
    "comparison_table": "M2/artifacts/m2-evaluation/methodology_comparison.csv",
    "selected_model_directory": "M2/models/final_selected_model/"
  },
  "status": "FROZEN_FOR_HOLDOUT"
}
```

## Phần 10.7 — Khung biện luận 3 luận điểm bắt buộc trong Báo cáo Quyết định

Báo cáo `M2/reports/Bao_cao_M2_Nhiem_vu_10_So_sanh_va_Chon_mo_hinh_tot_nhat.md` bắt buộc phải có đủ 3 luận điểm phản biện chính:
- **Luận điểm 1 — Vì sao mô hình chiến thắng được lựa chọn?** Nêu rõ các bằng chứng thực nghiệm về sự cân bằng tối ưu giữa chất lượng phân tách hình học, độ bền vững chuỗi thời gian, hồ sơ cụm dễ diễn giải và tính khả thi khi vận hành danh mục ở Milestone M3.
- **Luận điểm 2 — Vì sao hai mô hình đối chứng bị loại bỏ? (Rejection Analysis):** Phân tích rõ các nhược điểm cố hữu của hai phương án đối chứng dựa trên số liệu thực tế (ví dụ: tính phân cực cực đoan, thiếu cơ chế gán nhãn cho quan sát mới, hoặc việc giảm chiều làm phức tạp hóa pipeline mà không mang lại sự vượt trội về Silhouette).
- **Luận điểm 3 — Cam kết đóng băng phương pháp luận (Methodology Freeze Commitment):** Tuyên bố chính thức đóng băng phương pháp luận, khẳng định việc lựa chọn hoàn tất 100% trước khi mở tập dữ liệu ngoài mẫu, cam kết tuân thủ nguyên tắc kiểm định một chiều ở Nhiệm vụ 11.

## Kết quả cần đạt & Đường dẫn bàn giao của Nhiệm vụ 10

1. **Notebook thực thi hoàn chỉnh:**
   - `M2/notebooks/10_model_comparison.ipynb`
2. **Thư mục lưu trữ mô hình chiến thắng:**
   - `M2/models/final_selected_model/`
3. **Artifacts thực nghiệm chuẩn hóa:**
   - `M2/artifacts/m2-evaluation/methodology_comparison.csv`
   - `M2/artifacts/m2-evaluation/final_method_decision.json`
   - `M2/artifacts/m2-evaluation/model_comparison_radar_or_bar.png`
4. **Báo cáo chuyên đề Markdown độc lập:**
   - `M2/reports/Bao_cao_M2_Nhiem_vu_10_So_sanh_va_Chon_mo_hinh_tot_nhat.md`

---

# NHIỆM VỤ 11 — MỞ VÀ CHẠY FINAL HOLDOUT (OUT-OF-SAMPLE VALIDATION)

## Mục đích của Nhiệm vụ 11

Kiểm định độc lập năng lực tổng quát hóa ngoài mẫu (out-of-sample generalization) của **DUY NHẤT 1 MÔ HÌNH PHÂN CỤM TỐT NHẤT** đã được lựa chọn và đóng băng tại Nhiệm vụ 10 trên giai đoạn dữ liệu tương lai năm 2026.

Final Holdout là bài kiểm tra một chiều nghiêm ngặt nhằm xác nhận xem cấu trúc phân cụm có bền vững trước sự dịch chuyển của thời gian hay không. **Tuyệt đối không dùng Final Holdout để tìm mô hình tốt hơn, không so sánh lại các mô hình đã bị loại, và không dùng để điều chỉnh lại bất kỳ siêu tham số nào**.

Development (15 snapshots: 2023-11-30 đến 2025-01-24)  
→ Xây dựng, so sánh đối đầu và CHỌN XONG DUY NHẤT 1 MÔ HÌNH  
  
Final Holdout (7 snapshots: 2026-02-27 đến 2026-08-28)  
→ KIỂM ĐỊNH MỘT CHIỀU DUY NHẤT MÔ HÌNH ĐÃ ĐÓNG BĂNG

## Rào chắn học thuật bất biến cho Final Holdout (Strict Holdout Invariants)

- **Cổng kiểm soát đóng băng (Freeze Gate Rule):** Final Holdout chỉ được phép kích hoạt sau khi file `M2/artifacts/m2-evaluation/final_method_decision.json` đã tồn tại với trạng thái `status: "FROZEN_FOR_HOLDOUT"`.
- **Chỉ chạy duy nhất 1 mô hình (Single Model Execution):** Tuyệt đối không chạy lại 3 phương án trên Holdout. Hai phương án đã bị loại ở Nhiệm vụ 10 giữ nguyên vai trò đối chứng ở Development và không tham gia vào Holdout.
- **Không thử lại K:** Giữ nguyên Global K = 2 đã đóng băng. Tuyệt đối không quét lại K = 2..8 trên dữ liệu Holdout.
- **Giữ nguyên Preprocessing:** Áp dụng đúng công thức Robust Scaling per-snapshot: `x_scaled = (x - Median) / IQR`. Không dùng scaler của Development áp cho Holdout, không đổi sang Z-score.
- **Kiểm định một chiều (Strict One-Way Validation):** Dù kết quả Holdout cao hay thấp, giữ nguyên trung thực 100% số liệu. Không quay lại thay đổi feature set, không thay đổi K, không đổi thuật toán. Mọi suy giảm chất lượng đều được ghi nhận vào phần Giới hạn học thuật (Limitations).

## Phần 11.1 — Khung thời gian Holdout và 7 Snapshots thực tế

Giai đoạn Final Holdout gồm đúng 7 snapshots hàng tháng trong năm 2026 đã được quy định tại docs/DELTA_UNIFIED_PROJECT_PLAN.md mục 6.2:

1. Snapshot 1: `2026-02-27`
2. Snapshot 2: `2026-03-31`
3. Snapshot 3: `2026-04-29`
4. Snapshot 4: `2026-05-29`
5. Snapshot 5: `2026-06-30`
6. Snapshot 6: `2026-07-31`
7. Snapshot 7: `2026-08-28`

## Phần 11.2 — Lọc Universe và Điều kiện đủ của từng Snapshot Holdout

Tại mỗi snapshot `t` trong 7 tháng Holdout:
- Áp dụng nguyên tắc Universe theo từng thời điểm: `market_experiment_eligible(t) = market_feature_ready_v2(t)`.
- Tuyệt đối không lấy danh sách mã của snapshot cuối cùng (08/2026) áp đặt ngược lại cho các tháng trước đó.
- **Ngưỡng kiểm định số lượng mã (Sanity Threshold):** Yêu cầu số mã đủ điều kiện `n_eligible >= 120`. Nếu một snapshot có số mã nhỏ hơn 120, snapshot đó phải bị bỏ qua (skip) kèm theo lý do ghi nhận rõ ràng trong manifest, không được gộp ngày hoặc nội suy dữ liệu giả.

## Phần 11.3 — Chuẩn hóa Robust Scaling độc lập theo từng Snapshot Holdout

Mỗi snapshot Holdout được xem là một phiên giao dịch thực tế độc lập:
- Tính toán giá trị Median và IQR của 8 đặc trưng thị trường trên chính tập cổ phiếu đủ điều kiện của snapshot đó.
- Áp dụng công thức: `x_scaled = (x - Median) / IQR`.
- Lưu trữ các thông số chuẩn hóa (Median, IQR) của từng snapshot vào artifact để phục vụ việc kiểm toán tính tái lập tại Nhiệm vụ 12.

## Phần 11.4 — Thực thi duy nhất mô hình chiến thắng trên 7 Snapshots Holdout

- Nạp cấu hình và thuật toán đã được đóng băng từ `M2/artifacts/m2-evaluation/final_method_decision.json`.
- Thực hiện phân cụm trên không gian đặc trưng đã chuẩn hóa với đúng Global K = 2.
- Gán nhãn cụm cho từng mã cổ phiếu đủ điều kiện tại mỗi snapshot.
- Tính toán tọa độ tâm cụm thực tế và biến đổi ngược về thang đo 8 đặc trưng gốc để phục vụ phân tích hồ sơ cụm.

## Phần 11.5 — Đánh giá chất lượng phân cụm trên Holdout (Holdout Cluster Quality)

Tính toán các chỉ số chất lượng phân cụm hình học trên từng snapshot trong số 7 snapshots Holdout:
- Silhouette Score
- Davies-Bouldin Index
- Calinski-Harabasz Index
- Cluster Balance (min_size / max_size) và quy mô từng cụm

Tổng hợp thành bảng thống kê chất lượng Holdout `M2/artifacts/m2-final-holdout-v1/diagnostics.jsonl`.

## Phần 11.6 — Đánh giá độ ổn định thời gian và Quy tắc ngắt chuỗi tại Gap (Temporal Stability & Gap Reset)

Đo lường độ ổn định thời gian giữa 6 cặp snapshot liên tiếp trong giai đoạn Holdout:
1. Cặp 1: `2026-02-27 -> 2026-03-31`
2. Cặp 2: `2026-03-31 -> 2026-04-29`
3. Cặp 3: `2026-04-29 -> 2026-05-29`
4. Cặp 4: `2026-05-29 -> 2026-06-30`
5. Cặp 5: `2026-06-30 -> 2026-07-31`
6. Cặp 6: `2026-07-31 -> 2026-08-28`

Với mỗi cặp tháng liên tiếp, tính toán:
- Số lượng mã chung (n_common), số mã mới vào (Entry), số mã rớt ra (Exit).
- Adjusted Rand Index (ARI) và Normalized Mutual Information (NMI).
- Xác suất giữ cụm (Persistence) và Tỷ lệ luân chuyển cụm (Migration Rate).
- Ma trận chuyển đổi cụm (Transition Matrix).

> **QUY TẮC BẤT BIẾN VỀ NGẮT CHUỖI TẠI KHOẢNG ĐỨT GÃY (GAP RESET RULE):**  
> Tuyệt đối không tính toán chỉ số ổn định thời gian nối giữa snapshot cuối của Development (2025-01-24) và snapshot đầu của Holdout (2026-02-27). Khoảng đứt gãy hệ thống kéo dài từ 02/2025 đến 01/2026 là gián đoạn cấu trúc dữ liệu thực tế; việc cố tình nối chuỗi qua khoảng cách này sẽ tạo ra các chỉ số giả mạo. Chuỗi ổn định thời gian bắt buộc phải được reset hoàn toàn khi bắt đầu Holdout.

## Phần 11.7 — Bộ quy tắc đo lường Khoảng cách suy thoái ngoài mẫu (Generalization Gap Rubrics)

> **RÀO CHẮN HỌC THUẬT BẮT BUỘC VỀ KỊCH BẢN GIẢ ĐỊNH & RÀNG BUỘC THỰC CHỨNG (EVIDENCE-FIRST RULE):**
> 1. **Các kịch bản chỉ mang tính chất GIẢ ĐỊNH HƯỚNG DẪN (Hypothetical-Only Scenarios):** Các mức ngưỡng chênh lệch suy thoái (Delta_Silhouette >= -0.05, suy giảm > -0.20...) dưới đây thuần túy là bộ khung quy tắc chẩn đoán (Diagnostic Rubrics) để định hướng tư duy đánh giá. AI / người thực hiện **TUYỆT ĐỐI KHÔNG ĐƯỢC sao chép các kịch bản này làm kết luận định kiến**, không tự đoán trước kết quả Holdout nếu chưa thực thi đầy đủ trên 7 snapshot năm 2026.
> 2. **Ràng buộc số liệu thực tế (Ground-Truth Binding):** Mọi nhận định về năng lực tổng quát hóa bắt buộc phải căn cứ 100% vào khoảng cách suy thoái thực tế giữa tập Development (15 tháng) và tập Holdout (7 tháng) thu được từ artifacts xuất xưởng.
> 3. **Kỷ luật nghiên cứu một chiều tuyệt đối (Strict One-Way Validation Invariant):** Holdout là bài kiểm tra một chiều duy nhất. Tuyệt đối không được nhìn kết quả Holdout rồi quay lại thay đổi mô hình hay can thiệp vào các tham số đã đóng băng.

So sánh trực diện chất lượng phân cụm giữa hai tập dữ liệu theo công thức:  
`Delta_Silhouette = Median_Silhouette_Holdout - Median_Silhouette_Development`

- **Kịch bản A (Thích ứng xuất sắc — Nếu Delta_Silhouette >= -0.05):**  
  -> Kết luận: Mô hình có năng lực tổng quát hóa ngoài mẫu xuất sắc. Cấu trúc cụm không bị hiện tượng quá khớp (overfitting) trên tập phát triển; ranh giới phân tách toán học được bảo toàn ổn định trong tương lai.
- **Kịch bản B (Suy giảm tự nhiên chấp nhận được — Nếu Delta_Silhouette suy giảm từ -0.05 đến -0.15):**  
  -> Kết luận: Mô hình có độ suy giảm trong giới hạn chấp nhận được của thị trường tài chính, phản ánh sự biến động tự nhiên của môi trường vĩ mô năm 2026; cụm vẫn giữ được cấu trúc phân tách cơ bản.
- **Kịch bản C (Dịch chuyển chế độ thị trường mạnh — Nếu Delta_Silhouette suy giảm > -0.20 hoặc Silhouette < 0.50):**  
  -> Kết luận: Phải ghi nhận trung thực hiện tượng dịch chuyển chế độ thị trường (Macro Regime Shift). Không gian đặc trưng động lượng năm 2026 đã biến đổi mạnh so với giai đoạn 2023-2024; đây là bằng chứng thực nghiệm quan trọng làm ranh giới rủi ro cần bàn giao cho Milestone M3.

## Phần 11.8 — Kiểm tra tính bền vững của Hồ sơ cụm (Profile Consistency Test)

So sánh hồ sơ 8 đặc trưng gốc của các cụm giữa Development và Holdout:
- Kiểm tra xem Cụm dẫn dắt (Leader Cluster) trên dữ liệu mới năm 2026 có còn duy trì bản chất "Động lượng vượt trội, Thanh khoản lớn" hay không.
- Kiểm tra xem Cụm bám sau (Laggard Cluster) có duy trì đặc tính "Động lượng yếu, Biến động cao hoặc Thanh khoản thấp" hay không.
- Nếu xuất hiện sự đảo chiều hồ sơ cụm, tiến hành đối chiếu với bối cảnh xu hướng chung của chỉ số VN-Index trong năm 2026 để giải thích nguyên nhân kinh tế và ghi nhận vào báo cáo.

## Phần 11.9 — Quy trình thực thi 7 bước trong Notebook 11

Quy trình thực thi trong notebook `M2/notebooks/11_final_holdout_execution.ipynb` gồm đúng 7 bước:

- **Bước 1: Kiểm định Cổng đóng băng (Holdout Gate Verification)**  
  Nạp file `M2/artifacts/m2-evaluation/final_method_decision.json`, kiểm tra điều kiện tiên quyết `status == "FROZEN_FOR_HOLDOUT"`. Nếu file không tồn tại hoặc trạng thái chưa đóng băng, lập tức dừng chương trình (fail-closed). Trích xuất tên mô hình chiến thắng và Global K = 2.
- **Bước 2: Nạp dữ liệu 7 Snapshots Holdout từ Feature Store**  
  Nạp 8 đặc trưng thị trường của 7 snapshots năm 2026 từ kho dữ liệu chuẩn hóa `data/canonical/market/` (phiên bản Feature Store `1.6.0`).
- **Bước 3: Lọc Universe và Kiểm định Ngưỡng mã tối thiểu**  
  Lọc universe theo snapshot (`market_experiment_eligible`), kiểm tra điều kiện `n_eligible >= 120` cho từng tháng trong 7 tháng.
- **Bước 4: Chuẩn hóa Robust Scaling độc lập từng Snapshot**  
  Tính Median và IQR riêng biệt cho từng snapshot và thực hiện chuẩn hóa: `(x - Median) / IQR`.
- **Bước 5: Thực thi phân cụm mô hình chiến thắng trên Holdout**  
  Thực hiện fit/predict mô hình chiến thắng đã chọn từ Nhiệm vụ 10 với Global K = 2. Xuất nhãn cụm ra `assignments.jsonl` và tâm cụm gốc ra `profiles.jsonl`.
- **Bước 6: Đo lường Chất lượng, Độ ổn định và Khoảng cách suy thoái**  
  - Tính Silhouette, Davies-Bouldin, Calinski-Harabasz, Balance cho 7 snapshots, lưu vào `diagnostics.jsonl`.
  - Tính ARI, NMI, Persistence, Migration Rate cho 6 cặp tháng liên tiếp (áp dụng nghiêm ngặt Gap Reset Rule), lưu vào `temporal_stability.csv`.
  - Tính toán `Delta_Silhouette` và lập bảng khoảng cách suy thoái `holdout_generalization_gap.csv`.
- **Bước 7: Trực quan hóa, Tạo Manifest kiểm toán và Soạn thảo Báo cáo**  
  - Vẽ biểu đồ quỹ đạo chất lượng `M2/artifacts/m2-final-holdout-v1/holdout_vs_dev_trajectory.png`.
  - Tạo file kiểm toán `M2/artifacts/m2-final-holdout-v1/manifest.json` ghi nhận mã băm sha256 của tất cả các artifacts.
  - Soạn thảo báo cáo chuyên đề `M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`.

## Phần 11.10 — Trực quan hóa chuẩn hóa: Biểu đồ Quỹ đạo Development vs Holdout

Notebook 11 bắt buộc phải xuất biểu đồ `M2/artifacts/m2-final-holdout-v1/holdout_vs_dev_trajectory.png`:
- Kích thước đồ thị: `figsize=(14, 6)`.
- Trục tung: Điểm số Silhouette (từ 0.0 đến 1.0).
- Trục hoành: Toàn bộ 22 mốc thời gian (15 mốc Development từ 2023-11-30 đến 2025-01-24, và 7 mốc Holdout từ 2026-02-27 đến 2026-08-28).
- **Đường phân cách khoảng đứt gãy (Systemic Gap Boundary):** Bắt buộc phải có một đường thẳng đứng nét đứt màu đỏ (`linestyle='--'`, `color='red'`) phân tách rõ rệt giữa Development (tháng 01/2025) và Holdout (tháng 02/2026), có chú thích rõ vùng "Systemic Data Gap (2025-02 to 2026-01) — Temporal Chain Reset".
- Thể hiện hai đường trung vị nằm ngang riêng biệt cho tập Development và tập Holdout để làm nổi bật khoảng cách suy thoái trực quan.

## Kết quả cần đạt & Đường dẫn bàn giao của Nhiệm vụ 11

1. **Notebook thực thi hoàn chỉnh:**
   - `M2/notebooks/11_final_holdout_execution.ipynb`
2. **Thư mục lưu trữ mô hình và đối tượng Holdout:**
   - `M2/models/holdout/`
3. **Artifacts thực nghiệm chuẩn hóa (Thư mục `M2/artifacts/m2-final-holdout-v1/`):**
   - `M2/artifacts/m2-final-holdout-v1/assignments.jsonl` (gán nhãn cụm cho từng mã qua 7 snapshots holdout)
   - `M2/artifacts/m2-final-holdout-v1/profiles.jsonl` (hồ sơ tâm cụm trên 8 đặc trưng gốc)
   - `M2/artifacts/m2-final-holdout-v1/diagnostics.jsonl` (chỉ số chất lượng Silhouette, DB, CH, Balance theo từng snapshot)
   - `M2/artifacts/m2-final-holdout-v1/temporal_stability.csv` (chỉ số ARI, NMI, Persistence, Migration giữa 6 cặp tháng holdout)
   - `M2/artifacts/m2-final-holdout-v1/holdout_generalization_gap.csv` (bảng đối chiếu suy thoái chất lượng giữa Dev và Holdout)
   - `M2/artifacts/m2-final-holdout-v1/holdout_vs_dev_trajectory.png` (biểu đồ quỹ đạo phân cụm xuyên suốt 22 snapshots)
   - `M2/artifacts/m2-final-holdout-v1/manifest.json` (bằng chứng kiểm toán và mã băm sha256)
4. **Báo cáo chuyên đề Markdown:**
   - `M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`

# NHIỆM VỤ 12 — M2 VERIFY: KIỂM TOÁN TÍNH TOÀN VẸN VÀ RÀO CHẮN HỌC THUẬT

## Mục đích của Nhiệm vụ 12

Thực hiện kiểm toán toàn diện và độc lập toàn bộ quy trình thực nghiệm Milestone M2 trước khi chính thức bàn giao kết quả cho Milestone M3.

Nhiệm vụ 12 đảm bảo rằng mọi kết quả nghiên cứu đều tuân thủ 100% các nguyên tắc bất biến quy định tại docs/DELTA_UNIFIED_PROJECT_PLAN.md Mục 4 và Mục 9, bao gồm: tính đóng băng của cấu hình, không rò rỉ dữ liệu tương lai hay holdout, ngắt chuỗi an toàn tại khoảng đứt gãy hệ thống, tính bất biến của artifacts, và khả năng tái lập xác định (deterministic reproducibility).

## Bộ 8 Tiêu chí Kiểm toán Bắt buộc (8-point Audit Checklist)

Quá trình kiểm toán trong Nhiệm vụ 12 phải tự động kiểm tra và xuất phán quyết (PASS/FAIL) trên đúng 8 tiêu chí cốt lõi:

| Tiêu chí | Nội dung kiểm toán | Yêu cầu đối chiếu & Rào chắn học thuật | Phán quyết |
| :---: | :--- | :--- | :---: |
| **Audit 1** | **Config & Input Lineage** | Đối chiếu mã băm SHA-256 của tập dữ liệu đặc trưng Feature Store phiên bản 1.6.0. Đảm bảo dữ liệu đầu vào C8 là bất biến (immutable), không bị chỉnh sửa tại chỗ (no in-place mutation). | **PASS / FAIL** |
| **Audit 2** | **Global K Selection Integrity** | Xác thực Global K = 2 được lựa chọn hoàn toàn từ 15 snapshot Development thông qua tiêu chí Median Silhouette cao nhất và Median DB tie-breaker. Xác nhận không nhìn trước Holdout và không dùng Sharpe/lợi nhuận để chọn K. | **PASS / FAIL** |
| **Audit 3** | **Zero Future / Holdout Leakage** | Kiểm tra ranh giới thời gian nghiêm ngặt giữa Development (2023-11-30 đến 2025-01-24) và Holdout (2026-02-27 đến 2026-08-28). Đảm bảo không có bất kỳ quan sát hay scaler nào của Holdout bị rò rỉ ngược về Development. | **PASS / FAIL** |
| **Audit 4** | **Systemic Gap Reset Verification** | Xác thực chuỗi ổn định thời gian đã bị ngắt tuyệt đối tại khoảng đứt gãy hệ thống (tháng 02/2025 đến tháng 01/2026). Xác nhận phiên 2025-02-03 có 0 mã equity và tuyệt đối không tồn tại cặp nối thời gian giữa 2025-01-24 và 2026-02-27. | **PASS / FAIL** |
| **Audit 5** | **Per-Snapshot Universe Integrity** | Kiểm tra tính đủ điều kiện theo từng thời điểm: market_experiment_eligible(t) = market_feature_ready_v2(t) và n_eligible >= 120 cho toàn bộ 22 snapshots. Đảm bảo không lấy 905 mã terminal áp ngược lịch sử (no survivorship hindsight). | **PASS / FAIL** |
| **Audit 6** | **Strict Single Winning Model Holdout** | Xác nhận trên Holdout chỉ chạy duy nhất 1 mô hình đã được đóng băng trong final_method_decision.json. Hai phương án đối chứng còn lại tuyệt đối không được thực thi trên Holdout. | **PASS / FAIL** |
| **Audit 7** | **No Portfolio Metrics in Selection** | Quét toàn bộ mã nguồn và artifacts của M2, xác nhận không có bất kỳ lệnh tính toán Sharpe, CAGR, ROI, Calmar, Alpha nào tham gia vào việc chọn K hay chọn mô hình phân cụm. | **PASS / FAIL** |
| **Audit 8** | **Deterministic Reproducibility** | Chạy lại kiểm thử tự động trên bộ dữ liệu kiểm định cố định (bounded fixtures trong tests/). Xác nhận nhãn phân cụm và các chỉ số hình học đạt độ trùng khớp 100% giữa các lần chạy. | **PASS / FAIL** |

## Phần 12.1 — Kiểm tra tính toàn vẹn của cấu hình và nguồn dữ liệu (Config & Input Lineage)
- Nạp file cấu hình chuẩn hóa `configs/experiments/m2_market_only_v1.json` và manifest của Feature Store `1.6.0`.
- Tính toán mã băm SHA-256 của các tệp dữ liệu đặc trưng đầu vào trong `data/canonical/market/`.
- Xác thực tính bất biến: Đảm bảo không có bất kỳ tập tin gốc nào từ Milestone M1 (C8) bị thay đổi nội dung hoặc thay đổi cấu trúc bảng.

## Phần 12.2 — Kiểm toán quá trình lựa chọn Global K (Global K Audit)
- Kiểm tra lại toàn bộ ma trận chẩn đoán `diagnostics.csv` (105 hàng tương ứng 15 snapshots x 7 giá trị K từ 2 đến 8).
- Tái tính toán giá trị Median Silhouette và Median Davies-Bouldin cho từng K.
- Đối chiếu với biên bản quyết định K tại Nhiệm vụ 3 để xác nhận Global K = 2 được chọn đúng theo thứ tự ưu tiên hình học, hoàn toàn không bị chi phối bởi bất kỳ yếu tố chủ quan nào.

## Phần 12.3 — Kiểm toán rò rỉ dữ liệu ngoài mẫu (Zero Leakage Audit)
- Kiểm tra tính độc lập của việc chuẩn hóa: Từng snapshot trong số 15 tháng Development và 7 tháng Holdout phải được fit RobustScaler riêng biệt bằng chính Median và IQR của tháng đó.
- Kiểm tra nhãn thời gian của tất cả các vector đặc trưng: Tuyệt đối không có dữ liệu sau ngày 24/01/2025 xuất hiện trong các artifacts của Nhiệm vụ 4, 5, 6, 7, 8, 9, 10.
- Xác nhận file quyết định `final_method_decision.json` có dấu thời gian hoàn thành trước khi dữ liệu Holdout năm 2026 được nạp vào bộ nhớ.

## Phần 12.4 — Kiểm toán việc ngắt chuỗi tại khoảng đứt gãy hệ thống (Systemic Gap Reset Audit)
- Kiểm tra toàn bộ danh sách 14 cặp tháng trong Development và 6 cặp tháng trong Holdout:
  - Chuỗi Development kết thúc tại cặp: `2024-12-31 -> 2025-01-24`.
  - Chuỗi Holdout bắt đầu tại cặp: `2026-02-27 -> 2026-03-31`.
- Quét các bảng `temporal_stability.csv`, `transition_matrices.csv`, `centroid_drift.csv` để khẳng định không tồn tại bất kỳ dòng dữ liệu nào ghi nhận cặp `2025-01-24 -> 2026-02-27`. Xác nhận cơ chế Gap Reset hoạt động chính xác 100%.

## Phần 12.5 — Kiểm toán tính tái lập xác định (Deterministic Reproducibility Audit)
- Tái thực thi thuật toán phân cụm trên tập fixture cố định với cùng tham số `random_state`.
- So sánh nhãn cụm (cluster assignments) và tọa độ tâm cụm (centroids) giữa lần chạy kiểm toán và kết quả đã lưu trong artifact.
- Yêu cầu sai số tuyệt đối bằng 0 (Zero Tolerance Difference) đối với các phép gán nhãn cụm.

## Phần 12.6 — Quy trình thực thi 5 bước trong Notebook 12

Quy trình thực thi trong notebook `M2/notebooks/12_m2_verification_audit.ipynb` gồm đúng 5 bước tuần tự:

- **Bước 1: Nạp Manifest và Khởi tạo Môi trường Kiểm toán**  
  Nạp toàn bộ manifests từ các thư mục artifacts của Nhiệm vụ 1 đến 11, khởi tạo danh mục kiểm toán 8 tiêu chí.
- **Bước 2: Quét mã nguồn và Kiểm định Dữ liệu Tự động**  
  Chạy các hàm kiểm tra tự động đối với 8 tiêu chí kiểm toán; ghi nhận chi tiết giá trị kỳ vọng (expected) và giá trị thực tế quan sát được (observed).
- **Bước 3: Chạy Kiểm thử Hồi quy Tái lập (Regression & Reproducibility Test)**  
  Gọi bộ test kiểm định `pytest tests/unit/clustering/` và `pytest tests/integration/` để xác nhận toàn bộ hệ thống vượt qua các ràng buộc kỹ thuật.
- **Bước 4: Xuất Bảng Bằng chứng Kiểm toán (Audit Evidence Construction)**  
  Tổng hợp kết quả kiểm tra từng snapshot và từng module vào bảng `M2/artifacts/m2-verify-v1/audit_evidence.csv`.
- **Bước 5: Ban hành Biên bản Phán quyết Kiểm toán và Báo cáo**  
  Xuất file phán quyết chính thức `M2/artifacts/m2-verify-v1/verification_summary.json` và lập báo cáo chi tiết `M2/reports/Bao_cao_M2_Nhiem_vu_12_Verify_Audit.md`.

## Phần 12.7 — Cấu trúc chuẩn hóa của file `verification_summary.json`

File phán quyết kiểm toán bắt buộc phải tuân thủ đúng cấu trúc JSON sau:

```json
{
  "audit_timestamp": "ISO-8601 Timestamp",
  "pipeline_milestone": "M2_CLUSTERING_RESEARCH",
  "overall_verdict": "VERIFIED_PASS",
  "checkpoints": {
    "audit_1_config_and_input_lineage": { "status": "PASS", "details": "Feature store 1.6.0 immutable checksum verified" },
    "audit_2_global_k_selection": { "status": "PASS", "details": "Global K=2 strictly frozen via median silhouette on dev window" },
    "audit_3_zero_leakage": { "status": "PASS", "details": "Strict separation between Dev (15 snapshots) and Holdout (7 snapshots)" },
    "audit_4_gap_reset": { "status": "PASS", "details": "Temporal chain safely reset across systemic gap 2025-02..2026-01" },
    "audit_5_universe_eligibility": { "status": "PASS", "details": "Per-snapshot eligibility enforced, all snapshots have n_eligible >= 120" },
    "audit_6_single_model_holdout": { "status": "PASS", "details": "Only winning method evaluated on holdout" },
    "audit_7_no_portfolio_metrics": { "status": "PASS", "details": "Zero portfolio return/Sharpe used in clustering decisions" },
    "audit_8_reproducibility": { "status": "PASS", "details": "Deterministic rerun matches 100% with zero tolerance" }
  },
  "verified_artifacts_count": 22,
  "auditor_signature": "M2_AUTOMATED_VERIFICATION_SUITE"
}
```

## Kết quả cần đạt & Đường dẫn bàn giao của Nhiệm vụ 12

1. **Notebook thực thi hoàn chỉnh:**
   - `M2/notebooks/12_m2_verification_audit.ipynb`
2. **Artifacts thực nghiệm chuẩn hóa (Thư mục `M2/artifacts/m2-verify-v1/`):**
   - `M2/artifacts/m2-verify-v1/verification_summary.json` (biên bản phán quyết kiểm toán hệ thống)
   - `M2/artifacts/m2-verify-v1/audit_evidence.csv` (bảng chi tiết bằng chứng đối chiếu từng checkpoint)
3. **Báo cáo chuyên đề Markdown:**
   - `M2/reports/Bao_cao_M2_Nhiem_vu_12_Verify_Audit.md`

---

# NHIỆM VỤ 13 — BÁO CÁO TỔNG KẾT VÀ BÀN GIAO CHO MILESTONE M3 (FINAL REPORT & M3 HANDOFF)

## Mục đích của Nhiệm vụ 13

Tổng hợp toàn diện thành quả nghiên cứu phân cụm động lượng M2 thành tài liệu kỹ thuật hoàn chỉnh và đóng gói **Bộ bàn giao chuẩn hóa (Standardized M3 Handoff Package)** để đội ngũ Milestone M3 (Portfolio / Backtest) tiếp nhận trực tiếp mà không cần tính toán lại bất kỳ mô hình nào.

Nhiệm vụ 13 thiết lập ranh giới phương pháp luận bất biến giữa M2 và M3: M2 hoàn tất việc phát hiện cấu trúc phân cụm trên dữ liệu thị trường; M3 tiếp nhận nhãn cụm để xây dựng và đánh giá chiến lược đầu tư.

## Rào chắn ranh giới bất biến giữa M2 và M3 (M2/M3 Boundary Invariants)

Theo docs/DELTA_UNIFIED_PROJECT_PLAN.md Mục 4, 10, 11 và 12, quá trình bàn giao M2 sang M3 phải tuân thủ nghiêm ngặt 3 nguyên tắc sau:

- **Nguyên tắc một chiều (Strict One-Way Handoff):** Mô hình phân cụm M2 một khi đã được kiểm định và đóng băng thì trở thành bất biến. Nhóm M3 tuyệt đối không được phép yêu cầu thay đổi Global K, thay đổi cách scale, đổi PCA hay đổi thuật toán chỉ vì kết quả backtest danh mục bị lỗ hoặc Sharpe thấp.
- **Tách biệt tuyệt đối hai hệ thống chỉ số (Metric Segregation):**
  - Chỉ số thuộc M2 (Đánh giá cấu trúc cụm): Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index, Cluster Balance, ARI, NMI, Persistence, Migration Rate.
  - Chỉ số thuộc M3 (Đánh giá hiệu quả đầu tư): Cumulative Return, CAGR, Annualized Volatility, Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Calmar Ratio, Turnover, Transaction Costs, Alpha, Beta, Information Ratio.
  - Tuyệt đối không dùng chỉ số M3 để can thiệp vào M2.
- **Tính khả thi vận hành Point-in-Time (PIT Execution Rule):** Tại mỗi thời điểm snapshot tháng t, nhóm M3 chỉ được sử dụng nhãn cụm được gán tại đúng snapshot t để thiết lập tỷ trọng danh mục và thực hiện giao dịch tái cơ cấu từ phiên giao dịch tiếp theo (t+1). Tuyệt đối không sử dụng thông tin nhãn cụm tương lai để mua bán trước.

## Đặc tả 5 thành phần trong Gói bàn giao M2 sang M3 (Thư mục `M2/artifacts/m2-final-handoff-v1/`)

Gói bàn giao chuẩn hóa cho M3 bao gồm đúng 5 thành phần dữ liệu và mô hình:

- **Thành phần 1 — Bảng nhãn cụm lịch sử 22 snapshots (`m2_cluster_labels_for_m3.csv`):**  
  Chứa toàn bộ nhãn cụm (Cụm 0, Cụm 1) của mô hình chiến thắng cho tất cả các mã cổ phiếu đủ điều kiện qua đủ 22 snapshots (15 tháng Development và 7 tháng Holdout). Đây là đầu vào trực tiếp cho thuật toán phân bổ danh mục (cluster-to-portfolio mapping) của Milestone M3.  
  *Các cột:* `snapshot_date`, `ticker`, `cluster_label`, `membership_period` (development / holdout).

- **Thành phần 2 — Bảng hồ sơ kinh tế chuẩn hóa (`m2_cluster_profiles_for_m3.csv`):**  
  Chân dung tâm cụm chuẩn hóa trên 8 đặc trưng gốc (Động lượng 1M/3M/6M/12M, Biến động, MDD, Beta, Thanh khoản) qua từng snapshot và trung vị toàn kỳ. Cung cấp căn cứ học thuật để M3 quyết định: Cụm nào là "Cụm Dẫn dắt" (mua / tăng tỷ trọng) và cụm nào là "Cụm Bám sau" (bán / giảm tỷ trọng).

- **Thành phần 3 — Dữ liệu tham chiếu luân chuyển danh mục (`m2_transition_turnover_reference.csv`):**  
  Tổng hợp ma trận chuyển đổi cụm (Transition Matrix) và tỷ lệ chuyển cụm (Migration Rate) qua 20 cặp tháng thực tế (14 cặp Dev + 6 cặp Holdout). Nhóm M3 bắt buộc phải sử dụng dữ liệu này để ước lượng tỷ lệ tái cơ cấu danh mục tối thiểu hàng tháng và thiết lập mô hình chi phí giao dịch (Transaction Costs Modeling).

- **Thành phần 4 — Thư mục mô hình và bộ chuẩn hóa đã đóng băng (`M2/models/final_selected_model/`):**  
  Chứa đầy đủ các đối tượng mô hình (fitted model objects), tọa độ tâm cụm và các tham số chuẩn hóa RobustScaler (Median, IQR) đã được đóng băng. Cho phép M3 tái tạo việc gán nhãn cụm trong môi trường live mà không bị sai lệch.

- **Thành phần 5 — Tệp siêu dữ liệu bàn giao (`m2_to_m3_handoff_manifest.json`):**  
  Tệp metadata chuẩn hóa ghi nhận: Tên mô hình chiến thắng, Global K = 2, danh sách 22 ngày snapshot tái cơ cấu, mã băm SHA-256 của toàn bộ các file bàn giao, và xác nhận đã vượt qua kiểm toán tại Nhiệm vụ 12.

## Khung báo cáo Giới hạn học thuật minh bạch (Academic Limitations & Non-claims)

Trong Báo cáo tổng kết, người thực hiện bắt buộc phải dành riêng một chương để tuyên bố minh bạch các giới hạn nghiên cứu nhằm tránh việc ngộ nhận hoặc diễn giải quá mức (overclaiming):

- **Không phải Dynamic Clustering:** Phân cụm độc lập từng tháng rồi theo dõi ARI chỉ là phương pháp đo lường độ bền cấu trúc theo thời gian (Temporal Stability Diagnostic). Tuyệt đối không được tuyên bố đây là thuật toán Dynamic Clustering.
- **Phạm vi nghiên cứu Market-only:** Nghiên cứu hiện tại chỉ sử dụng các đặc trưng hành vi giá, rủi ro và thanh khoản thị trường. Các chỉ số cơ bản của doanh nghiệp (Piotroski F-Score, Altman Z-Score, Beneish M-Score) tạm thời được hoãn lại (deferred) do yêu cầu khắt khe về tính Point-in-Time (PIT) của báo cáo tài chính (docs/DELTA_UNIFIED_PROJECT_PLAN.md Mục 14, 15).
- **Giới hạn của giai đoạn Holdout 7 tháng năm 2026:** Giai đoạn Holdout ngắn (7 tháng) là một kiểm định bước đầu về độ tổng quát hóa ngoài mẫu. Nếu kết quả suy giảm (Delta_Silhouette âm), phải ghi nhận trung thực hiện tượng dịch chuyển chế độ thị trường (Macro Regime Shift) để nhóm M3 lường trước rủi ro khi vận hành.

## Cấu trúc 6 chương trong Báo cáo Tổng kết `Bao_cao_tong_ket_M2_Ban_giao_M3.md`

Báo cáo tổng kết M2 bắt buộc phải được soạn thảo hoàn chỉnh bằng định dạng Markdown gồm đúng 6 chương:
- **Chương 1 — Tổng quan Phương pháp luận và Protocol thực nghiệm:** Trình bày không gian 8 đặc trưng thị trường, quy tắc chuẩn hóa Robust Scaling per-snapshot, ngưỡng lọc mã đủ điều kiện n_eligible >= 120, và phân định 15 tháng Dev vs 7 tháng Holdout.
- **Chương 2 — Quá trình Lựa chọn và Đóng băng Global K:** Báo cáo chi tiết kết quả quét K từ 2 đến 8 trên tập Development, phân tích diễn biến Silhouette và Davies-Bouldin, lập luận chặt chẽ vì sao Global K = 2 là cấu trúc tối ưu và bền vững nhất.
- **Chương 3 — Kết quả Thực nghiệm Đối đầu giữa 3 Phương án:** So sánh toàn diện K-Means Baseline, Ward Hierarchical và PCA + K-Means trên Ma trận đánh đổi 5 tiêu chí; lập luận việc lựa chọn mô hình chiến thắng theo Dao cạo Occam và phân tích lý do loại bỏ 2 phương án đối chứng.
- **Chương 4 — Kết quả Kiểm định Ngoài mẫu Holdout năm 2026:** Đánh giá năng lực tổng quát hóa ngoài mẫu của mô hình chiến thắng qua 7 tháng năm 2026; phân tích chỉ số khoảng cách suy thoái Delta_Silhouette, độ ổn định thời gian và tính nhất quán của hồ sơ cụm.
- **Chương 5 — Giới hạn Nghiên cứu và Cảnh báo Rủi ro:** Minh bạch các rào chắn học thuật (Non-claims), giải thích việc hoãn tích hợp chỉ số tài chính, và các cảnh báo về hành vi thị trường cho giai đoạn tiếp theo.
- **Chương 6 — Hướng dẫn Tích hợp và Handoff cho Milestone M3:** Đặc tả chi tiết 5 thành phần trong Gói bàn giao, giải thích quy tắc ánh xạ cụm sang danh mục đầu tư, và cam kết ranh giới hoạt động giữa M2 và M3.

## Quy trình thực thi trong Notebook 13

Notebook `M2/notebooks/13_m2_m3_handoff_summary.ipynb` thực thi tuần tự các bước:
1. Nạp kết quả đã được xác thực từ `M2/artifacts/m2-verify-v1/verification_summary.json`. Xác nhận trạng thái `VERIFIED_PASS` trước khi tiến hành đóng gói.
2. Nạp nhãn cụm và hồ sơ cụm của mô hình chiến thắng qua toàn bộ 22 snapshots (15 Dev + 7 Holdout).
3. Đóng gói và xuất file `m2_cluster_labels_for_m3.csv` và `m2_cluster_profiles_for_m3.csv`.
4. Trích xuất ma trận chuyển dịch và tính toán tỷ lệ luân chuyển danh mục tham chiếu, xuất file `m2_transition_turnover_reference.csv`.
5. Tạo tệp siêu dữ liệu `m2_to_m3_handoff_manifest.json` kèm mã băm SHA-256 cho toàn bộ các file bàn giao.
6. Soạn thảo và hoàn thiện văn bản báo cáo `M2/reports/Bao_cao_tong_ket_M2_Ban_giao_M3.md`.

## Kết quả cần đạt & Đường dẫn bàn giao của Nhiệm vụ 13

1. **Notebook thực thi hoàn chỉnh:**
   - `M2/notebooks/13_m2_m3_handoff_summary.ipynb`
2. **Gói Artifact bàn giao chuẩn hóa cho M3 (Thư mục `M2/artifacts/m2-final-handoff-v1/`):**
   - `M2/artifacts/m2-final-handoff-v1/m2_cluster_labels_for_m3.csv` (nhãn cụm lịch sử 22 snapshots)
   - `M2/artifacts/m2-final-handoff-v1/m2_cluster_profiles_for_m3.csv` (chân dung kinh tế tâm cụm 8 đặc trưng gốc)
   - `M2/artifacts/m2-final-handoff-v1/m2_transition_turnover_reference.csv` (tham chiếu luân chuyển và chi phí giao dịch)
   - `M2/artifacts/m2-final-handoff-v1/m2_to_m3_handoff_manifest.json` (tệp siêu dữ liệu bàn giao và mã băm SHA-256)
3. **Thư mục mô hình bàn giao chính thức:**
   - `M2/models/final_selected_model/` (trọng số và tham số scaler của mô hình chiến thắng)
4. **Báo cáo chuyên đề Markdown tổng kết:**
   - `M2/reports/Bao_cao_tong_ket_M2_Ban_giao_M3.md`

# Cách phân công thành viên

## Mục đích

Làm rõ phần nào phải hoàn thành chung trước khi chia người.

Nhiệm vụ 1 → Freeze protocol  
↓  
Nhiệm vụ 2 → Runner  
↓  
Nhiệm vụ 3 → Global K  
↓  
Sau khi Global K khóa mới chia phương án

Thành viên A phụ trách Nhiệm vụ 4 – K-Means. Thành viên B phụ trách Nhiệm vụ 5 – Ward. Thành viên C phụ trách Nhiệm vụ 6 – PCA + K-Means. Mỗi người chạy pipeline phương án của mình từ đầu đến cuối.

Sau đó nhóm tổng hợp Nhiệm vụ 7 → 8 → 9 → 10 → 11 → 12 → 13.

# Workflow cuối cùng của M2

M1 feature snapshots  
↓  
NHIỆM VỤ 1 – Freeze protocol  
↓  
NHIỆM VỤ 2 – Build/test runner  
↓  
NHIỆM VỤ 3 – K-Means K=2..8 trên development  
↓  
Aggregate metrics & Chọn và khóa GLOBAL K  
↓  
K-Means / Ward / PCA + K-Means (Chạy độc lập 3 phương án)  
↓  
NHIỆM VỤ 7 – Quality evaluation  
↓  
NHIỆM VỤ 8 – Cluster profiles  
↓  
NHIỆM VỤ 9 – Temporal stability  
↓  
NHIỆM VỤ 10 – So sánh 3 phương án & CHỌN RA 1 MÔ HÌNH PHÂN CỤM TỐT NHẤT (Khóa Final Method)  
↓  
NHIỆM VỤ 11 – Final Holdout (Chỉ chạy kiểm định trên duy nhất 1 mô hình đã chọn)  
↓  
NHIỆM VỤ 12 – Verify  
↓  
NHIỆM VỤ 13 – Report / Handoff M3

Điểm quan trọng nhất: Nhiệm vụ 1–3 là phần chung để thống nhất methodology và chọn Global K. Sau đó mới chia người theo từng phương án. Mỗi snapshot được lọc, chuẩn hóa và phân cụm riêng; Global K và methodology được khóa chung. Sau Nhiệm vụ 10, nhóm chính thức so sánh và chọn ra duy nhất 1 mô hình tốt nhất (Final Method); Final holdout (Nhiệm vụ 11) chỉ chạy kiểm định độc lập trên mô hình đã chọn này và không được dùng để tiếp tục tuning Protocol v1.
