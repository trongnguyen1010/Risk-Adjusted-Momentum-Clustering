import type {
  AssessmentFeature,
  AssessmentFeatureId,
  AssessmentHistoryPoint,
  AssessmentResponse,
  MetricUnit,
} from "@/lib/types";
import { formatMetric } from "@/lib/indicator-format";

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

const FINANCIAL_FEATURES: AssessmentFeatureId[] = [
  "roe",
  "roa",
  "gross_margin",
  "net_margin",
  "debt_to_equity",
  "current_ratio",
  "asset_turnover",
  "revenue_growth",
  "cfo_to_ni",
];

const MARKET_FEATURES: AssessmentFeatureId[] = [
  "mom_21",
  "mom_63",
  "mom_126",
  "mom_252",
  "vol_63",
  "mdd_126",
  "beta_126",
  "liquidity_21",
  "downside_vol_63",
];

const STATUS_LABELS: Record<string, string> = {
  OK: "Hợp lệ",
  IMPUTED_MEDIAN: "Được điền bằng trung vị",
  DATA_MISSING: "Thiếu dữ liệu",
  MISSING_INPUT: "Thiếu dữ liệu đầu vào",
  NOT_APPLICABLE: "Không áp dụng",
};

function historyStatus(feature: AssessmentFeature, history: AssessmentHistoryPoint[]) {
  const matchingPoint = history.find(
    (point) =>
      point.feature_id === feature.feature_id &&
      point.period === feature.period,
  );
  return matchingPoint ?? null;
}

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? "Chưa đủ cơ sở";
}

function formatFeatureValue(value: number | null, unit: string): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const formatted = formatMetric(value, unit as MetricUnit, "", false);
  const knownUnits: MetricUnit[] = ["vnd", "percent", "times", "points", "score"];
  return knownUnits.includes(unit as MetricUnit) || !unit
    ? formatted
    : `${formatted} ${unit}`;
}

function featureCoverage(
  feature: AssessmentFeature,
  history: AssessmentHistoryPoint[],
): string {
  if (feature.category === "MARKET") {
    return feature.value == null ? "0/1 snapshot có giá trị" : "1/1 snapshot có giá trị";
  }

  const rows = history.filter((point) => point.feature_id === feature.feature_id);
  if (rows.length === 0) return "Không có history trong response";
  const available = rows.filter(
    (point) =>
      (point.status === "OK" || point.status === "IMPUTED_MEDIAN") &&
      point.value != null &&
      Number.isFinite(point.value),
  ).length;
  return `${available}/${rows.length} kỳ trong history có giá trị`;
}

function SourceCell({
  feature,
  historyPoint,
}: {
  feature: AssessmentFeature;
  historyPoint: AssessmentHistoryPoint | null;
}) {
  const source = feature.evidence_ref ?? historyPoint?.source ?? null;
  if (!source) return <span>Artifact không có tham chiếu riêng</span>;
  return <code>{source}</code>;
}

