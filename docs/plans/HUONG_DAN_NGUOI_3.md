# Hướng dẫn thực hiện công việc — Người 3

**Phạm vi phụ trách:** Backend FastAPI Read-only và Công cụ xác thực API.  
**Tổng số nhiệm vụ:** 15 tasks.  
**Tài liệu tham chiếu:** [Kế hoạch tổng thể](KE_HOACH_TRIEN_KHAI_B_PIT_VA_DANH_GIA_DAU_TU.md) · [PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json](PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json).

---

## Bảng tiến độ Người 3

> Cập nhật một dòng ngay khi bắt đầu hoặc hoàn tất task. `PASS` chỉ được ghi sau khi
> targeted test và self-review đạt; mỗi task hoàn tất có đúng một commit riêng.

| Task | Giai đoạn | Trạng thái | Commit | Ghi chú ngắn |
|---|---|---|---|---|
| R3-14 | S3 | PASS | `feat(assessment): Xây dựng validator kiểm tra toàn vẹn artifact` | Unit + integration + artifact thật đều PASS; commit SHA ghi trong `git log`. |
| R3-01 | S4 | PASS | `feat(assessment): Cấu hình đọc bản phát hành Assessment` | Config và resolver đều pin run cụ thể; test + resolve artifact thật PASS. |
| R3-02 | S4 | PASS | `feat(assessment): Kiểm manifest khi mở artifact phục vụ API` | Manifest, hash file serving và pin nguồn/revision được fail-closed. |
| R3-07 | S4 | PASS | `feat(assessment): Khai báo response schema Assessment` | Schema 18 features, context/status, evidence/peer/history và query guard PASS. |
| R3-03 | S4 | PASS | `feat(assessment): Nạp payload Assessment theo schema` | Nạp bốn payload read-only, giữ null và chặn schema/verdict sai. |
| R3-04 | S4 | PASS | `feat(assessment): Tra cứu đúng mã và ngữ cảnh phát hành` | Phân biệt READY/INSUFFICIENT_EVIDENCE/NOT_FOUND và chặn override release. |
| R3-08 | S4 | PASS | `feat(assessment): Reader artifact read-only` | Repository chỉ mở release pin; unavailable khác ticker không tồn tại. |
| R3-05 | S4 | PASS | `feat(assessment): Gắn repository vào vòng đời FastAPI` | Lifespan injection PASS; thiếu artifact không làm app dừng. |
| R3-06 | S4 | CHƯA MỞ | — | Chờ R3-08 và R3-07. |
| R3-09 | S4 | CHƯA MỞ | — | Chờ R3-05 và R3-06. |
| R3-10 | S4 | CHƯA MỞ | — | Chờ R3-09. |
| R3-11 | S4 | CHƯA MỞ | — | Chờ R3-10. |
| R3-12 | S4 | CHƯA MỞ | — | Chờ R3-11. |
| R3-13 | S4 | CHƯA MỞ | — | Chờ R3-12. |
| R3-15 | S4 | CHƯA MỞ | — | Chờ R3-13. |

---

## Quy chuẩn làm việc và Commit (Bắt buộc)

1. **Nguyên tắc Atomic Commit (1 Task = ĐÚNG 1 Commit riêng biệt):**
   - Mỗi task là một đơn vị tính năng độc lập. Khi hoàn thành và chạy test pass theo tiêu chuẩn nghiệm thu, **bắt buộc thực hiện commit ngay task đó**.
   - Tuyệt đối **KHÔNG gộp nhiều task vào một commit lớn** để đảm bảo lịch sử phát triển minh bạch, dễ dàng theo dõi tiến độ và thuận tiện rollback khi có sự cố.
2. **Cú pháp commit:** Sử dụng chính xác câu lệnh commit chuẩn đã đính kèm sẵn trong từng task bên dưới.
3. **Trình tự thực hiện:** Làm tuần tự từng task, nghiệm thu xong task hiện tại và commit xong thì mới chuyển sang task tiếp theo.

---

## Chuẩn bị Dữ liệu (Bắt buộc trước khi chạy)

Do tệp cơ sở dữ liệu `indicators.sqlite` có dung lượng ~106 MB (vượt giới hạn 100 MB của GitHub), thư mục `data/` được đưa vào `.gitignore`. Người 1 đã xuất và đóng gói toàn bộ dữ liệu làm giàu và đánh giá.

