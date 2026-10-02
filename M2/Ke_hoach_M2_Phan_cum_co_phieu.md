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

- **Code model / Thực thi (cả .ipynb và .py đều lưu trong `M2/notebooks/`)**:
  - Toàn bộ file mã nguồn thực thi mô hình và phân tích của M2 đều được lưu trữ thống nhất trong thư mục `M2/notebooks/`.
  - **Khi nào dùng `.ipynb` (nhiều cell)**: Tác vụ mang tính khám phá (EDA), phân tích từng bước, cần vẽ biểu đồ và trực quan hóa (như Scree plot, Radar chart hồ sơ cụm, Heatmap ma trận chuyển dịch cụm, biểu đồ Boxplot so sánh chất lượng). Phù hợp nhất cho **Nhiệm vụ 6, 7, 8, 9, 10**.
  - **Khi nào dùng `.py` (chạy một mạch)**: Tác vụ là pipeline thực thi tự động, batch runner chạy một mạch từ đầu đến cuối không cần ngắt quãng xem cell, hoặc script kiểm định (verify/audit). Phù hợp cho **Nhiệm vụ 4, 5, 11, 12, 13** (các script `.py` này cũng được đặt trực tiếp trong `M2/notebooks/` để tập trung toàn bộ code vào một nơi).
- **Mô hình / Trọng số (Fitted models & objects)**: Lưu trữ trong thư mục `M2/models/` (các file đối tượng mô hình đã fit, scalers, weights, centroids, linkages, PCA transformers được lưu trữ tuần tự theo nhiệm vụ và thuật toán, bao gồm thư mục `M2/models/final_selected_model/` cho 1 mô hình tốt nhất được chọn sau Nhiệm vụ 10).
- **Báo cáo (Reports & Documents)**: Lưu trữ trong thư mục `M2/reports/` (các file Word `.docx`, báo cáo tổng kết `.md`, tài liệu kiểm định, slide thuyết trình của từng nhiệm vụ và toàn bộ M2).
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
Global K = 2 (hoặc minh họa K = 4)

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
- số mã >= minimum eligible ($n\_eligible \ge 120$)
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
$$x' = \frac{x - \text{Median}}{\text{IQR}}$$

Scaler chỉ thuộc snapshot này. Sang tháng tiếp theo phải tính scaler mới.  
Không: tính scaler tháng 11 rồi dùng lại cho tháng 12.

## Phần 4.4 — Chạy K-Means với Global K

### Mục đích

Tạo kết quả phân cụm chính thức cho snapshot.

Ví dụ:
Global K = 2 (hoặc K = 4)

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

