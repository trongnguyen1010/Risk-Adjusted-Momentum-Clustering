"use client";
import { useMemo } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { useApi, url } from "@/lib/api";
import { useSelection } from "@/lib/selection";
import { Chart, axis, baseChart } from "@/components/chart";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui";
import { COLORS, dateLabel, number } from "@/lib/format";
import type { BacktestHoldings, BacktestMetrics, BacktestSegment, BacktestSeries, BacktestSummary } from "@/lib/types";

const SEGMENTS = [
  ["development", "Development"],
  ["holdout", "Holdout"],
] as const;
const TABS = [
  ["compare", "So sánh"],
  ["nav", "Đường NAV"],
  ["holdings", "Danh mục theo kỳ"],
  ["provenance", "Nguồn & giới hạn"],
] as const;
/** Combined uses the chart accent (#ff5500 is swapped for --accent by Chart); VNINDEX is the muted dashed line. */
const STRATEGY: Record<string, { label: string; help: string; color: string }> = {
  combined: { label: "Kết hợp", help: "Cụm thị trường dẫn đầu ∩ cụm tài chính được phép, xếp theo động lượng", color: "#ff5500" },
  market_only: { label: "Chỉ thị trường", help: "Chỉ lọc theo cụm thị trường dẫn đầu", color: COLORS[1] },
  financial_only: { label: "Chỉ tài chính", help: "Chỉ lọc theo cụm tài chính được phép (B-PIT)", color: COLORS[0] },
  equal_weight: { label: "Đồng tỷ trọng", help: "Toàn bộ mã đủ điều kiện, tỷ trọng bằng nhau", color: COLORS[3] },
  momentum_only: { label: "Chỉ động lượng", help: "Xếp theo động lượng, không dùng phân cụm", color: COLORS[4] },
  vnindex: { label: "VNINDEX", help: "Chỉ số giá tham chiếu", color: "#aab6ca" },
};
const STATUS: Record<string, string> = {
  OK: "Đã chọn danh mục",
  UNIVERSE_TOO_SMALL: "Tập ứng viên dưới ngưỡng tối thiểu: không mua mới",
  NOT_EXECUTED_SEGMENT_END: "Quyết định cuối đoạn: không thực hiện",
};
const INPUT_LABEL: Record<string, string> = {
  terminal_sha256: "Bộ phân cụm A v4 (terminal.sqlite)",
  b_pit_labels_sha256: "Nhãn tài chính B-PIT",
  indicators_sha256: "Chỉ số tài chính v1",
  availability_sha256: "Ngày công bố BCTC",
  c8_prices_sha256: "Giá ngày C8",
  c8_benchmark_sha256: "VNINDEX C8",
  c8_calendar_sha256: "Lịch phiên C8",
};

const pct = (v: number | null | undefined, digits = 1) =>
  v == null || !Number.isFinite(v)
    ? "—"
    : `${(Math.abs(v) < 1e-9 ? 0 : v * 100).toLocaleString("vi-VN", { minimumFractionDigits: digits, maximumFractionDigits: digits })}%`;
const tone = (v: number | null | undefined) => (v == null ? "" : v > 0 ? "up" : v < 0 ? "down" : "");
const short = (sha: string) => `${sha.slice(0, 12)}…`;

function Kpi({ label, value, compare, note }: { label: string; value: number | null; compare?: number | null; note: string }) {
  return (
    <div className="bp-cell">
      <header>
        <span>{label}</span>
      </header>
      <div className="kpi-body">
        <div className="kpi-value">{pct(value)}</div>
        <p>
          {compare !== undefined && <b className="bt-vs">VNINDEX {pct(compare)}</b>}
          {note}
        </p>
      </div>
    </div>
  );
}

