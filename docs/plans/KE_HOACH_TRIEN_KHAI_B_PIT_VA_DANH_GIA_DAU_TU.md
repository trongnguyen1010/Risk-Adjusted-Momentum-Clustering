# DELTA — Kế hoạch phân công triển khai B-PIT và đánh giá đầu tư

**Phiên bản:** 3.1 · **Trạng thái:** Bản phân công để review · **Baseline:** `feature/indicators-v1@1751e9c`.

Tài liệu chia nhỏ công việc cho Người 1–4 từ hai kế hoạch nguồn đã có. Các quy tắc, phạm vi, artifact và điều kiện chuyển bước tuân theo tài liệu nguồn; việc chia nhiệm vụ không tạo quyết định phương pháp mới.

## 1. Tài liệu áp dụng

- [Kế hoạch làm giàu dữ liệu B-PIT và backtest M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md): thực hiện A → B → C → D → E → F.
- [Kế hoạch Output Investment Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md): sau bàn giao F thực hiện S1 → S2 → S3 → S4 → S5 → S6; S0 đã chốt trong nguồn.
- [AGENTS.md](../../AGENTS.md) và [CONTRIBUTING.md](../../CONTRIBUTING.md): ranh giới code, test, evidence và quy trình thực hiện.

[Bản phân công có cấu trúc cho AI](PHAN_CONG_CONG_VIEC_B_PIT_VA_DANH_GIA_DAU_TU.json) ghi cùng task IDs, người phụ trách, dependency, file, nguồn tham chiếu và kiểm tra. Người thực hiện đọc task của mình cùng đúng mục nguồn trước khi code.

## 2. Phân công Người 1–4

| Người | Phần phụ trách | Mã công việc | Bàn giao chính |
|---|---|---|---|
| **Người 1** | Nguồn dữ liệu, enrichment, B-PIT, notebook và builder Assessment | [HUONG_DAN_NGUOI_1.md](HUONG_DAN_NGUOI_1.md) (R1-01…20) | SQLite/audit C; labels/models D; notebook; Assessment artifacts S3 |
| **Người 2** | Loader/config/feasibility M3, backtest/seal và rulebook | [HUONG_DAN_NGUOI_2.md](HUONG_DAN_NGUOI_2.md) (R2-01…15) | Runs/seals/config/pins; bảng đối sánh; policy/rules/verdict/rationale |
| **Người 3** | Backend read-only và validator Assessment | [HUONG_DAN_NGUOI_3.md](HUONG_DAN_NGUOI_3.md) (R3-01…15) | Release reader; schema/API/revision/cache; validator Assessment và OpenAPI |
| **Người 4** | Báo cáo F, giao diện, UAT và hướng dẫn | [HUONG_DAN_NGUOI_4.md](HUONG_DAN_NGUOI_4.md) (R4-01…15) | Hồ sơ bàn giao F; tab Assessment; UI evidence; hướng dẫn/limitations |

Người 1–4 là định danh thành viên trong kế hoạch. Nhóm tự gắn họ tên tương ứng; owner và mã nhiệm vụ giữ nguyên.

### Người 1

1. R1-01..06 thực hiện A/B/C: kiểm môi trường/nguồn, eligibility, median, engine, SQLite dẫn xuất và audit.
2. R1-07..13 thực hiện D: cohort/loader, bốn phương án mô hình, metrics, screening/validation, artifacts và notebook; Người 1 tự chạy kiểm tra cutoff/FIT/leakage/replay theo nguồn, phối hợp loader M3 của Người 2.
3. Sau F, R1-14..15 làm S1: nhận đúng pin, chọn input và Peers.
4. Sau S2 của Người 2, R1-16..20 làm S3: history/coverage, orchestrator/CLI, deterministic manifest và nghiệm thu bằng verifier của Người 3.

### Người 2

1. R2-01 phối hợp D để loader M3 nhận đủ k/order/cutoff.
2. R2-02..09 làm E: nguồn SQLite/config/feasibility/tests/verifier, targets và LOCKED, Dev seal rồi Holdout seal cùng execution SHA.
3. R2-10 cung cấp bảng đối sánh M3 cho F; không thay mô hình bằng kết quả danh mục.
4. Sau S1, R2-11..15 làm S2: policy D-ASS-01, market/financial rules, priority verdict và rationale; giao interface deterministic cho builder của Người 1.

### Người 3

1. R3-14 làm verifier Assessment trong S3 theo mục9.2 của kế hoạch Output; đây là verifier của sản phẩm offline, không phải một đợt kiểm lại dữ liệu enrichment.
2. Sau S3 đạt, R3-01..04/07/08 làm phần đọc bản phát hành: config/pointer, manifest, payload/schema, lookup và repository read-only.
3. R3-05/06/09..13/15 làm lifecycle/response mapper, endpoint, history projection, HTTP/revision/cache, integration và OpenAPI; giao contract cho Người 4.
4. Kiểm đầu vào, median, SQLite dẫn xuất và B-PIT ở B/C/D do Người 1 thực hiện cùng pipeline. Người 3 chỉ kiểm artifact ở điểm mở dịch vụ theo hợp đồng serving.

### Người 4

1. R4-01..03 làm F từ evidence đã verify: báo cáo B-PIT/M3, mục công việc còn lại, pin/run IDs và hồ sơ nhận dữ liệu cho Assessment.
2. Sau S4, R4-04..13 làm S5: types, verdict/availability, một chart, lookback, Peers, bảng18features, rationale/nguồn, panel/tab/API/URL.
3. R4-14..15 làm S6: UAT, regression, hướng dẫn sử dụng và hồ sơ nghiệm thu. Thực hiện release theo điều kiện/approval của nguồn.

## 3. Thứ tự và điều kiện bàn giao

| Giai đoạn | Đầu ra / điều kiện chuyển bước |
|---|---|
| **A** — Khóa môi trường và baseline | Môi trường import được, pip check sạch, tests M3 và dung lượng đạt theo kế hoạch làm giàu mục2. |
| **B** — Nhận và kiểm dữ liệu | Đủ nguồn bắt buộc, hash/schema/integrity/readiness đúng theo mục3. |
| **C** — Làm giàu9chỉ số | Audit từng ô, median/cohort/DB invariants và manifest đúng theo mục4. |
| **D** — Sàng lọc và kiểm định B-PIT | Artifacts/cohort/cutoff/fit_leaks/compatibility đạt; owner review cấu hình và tác động Va trước E theo mục5. |
| **E** — Feasibility và backtest M3 | Targets/LOCKED/Devseal/Holdoutseal cùng HEAD/config/inputs; checks đạt theo mục6. |
| **F** — Đối sánh và bàn giao | Bộ C/D/E có report/status/config/commit/hashes/run IDs và nơi nhận theo mục7; Assessment nhận đúng nguồn mục6.4. |
| **S1** — Contract, eligibility và Peers | Chỉ bắt đầu sau F; pin/provenance/18features/Peers/fixtures đạt theo Assessment mục14/S1. |
| **S2** — Rulebook D-ASS-01 | Policy versioned và bảng conditions/priority/boundaries được kiểm thử, nghiệm thu theo mục8.3 và14/S2. |
| **S3** — Builder và QA offline | Assessment artifact, independent verifier, coverage và replay đạt theo mục9.3 và14/S3. |
| **S4** — Backend read-only | API/schema/revision và contract200/404/409/422/503 đạt theo mục10 và14/S4. |
| **S5** — Frontend stocks | Tab thứ5, một chart18features,5/10năm,Peers/nguồn/URL/mobile đạt theo mục11 và14/S5. |
| **S6** — UAT và bàn giao | Smoke/UAT demo và các cases mục17 đạt, evidence/limitations đầy đủ; release theo quyền đã duyệt trong kế hoạch nguồn. |

- Thực hiện một stage đã mở trong mỗi AI session theo AGENTS.md. ID task dùng để theo dõi, không có nghĩa phải làm theo thứ tự số tăng nếu dependency chưa sẵn sàng.
- Có thể đọc code, chuẩn bị fixture và kiểm interface của phần phụ trách trong lúc chờ đầu vào. Việc chuẩn bị không mở gate, không chứng nhận PASS dữ liệu thật và không thay yêu cầu S1 sau F.
- D giữ `MANUAL_REVIEW_REQUIRED` ở đúng điểm nguồn yêu cầu owner review. E chỉ nhận cấu hình đã được chấp thuận; không tự promote.
- Full Dev/Holdout chạy cùng frozen code/config/input pins. Không commit thay code/config giữa hai full runs; seal là file riêng. Ghi receipts sau hai run; khi phải sửa code thì tạo SHA/run mới theo kiểm tra liên quan.

## 4. Quy tắc giữ nguyên khi thực hiện