- **Code model / Thực thi**: `M2/notebooks/04_kmeans_baseline.py` (script batch chạy một mạch; hoặc `04_kmeans_baseline.ipynb` nếu muốn vẽ trực quan hóa cụm; phối hợp `src/delta_t1/clustering/kmeans.py` và `src/delta_t1/experiments/runner.py`)
- **Mô hình / Trọng số (Models & Centroids)**: `M2/models/kmeans/` (lưu trữ model K-Means fitted, centroids và snapshot scaler parameters)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_4_KMeans_Baseline.docx` (hoặc `.md`)
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
Global K = 2 (hoặc K = 4)

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
Global K = 2 (hoặc K = 4)

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

- **Code model / Thực thi**: `M2/notebooks/05_ward_hierarchical.py` (script batch chạy một mạch; hoặc `05_ward_hierarchical.ipynb` nếu muốn vẽ dendrogram; phối hợp `src/delta_t1/clustering/hierarchical.py` và `src/delta_t1/experiments/runner.py`)
- **Mô hình / Trọng số (Models & Linkages)**: `M2/models/ward/` (lưu trữ ma trận linkage, cluster representatives, scaler parameters)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_5_Ward.docx` (hoặc `.md`)
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
Global K = 2 (hoặc K = 4)

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
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_6_PCA_KMeans.docx` (hoặc `.md`)
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
1. **Bước 1 (Đọc dữ liệu chẩn đoán):** Sử dụng `pandas` đọc trực tiếp file `diagnostics.csv` từ thư mục artifact của phương án tương ứng.
2. **Bước 2 (Trích xuất & Tính toán bảng tổng hợp):** Lọc lấy 15 dòng dữ liệu ứng với cấu hình K=2, dùng các hàm thống kê mô tả cơ bản của pandas để tính Mean, Median, Min, Max cho 5 chỉ số và tự động xuất ra file `quality_summary.csv`.
3. **Bước 3 (Hiển thị 2 Bảng chuẩn):** Hiển thị Bảng tổng hợp (Bảng 1) và Bảng chi tiết 15 snapshots (Bảng 2) dưới dạng bảng HTML tương tác (`display()`).
4. **Bước 4 (Trực quan hóa 5 Biểu đồ đường):** Dùng `matplotlib` vẽ 5 biểu đồ chuỗi thời gian cho 5 chỉ số chất lượng từ Mục 7.1 đến 7.5 kèm đường tham chiếu Median nét đứt màu đỏ.
5. **Bước 5 (Soạn thảo Nhận định kinh tế & Rào chắn học thuật):** Trình bày phân tích hiện tượng thị trường và giới hạn toán học trực tiếp vào các ô Markdown trong Notebook, sau đó tổng hợp thành file báo cáo Markdown độc lập.

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

## Nhận định kinh tế tài chính & Rào chắn học thuật (Academic Invariants)

Sau khi chạy code hiển thị bảng và biểu đồ, người thực hiện **bắt buộc phải tạo các ô Markdown trong Notebook** để trình bày bằng văn bản 3 nội dung trọng tâm sau:

### 1. Phân cấp ưu tiên tiêu chí theo DELTA_UNIFIED_PROJECT_PLAN.md
- **Tiêu chí cấp 1 (Primary Criterion):** `Median Silhouette cao nhất`. Đây là cơ sở toán học cao nhất để chứng minh K=2 tạo ra ranh giới tách biệt rõ ràng nhất giữa các nhóm cổ phiếu trên thị trường Việt Nam.
- **Tiêu chí phá vỡ thế cân bằng (Secondary Tie-breaker):** `Median Davies-Bouldin thấp hơn`. Dùng khi Silhouette giữa các phương án xấp xỉ nhau.
- **Tiêu chí kiểm định an toàn (Sanity Diagnostics):** `Calinski-Harabasz` và `Cluster Balance` dùng để kiểm tra độ tin cậy, cảnh báo nguy cơ phân cụm bị chi phối bởi các cổ phiếu dị biệt.

### 2. Hiện tượng kinh tế và cấu trúc vi mô thị trường
- **Giải thích hiện tượng Balance thấp (Fragmentation / Outlier Clusters):** Nếu Cluster Balance ở mức thấp (< 0.05 hoặc cụm nhỏ chỉ có vài mã đến vài chục mã), phải diễn giải rõ: Thuật toán đang tách thị trường thành một nhóm đại trà (phần lớn thị trường) và một nhóm cực đoan (gồm các cổ phiếu siêu động lượng, siêu thanh khoản hoặc biến động dị biệt). Đây là đặc tính tự nhiên của dữ liệu tài chính có đuôi dài (heavy tails).
- **Phân tích hiện tượng biến động (Spikes):** Đánh giá các tháng có điểm chất lượng sụt giảm mạnh (ví dụ tháng 07/2024) hoặc tăng đột biến (cuối năm 2024 khi số mã tăng lên ~800 mã).

### 3. Ranh giới kỷ luật phương pháp luận (Methodology Boundaries)
- **Cảnh báo về Inertia trên chuỗi thời gian:** Tuyệt đối không so sánh giá trị Inertia tuyệt đối giữa các tháng với nhau vì quy mô mã N tăng từ 142 lên 780 làm Inertia tăng cơ học. Inertia chỉ có giá trị khi so sánh các K khác nhau trong cùng 1 tháng.
- **Nghiêm cấm tối ưu hóa bằng lợi nhuận:** Không được đưa Return, Sharpe hay ROI vào Nhiệm vụ 7 để chọn mô hình có chất lượng "tốt hơn". Đánh giá chất lượng cụm độc lập hoàn toàn với bài toán danh mục.

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
1. **Bước 1 (Đã hoàn thành ở Nhiệm vụ 4, 5, 6):** Pipeline huấn luyện tự động xuất ra file `cluster_profiles.csv` (13 cột chuẩn) vào thư mục artifact tương ứng.
2. **Bước 2 (Nạp dữ liệu vào Notebook):** Notebook đọc trực tiếp file CSV vào DataFrame bằng 1 dòng lệnh duy nhất.
3. **Bước 3 (Tổng hợp số liệu & Trực quan hóa):** Chạy code pandas để xuất ra 3 Bảng số liệu chuẩn và 2 Biểu đồ chuẩn (Radar Chart, Heatmap).
4. **Bước 4 (Viết nhận định & Báo cáo):** Soạn thảo nhận định tài chính và giới hạn học thuật vào các ô Markdown trong Notebook, sau đó tổng hợp thành file báo cáo Markdown độc lập.

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

### Phần 8.4 — Nhận định kinh tế tài chính & Giới hạn diễn giải học thuật

Sau khi chạy code hiển thị bảng và biểu đồ, người thực hiện **bắt buộc phải tạo các ô Markdown trong Notebook** để trình bày bằng văn bản 2 nội dung then chốt sau:

#### 1. Nhận định kinh tế tài chính (Financial Interpretations)
Diễn giải ý nghĩa kinh tế thực tế của các con số trên thị trường chứng khoán Việt Nam:
- **Thanh khoản:** Phân tích sự chênh lệch dòng tiền giữa Cụm 0 và Cụm 1 (Cụm thanh khoản lớn gồm các mã Blue-chip/Mid-cap dẫn dắt hay Cụm thanh khoản thấp chiếm đa số).
- **Rủi ro hệ thống (Beta):** Phân tích tương quan chuyển động của cụm so với VNINDEX (Cụm nhạy sóng khuếch đại thị trường với Beta > 1 hay cụm phòng thủ ít nhạy với Beta < 1).
- **Động lượng giá:** Đánh giá xu hướng tăng trưởng giá ngắn hạn (21, 63 ngày) và dài hạn (126, 252 ngày).
- **Bản chất phân tách:** Tóm lược động lực chính khiến thuật toán tách thị trường thành 2 nhóm.

#### 2. Giới hạn diễn giải học thuật (Academic Invariants & Boundaries)
Ghi nhận đầy đủ các rào chắn kỷ luật nghiên cứu để đảm bảo tính chuẩn mực học thuật:
- **Mean nhạy với quan sát cực đoan:** Giá trị trung bình của cụm không đại diện cho phân phối của từng cổ phiếu đơn lẻ bên trong cụm.
- **Tuyệt đối không khuyến nghị đầu tư:** Sự vượt trội về thanh khoản hay động lượng ở giai đoạn M2 chỉ mô tả đặc tính nhóm trong quá khứ, không suy diễn thành khuyến nghị "nên mua cổ phiếu thuộc Cụm 0".
- **Duy trì nhãn trung tính:** Giữ nguyên tên gọi trung tính "Cụm 0" và "Cụm 1", không tùy tiện gán nhãn chủ quan như "siêu cổ phiếu", "tinh hoa" hay "penny".
- **Ranh giới M2 và M3:** Đánh giá tỷ suất sinh lời hay Sharpe ratio thuộc về bước Backtest (Milestone M3), nghiêm cấm đưa các chỉ số lợi nhuận vào Nhiệm vụ 8.

## Kết quả cần đạt & Đường dẫn bàn giao (Deliverables)

Mỗi mô hình khi hoàn thành Nhiệm vụ 8 phải có đầy đủ bộ bàn giao gồm:
1. **Notebook thực thi hoàn chỉnh:**
   - K-Means: `M2/notebooks/08_cluster_profiling_kmeans.ipynb`
   - Ward: `M2/notebooks/08_cluster_profiling_ward.ipynb`
   - PCA + K-Means: `M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb`
2. **Hình ảnh biểu đồ xuất xưởng (lưu vào thư mục báo cáo):**
   - `radar_chart.png`
   - `heatmap.png`
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
1. **Bước 1 (Đã hoàn thành ở Nhiệm vụ 4, 5, 6):** Pipeline huấn luyện tự động xuất ra bộ 3 file CSV chuẩn gồm `temporal_stability.csv`, `transition_matrices.csv` và `centroid_drift.csv` vào thư mục artifact tương ứng.
2. **Bước 2 (Nạp dữ liệu vào Notebook):** Notebook đọc trực tiếp 3 file CSV bằng lệnh `pd.read_csv()`.
3. **Bước 3 (Tổng hợp số liệu & Trực quan hóa):** Chạy code pandas để xuất ra đúng 4 Bảng số liệu chuẩn và 2 Biểu đồ chuẩn (Đồ thị xu hướng đa panel và Heatmap ma trận chuyển dịch).
4. **Bước 4 (Viết nhận định & Báo cáo):** Soạn thảo nhận định tài chính và giới hạn học thuật vào các ô Markdown trong Notebook, sau đó tổng hợp thành file báo cáo Markdown độc lập.

## Quy chuẩn Dữ liệu Đầu vào (Unified Input Contract)

Nhiệm vụ 9 của cả 3 mô hình đều đọc vào **bộ 3 file CSV phẳng** có cấu trúc cột cố định từ thư mục artifact của task trước:
- K-Means: `M2/artifacts/m2-evaluation-kmeans/` (hoặc `m2-task4-kmeans-baseline-v1/`)
- Ward: `M2/artifacts/m2-evaluation-ward/` (hoặc `m2-task5-ward-v1/`)
- PCA + K-Means: `M2/artifacts/m2-evaluation-pca-kmeans/` (hoặc `m2-task6-pca-kmeans-v1/`)

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

### Phần 9.10 — Nhận định tài chính & Giới hạn diễn giải học thuật

Sau khi hiển thị bảng và biểu đồ, người thực hiện **bắt buộc phải tạo ô Markdown trong Notebook** để trình bày bằng văn bản 2 nội dung:

#### 1. Nhận định kinh tế tài chính
- **Độ bền vững cấu trúc:** Đánh giá trị số ARI và NMI trung bình (thường đạt quanh mức 0.75 - 0.80) chứng minh cấu trúc 2 cụm phân tách rất rõ ràng, không bị xáo trộn ngẫu nhiên.
- **Tính gắn kết thành viên:** Đánh giá chỉ số Persistence (> 98%) cho thấy các mã cổ phiếu cực kỳ ổn định trong cụm của mình; nhóm thanh khoản cao Bluechip/Midcap rất hiếm khi bị rớt sang nhóm thanh khoản thấp và ngược lại.
- **Tính ổn định tâm cụm:** Phân tích độ lệch tâm Centroid Drift để khẳng định ranh giới giữa 2 cụm giữ nguyên bản chất qua các tháng thị trường tăng lẫn giảm.

#### 2. Giới hạn học thuật bất biến
- **Không phải Dynamic Clustering:** Phân cụm độc lập từng tháng rồi nối lại đo lường ARI/chuyển dịch chỉ là phương pháp đánh giá độ bền (Temporal Stability Diagnostic), **tuyệt đối không được gọi đây là thuật toán Dynamic Clustering**.
- **Không tối ưu hóa theo lợi nhuận:** Không được phép dùng chỉ số ổn định thời gian để suy diễn cụm nào sinh lời tốt hơn hay can thiệp vào chiến lược đầu tư (thuộc Milestone M3).

## Kết quả cần đạt & Đường dẫn bàn giao (Deliverables)

Mỗi mô hình khi hoàn thành Nhiệm vụ 9 phải có đầy đủ bộ bàn giao gồm:
1. **Notebook thực thi hoàn chỉnh:**
   - K-Means: `M2/notebooks/09_temporal_stability_kmeans.ipynb`
   - Ward: `M2/notebooks/09_temporal_stability_ward.ipynb`
   - PCA + K-Means: `M2/notebooks/09_temporal_stability_pca_kmeans.ipynb`
2. **Hình ảnh biểu đồ xuất xưởng (lưu vào thư mục báo cáo):**
   - `temporal_trends.png`
   - `transition_heatmap.png`
3. **Báo cáo chuyên đề Markdown:**
   - K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_KMeans.md`
   - Ward: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_Ward.md`
   - PCA + K-Means: `M2/reports/Bao_cao_M2_Nhiem_vu_9_Do_on_dinh_thoi_gian_PCA_KMeans.md`

# NHIỆM VỤ 10 — SO SÁNH CÁC PHƯƠNG ÁN VÀ CHỌN RA 1 MÔ HÌNH TỐT NHẤT (FINAL METHOD SELECTION)

## Mục đích của Nhiệm vụ 10

Tổng hợp toàn diện kết quả của K-Means, Ward và PCA + K-Means trên cùng protocol development, và **chính thức lựa chọn duy nhất 1 mô hình phân cụm tốt nhất (Final Method)** để khóa lại trước khi mở Final Holdout (Nhiệm vụ 11) và chuyển giao cho M3.

Hai phương án còn lại không bị loại bỏ mà được giữ nguyên trong toàn bộ tài liệu và báo cáo dưới vai trò các phương án đối chứng (*comparator baselines*) để chứng minh tính thuyết phục của quá trình thực nghiệm.

## Vị trí của bước chọn phương án trong workflow

Bước lựa chọn 1 mô hình tốt nhất diễn ra ngay tại Nhiệm vụ 10 (sau khi đã có đủ kết quả chất lượng, hồ sơ cụm, độ ổn định thời gian) và **trước khi mở Nhiệm vụ 11 – Final Holdout**:

Development (15 snapshots)  
↓  
K-Means / Ward / PCA + K-Means  
↓  
Nhiệm vụ 7 – Quality  
↓  
Nhiệm vụ 8 – Cluster profile  
↓  
Nhiệm vụ 9 – Temporal stability  
↓  
Nhiệm vụ 10 – So sánh 3 phương án  
↓  
**CHỌN VÀ KHÓA 1 MÔ HÌNH PHÂN CỤM TỐT NHẤT (FINAL METHOD)**  
↓  
Nhiệm vụ 11 – Final Holdout (chỉ chạy duy nhất mô hình đã chọn)  
↓  
Nhiệm vụ 12 – Verify  
↓  
Nhiệm vụ 13 – Report / Handoff M3

## Nguyên tắc bắt buộc khi lựa chọn

- Việc chọn phương án chỉ được dựa trên kết quả giai đoạn development. Final holdout tuyệt đối không được mở trước khi final method đã được quyết định và khóa.
- Không dùng future return, CAGR, Sharpe, Sortino, ROI, Calmar, alpha hoặc kết quả backtest để chọn thuật toán M2.
- Không nhìn kết quả holdout rồi quay lại thay đổi phương án.
- Không thay đổi feature set, Global K, scaling hoặc PCA rule riêng cho từng phương án chỉ để cải thiện kết quả so sánh.
- Các phương án phải được so sánh trên cùng development window, cùng universe rule, cùng 8 feature và cùng Global K đã khóa.

## Phần 10.1 — So sánh quality

### Mục đích

So sánh chất lượng cấu trúc cụm giữa 3 phương án:
- So sánh median Silhouette (cao hơn thường tốt hơn, chỉ số chính).
- So sánh median Davies–Bouldin (thấp hơn thường tốt hơn, dùng xác nhận).
- So sánh Calinski–Harabasz (chỉ số bổ sung).

## Phần 10.2 — So sánh temporal stability

### Mục đích

So sánh độ ổn định theo thời gian:
- So sánh ARI và NMI trung vị giữa hai snapshot liên tiếp ($t$ và $t+1$).
- Persistence probability (xác suất giữ nguyên cụm) và Migration rate (tỷ lệ chuyển dịch cụm).
- Centroid drift (mức độ biến động tâm cụm theo thời gian).

## Phần 10.3 — So sánh cân bằng và khả năng diễn giải hồ sơ cụm

### Mục đích

- **Cluster balance**: Sanity check phát hiện cụm suy biến (cụm rác hoặc cụm quá bé < 5 mã).
- **Khả năng diễn giải**: Xem cluster profile của phương án nào thể hiện rõ ràng và hợp lý nhất theo 8 đặc trưng gốc (Động lượng, Biến động, MDD, Beta, Thanh khoản). Đối với PCA + K-Means, kiểm tra trade-off giữa việc giảm chiều và độ phức tạp khi giải thích ngược về 8 feature gốc.

## Phần 10.4 — Các nhóm tiêu chí và thứ tự ưu tiên chọn 1 mô hình tốt nhất

Đánh giá lựa chọn theo thứ tự ưu tiên 5 cấp độ:

| **Ưu tiên** | **Nhóm tiêu chí** | **Chỉ số / bằng chứng** | **Mục đích** | **Vai trò** |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Chất lượng phân cụm** | Silhouette, Davies–Bouldin | Đánh giá cụm có rõ nét, chặt chẽ và tách biệt không | **Tiêu chí quyết định chính** |
| **2** | **Độ ổn định thời gian** | ARI, Persistence, Migration, Centroid drift | Đánh giá cấu trúc cụm có ổn định qua các tháng không | **Tiêu chí quan trọng thứ hai** |
| **3** | **Cân bằng cụm** | Phân phối kích thước cụm | Loại trừ hiện tượng cụm suy biến / quá nhỏ | **Sanity check** |
| **4** | **Khả năng diễn giải** | Profile trên 8 đặc trưng gốc | Đảm bảo cụm có ý nghĩa kinh tế rõ ràng | **Tiêu chí hỗ trợ** |
| **5** | **Độ đơn giản & Tái lập** | Số bước, số siêu tham số, reproducibility | Ưu tiên phương pháp ít phức tạp hơn nếu kết quả tương đương | **Tie-breaker** |

*Lưu ý: Không dùng công thức điểm tổng hợp trọng số cảm tính (như 40% Silhouette + 30% ARI...) để tránh quyết định chủ quan.*

## Phần 10.5 — Quy trình ra quyết định và lập Decision Artifact

1. Tổng hợp bảng đối đầu 3 phương án theo đầy đủ các chỉ số median trên development.
2. Áp dụng quy tắc ưu tiên:
   - Nếu một phương án vượt trội rõ nét ở cả Silhouette và Davies–Bouldin → Chọn phương án đó làm Final Method.
   - Nếu chất lượng cụm giữa các phương án sát nhau → So sánh độ ổn định theo thời gian (ARI, Migration).
   - Nếu vẫn tương đương → Xét khả năng diễn giải và ưu tiên phương án có pipeline đơn giản hơn (ví dụ K-Means gốc đơn giản hơn PCA + K-Means).
3. Lập **Decision Artifact** (`final_method_decision.json` hoặc `.md`) lưu rõ: phương án được chọn, bảng số liệu đối đầu, lý do lựa chọn, và cam kết khóa mô hình.

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file `.py` riêng lẻ; thông thường `runner.py` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**`src/delta_t1/experiments/runner.py`** — file đã có; nguồn artifact chuẩn hóa.
> Mục đích: Đã ghi diagnostics, profiles, stability và transitions cho từng run.  
> Cách dùng trong nhiệm vụ này: Nhiệm vụ 10 đọc các artifact này của ba phương án, không cần fit lại mô hình chỉ để so sánh.

**`src/delta_t1/evaluation/cluster_metrics.py`** — file đã có; nguồn quality.
> Mục đích: Cung cấp định nghĩa/giá trị quality metrics.  
> Cách dùng trong nhiệm vụ này: Tổng hợp median/summary của Silhouette, DB, CH và balance theo phương án.

**`src/delta_t1/evaluation/temporal_metrics.py`** — file đã có; nguồn temporal.
> Mục đích: Cung cấp chỉ số ổn định qua thời gian.  
> Cách dùng trong nhiệm vụ này: Tổng hợp ARI, NMI, persistence, migration và centroid drift để so sánh.

**`src/delta_t1/experiments/reporting.py`** — file đã có; hỗ trợ xuất kết quả.
> Mục đích: Có các hàm tạo bảng/report/plot từ artifact.  
> Cách dùng trong nhiệm vụ này: Dùng để trình bày bảng so sánh cuối thay vì viết lại logic clustering.

### Cách các file phối hợp

> diagnostics + profiles + stability + transitions của 3 phương án → tổng hợp quality/temporal/interpretability → reporting.py → bảng so sánh/decision evidence → chọn & khóa 1 Final Method.

## Kết quả cần đạt của Nhiệm vụ 10

- Bảng so sánh đa chiều thống nhất giữa K-Means, Ward, PCA + K-Means;
- Quyết định lựa chọn duy nhất 1 mô hình phân cụm tốt nhất (Final Method);
- Decision Artifact ghi nhận căn cứ lựa chọn;
- Khóa cấu hình mô hình được chọn để chuyển tiếp sang Nhiệm vụ 11 (Final Holdout).

## Vị trí trong repo & Đường dẫn output

- **Code tổng hợp / So sánh**: `M2/notebooks/10_model_comparison.ipynb` (hoặc `10_model_comparison.py`, lưu trong `M2/notebooks/`)
- **Mô hình được chọn**: `M2/models/final_selected_model/` (lưu trữ model và scaler parameters của phương án chiến thắng)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_10_So_sanh_va_Chon_mo_hinh_tot_nhat.docx` (hoặc `.md`)
- **Artifacts thực nghiệm chuẩn hóa**: `M2/artifacts/m2-evaluation/methodology_comparison.csv`, `M2/artifacts/m2-evaluation/final_method_decision.json` (lưu trong M2 để push lên GitHub)

