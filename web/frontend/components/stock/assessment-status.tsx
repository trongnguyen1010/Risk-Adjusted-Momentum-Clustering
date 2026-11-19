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
  return (
    <>
      <dt>{label}</dt>
      <dd>
        {value ? (
          <time dateTime={value}>{value}</time>
        ) : (
          "Chưa có"
        )}
      </dd>
    </>
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
      className="assessment-status"
    >
      {showStale && (
        <p aria-live="polite" className="badge amber" role="status">
          {loading
            ? "Đang cập nhật; kết quả đang hiển thị có thể đã cũ."
            : "Đang hiển thị dữ liệu cũ; cần kiểm tra lại trước khi sử dụng."}
        </p>
      )}

      <div aria-label="Trạng thái và kết luận Assessment" className="status-row">
        <span
          aria-label={`Availability: ${availabilityPresentation.label}`}
          className={`badge ${availabilityPresentation.tone}`}
        >
          {availabilityPresentation.label}
        </span>
        <VerdictBadge status={currentResponse.assessment_status} />
      </div>

      <p>{currentResponse.rationale}</p>

      <dl aria-label="Thời điểm và phạm vi Assessment" className="provenance">
        <dt>Ngữ cảnh</dt>
        <dd>{contextLabel}</dd>
        <DateText label="As of" value={currentResponse.as_of} />
        <DateText
          label="Phiên giá yêu cầu"
          value={currentResponse.required_price_session}
        />
        <DateText
          label="Mốc chốt bằng chứng"
          value={currentResponse.evidence_cutoff_at}
        />
      </dl>
    </section>
  );
}