- **Enrichment C:** FY2017–2024,9 chỉ số cùng một lượt; median từng FY/metric từ đúng baseline FIT đủ9/9 trước transform. CFO chỉ điền khi CFO thiếu và NI quan sát dương; ROE tuân công thức vốn chủ. Giữ F/Z, usable dates, observed và FY ngoài scope.
- **B-PIT D:** cutoff/cohort baseline được pin; T1 và model/PCA/profile/order chỉ fit FIT.24cặp, selection2017–2022, validation2023–2024, k3 đối chứng, criteria/tie-break/late assignment đúng mục5 nguồn. Không dùng lợi suất/Sharpe để chọn model.
- **M3 E:** cùng SQLite enriched cho scoring/ngành/manifest; giữ A/Va/Q-date/18tháng/rank/calendar/basis/cost/execution. Feasibility → targets cảhai đoạn → LOCKED → Dev seal → Holdout seal; không Sharpe ở Dev/Holdout.
- **Assessment:** nhận đúng cặp enriched theo6.4; demo as_of2026-01-02 và price session2025-12-31. Chỉ9A+9B, bốn trạng thái, Peers đúng metric/ngưỡng3; Peers không đổi verdict. Dùng policy imputed đã duyệt theo6.4.3, không tự suy từ opt-in M3.
- **Thời điểm và độ mới:** giá phải đúng phiên giao dịch hoàn tất gần nhất tại as_of; A theo chu kỳ snapshot tháng và lịch phát hành đã nghiệm thu, không dùng ngưỡng cứng22/23phiên. Thiếu kỳ A đã đến hạn thì chỉ tham khảo, không verdict. B-PIT kiểm usable/cutoff/FY và18tháng; FY usable mới nhất chưa có model không tự lùi năm cũ, theo Assessment5.2/7.3/16.1.
- **Artifact/API/UI:** chỉ các outputs và endpoint stock assessment trong nguồn9.3/10.1; runtime đọc artifact, không crawl/fit/recompute. Một vùng chart, selector18 và5/10năm; không đổi verdict khi đổi phần trình bày. Giữ hợp đồng website hiện hữu.
- **Code và evidence:** `clustering` fit/predict, `evaluation` metrics, `experiments` orchestrate/build, `product/web` read-only. Notebook điều phối B-PIT; giữ entrypoint enriched của D.1, dùng chung logic và giữ baseline read-only.

### Ownership file dùng chung

| Phần | Người sửa chính |
|---|---|
| Enrichment helpers, B-PIT builder/config, notebook, Assessment input/Peers/history/orchestrator/CLI | Người 1 |
| M3 inputs/runner/feasibility/config/verifier/exporter; Assessment policy/rules/verdict/rationale | Người 2 |
| Product reader; backend main/schema/assessment/cache/OpenAPI; verifier Assessment S3 | Người 3 |
| Frontend/types/API client; REPORT_BACKTEST, hướng dẫn, README/index | Người 4 |
| Decisions/Changelog khi contract hoặc behavior đổi | Người thực hiện chuẩn bị cùng PR; phối hợp Người 4 tích hợp phần tài liệu, không chờ tới cuối mới ghi quyết định |

Đường dẫn module/helper/test ở các thẻ là dự kiến cho implementation. Trước khi tạo mới phải kiểm code có thể tái sử dụng; không tách thêm pipeline hoặc copy logic. `FE` = `src/delta_t1/features/financial_enrichment/`, `AE` = `src/delta_t1/experiments/assessment/`; orchestrator chính dùng `src/delta_t1/experiments/investment_assessment_v1.py` theo nguồn9.2.

### Phụ trách kiểm tra theo pipeline

Người 1 thực hiện kiểm file/hash/schema/integrity tại B, kiểm median/ô điền/baseline tại C và kiểm cutoff/FIT/leakage/model replay tại D trong chính công việc của mình. Các kiểm tra là điều kiện chuyển bước có sẵn của nguồn, không tạo một vai trò audit dữ liệu thứ hai. Người 2 kiểm nguồn và execution của M3; Người 3 kiểm artifact khi phục vụ API và giữ verifier Assessment S3 theo kế hoạch Output.

## 5. Danh mục nhiệm vụ

### Người 1 — Dữ liệu tài chính, B-PIT và builder Assessment

| ID | Giai đoạn | Công việc | Dependency |
|---|---|---|---|
| R1-01 | A | Khóa môi trường và baseline | Baseline đã chốt |
| R1-02 | B | Kiểm kê và pin đầu vào | R1-01 |
| R1-03 | C | Phân loại các ô đủ điều kiện làm giàu | R1-02 |
| R1-04 | C | Tính median từ tập FIT gốc | R1-03 |
| R1-05 | C | Điền giá trị và ghi lineage theo ô | R1-04 |
| R1-06 | C | Xuất SQLite dẫn xuất và audit | R1-05 |
| R1-07 | D | Chuẩn hóa cohort và loader enriched | R1-06 |
| R1-08 | D | Thực hiện K-Means và PCA + K-Means | R1-07 |
| R1-09 | D | Thực hiện Ward và GMM | R1-08 |
| R1-10 | D | Tính chất lượng và độ ổn định cụm | R1-08, R1-09 |
| R1-11 | D | Sàng lọc và khóa cấu hình chung | R1-10 |
| R1-12 | D | Xuất mô hình, labels và manifest B-PIT | R1-11 |
| R1-13 | D | Hoàn thiện notebook chạy và bàn giao B-PIT | R1-12, R2-01 |
| R1-14 | S1 | Nhận pin và chọn input Assessment | R4-03, R2-10 |
| R1-15 | S1 | Tạo Peers theo từng đặc trưng | R1-14 |
| R1-16 | S3 | Dựng lịch sử và coverage | R1-15, R2-15 |
| R1-17 | S3 | Nối engine đánh giá offline | R1-16, R2-15 |
| R1-18 | S3 | Bổ sung CLI build Assessment | R1-17 |
| R1-19 | S3 | Khóa manifest và deterministic payload | R1-18 |
| R1-20 | S3 | Nghiệm thu builder trên bộ bàn giao thật | R1-19, R3-14 |

### Người 2 — Tích hợp M3, backtest và rulebook

| ID | Giai đoạn | Công việc | Dependency |
|---|---|---|---|
| R2-01 | D | Sửa loader M3 nhận đủ k cụm | R1-07 |
| R2-02 | E | Truyền nguồn enriched xuyên runner | R1-13 |
| R2-03 | E | Tạo config thử nghiệm và cache riêng | R2-02 |
| R2-04 | E | Thêm --config cho feasibility | R2-03 |
| R2-05 | E | Mở rộng regression giá/cutoff/targets | R2-04 |
| R2-06 | E | Chuẩn bị verifier và seal hai đoạn | R2-05 |
| R2-07 | E | Feasibility thật, targets-only và khóa config | R1-13, R2-06 |
| R2-08 | E | Chạy và seal Development | R2-07 |
| R2-09 | E | Chạy và seal Holdout | R2-08 |
| R2-10 | F | Xuất đối sánh M3 theo segment | R2-09 |
| R2-11 | S2 | Mã hóa policy D-ASS-01 | R1-15 |
| R2-12 | S2 | Hiện thực điều kiện thị trường | R2-11 |
| R2-13 | S2 | Hiện thực tài chính và dòng tiền | R2-11 |
| R2-14 | S2 | Kết hợp eligibility và bốn verdict | R1-14, R2-12, R2-13 |
| R2-15 | S2 | Dựng rationale và counter-evidence | R2-14, R1-15 |

### Người 3 — Backend read-only và verifier Assessment

| ID | Giai đoạn | Công việc | Dependency |
|---|---|---|---|
| R3-01 | S4 | Cấu hình đọc bản phát hành Assessment | R1-20 |
| R3-02 | S4 | Kiểm manifest khi mở artifact phục vụ API | R3-01 |
| R3-03 | S4 | Nạp payload Assessment theo schema | R3-02, R3-07 |
| R3-04 | S4 | Tra cứu đúng mã và ngữ cảnh phát hành | R3-03 |
| R3-05 | S4 | Gắn repository vào vòng đời FastAPI | R3-08 |
| R3-06 | S4 | Ánh xạ payload sang response API | R3-08, R3-07 |
| R3-07 | S4 | Khai báo response schema Assessment | R1-20 |
| R3-08 | S4 | Reader artifact read-only | R3-04, R3-07 |
| R3-09 | S4 | Đăng ký endpoint đánh giá | R3-05, R3-06 |
| R3-10 | S4 | Projection lịch sử 5/10 năm | R3-09 |
| R3-11 | S4 | HTTP errors và khóa revision | R3-10 |
| R3-12 | S4 | Cache đúng context và nguồn | R3-11 |
| R3-13 | S4 | Integration API và regression | R3-12 |
| R3-14 | S3 | Xây dựng validator kiểm tra toàn vẹn artifact | R1-19 |
| R3-15 | S4 | Xuất OpenAPI và smoke API | R3-13 |

### Người 4 — Đối sánh, frontend và tài liệu