Bạn chuẩn bị dữ liệu bằng **1 trong 2 cách sau**:
* **Cách 1 (Nhanh nhất & Khuyên dùng):** Tải file `data.zip` (~40 MB do Người 1 bàn giao tại thư mục `Downloads/data.zip` hoặc trên Google Drive / nhóm chat), giải nén vào thư mục gốc của repo sao cho đường dẫn là `data/...`.
* **Cách 2 (Tự sinh từ baseline):** Nếu máy bạn đã có sẵn thư mục `data` gốc baseline, mở terminal chạy 3 lệnh sau để tự sinh toàn bộ dữ liệu trong 30 giây:
  ```powershell
  $env:PYTHONPATH="src"
  python scripts/build_enriched_indicators.py
  python scripts/build_financial_pit_clusters_enriched.py
  python scripts/build_investment_assessment_v1.py
  ```

---

---

## Danh mục các nhiệm vụ chi tiết

### Task 01 (R3-01) — Cấu hình đọc bản phát hành Assessment

- **Giai đoạn:** Stage S4
- **File can thiệp:** `configs/product/assessment_release_v1.json`, `src/delta_t1/product/assessment_repository.py`
- **Nội dung công việc:** Khai báo pointer tới artifact Assessment đã verify, release context và revision. Reader resolve đường dẫn từ cấu hình, kiểm trường bắt buộc và phân biệt chưa có bản phát hành; không sửa model/data nguồn.
- **Tiêu chuẩn nghiệm thu:** Cấu hình hợp lệ resolve đúng artifact; pointer thiếu hoặc không tồn tại được báo trạng thái chưa sẵn sàng, không tự chọn baseline hoặc run mới nhất.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_release_config.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add configs/product/assessment_release_v1.json src/delta_t1/product/assessment_repository.py
  git commit -m "feat(assessment): Cấu hình đọc bản phát hành Assessment"
  ```

### Task 02 (R3-02) — Kiểm manifest khi mở artifact phục vụ API

- **Giai đoạn:** Stage S4
- **File can thiệp:** `src/delta_t1/product/assessment_repository.py`
- **Nội dung công việc:** Khi reader mở bản phát hành, đối chiếu manifest, hashes của các file cần phục vụ và source/policy revision. Dùng evidence đã bàn giao, không chạy lại imputation hoặc kiểm lại donor median.
- **Tiêu chuẩn nghiệm thu:** File bị sửa, thiếu hoặc khác revision bị từ chối trước serving; artifact đúng được mở read-only. Không tạo một lượt audit enrichment riêng.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_manifest_reader.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/product/assessment_repository.py
  git commit -m "feat(assessment): Kiểm manifest khi mở artifact phục vụ API"
  ```

### Task 03 (R3-03) — Nạp payload Assessment theo schema

- **Giai đoạn:** Stage S4
- **File can thiệp:** `src/delta_t1/product/assessment_repository.py`
- **Nội dung công việc:** Đọc assessments, peer_benchmarks, coverage và feature_history từ bản phát hành; parse types/status/null theo contract. Giữ nguyên dữ liệu và provenance đã build, không tính lại features, Peers hoặc verdict.
- **Tiêu chuẩn nghiệm thu:** Payload hợp lệ nạp đúng; bản ghi thiếu required, sai status hoặc không tương thích schema bị phát hiện. Null không biến thành0.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_payload_reader.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/product/assessment_repository.py
  git commit -m "feat(assessment): Nạp payload Assessment theo schema"
  ```

### Task 04 (R3-04) — Tra cứu đúng mã và ngữ cảnh phát hành

- **Giai đoạn:** Stage S4
- **File can thiệp:** `src/delta_t1/product/assessment_repository.py`
- **Nội dung công việc:** Bổ sung lookup theo ticker, assessment_context, as_of, required_price_session và revision. Phân biệt mã không tồn tại với mã tồn tại nhưng thiếu bằng chứng; đọc kết quả đã có, không suy nhãn.
- **Tiêu chuẩn nghiệm thu:** Lookup trả đúng mã/ngày/context/revision; demo không được trả như current, mã thiếu dữ liệu không bị coi là mã không tồn tại.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_lookup.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/product/assessment_repository.py
  git commit -m "feat(assessment): Tra cứu đúng mã và ngữ cảnh phát hành"
  ```