# NHIỆM VỤ 11 — MỞ VÀ CHẠY FINAL HOLDOUT

## Mục đích của Nhiệm vụ 11

Kiểm tra xem **duy nhất 1 mô hình phân cụm tốt nhất** đã được chọn và khóa ở Nhiệm vụ 10 có tiếp tục hoạt động ổn định và hợp lý trên giai đoạn dữ liệu mới (holdout) hay không. Final holdout chỉ dùng để kiểm định độc lập, tuyệt đối không dùng để tìm mô hình tốt hơn hoặc thay đổi lại mô hình đã chọn.

Development  
→ xây, so sánh và chọn ra 1 mô hình tốt nhất  
  
Final Holdout  
→ kiểm định duy nhất mô hình đã khóa

Trước khi mở holdout phải khóa 8 feature, universe rule, minimum eligible threshold, missing policy, outlier policy, scaling, Global K, PCA rule (nếu chọn PCA), và thuật toán đã chọn. Không thử lại K=2..8 và không chạy lại các phương án đã bị loại trên holdout.

## Đầu vào của Nhiệm vụ 11

### Final holdout

27/02/2026 → 28/08/2026  
7 snapshot liên tục

### Methodology đã freeze

Feature: 8 market features  
Scaling: Robust Scaling theo snapshot  
Global K: giá trị đã khóa  
Algorithm: Duy nhất 1 mô hình phân cụm tốt nhất được chọn từ Nhiệm vụ 10 (Final Method)