| ID | Giai đoạn | Công việc | Dependency |
|---|---|---|---|
| R4-01 | F | Tổng hợp đối sánh B-PIT | R1-13, R1-06 |
| R4-02 | F | Tổng hợp đối sánh M3 | R4-01, R2-10 |
| R4-03 | F | Hoàn tất hồ sơ bàn giao và tài liệu liên quan | R4-02 |
| R4-04 | S5 | Types và trạng thái dữ liệu frontend | R3-15 |
| R4-05 | S5 | Verdict và availability states | R4-04 |
| R4-06 | S5 | Một biểu đồ chuyển đổi chỉ số | R4-04 |
| R4-07 | S5 | Lookback và thông tin coverage | R4-06 |
| R4-08 | S5 | Bảng Peers theo đặc trưng | R4-04 |
| R4-09 | S5 | Bảng chi tiết 18 đặc trưng | R4-04 |
| R4-10 | S5 | Giải thích tín hiệu và rủi ro | R4-05 |
| R4-11 | S5 | Nguồn và chất lượng dữ liệu | R4-09, R4-10 |
| R4-12 | S5 | Ghép panel đánh giá | R4-05, R4-07, R4-08, R4-09, R4-10, R4-11 |
| R4-13 | S5 | Tab, API và URL state | R4-12, R3-15 |
| R4-14 | S6 | UAT và regression giao diện | R4-13, R1-20 |
| R4-15 | S6 | Hướng dẫn và hồ sơ nghiệm thu | R4-14, R3-15 |

## 6. Thẻ triển khai chi tiết

Đọc nguồn tham chiếu và dependency trước mỗi thẻ. Test/file chưa có trong checkout là đầu ra cần tạo, không phải bằng chứng đã triển khai. Command chạy0test hoặc chỉskip không phải PASS. `$py` là Python/kernel đã xác minh tại A; cấu hình PYTHONPATH theo repo. Mọi task đang ở trạng thái PLANNED.

### R1-01 — Khóa môi trường và baseline

- **Người phụ trách:** Người 1. **Giai đoạn:** A.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 2.
- **Đầu vào:** Baseline đã chốt; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `M3/notebooks/05_B_PIT_Enriched.ipynb`.
- **Thực hiện:** Kiểm HEAD/local diff, Python/kernel, pip check và SQLite/NumPy/scikit-learn; đối chiếu Python3.12.7, SQLite3.45.3, NumPy2.2.6, scikit-learn1.8.0 của baseline. Ghi phiên bản thực tế, pip freeze, test M3 và dung lượng.
- **Nghiệm thu:** Môi trường import được, pip check sạch, test M3 đạt và đủ dung lượng; khác biệt môi trường/baseline có ghi nhận trước khi chuyển B.
- **Test dự kiến:** `tests/unit/test_m3_*.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_*.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-02 — Kiểm kê và pin đầu vào

- **Người phụ trách:** Người 1. **Giai đoạn:** B.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 3.
- **Đầu vào:** R1-01; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `M3/notebooks/05_B_PIT_Enriched.ipynb`.
- **Thực hiện:** Kiểm dữ liệu local trước; nhận đúng revision HF trong kế hoạch nguồn khi thiếu, lưu receipt/hash rồi mới copy logical path. Pin Indicators, availability, v4, C8 prices/calendar/VNINDEX, B-PIT baseline và hai run đối chứng; kiểm SQLite/schema. Người 1 tự kiểm hash tất cả nguồn, PRAGMA integrity_check, bảng/cột/unique keys, missingness/coverage và Q-date như mục3.4–3.5 trước khi làm giàu.
- **Nghiệm thu:** Đủ file bắt buộc, hash/schema/integrity/readiness đúng; file khác hash được cô lập để đối chiếu, không ghi đè baseline.
- **Test dự kiến:** `tests/unit/test_m3_*.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_*.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-03 — Phân loại các ô đủ điều kiện làm giàu

- **Người phụ trách:** Người 1. **Giai đoạn:** C.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 4.1–4.2.
- **Đầu vào:** R1-02; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/features/financial_enrichment/eligibility.py`.
- **Thực hiện:** Lập inventory ticker/FY/metric/status/inputs_json cho FY2017–2024. Xét phi tài chính, báo cáo năm, usable date/cutoff và toàn bộ ô thiếu; CFO thiếu chỉ điền khi NI quan sát dương; ROE giữ điều kiện vốn chủ.
- **Nghiệm thu:** NI0/âm/unknown, equity không hợp lệ, NOT_APPLICABLE hoặc thiếu báo cáo không bị điền. Đối chiếu1045mã–năm/1111ô theo nguồn; nếu lệch ghi nguyên nhân.
- **Test dự kiến:** `tests/unit/test_financial_enrichment_eligibility.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_eligibility.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-04 — Tính median từ tập FIT gốc

- **Người phụ trách:** Người 1. **Giai đoạn:** C.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 4.3.
- **Đầu vào:** R1-03; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/features/financial_enrichment/medians.py`.
- **Thực hiện:** Đọc baseline role=FIT, đủ9/9 tại cutoff từng FY. Tính median theo FY/metric trên raw ratios chưa winsorize/scale; đóng băng donor IDs/counts và median table. Tự đối chiếu median bằng fixture tính tay, donor IDs/counts và thử loại late/imputed donor; các kiểm tra này đi cùng bước tính median.
- **Nghiệm thu:** Median khớp phép tính độc lập; không có donor imputed/late/khácFY; count khớp n_fit. Thiếu donor không tự tạo giá trị.
- **Test dự kiến:** `tests/unit/test_financial_enrichment_medians.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_medians.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-05 — Điền giá trị và ghi lineage theo ô

- **Người phụ trách:** Người 1. **Giai đoạn:** C.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 4.4.
- **Đầu vào:** R1-04; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/features/financial_enrichment/engine.py`.
- **Thực hiện:** Áp median cho đúng các ô đủ điều kiện, hỗ trợ một hoặc nhiều ô thiếu trên một row. Giữ observed/F/Z/usable date; receipt gồm original status/value, rule, median/count, cutoff và số ô điền.
- **Nghiệm thu:** Chỉ ô được phép thay đổi; imputed có status riêng. Replay cùng source/rule cho cùng giá trị, không dùng ô vừa điền làm donor.
- **Test dự kiến:** `tests/unit/test_financial_enrichment_engine.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_engine.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-06 — Xuất SQLite dẫn xuất và audit

- **Người phụ trách:** Người 1. **Giai đoạn:** C.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 4.5.
- **Đầu vào:** R1-05; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/features/financial_enrichment/export.py`.
- **Thực hiện:** Tạo run riêng gồm indicators.sqlite, imputed_cells.csv, medians_by_year_metric.csv, imputation_summary.csv, manifest.json. Pin commit/source/availability/FIT/rules và hashes đầu ra. Người 1 tự đối chiếu DB diff với receipts/manifest, baseline hashes, observed/F/Z/availability và FY ngoài scope trước khi bàn giao C.
- **Nghiệm thu:** Integrity/unique keys/DB diff/receipts khớp; observed và FY ngoài scope không đổi, hash baseline giữ nguyên; run có sẵn không bị sửa.
- **Test dự kiến:** `tests/unit/test_financial_enrichment_export.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_financial_enrichment_export.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-07 — Chuẩn hóa cohort và loader enriched

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.1–5.2.
- **Đầu vào:** R1-06; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/bpit_enriched.py`, `configs/experiments/bpit_enriched_v1.json`.
- **Thực hiện:** Nhận đúng SQLite C; loader thử nghiệm opt-in IMPUTED_MEDIAN. Cohort từng FY = FIT gốc cộng rows hoàn tất9/9 có usable<=cutoff gốc; T1 chỉ fit cohort này, cùng cohort cho mọi candidate. Tự kiểm cohort/cutoff/T1 trên fixture, late/no-date và FY ngoài phạm vi; không cần một người khác chạy lại bước này.
- **Nghiệm thu:** Cutoff/availability không đổi; late/no-date không tham gia FIT. Config enriched pin rõ parameters, scope, selection/validation và đối chứng; baseline builder/pointer giữ read-only.
- **Test dự kiến:** `tests/unit/test_bpit_enriched_cohorts.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_bpit_enriched_cohorts.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-08 — Thực hiện K-Means và PCA + K-Means

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.3.
- **Đầu vào:** R1-07; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/clustering/bpit_adapters.py`.
- **Thực hiện:** Tái sử dụng fitting/transform hiện có; KMeans và PCA-KMeans k3..8, PCA80%, parameters/seed theo config. Lưu state/feature order/label mapping; giữ đối chứng k3 seed42 n_init10 trên cùng dữ liệu enriched.
- **Nghiệm thu:** Reload cho cùng assignment; late dùng frozen transform và centroid trong đúng không gian, không refit PCA/T1/model.
- **Test dự kiến:** `tests/unit/test_bpit_kmeans_pca.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_bpit_kmeans_pca.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-09 — Thực hiện Ward và GMM

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.3.
- **Đầu vào:** R1-08; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/clustering/bpit_adapters.py`.
- **Thực hiện:** Bổ sung adapters Ward/GMM theo config tham chiếu; Ward gán late bằng centroid FIT trong T1, GMM bằng posterior của frozen model. Lưu đầy đủ model state và label mapping.
- **Nghiệm thu:** Replay đúng assignments sau reload; nonconvergence/không đủ cụm được ghi evidence. Late inference không sửa model.
- **Test dự kiến:** `tests/unit/test_bpit_ward_gmm.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_bpit_ward_gmm.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-10 — Tính chất lượng và độ ổn định cụm

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.4.
- **Đầu vào:** R1-08, R1-09; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/evaluation/bpit_screening.py`.
- **Thực hiện:** Silhouette/DB/CH đo trong T1; size/share theo FY; ARI subsample90% với seeds đã pin và temporal ARI trên mã FIT chung. Giữ metrics riêng khỏi portfolio evaluation.
- **Nghiệm thu:** Đối chiếu metric trên fixture; label permutation không đổi ARI; case không tính được có status/null rõ và không được giả0.
- **Test dự kiến:** `tests/unit/test_bpit_screening_metrics.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_bpit_screening_metrics.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-11 — Sàng lọc và khóa cấu hình chung

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.3–5.4.
- **Đầu vào:** R1-10; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/bpit_enriched.py`.
- **Thực hiện:** Chạy đủ24cặp trên FY2017–2022; admissibility minshare5% ở≥80%FY và median stability≥0.80; mean rank5metrics, tie nhỏk rồi KMeans/PCA-KMeans/Ward/GMM. Khóa trước validation FY2023–2024.
- **Nghiệm thu:** Thay validation/returns không đổi selection. Validation fit riêng từng FY với algorithm/k đã khóa. Không candidate đạt thì trình đối chứng k3, không tự nới ngưỡng.
- **Test dự kiến:** `tests/unit/test_bpit_screening_selection.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_bpit_screening_selection.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-12 — Xuất mô hình, labels và manifest B-PIT

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.1,5.5–5.6.
- **Đầu vào:** R1-11; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/bpit_enriched.py`, `scripts/build_financial_pit_clusters_enriched.py`.
- **Thực hiện:** Tạo entrypoint enriched riêng theo nguồn, dùng chung logic với notebook. Xuất labels/models/audit/manifest; pin C/availability/parent/code/config; lưu cohort, transforms, đủk, FIT-only order ROE/D-E, change labels/ARI/đối chứng. Tự reload artifacts và replay inference bốn thuật toán, kiểm feature order/label mapping/model hash và đối chứng k=3 trước xuất bàn giao.
- **Nghiệm thu:** fit_leaks rỗng; model/labels/order/hashes đúng; serializable/reload đạt; không sửa baseline. Loader M3 đọc đủk theo phần Người2.
- **Test dự kiến:** `tests/unit/test_bpit_enriched_artifacts.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_bpit_enriched_artifacts.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-13 — Hoàn thiện notebook chạy và bàn giao B-PIT

