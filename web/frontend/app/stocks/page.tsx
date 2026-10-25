"use client";
import { useState } from "react";
import { Search } from "lucide-react";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { number } from "@/lib/format";
import { formatMetric, signedPercent } from "@/lib/indicator-format";
import type { PriceData, StockFundamentals, StockOverview } from "@/lib/types";
import { Panel, Skeleton, ErrorState, EmptyState } from "@/components/ui";
import { Chart, baseChart, axis } from "@/components/chart";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { StockCards } from "@/components/stock/stock-cards";
import { FundamentalsTable } from "@/components/stock/fundamentals-table";
import { ScoresPanel } from "@/components/stock/scores-panel";
import { PeersTable } from "@/components/stock/peers-table";
import { MethodDialog } from "@/components/stock/method-dialog";

const tabs = [
  ["overview", "Tổng quan"],
  ["indicators", "Chỉ số tài chính"],
  ["scores", "Điểm sức khỏe"],
  ["peers", "So sánh cùng nhóm"],
] as const;

function Change({ label, value }: { label: string; value: number | null | undefined }) {
  const tone = value == null ? "" : value > 0 ? "up" : value < 0 ? "down" : "";
  return (
    <span className={`price-change ${tone}`}>
      <small>{label}</small>
      {signedPercent(value)}
    </span>
  );
}