## Phần 11.1 — Chỉ mở holdout sau khi development freeze và khóa Final Method

### Mục đích

Ngăn holdout ảnh hưởng đến quá trình lựa chọn methodology.

Development hoàn tất → Global K khóa → So sánh 3 phương án xong → Chọn & Khóa 1 Final Method → Decision artifact freeze → mới mở holdout.

## Phần 11.2 — Lấy snapshot holdout đầu tiên

### Mục đích

Tạo dữ liệu đầu vào holdout theo đúng rule development.

Ví dụ 27/02/2026 → lọc universe tại đúng ngày này → lấy 8 feature → kiểm tra hợp lệ → kiểm tra số mã \>=120. Không dùng 905 mã của 08/2026 áp cho tháng 02/2026.

## Phần 11.3 — Chuẩn hóa snapshot holdout

### Mục đích

Giữ nguyên preprocessing đã freeze.

Với mỗi snapshot, tính Median và IQR của chính snapshot đó rồi Robust Scaling. Development và holdout đều dùng snapshot-fit. Không dùng một scaler chung của toàn development và không đổi sang Z-score.

## Phần 11.4 — Chạy K-Means trên holdout

### Mục đích

Kiểm tra baseline K-Means trên dữ liệu mới.

snapshot → lọc universe → 8 feature → Robust Scaling → K-Means Global K → assignment → centroid → profile → quality metrics. Không thử K khác.