- **Người phụ trách:** Người 1. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.1–5.6.
- **Đầu vào:** R1-12, R2-01; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `M3/notebooks/05_B_PIT_Enriched.ipynb`.
- **Thực hiện:** Tổ chức notebook cấu hình→preflight→C→D→audit→bàn giao, gọi module/entrypoint chung. Run All trên fixture; chạy D thật khi A–C đạt; lập ranking và tác động Va cho owner review. Tổng hợp kết quả self-check C/D, fit_leaks và tương thích loader vào packet owner review; không thêm gate audit dữ liệu bởi Người 3.
- **Nghiệm thu:** Không hidden state/fit ngầm ở chart hoặc sửa run cũ. D chỉ chuyển E sau owner duyệt theo nguồn; chưa được duyệt giữ MANUAL_REVIEW_REQUIRED.
- **Đối chiếu:** Validate notebook và Restart Kernel → Run All trên fixture; chỉ chạy data thật khi A–C đạt và D đang mở.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-14 — Nhận pin và chọn input Assessment

- **Người phụ trách:** Người 1. **Giai đoạn:** S1.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 6.4,7.3,14/S1.
- **Đầu vào:** R4-03, R2-10; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/inputs.py`, `tests/fixtures/assessment_v1/`.
- **Thực hiện:** Sau F nhận cùng cặp B-PIT/SQLite enriched; kiểm labels/model/SQLite/availability hashes. Resolve ticker, demo as_of/session,18features/status/provenance, FY usable mới nhất/cutoff/18tháng; không fallback baseline hoặc modelFY cũ. Người 1 tự nhận và đối chiếu đủ pins C/D/E/F trước S1 theo mục6.4; hash thiếu hoặc sai vẫn phải dừng dù không có vai trò QA enrichment riêng.
- **Nghiệm thu:** Pin mismatch/thiếu nguồn dừng build. Case mới usable nhưng thiếu model, sector không áp dụng, missing và stale theo đúng nguồn; không tự thêm policy nhận imputed.
- **Test dự kiến:** `tests/unit/test_assessment_inputs.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_inputs.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-15 — Tạo Peers theo từng đặc trưng

- **Người phụ trách:** Người 1. **Giai đoạn:** S1.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 6.3,14/S1.
- **Đầu vào:** R1-14; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/peers.py`.
- **Thực hiện:** Ưu tiên cùngA+B, dưới3 thì financial cùngB/market cùngA. Loại self/trùng/null/sai identity/kỳ/unit/source. ≥3 tính median/IQR, lưu basis/count/ref theo metric; missingB không tạoPeers.
- **Nghiệm thu:** 0–2 không median, đúng3 có median; Peers ít không tự đổi verdict. Opt-in imputed theo policy đã duyệt, không kế thừa tự động từ M3.
- **Test dự kiến:** `tests/unit/test_assessment_peers.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_peers.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-16 — Dựng lịch sử và coverage

- **Người phụ trách:** Người 1. **Giai đoạn:** S3.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 5.1,9.3,11.2,14/S3.
- **Đầu vào:** R1-15, R2-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/history.py`.
- **Thực hiện:** Xuất feature_history.jsonl và coverage.csv cho đúng18features, ngày/FY/usable/status/unit/source. Lookback5/10 từ as_of, giữ gap và coverage thực; dòng tài chính theo FY và market theo snapshot hợp lệ.
- **Nghiệm thu:** Không tạo số liệu/nội suy/đổi missing thành0; không dùng FY tương lai. Đổi lookback chỉ thay phần lịch sử, không đổi evidence/nhãn/verdict.
- **Test dự kiến:** `tests/unit/test_assessment_history.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_history.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-17 — Nối engine đánh giá offline

- **Người phụ trách:** Người 1. **Giai đoạn:** S3.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2–9.3,14/S3.
- **Đầu vào:** R1-16, R2-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/investment_assessment_v1.py`.
- **Thực hiện:** Orchestrate inputs, rule evaluation/verdict/rationale của Người2, Peers/history. Tạo kết quả từng ticker trong danh mục hỗ trợ; không dùng NAV/trades/return để quyết định assessment.
- **Nghiệm thu:** Fixture đủ4verdict, evidence thuộc18features, kết quả đúng mã/as_of/source. Rationale/Peers không thay điều kiện kết luận đã chốt.
- **Test dự kiến:** `tests/integration/test_assessment_offline_builder.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/integration -p 'test_assessment_offline_builder.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-18 — Bổ sung CLI build Assessment

