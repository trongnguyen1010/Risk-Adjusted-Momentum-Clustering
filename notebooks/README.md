# Notebook nghiên cứu

V0.1.0 chưa có notebook nghiên cứu hoặc EDA dựa trên dữ liệu thật. Tạo lần lượt:

1. `01_source_audit.ipynb`: sample vendor, units, coverage, corporate action checks.
2. `02_eda_features.ipynb`: phân phối, missingness, correlation, eligibility theo tháng; 3–5 nhận xét có số liệu.
3. `03_clustering_comparison.ipynb`: đọc runner artifacts của ba thuật toán, không copy logic fit.
4. `04_stability_backtest.ipynb`: giải thích transitions, ledger, NAV và hạn chế.

Notebook chỉ gọi `delta_t1` hoặc đọc artifacts theo manifest. Không hardcode token, path máy cá nhân hoặc chọn lại holdout. Xuất notebook sạch output nhạy cảm khi đưa vào repo.