function CompareTable({ seg, order }: { seg: BacktestSegment; order: string[] }) {
  const rows: [string, BacktestMetrics][] = [...order, "vnindex"].map((k) => [k, seg.metrics[k]]);
  return (
    <>
      <div className="table-scroll">
        <table className="screener bt-table">
          <thead>
            <tr>
              <th>Chiến lược</th>
              <th className="r">Tổng lợi suất</th>
              <th className="r">CAGR</th>
              <th className="r">Biến động năm</th>
              <th className="r">Sụt giảm tối đa</th>
              <th className="r">Vòng quay TB</th>
              <th className="r">Tiền mặt TB</th>
              <th className="r">Mua lỗi / bán lỗi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([key, m]) => (
              <tr key={key} aria-selected={key === "combined"}>
                <td className="tk">
                  <span className="group" title={STRATEGY[key].help}>
                    <i style={{ background: key === "combined" ? "var(--accent)" : STRATEGY[key].color }} />
                    {STRATEGY[key].label}
                  </span>
                </td>
                <td className="r">
                  <span className={`bt-num ${tone(m.total_return)}`}>{pct(m.total_return)}</span>
                </td>
                <td className="r">{pct(m.cagr)}</td>
                <td className="r">{pct(m.volatility_annual)}</td>
                <td className="r">{pct(m.max_drawdown)}</td>
                <td className="r">{pct(m.avg_turnover)}</td>
                <td className="r">{pct(m.avg_cash_after_trading)}</td>
                <td className="r">{key === "vnindex" ? "—" : `${number(m.failed_buys)} / ${number(m.failed_sells)}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="bt-caption">
        {number(seg.metrics.combined.periods)} kỳ thực hiện · {dateLabel(seg.start)} – {dateLabel(seg.end)} · NAV bắt đầu
        bằng 1. Kết hợp có {number(seg.counts.combined?.too_small)} kỳ tập ứng viên quá nhỏ. Lệnh lỗi: không khớp do trần/sàn
        hoặc thiếu giá. Số liệu lấy nguyên từ <code>metrics.json</code> của run đã niêm phong, không tính lại.
      </p>
    </>
  );
}

function NavCharts({ data, order }: { data: BacktestSeries; order: string[] }) {
  const keys = [...order, "vnindex"];
  // The legend wraps to two rows on phones; leave room so it does not cover the plot.
  const top = typeof window !== "undefined" && window.innerWidth < 680 ? 72 : 46;
  const lines = (block: BacktestSeries["nav"], percent: boolean) => ({
    ...baseChart,
    tooltip: {
      ...baseChart.tooltip,
      trigger: "axis" as const,
      valueFormatter: (v: unknown) => (typeof v === "number" ? (percent ? pct(v) : number(v, 3)) : "—"),
    },
    legend: { top: 4, left: 8, icon: "rect", itemWidth: 14, itemHeight: 3, textStyle: { color: "#b8c2d4", fontSize: 12 } },
    grid: { ...baseChart.grid, top },
    xAxis: { ...axis, type: "category" as const, boundaryGap: false, data: block.dates },
    yAxis: {
      ...axis,
      type: "value" as const,
      scale: !percent,
      axisLabel: { ...axis.axisLabel, formatter: (v: number) => (percent ? `${Math.round(v * 100)}%` : number(v, 2)) },
    },
    series: keys.map((k) => ({
      name: STRATEGY[k].label,
      type: "line" as const,
      symbol: "none",
      data: block.series[k],
      z: k === "combined" ? 5 : 2,
      itemStyle: { color: STRATEGY[k].color },
      lineStyle: { color: STRATEGY[k].color, width: k === "combined" ? 2.5 : 1.5, type: k === "vnindex" ? ("dashed" as const) : ("solid" as const) },
    })),
  });
  return (
    <div className="bp-viewport">
      <Chart height={360} label="NAV theo kỳ của năm chiến lược và VNINDEX" option={lines(data.nav, false)} />
      <div className="bt-subhead">
        <span className="bp-tag">Mức sụt giảm từ đỉnh</span>
        <small>NAV ÷ đỉnh trước đó − 1, theo kỳ; đáy của mỗi đường bằng “Sụt giảm tối đa” trong bảng.</small>
      </div>
      <Chart height={240} label="Mức sụt giảm từ đỉnh theo kỳ" option={lines(data.drawdown, true)} />
    </div>
  );
}

function Holdings({ segment, date, onDate }: { segment: string; date: string | null; onDate: (d: string) => void }) {
  const state = useApi<BacktestHoldings>(url(`backtest/${segment}/holdings`, { date }));
  if (state.error) return <ErrorState message={state.error} retry={state.retry} />;
  if (!state.data) return <Skeleton height={420} />;
  const { periods, period } = state.data;

  return (
    <>
      <div className="bp-toolbar">
        <span className="bp-tag">Kỳ thực hiện</span>
        <select className="bt-select" aria-label="Chọn kỳ" value={period.date} onChange={(e) => onDate(e.target.value)}>
          {periods.map((p) => (
            <option key={p.date} value={p.date}>
              {p.date} · {p.executed ? `${p.n} mã` : "không thực hiện"}
              {p.status === "UNIVERSE_TOO_SMALL" ? " · tập nhỏ" : ""}
            </option>
          ))}
        </select>
        <span className="toolbar-meta">
          Quyết định {period.decision_date} · {number(period.candidates)} ứng viên
        </span>
      </div>
      <div className="bt-period">
        <span className={`tag ${period.status === "OK" ? "" : "warn"}`}>{STATUS[period.status] || period.status}</span>
        <span>
          Kết hợp nắm {number(period.items.length)} mã · tiền mặt sau giao dịch {pct(period.cash)}
        </span>
      </div>
      {period.items.length ? (
        <div className="table-scroll">
          <table className="screener bt-table">
            <thead>
              <tr>
                <th>Mã</th>
                <th className="r">Tỷ trọng</th>
                <th className="r">Hạng động lượng</th>
              </tr>
            </thead>
            <tbody>
              {period.items.map((i) => (
                <tr key={i.ticker}>
                  <td className="tk">
                    <Link className="text-link" href={`/stocks?ticker=${i.ticker}`} title={`Tra cứu ${i.ticker}`}>
                      {i.ticker} <ArrowUpRight size={13} />
                    </Link>
                  </td>
                  <td className="r">{pct(i.weight, 2)}</td>
                  <td className="r">{i.rank == null ? <span title="Mã còn giữ từ kỳ trước (chưa bán được)">giữ lại</span> : `#${i.rank}`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="Không có mã trong danh mục" message="Kỳ này danh mục Kết hợp giữ toàn bộ tiền mặt." />
      )}
      <p className="bt-caption">
        Tỷ trọng và tiền mặt sau giao dịch từ <code>holdings_combined.csv</code>; hạng từ <code>targets_combined.csv</code>. “Giữ lại” là mã
        không bán được (trần/sàn, thiếu giá) nên vẫn nằm trong danh mục.
      </p>
    </>
  );
}

