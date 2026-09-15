# Documentation map

Chỉ các tài liệu dưới đây là nguồn sự thật đang hoạt động:

| File | Vai trò |
|---|---|
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | Sản phẩm phục vụ ai, module nào cần có |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Ranh giới source/canonical/research/product/API/web |
| [PLAN.md](PLAN.md) | Thứ tự triển khai và acceptance gates |
| [DATA_CONTRACT.md](DATA_CONTRACT.md) | Schema, semantics, versioning và quality rules |
| [DATA_PIPELINE.md](DATA_PIPELINE.md) | Nguồn, ingestion, reconciliation, PIT và scale-up |
| [RESEARCH.md](RESEARCH.md) | Literature status, feature/model/evaluation/backtest protocol |
| [API_CONTRACT.md](API_CONTRACT.md) | Public API v1 và missing-state behavior |
| [DECISIONS.md](DECISIONS.md) | Quyết định còn hiệu lực và open decisions |
| [VALIDATION.md](VALIDATION.md) | Bằng chứng test/run gần nhất |

`data/kbs_pilot_semantics.md` là evidence lịch sử duy nhất còn giữ vì immutable pilot manifests tham chiếu đúng đường dẫn đó. Nó không phải hướng dẫn phát triển hiện tại.

Tài liệu audit, phase report, dashboard draft, template rỗng và đặc tả bị trùng đã được hợp nhất hoặc xóa. Lịch sử thay đổi nằm trong `CHANGELOG.md`; không tạo thêm report trạng thái mới nếu có thể cập nhật một trong chín file trên.
