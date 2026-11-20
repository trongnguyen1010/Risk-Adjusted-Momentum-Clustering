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

function DateText({ label, value }: { label: string; value: string | null }) {
  if (!value && label === "Mốc chốt bằng chứng") return null;
  return (
    <div style={{ display: "inline-flex", gap: "0.35rem", alignItems: "center" }}>
      <dt style={{ color: "var(--muted, #64748b)", fontWeight: 500 }}>{label}:</dt>
      <dd style={{ margin: 0 }}>
        {value ? (
          <time dateTime={value}>{value}</time>
        ) : (
          "Chưa có"
        )}
      </dd>
    </div>
  );
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
      ? "Bản mô phỏng theo thời điểm (demo)"
      : "Bản theo thời điểm hiện tại";

  return (
    <section
      aria-busy={loading}
      aria-label={`Assessment cho ${currentTicker}`}
      className="assessment-status state-box"
      style={{
        background: "var(--surface, #ffffff)",
        border: "1px solid var(--border, #e2e8f0)",
        borderRadius: "10px",
        padding: "1.25rem 1.5rem",
        marginBottom: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
      }}
    >
      {showStale && (
        <p aria-live="polite" className="badge amber" role="status" style={{ marginBottom: "0.75rem" }}>
          {loading
            ? "Đang cập nhật; kết quả đang hiển thị có thể đã cũ."
            : "Đang hiển thị dữ liệu cũ; cần kiểm tra lại trước khi sử dụng."}
        </p>
      )}

      <div
        aria-label="Trạng thái và kết luận Assessment"
        className="status-row"
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
          marginBottom: "0.75rem",
          paddingBottom: "0.75rem",
          borderBottom: "1px solid var(--border-subtle, #f1f5f9)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <VerdictBadge status={currentResponse.assessment_status} />
          <span
            aria-label={`Availability: ${availabilityPresentation.label}`}
            className={`badge ${availabilityPresentation.tone}`}
          >
            {availabilityPresentation.label}
          </span>
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--muted, #64748b)" }}>
          Kỳ đánh giá: <time dateTime={currentResponse.as_of}>02/01/2026</time> · Phiên giá áp dụng: <time dateTime={currentResponse.required_price_session}>31/12/2025</time>
        </div>
      </div>

      <p
        style={{
          fontSize: "1.1rem",
          fontWeight: 600,
          color: "var(--foreground, #0f172a)",
          margin: "0 0 0.75rem 0",
          lineHeight: 1.55,
        }}
      >
        {currentResponse.rationale}
      </p>

      <dl
        aria-label="Thời điểm và phạm vi Assessment"
        className="provenance"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem 1.25rem",
          margin: 0,
          padding: "0.45rem 0.75rem",
          background: "var(--surface-muted, rgba(0,0,0,0.02))",
          borderRadius: "6px",
          fontSize: "0.8rem",
          color: "var(--muted, #64748b)",
        }}
      >
        <div style={{ display: "inline-flex", gap: "0.35rem", alignItems: "center" }}>
          <dt style={{ fontWeight: 500 }}>Chế độ:</dt>
          <dd style={{ margin: 0 }}>Mô phỏng tại ngày 02/01/2026</dd>
        </div>
        <DateText label="Phiên giá yêu cầu" value={currentResponse.required_price_session} />
        {currentResponse.market_cluster && (
          <div style={{ display: "inline-flex", gap: "0.35rem", alignItems: "center" }}>
            <dt style={{ fontWeight: 500 }}>Phân cụm DELTA:</dt>
            <dd style={{ margin: 0 }}>Thị trường #{currentResponse.market_cluster.id} · Tài chính #{currentResponse.financial_cluster?.id ?? "N/A"}</dd>
          </div>
        )}
      </dl>
    </section>
  );
}
