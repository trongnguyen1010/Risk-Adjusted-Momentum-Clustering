"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Search } from "lucide-react";
import { useApi, url } from "@/lib/api";
import { useSelection } from "@/lib/selection";
import { Skeleton, ErrorState } from "@/components/ui";
import { Scatter } from "@/components/scatter";
import { FAMILY, number, metric, dateLabel, clusterColor } from "@/lib/format";
import { signedPercent } from "@/lib/indicator-format";
import { FEATURE_HELP } from "@/lib/feature-help";
import type { Dataset, Kind, Observation, SnapshotData, StockOverview } from "@/lib/types";

const KINDS: Kind[] = ["market", "financial", "combined"];
/** Features shown in the inspector bars; the first four are also screener columns. */
const KEY_FEATURES: Record<Kind, string[]> = {
  market: ["mom_63", "mom_252", "vol_63", "mdd_126", "beta_126", "liquidity_21"],
  financial: ["roe", "net_margin", "revenue_growth", "debt_to_equity", "current_ratio", "cfo_to_ni"],
  combined: ["mom_63", "roe", "vol_63", "net_margin", "debt_to_equity", "liquidity_21"],
};
const PAGE = 25;

const featureLabel = (key: string) => {
  const help = FEATURE_HELP[key];
  if (!help) return key;
  return help.group === "Động lượng giá" ? `Động lượng ${help.label}` : help.label;
};
const pct = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? `${Math.round(v * 100)}%` : "—");
const tagTone = (v: number | null | undefined) => (v == null ? "" : v > 0 ? "up" : v < 0 ? "down" : "");

