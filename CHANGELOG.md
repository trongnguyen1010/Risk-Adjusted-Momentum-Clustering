# Chưa phát hành — REPRESENTATIVE_PILOT readiness (2026-09-16)

- Thêm official pilot runner/config/universe contract dùng đúng KBS direct public HTTP + CafeF direct; dry-run zero-network không thể emit PASS gate hoặc unlock scale.
- Chặn official gate khỏi legacy Vnstock SDK collector; giữ collector cho <=5-symbol reference experiments.
- Tách market pilot gate khỏi financial PIT: `PIT_UNRESOLVED` không chặn market readiness nhưng bắt buộc `financial_features_allowed=false`.
- Sửa volume classifier: chỉ exact equality/documented mapping mới xác định semantic; ACV là `UNRESOLVED`, giữ `KEEP_SOURCE_QUALIFIED`, không merge.
- Chuẩn bị immutable run/job/manifest/gate layout, resume hash guards và pilot gate chỉ unlock `M1_SCALE` sau future real evidence.
- Validation: 116/116 tests, compileall, synthetic smoke và zero-network pilot dry-run pass; GitHub CI không chạy; không thực hiện real pilot.

# Chưa phát hành — M1 Data V2 runtime reset (2026-09-16)

- Cho phép bounded private research/demo collection trên public CafeF/KBS paths theo owner-accepted risk; rights vẫn `RIGHTS_NOT_VERIFIED`, raw không redistribution và production vẫn yêu cầu licensed source.
- Thêm adapter CafeF historical limits/value, KBS/Vnstock OHLCV, financial `RAW_ONLY_PIT_UNRESOLVED`, config và runner cho đúng bốn mã SOURCE_SMOKE.

- Retire legacy runtime `data/` và generated `artifacts/` khỏi active workspace.
- Khôi phục `/data/` và `artifacts/` vào Git ignore.
- Xóa legacy product path assumptions; launcher chỉ dùng explicit config và existing bundle.
- Giữ historical KBS/Vnstock lessons trong documentation, không giữ runtime evidence.
- Active M1 data lifecycle bắt đầu lại từ source discovery và `SOURCE_SMOKE` mới.

# Chưa phát hành — M1 readiness correction (2026-09-16)

- Chuẩn hóa future artifact ID thành `<prefix>-YYYYMMDDTHHMMSSZ-xxxxxxxx` qua một helper trung tâm; giữ compatibility với mọi old immutable ID.
- Thêm local `data/ACTIVE_INDEX.json` và archive manifest; move ba unreferenced synthetic technical artifacts vào `data/archive/legacy-20260916/` mà không xóa hoặc đổi tên real/referenced evidence.
- Thêm optional canonical contract `shares_history`, generic reconciliation key và QC cho security relation, non-empty counts và availability timing; không thay legacy Vnstock promotion.
- Bổ sung discovery/smoke documentation cho capital structure với explicit availability status; chưa crawl hoặc discover endpoint thật.
- Thay gate pilot cũ bằng `SOURCE_SMOKE`, `REPRESENTATIVE_PILOT`, `M1_SCALE`, `EXTENDED_SCALE`; synthetic không thể mở gate thật và extended planner không còn cap 350.
- Đổi tên config thành `synthetic_smoke.example.json`, thêm `source_smoke.example.json` fail-closed không chứa endpoint giả và thêm hướng dẫn collection/handoff nhiều người.
- Nâng market/feature contract lên 1.4: thêm reference/ceiling/floor theo VND/share và loại Sharpe khỏi active feature snapshot; giữ read-only legacy 1.3 compatibility.
- Chuyển reconciliation sang field level với bảy trạng thái match/conflict, semantic financial report key, canonical report identity và decision records có raw hashes.
- Thêm boundary `portfolio_evaluation.enabled`; M2 configs mặc định không sinh backtest/performance.
- Viết lại Literature Matrix thành 22 row riêng với đúng năm cột; field chưa full-text review ghi `PENDING — FULL-TEXT REVIEW`, giữ rõ conflict lịch sử về Sharpe và nhóm F chưa approved.
- Không thực hiện real crawl, storage migration, DBSCAN hoặc Dynamic Clustering.
- Acceptance: baseline 70/70, sau thay đổi 83/83 tests pass; synthetic smoke `run-c10574e177a6` và M2 no-portfolio experiment `experiment-8ecc8caa6dd9` complete.