function Provenance({ data, seg }: { data: BacktestSummary; seg: BacktestSegment }) {
  return (
    <div className="bt-prov">
      <dl className="bt-facts">
        <div>
          <dt>Run</dt>
          <dd>{seg.run_id}</dd>
        </div>
        <div>
          <dt>Niêm phong</dt>
          <dd>
            <span className="tag up">{seg.seal.status}</span> {seg.seal.sealed_at.slice(0, 16).replace("T", " ")} UTC
          </dd>
        </div>
        <div>
          <dt>Seal SHA-256</dt>
          <dd title={seg.seal.sha256}>{short(seg.seal.sha256)}</dd>
        </div>
        <div>
          <dt>Config ({seg.status})</dt>
          <dd title={seg.config_sha256}>
            {seg.config} · {short(seg.config_sha256)}
          </dd>
        </div>
        <div>
          <dt>Mã nguồn</dt>
          <dd title={seg.git_commit}>{seg.git_commit.slice(0, 7)}</dd>
        </div>
        <div>
          <dt>Final Evaluation</dt>
          <dd>
            <span className="tag warn">{data.final_status}</span> chưa đủ dữ liệu 2026
          </dd>
        </div>
      </dl>
      <section>
        <h3 className="bp-tag">Đầu vào đã khóa</h3>
        <ul className="source-list">
          {Object.entries(seg.inputs_sha256).map(([key, sha]) => (
            <li key={key}>
              <span className="source-path">{INPUT_LABEL[key] || key}</span>
              <code title={sha}>{short(sha)}</code>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="bp-tag">Tệp kết quả ({seg.sources.length})</h3>
        <ul className="source-list">
          {seg.sources.map((s) => (
            <li key={s.path}>
              <span className="source-path">{s.path}</span>
              <code title={s.sha256}>{short(s.sha256)}</code>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="bp-tag">Giới hạn cần biết</h3>
        <ul className="limit-list">
          <li>Kết quả lịch sử, không phải khuyến nghị mua bán và không dự báo lợi suất tương lai.</li>
          <li>Development và Holdout là hai đoạn riêng; NAV không nối liền giữa hai đoạn.</li>
          <li>Phí giao dịch và trượt giá bằng 0. Danh mục dùng giá đóng cửa điều chỉnh của nhà cung cấp, VNINDEX là chỉ số giá.</li>
          <li>Sụt giảm và biến động đo theo kỳ tháng, không theo ngày.</li>
          <li>Nhãn tài chính dùng B-PIT: báo cáo chỉ được dùng từ phiên sau ngày công bố.</li>
          <li>Final Evaluation chưa chạy (NOT_READY); Holdout không thay thế Final.</li>
        </ul>
        <p className="bt-caption">
          Chi tiết: <code>docs/REPORT_BACKTEST.md</code>, <code>M3/reports/BAO_CAO_KY_THUAT_M3.md</code>. Gói hiển thị{" "}
          {data.version} dựng từ <code>{data.outputs_manifest.path}</code> ({short(data.outputs_manifest.sha256)}); máy chủ kiểm
          lại mã băm khi khởi động.
        </p>
      </section>
    </div>
  );
}

export default function Backtest() {
  const s = useSelection();
  const summary = useApi<BacktestSummary>(url("backtest"));
  const segment = SEGMENTS.some(([id]) => id === s.params.get("seg")) ? s.params.get("seg")! : "development";
  const tab = TABS.some(([id]) => id === s.params.get("tab")) ? s.params.get("tab")! : "compare";
  const series = useApi<BacktestSeries>(tab === "nav" ? url(`backtest/${segment}/series`) : null);
  const seg = useMemo(() => summary.data?.segments.find((x) => x.segment === segment), [summary.data, segment]);
  if (summary.error) return <ErrorState message={summary.error} retry={summary.retry} />;
  if (!summary.data || !seg) return <Skeleton height={600} />;
  const order = summary.data.strategies;
  const c = seg.metrics.combined;
  const v = seg.metrics.vnindex;
  return (
    <>
      <header className="bp-hero">
        <div>
          <span className="bp-tag">Kiểm định chiến lược · M3</span>
          <h1>Backtest danh mục theo hai hệ phân cụm</h1>
          <p>
            Năm chiến lược và VNINDEX trên dữ liệu lịch sử đã niêm phong · không phải khuyến nghị đầu tư.
          </p>
        </div>
        <div className="mini-seg bt-seg" role="group" aria-label="Đoạn kiểm định">
          {SEGMENTS.map(([id, label]) => {
            const x = summary.data!.segments.find((y) => y.segment === id);
            return (
              <button key={id} aria-pressed={segment === id} onClick={() => s.set({ seg: id === "development" ? null : id, date: null })}>
                {label}
                {x && <span> · {x.start.slice(0, 4)}–{x.end.slice(0, 4)}</span>}
              </button>
            );
          })}
        </div>
      </header>

      <section className="bp-grid bp-kpis" aria-label="Chỉ số chính của chiến lược Kết hợp">
        <Kpi label="Kết hợp · tổng lợi suất" value={c.total_return} compare={v.total_return} note={`${number(c.periods)} kỳ tháng, NAV từ 1`} />
        <Kpi label="Kết hợp · CAGR" value={c.cagr} compare={v.cagr} note="Tăng trưởng kép theo năm" />
        <Kpi label="Kết hợp · sụt giảm tối đa" value={c.max_drawdown} compare={v.max_drawdown} note="Từ đỉnh xuống đáy, theo kỳ" />
        <Kpi label="Kết hợp · biến động năm" value={c.volatility_annual} compare={v.volatility_annual} note="Độ lệch chuẩn lợi suất kỳ, quy năm" />
      </section>

      <section className="bp-grid" aria-label="Kết quả backtest">
        <div className="bp-cell">
          <div className="bp-tabs" role="tablist" aria-label="Nội dung backtest">
            {TABS.map(([id, label]) => (
              <button key={id} role="tab" aria-selected={tab === id} onClick={() => s.set({ tab: id === "compare" ? null : id })}>
                {label}
              </button>
            ))}
            <span className="spacer" />
            <span className="hint">Run {seg.run_id}</span>
          </div>
          <div className="bp-stage" key={`${segment}-${tab}`}>
            {tab === "compare" && <CompareTable seg={seg} order={order} />}
            {tab === "nav" &&
              (series.error ? (
                <ErrorState message={series.error} retry={series.retry} />
              ) : !series.data ? (
                <Skeleton height={600} />
              ) : (
                <NavCharts data={series.data} order={order} />
              ))}
            {tab === "holdings" && <Holdings segment={segment} date={s.params.get("date")} onDate={(date) => s.set({ date })} />}
            {tab === "provenance" && <Provenance data={summary.data} seg={seg} />}
          </div>
        </div>
      </section>
      <p className="bp-note">
        Backtest chỉ mô tả dữ liệu lịch sử; phí và trượt giá bằng 0. Final Evaluation chưa chạy.{" "}
        <button className="text-link bt-link" onClick={() => s.set({ tab: "provenance" })}>
          Đọc giới hạn ↗
        </button>
      </p>
    </>
  );
}
