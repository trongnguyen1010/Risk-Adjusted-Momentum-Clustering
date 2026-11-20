import type {
  AssessmentAvailabilityStatus,
  AssessmentResponse,
} from "@/lib/types";
import { VerdictBadge } from "./verdict-badge";

type AvailabilityPresentation = { label: string; tone: string };

const AVAILABILITY_PRESENTATION: Record<
  AssessmentAvailabilityStatus,
  AvailabilityPresentation
> = {
  READY: { label: "Dữ liệu sẵn sàng", tone: "teal" },
  HISTORICAL_ONLY: { label: "Chỉ có dữ liệu lịch sử", tone: "purple" },
  STALE: { label: "Dữ liệu đã cũ", tone: "amber" },
  NOT_ELIGIBLE: { label: "Chưa đủ điều kiện dữ liệu", tone: "amber" },
  NOT_FOUND: { label: "Không có dữ liệu cho mã này", tone: "subtle" },
  DATA_MISSING: { label: "Thiếu dữ liệu", tone: "amber" },
};

const HTTP_ERROR_PRESENTATION: Record<number, { title: string; detail: string }> = {
  404: {
    title: "Không tìm thấy Assessment cho mã này",
    detail: "Ticker không có trong release đã phát hành.",
  },
  409: {
    title: "Release Assessment không khớp",
    detail: "Revision được yêu cầu khác với revision của dữ liệu đang phục vụ.",
  },
  503: {
    title: "Assessment chưa sẵn sàng",
    detail: "Artifact chưa được phát hành hoặc chưa qua kiểm tra.",
  },
};

export interface AssessmentStatusProps {
  ticker: string;
  response: AssessmentResponse | null;
  loading: boolean;
  error: string | null;
  errorStatus: number | null;
  stale?: boolean;
  onRetry?: () => void;
}

function formatIsoDateVi(isoDate: string): string {
  const parts = isoDate.split("-");
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : isoDate;
}

export function AssessmentStatus({
  ticker,
  response,
  loading,
  error,
  errorStatus,
  stale = false,
  onRetry,
}: AssessmentStatusProps) {
  const currentTicker = ticker.trim().toUpperCase();
  const currentResponse =
    response?.ticker.toUpperCase() === currentTicker ? response : null;

  if (error) {
    const knownError = errorStatus ? HTTP_ERROR_PRESENTATION[errorStatus] : null;
    return (
      <section aria-label="Trạng thái Assessment" className="state-box error" role="alert">
        <h3>{knownError?.title ?? "Không tải được Assessment"}</h3>
        <p>{knownError?.detail ?? error}</p>
        {knownError && error !== knownError.detail && (
          <p className="text-small">Chi tiết: {error}</p>
        )}
        {onRetry && (
          <button className="button small" onClick={onRetry} type="button">
            Thử lại
          </button>
        )}
      </section>
    );
  }

  if (!currentResponse) {
    if (loading) {
      return (
        <section
          aria-busy="true"
          aria-label={`Đang tải Assessment cho ${currentTicker}`}
          aria-live="polite"
          className="state-box"
          role="status"
        >
          <h3>Đang tải Assessment</h3>
          <p>Đang lấy kết quả cho {currentTicker}.</p>
        </section>
      );
    }

    return (
      <section aria-label="Trạng thái Assessment" className="state-box" role="status">
        <h3>Chưa có kết quả Assessment</h3>
        <p>Chưa có dữ liệu cho {currentTicker}.</p>
      </section>
    );
  }

  const availability = currentResponse.availability_status;
  const availabilityPresentation = AVAILABILITY_PRESENTATION[availability];
  const showStale = stale || availability === "STALE" || loading;
  const contextLabel =
    currentResponse.assessment_context === "SIMULATED_AS_OF"
      ? `Mô phỏng tại ngày ${formatIsoDateVi(currentResponse.as_of)}`
      : "Đánh giá theo thời điểm hiện hành";

  return (
    <section
      aria-busy={loading}
      aria-label={`Assessment cho ${currentTicker}`}
      style={{
        padding: "0 22px 18px",
      }}
    >
      {showStale && (
        <p aria-live="polite" className="badge amber" role="status" style={{ marginBottom: "12px", display: "inline-block" }}>
          {loading
            ? "Đang cập nhật; kết quả đang hiển thị có thể đã cũ."
            : "Đang hiển thị dữ liệu cũ; cần kiểm tra lại trước khi sử dụng."}
        </p>
      )}

      <div
        aria-label="Trạng thái và kết luận Assessment"
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          paddingBottom: "12px",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px" }}>
          <VerdictBadge status={currentResponse.assessment_status} />
          <span
            aria-label={`Availability: ${availabilityPresentation.label}`}
            className={`badge ${availabilityPresentation.tone}`}
          >
            {availabilityPresentation.label}
          </span>
        </div>
        <div style={{ fontSize: "13px", color: "var(--muted)" }}>
          Kỳ đánh giá: <time dateTime={currentResponse.as_of}>{formatIsoDateVi(currentResponse.as_of)}</time> · Phiên giá áp dụng:{" "}
          <time dateTime={currentResponse.required_price_session}>{formatIsoDateVi(currentResponse.required_price_session)}</time>
        </div>
      </div>

      <p
        style={{
          fontSize: "17px",
          fontWeight: 600,
          color: "var(--text)",
          margin: "14px 0",
          lineHeight: 1.55,
          textAlign: "left",
        }}
      >
        {currentResponse.rationale}
      </p>

      <dl
        aria-label="Thời điểm và phạm vi Assessment"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "6px 20px",
          margin: 0,
          padding: "8px 12px",
          background: "var(--surface-2)",
          border: "1px solid var(--line)",
          borderRadius: "8px",
          fontSize: "13px",
          color: "var(--muted)",
        }}
      >
        <div style={{ display: "inline-flex", gap: "6px", alignItems: "center" }}>
          <dt style={{ fontWeight: 500 }}>Phạm vi:</dt>
          <dd style={{ margin: 0, color: "var(--text-2)" }}>{contextLabel}</dd>
        </div>
        {currentResponse.evidence_cutoff_at && (
          <div style={{ display: "inline-flex", gap: "6px", alignItems: "center" }}>
            <dt style={{ fontWeight: 500 }}>Mốc chốt bằng chứng:</dt>
            <dd style={{ margin: 0, color: "var(--text-2)" }}>
              <time dateTime={currentResponse.evidence_cutoff_at}>{currentResponse.evidence_cutoff_at}</time>
            </dd>
          </div>
        )}
        <div style={{ display: "inline-flex", gap: "6px", alignItems: "center" }}>
          <dt style={{ fontWeight: 500 }}>Phân cụm DELTA:</dt>
          <dd style={{ margin: 0, color: "var(--text-2)" }}>
            Thị trường {currentResponse.market_cluster != null ? `#${currentResponse.market_cluster.id}` : "chưa có"} · Tài chính{" "}
            {currentResponse.financial_cluster != null ? `#${currentResponse.financial_cluster.id}` : "chưa có"}
          </dd>
        </div>
      </dl>
    </section>
  );
}
