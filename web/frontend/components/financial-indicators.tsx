"use client";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { number } from "@/lib/format";
import { Panel, Badge, ErrorState, Skeleton } from "./ui";

type Metric = {
  family: string; value: string | null; availability: string; status: string;
  year: string | null; period_kind: string | null; input_period: string | null;
  price_date: string | null; reference_date: string | null; balance_date: string | null;
  variant: string | null; unit: string; missing_inputs: string | null;
  components: Record<string, unknown> | null; evidence_ref: string;
};
type Group = { id: string; source_id: string; source_label: string; cohort: string; year: string; metrics: Metric[]; source_path: string; source_sha256: string };
type Payload = { groups: Group[]; default_group_id: string | null; coverage: { unavailable_sources: string[] }; missing_reason: string | null };
const families = ["EPS", "PE", "PB", "F_SCORE", "M_SCORE", "Z_SCORE"];
const names: Record<string, string> = { EPS: "Lợi nhuận mỗi cổ phiếu", PE: "Giá / Lợi nhuận", PB: "Giá / Giá trị sổ sách", F_SCORE: "Sức khỏe tài chính", M_SCORE: "Dấu hiệu biến động lợi nhuận", Z_SCORE: "Khả năng chịu áp lực tài chính" };
const labels: Record<string, string> = { EPS: "EPS cơ bản", PE: "P/E", PB: "P/B", F_SCORE: "F-Score", M_SCORE: "M-Score", Z_SCORE: "Z-Score" };
const descriptions: Record<string, string> = {
  EPS: "Mỗi cổ phiếu tạo ra bao nhiêu đồng lợi nhuận trong kỳ báo cáo. EPS quý và EPS cả năm phản ánh các khoảng thời gian khác nhau.",
  PE: "Giá cổ phiếu gấp bao nhiêu lần lợi nhuận trên mỗi cổ phiếu. Cần xem cùng ngày giá và kỳ lợi nhuận; con số thấp không tự có nghĩa là rẻ.",
  PB: "Giá thị trường so với giá trị sổ sách trên mỗi cổ phiếu. Hữu ích khi so sánh các doanh nghiệp có đặc điểm kinh doanh tương đồng.",
  F_SCORE: "Tổng hợp 9 tiêu chí về lợi nhuận, dòng tiền, đòn bẩy và hiệu quả hoạt động. Chỉ có tổng điểm khi đủ cả 9 tiêu chí.",
  M_SCORE: "Kết hợp các biến động trong báo cáo để hỗ trợ sàng lọc và tìm điểm cần đọc kỹ. Một con số không đủ để kết luận doanh nghiệp gian lận.",
  Z_SCORE: "Kết hợp các tỷ số về vốn lưu động, lợi nhuận và cấu trúc vốn. Cách đọc phụ thuộc phiên bản mô hình và loại doanh nghiệp.",
};
function date(value: string | null) {
  return value && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value.split("-").reverse().join("/") : value;
}
function period(group: Group) {
  const kind = group.metrics.find(m => m.value !== null)?.period_kind || group.metrics.find(m => m.period_kind)?.period_kind || "ANNUAL";
  if (kind === "YTD6" || kind === "H1_REVIEWED") return "6 tháng đầu năm";
  if (kind === "YTD9") return "9 tháng đầu năm";
  if (kind.startsWith("YTD")) return `${kind.slice(3)} tháng lũy kế`;
  if (kind === "QUARTER_REPORTED" || kind === "QUARTER_STANDALONE") {
    const input = group.metrics.find(m => m.input_period)?.input_period || group.cohort;
    const q = /Q([1-4])/.exec(input) || /:(\d):QUY$/.exec(group.cohort);
    return q ? `Quý ${q[1]}` : "Theo quý";
  }
  return "Cả năm";
}
function revision(group: Group) {
  const d = group.metrics.find(m => m.reference_date)?.reference_date;
  const present = group.metrics.filter(m => m.value !== null).map(m => labels[m.family]).join(", ");
  return `${group.source_id === "provider_eps" ? "EPS nguồn CafeF" : "Bộ số liệu báo cáo"}${d ? ` · mốc tham chiếu ${date(d)}` : ""}${present ? ` · ${present}` : ""}`;
}
function missing(family: string, metric?: Metric) {
  if (metric?.status === "UNCONFIRMED_PROVIDER_ZERO") return "Nguồn trả EPS bằng 0; cần đối chiếu báo cáo trước khi sử dụng.";
  if (metric?.availability === "SOURCE_UNAVAILABLE") return "Chưa tải được dữ liệu nguồn. Hãy thử lại sau.";
  if (metric?.status.includes("CONFLICT")) return "Các bản báo cáo có số khác nhau; cần đối chiếu trước khi sử dụng.";
  return ({ EPS: "Chưa có EPS hoặc số cổ phiếu bình quân phù hợp với kỳ này.", PE: "Cần EPS và giá cổ phiếu cùng cơ sở tính toán.", PB: "Cần vốn chủ sở hữu, số cổ phiếu và giá cùng cơ sở tính toán.", F_SCORE: "Chưa đủ cả 9 tiêu chí để có tổng điểm.", M_SCORE: "Chưa đủ dữ liệu so sánh hai kỳ và khấu hao phù hợp.", Z_SCORE: "Chưa đủ đầu vào đã đối chiếu để áp dụng mô hình này." })[family];
}
export function FinancialIndicators({ ticker, view = "overview" }: { ticker: string; view?: "overview" | "history" | "sources" }) {
  const selection = useSelection();
  const state = useApi<Payload>(url(`indicators/${encodeURIComponent(ticker)}`));
  const groups = state.data?.groups || [];
  const years = [...new Set(groups.map(g => g.year))].sort().reverse();
  const direct = groups.find(g => g.id === selection.params.get("source"));
  const year = direct?.year || selection.params.get("report_year") || years[0] || "";
  const inYear = groups.filter(g => g.year === year);
  const periods = [...new Set(inYear.map(period))];
  const selectedPeriod = direct ? period(direct) : selection.params.get("report_period") || (periods.includes("Cả năm") ? "Cả năm" : periods[0]);
  const eligible = inYear.filter(g => period(g) === selectedPeriod);
  const group = selection.params.get("source") ? direct : eligible.find(g => g.id === state.data?.default_group_id) || eligible.find(g => g.metrics.some(m => m.value !== null)) || eligible[0];
  const history = periods.map(p => {
    const candidates = inYear.filter(g => period(g) === p && g.metrics.some(m => m.value !== null));
    return candidates.find(g => g.id === group?.id) || candidates.find(g => g.id === state.data?.default_group_id) || candidates[0];
  }).filter((g): g is Group => !!g);
  const count = group?.metrics.filter(m => m.value !== null).length || 0;
  return <Panel title="Chỉ số tài chính" eyebrow="HIỂU DOANH NGHIỆP QUA CÁC CON SỐ" action={<Badge>{year ? `${selectedPeriod} ${year}` : "Theo báo cáo"}</Badge>}>
    {state.error ? <ErrorState message={state.error} retry={state.retry} /> : !state.data ? <Skeleton height={340} /> : <>
      <div className="report-controls">
        <div><p className="report-lead">Lợi nhuận, định giá và sức khỏe tài chính</p><p className="muted">{count ? `${count}/6 chỉ số có dữ liệu trong kỳ đang chọn.` : "Chưa đủ dữ liệu cho bộ chỉ số này."} Chọn từng chỉ số để xem cách đọc.</p></div>
        <div className="report-selectors">
          <label>Năm báo cáo<select aria-label="Năm báo cáo của bộ chỉ số" value={year} disabled={!years.length} onChange={e => selection.set({ report_year: e.target.value, report_period: null, source: null })}>{!years.length && <option value="">Chưa có báo cáo</option>}{years.map(y => <option key={y} value={y}>{y}</option>)}</select></label>
          <label>Kỳ báo cáo<select aria-label="Kỳ báo cáo của bộ chỉ số" value={selectedPeriod || ""} disabled={!periods.length} onChange={e => selection.set({ report_period: e.target.value, source: null })}>{!periods.length && <option value="">—</option>}{periods.map(p => <option key={p}>{p}</option>)}</select></label>
        </div>
      </div>
      {!!state.data.coverage.unavailable_sources.length && <p className="panel-note warning-line">Một phần dữ liệu nguồn chưa tải được. Kết quả có thể chưa đầy đủ.</p>}
      <div className="indicator-cards product-indicators">
        {families.map(f => {
          const m = group?.metrics.find(x => x.family === f);
          return <article className={`indicator-card ${m?.value == null ? "indicator-missing" : ""}`} key={f}>
            <div className="indicator-label"><span>{labels[f]}</span><span className="indicator-unit">{f === "EPS" ? "đồng/cp" : ["PE", "PB"].includes(f) ? "lần" : f === "F_SCORE" ? "điểm / 9" : "điểm"}</span></div>
            <strong>{m?.value == null ? "—" : number(Number(m.value), f === "F_SCORE" ? 0 : 2)}{m?.value != null && f === "F_SCORE" && <small> / 9</small>}</strong>
            <p className="indicator-purpose">{names[f]}</p>
            {m?.price_date && <small>Giá ngày {date(m.price_date)}</small>}
            {m?.value == null ? <p className="indicator-reason">{missing(f, m)}</p> : <small className="indicator-origin">{m.status === "PROVIDER_REPORTED" ? "EPS do CafeF cung cấp · chưa đối chiếu BCTC gốc" : "Tính từ dữ liệu báo cáo đã đối chiếu"}</small>}
            <details className="indicator-help"><summary>Chỉ số này dùng để làm gì?</summary><p>{descriptions[f]}</p></details>
          </article>;
        })}
      </div>
      <p className="panel-note">Số liệu thuộc kỳ báo cáo đang chọn. P/E và P/B dùng ngày giá ghi trên thẻ; đây không phải giá trực tiếp.</p>
      {view !== "overview" && <div className="data-table-wrap"><table className="data-table"><caption>Các kỳ báo cáo năm {year} — mỗi hàng giữ nguyên một bộ số liệu. Chọn năm khác ở phía trên.</caption><thead><tr><th>Kỳ báo cáo</th>{families.map(f => <th key={f}>{labels[f]}</th>)}</tr></thead><tbody>{history.map(g => <tr key={g.id}><th><button onClick={() => selection.set({ source: g.id, report_year: g.year, report_period: period(g) })}>{period(g)} {g.year}</button><small className="block">{revision(g)}</small></th>{families.map(f => { const m = g.metrics.find(x => x.family === f); return <td className="mono" key={f}>{m?.value == null ? "—" : number(Number(m.value), f === "F_SCORE" ? 0 : 2)}</td>; })}</tr>)}</tbody></table></div>}
      <details className="indicator-details" open={view === "sources"}>
        <summary>Nguồn dữ liệu và phương pháp tính</summary>
        <div className="panel-body">
          <p>Các số được giữ theo từng bản báo cáo. Khi doanh nghiệp điều chỉnh báo cáo, các bản khác nhau được lưu riêng.</p>
          {eligible.length > 1 && <label className="select-label">Bản số liệu<select aria-label="Bản số liệu báo cáo" value={group?.id || ""} onChange={e => selection.set({ source: e.target.value })}>{eligible.map(g => <option value={g.id} key={g.id}>{revision(g)}</option>)}</select></label>}
          {group?.metrics.map(m => <details className="metric-explanation" key={m.family}><summary>{labels[m.family]} · cách tính và dữ liệu đầu vào</summary><div className="panel-body"><p>{descriptions[m.family]}</p>{m.missing_inputs && m.missing_inputs !== "[]" && <p>Dữ liệu còn thiếu được ghi trong hồ sơ nguồn bên dưới.</p>}<details><summary>Hồ sơ kỹ thuật</summary><pre className="code-block">{JSON.stringify({ variant: m.variant, status: m.status, period: m.input_period, publication_reference: m.reference_date, price_date: m.price_date, balance_date: m.balance_date, missing_inputs: m.missing_inputs, components: m.components, evidence: m.evidence_ref }, null, 2)}</pre></details></div></details>)}
          {group && <details><summary>Định danh và checksum để đối chiếu</summary><p className="panel-note mono">{group.cohort}<br />{group.source_path}<br />SHA-256 {group.source_sha256}</p></details>}
        </div>
      </details>
    </>}
  </Panel>;
}
