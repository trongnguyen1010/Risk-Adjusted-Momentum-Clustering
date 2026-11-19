import type {
  AssessmentEvidence,
  AssessmentFeature,
  AssessmentResponse,
} from "@/lib/types";

function safeReference(value: string): { text: string; href: string | null } {
  const trimmed = value.trim();
  if (!trimmed) return { text: "Không có tham chiếu", href: null };

  const localPath =
    /^(?:[a-zA-Z]:[\\/]|\\\\|\/)/.test(trimmed) ||
    trimmed.toLowerCase().startsWith("file:");
  if (localPath) {
    const name = trimmed.split(/[\\/]/).filter(Boolean).at(-1) ?? "tham chiếu nội bộ";
    return { text: `${name} (đã ẩn đường dẫn máy)`, href: null };
  }

  const redacted = trimmed.replace(
    /\b(token|access_token|api[_-]?key|secret|password)\s*[=:]\s*[^&\s]+/gi,
    "$1=[đã ẩn]",
  );

  try {
    const url = new URL(redacted);
    if (url.protocol !== "https:" || url.username || url.password) {
      return { text: redacted, href: null };
    }
    // Query strings and fragments can contain credentials or private state.
    url.search = "";
    url.hash = "";
    return { text: url.toString(), href: url.toString() };
  } catch {
    return { text: redacted, href: null };
  }
}

function ReferenceValue({ value }: { value: string | null | undefined }) {
  if (!value) return <span>Artifact không cung cấp tham chiếu riêng.</span>;
  const reference = safeReference(value);
  return reference.href ? (
    <a
      href={reference.href}
      rel="noreferrer noopener"
      target="_blank"
      style={{ overflowWrap: "anywhere" }}
    >
      {reference.text}
    </a>
  ) : (
    <code style={{ overflowWrap: "anywhere" }}>{reference.text}</code>
  );
}

function DateValue({ value }: { value: string | null | undefined }) {
  return value ? (
    <time dateTime={value}>{value}</time>
  ) : (
    <span>Artifact không cung cấp ngày này.</span>
  );
}

function featurePeriod(feature: AssessmentFeature | null): string | null {
  if (!feature) return null;
  return feature.period;
}

export function EvidenceProvenanceModal({
  response,
  feature = null,
  evidence = null,
  title = "Nguồn và chất lượng dữ liệu",
}: {
  response: AssessmentResponse;
  feature?: AssessmentFeature | null;
  evidence?: AssessmentEvidence | null;
  title?: string;
}) {
  const status = evidence?.status ?? feature?.status ?? null;
  const period = featurePeriod(feature);
  const sourceReference = evidence?.evidence_ref ?? feature?.evidence_ref;
  const sourceHashes = Object.entries(response.references.source_hashes);

  return (
    <details className="evidence-provenance">
      <summary
        className="text-link"
        style={{ cursor: "pointer", overflowWrap: "anywhere" }}
      >
        {title}
      </summary>
      <section
        aria-label={title}
        className="state-box"
        style={{ marginTop: "0.75rem", overflowWrap: "anywhere" }}
      >
        {feature && <h3>{feature.feature_id}</h3>}
        {evidence?.message && <p>{evidence.message}</p>}
        <dl className="provenance">
          <dt>Kỳ tài chính / snapshot</dt>
          <dd>
            {period ? (
              <span>
                {feature?.category === "FINANCIAL" ? "FY " : "Snapshot "}
                {period}
              </span>
            ) : feature?.category === "MARKET" ? (
              <DateValue value={response.required_price_session} />
            ) : (
              <span>Artifact không cung cấp kỳ riêng cho mục này.</span>
            )}
          </dd>
          <dt>Ngày khả dụng</dt>
          <dd><DateValue value={feature?.usable_from_date} /></dd>
          <dt>As of</dt>
          <dd><DateValue value={response.as_of} /></dd>
          <dt>Phiên giá yêu cầu</dt>
          <dd><DateValue value={response.required_price_session} /></dd>
          <dt>Trạng thái</dt>
          <dd>{status ?? "Artifact không cung cấp status riêng."}</dd>
          <dt>Release revision</dt>
          <dd><ReferenceValue value={response.references.release_revision} /></dd>
          <dt>Policy revision</dt>
          <dd><ReferenceValue value={response.references.policy_revision} /></dd>
          <dt>Evidence reference</dt>
          <dd><ReferenceValue value={sourceReference} /></dd>
        </dl>

        <details>
          <summary style={{ cursor: "pointer" }}>Manifest và source hashes</summary>
          <dl className="provenance" style={{ overflowWrap: "anywhere" }}>
            <dt>Manifest SHA-256</dt>
            <dd><code>{response.references.manifest_sha256}</code></dd>
            <dt>Deterministic content SHA-256</dt>
            <dd><code>{response.references.deterministic_content_sha256}</code></dd>
            {sourceHashes.map(([name, hash]) => (
              <div key={name}>
                <dt><ReferenceValue value={name} /></dt>
                <dd><code style={{ overflowWrap: "anywhere" }}>{hash}</code></dd>
              </div>
            ))}
          </dl>
        </details>
      </section>
    </details>
  );
}