function FeatureRows({
  features,
  featureIds,
  response,
}: {
  features: AssessmentFeature[];
  featureIds: AssessmentFeatureId[];
  response: AssessmentResponse;
}) {
  const orderedFeatures = featureIds
    .map((id) => features.find((feature) => feature.feature_id === id))
    .filter((feature): feature is AssessmentFeature => feature !== undefined);

  return (
    <tbody>
      {orderedFeatures.map((feature) => {
        const historyPoint = historyStatus(feature, response.history);
        const status = historyPoint?.status ?? feature.status;
        const statusSource = status === "IMPUTED_MEDIAN" ? historyPoint?.source : null;
        const valueIsMissing =
          status === "DATA_MISSING" ||
          status === "MISSING_INPUT" ||
          status === "NOT_APPLICABLE";
        const displayedValue = valueIsMissing
          ? null
          : historyPoint?.status === "IMPUTED_MEDIAN"
            ? historyPoint.value
            : feature.value;

        return (
          <tr key={feature.feature_id}>
            <th scope="row">
              <span className="metric-name">
                {FEATURE_LABELS[feature.feature_id]}
                <small className="unit-hint">{feature.unit}</small>
              </span>
            </th>
            <td>{formatFeatureValue(displayedValue, feature.unit)}</td>
            <td>
              <span>{statusLabel(status)}</span>
              <small className="unit-hint">{status}</small>
              {status === "IMPUTED_MEDIAN" && (
                <small className="unit-hint">
                  {statusSource
                    ? `Nguồn impute: ${statusSource}`
                    : feature.evidence_ref
                      ? `Tham chiếu: ${feature.evidence_ref}`
                      : "Artifact chưa cung cấp provenance riêng cho ô imputed"}
                </small>
              )}
            </td>
            <td>{featureCoverage(feature, response.history)}</td>
            <td>{feature.period ?? "Chưa có kỳ"}</td>
            <td>
              {feature.usable_from_date ? (
                <time dateTime={feature.usable_from_date}>{feature.usable_from_date}</time>
              ) : (
                "Chưa có ngày khả dụng"
              )}
            </td>
            <td>
              <SourceCell feature={feature} historyPoint={historyPoint} />
            </td>
          </tr>
        );
      })}
    </tbody>
  );
}

export function AssessmentFeatureTable({
  response,
}: {
  response: AssessmentResponse;
}) {
  const financialCount = response.features.filter(
    (feature) => feature.category === "FINANCIAL",
  ).length;
  const marketCount = response.features.filter(
    (feature) => feature.category === "MARKET",
  ).length;

  return (
    <section aria-label={`18 đặc trưng Assessment của ${response.ticker}`}>
      <div className="panel-heading">
        <div>
          <div className="eyebrow">CHI TIẾT ĐẶC TRƯNG · AS OF {response.as_of}</div>
          <h2>18 đặc trưng Assessment</h2>
        </div>
      </div>
      <p className="panel-intro">
        Bảng chỉ trình bày các giá trị và trạng thái có trong Assessment artifact. Giá trị null
        được giữ là chưa có dữ liệu; không được đổi thành 0.
      </p>

      <h3>Đặc trưng tài chính B-PIT ({financialCount}/9)</h3>
      <div className="data-table-wrap">
        <table className="data-table">
          <caption className="sr-only">Chín đặc trưng tài chính B-PIT của {response.ticker}</caption>
          <thead>
            <tr>
              <th scope="col">Đặc trưng</th>
              <th scope="col">Giá trị</th>
              <th scope="col">Trạng thái</th>
              <th scope="col">Coverage history</th>
              <th scope="col">Kỳ dữ liệu</th>
              <th scope="col">Khả dụng từ</th>
              <th scope="col">Nguồn / tham chiếu</th>
            </tr>
          </thead>
          <FeatureRows
            featureIds={FINANCIAL_FEATURES}
            features={response.features.filter((feature) => feature.category === "FINANCIAL")}
            response={response}
          />
        </table>
      </div>

      <h3>Đặc trưng thị trường A v4 ({marketCount}/9)</h3>
      <div className="data-table-wrap">
        <table className="data-table">
          <caption className="sr-only">Chín đặc trưng thị trường A v4 của {response.ticker}</caption>
          <thead>
            <tr>
              <th scope="col">Đặc trưng</th>
              <th scope="col">Giá trị</th>
              <th scope="col">Trạng thái</th>
              <th scope="col">Coverage</th>
              <th scope="col">Kỳ / phiên dữ liệu</th>
              <th scope="col">Khả dụng từ</th>
              <th scope="col">Nguồn / tham chiếu</th>
            </tr>
          </thead>
          <FeatureRows
            featureIds={MARKET_FEATURES}
            features={response.features.filter((feature) => feature.category === "MARKET")}
            response={response}
          />
        </table>
      </div>
      <p className="panel-note">
        Coverage history là số kỳ được trả trong response có giá trị OK hoặc imputed trên tổng số
        kỳ history artifact cung cấp; không diễn giải thành toàn bộ cửa sổ lookback nếu artifact
        không có đủ kỳ.
      </p>
    </section>
  );
}
