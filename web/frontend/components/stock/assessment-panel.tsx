"use client";

import type {
  AssessmentClusterProfile,
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
    <section className="state-box" aria-label={title}>
      <h3>{title}</h3>
      {profile ? (
        <>
          <dl className="provenance">
            <dt>Cluster ID</dt>
            <dd>{profile.id}</dd>
            <dt>Model version</dt>
            <dd>{profile.model_version}</dd>
            <dt>Kỳ / snapshot</dt>
            <dd>{profile.date_or_fy}</dd>
            <dt>Profile</dt>
            <dd>{profile.profile ?? "Artifact không cung cấp profile mô tả."}</dd>
            <dt>Source revision</dt>
            <dd><code>{profile.source_revision}</code></dd>
          </dl>
          {profile.quality_flags.length > 0 ? (
            <div>
              <h4>Cờ chất lượng từ artifact</h4>
              <ul>
                {profile.quality_flags.map((flag, index) => (
                  <li key={`${flag}-${index}`}>{flag}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-small">Artifact không ghi cờ chất lượng cho profile này.</p>
          )}
        </>
      ) : (
        <p role="status">Response không có cluster profile cho phần này.</p>
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
          <div
            aria-label="Hồ sơ hai cụm đã phát hành"
            style={{
              display: "grid",
              gap: "1rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 18rem), 1fr))",
              marginBlock: "1rem",
            }}
          >
            <ClusterProfileCard title="Cụm thị trường A v4" profile={matchingResponse.market_cluster} />
            <ClusterProfileCard title="Cụm tài chính B-PIT" profile={matchingResponse.financial_cluster} />
          </div>

          <SingleFeatureChart
            response={matchingResponse}
            lookbackYears={lookbackYears}
            onLookbackChange={onLookbackChange}
          />

          <AssessmentFeatureTable response={matchingResponse} />
          <PeerComparisonTable response={matchingResponse} />
          <RationaleCard response={matchingResponse} />
          <EvidenceProvenanceModal response={matchingResponse} />
        </div>
      )}
    </section>
  );
}