function Kpi({ index, kind, d }: { index: string; kind: Kind; d: Dataset }) {
  const m = d.latest.metrics as Record<string, unknown>;
  const clear = typeof m.boundary_share === "number" ? 1 - m.boundary_share : null;
  return (
    <Link className="bp-cell link" href={`/atlas?kind=${kind}&date=${d.latest.date}`}>
      <header>
        <span>
          [{index} // {FAMILY[kind].letter} · {FAMILY[kind].label}]
        </span>
        <ArrowUpRight size={14} />
      </header>
      <div className="kpi-body">
        <div className="kpi-value">
          {d.k}
          <small>nhóm · {number(d.latest.n)} mã</small>
        </div>
        <p>{pct(clear)} số mã thuộc rõ một nhóm</p>
      </div>
      <footer>
        {kind === "market" ? "Kỳ tháng" : "Kỳ năm"} · {dateLabel(d.latest.date)}
        {d.stability_note ? " · cần thận trọng" : ""}
      </footer>
    </Link>
  );
}

/** Percentile of one ticker's value within the snapshot (0–1); null when missing. */
function percentile(points: Observation[], key: string, value: number | null | undefined) {
  if (value == null) return null;
  const values = points.map((p) => p.features[key]).filter((v): v is number => v != null);
  if (!values.length) return null;
  return values.filter((v) => v < value).length / values.length;
}

function Inspector({ kind, data, ticker }: { kind: Kind; data: SnapshotData; ticker: string }) {
  const point = data.points.find((p) => p.ticker === ticker);
  const overview = useApi<StockOverview>(ticker ? url(`stocks/${encodeURIComponent(ticker)}/overview`) : null);
  if (!point)
    return (
      <div className="insp-section">
        <p>Bấm một chấm trên bản đồ hoặc một dòng trong bảng để xem chi tiết.</p>
      </div>
    );
  const labels = Object.keys(data.snapshot.sizes).map(Number);
  const profile = data.profiles.find((p) => p.cluster === point.cluster);
  const price = overview.data?.price;
  return (
    <>
      <div className="insp-head">
        <div className="insp-ticker">
          <strong>{ticker}</strong>
          <span>{point.exchange || overview.data?.exchange || ""}</span>
        </div>
        <p className="insp-name">{point.name || overview.data?.name || "—"}</p>
        <div className="insp-price">
          {price ? (
            <>
              <b>{number(price.close)}</b>
              <span className={`tag ${tagTone(price.change_1d)}`}>1N {signedPercent(price.change_1d)}</span>
              <span className={`tag ${tagTone(price.change_ytd)}`}>YTD {signedPercent(price.change_ytd)}</span>
            </>
          ) : (
            <span className="bp-tag">{overview.loading ? "Đang tải giá…" : "Chưa có giá"}</span>
          )}
          {point.liquidity === "ILLIQUID" && <span className="tag warn">Kém thanh khoản</span>}
        </div>
      </div>
      <section className="insp-section">
        <h3>Nhóm · {dateLabel(data.snapshot.date)}</h3>
        <div className="insp-group">
          <i style={{ background: clusterColor(point.cluster, labels) }} />
          {FAMILY[kind].letter}
          {point.cluster}
          {profile?.name ? ` · ${profile.name}` : ""}
        </div>
        {profile?.description && <p>{profile.description}</p>}
      </section>
      <section className="insp-section">
        <h3>Vị trí so với toàn thị trường</h3>
        <dl className="bars">
          {KEY_FEATURES[kind].map((key) => {
            const value = point.features[key];
            const rank = percentile(data.points, key, value);
            return (
              <div key={key}>
                <dt>{featureLabel(key)}</dt>
                <dd>{metric(value, key)}</dd>
                <span className="track" aria-hidden>
                  <i className={rank != null && rank >= 0.5 ? "high" : ""} style={{ width: `${(rank ?? 0) * 100}%` }} />
                </span>
                <small>{rank == null ? "Không có số liệu" : `Cao hơn ${Math.round(rank * 100)}% số mã`}</small>
              </div>
            );
          })}
        </dl>
      </section>
      <Link className="insp-open" href={`/stocks?ticker=${encodeURIComponent(ticker)}`}>
        Mở trang cổ phiếu <ArrowUpRight size={15} />
      </Link>
    </>
  );
}

export default function Overview() {
  const s = useSelection("market");
  const kind = s.kind;
  const tab = s.params.get("tab") === "sizes" ? "sizes" : "map";
  const d = s.data?.datasets;
  const snapshot = useApi<SnapshotData>(
    d ? url(`snapshots/${kind}`, { date: d[kind].latest.date, version: d[kind].version }) : null,
  );
  const [group, setGroup] = useState<string>("all");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(PAGE);
  const data = snapshot.data;
  const ticker = useMemo(() => {
    const wanted = (s.params.get("t") || "").toUpperCase();
    if (!data) return wanted;
    if (data.points.some((p) => p.ticker === wanted)) return wanted;
    return data.points.find((p) => p.ticker === "FPT")?.ticker || data.points[0]?.ticker || "";
  }, [data, s.params]);
  const rows = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toUpperCase();
    return data.points
      .filter((p) =>
        group === "all" ? true : group === "illiquid" ? p.liquidity === "ILLIQUID" : p.cluster === Number(group),
      )
      .filter((p) => !q || p.ticker.includes(q) || (p.name || "").toUpperCase().includes(q))
      .sort((a, b) => (b.features.liquidity_21 ?? -1) - (a.features.liquidity_21 ?? -1) || a.ticker.localeCompare(b.ticker));
  }, [data, group, query]);
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;
  if (!d) return <Skeleton height={600} />;
  const labels = data ? Object.keys(data.snapshot.sizes).map(Number) : [];
  const names = data ? Object.fromEntries(data.profiles.map((p) => [p.cluster, p.name])) : {};
  const hasMap = !!data?.points.some((p) => p.features._map_x != null);
  const select = (t: string) => s.set({ t });
  const columns = KEY_FEATURES[kind].slice(0, 4);
  const illiquid = data?.points.filter((p) => p.liquidity === "ILLIQUID").length || 0;
  return (
    <>
      <header className="bp-hero">
        <div>
          <span className="bp-tag">[00 // Tổng quan]</span>
          <h1>Toàn cảnh cổ phiếu Việt Nam</h1>
          <p>Ba mô hình phân nhóm trên {number(d.market.latest.n)} mã · dữ liệu lịch sử, không phải giá trực tiếp.</p>
        </div>
        <button className="bp-search" onClick={() => window.dispatchEvent(new Event("delta:search"))}>
          <Search size={18} />
          Tìm mã hoặc tên doanh nghiệp…
          <kbd>Ctrl K</kbd>
        </button>
      </header>

      <section className="bp-grid bp-kpis" aria-label="Chỉ số chính">
        <div className="bp-cell">
          <header>
            <span>[01 // Tập cổ phiếu]</span>
            <i className="status-square" />
          </header>
          <div className="kpi-body">
            <div className="kpi-value">
              {number(d.market.latest.n)}
              <small>mã</small>
            </div>
            <p>Giá hằng ngày và báo cáo tài chính năm</p>
          </div>
          <footer>
            Giá đến {dateLabel(d.market.latest.date)} · BCTC {d.financial.dates[0]}–{d.financial.latest.date}
          </footer>
        </div>
        {KINDS.map((k, i) => (
          <Kpi key={k} index={`0${i + 2}`} kind={k} d={d[k]} />
        ))}
      </section>

      <section className="bp-grid bp-work" aria-label="Bàn làm việc">
        <div className="bp-cell">
          <div className="bp-tabs" role="tablist" aria-label="Mô hình">
            {KINDS.map((k, i) => (
              <button
                key={k}
                role="tab"
                aria-selected={tab === "map" && kind === k}
                onClick={() => {
                  setGroup("all");
                  setLimit(PAGE);
                  s.set({ kind: k, tab: null });
                }}
              >
                0{i + 1}. {FAMILY[k].letter} · {FAMILY[k].label}
              </button>
            ))}
            <button role="tab" aria-selected={tab === "sizes"} onClick={() => s.set({ tab: "sizes" })}>
              04. Quy mô
            </button>
            <span className="spacer" />
            <span className="hint">Fig {FAMILY[kind].letter}.1 · {dateLabel(d[kind].latest.date)}</span>
          </div>
          {snapshot.error ? (
            <ErrorState message={snapshot.error} retry={snapshot.retry} />
          ) : !data ? (
            <Skeleton height={430} />
          ) : tab === "map" ? (
            <div className="bp-viewport">
              <Scatter
                data={data}
                x={hasMap ? "_map_x" : KEY_FEATURES[kind][0]}
                y={hasMap ? "_map_y" : KEY_FEATURES[kind][1]}
                map={hasMap}
                names={names}
                kind={kind}
                height={500}
                focus={ticker}
                selected={group === "all" || group === "illiquid" ? "" : group}
                onSelect={select}
              />
            </div>
          ) : (
            <div className="bp-viewport">
              <dl className="bars" style={{ padding: "16px 8px" }}>
                {labels.map((id) => {
                  const n = data.snapshot.sizes[String(id)];
                  return (
                    <div key={id}>
                      <dt>
                        {FAMILY[kind].letter}
                        {id} · {names[id] || "—"}
                      </dt>
                      <dd>
                        {number(n)} mã · {number((100 * n) / data.snapshot.n, 1)}%
                      </dd>
                      <span className="track" aria-hidden>
                        <i style={{ width: `${(100 * n) / data.snapshot.n}%`, background: clusterColor(id, labels) }} />
                      </span>
                    </div>
                  );
                })}
              </dl>
            </div>
          )}
          {data && (
            <div className="bp-legend" aria-label="Lọc theo nhóm">
              {labels.map((id) => (
                <button
                  key={id}
                  aria-pressed={group === String(id)}
                  onClick={() => {
                    setGroup(group === String(id) ? "all" : String(id));
                    setLimit(PAGE);
                  }}
                >
                  <i style={{ background: clusterColor(id, labels) }} />
                  <b>
                    {FAMILY[kind].letter}
                    {id}
                  </b>
                  <span>{names[id] || "—"}</span>
                  <small>{number(data.snapshot.sizes[String(id)])}</small>
                </button>
              ))}
            </div>
          )}
        </div>
        <aside className="bp-cell inspector" aria-label="Chi tiết mã đang chọn">
          <header className="ruled">
            <span>[05 // Soi mã]</span>
            <span className="meta">Mô hình {FAMILY[kind].letter}</span>
          </header>
          {data ? <Inspector kind={kind} data={data} ticker={ticker} /> : <Skeleton height={420} />}
        </aside>
      </section>

      <section className="bp-grid" aria-label="Bảng lọc cổ phiếu">
        <div className="bp-cell">
          <header className="ruled">
            <span>[06 // Bảng lọc cổ phiếu · mô hình {FAMILY[kind].letter}]</span>
            <span className="meta">{number(rows.length)} mã</span>
          </header>
          <div className="screener-bar">
            <button aria-pressed={group === "all"} onClick={() => setGroup("all")}>
              Tất cả
            </button>
            {labels.map((id) => (
              <button key={id} aria-pressed={group === String(id)} onClick={() => setGroup(String(id))}>
                {FAMILY[kind].letter}
                {id}
              </button>
            ))}
            {illiquid > 0 && (
              <button aria-pressed={group === "illiquid"} onClick={() => setGroup("illiquid")}>
                Kém thanh khoản
              </button>
            )}
            <label>
              <Search size={15} />
              <input
                aria-label="Lọc theo mã"
                placeholder="Lọc mã…"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setLimit(PAGE);
                }}
              />
            </label>
          </div>
          <div className="table-scroll">
            <table className="screener">
              <thead>
                <tr>
                  <th>Mã</th>
                  <th className="nm">Doanh nghiệp</th>
                  <th>Nhóm</th>
                  {columns.map((c) => (
                    <th key={c} className="r">
                      {featureLabel(c)}
                    </th>
                  ))}
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, limit).map((p) => (
                  <tr key={p.ticker} aria-selected={p.ticker === ticker} onClick={() => select(p.ticker)}>
                    <td className="tk">{p.ticker}</td>
                    <td className="nm">{p.name || "—"}</td>
                    <td>
                      <span className="group">
                        <i style={{ background: clusterColor(p.cluster, labels) }} />
                        {FAMILY[kind].letter}
                        {p.cluster}
                      </span>
                    </td>
                    {columns.map((c) => (
                      <td key={c} className="r">
                        {metric(p.features[c], c)}
                      </td>
                    ))}
                    <td>{p.liquidity === "ILLIQUID" ? <span className="tag warn">Kém TK</span> : <span className="tag">Giao dịch</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="screener-more">
            <span>
              Hiển thị {number(Math.min(limit, rows.length))} / {number(rows.length)} · xếp theo giá trị giao dịch
            </span>
            {limit < rows.length && (
              <button className="button small" onClick={() => setLimit(limit + PAGE)}>
                Xem thêm {PAGE}
              </button>
            )}
          </div>
        </div>
      </section>
      <p className="bp-note">
        Nhóm là kết quả thống kê, không phải khuyến nghị đầu tư. Báo cáo tài chính năm có thể công bố sau ngày giá được dùng.{" "}
        <Link className="text-link" href="/lab?tab=quality">
          Đọc giới hạn ↗
        </Link>
      </p>
    </>
  );
}
