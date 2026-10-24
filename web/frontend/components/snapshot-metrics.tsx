import type { Snapshot } from "@/lib/types";
import { number } from "@/lib/format";
import { Panel, Badge } from "./ui";
export function SnapshotMetrics({ snapshot }: { snapshot: Snapshot }) {
  const fields = [
    ["silhouette", "Silhouette"],
    ["davies_bouldin", "Davies–Bouldin"],
    ["calinski_harabasz", "Calinski–Harabasz"],
    ["min_cluster_size", "Cụm nhỏ nhất"],
  ];
  return (
    <Panel
      className="section-gap"
      title="Chỉ số đánh giá mô hình đã lưu"
      eyebrow="CHẤT LƯỢNG CỤM · KHÔNG PHẢI HIỆU QUẢ DANH MỤC"
      action={<Badge tone="amber">Cần rà soát</Badge>}
    >
      <div className="stock-metrics">
        {fields.map(([key, label]) => (
          <div className="stock-metric" key={key}>
            <span>{label}</span>
            <strong>
              {typeof snapshot.metrics[key] === "number"
                ? number(snapshot.metrics[key] as number, 4)
                : "Chưa có dữ liệu"}
            </strong>
          </div>
        ))}
      </div>
      <p className="panel-note">
        Đọc từ kết quả đã lưu. Silhouette cao vẫn có thể đi kèm mất cân bằng
        nghiêm trọng; các chỉ số này không chứng minh tính ổn định, khả năng
        dùng PIT hay hiệu quả đầu tư.
      </p>
    </Panel>
  );
}