## Phần 11.5 — Chạy Ward trên holdout

### Mục đích

Kiểm tra Ward trên cùng điều kiện.

snapshot → same universe → same 8 feature → same scaling rule → Ward → Global K → assignment → metrics.

## Phần 11.6 — Chạy PCA + K-Means trên holdout

### Mục đích

Kiểm tra nhánh giảm chiều đã freeze.

snapshot → 8 feature → Robust Scaling → PCA theo rule đã khóa → K-Means Global K. Không dùng holdout để chọn lại số PCA components.

## Phần 11.7 — Lặp lại cho toàn bộ 7 snapshot

### Mục đích

Đánh giá methodology trên toàn holdout.

Mỗi snapshot: lọc universe → lấy 8 feature → fit RobustScaler riêng → chạy 3 phương án → lưu output.

## Phần 11.8 — Đánh giá quality từng snapshot holdout

### Mục đích

Kiểm tra chất lượng phân cụm trên dữ liệu mới.

Tính Silhouette, DB, CH, balance và inertia khi phù hợp cho từng snapshot × phương án.

## Phần 11.9 — Phân tích cluster profile holdout

### Mục đích

Kiểm tra các cụm trên dữ liệu mới còn có ý nghĩa và dễ diễn giải không.

Nếu profile thay đổi mạnh thì ghi nhận, phân tích và đưa vào limitations; không retune.

