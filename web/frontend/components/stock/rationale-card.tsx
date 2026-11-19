import type {
  AssessmentEvidence,
  AssessmentFeature,
  AssessmentFeatureId,
  AssessmentResponse,
  AssessmentStatus,
  MetricUnit,
} from "@/lib/types";
import { formatMetric } from "@/lib/indicator-format";
import { VerdictBadge } from "./verdict-badge";

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

const VERDICT_EXPLANATIONS: Record<AssessmentStatus, string> = {
  RESEARCH_FAVORABLE:
    "Xu hướng và tài chính đều thuận lợi, đủ dữ liệu bắt buộc và không có cảnh báo.",
  WATCH:
    "Các trường hợp đủ dữ liệu còn lại, gồm tín hiệu trái chiều, dòng tiền bằng 0 và cảnh báo theo dõi.",
  CAUTION:
    "Có cảnh báo trọng yếu, hoặc cả xu hướng thị trường và sinh lời đều bất lợi.",
  INSUFFICIENT_EVIDENCE:
    "Thiếu hoặc không xác minh được dữ liệu bắt buộc tại as_of.",
};

const VERDICT_LABELS: Record<AssessmentStatus, string> = {
  RESEARCH_FAVORABLE: "Đáng cân nhắc đầu tư",
  WATCH: "Cần theo dõi",
  CAUTION: "Chưa nên ưu tiên đầu tư",
  INSUFFICIENT_EVIDENCE: "Không đủ cơ sở đánh giá",
};

const EVIDENCE_DIRECTION: Record<
  AssessmentEvidence["direction"],
  { title: string; className: string }
> = {
  FAVORABLE: { title: "Tín hiệu hỗ trợ", className: "teal" },
  CAUTION: { title: "Rủi ro / cảnh báo", className: "amber" },
  COUNTER_EVIDENCE: { title: "Bằng chứng trái chiều", className: "purple" },
};

const STATUS_LABELS: Record<string, string> = {
  OK: "Hợp lệ",
  IMPUTED_MEDIAN: "Được điền bằng trung vị",
  DATA_MISSING: "Thiếu dữ liệu",
  MISSING_INPUT: "Thiếu dữ liệu đầu vào",
  NOT_APPLICABLE: "Không áp dụng",
};

function featureForEvidence(
  evidence: AssessmentEvidence,
  features: AssessmentFeature[],
): AssessmentFeature | null {
  if (!evidence.feature_id) return null;
  return features.find((feature) => feature.feature_id === evidence.feature_id) ?? null;
}

function formatEvidenceValue(value: number | null, feature: AssessmentFeature | null) {
  if (value == null || !Number.isFinite(value)) return null;
  if (!feature?.unit) {
    return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 4 }).format(value);
  }
  const formatted = formatMetric(value, feature.unit as MetricUnit, "", false);
  const knownUnits: MetricUnit[] = ["vnd", "percent", "times", "points", "score"];
  return knownUnits.includes(feature.unit as MetricUnit)
    ? formatted
    : `${formatted} ${feature.unit}`;
}

function EvidenceItem({
  evidence,
  response,
}: {
  evidence: AssessmentEvidence;
  response: AssessmentResponse;
}) {
  const feature = featureForEvidence(evidence, response.features);
  const direction = EVIDENCE_DIRECTION[evidence.direction];
  const source = evidence.evidence_ref ?? feature?.evidence_ref;
  const status = evidence.status ?? feature?.status ?? null;
  const formattedValue = formatEvidenceValue(evidence.value, feature);
  const period = feature?.period ?? null;
  const usableFrom = feature?.usable_from_date ?? null;
  const peer = feature?.peer;
  const showPeerContext = peer != null && peer.peer_count >= 3;

  return (
    <li className="state-box">
      <div className="status-row">
        <span className={`badge ${direction.className}`}>{direction.title}</span>
        {feature && <span className="badge subtle">{FEATURE_LABELS[feature.feature_id]}</span>}
      </div>
      <p>{evidence.message}</p>
      {formattedValue != null && (
        <p className="text-small">
          Giá trị trong response: {formattedValue}
          {feature ? ` · ${feature.unit}` : ""}
        </p>
      )}
      <dl className="provenance">
        <dt>Trạng thái</dt>
        <dd>
          {status
            ? `${STATUS_LABELS[status] ?? status} (${status})`
            : "Artifact không cung cấp trạng thái riêng cho mục này"}
        </dd>
        <dt>Kỳ / ngày dữ liệu</dt>
        <dd>
          {period ?? `As of ${response.as_of}`}
          {usableFrom ? ` · khả dụng từ ${usableFrom}` : ""}
        </dd>
        <dt>Nguồn / tham chiếu</dt>
        <dd>
          {source ? (
            <code>{source}</code>
          ) : (
            "Artifact không cung cấp tham chiếu riêng cho mục này"
          )}
        </dd>
      </dl>
      {showPeerContext && peer && (
        <p className="panel-note">
          Ngữ cảnh Peers từ artifact: {peer.peer_basis}, {peer.peer_count} mã; trung vị{" "}
          {peer.peer_median == null
            ? "chưa được cung cấp"
            : formatEvidenceValue(peer.peer_median, feature)}
          {peer.p25 != null && peer.p75 != null
            ? `; IQR ${formatEvidenceValue(peer.p25, feature)}–${formatEvidenceValue(peer.p75, feature)}`
            : ""}
          . Đây chỉ là thông tin bổ sung, không thay đổi verdict.
        </p>
      )}
    </li>
  );
}