- **Người phụ trách:** Người 1. **Giai đoạn:** S3.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,14/S3.
- **Đầu vào:** R1-17; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `scripts/build_investment_assessment_v1.py`.
- **Thực hiện:** CLI mỏng nhận source manifest/policy/output root rõ, gọi orchestrator. Preflight pins rồi build run mới; báo paths/counts/status, không crawl/fit realtime hoặc sửa pointer production.
- **Nghiệm thu:** Thiếu input/sai pin/policy/version thì exit lỗi rõ; existing output không bị ghi đè; không dùng default baseline thay nguồn enriched.
- **Test dự kiến:** `tests/unit/test_assessment_build_cli.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_build_cli.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-19 — Khóa manifest và deterministic payload

- **Người phụ trách:** Người 1. **Giai đoạn:** S3.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.3,13/T15,14/S3.
- **Đầu vào:** R1-18; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/investment_assessment_v1.py`.
- **Thực hiện:** Xuất manifest,assessments.jsonl,peer_benchmarks.csv,coverage.csv,feature_history.jsonl; pin A/B-PIT/SQLite/availability/policy/code. Tách operational metadata khỏi deterministic assessment content hash.
- **Nghiệm thu:** Cùng inputs/policy cho cùng nội dung/hash dù run_id/generated_at khác. Mọi file/hash và references truy được, không tự gắn verificationPASS.
- **Test dự kiến:** `tests/unit/test_assessment_reproducibility.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_reproducibility.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R1-20 — Nghiệm thu builder trên bộ bàn giao thật

- **Người phụ trách:** Người 1. **Giai đoạn:** S3.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 13/T01,T19,T32;17.1–17.4;14/S3.
- **Đầu vào:** R1-19, R3-14; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `tests/integration/test_assessment_real_handoff.py`.
- **Thực hiện:** Build từ F, đối chiếu FPT+ít nhất1mã hợp lệ khác, VCB/mã thiếu lịch sử và missing cases; chạy verifier độc lập, kiểm labels/FY/value/provenance và demo dates.
- **Nghiệm thu:** FPT không bị hard-code verdict; nguồn thiếu/sai không dùng fixture thay thật. Có actual run IDs/hashes/coverage và verifier results trước bàn giao API.
- **Test dự kiến:** `tests/integration/test_assessment_real_handoff.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/integration -p 'test_assessment_real_handoff.py' -v`.
- **Đối chiếu:** Build/verify trên chính bộ pin F; thiếu nguồn thật ghi thiếu và dừng, không thay bằng synthetic.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-01 — Sửa loader M3 nhận đủ k cụm

- **Người phụ trách:** Người 2. **Giai đoạn:** D.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 5.6.
- **Đầu vào:** R1-07; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/m3/inputs.py`, `tests/unit/test_m3_cutoff.py`.
- **Thực hiện:** Sửa loader theo metadata k, thứ tự và nhãn cụm thay cho điều kiện cố định ba cụm. Giữ interface và kiểm tra legacy; bổ sung fixture k=3,4,8.
- **Nghiệm thu:** Model có đầy đủ metadata giữ được cutoff; order/labels thiếu hoặc trùng bị chặn, legacy k=3 vẫn tái lập đúng.
- **Test dự kiến:** `tests/unit/test_m3_cutoff.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_cutoff.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-02 — Truyền nguồn enriched xuyên runner

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.1.
- **Đầu vào:** R1-13; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `scripts/run_m3.py`, `src/delta_t1/m3/inputs.py`.
- **Thực hiện:** Resolve SQLite từ config, truyền cùng path cho scoring, sectors và hash trong manifest. Kiểm nhãn/model/availability và mở dữ liệu read-only.
- **Nghiệm thu:** Fixture baseline/enriched cho đúng values, sector và hash cùng một nguồn; không bỏ sót default arguments của loader.
- **Test dự kiến:** `tests/unit/test_m3_enriched_sources.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_enriched_sources.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-03 — Tạo config thử nghiệm và cache riêng

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.1.
- **Đầu vào:** R2-02; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `configs/experiments/m3_strategy_enriched_v1.json`, `scripts/run_m3.py`.
- **Thực hiện:** Tạo config enriched từ baseline với trạng thái READY_TO_LOCK_AFTER_BPIT. Pin C/D/models/availability và dùng limits cache riêng; giữ các quy tắc M3 đã chốt.
- **Nghiệm thu:** Không tự đổi A, Va, Q-date, 18 tháng, ranking, lịch, basis, chi phí hoặc execution; sai hash thì dừng.
- **Test dự kiến:** `tests/unit/test_m3_enriched_sources.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_enriched_sources.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-04 — Thêm --config cho feasibility

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.2.
- **Đầu vào:** R2-03; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `scripts/m3_feasibility_variants.py`.
- **Thực hiện:** Thêm --config, dùng cùng nguồn chỉ số/ngành/scoring/cutoff với runner. Báo official config sau FINANCIAL_CRITERIA_MISSING cho từng segment, gồm median/min và số kỳ N<10.
- **Nghiệm thu:** Counts và lý do loại khớp runner trên fixture; không đọc ngầm config hoặc SQLite baseline khi đã truyền enriched.
- **Test dự kiến:** `tests/unit/test_m3_feasibility_config.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_feasibility_config.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-05 — Mở rộng regression giá/cutoff/targets

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.3–6.4.
- **Đầu vào:** R2-04; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `tests/unit/test_m3_cutoff.py`, `tests/unit/test_m3_prices_boundary.py`, `tests/unit/test_m3_engine.py`.
- **Thực hiện:** Mở rộng tests hiện có cho nguồn enriched, k mới, targets/audit và Q17. Thử thêm giá/lịch tương lai ngoài segment và các phiên lân cận ranh giới.
- **Nghiệm thu:** Future append không đổi Dev; kỳ cuối và NAV bounds đúng, missing limits giữ hành vi đã duyệt; không giảm assertion cũ.
- **Test dự kiến:** `tests/unit/test_m3_*.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_*.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-06 — Chuẩn bị verifier và seal hai đoạn

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.5–6.6.
- **Đầu vào:** R2-05; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `scripts/verify_m3_enriched_run.py`.
- **Thực hiện:** Viết verifier cho manifest, targets, audit, ledger, cash, holdings, NAV, metrics, controls và hashes. Seal là file riêng; Holdout phải có Dev seal PASS và cùng code/config/inputs.
- **Nghiệm thu:** Fixture sai dòng tiền, date bounds hoặc pin bị phát hiện trước seal; run bytes giữ nguyên và NAV hai đoạn tách riêng.
- **Test dự kiến:** `tests/unit/test_m3_enriched_verifier.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_enriched_verifier.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-07 — Feasibility thật, targets-only và khóa config

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.2–6.4.
- **Đầu vào:** R1-13, R2-06; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `configs/experiments/m3_strategy_enriched_v1.json`.
- **Thực hiện:** Sau khi D được duyệt, chạy feasibility và targets-only cả hai đoạn; kiểm pins, financial_source, git_dirty, candidates/audit/weights và Q17. Review rồi LOCKED, commit code/config và ghi execution SHA.
- **Nghiệm thu:** Dev60/59/1 và Holdout24/23/1 theo lịch; trường hợp số kỳ N<10 tăng được trình owner theo nguồn trước full run.
- **Lệnh kiểm tra/chạy:** `& $py scripts/m3_feasibility_variants.py --config configs/experiments/m3_strategy_enriched_v1.json`; `& $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment development --targets-only`; `& $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment holdout --targets-only`.
- **Đối chiếu:** Kiểm targets/audit/source/pins/Q17, review theo nguồn rồi LOCKED và commit code/config trước full run.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-08 — Chạy và seal Development

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.5.
- **Đầu vào:** R2-07; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `data/experiments/m3/development/<run_id>/`.
- **Thực hiện:** Full Dev từ HEAD/config đã khóa; đối chiếu targets-only, ledger, cash, holdings, NAV và controls với baseline. Rà UNIVERSE_TOO_SMALL/LIMIT_DATA_MISSING, verify rồi seal.
- **Nghiệm thu:** NAV kết thúc2023-12-29, pins đúng C/D và controls khớp nghiệp vụ; không thay code/config trước Holdout.
- **Lệnh kiểm tra/chạy:** `& $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment development`.
- **Đối chiếu:** Verify rồi seal theo mục6.5/6.6 kế hoạch làm giàu. Holdout chỉ chạy sau Dev seal PASS và cùng execution SHA/config/inputs.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-09 — Chạy và seal Holdout

- **Người phụ trách:** Người 2. **Giai đoạn:** E.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 6.6.
- **Đầu vào:** R2-08; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `data/experiments/m3/holdout/<run_id>/`.
- **Thực hiện:** Sau Dev seal, chạy full Holdout cùng execution HEAD/config/inputs, khởi tạo NAV riêng, verify và seal. Chỉ commit receipts sau khi hai full run hoàn tất.
- **Nghiệm thu:** NAV kết thúc2025-12-31; pins bằng Dev, không Sharpe. Nếu sửa lỗi code/config phải dùng SHA mới và chạy lại phần chịu ảnh hưởng.
- **Lệnh kiểm tra/chạy:** `& $py scripts/run_m3.py --config configs/experiments/m3_strategy_enriched_v1.json --segment holdout`.
- **Đối chiếu:** Verify rồi seal theo mục6.5/6.6 kế hoạch làm giàu. Holdout chỉ chạy sau Dev seal PASS và cùng execution SHA/config/inputs.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-10 — Xuất đối sánh M3 theo segment

- **Người phụ trách:** Người 2. **Giai đoạn:** F.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 7.
- **Đầu vào:** R2-09; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `scripts/export_backtest_comparison_metrics.py`.
- **Thực hiện:** Đọc baseline và enriched runs/seals, xuất Combined/Financial-only cùng controls theo từng segment. Báo N, cash, failed trades, selected/held, NAV, return, drawdown và cơ sở giá.
- **Nghiệm thu:** Các bảng truy được series và pins; không gộp NAV hai đoạn hoặc dùng performance để chọn lại mô hình; giữ kết quả bất lợi.
- **Test dự kiến:** `tests/unit/test_m3_comparison_export.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_m3_comparison_export.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-11 — Mã hóa policy D-ASS-01

- **Người phụ trách:** Người 2. **Giai đoạn:** S2.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 6.4.3,8.3,14/S2.
- **Đầu vào:** R1-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `configs/product/assessment_policy_v1.json`.
- **Thực hiện:** Chuyển bảng D-ASS-01 thành policy versioned: whitelist18, mandatory/optional, threshold, priority, Peers và cách nhận ô imputed theo policy đã duyệt.
- **Nghiệm thu:** Không tự thêm điểm tổng/penalty hoặc quyết định imputed mới. Ô bắt buộc chưa được phép dùng xử lý đúng mục6.4.3 và8.3 trước verdict thật.
- **Test dự kiến:** `tests/unit/test_assessment_policy.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_policy.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-12 — Hiện thực điều kiện thị trường