### Task 05 (R3-05) — Gắn repository vào vòng đời FastAPI

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/main.py`
- **Nội dung công việc:** Khởi tạo repository theo cấu hình trong lifespan/app state và hỗ trợ dependency injection cho tests. Giữ các endpoint cũ hoạt động khi chưa có artifact Assessment; quản lý tài nguyên đọc đúng vòng đời.
- **Tiêu chuẩn nghiệm thu:** App khởi động khi artifact vắng; dịch vụ Assessment biểu thị chưa sẵn sàng, không làm hỏng API hiện hữu. Tests dùng repository fixture được inject rõ.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_lifespan.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/main.py
  git commit -m "feat(assessment): Gắn repository vào vòng đời FastAPI"
  ```

### Task 06 (R3-06) — Ánh xạ payload sang response API

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/assessment.py`
- **Nội dung công việc:** Mapper chuyển payload offline sang response Pydantic, bổ sung request_time của lần gọi và giữ nguyên as_of/context/nhãn/evidence từ bản phát hành. Không tạo rationale, Peers hoặc kết luận mới trong request.
- **Tiêu chuẩn nghiệm thu:** Response giữ nguyên nội dung quyết định, dates/status/nguồn đúng; request_time cập nhật riêng, payload dùng cache không giữ metadata request cũ.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_response_mapper.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/assessment.py
  git commit -m "feat(assessment): Ánh xạ payload sang response API"
  ```

### Task 07 (R3-07) — Khai báo response schema Assessment

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/schemas.py`
- **Nội dung công việc:** Thêm Pydantic response cho dates/context/status, A/B profiles,18features, evidence, Peers, history và references. Ánh xạ đúng offline artifact, giữ hợp đồng API cũ.
- **Tiêu chuẩn nghiệm thu:** Fixture hợp lệ parse được; invalid status hoặc thiếu required bị bắt; null khác0, public API không nhận as_of tùy ý.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_response_models.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/schemas.py
  git commit -m "feat(assessment): Khai báo response schema Assessment"
  ```

### Task 08 (R3-08) — Reader artifact read-only

- **Giai đoạn:** Stage S4
- **File can thiệp:** `src/delta_t1/product/assessment_repository.py`
- **Nội dung công việc:** Reader kiểm manifest/hash/policy/source pins rồi tra theo ticker/as_of/context/revision. Phân biệt chưa phát hành, ticker không tồn tại, thiếu evidence và corruption.
- **Tiêu chuẩn nghiệm thu:** Không network/write/recompute; sai nguồn không fallback baseline hoặc tráo demo/current; absent artifact khác unknown ticker.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_repository.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add src/delta_t1/product/assessment_repository.py
  git commit -m "feat(assessment): Reader artifact read-only"
  ```

### Task 09 (R3-09) — Đăng ký endpoint đánh giá

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/assessment.py`, `web/backend/app/main.py`
- **Nội dung công việc:** Đăng ký GET stock assessment, repository injection/lifespan, release context cố định và request_time. Dùng revision middleware hiện có, không lấy nhãn từ legacy overview/peers.
- **Tiêu chuẩn nghiệm thu:** App vẫn khởi động khi chưa có artifact và endpoint trả503; đúng ticker/context/date, không crawl/fit/build trong request.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_api.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/assessment.py web/backend/app/main.py
  git commit -m "feat(assessment): Đăng ký endpoint đánh giá"
  ```

### Task 10 (R3-10) — Projection lịch sử 5/10 năm

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/assessment.py`, `src/delta_t1/product/assessment_repository.py`
- **Nội dung công việc:** Nhận lookback_years5/10, mặc định10; đọc và cắt feature_history từ as_of. Giữ nguyên verdict, evidence quyết định và peer_basis; dùng endpoint stock assessment đã chốt.
- **Tiêu chuẩn nghiệm thu:** Đổi lookback chỉ đổi history; giá trị khác trả422, không lọt FY tương lai hoặc nội suy khoảng trống.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_history_api.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/assessment.py src/delta_t1/product/assessment_repository.py
  git commit -m "feat(assessment): Projection lịch sử 5/10 năm"
  ```

### Task 11 (R3-11) — HTTP errors và khóa revision

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/assessment.py`, `web/backend/app/main.py`
- **Nội dung công việc:** Ánh xạ200 cho mã tồn tại nhưng insufficient,404 unknown,409 revision mismatch,422 invalid query và503 unpublished. Kiểm ticker/path/SQL injection và compatibility source/policy.
- **Tiêu chuẩn nghiệm thu:** HTTP matrix đúng, không query tùy ý theo input ticker; existing endpoints giữ meaning và dữ liệu hỏng không thành verdict hợp lệ.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_api.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/assessment.py web/backend/app/main.py
  git commit -m "feat(assessment): HTTP errors và khóa revision"
  ```

### Task 12 (R3-12) — Cache đúng context và nguồn

- **Giai đoạn:** Stage S4
- **File can thiệp:** `web/backend/app/assessment_cache.py`, `web/backend/app/assessment.py`
- **Nội dung công việc:** Cache bounded với key ticker/context/as_of/required session/evidence cutoff/lookback/policy/bundle revision. Request_time cập nhật riêng; invalidate khi artifact/model/rule/date đổi.
- **Tiêu chuẩn nghiệm thu:** Demo/current không dùng nhầm payload; cache hit không giữ request_time cũ; có ca key mismatch và eviction.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_cache.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add web/backend/app/assessment_cache.py web/backend/app/assessment.py
  git commit -m "feat(assessment): Cache đúng context và nguồn"
  ```