## Phần 11.10 — Temporal stability trong holdout

### Mục đích

Kiểm tra sự ổn định giữa các tháng holdout.

Tính ARI, NMI, persistence, migration, transition matrix, centroid drift và entry/exit cho các cặp tháng liên tiếp trong holdout.

## Phần 11.11 — Không nối development sang holdout qua gap

### Mục đích

Không tạo sự liên tục giả.

Development kết thúc khoảng 01/2025, holdout bắt đầu 02/2026; không tính 01/2025 → 02/2026 như hai tháng liên tiếp. Phải reset temporal chain.

## Phần 11.12 — So sánh development và holdout

### Mục đích

Đánh giá độ bền của methodology.

So sánh median Silhouette, median DB, balance, ARI/NMI, migration và cluster profiles. Đây là đánh giá, không phải tuning.

## Phần 11.13 — Nếu holdout cho kết quả xấu

### Mục đích

Đảm bảo holdout không bị biến thành development thứ hai.

Nếu Silhouette giảm, DB tăng, ARI thấp hoặc migration cao thì giữ nguyên kết quả, phân tích nguyên nhân và báo cáo limitation. Không đổi K, scaler hay PCA rồi chạy lại. Nếu thay methodology thì tạo Protocol v2.

## Phần 11.14 — Ví dụ toàn bộ một snapshot holdout

### Mục đích

Giúp thành viên hình dung một vòng chạy hoàn chỉnh.

Ví dụ Global K=4, PCA=4 components: 27/02/2026 → universe hợp lệ → 8 feature → Robust Scaling riêng snapshot → K-Means K=4 / Ward K=4 / PCA 4 components → K-Means K=4 → lưu assignment, profile, metrics.

## Phần 11.15 — Output từng snapshot holdout

### Mục đích

Đảm bảo output holdout tương thích với development.

Lưu snapshot date, số mã đủ điều kiện, danh sách mã, Median, IQR, scaler parameters, PCA parameters, explained variance nếu có, assignments, cluster sizes, centroid/profile và quality metrics.

## Phần 11.16 — Output toàn holdout

### Mục đích

Tạo evidence hoàn chỉnh cho M2-VERIFY.

Cần có assignments của 7 snapshot, cluster profiles, quality metrics, aggregate metrics, ARI, NMI, persistence, migration, transition matrices, centroid drift, entry/exit, PCA information, skipped snapshot reasons nếu có, manifest và hashes.

