"""CSV, plot and human-readable report generation from experiment outputs."""
import csv
import io
from pathlib import Path

from ..io import atomic_write, encoded


def table_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        atomic_write(path, b"")
        return
    stream = io.StringIO(newline="")
    fields = sorted({key for row in rows for key in row})
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: encoded(value).decode("utf-8") if isinstance(value, (dict, list)) else value
                         for key, value in row.items()})
    atomic_write(path, stream.getvalue().encode("utf-8"))


def plot_artifacts(directory: Path, backtests: dict, transitions: list[dict],
                   diagnostics: list[dict], synthetic: bool) -> None:
    """Render only supplied results; this function never fits a model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    label = "data_mode=synthetic | " if synthetic else "PILOT DỮ LIỆU THẬT (data_mode=real) | "
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    benchmark_drawn = False
    for name, result in backtests.items():
        rows = result["nav"]
        ax.plot(range(len(rows)), [row["net_nav"] for row in rows], label=name)
        if not benchmark_drawn:
            level, curve = 1.0, []
            for row in rows:
                level *= 1 + row["benchmark_return"]
                curve.append(level)
            ax.plot(range(len(rows)), curve, label="benchmark", linestyle="--")
            benchmark_drawn = True
    ax.set(xlabel="Số phiên kể từ lần thực hiện đầu tiên", ylabel="NAV chuẩn hóa",
           title=label + "Mô phỏng return-space")
    ax.legend(fontsize=8)
    fig.savefig(directory / "nav.png", dpi=150)
    plt.close(fig)
    if transitions:
        k = max(row["from_cluster"] for row in transitions) + 1
        counts = [[sum(row["count"] for row in transitions
                       if row["from_cluster"] == i and row["to_cluster"] == j)
                   for j in range(k)] for i in range(k)]
        fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
        image = ax.imshow(counts, cmap="Blues")
        for i in range(k):
            for j in range(k):
                ax.text(j, i, counts[i][j], ha="center", va="center")
        ax.set(xlabel="Cluster đích đã căn chỉnh", ylabel="Cluster nguồn đã căn chỉnh",
               title=label + "Số lượng transition")
        ax.set_xticks(range(k))
        ax.set_yticks(range(k))
        fig.colorbar(image, ax=ax)
        fig.savefig(directory / "transitions.png", dpi=150)
        plt.close(fig)
    valid = [row for row in diagnostics if row.get("silhouette") is not None]
    if valid:
        ks = sorted({row["k"] for row in valid})
        fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
        ax.plot(ks, [sum(row["silhouette"] for row in valid if row["k"] == k)
                     / sum(row["k"] == k for row in valid) for k in ks], marker="o")
        ax.set(xlabel="k", ylabel="Silhouette trung bình theo tháng", title=label + "Chẩn đoán k")
        fig.savefig(directory / "k_diagnostics.png", dpi=150)
        plt.close(fig)


def write_report(path: Path, run_id: str, data_mode: str, assumptions: dict,
                 snapshot_count: int, skipped_count: int, assignment_count: int) -> None:
    report = [
        "# Báo cáo thí nghiệm " + run_id,
        "",
        "data_mode = " + data_mode,
        "",
        ("**KIỂM CHỨNG KỸ THUẬT BẰNG DỮ LIỆU GIẢ LẬP (SYNTHETIC)**"
         if data_mode == "synthetic" else
         "**KẾT QUẢ PILOT — KHÔNG PHẢI KẾT QUẢ CUỐI CÙNG CỦA LUẬN VĂN**"),
        "",
        "Mô phỏng danh mục trên chuỗi lợi suất với tỷ trọng phân số, khớp tại giá đóng cửa phiên kế tiếp. Chưa mô phỏng sổ giao dịch theo số lượng cổ phiếu thực tế.",
        "Không đánh giá trên tập kiểm định độc lập (holdout), không chọn mô hình dựa trên lợi nhuận.",
        "",
        f"Số thời điểm phân cụm: {snapshot_count}; số thời điểm bỏ qua: {skipped_count}; số bản ghi gán cụm: {assignment_count}.",
        "",
        "## Các tệp kết quả",
        "",
        "- [Chỉ tiêu hiệu quả](performance.csv)",
        "- [Đặc trưng từng cụm](profiles.csv)",
        "- [Chỉ tiêu đánh giá số cụm](diagnostics.csv)",
        "- [Ma trận chuyển cụm](transitions.csv)",
        "- [Độ ổn định qua thời gian](stability.jsonl)",
        "",
        "Khoảng tin cậy bootstrap được tính với chiến lược đã cố định; kết quả này không chứng minh ý nghĩa thống kê của chiến lược.",
        "",
        "## Các giả định được khai báo",
        "",
    ]
    labels = {"risk_free": "Lãi suất phi rủi ro", "costs": "Chi phí giao dịch và trượt giá",
              "cash_return": "Lợi suất tiền mặt", "return_semantics": "Quy ước lợi suất và mô phỏng",
              "k_rationale": "Cơ sở lựa chọn số cụm"}
    report.extend(f"- **{labels.get(key, key)}:** {value}" for key, value in assumptions.items())
    atomic_write(path, ("\n".join(report) + "\n").encode("utf-8"))
