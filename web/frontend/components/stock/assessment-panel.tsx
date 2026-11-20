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
    <div
      aria-label={title}
      style={{
        background: "var(--surface-2)",
        border: "1px solid var(--line)",
        borderRadius: "var(--radius-sm)",
        padding: "12px 14px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        <strong style={{ fontSize: "13px", color: "var(--text)" }}>{title}</strong>
        {profile ? (
          <span className="badge teal">Cụm #{profile.id}</span>
        ) : (
          <span className="badge">Chưa có</span>
        )}
      </div>
      {profile ? (
        <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px", margin: 0, fontSize: "13px" }}>
          <dt style={{ color: "var(--muted)" }}>Mô hình</dt>
          <dd style={{ margin: 0, color: "var(--text-2)" }}>{profile.model_version} · Kỳ {profile.date_or_fy}</dd>
          {profile.profile && (
            <>
              <dt style={{ color: "var(--muted)" }}>Đặc trưng</dt>
              <dd style={{ margin: 0, color: "var(--text-2)" }}>{profile.profile}</dd>
            </>
          )}
          {profile.quality_flags.length > 0 && (
            <>
              <dt style={{ color: "var(--muted)" }}>Chất lượng</dt>
              <dd style={{ margin: 0, color: "var(--text-2)" }}>{profile.quality_flags.join(", ")}</dd>
            </>
          )}
        </dl>
      ) : (
        <p role="status" style={{ margin: 0, color: "var(--muted)", fontSize: "13px" }}>
          Chưa có phân cụm cho kỳ đánh giá này.
        </p>
      )}
    </div>
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
    <div aria-label={`Panel Assessment ${requestedTicker}`}>
      <section className="panel">
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
          <details
            aria-label="Hồ sơ hai cụm đã phát hành"
            style={{
              borderTop: "1px solid var(--line)",
              padding: "10px 22px 12px",
              fontSize: "13px",
              color: "var(--muted)",
            }}
          >
            <summary style={{ cursor: "pointer", userSelect: "none", fontWeight: 500, color: "var(--text-2)" }}>
              Chi tiết mô hình phân cụm (Thị trường A v4:{" "}
              {matchingResponse.market_cluster != null ? `Cụm #${matchingResponse.market_cluster.id}` : "Chưa có"} · Tài chính B-PIT:{" "}
              {matchingResponse.financial_cluster != null ? `Cụm #${matchingResponse.financial_cluster.id}` : "Chưa có"})
            </summary>
            <div
              style={{
                display: "grid",
                gap: "12px",
                gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 18rem), 1fr))",
                marginTop: "12px",
              }}
            >
              <ClusterProfileCard title="Cụm thị trường A v4" profile={matchingResponse.market_cluster} />
              <ClusterProfileCard title="Cụm tài chính B-PIT" profile={matchingResponse.financial_cluster} />
            </div>
          </details>
        )}
      </section>

      {canShowAssessment && matchingResponse && (
        <>
          <RationaleCard response={matchingResponse} />

          <SingleFeatureChart
            response={matchingResponse}
            lookbackYears={lookbackYears}
            onLookbackChange={onLookbackChange}
            selectedFeatureId={selectedFeatureId}
            onFeatureChange={onFeatureChange}
          />

          <PeerComparisonTable response={matchingResponse} />
          <AssessmentFeatureTable response={matchingResponse} />

          <section className="panel section-gap" style={{ padding: "14px 22px" }}>
            <EvidenceProvenanceModal response={matchingResponse} />
          </section>
        </>
      )}
    </div>
  );
}
