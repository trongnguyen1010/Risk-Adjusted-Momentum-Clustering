# Review Dynamic Clustering

## Trạng thái quyết định

**NOT APPROVED — chưa có concrete dynamic algorithm được phép triển khai.**

Monthly independent K-Means sau đó tính ARI, align label hoặc transition matrix là static snapshot clustering + temporal evaluation, không phải Dynamic Clustering.

Danh sách 22 reference gốc không có dedicated Dynamic Clustering primary-method section. Supporting file `LITERATURE_MATRIX_COMPLETE.md` hiện có ba candidate F1–F3; presence và summaries của chúng không phải explicit methodology approval. Trong số đó, João et al. (2024) gần kiến trúc DELTA nhất vì temporal persistence trên static-style assignments, còn HMM panel method phức tạp hơn. Cả hai vẫn cần review objective, equations, hyperparameters, entry/exit và leakage controls theo checklist dưới đây.

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
