import { AlertTriangle, CheckCircle2, ShieldCheck, TrendingUp, Wallet, CircleDollarSign } from "lucide-react";
import type {
  AssessmentEvidence,
  AssessmentFeature,
  AssessmentFeatureId,
  AssessmentResponse,
  AssessmentStatus,
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

const VERDICT_EXPLANATIONS: Record<AssessmentStatus, string> = {
  RESEARCH_FAVORABLE:
    "Xu hướng và tài chính đều thuận lợi, đủ dữ liệu bắt buộc và không có cảnh báo.",
  WATCH:
    "Các trường hợp đủ dữ liệu còn lại, gồm tín hiệu trái chiều, dòng tiền bằng 0 và cảnh báo theo dõi.",
  CAUTION:
    "Có cảnh báo trọng yếu, hoặc cả xu hướng thị trường và sinh lời đều bất lợi.",
  INSUFFICIENT_EVIDENCE:
    "Thiếu hoặc không xác minh được dữ liệu bắt buộc tại ngày đánh giá.",
};

const VERDICT_LABELS: Record<AssessmentStatus, string> = {
  RESEARCH_FAVORABLE: "Đáng cân nhắc đầu tư",
  WATCH: "Cần theo dõi",
  CAUTION: "Chưa nên ưu tiên đầu tư",
  INSUFFICIENT_EVIDENCE: "Không đủ cơ sở đánh giá",
};

const EVIDENCE_DIRECTION: Record<
  AssessmentEvidence["direction"],
  { title: string; toneColor: string; badgeClass: string }
> = {
  FAVORABLE: { title: "Tín hiệu hỗ trợ", toneColor: "var(--teal)", badgeClass: "teal" },
  CAUTION: { title: "Rủi ro / cảnh báo", toneColor: "var(--amber)", badgeClass: "amber" },
  COUNTER_EVIDENCE: { title: "Bằng chứng trái chiều", toneColor: "var(--purple)", badgeClass: "purple" },
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
  const Icon = evidence.direction === "FAVORABLE" ? CheckCircle2 : AlertTriangle;

  return (
    <li
      style={{
        background: "var(--surface-2)",
        border: "1px solid var(--line)",
        borderLeft: `3px solid ${direction.toneColor}`,
        borderRadius: "8px",
        padding: "10px 14px",
        textAlign: "left",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
        <Icon size={16} style={{ color: direction.toneColor, flexShrink: 0, marginTop: "3px" }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: 0, fontSize: "14px", fontWeight: 500, color: "var(--text)", lineHeight: 1.5 }}>
            {evidence.message}
          </p>
          {(feature || formattedValue != null || period || source) && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 12px", marginTop: "4px", fontSize: "12px", color: "var(--muted)" }}>
              {feature && <span>{FEATURE_LABELS[feature.feature_id]}</span>}
              {formattedValue != null && <span>Giá trị: {formattedValue}</span>}
              {status && <span>{STATUS_LABELS[status] ?? status}</span>}
              {period && <span>Kỳ: {period}{usableFrom ? ` (công bố ${usableFrom})` : ""}</span>}
              {source && <code>{source}</code>}
              {showPeerContext && peer && peer.peer_median != null && (
                <span>Trung vị Peers ({peer.peer_count} mã): {formatEvidenceValue(peer.peer_median, feature)}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function EvidenceSection({
  title,
  displayTitle,
  emptyMessage,
  evidence,
  response,
}: {
  title: string;
  displayTitle: string;
  emptyMessage: string;
  evidence: AssessmentEvidence[];
  response: AssessmentResponse;
}) {
  if (evidence.length === 0 && title === "Counter-evidence") return null;

  return (
    <section aria-label={title}>
      <h3 style={{ fontSize: "14px", fontWeight: 600, color: "var(--text)", margin: "0 0 10px 0" }}>
        {displayTitle} ({evidence.length})
      </h3>
      {evidence.length === 0 ? (
        <p
          role="status"
          style={{
            margin: 0,
            padding: "12px 14px",
            borderRadius: "8px",
            background: "var(--surface-2)",
            border: "1px solid var(--line)",
            fontSize: "13px",
            color: "var(--muted)",
          }}
        >
          {emptyMessage}
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "8px" }}>
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
    <section aria-label={`Giải thích Assessment của ${response.ticker}`} className="panel section-gap">
      <div className="panel-heading" style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "flex-end", gap: "12px" }}>
        <div>
          <div className="eyebrow">CƠ SỞ VÀ TIÊU CHÍ PHÂN TÍCH · D-ASS-01</div>
          <h2>Tiêu chuẩn phân loại & Tín hiệu trọng yếu</h2>
        </div>
        <details style={{ fontSize: "12px", color: "var(--muted)" }}>
          <summary style={{ cursor: "pointer", userSelect: "none", color: "var(--text-2)" }}>
            Định nghĩa 4 mức phân loại
          </summary>
          <ul style={{ listStyle: "none", margin: "8px 0 0", padding: "10px 12px", background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: "8px", display: "grid", gap: "6px", maxWidth: "460px" }}>
            {(Object.keys(VERDICT_EXPLANATIONS) as AssessmentStatus[]).map((status) => (
              <li key={status} style={{ fontSize: "12px", lineHeight: 1.45 }}>
                <strong style={{ color: "var(--text)" }}>{VERDICT_LABELS[status]}:</strong>{" "}
                <span style={{ color: "var(--muted)" }}>{VERDICT_EXPLANATIONS[status]}</span>
              </li>
            ))}
          </ul>
        </details>
      </div>

      <div
        style={{
          display: "grid",
          gap: "10px",
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          padding: "0 22px 18px",
        }}
      >
        <div style={{ background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: "8px", padding: "12px 14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 600, fontSize: "13px", color: "var(--text)", marginBottom: "4px" }}>
            <TrendingUp size={15} style={{ color: "var(--teal)" }} />
            <span>Động lượng thị trường</span>
          </div>
          <div style={{ color: "var(--muted)", fontSize: "12px", lineHeight: 1.5 }}>
            Xu hướng 63 &amp; 126 phiên dương; 21 hoặc 252 phiên tích cực.
          </div>
        </div>
        <div style={{ background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: "8px", padding: "12px 14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 600, fontSize: "13px", color: "var(--text)", marginBottom: "4px" }}>
            <CircleDollarSign size={15} style={{ color: "var(--teal)" }} />
            <span>Năng lực sinh lời</span>
          </div>
          <div style={{ color: "var(--muted)", fontSize: "12px", lineHeight: 1.5 }}>
            ROA &amp; Biên lợi nhuận ròng dương; đối chiếu ROE với nhóm tương đồng.
          </div>
        </div>
        <div style={{ background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: "8px", padding: "12px 14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 600, fontSize: "13px", color: "var(--text)", marginBottom: "4px" }}>
            <Wallet size={15} style={{ color: "var(--teal)" }} />
            <span>Chất lượng dòng tiền</span>
          </div>
          <div style={{ color: "var(--muted)", fontSize: "12px", lineHeight: 1.5 }}>
            Dòng tiền kinh doanh (CFO) dương khi lợi nhuận sau thuế dương.
          </div>
        </div>
        <div style={{ background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: "8px", padding: "12px 14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 600, fontSize: "13px", color: "var(--text)", marginBottom: "4px" }}>
            <ShieldCheck size={15} style={{ color: "var(--teal)" }} />
            <span>Kiểm soát rủi ro</span>
          </div>
          <div style={{ color: "var(--muted)", fontSize: "12px", lineHeight: 1.5 }}>
            Không vi phạm cảnh báo thanh khoản, dòng tiền âm hay biên lãi/thanh toán.
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gap: "16px",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 20rem), 1fr))",
          padding: "0 22px 20px",
          alignItems: "start",
        }}
      >
        <EvidenceSection
          title="Drivers"
          displayTitle="Tín hiệu hỗ trợ (Drivers)"
          emptyMessage="Không có tín hiệu hỗ trợ riêng lẻ tại kỳ quan sát này."
          evidence={response.drivers}
          response={response}
        />
        <EvidenceSection
          title="Risks"
          displayTitle="Cảnh báo & Rủi ro cần lưu ý (Risks)"
          emptyMessage="Không ghi nhận cảnh báo rủi ro trọng yếu."
          evidence={response.risks}
          response={response}
        />
      </div>

      {response.counter_evidence.length > 0 && (
        <div style={{ padding: "0 22px 20px" }}>
          <EvidenceSection
            title="Counter-evidence"
            displayTitle="Bằng chứng trái chiều (Counter-evidence)"
            emptyMessage="Không có bằng chứng trái chiều."
            evidence={response.counter_evidence}
            response={response}
          />
        </div>
      )}
    </section>
  );
}
