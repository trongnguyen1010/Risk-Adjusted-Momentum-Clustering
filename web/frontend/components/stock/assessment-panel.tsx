"use client";

import type {
  AssessmentClusterProfile,
  AssessmentFeatureId,
  AssessmentQuery,
  AssessmentResponse,
} from "@/lib/types";
import { AssessmentFeatureTable } from "./assessment-feature-table";
import { AssessmentStatus } from "./assessment-status";
import { EvidenceProvenanceModal } from "./evidence-provenance-modal";
import { PeerComparisonTable } from "./peer-comparison-table";
import { RationaleCard } from "./rationale-card";
import { SingleFeatureChart } from "./single-feature-chart";

function ClusterProfileCard({
  title,
  profile,
}: {
  title: string;
  profile: AssessmentClusterProfile | null;
}) {
  return (
    <section className="state-box" aria-label={title} style={{ padding: "0.85rem 1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
        <h3 style={{ margin: 0, fontSize: "0.95rem" }}>{title}</h3>
        {profile && (
          <span className="badge teal" style={{ fontWeight: "bold" }}>
            Cụm {profile.id}
          </span>
        )}
      </div>
      {profile ? (
        <dl className="provenance" style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.25rem 0.75rem", margin: 0, fontSize: "0.85rem" }}>
          <dt style={{ color: "var(--muted, #64748b)" }}>Mô hình:</dt>
          <dd style={{ margin: 0 }}>{profile.model_version} · Kỳ {profile.date_or_fy}</dd>
          {profile.profile && (
            <>
              <dt style={{ color: "var(--muted, #64748b)" }}>Mô tả:</dt>
              <dd style={{ margin: 0 }}>{profile.profile}</dd>
            </>
          )}
          {profile.quality_flags.length > 0 && (
            <>
              <dt style={{ color: "var(--muted, #64748b)" }}>Chất lượng:</dt>
              <dd style={{ margin: 0 }}>{profile.quality_flags.join(", ")}</dd>
            </>
          )}
        </dl>
      ) : (
        <p role="status" style={{ margin: 0, color: "var(--muted, #64748b)", fontSize: "0.85rem" }}>Không có thông tin cụm</p>
      )}
    </section>
  );
}

export interface AssessmentPanelProps {
  ticker: string;
  response: AssessmentResponse | null;
  loading: boolean;
  error: string | null;
  errorStatus: number | null;
  stale?: boolean;
  onRetry?: () => void;
  lookbackYears?: 5 | 10;
  onLookbackChange?: (query: AssessmentQuery) => void;
  selectedFeatureId?: AssessmentFeatureId;
  onFeatureChange?: (featureId: AssessmentFeatureId) => void;
}

export function AssessmentPanel({
  ticker,
  response,
  loading,
  error,
  errorStatus,
  stale = false,
  onRetry,
  lookbackYears,
  onLookbackChange,
  selectedFeatureId,
  onFeatureChange,
}: AssessmentPanelProps) {
  const requestedTicker = ticker.trim().toUpperCase();
  const matchingResponse =
    response?.ticker.trim().toUpperCase() === requestedTicker ? response : null;
  const canShowAssessment = matchingResponse != null && error == null;

  return (
    <section aria-label={`Panel Assessment ${requestedTicker}`} className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">ĐÁNH GIÁ ĐẦU TƯ</div>
          <h2>Assessment · {requestedTicker || "Chưa chọn mã"}</h2>
        </div>
      </div>

      <AssessmentStatus
        ticker={ticker}
        response={matchingResponse}
        loading={loading}
        error={error}
        errorStatus={errorStatus}
        stale={stale}
        onRetry={onRetry}
      />

      {canShowAssessment && matchingResponse && (
        <div className="assessment-panel-content">
          <RationaleCard response={matchingResponse} />

          <details
            aria-label="Hồ sơ hai cụm đã phát hành"
            style={{
              marginBlock: "0.75rem",
              fontSize: "0.85rem",
              color: "var(--muted, #64748b)",
            }}
          >
            <summary style={{ cursor: "pointer", userSelect: "none", fontWeight: 500, padding: "0.35rem 0" }}>
              Mô hình phân cụm DELTA (Thị trường A v4: Cụm #{matchingResponse.market_cluster?.id ?? 0} · Tài chính B-PIT: Cụm #{matchingResponse.financial_cluster?.id ?? 0})
            </summary>
            <div
              style={{
                display: "grid",
                gap: "0.75rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 18rem), 1fr))",
                marginTop: "0.5rem",
              }}
            >
              <ClusterProfileCard title="Cụm thị trường A v4" profile={matchingResponse.market_cluster} />
              <ClusterProfileCard title="Cụm tài chính B-PIT" profile={matchingResponse.financial_cluster} />
            </div>
          </details>

          <SingleFeatureChart
            response={matchingResponse}
            lookbackYears={lookbackYears}
            onLookbackChange={onLookbackChange}
            selectedFeatureId={selectedFeatureId}
            onFeatureChange={onFeatureChange}
          />

          <PeerComparisonTable response={matchingResponse} />
          <AssessmentFeatureTable response={matchingResponse} />
          <EvidenceProvenanceModal response={matchingResponse} />
        </div>
      )}
    </section>
  );
}