- **Người phụ trách:** Người 2. **Giai đoạn:** S2.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 8.3.
- **Đầu vào:** R2-11; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/rules_market.py`.
- **Thực hiện:** Hiện thực xu hướng thuận lợi khi mom_63>0 và mom_126>0, đồng thời mom_21>0 hoặc mom_252>0; bất lợi theo điều kiện âm đối xứng. Tổ hợp còn lại mixed; ILLIQUID là cảnh báo trọng yếu.
- **Nghiệm thu:** Ngưỡng 0, missing và mixed đúng; rule results có evidence/status, không dùng cluster ID như thứ hạng hoặc future return.
- **Test dự kiến:** `tests/unit/test_assessment_market_rules.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_market_rules.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-13 — Hiện thực tài chính và dòng tiền

- **Người phụ trách:** Người 2. **Giai đoạn:** S2.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 8.3.
- **Đầu vào:** R2-11; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/rules_financial.py`.
- **Thực hiện:** Hiện thực ROA/net_margin/CFO và các cảnh báo đúng bảng8.3. Chỉ đọc dấu CFO qua tỷ lệ khi NI dương và ratio hợp lệ; watch khi gross_margin<0, current_ratio<1 hoặc revenue_growth<0.
- **Nghiệm thu:** Giá trị bằng ngưỡng không kích hoạt warning; một watch đủ chặn favorable, CFO0 không thuận lợi; imputed/denominator theo policy đã duyệt.
- **Test dự kiến:** `tests/unit/test_assessment_financial_rules.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_financial_rules.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-14 — Kết hợp eligibility và bốn verdict

- **Người phụ trách:** Người 2. **Giai đoạn:** S2.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 7.3,8.3.
- **Đầu vào:** R1-14, R2-12, R2-13; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/verdict.py`.
- **Thực hiện:** Kết hợp eligibility/freshness/model gates với thứ tự INSUFFICIENT_EVIDENCE→CAUTION→RESEARCH_FAVORABLE→WATCH. Optional missing bỏ phép kiểm tương ứng, major warning ưu tiên CAUTION.
- **Nghiệm thu:** Có bảng kiểm bốn verdict và ca biên; thiếu Peers không tự insufficient, FY mới có dữ liệu nhưng chưa có model không fallback năm cũ.
- **Test dự kiến:** `tests/unit/test_d_ass_01_rules.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_d_ass_01_rules.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R2-15 — Dựng rationale và counter-evidence

