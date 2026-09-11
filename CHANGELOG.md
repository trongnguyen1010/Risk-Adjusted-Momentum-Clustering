# Changelog

Ghi thay đổi có ảnh hưởng tới người dùng/developer và bằng chứng kiểm thử. Không dùng changelog như bằng chứng kết quả nghiên cứu chưa chạy.

## 0.1.0 - 2026-09-11

### Added

- Đánh giá năm PDF, kiến trúc module, data contract, feature specification, source evaluation, plan M1/M2/M3, development rules và decision log.
- Core Python CLI: CSV/HTTP JSON → raw snapshot → normalization/QC → clean JSONL → monthly features.
- Crawl checkpoint theo trang, SHA-256, config/code/data hash, bounded retry, rate limit, timeout, pagination và resume.
- Vnstock Community 4.0.6 collector riêng cho sample equity/index và listing; vendor staging không tự được xem là canonical.
- 12 schema JSON theo định dạng table contract; runtime validate cho input, vendor snapshot và feature, interface contracts cho clustering/evaluation/backtest.
- Synthetic fixture 12 mã/18 tháng và 27 test về feature, QC, availability, pagination/retry/resume và cô lập SDK worker.
- Lock dependencies tùy chọn cho môi trường Vnstock đã cài, template model card/strategy spec/weekly report.

### Decisions and limitations

- JSONL là định dạng MVP; chưa có Parquet storage hoặc incremental merge tự động.
- raw_close nullable để ghi nhận dữ liệu thiếu; không tự đồng nhất raw và adjusted.
- M2/M3 là interfaces và schema dự kiến; chưa có trained models, backtest hoặc UI hoàn chỉnh.
- Chưa chứng minh coverage 300 mã/5 năm hoặc hoàn thành nghiệm thu M1. Chi tiết kết quả chạy ở `docs/VALIDATION.md`.