# Chưa phát hành — refactor kiến trúc DELTA (2026-09-15)

- Tái xác lập DELTA là project Research Core + Product Layer theo milestone M1/M2/M3.
- Tạo documentation onboarding tiếng Việt, Project Map, Roadmap, feature/method/evaluation/product/reproducibility contracts và research review structure.
- Hợp nhất nội dung tài liệu superseded; thay `DEVELOPMENT_RULES.md` bằng `CONTRIBUTING.md` và viết lại `AGENTS.md` cho automated agents.
- Giữ `docs/data/kbs_pilot_semantics.md` tại path cũ vì immutable evidence có thể tham chiếu.
- Tách research runner thành `experiments/protocol.py`, `runner.py`, `artifacts.py`, `reporting.py`; orchestration resolve algorithm qua registry thay vì hard-code K-Means.
- Tạo common clustering interface/registry, Ward comparator và `dynamic/base.py` guard; tách cluster, temporal và portfolio metrics thành ba module độc lập.
- Chuyển Vnstock adapter/verification vào `ingestion/sources`, thêm CafeF/VietFin fail-closed interfaces và nối legacy promotion qua normalization/reconciliation generic có conflict records.
- Tổ chức config theo data/features/experiments/product; thêm PCA snapshot preprocessing và `pca_kmeans.example.json` không fit future/holdout.
- Migrate test suite sang unit/integration/regression theo subsystem, giữ assertion cũ và bổ sung invariant tests; acceptance đạt 70/70 tests, compile/JSON/link/web/diff checks pass.
- Synthetic smoke `run-5016b877990c` và PCA+K-Means technical experiment `experiment-85dd31d7598b` complete; không xem đây là research result.

# 0.5 — product-first restructuring (2026-09-14)

- Reframe the repository as Delta Intelligence: company/ticker intelligence is the product surface and clustering is one bounded analytical capability.
- Add immutable company-detail bundle builder, safe file repository, read-only API edge and responsive web shell.
- Preserve missing fundamentals/news/sentiment as explicit unavailable states; never fabricate zero values.
- Add product requirements and API v1 contract; rewrite architecture and execution plan into product and research tracks.
- Make direct-file opening show a styled server-required message, add one-command PowerShell launcher, and keep asset URLs valid under both file and HTTP contexts.
- Remove superseded KBS unresolved/smoke config and reports whose referenced raw runs were already removed.
- Repair the retained real-pilot latest pointer after generated-data cleanup.
- Consolidate 25 scattered documentation files into a canonical 9-document set plus index and one immutable-manifest evidence file; remove duplicate audits, phase reports, drafts and empty templates.
- Remove legacy real/offline pilot entry scripts and configs; extract the only reused benchmark-calendar helper into the generic ingestion layer.

# 0.4 — research realignment foundation (2026-09-14)

- Add a framework decision report: research framework is not final-standard, engineering core is reusable; recommend `RETAIN CORE / ARCHIVE LEGACY / REBUILD RESEARCH LAYER` rather than deleting the whole repository.
- Re-read the complete 1,266-line instruction attachment and 74-line paper list; revise the roadmap around all 22 papers and their stated purposes across groups A–E. Correct the evidence status: only Aslam is locally full-text reviewed; Han/Nanda/DBSCAN have primary partial review, while the remaining listed works still require full-text review.
- Clean reproducible generated data: remove obsolete synthetic runs/experiments/canonical/offline-pilot outputs, temporary PDF/test extraction, one interrupted vendor run and one incomplete real-pilot folder; retain complete real source/pilot evidence and the referenced regression run.
- Audit leader requirements against local research PDFs, reading list, code, configs, artifacts and Git state; verdict `MAJOR REALIGNMENT REQUIRED`.
- Document that current implementation is a monthly snapshot K-Means baseline, not an Aslam (2025) replication or approved Dynamic Clustering method.
- Enforce three calendar years observed history for real clustering; add eligible/reference/excluded segments and coverage.
- Prevent Sharpe/ROI from clustering inputs and selection; retain Sharpe as portfolio-performance metric.
- Add optional quarterly financial report/fact PIT contracts and percentage/top-N universe capability.
- Add source comparison, reconciliation design, dashboard contract, deliverable folders and P0–P2 roadmap. No large crawl, rename, remote change or commit was performed.