| **Snapshot** | **Phương án** | **Silhouette** | **DB** | **CH** | **Balance** |
|--------------|---------------|----------------|--------|--------|-------------|
| 02/2026      | K-Means       | ...            | ...    | ...    | ...         |
| 02/2026      | Ward          | ...            | ...    | ...    | ...         |
| 02/2026      | PCA + K-Means | ...            | ...    | ...    | ...         |

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file \`.py\` riêng lẻ; thông thường \`runner.py\` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**\`src/delta_t1/experiments/protocol.py\`** — file đã có; kiểm tra protocol đã freeze.

> Mục đích: Ngăn holdout chạy với config khác rule development.
>
> Cách dùng trong nhiệm vụ này: Validate config trước khi mở/chạy holdout.

**\`src/delta_t1/experiments/runner.py\`** — file đã có; điều phối 7 snapshot holdout.

> Mục đích: Tái sử dụng pipeline đã kiểm thử ở development.
>
> Cách dùng trong nhiệm vụ này: Đọc holdout window từ config, lọc snapshot, gọi final method và lưu artifact.

**\`src/delta_t1/clustering/base.py\`** — file đã có; xử lý từng holdout snapshot.

> Mục đích: Giữ cùng eligibility/preprocessing/output contract.
>
> Cách dùng trong nhiệm vụ này: Mỗi snapshot được lọc, scale và fit độc lập đúng rule.

**\`src/delta_t1/features/preprocessing.py\`** — file đã có; preprocessing đã freeze.

> Mục đích: Áp dụng Robust Scaling và PCA nếu final method cần.
>
> Cách dùng trong nhiệm vụ này: Không đổi scaler và không chọn lại PCA component trên holdout.

**\`src/delta_t1/clustering/kmeans.py\` / \`src/delta_t1/clustering/hierarchical.py\`** — file đã có; chỉ dùng file phù hợp final method.

> Mục đích: Thực hiện thuật toán đã được khóa sau development.
>
> Cách dùng trong nhiệm vụ này: Nếu final method là K-Means thì gọi kmeans.py; nếu Ward thì gọi hierarchical.py; nếu PCA+KMeans thì preprocessing.py PCA rồi kmeans.py.

**\`src/delta_t1/evaluation/cluster_metrics.py\` và \`src/delta_t1/evaluation/temporal_metrics.py\`** — file đã có; chỉ dùng để đánh giá.

> Mục đích: Đo quality và temporal stability trên dữ liệu mới.
>
> Cách dùng trong nhiệm vụ này: Không dùng kết quả holdout để retune K, scaler, PCA hay thuật toán.

### Cách các file phối hợp

> frozen config → protocol.py → runner.py → base.py → preprocessing.py → final algorithm → cluster_metrics + temporal_metrics → holdout artifact; không retune.

## Kết quả cần đạt của Nhiệm vụ 11

- Kết quả kiểm định độc lập của **duy nhất 1 mô hình tốt nhất đã chọn** trên 7 snapshots holdout;
- Không dùng kết quả holdout để thay đổi lại mô hình đã chọn hoặc retune siêu tham số;
- Đánh giá chất lượng cụm và độ ổn định thời gian trên holdout so với development;
- Ghi nhận đầy đủ giới hạn thực nghiệm.

## Vị trí trong repo & Đường dẫn output

- **Vị trí tài liệu tham chiếu**: `docs/DELTA_UNIFIED_PROJECT_PLAN.md` §6.2, §6.6, §6.7, §6.8, §9, `docs/EXPERIMENT_PROTOCOL.md`, `docs/METHODOLOGY.md`
- **Code model / Thực thi holdout**: `M2/notebooks/11_final_holdout_execution.py` (script batch chạy một mạch; hoặc `11_final_holdout_execution.ipynb` ngắn; chạy đóng băng trên 1 mô hình đã chọn)
- **Mô hình / Trọng số (Models & Holdout Objects)**: `M2/models/holdout/` (lưu trữ fitted objects cho holdout snapshots)
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.docx` (hoặc `.md`)
- **Artifacts thực nghiệm chuẩn hóa**: `M2/artifacts/m2-final-holdout-v1/` (lưu trong M2 để push lên GitHub)

# NHIỆM VỤ 12 — M2 VERIFY

## Mục đích của Nhiệm vụ 12

Kiểm tra toàn bộ M2 đã thực hiện đúng methodology, không leakage và có thể tái lập.

## Phần 12.1 — Kiểm tra config và input

### Mục đích

Đảm bảo đúng version dữ liệu và đúng config.

Kiểm tra input hash, config hash và output hash.

## Phần 12.2 — Kiểm tra Global K

### Mục đích

Đảm bảo Global K được chọn đúng rule và không thay đổi sau development.

Đối chiếu decision artifact với các run chính thức.

## Phần 12.3 — Kiểm tra leakage

### Mục đích

Đảm bảo không dùng future data, holdout hoặc portfolio performance để tuning M2.

Audit development/holdout boundary và các trường dữ liệu.

## Phần 12.4 — Kiểm tra temporal gaps

### Mục đích

Đảm bảo temporal chain reset đúng.

Không nối qua các gap đã xác định.

## Phần 12.5 — Kiểm tra reproducibility

### Mục đích

Đảm bảo chạy lại trên fixture giới hạn cho kết quả xác định.

