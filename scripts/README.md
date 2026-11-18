# Bảng lệnh scripts/

Chạy mọi lệnh từ thư mục gốc repo. Script nằm phẳng trong `scripts/` vì nhiều manifest/config đã ghi
đường dẫn của chúng; đừng di chuyển hoặc đổi tên. Bảng dưới chia theo nhóm để dễ tìm.

## Đang dùng

| Nhóm | Script | Việc |
|---|---|---|
| M3 | `run_m3.py --segment development\|holdout\|final [--targets-only]` | Chọn danh mục và backtest theo `configs/experiments/m3_strategy_v1.json` |
| M3 | `build_financial_pit_clusters.py` | Build nhãn B-PIT (`data/financial/b_pit_v1/`) |
| M3 | `m3_stage0.py`, `m3_feasibility_variants.py` | Manifest đầu vào, đếm tập ứng viên (không tính lợi suất) |
| M3 | `publish_hf_data.py`, `publish_m3_data.py` | Đẩy dữ liệu M3/web lên HuggingFace |
| Ngày công bố | `crawl_cafef_disclosure_dates.py`, `build_financial_availability.py` | Crawl ngày gửi BCTC CafeF, build bảng `usable_from_date` |
| Indicators v1 | `build_indicator_inputs.py` → `build_indicators.py` → `verify_indicators.py` | Lớp chỉ số sản phẩm D-IND-01 |
| Phân cụm A/B/C | `run_clustering_rework_v2.py`, `dual_cluster_review.py`, `combined_reference.py [--execute]`, `verify_combined_reference.py`, `build_cluster_comparison_report.py` | Mô hình A/B v4 và tham chiếu C |
| Web | `build_delta_bundle_v4.py`, `export_delta_terminal.py`, `start_delta_terminal.py`, `verify_delta_terminal.py`, `start_product.ps1` | Bundle và chạy web local |
| Web QA | `test_delta_frontend.cjs`, `verify_delta_ui.cjs`, `measure_delta_ui.cjs` | Kiểm giao diện |
| Corporate actions | `corporate_actions/collect_vsdc_recovery_supervisor_v7.py` | Supervisor V7 chạy worker V6 (xem `docs/README.md`) |
| Kiểm repo | `verify_repository_r1.py`, `project_cleanup.py check` | Kiểm toàn vẹn sau dọn dẹp |

## Lịch sử (giữ để tái lập, không chạy cho việc mới)

| Nhóm | Mẫu tên | Ghi chú |
|---|---|---|
| Crawl và xử lý tài chính | `financial_*.py\|.ps1` (107 file), `crawl_financial*`, `crawl_cafef_financial.py`, `probe_financial_*`, `review_financial_scale.py`, `extract_financial_selected_pages.py`, `ocr_financial_pages.ps1`, `setup_financial_ocr.py`, `calculate_cached_financial_scores.py`, `build_financial_serving.py`, `integrate_financial_trial.py` | Các campaign đã xong; dataset hiện hành ở `data/financial/` |
| Financial PIT cũ | `run_fin_pit_*`, `validate_fin_pit_1a_continuation_proposal.py` | Trước B-PIT |
| Thị trường C5–C8 | `build_cafef_c*`, `run_cafef_*`, `verify_cafef_*`, `*cafef_expansion*`, `build_m1_market_foundation_report.py` | M1 |
| M2 K=2 (LEGACY) | `build_m2_prep.py`, `run_m2_global_k.py`, `export_m2_selected_k.py`, `verify_m2_task12.py`, `generate_m2_task13_handoff.py`, `compare_m2_vs_rework.py`, `run_clustering_rework_v1.py` | Đối chứng |
| Integration market–financial | `import_market_bundle.py`, `verify_market_financial_integration.py`, `market_financial_integration.ps1` | Xem ghi chú bên dưới |
| DELTA upgrade R1 | `run_delta_upgrade_r1.py`, `verify_delta_upgrade_r1.py`, `audit_delta_upgrade.py`, `export_delta_research_preview.py`, `verify_delta_research_preview.py`, `build_delta_bundle_v2.py`, `build_delta_bundle_v3.py` | Byte được ghim trong `.gitattributes` |
| Corporate actions / HNX / VCI | `*corporate_action*`, `*hnx_*`, `*vci_calendar*`, `*dtp_asg*`, `*gsp_kpf*`, `*abb_aas*` ở gốc `scripts/`; `corporate_actions/` chứa shim gọi các file này và các runner VSDC | Code chính import `delta_t1.ingestion.<module>` |
| Khác | `generate_demo.py`, `run_research.py`, `export_presentation_guide_to_docx.py`, `prune_financial_archives.ps1`, `monitor_cafef_worker.py` | |

## Ghi chú lịch sử

## Indicators v1 (D-IND-01) — lớp chỉ số sản phẩm

```powershell
python scripts/build_indicator_inputs.py   # Giai đoạn 1: ~7 phút, ghi data/financial/indicators_v1/inputs/<run-id>/
python scripts/build_indicators.py         # Giai đoạn 2: ~1 phút, đọc inputs/latest.json, ghi results/<run-id>/
python scripts/verify_indicators.py        # Giai đoạn 3: ~20 giây, ghi qa-report.md vào results/<run-id>/
```

