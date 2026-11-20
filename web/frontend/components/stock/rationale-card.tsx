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

  const hasProvenance = status || period || source || usableFrom;

  return (
    <li className="state-box" style={{ padding: "0.85rem 1rem" }}>
      <div className="status-row" style={{ marginBottom: "0.35rem" }}>
        <span className={`badge ${direction.className}`}>{direction.title}</span>
        {feature && <span className="badge subtle">{FEATURE_LABELS[feature.feature_id]}</span>}
      </div>
      <p style={{ margin: "0.25rem 0", fontWeight: 500 }}>{evidence.message}</p>
      {formattedValue != null && (
        <p className="text-small" style={{ margin: "0.2rem 0", color: "var(--muted, #64748b)" }}>
          Giá trị ghi nhận: <strong>{formattedValue}</strong>
          {feature ? ` · ${feature.unit}` : ""}
        </p>
      )}
      {hasProvenance && (
        <dl className="provenance" style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem 1rem", margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--muted, #64748b)" }}>
          {status && (
            <div>
              <dt style={{ display: "inline", fontWeight: 500 }}>Trạng thái: </dt>
              <dd style={{ display: "inline", margin: 0 }}>{STATUS_LABELS[status] ?? status}</dd>
            </div>
          )}
          {period && (
            <div>
              <dt style={{ display: "inline", fontWeight: 500 }}>Kỳ: </dt>
              <dd style={{ display: "inline", margin: 0 }}>{period}{usableFrom ? ` (công bố ${usableFrom})` : ""}</dd>
            </div>
          )}
          {source && (
            <div>
              <dt style={{ display: "inline", fontWeight: 500 }}>Nguồn: </dt>
              <dd style={{ display: "inline", margin: 0 }}><code>{source}</code></dd>
            </div>
          )}
        </dl>
      )}
      {showPeerContext && peer && (
        <p className="panel-note" style={{ marginTop: "0.4rem", fontSize: "0.8rem" }}>
          Nhóm tương đồng ({peer.peer_basis}): {peer.peer_count} mã · Trung vị:{" "}
          <strong>
            {peer.peer_median == null
              ? "chưa đủ mẫu"
              : formatEvidenceValue(peer.peer_median, feature)}
          </strong>
        </p>
      )}
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
  displayTitle?: string;
  emptyMessage: string;
  evidence: AssessmentEvidence[];
  response: AssessmentResponse;
}) {
  if (evidence.length === 0 && title === "Counter-evidence") return null;

  return (
    <section aria-label={title} style={{ marginTop: "0.75rem" }}>
      <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>{displayTitle || title}</h3>
      {evidence.length === 0 ? (
        <p className="state-box subtle" role="status" style={{ fontSize: "0.85rem", color: "var(--muted, #64748b)" }}>{emptyMessage}</p>
      ) : (
        <ul className="stack-list" style={{ display: "grid", gap: "0.5rem" }}>
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
    <section aria-label={`Giải thích Assessment của ${response.ticker}`} className="panel" style={{ marginTop: "0.75rem" }}>
      <div className="panel-heading" style={{ marginBottom: "0.75rem" }}>
        <div>
          <div className="eyebrow">CƠ SỞ VÀ TIÊU CHÍ PHÂN TÍCH · D-ASS-01</div>
          <h2>Tiêu chuẩn phân loại & Tín hiệu trọng yếu</h2>
        </div>
      </div>

      <section aria-label="Giải thích verdict" style={{ marginBottom: "1rem" }}>
        <div className="state-box" style={{ background: "rgba(14, 165, 233, 0.03)", borderColor: "rgba(14, 165, 233, 0.25)", padding: "1rem" }}>
          <div className="status-row" style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.95rem", fontWeight: 600 }}>Cơ sở xếp loại:</span>
            <VerdictBadge status={response.assessment_status} />
          </div>
          <p style={{ margin: "0 0 0.85rem 0", fontSize: "0.95rem", color: "var(--foreground, #1e293b)", lineHeight: 1.5 }}>
            {VERDICT_EXPLANATIONS[response.assessment_status]}
          </p>
          <div style={{ display: "grid", gap: "0.6rem", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 14rem), 1fr))", fontSize: "0.85rem" }}>
            <div className="state-box subtle" style={{ padding: "0.6rem 0.8rem" }}>
              <div style={{ fontWeight: 600, color: "var(--foreground, #0f172a)", marginBottom: "0.25rem" }}>📈 Động lượng thị trường</div>
              <div style={{ color: "var(--muted, #64748b)", fontSize: "0.8rem" }}>Động lượng 21, 63, 126 phiên duy trì đà tăng trưởng.</div>
            </div>
            <div className="state-box subtle" style={{ padding: "0.6rem 0.8rem" }}>
              <div style={{ fontWeight: 600, color: "var(--foreground, #0f172a)", marginBottom: "0.25rem" }}>💰 Năng lực sinh lời</div>
              <div style={{ color: "var(--muted, #64748b)", fontSize: "0.8rem" }}>ROA & Biên lãi ròng dương, ROE vượt trung vị nhóm.</div>
            </div>
            <div className="state-box subtle" style={{ padding: "0.6rem 0.8rem" }}>
              <div style={{ fontWeight: 600, color: "var(--foreground, #0f172a)", marginBottom: "0.25rem" }}>💵 Chất lượng dòng tiền</div>
              <div style={{ color: "var(--muted, #64748b)", fontSize: "0.8rem" }}>Dòng tiền kinh doanh (CFO) dương, tỷ lệ CFO/NI vững vàng.</div>
            </div>
            <div className="state-box subtle" style={{ padding: "0.6rem 0.8rem" }}>
              <div style={{ fontWeight: 600, color: "var(--foreground, #0f172a)", marginBottom: "0.25rem" }}>🛡️ Kiểm soát rủi ro</div>
              <div style={{ color: "var(--muted, #64748b)", fontSize: "0.8rem" }}>Không vi phạm cảnh báo thanh khoản hoặc sụt giảm doanh thu.</div>
            </div>
          </div>
        </div>

        <details style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "var(--muted, #64748b)" }}>
          <summary style={{ cursor: "pointer", userSelect: "none" }}>Xem định nghĩa các mức phân loại khác theo quy chuẩn</summary>
          <ul className="stack-list" style={{ marginTop: "0.5rem", display: "grid", gap: "0.35rem" }}>
            {(Object.keys(VERDICT_EXPLANATIONS) as AssessmentStatus[])
              .filter((status) => status !== response.assessment_status)
              .map((status) => (
                <li className="state-box subtle" key={status} style={{ padding: "0.5rem 0.75rem" }}>
                  <div className="status-row" style={{ marginBottom: "0.2rem" }}>
                    <strong style={{ fontSize: "0.85rem" }}>{VERDICT_LABELS[status]}</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--muted, #64748b)" }}>{VERDICT_EXPLANATIONS[status]}</p>
                </li>
              ))}
          </ul>
        </details>
      </section>

      <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 20rem), 1fr))" }}>
        <EvidenceSection
          title="Drivers"
          displayTitle="Tín hiệu hỗ trợ nổi bật (Drivers)"
          emptyMessage="Không có tín hiệu hỗ trợ riêng lẻ tại kỳ quan sát này."
          evidence={response.drivers}
          response={response}
        />
        <EvidenceSection
          title="Risks"
          displayTitle="Cảnh báo & Rủi ro cần theo dõi (Risks)"
          emptyMessage="Không ghi nhận cảnh báo rủi ro trọng yếu."
          evidence={response.risks}
          response={response}
        />
      </div>

      <EvidenceSection
        title="Counter-evidence"
        displayTitle="Bằng chứng trái chiều (Counter-evidence)"
        emptyMessage="Không có bằng chứng trái chiều."
        evidence={response.counter_evidence}
        response={response}
      />

      <p className="panel-note" style={{ overflowWrap: "anywhere", marginTop: "1rem", fontSize: "0.75rem", color: "var(--muted, #94a3b8)" }}>
        Cơ chế: Kiểm toán chuẩn D-ASS-01 · Phiên giá cơ sở: <time dateTime={response.required_price_session}>{response.required_price_session}</time>
      </p>
    </section>
  );
}