Rerun bounded fixture và đối chiếu output.

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file \`.py\` riêng lẻ; thông thường \`runner.py\` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**\`src/delta_t1/experiments/artifacts.py\`** — file đã có; quản lý artifact/manifest.

> Mục đích: Runner dùng file này để mở, hoàn tất và xác thực data/experiment run.
>
> Cách dùng trong nhiệm vụ này: Đối chiếu manifest, run lineage và input đã verified.

**\`src/delta_t1/experiments/protocol.py\`** — file đã có; kiểm tra config.

> Mục đích: Xác nhận run dùng đúng protocol đã freeze.
>
> Cách dùng trong nhiệm vụ này: So sánh config thực tế với rule M2 v1 và decision artifacts.

**\`src/delta_t1/experiments/runner.py\`** — file đã có; nguồn evidence của run.

> Mục đích: Tạo events, manifest, số snapshot, assignments và trạng thái complete/failed.
>
> Cách dùng trong nhiệm vụ này: Dùng các artifact runner sinh ra để audit leakage, gap và số liệu đầu ra.

**Các test hiện có trong repo** — dùng để kiểm tra reproducibility và integration.

> Mục đích: Chứng minh cùng input/config cho kết quả xác định và market-only rule hoạt động đúng.
>
> Cách dùng trong nhiệm vụ này: Chạy unit/integration test cho eligibility, terminal-universe, temporal gap và deterministic rerun; nếu thiếu test thì bổ sung test tương ứng.

### Cách các file phối hợp

> config + decision artifacts + manifest + events + hashes + tests → artifacts.py/protocol.py/runner outputs → audit → verify status + evidence.

## Kết quả cần đạt của Nhiệm vụ 12

- verify status;

- evidence đầy đủ;

- không có methodology violation.

## Vị trí trong repo & Đường dẫn output

- **Code kiểm định / Verify script**: `M2/notebooks/12_m2_verification_audit.py` (script kiểm định tự động chạy một mạch; hoặc `12_m2_verification_audit.ipynb`)
- **Mô hình**: Kiểm tra tính toàn vẹn của tất cả model objects trong `M2/models/`
- **Báo cáo (Reports)**: `M2/reports/Bao_cao_M2_Nhiem_vu_12_Verify_Audit.docx` (hoặc `.md`)
- **Artifacts kiểm định**: `M2/artifacts/m2-verify-v1/verification_summary.json`, `M2/artifacts/m2-verify-v1/audit_evidence.csv` (lưu trong M2 để push lên GitHub)

# NHIỆM VỤ 13 — BÁO CÁO VÀ BÀN GIAO M3

## Mục đích của Nhiệm vụ 13

Tổng hợp toàn bộ M2 thành tài liệu để mentor hoặc nhóm M3 có thể tiếp nhận trực tiếp.

## Phần 13.1 — Báo cáo protocol

### Mục đích

Cho biết M2 được thực hiện theo quy tắc nào.

Gồm development, holdout, feature, scaling, Global K, PCA và algorithms.

## Phần 13.2 — Báo cáo Global K selection

### Mục đích

Chứng minh K không được chọn tùy ý.

Thể hiện K=2..8 → metric từng snapshot → aggregate theo K → Global K.

## Phần 13.3 — Báo cáo từng phương án

### Mục đích

Trình bày đầy đủ kết quả của K-Means, Ward và PCA + K-Means.

Bao gồm assignments, profiles và metrics.

## Phần 13.4 — Báo cáo temporal stability

### Mục đích

Trình bày sự thay đổi cụm theo thời gian.

Tổng hợp ARI, NMI, persistence, migration, transitions và centroid drift.

## Phần 13.5 — Báo cáo holdout

### Mục đích

Thể hiện methodology hoạt động thế nào trên giai đoạn chưa dùng để tuning.

Bao gồm quality holdout, temporal holdout, development vs holdout và limitations.

## Phần 13.6 — Báo cáo hạn chế

### Mục đích

Tránh overclaim.

Phải ghi rõ M2 là market-only experiment, independent monthly clustering chưa phải Dynamic Clustering, DBSCAN chưa thuộc M2 v1, GMM chưa hoàn thiện và M2 chưa đánh giá hiệu quả đầu tư.

## File code sử dụng trong nhiệm vụ và cách dùng

Phần này giải thích các file đã có trong repo, vai trò của từng file và cách chúng được gọi trong nhiệm vụ. Người thực hiện không cần chạy từng file \`.py\` riêng lẻ; thông thường \`runner.py\` hoặc entry point của experiment sẽ import/gọi các module còn lại.

**\`src/delta_t1/experiments/reporting.py\`** — file đã có; file chính hỗ trợ báo cáo.

> Mục đích: Cung cấp hàm tạo bảng CSV, plot và report.
>
> Cách dùng trong nhiệm vụ này: Đọc artifact đã verify và tạo báo cáo, không chạy lại clustering.

**\`src/delta_t1/experiments/runner.py\`** — file đã có; nguồn report/manifest gốc.

> Mục đích: Mỗi experiment run đã có report/manifest và các artifact liên quan.
>
> Cách dùng trong nhiệm vụ này: Dùng chúng làm evidence cho báo cáo tổng M2.

**\`assignments.jsonl\`, \`profiles.jsonl\`, \`diagnostics.jsonl\`, \`stability.jsonl\`, \`transitions.jsonl\`, \`models/\`, manifest** — artifact do runner tạo; không phải file code.

> Mục đích: Là dữ liệu thực tế để báo cáo Global K, cluster profile, temporal stability và holdout.
>
> Cách dùng trong nhiệm vụ này: Đọc và tổng hợp; không chỉnh sửa trực tiếp artifact đã hoàn tất.

**Các tài liệu trong \`docs/\` như \`DELTA_UNIFIED_PROJECT_PLAN.md\`, \`METHODOLOGY.md\`, \`EXPERIMENT_PROTOCOL.md\`** — tài liệu phương pháp.

> Mục đích: Giúp mô tả đúng protocol, giới hạn và phạm vi M2.
>
> Cách dùng trong nhiệm vụ này: Đối chiếu nội dung báo cáo với methodology đã freeze để tránh báo cáo khác với cách thực nghiệm thực sự.

### Cách các file phối hợp

> verified artifacts + protocol docs → reporting.py → report/notebook/handoff M3.

## Kết quả cần đạt của Nhiệm vụ 13

- report;

- notebook;

- methodology description;

- selected Global K;

- comparator results;

- cluster profiles;

- temporal results;

- holdout results;

- limitations;

- handoff package M3.

## Vị trí trong repo & Đường dẫn output

- **Code tổng kết & Handoff**: `M2/notebooks/13_m2_m3_handoff_summary.py` (script tổng kết bàn giao; hoặc `13_m2_m3_handoff_summary.ipynb`)
- **Mô hình bàn giao chính thức cho M3**: `M2/models/final_selected_model/` (gói model chuẩn hóa của 1 mô hình tốt nhất được chọn sau Task 10 và Holdout Task 11)
- **Báo cáo tổng kết & Bàn giao (Reports)**: `M2/reports/Bao_cao_tong_ket_M2_Ban_giao_M3.docx` (hoặc `.md`, slide báo cáo tổng kết M2)
- **Gói Artifact bàn giao hoàn chỉnh**: `M2/artifacts/m2-final-handoff-v1/` (lưu trong M2 để push lên GitHub)

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