# 0.3 — real KBS pilot (2026-09-12)

- Resolve SDK 1000x price conversion using source/API and independent FPT price; detect vendor historical technical adjustment instead of mislabeling raw.
- Promote explicit vendor_adjusted convention; support raw-close features/backtests when unadjusted mapping is justified.
- Add retrospective availability safety delay, bounded provisional master, benchmark-derived calendar, nullable turnover and assumed rf.
- Add real-pilot runner, 10-symbol 2023-2025 config, source snapshots, lineage and acceptance evidence.
- Add conversion, optional-field, corrupt-OHLC, raw-feature and calendar tests.
- Remove unused Protocol interfaces/app/notebook placeholders; retain old raw evidence and test fixtures.

# Nhật ký thay đổi

## SOURCE_SMOKE failure resolution — 2026-09-16

- Phân loại VNM CafeF `2021-09-09` là `PROVIDER_CORRUPT_ROW`; chỉ exact versioned evidence mới được exclude khỏi constraint promotion, raw/finding được giữ và mismatch fail-closed.
- Phân loại ACV volume là `SOURCE_SEMANTIC_DIFFERENCE`; giữ giá trị source-qualified riêng biệt, không giả định equality hay overwrite.
- Sửa provenance KBS direct HTTP thành `acquisition_client=delta_public_http`, giữ `endpoint_discovered_via=vnstock`.
- Bổ sung machine-readable SOURCE_SMOKE gate, actual CafeF contributing-page hashes, corporate-action/shares evidence và coverage tests.
- Real rerun `source-smoke-20260916T122331Z-79427ec6` PASS và chỉ unlock `REPRESENTATIVE_PILOT`; không chạy pilot hoặc large-scale crawl.

## Bổ sung ngày 12/09/2026 — Báo cáo tiếng Việt

- Chuyển báo cáo triển khai theo giai đoạn và báo cáo rà soát repository sang tiếng Việt.
- Chuyển mẫu sinh report nghiên cứu và phần diễn giải giả định trong cấu hình demo sang tiếng Việt; giữ nguyên tham số và công thức nghiên cứu.
- Sinh bản report pilot tiếng Việt trong một thí nghiệm mới để giữ nguyên báo cáo và checksum của các lần chạy cũ.
- Việt hóa phần nhật ký v0.2 và các quyết định ADR-007 đến ADR-015; bổ sung ADR-016 về ngôn ngữ báo cáo theo yêu cầu người dùng.
- Bản tiếng Việt: `experiment-6436b9f4eb78`. Đối chiếu 9 tệp kết quả số với bản trước: giống nhau từng byte; xác minh toàn bộ checksum đầu ra của cả hai lần chạy và kiểm tra cú pháp thành công. Không chạy lại toàn bộ 44 kiểm thử vì lần này chỉ sửa nội dung báo cáo; kết quả 44/44 thuộc đợt triển khai kỹ thuật trước.

## 0.2.0 — 2026-09-12