Run mới không ghi đè run cũ; `inputs/latest.json` và `results/latest.json` trỏ run gần nhất.

## A/B/C reference hiện hành

```powershell
python scripts/dual_cluster_review.py
python scripts/combined_reference.py
python scripts/combined_reference.py --execute
python scripts/verify_combined_reference.py --result data/experiments/combined_reference_v1/results/3904b52cda7753aeac90
python scripts/build_cluster_comparison_report.py
```

C đã được owner duyệt/chạy; cùng code/config/pins sẽ verify/reuse immutable result,
không tự refit. Default combined_reference.py chỉ preflight. A/B giữ modelnguồn.
Các bảng annualjoin là ex-postreference, không trading/PITinput. Full replay cần
localdata/evidence; Git không chứa toàn bộ raw hoặc prepared14-featuretable.


## Integration market–financial — 23/10/2026

Financial Execution56 checkpoint `819cd82` đã merge cùng market `340519d` trên
`integration/market-financial`. C8 V2 giữ19/19hashes; current market verifier kiểm84models,
75.801assignments, nearest centroid và eligibility, tạo reference handoff có version.
Financial vẫn11.720annualrows/1.172symbols; model không refit.

Shared KMeans/preprocessing hiện kế thừa market. Hai file source đã pin của Execution56
được lưu exact bytes tại `M2/artifacts/financial-execution56-frozen-source-v2/`;
historical review dùng explicit source overlay và output mới, không sửa frozen input hashes.

```powershell
python scripts/import_market_bundle.py 'C:/Users/ASUS/Downloads/DELTA_02_ACTIVE_M2_M3.zip'
python scripts/verify_market_financial_integration.py --publish
python scripts/financial_full10_review.py --source-root M2/artifacts/financial-execution56-frozen-source-v2 --output M2/artifacts/financial-execution56-integration-review-v2
```

Tại cuối2025 có1.148financialsymbols đồng thời market-ready; giao theo snapshot thay đổi.
Chưa có availability-aware historical join hoặc model kết hợp. Quality REVIEW_REQUIRED,
strict PIT/research/M3 vẫn false. Tests/gates integration được ghi ở Current status.

Lệnh gọn hiện hành: `scripts/market_financial_integration.ps1 -Mode Verify -Python <python.exe>`.
`-Mode Test` chạy targeted regression; `-Mode Import -Bundle <zip>` nhập bundle đã pin.
Runtime local hiện dùng Python ở `C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`;
wrapper thêm `.tools/market-runtime` và `.tools/research-runtime` vào PYTHONPATH.
Máy mới dùng Python3.12 và `requirements-market-integration.lock.txt`; Streamlit thuộc extra dashboard.

## Nội dung từ checkpoint trước integration

Đọc [documentation index](../docs/README.md) trước. Tên có số phiên bản trong
script/config cũ là lineage cần giữ, không phải lời mời chạy lại campaign.

| Việc cần làm | Điểm vào |
|---|---|
| Xem tiến độ baseline financial | `financial_full10_baseline.ps1 -Mode Status` |
| Kiểm input / chạy lại đúng protocol baseline | `financial_full10_baseline.ps1 -Mode Check` / `-Mode Run` (thêm `-Python` nếu cần) |
| Kiểm độc lập baseline, không refit | `python scripts/financial_full10_review.py` |
| Lấy dataset tài chính hiện hành để bàn giao | [Financial reference2016–2025](../data/handoffs/financial-reference-2016-2025/README.md) |
| Xem trạng thái DStock đã hoàn tất | `financial_dstock_remaining.ps1 -Mode Status` |
| Replay DStock offline | `financial_dstock_remaining.ps1 -Mode Offline` từprojectroot |
| Theo dõi campaign qua dashboard | `financial_workflow_monitor.ps1` — dashboard acquisition cũ không thay counter DStock |
| Kiểm gói dọn dẹp23/10 | `project_cleanup.py check` |
| Khôi phục report/helper đã lưu ZIP | `project_cleanup.py restore` — không ghi đè nội dung khác hash |

Python của runtime hiện có:

Baseline đã hoàn tất; [report](../artifacts/reports/financial-full10-baseline-v1/report.md).
Run giữ checkpoint theo năm và pins của config/code/input; resume chỉ tái sử dụng
checkpoint khớp identity/checksum. Đổi input/protocol sinh run khác, không ghi đè.
Log của lượt này: `.tmp/financial-full10-baseline.log`; trạng thái bền vững nằm ở
`data/financial/financial_full10_baseline_v1/pipeline-status.json`.

```powershell
& 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' scripts/project_cleanup.py check
```

`project_cleanup.ps1 -Mode Prune` chỉ gỡ đúng các file trong plan đã verify,
kiểm archive hash, input anchors, đường dẫn tuyệt đối và hash từng file trước
khi xóa. Không dùng để xóa campaign khác. `plan`/`pack` là bước chuẩn bị một lần;
không tạo lại plan sau khi đã prune. Cache Python/test có thể tái tạo.

Các runner/config tài chính cũ còn ở project vì đang là import, dependency hoặc
implementation pin. Đổi tên/move chúng cần migration riêng; không dùng việc
đổi tên để sửa frozen hashes. Bước phân cụm chưa chạy trong lượt cleanup.
