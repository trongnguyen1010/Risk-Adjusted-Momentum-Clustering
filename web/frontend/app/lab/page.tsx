"use client";
import Link from "next/link";
import { ArrowRight, Database, Layers, Sigma, Sparkles } from "lucide-react";
import { useSelection } from "@/lib/selection";
import { PageHeading, Skeleton, ErrorState } from "@/components/ui";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { FAMILY, number, compact, dateLabel } from "@/lib/format";
import { FEATURE_HELP, groupFeatures } from "@/lib/feature-help";
import type { Dataset, Kind } from "@/lib/types";

const tabs = [
  ["methods", "Mô hình"],
  ["quality", "Độ tin cậy"],
  ["provenance", "Dữ liệu & nguồn"],
] as const;
const KINDS: Kind[] = ["market", "financial", "combined"];
const PURPOSE: Record<Kind, string> = {
  market: "Nhóm cổ phiếu có hành vi giá giống nhau trong cùng tháng.",
  financial: "Nhóm doanh nghiệp có báo cáo tài chính năm giống nhau.",
  combined: "Nhóm cổ phiếu giống nhau ở cả giá cuối năm lẫn tài chính cùng năm.",
};
const STEPS = [
  { icon: Database, title: "Thu thập", text: "Giá đóng cửa hằng ngày và báo cáo tài chính năm 2016–2025." },
  { icon: Sigma, title: "Chuẩn hóa", text: "Log thanh khoản, cắt bỏ 1% giá trị cực đoan mỗi đầu, đưa về cùng thang trong từng kỳ." },
  { icon: Layers, title: "Phân nhóm", text: "K-Means (C thêm PCA) học trên mã có giao dịch; mã kém thanh khoản xếp vào nhóm gần nhất." },
  { icon: Sparkles, title: "Giải thích", text: "Bản đồ 2 trục, tên và mô tả từng nhóm sinh từ chỉ số khác biệt nhất." },
];

const pct = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? `${Math.round(v * 100)}%` : "—");
const fixed = (v: unknown, d = 2) =>
  typeof v === "number" && Number.isFinite(v) ? v.toLocaleString("vi-VN", { maximumFractionDigits: d }) : "—";

function grade(value: unknown, good: number, ok: number, higher = true) {
  if (typeof value !== "number" || !Number.isFinite(value)) return { text: "—", tone: "" };
  const g = higher ? value >= good : value <= good;
  const o = higher ? value >= ok : value <= ok;
  return g ? { text: "Tốt", tone: "good" } : o ? { text: "Trung bình", tone: "mid" } : { text: "Yếu", tone: "weak" };
}

function Meter({ value }: { value: number | null }) {
  return (
    <span className="meter" aria-hidden>
      <i style={{ width: `${Math.max(0, Math.min(1, value ?? 0)) * 100}%` }} />
    </span>
  );
}

function ModelCard({ kind, d }: { kind: Kind; d: Dataset }) {
  const m = d.latest.metrics as Record<string, unknown>;
  return (
    <article className="lab-card">
      <header>
        <span className="model-letter">{FAMILY[kind].letter}</span>
        <div>
          <h2>{FAMILY[kind].label}</h2>
          <p>{PURPOSE[kind]}</p>
        </div>
      </header>
      <dl className="lab-stats">
        <div>
          <dt>Nhóm</dt>
          <dd>{d.k}</dd>
        </div>
        <div>
          <dt>Chỉ số</dt>
          <dd>{d.features.length}</dd>
        </div>
        <div>
          <dt>Kỳ</dt>
          <dd>{d.dates.length}</dd>
        </div>
        <div>
          <dt>Số mã</dt>
          <dd>{number(d.latest.n)}</dd>
        </div>
      </dl>
      <p className="lab-line">
        {/PCA/.test(d.scaling) ? "PCA + K-Means" : "K-Means"} · {kind === "market" ? "mỗi tháng" : "mỗi năm"}
        {typeof m.illiquid_n === "number" && m.illiquid_n > 0 ? ` · ${number(m.illiquid_n)} mã kém thanh khoản được gán` : ""}
      </p>
      {d.stability_note && <p className="lab-warn">{d.stability_note}</p>}
      <footer>
        <Link className="text-link" href={`/atlas?kind=${kind}`}>
          Xem trên bản đồ <ArrowRight size={14} />
        </Link>
        <small>Phiên bản {d.version}</small>
      </footer>
    </article>
  );
}