- **Người phụ trách:** Người 2. **Giai đoạn:** S2.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 8.1–8.5,10.2,13/T30.
- **Đầu vào:** R2-14, R1-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/experiments/assessment/rationale.py`.
- **Thực hiện:** Dựng drivers/risks/counter_evidence từ templates có rule ID, value, status, unit, kỳ và evidence_ref thuộc18features. Peers là bằng chứng giải thích G4; kiểm replay và mutation Peers.
- **Nghiệm thu:** Lý do truy được nguồn, không text tự do thiếu evidence hoặc đổi verdict do Peers; không mô tả giá trị median như CFO quan sát của doanh nghiệp.
- **Test dự kiến:** `tests/unit/test_assessment_rationale.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_rationale.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-01 — Cấu hình đọc bản phát hành Assessment

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,12.3,14/S4.
- **Đầu vào:** R1-20; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `configs/product/assessment_release_v1.json`, `src/delta_t1/product/assessment_repository.py`.
- **Thực hiện:** Khai báo pointer tới artifact Assessment đã verify, release context và revision. Reader resolve đường dẫn từ cấu hình, kiểm trường bắt buộc và phân biệt chưa có bản phát hành; không sửa model/data nguồn.
- **Nghiệm thu:** Cấu hình hợp lệ resolve đúng artifact; pointer thiếu hoặc không tồn tại được báo trạng thái chưa sẵn sàng, không tự chọn baseline hoặc run mới nhất.
- **Test dự kiến:** `tests/unit/test_assessment_release_config.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_release_config.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-02 — Kiểm manifest khi mở artifact phục vụ API

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10.3,12.3,14/S4.
- **Đầu vào:** R3-01; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/product/assessment_repository.py`.
- **Thực hiện:** Khi reader mở bản phát hành, đối chiếu manifest, hashes của các file cần phục vụ và source/policy revision. Dùng evidence đã bàn giao, không chạy lại imputation hoặc kiểm lại donor median.
- **Nghiệm thu:** File bị sửa, thiếu hoặc khác revision bị từ chối trước serving; artifact đúng được mở read-only. Không tạo một lượt audit enrichment riêng.
- **Test dự kiến:** `tests/unit/test_assessment_manifest_reader.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_manifest_reader.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-03 — Nạp payload Assessment theo schema

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.3,10.2,14/S4.
- **Đầu vào:** R3-02, R3-07; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/product/assessment_repository.py`.
- **Thực hiện:** Đọc assessments, peer_benchmarks, coverage và feature_history từ bản phát hành; parse types/status/null theo contract. Giữ nguyên dữ liệu và provenance đã build, không tính lại features, Peers hoặc verdict.
- **Nghiệm thu:** Payload hợp lệ nạp đúng; bản ghi thiếu required, sai status hoặc không tương thích schema bị phát hiện. Null không biến thành0.
- **Test dự kiến:** `tests/unit/test_assessment_payload_reader.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_payload_reader.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-04 — Tra cứu đúng mã và ngữ cảnh phát hành

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10.1–10.3,14/S4.
- **Đầu vào:** R3-03; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/product/assessment_repository.py`.
- **Thực hiện:** Bổ sung lookup theo ticker, assessment_context, as_of, required_price_session và revision. Phân biệt mã không tồn tại với mã tồn tại nhưng thiếu bằng chứng; đọc kết quả đã có, không suy nhãn.
- **Nghiệm thu:** Lookup trả đúng mã/ngày/context/revision; demo không được trả như current, mã thiếu dữ liệu không bị coi là mã không tồn tại.
- **Test dự kiến:** `tests/unit/test_assessment_lookup.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_lookup.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-05 — Gắn repository vào vòng đời FastAPI

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,10.3,14/S4.
- **Đầu vào:** R3-08; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/main.py`.
- **Thực hiện:** Khởi tạo repository theo cấu hình trong lifespan/app state và hỗ trợ dependency injection cho tests. Giữ các endpoint cũ hoạt động khi chưa có artifact Assessment; quản lý tài nguyên đọc đúng vòng đời.
- **Nghiệm thu:** App khởi động khi artifact vắng; dịch vụ Assessment biểu thị chưa sẵn sàng, không làm hỏng API hiện hữu. Tests dùng repository fixture được inject rõ.
- **Test dự kiến:** `tests/unit/test_assessment_lifespan.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_lifespan.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-06 — Ánh xạ payload sang response API

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10.1–10.3,14/S4.
- **Đầu vào:** R3-08, R3-07; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/assessment.py`.
- **Thực hiện:** Mapper chuyển payload offline sang response Pydantic, bổ sung request_time của lần gọi và giữ nguyên as_of/context/nhãn/evidence từ bản phát hành. Không tạo rationale, Peers hoặc kết luận mới trong request.
- **Nghiệm thu:** Response giữ nguyên nội dung quyết định, dates/status/nguồn đúng; request_time cập nhật riêng, payload dùng cache không giữ metadata request cũ.
- **Test dự kiến:** `tests/unit/test_assessment_response_mapper.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_response_mapper.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-07 — Khai báo response schema Assessment

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,10.2,14/S4.
- **Đầu vào:** R1-20; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/schemas.py`.
- **Thực hiện:** Thêm Pydantic response cho dates/context/status, A/B profiles,18features, evidence, Peers, history và references. Ánh xạ đúng offline artifact, giữ hợp đồng API cũ.
- **Nghiệm thu:** Fixture hợp lệ parse được; invalid status hoặc thiếu required bị bắt; null khác0, public API không nhận as_of tùy ý.
- **Test dự kiến:** `tests/unit/test_assessment_response_models.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_response_models.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-08 — Reader artifact read-only

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,12.3,14/S4.
- **Đầu vào:** R3-04, R3-07; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `src/delta_t1/product/assessment_repository.py`.
- **Thực hiện:** Reader kiểm manifest/hash/policy/source pins rồi tra theo ticker/as_of/context/revision. Phân biệt chưa phát hành, ticker không tồn tại, thiếu evidence và corruption.
- **Nghiệm thu:** Không network/write/recompute; sai nguồn không fallback baseline hoặc tráo demo/current; absent artifact khác unknown ticker.
- **Test dự kiến:** `tests/unit/test_assessment_repository.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_repository.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-09 — Đăng ký endpoint đánh giá

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10.1,14/S4.
- **Đầu vào:** R3-05, R3-06; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/assessment.py`, `web/backend/app/main.py`.
- **Thực hiện:** Đăng ký GET stock assessment, repository injection/lifespan, release context cố định và request_time. Dùng revision middleware hiện có, không lấy nhãn từ legacy overview/peers.
- **Nghiệm thu:** App vẫn khởi động khi chưa có artifact và endpoint trả503; đúng ticker/context/date, không crawl/fit/build trong request.
- **Test dự kiến:** `tests/unit/test_assessment_api.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_api.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-10 — Projection lịch sử 5/10 năm

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 5.1,10.1–10.2.
- **Đầu vào:** R3-09; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/assessment.py`, `src/delta_t1/product/assessment_repository.py`.
- **Thực hiện:** Nhận lookback_years5/10, mặc định10; đọc và cắt feature_history từ as_of. Giữ nguyên verdict, evidence quyết định và peer_basis; dùng endpoint stock assessment đã chốt.
- **Nghiệm thu:** Đổi lookback chỉ đổi history; giá trị khác trả422, không lọt FY tương lai hoặc nội suy khoảng trống.
- **Test dự kiến:** `tests/unit/test_assessment_history_api.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_history_api.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-11 — HTTP errors và khóa revision

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10.3.
- **Đầu vào:** R3-10; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/assessment.py`, `web/backend/app/main.py`.
- **Thực hiện:** Ánh xạ200 cho mã tồn tại nhưng insufficient,404 unknown,409 revision mismatch,422 invalid query và503 unpublished. Kiểm ticker/path/SQL injection và compatibility source/policy.
- **Nghiệm thu:** HTTP matrix đúng, không query tùy ý theo input ticker; existing endpoints giữ meaning và dữ liệu hỏng không thành verdict hợp lệ.
- **Test dự kiến:** `tests/unit/test_assessment_api.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_api.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-12 — Cache đúng context và nguồn

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10.3.
- **Đầu vào:** R3-11; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/backend/app/assessment_cache.py`, `web/backend/app/assessment.py`.
- **Thực hiện:** Cache bounded với key ticker/context/as_of/required session/evidence cutoff/lookback/policy/bundle revision. Request_time cập nhật riêng; invalidate khi artifact/model/rule/date đổi.
- **Nghiệm thu:** Demo/current không dùng nhầm payload; cache hit không giữ request_time cũ; có ca key mismatch và eviction.
- **Test dự kiến:** `tests/unit/test_assessment_cache.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_cache.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-13 — Integration API và regression

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 13/T03,T10–12,T17–18,T21–22,T25–28,T31.
- **Đầu vào:** R3-12; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `tests/integration/test_assessment_endpoints.py`, `tests/unit/test_terminal_api.py`.
- **Thực hiện:** Integration trên injected fixtures và verified artifact; kiểm revision/cache/error/payload/read-only, chặn network/fit calls. Giữ Overview/Fundamentals/Scores/Peers cũ.
- **Nghiệm thu:** Có test thực chạy và ghi rõ skip; payload lỗi bị từ chối, không legacy fallback hoặc thay nghĩa endpoint hiện có.
- **Test dự kiến:** `tests/integration/test_assessment_endpoints.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/integration -p 'test_assessment_endpoints.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-14 — Xây dựng validator kiểm tra toàn vẹn artifact

- **Người phụ trách:** Người 3. **Giai đoạn:** S3.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,9.3,13/T15,T23,T32,14/S3.
- **Đầu vào:** R1-19; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `scripts/verify_investment_assessment_v1.py`.
- **Thực hiện:** Xây dựng CLI tool scripts/verify_investment_assessment_v1.py để backend tự động kiểm tra tính toàn vẹn của artifact trước khi nạp serving. Xuất verification.json riêng.
- **Nghiệm thu:** Mutation future data, driver ngoài18, SQLite sai hoặc hash lỗi bị bắt; content hash tách metadata vận hành, fixture PASS không thay real PASS.
- **Test dự kiến:** `tests/unit/test_assessment_release_verifier.py`.
- **Lệnh kiểm tra/chạy:** `& $py -m unittest discover -s tests/unit -p 'test_assessment_release_verifier.py' -v`.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R3-15 — Xuất OpenAPI và smoke API

- **Người phụ trách:** Người 3. **Giai đoạn:** S4.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 10,13/GATEC,14/S4.
- **Đầu vào:** R3-13; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `docs/api/OPENAPI_ASSESSMENT_SPEC.json`, `web/README.md`.
- **Thực hiện:** Xuất OpenAPI từ app version thực, examples và HTTP matrix. Smoke với artifact Assessment đã verify, ghi revision/context/pins và lệnh tái lập.
- **Nghiệm thu:** Spec parse được, examples và response đúng artifact; không ghi đã deploy khi mới nghiệm thu local.
- **Lệnh kiểm tra/chạy:** `git diff --check`.
- **Đối chiếu:** Parse OpenAPI/examples và smoke endpoint trên artifact đã verify; ghi context/revision/response/error matrix.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-01 — Tổng hợp đối sánh B-PIT

- **Người phụ trách:** Người 4. **Giai đoạn:** F.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 7.
- **Đầu vào:** R1-13, R1-06; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `docs/REPORT_BACKTEST.md`.
- **Thực hiện:** Báo ô điền theo FY/metric, mã–năm theo số ô điền, coverage9/9, n_fit, sizes, thay nhãn/common ARI và đối chứng k=3 từ audit C/D đã verify.
- **Nghiệm thu:** Số liệu khớp pins; phân biệt tác động mở cohort, refit và ROE scoring; không sửa baseline.
- **Lệnh kiểm tra/chạy:** `git diff --check`.
- **Đối chiếu:** Kiểm links/JSON và đối chiếu số liệu, hashes, run IDs với evidence; không chạy lại model chỉ để kiểm tài liệu.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-02 — Tổng hợp đối sánh M3

- **Người phụ trách:** Người 4. **Giai đoạn:** F.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 7.
- **Đầu vào:** R4-01, R2-10; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `docs/REPORT_BACKTEST.md`.
- **Thực hiện:** Nhập bảng đối sánh Combined/Financial-only/controls từ Người2 theo từng segment: N, cash, trades, NAV, return, drawdown. Ghi price basis và các giới hạn.
- **Nghiệm thu:** Không gộp NAV hoặc báo Sharpe ở Dev/Holdout; kết quả bất lợi và source references được giữ đủ.
- **Lệnh kiểm tra/chạy:** `git diff --check`.
- **Đối chiếu:** Kiểm links/JSON và đối chiếu số liệu, hashes, run IDs với evidence; không chạy lại model chỉ để kiểm tài liệu.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-03 — Hoàn tất hồ sơ bàn giao và tài liệu liên quan

- **Người phụ trách:** Người 4. **Giai đoạn:** F.
- **Nguồn:** [B-PIT/M3](../KE_HOACH_LAM_GIAU_DU_LIEU_B_PIT_M3.md) 7.
- **Đầu vào:** R4-02; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `docs/REPORT_BACKTEST.md`, `docs/DECISIONS.md`, `CHANGELOG.md`.
- **Thực hiện:** Ghi mục4 công việc còn lại, phase status/evidence, config/HEAD/hash/run IDs và đường dẫn nhận có quyền. Cập nhật Decisions/Changelog khi quy tắc được triển khai; chuẩn bị bộ bàn giao F.
- **Nghiệm thu:** Bộ C/D/E và đối sánh đủ cho Assessment; owner review theo nguồn trước cân nhắc promote. ADR/Changelog đi cùng PR đổi behavior liên quan.
- **Lệnh kiểm tra/chạy:** `git diff --check`.
- **Đối chiếu:** Kiểm links/JSON và đối chiếu số liệu, hashes, run IDs với evidence; không chạy lại model chỉ để kiểm tài liệu.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-04 — Types và trạng thái dữ liệu frontend

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,10.2,14/S5.
- **Đầu vào:** R3-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/lib/types.ts`.
- **Thực hiện:** Bổ sung types theo response đã nghiệm thu S4: status, dates, provenance,18features, Peers và history. Đọc tài liệu Next local theo AGENTS trước khi code.
- **Nghiệm thu:** Typecheck đạt, null/status mapping đúng; không dùng fixture làm fallback production hoặc tạo contract API khác.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-05 — Verdict và availability states

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 8.3,11.3,14/S5.
- **Đầu vào:** R4-04; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/verdict-badge.tsx`, `web/frontend/components/stock/assessment-status.tsx`.
- **Thực hiện:** Hiển thị bốn verdict, loading/error/insufficient/stale, demo/as_of/session/context bằng text và trạng thái accessible. Reset kết luận cũ khi đổi mã.
- **Nghiệm thu:** Giá trị lấy đúng API, pending/404/503/409 rõ; không đồng nhất availability với verdict.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-06 — Một biểu đồ chuyển đổi chỉ số

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 11.2,13/T24,14/S5.
- **Đầu vào:** R4-04; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/single-feature-chart.tsx`.
- **Thực hiện:** Một vùng chart với selector18feature hoặc nhóm cùng unit/tần suất/basis. Trục tài chính theo FY, market theo snapshot; chỉ vẽ điểm hợp lệ tại as_of.
- **Nghiệm thu:** Không ghép line khác đơn vị/tần suất; gap giữ trống, selector không tính lại verdict hoặc model labels.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-07 — Lookback và thông tin coverage

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 5.1,11.2,13/T13.
- **Đầu vào:** R4-06; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/single-feature-chart.tsx`.
- **Thực hiện:** Thêm selector5/10 năm mặc định10 tính lùi từ as_of; hiển thị coverage thực và thông tin ngày/status/nguồn. Query theo hợp đồng API.
- **Nghiệm thu:** Đổi lookback không đổi as_of/verdict/evidence; thiếu kỳ chỉ hiện phần thực có, không tạo dữ liệu.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-08 — Bảng Peers theo đặc trưng

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 6.3,11.2,13/T07,T28.
- **Đầu vào:** R4-04; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/peer-comparison-table.tsx`.
- **Thực hiện:** Render basis/count/date/source và median/IQR từng metric;0–2 ghi thiếu đối chứng, đúng3 có median. Missing B-PIT không lập Peers, dữ liệu lấy từ artifact.
- **Nghiệm thu:** Không gọi legacy peers hoặc tính lại nhóm trên client; thiếu Peers không tự đổi verdict.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-09 — Bảng chi tiết 18 đặc trưng

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 6.1–6.2,11.2.
- **Đầu vào:** R4-04; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/assessment-feature-table.tsx`.
- **Thực hiện:** Bảng đủ9A+9B với value/unit/period/status/coverage/ref, phân biệt observed/imputed/missing/NOT_APPLICABLE. Dùng formatters và primitives hiện có.
- **Nghiệm thu:** Không thêm metric ngoài18, null khác0; ô imputed có provenance, optional missing không bị trình bày như giá trị quan sát.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-10 — Giải thích tín hiệu và rủi ro

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 8.1–8.5,11.2.
- **Đầu vào:** R4-05; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/rationale-card.tsx`.
- **Thực hiện:** Render drivers/risks/counter_evidence từ response, kèm nguồn/ngày/status, giải thích bốn verdict và tín hiệu trái chiều.
- **Nghiệm thu:** Không sinh text thiếu evidence hoặc tính score/đổi rule trên client; Peers chỉ bổ sung giải thích.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-11 — Nguồn và chất lượng dữ liệu

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 6.2,10.2,11.2.
- **Đầu vào:** R4-09, R4-10; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/evidence-provenance-modal.tsx`.
- **Thực hiện:** Expander/modal nguồn cạnh chart/bảng, ghi FY/snapshot/usable/as_of/status/revision/evidence. Hỗ trợ keyboard/focus và link phù hợp.
- **Nghiệm thu:** Không lộ token/absolute local paths hoặc tạo dashboard QA riêng; long references đọc được trên mobile.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-12 — Ghép panel đánh giá

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 11.1–11.4,14/S5.
- **Đầu vào:** R4-05, R4-07, R4-08, R4-09, R4-10, R4-11; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/components/stock/assessment-panel.tsx`.
- **Thực hiện:** Ghép verdict, A/B profiles, một chart, bảng18feature, Peers, rationale, provenance và empty states trong panel Assessment.
- **Nghiệm thu:** Panel read-only, không compute/fit; tại một thời điểm một chart, case stale/insufficient hiển thị đúng.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-13 — Tab, API và URL state