export default function Stocks() {
  const s = useSelection();
  const ticker = (s.params.get("ticker") || "FPT").toUpperCase();
  const tab = tabs.some(([id]) => id === s.params.get("tab")) ? s.params.get("tab")! : "overview";
  const basis = s.params.get("basis") === "raw_close" ? "raw_close" : "adj_close";
  const [input, setInput] = useState("");
  const path = `stocks/${encodeURIComponent(ticker)}`;
  const overview = useApi<StockOverview>(url(`${path}/overview`));
  const fundamentals = useApi<StockFundamentals>(url(`${path}/fundamentals`, { from: 2016, to: 2025 }));
  const prices = useApi<PriceData>(tab === "overview" ? url(`prices/${encodeURIComponent(ticker)}`, { basis }) : null);
  const o = overview.data;
  const latest = o?.latest_fiscal_year || 2025;
  const scoreYear = Number(s.params.get("fy")) || latest;
  const go = (next: string) => s.set({ ticker: next, tab: null, fy: null });
  // A link from another data revision must not silently show this bundle's numbers.
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;

  return (
    <>
      <form
        className="search-field stock-search"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          if (input.trim()) {
            go(input.trim().toUpperCase());
            setInput("");
          }
        }}
      >
        <Search size={18} />
        <input
          aria-label="Tra cứu mã cổ phiếu"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nhập mã, ví dụ FPT"
        />
        <button className="button small">Xem</button>
      </form>
      {overview.error ? (
        <ErrorState message={overview.error} retry={overview.retry} />
      ) : !o ? (
        <Skeleton height={260} />
      ) : (
        <>
          <header className="stock-header">
            <div className="stock-title">
              <h1>
                {o.ticker}
                <span>{o.name}</span>
              </h1>
              <p>
                {o.exchange || "—"} · {o.sector_label}
              </p>
            </div>
            <div className="stock-quote">
              {o.price ? (
                <>
                  <strong>{number(o.price.close)} đ</strong>
                  <small>Đóng cửa {new Date(`${o.price.date}T00:00:00Z`).toLocaleDateString("vi-VN", { timeZone: "UTC" })}</small>
                  <div className="price-changes">
                    <Change label="1 ngày" value={o.price.change_1d} />
                    <Change label="1 tháng" value={o.price.change_1m} />
                    <Change label="Từ đầu năm" value={o.price.change_ytd} />
                  </div>
                </>
              ) : (
                <small>Chưa có dữ liệu giá.</small>
              )}
              <p className="stock-cap">
                Vốn hóa <b>{formatMetric(o.market_cap, "vnd", "market_cap")}</b>
              </p>
            </div>
          </header>
          {o.cards.length ? (
            <>
              <p className="cards-caption">Chỉ số năm tài chính {o.latest_fiscal_year}</p>
              <StockCards cards={o.cards} sector={o.sector_group} />
            </>
          ) : (
            <EmptyState title="Chưa có báo cáo tài chính" message="Mã này chưa có báo cáo năm nào trong dữ liệu." />
          )}
        </>
      )}
      <WorkspaceTabs tabs={tabs} scope="stock" value={tab} onChange={(next) => s.set({ tab: next })} />
      <div role="tabpanel" id="stock-panel" aria-labelledby={`stock-${tab}`} className="stock-panel">
        {tab === "overview" && (
          <>
            {o && o.summary.length > 0 && (
              <Panel title="Tóm tắt">
                <ul className="stock-summary">
                  {o.summary.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </Panel>
            )}
            <Panel
              className="section-gap"
              title="Giá đóng cửa"
              eyebrow="ĐỒNG / CỔ PHIẾU"
              action={
                <select aria-label="Loại giá" value={basis} onChange={(e) => s.set({ basis: e.target.value })}>
                  <option value="adj_close">Giá điều chỉnh</option>
                  <option value="raw_close">Giá thực tế</option>
                </select>
              }
            >
              {prices.error ? (
                <ErrorState message={prices.error} retry={prices.retry} />
              ) : !prices.data ? (
                <Skeleton />
              ) : !prices.data.available ? (
                <EmptyState title="Không có lịch sử giá" message="Chưa có dữ liệu giá cho mã này." />
              ) : (
                <>
                  <Chart
                    height={320}
                    label={`${ticker}: giá đóng cửa theo ngày`}
                    option={{
                      ...baseChart,
                      tooltip: { ...baseChart.tooltip, trigger: "axis" },
                      grid: { ...baseChart.grid, bottom: 70 },
                      xAxis: { ...axis, type: "category", data: prices.data.points.map((p) => p.date) },
                      yAxis: { ...axis, type: "value", scale: true },
                      dataZoom: [
                        { type: "inside", start: 70, end: 100 },
                        { type: "slider", height: 22, bottom: 12, textStyle: { fontSize: 12, color: "#b8c2d4" } },
                      ],
                      series: [
                        {
                          type: "line",
                          symbol: "none",
                          connectNulls: false,
                          data: prices.data.points.map((p) => p.close),
                          lineStyle: { color: "#67d5bf", width: 2 },
                        },
                      ],
                    }}
                  />
                  <p className="panel-note">
                    {basis === "adj_close"
                      ? "Giá điều chỉnh theo cổ tức và chia tách để so sánh xu hướng."
                      : "Giá khớp thực tế từng phiên, chưa điều chỉnh."}
                  </p>
                </>
              )}
            </Panel>
          </>
        )}
        {tab === "indicators" &&
          (fundamentals.error ? (
            <ErrorState message={fundamentals.error} retry={fundamentals.retry} />
          ) : !fundamentals.data || !o ? (
            <Skeleton height={600} />
          ) : (
            <Panel title="Chỉ số tài chính theo năm" eyebrow="BÁO CÁO NĂM 2016–2025">
              <FundamentalsTable data={fundamentals.data} sector={o.sector_group} />
              <p className="panel-note">Ô “—”: rê chuột hoặc chạm để xem lý do. Tỷ lệ tính trên số liệu cả năm.</p>
            </Panel>
          ))}
        {tab === "scores" && o && (
          <ScoresPanel
            key={`${ticker}-${scoreYear}`}
            ticker={ticker}
            year={scoreYear}
            years={Array.from({ length: 10 }, (_, i) => 2025 - i)}
            onYear={(y) => s.set({ fy: String(y) })}
            sectorLabel={o.sector_label}
          />
        )}
        {tab === "peers" && <PeersTable key={ticker} ticker={ticker} onSelect={go} />}
      </div>
      <footer className="stock-footer">
        Nguồn: báo cáo tài chính năm (CafeF/DStock), giá đóng cửa HOSE/HNX/UPCOM. <MethodDialog data={fundamentals.data} />
      </footer>
    </>
  );
}