function QualityCard({ kind, d }: { kind: Kind; d: Dataset }) {
  const m = d.latest.metrics as Record<string, unknown>;
  const clear = typeof m.boundary_share === "number" ? 1 - m.boundary_share : null;
  const n = typeof m.fitted_n === "number" ? m.fitted_n : d.latest.n;
  const smallest = typeof m.min_cluster_size === "number" ? m.min_cluster_size / d.latest.n : null;
  const rows = [
    { label: "Mã thuộc rõ một nhóm", help: "Tỷ lệ mã gần nhóm của mình rõ rệt hơn nhóm thứ hai.", value: pct(clear), meter: clear, g: grade(clear, 0.85, 0.7) },
    { label: "Silhouette", help: "−1 đến 1; cao là nhóm tách rõ. Dữ liệu cổ phiếu thường 0,1–0,3.", value: fixed(m.silhouette), meter: typeof m.silhouette === "number" ? Math.max(0, m.silhouette) * 2 : null, g: grade(m.silhouette, 0.25, 0.1) },
    { label: "Davies–Bouldin", help: "Càng thấp càng tốt; dưới 1 là tách tốt.", value: fixed(m.davies_bouldin), meter: typeof m.davies_bouldin === "number" ? Math.max(0, 1 - m.davies_bouldin / 3) : null, g: grade(m.davies_bouldin, 1, 2, false) },
    { label: "Nhóm nhỏ nhất", help: "Phần mã của nhóm nhỏ nhất; dưới 5% thường chỉ là vài mã bất thường.", value: pct(smallest), meter: smallest !== null ? smallest * 3 : null, g: grade(smallest, 0.1, 0.05) },
  ];
  return (
    <article className="lab-card">
      <header>
        <span className="model-letter">{FAMILY[kind].letter}</span>
        <div>
          <h2>{FAMILY[kind].label}</h2>
          <p>
            {dateLabel(d.latest.date)} · {number(n)} mã dùng để đánh giá
          </p>
        </div>
      </header>
      <ul className="quality-list">
        {rows.map((r) => (
          <li key={r.label}>
            <div>
              <strong>{r.label}</strong>
              <small>{r.help}</small>
            </div>
            <span className="quality-value">
              <b>{r.value}</b>
              <em className={`grade ${r.g.tone}`}>{r.g.text}</em>
            </span>
            <Meter value={r.meter} />
          </li>
        ))}
      </ul>
      {d.stability_note && <p className="lab-warn">{d.stability_note}</p>}
    </article>
  );
}