- Rà soát repository, SDK đã cài và ý nghĩa các trường dữ liệu nhà cung cấp; ghi rõ đơn vị, phương pháp điều chỉnh giá, múi giờ và dữ liệu tham chiếu còn chưa xác minh. Chưa cho phép chuyển đổi hoặc tải diện rộng dữ liệu thật.
- Bổ sung bộ chuyển đổi có kiểm tra bằng chứng và dữ liệu bất biến, ghép nguồn tham chiếu, cách ly lỗi và đầu vào dùng chung cho pipeline chuẩn; có bộ thử nghiệm giả lập tái lập được.
- Nâng hợp đồng dữ liệu lên 1.1: hỗ trợ UPCOM, cho phép thiếu giá/khối lượng chưa xác minh, bổ sung thời điểm khả dụng và cơ sở của lịch/chỉ số, thông tin sự kiện/lãi suất, số quan sát và lý do thiếu đặc trưng, động lượng điều chỉnh rủi ro và độ biến động giảm giá.
- Bổ sung điều kiện kiểm tra chỉ số tham chiếu, OHLC và tính đúng thời điểm; đặt lại cửa sổ khi đổi cơ sở điều chỉnh giá. Giữ nguyên định nghĩa động lượng, độ biến động, Sharpe, beta và mức sụt giảm tối đa. Tiếp tục một lần chạy đã hoàn tất chỉ kiểm tra, không ghi đè.
- Triển khai KMeans xác định theo từng thời điểm, tiền xử lý, đánh giá số cụm k, nhãn có ý nghĩa kinh tế, độ ổn định không phụ thuộc hoán vị nhãn và ma trận chuyển cụm đã căn chỉnh.
- Bổ sung mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp sau tín hiệu, chi phí, bốn chiến lược, so sánh chỉ số tham chiếu, bootstrap ghép cặp, phân tích giai đoạn/độ nhạy chi phí và báo cáo/biểu đồ theo phiên bản.
- Bổ sung dữ liệu mẫu và kiểm thử tích hợp/hồi quy ngoại tuyến; chỉ cho tải lớn sau khi bộ thử nghiệm thật đạt. Sổ giao dịch theo số lượng cổ phiếu, nghiệm thu dữ liệu thật và quy trình kiểm định độc lập đã khóa vẫn chưa hoàn tất.
- Phát hiện các file nhà cung cấp có mã băm lệch do đổi định dạng; bổ sung phục hồi đúng bytes từ cache sang snapshot mới có thông tin truy vết, không sửa file gốc.
- Kết quả kiểm chứng cuối đợt triển khai: 44/44 kiểm thử đạt; pilot 6 mã giả lập trong 18 tháng chạy xuyên suốt. Trạng thái validation hiện được hợp nhất tại `docs/REPRODUCIBILITY.md`; báo cáo phase cũ đã được gỡ.

Ghi thay đổi có ảnh hưởng tới người dùng/developer và bằng chứng kiểm thử. Không dùng changelog như bằng chứng kết quả nghiên cứu chưa chạy.

## 0.1.0 - 2026-09-11

### Bổ sung

- Đánh giá năm PDF, kiến trúc module, data contract, feature specification, source evaluation, plan M1/M2/M3, development rules và decision log.
- Core Python CLI: CSV/HTTP JSON → raw snapshot → normalization/QC → clean JSONL → monthly features.
- Crawl checkpoint theo trang, SHA-256, config/code/data hash, bounded retry, rate limit, timeout, pagination và resume.
- Vnstock Community 4.0.6 collector riêng cho sample equity/index và listing; vendor staging không tự được xem là canonical.
- 12 schema JSON theo định dạng table contract; runtime validate cho input, vendor snapshot và feature, interface contracts cho clustering/evaluation/backtest.
- Synthetic fixture 12 mã/18 tháng và 27 test về feature, QC, availability, pagination/retry/resume và cô lập SDK worker.
- Lock dependencies tùy chọn cho môi trường Vnstock đã cài, template model card/strategy spec/weekly report.

### Quyết định và giới hạn

- JSONL là định dạng MVP; chưa có Parquet storage hoặc incremental merge tự động.
- raw_close nullable để ghi nhận dữ liệu thiếu; không tự đồng nhất raw và adjusted.
- M2/M3 là interfaces và schema dự kiến; chưa có trained models, backtest hoặc UI hoàn chỉnh.
- Chưa chứng minh coverage 300 mã/5 năm hoặc hoàn thành nghiệm thu M1. Trạng thái hiện tại xem tại `docs/REPRODUCIBILITY.md`.
