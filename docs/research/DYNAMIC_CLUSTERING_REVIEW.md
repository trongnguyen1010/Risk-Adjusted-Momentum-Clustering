# Review Dynamic Clustering

## Trạng thái quyết định

**NOT APPROVED — chưa có concrete dynamic algorithm được phép triển khai.**

Monthly independent K-Means sau đó tính ARI, align label hoặc transition matrix là static snapshot clustering + temporal evaluation, không phải Dynamic Clustering.

Danh sách 22 reference gốc không có dedicated Dynamic Clustering primary-method section. Nhóm F trong [LITERATURE_MATRIX.md](LITERATURE_MATRIX.md) được thêm sau mentor review nhưng hiện chưa có paper đủ full-text evidence để tạo methodology entry.

## Điều kiện approval

Review phải nêu rõ:

- research objective và vì sao static baseline không đủ;
- paper/method gốc với page/section, assumptions và temporal mechanism;
- objective function/state update/regularization theo thời gian;
- initialization, hyperparameter, missing/entry/exit handling;
- leakage-safe validation và comparator;
- metric cluster quality tách khỏi temporal stability và portfolio outcome;
- computational feasibility và reproducibility artifact;
- reviewer/mentor, ngày và explicit decision `APPROVED`.

Cho tới khi tất cả mục trên hoàn tất, code chỉ được có `clustering/dynamic/base.py` interface và phải fail rõ khi request concrete algorithm.