export default function Lab() {
  const s = useSelection();
  const tab = tabs.some(([id]) => id === s.params.get("tab")) ? s.params.get("tab")! : "methods";
  const query = s.params.get("source_q") || "";
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;
  if (!s.data) return <Skeleton height={600} />;
  const { metadata: m, datasets: d, provenance } = s.data;
  const marketFeatures = groupFeatures(d.market.features);
  const financialFeatures = groupFeatures(d.financial.features);
  const sources = provenance.filter((p) => p.path.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <PageHeading
        eyebrow="Phương pháp · độ tin cậy · nguồn"
        title="Phòng nghiên cứu"
        description="Các mô hình được xây dựng thế nào, tin được đến đâu, và dữ liệu lấy từ đâu."
      />
      <WorkspaceTabs tabs={tabs} scope="lab" value={tab} onChange={(tab) => s.set({ tab })} />
      <div id="lab-panel" role="tabpanel" aria-labelledby={`lab-${tab}`} className="lab-panel">
        {tab === "methods" && (
          <>
            <ol className="pipeline">
              {STEPS.map(({ icon: Icon, title, text }, i) => (
                <li key={title}>
                  <span className="pipeline-icon">
                    <Icon size={18} />
                  </span>
                  <small>Bước {i + 1}</small>
                  <strong>{title}</strong>
                  <p>{text}</p>
                </li>
              ))}
            </ol>
            <div className="lab-grid">
              {KINDS.map((kind) => (
                <ModelCard key={kind} kind={kind} d={d[kind]} />
              ))}
            </div>
            <section className="lab-section">
              <h2>Từ điển chỉ số</h2>
              <div className="dictionary">
                {[
                  ["Mô hình thị trường (A)", marketFeatures],
                  ["Mô hình tài chính (B)", financialFeatures],
                ].map(([title, groups]) => (
                  <div className="lab-card" key={title as string}>
                    <h3>{title as string}</h3>
                    {(groups as typeof marketFeatures).map((g) => (
                      <div className="dict-group" key={g.name}>
                        <span>{g.name}</span>
                        <dl>
                          {g.items.map((f) => (
                            <div key={f.key}>
                              <dt>
                                {FEATURE_HELP[f.key]?.group === "Động lượng giá" ? `Động lượng ${f.label}` : f.label}
                                {f.isNew && <em className="new-tag">Mới</em>}
                              </dt>
                              <dd>{f.help}</dd>
                            </div>
                          ))}
                        </dl>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              <p className="lab-note">C dùng 8 chỉ số giá (không gồm biến động giảm) cùng 9 chỉ số tài chính của B.</p>
            </section>
          </>
        )}
        {tab === "quality" && (
          <>
            <div className="lab-grid">
              {KINDS.map((kind) => (
                <QualityCard key={kind} kind={kind} d={d[kind]} />
              ))}
            </div>
            <section className="lab-section">
              <h2>Giới hạn cần biết</h2>
              <ul className="limit-list">
                <li>Nhóm chỉ mô tả dữ liệu lịch sử, không phải khuyến nghị mua bán.</li>
                <li>Báo cáo tài chính năm có thể công bố sau ngày giá được dùng; B và C là tham chiếu sau kỳ.</li>
                <li>Nhóm ở mỗi kỳ được tính riêng; chưa có phân cụm động theo thời gian.</li>
                <li>Chưa kiểm chứng bằng backtest danh mục.</li>
                <li>Ngân hàng, chứng khoán, bảo hiểm không nằm trong nhóm tài chính (B).</li>
              </ul>
            </section>
          </>
        )}
        {tab === "provenance" && (
          <>
            <dl className="lab-stats wide">
              <div>
                <dt>Bộ dữ liệu</dt>
                <dd>{String((m as unknown as Record<string, unknown>).bundle || m.version)}</dd>
              </div>
              <div>
                <dt>Tạo lúc</dt>
                <dd>{String(m.generated_at).slice(0, 10)}</dd>
              </div>
              <div>
                <dt>Dòng giá</dt>
                <dd>{compact(m.price_rows)}</dd>
              </div>
              <div>
                <dt>Nguồn đã khóa</dt>
                <dd>{number(provenance.length)}</dd>
              </div>
            </dl>
            <section className="lab-section">
              <div className="lab-section-head">
                <h2>Nguồn dữ liệu</h2>
                <input
                  aria-label="Lọc nguồn dữ liệu"
                  placeholder="Tìm đường dẫn nguồn…"
                  value={query}
                  onChange={(e) => s.set({ source_q: e.target.value || null })}
                />
              </div>
              <p className="lab-note">Mỗi tệp được khóa bằng mã băm; máy chủ kiểm lại khi khởi động và từ chối nếu khác.</p>
              <ul className="source-list">
                {sources.map((p) => (
                  <li key={p.path}>
                    <span className="source-path">{p.path}</span>
                    <code title={p.sha256}>{p.sha256.slice(0, 12)}…</code>
                    <small>{compact(p.bytes)} B</small>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
      </div>
    </>
  );
}