function EvidenceSection({
  title,
  emptyMessage,
  evidence,
  response,
}: {
  title: string;
  emptyMessage: string;
  evidence: AssessmentEvidence[];
  response: AssessmentResponse;
}) {
  return (
    <section aria-label={title}>
      <h3>{title}</h3>
      {evidence.length === 0 ? (
        <p className="state-box" role="status">{emptyMessage}</p>
      ) : (
        <ul className="stack-list">
          {evidence.map((item, index) => (
            <EvidenceItem
              key={`${item.feature_id ?? "general"}-${item.direction}-${index}`}
              evidence={item}
              response={response}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

export function RationaleCard({
  response,
}: {
  response: AssessmentResponse;
}) {
  return (
    <section aria-label={`Giải thích Assessment của ${response.ticker}`}>
      <div className="panel-heading">
        <div>
          <div className="eyebrow">LÝ DO VÀ BẰNG CHỨNG · AS OF {response.as_of}</div>
          <h2>Giải thích tín hiệu và rủi ro</h2>
        </div>
      </div>

      <section aria-label="Giải thích verdict">
        <h3>Ý nghĩa verdict</h3>
        <p className="status-row">
          Verdict hiện tại: <VerdictBadge status={response.assessment_status} />
        </p>
        <ul className="stack-list">
          {(Object.keys(VERDICT_EXPLANATIONS) as AssessmentStatus[]).map((status) => (
            <li className="state-box" key={status}>
              <div className="status-row">
                <strong>{VERDICT_LABELS[status]}</strong>
                {status === response.assessment_status && <span className="badge teal">Đang áp dụng</span>}
              </div>
              <p>{VERDICT_EXPLANATIONS[status]}</p>
            </li>
          ))}
        </ul>
        <p>
          Verdict lấy nguyên trạng từ Assessment response. Phần này không tự tính điểm, áp dụng
          lại rule hoặc đưa ra dự báo/lệnh giao dịch.
        </p>
      </section>

      {response.rationale && (
        <section aria-label="Rationale từ Assessment artifact">
          <h3>Lý do từ artifact</h3>
          <p>{response.rationale}</p>
        </section>
      )}

      <EvidenceSection
        title="Drivers"
        emptyMessage="Response không có mục driver nào để hiển thị."
        evidence={response.drivers}
        response={response}
      />
      <EvidenceSection
        title="Risks"
        emptyMessage="Response không có mục risk nào để hiển thị."
        evidence={response.risks}
        response={response}
      />
      <EvidenceSection
        title="Counter-evidence"
        emptyMessage="Response không có mục counter-evidence nào để hiển thị."
        evidence={response.counter_evidence}
        response={response}
      />

      <p className="panel-note" style={{ overflowWrap: "anywhere" }}>
        Nguồn chung: release <code>{response.references.release_revision}</code>; manifest{" "}
        <code>{response.references.manifest_sha256}</code>. Ngày đánh giá <time dateTime={response.as_of}>{response.as_of}</time>;
        phiên giá yêu cầu <time dateTime={response.required_price_session}>{response.required_price_session}</time>.
      </p>
    </section>
  );
}