- **Người phụ trách:** Người 4. **Giai đoạn:** S5.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 9.2,10.3,11.4,13/T11–12.
- **Đầu vào:** R4-12, R3-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/app/stocks/page.tsx`, `web/frontend/lib/api.ts`.
- **Thực hiện:** Thêm tab thứ5, nối API và URL state ticker/tab/metric/lookback. Xử lý409 reset/reload và race A→B/Back; giữ các tab hiện hữu.
- **Nghiệm thu:** Response mã cũ không ghi đè mã mới; revision lock đúng; lookback chỉ đổi history, không có nút chọn as_of hoặc mode công khai.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-14 — UAT và regression giao diện

- **Người phụ trách:** Người 4. **Giai đoạn:** S6.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 13/T01–T32;17;14/S6.
- **Đầu vào:** R4-13, R1-20; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `web/frontend/`, `tests/integration/`.
- **Thực hiện:** UAT FPT+mã hợp lệ khác, VCB/mã mới, stale/current fixtures, mismatch/missing; kiểm18selector5/10, một chart, navigation, mobile/keyboard/theme. Ghi rõ manual và automated.
- **Nghiệm thu:** Typecheck/build và ca nghiệm thu đạt; screenshots/response đúng pins, không bỏ case fail để ghi PASS.
- **Lệnh kiểm tra/chạy:** `npm --prefix web/frontend run typecheck`; `npm --prefix web/frontend run build`.
- **Đối chiếu:** Thực hiện ca tương tác/empty state ghi trong task; dùng hạ tầng test hiện có, ghi rõ manual hoặc automated.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

### R4-15 — Hướng dẫn và hồ sơ nghiệm thu

- **Người phụ trách:** Người 4. **Giai đoạn:** S6.
- **Nguồn:** [Assessment](../Ke_hoach_Output_DELTA_Investment_Assessment.md) 12–15,18,14/S6.
- **Đầu vào:** R4-14, R3-15; đầu ra/pins của giai đoạn trước phải đạt điều kiện ở mục3.
- **File chính:** `docs/HUONG_DAN_SU_DUNG_TOOL_DANH_GIA_DAU_TU.md`, `README.md`, `docs/README.md`.
- **Thực hiện:** Hướng dẫn demo, tra mã, bốn verdict, Peers/history/nguồn; setup/commands/pins/coverage/limitations/rollback. Tổng hợp API/UI/verifier/UAT evidence và index.
- **Nghiệm thu:** Giữ M2/M3/artifact frozen, công bố đúng phần đạt/chưa đạt; production release theo approval của kế hoạch nguồn, không tự deploy.
- **Lệnh kiểm tra/chạy:** `git diff --check`.
- **Đối chiếu:** Kiểm links/JSON và đối chiếu số liệu, hashes, run IDs với evidence; không chạy lại model chỉ để kiểm tài liệu.
- **Bàn giao:** diff, kết quả test thực chạy, artifact/run IDs/hashes nếu có, trạng thái và việc còn thiếu. Nếu input/pin/check hoặc điều kiện nguồn chưa đạt thì dừng phần phụ thuộc.

## 7. Bao phủ kiểm thử của kế hoạch Assessment

Các mã T bên dưới lấy từ mục13.1 kế hoạch nguồn; đây là phân công người thực hiện kiểm tra, không phải kết quả test đã chạy.

| Test nguồn | Task phụ trách |
|---|---|
| T01 | R1-20, R4-14 |
| T02 | R1-14, R3-14 |
| T03 | R3-13, R4-14 |
| T04 | R1-14 |
| T05 | R1-20, R4-14 |
| T06 | R1-20, R4-14 |
| T07 | R1-15, R4-08 |
| T08 | R1-14, R4-05 |
| T09 | R2-13, R1-14 |
| T10 | R1-14, R3-14, R3-02 |
| T11 | R3-11, R4-13 |
| T12 | R4-13 |
| T13 | R1-16, R3-10, R4-07 |
| T14 | R3-07, R4-13 |
| T15 | R1-19, R3-14 |
| T16 | R4-14 |
| T17 | R3-11, R3-13 |
| T18 | R3-13 |
| T19 | R1-20, R4-14 |
| T20 | R1-14, R4-05 |
| T21 | R3-12, R3-13 |
| T22 | R3-09, R3-13 |
| T23 | R1-17, R3-14 |
| T24 | R4-06 |
| T25 | R1-14, R3-13 |
| T26 | R1-14 |
| T27 | R1-14, R3-13 |
| T28 | R1-15, R4-08 |
| T29 | R2-13, R2-14 |
| T30 | R2-15, R1-15 |
| T31 | R3-11 |
| T32 | R1-14, R3-14, R3-02 |

## 8. Prompt nhận một nhiệm vụ

```text
Đọc AGENTS.md và docs/plans/KE_HOACH_TRIEN_KHAI_B_PIT_VA_DANH_GIA_DAU_TU.md.
Bạn là Người <1/2/3/4>, thực hiện duy nhất task <ID> trong stage đã được mở.
Đọc đúng mục nguồn ghi trong task; không sửa hai kế hoạch nguồn.
Baseline/integration HEAD: <SHA thật>.
Dependency đã bàn giao: <task IDs + SHA hoặc artifact paths + hashes>.
Thực hiện phần việc, targeted tests và self-review theo thẻ.
Không tự thay methodology, dùng baseline thay enriched hoặc dùng fixture để claim real PASS.
Không tự chuyển stage, approve, commit/push/deploy ngoài quyền đã được giao.
Kết thúc bằng diff, test thực chạy, input/output pins, trạng thái và phần còn thiếu.
```

## 9. Hồ sơ kết thúc nhiệm vụ

```text
Task / Người phụ trách / Stage:
Baseline HEAD / Dependency:
File thay đổi / Phần việc hoàn thành:
Input paths + run IDs + hashes / FIXTURE hay REAL:
Commands / tests thực chạy, fail, skip / kết quả:
Một ca đối chiếu độc lập input → output:
Output paths + hashes / verification hoặc seal nếu có:
Trạng thái PASS | PARTIAL | BLOCKED | FAIL và phạm vi:
Điều kiện chuyển bước đã đạt / phần còn thiếu:
Commit/PR sau khi được giao quyền / task nhận bàn giao:
```

Chạy targeted tests, compileall khi đổi Python, synthetic smoke khi đổi pipeline và kiểm web theo AGENTS.md. Với tài liệu-only chỉ kiểm parse/links/diff và đối chiếu evidence. Không sửa sealed bytes, bỏ assertion hoặc ghi PASS dựa trên việc file đã tồn tại.


