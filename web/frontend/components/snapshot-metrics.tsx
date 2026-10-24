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
      {snapshot.metrics.largest_share != null && (
        <div className="stock-metrics">
          {[
            ["largest_share", "Nhóm lớn nhất"],
            ["effective_k", "Số cụm hiệu dụng"],
            ["tiny_count", "Nhóm rất nhỏ"],
            ["singleton_count", "Singletons"],
          ].map(([key, label]) => (
            <div className="stock-metric" key={key}>
              <span>{label}</span>
              <strong>
                {typeof snapshot.metrics[key] === "number"
                  ? key === "largest_share"
                    ? `${number((snapshot.metrics[key] as number) * 100, 2)}%`
                    : number(snapshot.metrics[key] as number, 3)
                  : "—"}
              </strong>
            </div>
          ))}
        </div>
      )}
      {snapshot.metrics.feature_contribution &&
      typeof snapshot.metrics.feature_contribution === "object" ? (
        <details className="indicator-details">
          <summary>Feature / block contribution đã lưu</summary>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Between-centroid contribution</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(
                  snapshot.metrics.feature_contribution as Record<
                    string,
                    number
                  >,
                ).map(([field, share]) => (
                  <tr key={field}>
                    <th>{field}</th>
                    <td>{number(share * 100, 2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="panel-note">
            {Object.entries(
              (snapshot.metrics.block_contribution || {}) as Record<
                string,
                number
              >,
            )
              .map(([block, share]) => `${block}: ${number(share * 100, 2)}%`)
              .join(" · ")}{" "}
            · Không mặc định variance 50/50 đồng nghĩa separation 50/50.
          </p>
        </details>
      ) : null}
      {Array.isArray(snapshot.metrics.silhouette_quantiles) && (
        <details className="indicator-details">
          <summary>Silhouette distribution đã export</summary>
          <div className="panel-body">
            <p>Quantiles min / P10 / Q1 / median / Q3 / P90 / max:</p>
            <p className="mono">
              {(snapshot.metrics.silhouette_quantiles as number[])
                .map((v) => number(v, 4))
                .join(" · ")}
            </p>
            <p>
              Toàn bộ point distribution và per-cluster statistics có trong
              versioned source artifact; không tính lại trong browser.
            </p>
          </div>
        </details>
      )}
    </Panel>
  );
}