### Task 13 (R3-13) — Integration API và regression

- **Giai đoạn:** Stage S4
- **File can thiệp:** `tests/integration/test_assessment_endpoints.py`, `tests/unit/test_terminal_api.py`
- **Nội dung công việc:** Integration trên injected fixtures và verified artifact; kiểm revision/cache/error/payload/read-only, chặn network/fit calls. Giữ Overview/Fundamentals/Scores/Peers cũ.
- **Tiêu chuẩn nghiệm thu:** Có test thực chạy và ghi rõ skip; payload lỗi bị từ chối, không legacy fallback hoặc thay nghĩa endpoint hiện có.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/integration -p 'test_assessment_endpoints.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add tests/integration/test_assessment_endpoints.py tests/unit/test_terminal_api.py
  git commit -m "feat(assessment): Integration API và regression"
  ```

### Task 14 (R3-14) — Xây dựng validator kiểm tra toàn vẹn artifact

- **Giai đoạn:** Stage S3
- **File can thiệp:** `scripts/verify_investment_assessment_v1.py`
- **Nội dung công việc:** Xây dựng CLI tool scripts/verify_investment_assessment_v1.py để backend tự động kiểm tra tính toàn vẹn của artifact (files, manifest, hash, schema, whitelist 18, không rò rỉ tương lai) trước khi nạp serving.
- **Tiêu chuẩn nghiệm thu:** Tool phát hiện đúng sai lệch dữ liệu, thiếu file hoặc hash không khớp; xuất verification.json làm điều kiện khởi động backend an toàn.
- **Lệnh kiểm tra / Test:**
  ```powershell
  & $py -m unittest discover -s tests/unit -p 'test_assessment_release_verifier.py' -v
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add scripts/verify_investment_assessment_v1.py
  git commit -m "feat(assessment): Xây dựng validator kiểm tra toàn vẹn artifact"
  ```

### Task 15 (R3-15) — Xuất OpenAPI và smoke API

- **Giai đoạn:** Stage S4
- **File can thiệp:** `docs/api/OPENAPI_ASSESSMENT_SPEC.json`, `web/README.md`
- **Nội dung công việc:** Xuất OpenAPI từ app version thực, examples và HTTP matrix. Smoke với artifact Assessment đã verify, ghi revision/context/pins và lệnh tái lập.
- **Tiêu chuẩn nghiệm thu:** Spec parse được, examples và response đúng artifact; không ghi đã deploy khi mới nghiệm thu local.
- **Lệnh kiểm tra / Test:**
  ```powershell
  git diff --check
  ```
- **Lệnh Git Commit sau khi hoàn thành:**
  ```bash
  git add docs/api/OPENAPI_ASSESSMENT_SPEC.json web/README.md
  git commit -m "feat(assessment): Xuất OpenAPI và smoke API"
  ```
