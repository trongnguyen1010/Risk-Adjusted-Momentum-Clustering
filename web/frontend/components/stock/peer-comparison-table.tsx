import type {
  AssessmentFeature,
  AssessmentFeatureId,
  AssessmentResponse,
} from "@/lib/types";

const FEATURE_LABELS: Record<AssessmentFeatureId, string> = {
  roe: "ROE",
  roa: "ROA",
  gross_margin: "Biên lợi nhuận gộp",
  net_margin: "Biên lợi nhuận ròng",
  debt_to_equity: "Nợ trên vốn chủ sở hữu",
  current_ratio: "Hệ số thanh toán hiện hành",
  asset_turnover: "Vòng quay tài sản",
  revenue_growth: "Tăng trưởng doanh thu",
  cfo_to_ni: "CFO trên lợi nhuận ròng",
  mom_21: "Momentum 21 phiên",
  mom_63: "Momentum 63 phiên",
  mom_126: "Momentum 126 phiên",
  mom_252: "Momentum 252 phiên",
  vol_63: "Biến động 63 phiên",
  mdd_126: "Drawdown tối đa 126 phiên",
  beta_126: "Beta 126 phiên",
  liquidity_21: "Thanh khoản 21 phiên",
  downside_vol_63: "Biến động giảm 63 phiên",
};

const PEER_BASIS_LABELS: Record<string, string> = {
  SAME_A_AND_B: "Cùng cụm A và B-PIT",
  SAME_A_AND_B_PIT: "Cùng cụm A và B-PIT",
  SAME_B_ONLY: "Cùng B-PIT",
  SAME_B_PIT: "Cùng B-PIT",
  SAME_A_ONLY: "Cùng cụm A v4",
  SAME_A_V4: "Cùng cụm A v4",
  NONE: "Không có nhóm đối chứng",
};

function numberText(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 4 }).format(value);
}

function metricValue(value: number | null, unit: string): string {
  const formatted = numberText(value);
  return value == null || !unit ? formatted : `${formatted} ${unit}`;
}

function peerBasisLabel(basis: string): string {
  return PEER_BASIS_LABELS[basis] ?? basis;
}

function dateLabel(feature: AssessmentFeature, response: AssessmentResponse): string {
  const period = feature.period ?? response.required_price_session;
  const usableFrom = feature.usable_from_date;
  if (period && usableFrom) return `${period}; khả dụng từ ${usableFrom}`;
  if (period) return period;
  if (usableFrom) return `Khả dụng từ ${usableFrom}`;
  return `As of ${response.as_of}`;
}

function SourceReference({ feature }: { feature: AssessmentFeature }) {
  return feature.evidence_ref ? (
    <code>{feature.evidence_ref}</code>
  ) : (
    <span>Artifact Assessment</span>
  );
}

export function PeerComparisonTable({
  response,
}: {
  response: AssessmentResponse;
}) {
  const sourceHashes = Object.entries(response.references.source_hashes);

  return (
    <section aria-label={`So sánh Peers theo đặc trưng của ${response.ticker}`}>
      <div className="panel-heading">
        <div>
          <div className="eyebrow">AS OF {response.as_of}</div>
          <h2>Peers theo đặc trưng</h2>
        </div>
      </div>
      <p className="panel-intro">
        Số liệu lấy từ Assessment artifact cho từng đặc trưng. Bảng không tự chọn nhóm Peers,
        tính lại thống kê hoặc thay đổi kết luận Assessment.
      </p>
      <div className="data-table-wrap">
        <table className="data-table">
          <caption className="sr-only">
            Trung vị và khoảng tứ phân vị của Peers theo từng đặc trưng cho {response.ticker}
          </caption>
          <thead>
            <tr>
              <th scope="col">Đặc trưng</th>
              <th scope="col">Giá trị {response.ticker}</th>
              <th scope="col">Cơ sở Peers</th>
              <th scope="col">Số Peers</th>
              <th scope="col">Kỳ / ngày dữ liệu</th>
              <th scope="col">Nguồn</th>
              <th scope="col">Trung vị</th>
              <th scope="col">IQR (P25–P75)</th>
            </tr>
          </thead>
          <tbody>
            {response.features.map((feature) => {
              const peer = feature.peer;
              const hasEnoughPeers = (peer?.peer_count ?? 0) >= 3;
              const median = hasEnoughPeers ? peer?.peer_median ?? null : null;
              const hasIqr = hasEnoughPeers && peer?.p25 != null && peer.p75 != null;

              return (
                <tr key={feature.feature_id}>
                  <th scope="row">
                    {FEATURE_LABELS[feature.feature_id]}
                    <small className="unit-hint">{feature.unit}</small>
                  </th>
                  <td>{metricValue(feature.value, feature.unit)}</td>
                  <td>{peer ? peerBasisLabel(peer.peer_basis) : "Chưa có dữ liệu Peers"}</td>
                  <td>{peer?.peer_count ?? 0}</td>
                  <td>{dateLabel(feature, response)}</td>
                  <td><SourceReference feature={feature} /></td>
                  <td>
                    {hasEnoughPeers
                      ? median == null
                        ? "Artifact chưa cung cấp trung vị"
                        : metricValue(median, feature.unit)
                      : "Chưa đủ 3 mã tương đồng để tính trung vị"}
                  </td>
                  <td>
                    {hasIqr
                      ? `${metricValue(peer!.p25, feature.unit)} – ${metricValue(peer!.p75, feature.unit)}`
                      : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <details className="panel-note">
        <summary>Nguồn và phiên bản artifact</summary>
        <p>
          Release {response.references.release_revision}; manifest SHA-256{" "}
          <code>{response.references.manifest_sha256}</code>.
        </p>
        {sourceHashes.length > 0 ? (
          <ul>
            {sourceHashes.map(([name, hash]) => (
              <li key={name}>
                <code>{name}</code>: <code>{hash}</code>
              </li>
            ))}
          </ul>
        ) : (
          <p>Artifact không cung cấp source hash riêng.</p>
        )}
      </details>
    </section>
  );
}
