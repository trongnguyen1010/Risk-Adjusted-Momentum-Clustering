"use client";
import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { number, metric, clusterColor, FAMILY } from "@/lib/format";
import type { Stock, PriceData, Comparison, Kind } from "@/lib/types";
import {
  Panel,
  PageHeading,
  FamilyTabs,
  Badge,
  ClusterBadge,
  ScopeNote,
  Skeleton,
  ErrorState,
  EmptyState,
} from "@/components/ui";
import { Chart, baseChart, axis } from "@/components/chart";
import { TimeMachine } from "@/components/time-machine";
import { IndicatorReference } from "@/components/indicator-reference";
import { MembersTable } from "@/components/members-table";
import { LazyDetails } from "@/components/lazy-details";
import { ModelVersion, PreviewNote } from "@/components/model-version";
import { WorkspaceTabs } from "@/components/workspace-tabs";
const tabs = [
  ["overview", "Tổng quan"],
  ["indicators", "Chỉ số tài chính"],
  ["clusters", "Phân cụm"],
  ["sources", "Dữ liệu & nguồn"],
] as const;
export default function Stocks() {
  const s = useSelection();
  const ticker = (s.params.get("ticker") || "FPT").toUpperCase();
  const tab = tabs.some(([id]) => id === s.params.get("tab"))
    ? s.params.get("tab")!
    : "overview";
  const basis =
    s.params.get("basis") === "raw_close" ? "raw_close" : "adj_close";
  const fy =
    s.params.get("fy") || s.data?.datasets.financial.latest.date || "2025";
  const comparison = s.params.get("compare") || "FPT,VNM,HPG";
  const [input, setInput] = useState("");
  const stock = useApi<Stock>(
    s.date
      ? url(`stocks/${encodeURIComponent(ticker)}`, {
          kind: s.kind,
          date: s.date,
          version: s.dataset?.version,
        })
      : null,
  );
  const prices = useApi<PriceData>(
    tab === "overview" && s.date
      ? url(`prices/${encodeURIComponent(ticker)}`, {
          basis,
          end: s.date.length === 4 ? `${s.date}-12-31` : s.date,
        })
      : null,
  );
  const compare = useApi<Comparison>(
    tab === "clusters" && s.date
      ? url("compare", {
          tickers: comparison,
          kind: s.kind,
          date: s.date,
          version: s.dataset?.version,
        })
      : null,
  );
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;
  if (!s.data || !s.dataset) return <Skeleton height={600} />;
  const historyDataset = (kind: Kind) =>
    [s.data!.datasets[kind], ...(s.data!.variants?.[kind] || [])].find(
      (d) => d.version === stock.data?.history_versions?.[kind],
    ) || s.data!.datasets[kind];
  const annual = stock.data?.history.financial.find((r) => r.date === fy);
  const last = prices.data?.points.filter((p) => p.close !== null).at(-1);
  return (
    <>
      <PageHeading
        eyebrow="DOANH NGHIỆP / TRA CỨU"
        title={
          stock.data
            ? `${ticker} · ${stock.data.security.name}`
            : `Tra cứu ${ticker}`
        }
        description="Xem lợi nhuận, định giá và sức khỏe tài chính của doanh nghiệp theo từng kỳ báo cáo."
        action={
          <form
            className="search-field"
            onSubmit={(e) => {
              e.preventDefault();
              if (input.trim())
                s.set({ ticker: input.trim().toUpperCase(), source: null });
            }}
          >
            <Search size={18} />
            <input
              aria-label="Tra cứu mã cổ phiếu"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Mã, ví dụ FPT"
            />
            <button className="button small">Xem</button>
          </form>
        }
      />
      {(tab === "clusters" || tab === "sources") && <div className="toolbar">
        <FamilyTabs
          value={s.kind}
          onChange={(kind) =>
            s.set({
              kind,
              date: null,
              sort: null,
              direction: null,
              page: null,
              cluster: null,
            })
          }
        />
        <ModelVersion
          options={s.options}
          value={s.dataset.version}
          onChange={(version) => s.set({ version, cluster: null, page: null })}
        />
        <TimeMachine
          dates={s.dataset.dates}
          date={s.date}
          onChange={(date) => s.set({ date })}
        />
      </div>}
      <p className="context-line">
        {stock.data?.security.exchange || "Đang kiểm tra sàn"} · Dữ liệu giá đến {s.date}.
        {tab === "clusters" || tab === "sources" ? ` Mô hình ${FAMILY[s.kind].letter} tại ${s.date}.` : " Chọn năm và kỳ báo cáo trong phần chỉ số."}
      </p>
      {(tab === "clusters" || tab === "sources") && <PreviewNote dataset={s.dataset} />}
      <WorkspaceTabs
        tabs={tabs}
        scope="stock"
        value={tab}
        onChange={(tab) => s.set({ tab })}
      />
      <div role="tabpanel" id="stock-panel" aria-labelledby={`stock-${tab}`}>
        {stock.error ? (
          <ErrorState message={stock.error} retry={stock.retry} />
        ) : !stock.data ? (
          <Skeleton height={480} />
        ) : (
          <>
            {tab === "overview" && (
              <>
                <IndicatorReference key={ticker} ticker={ticker} />
                <div className="grid-two section-gap">
                  <Panel
                    title="Giá đóng cửa lịch sử"
                    eyebrow="VND / CỔ PHIẾU · NGÀY QUAN SÁT"
                    action={
                      <select
                        aria-label="Loại giá"
                        value={basis}
                        onChange={(e) => s.set({ basis: e.target.value })}
                      >
                        <option value="adj_close">
                          Giá điều chỉnh theo nhà cung cấp
                        </option>
                        <option value="raw_close">Giá đóng cửa gốc</option>
                      </select>
                    }
                  >
                    {prices.error ? (
                      <ErrorState message={prices.error} retry={prices.retry} />
                    ) : !prices.data ? (
                      <Skeleton />
                    ) : !prices.data.available ? (
                      <EmptyState
                        title="Không có lịch sử giá"
                        message={
                          prices.data.missing_reason || "Chưa có dữ liệu"
                        }
                      />
                    ) : (
                      <>
                        <div className="price-header">
                          <div>
                            <strong>₫{number(last?.close, 2)}</strong>
                            <small>
                              Quan sát gần nhất {last?.date} · {basis} · đến kỳ
                              mô hình {s.date}
                            </small>
                          </div>
                          <Badge>Lịch sử</Badge>
                        </div>
                        <Chart
                          height={320}
                          label={`${ticker}: giá đóng cửa ${basis}, VND/share. Quan sát gần nhất ${last?.date}: ${last?.close}.`}
                          option={{
                            ...baseChart,
                            tooltip: { ...baseChart.tooltip, trigger: "axis" },
                            grid: { ...baseChart.grid, bottom: 70 },
                            xAxis: {
                              ...axis,
                              type: "category",
                              data: prices.data.points.map((p) => p.date),
                            },
                            yAxis: { ...axis, type: "value", scale: true },
                            dataZoom: [
                              { type: "inside", start: 70, end: 100 },
                              {
                                type: "slider",
                                height: 22,
                                bottom: 12,
                                textStyle: { fontSize: 12, color: "#b8c2d4" },
                              },
                            ],
                            series: [
                              {
                                type: "line",
                                symbol: "none",
                                connectNulls: false,
                                smooth: false,
                                data: prices.data.points.map((p) => p.close),
                                lineStyle: { color: "#67d5bf", width: 2 },
                              },
                            ],
                          }}
                        />
                        <p className="panel-note">
                          Giữ gaps và basis riêng; không phải giá trực tiếp hoặc
                          total return đã xác minh.
                        </p>
                        <LazyDetails summary="Bảng quan sát giá (thay thế biểu đồ)">
                          <div className="data-table-wrap price-table">
                            <table className="data-table">
                              <thead>
                                <tr>
                                  <th>Ngày</th>
                                  <th>Giá · VND/share</th>
                                  <th>Volume · shares</th>
                                </tr>
                              </thead>
                              <tbody>
                                {prices.data.points.map((p) => (
                                  <tr key={p.date}>
                                    <td>{p.date}</td>
                                    <td>{number(p.close, 2)}</td>
                                    <td>{number(p.volume)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </LazyDetails>
                      </>
                    )}
                  </Panel>
                  <Panel
                    title="Thành viên A / B / C"
                    eyebrow="CÁC KỲ RIÊNG · KHÔNG PHẢI CÙNG THỜI ĐIỂM"
                  >
                    <div className="panel-body">
                      {(["market", "financial", "combined"] as Kind[]).map(
                        (kind) => {
                          const day =
                            kind === s.kind
                              ? s.date
                              : historyDataset(kind).latest.date;
                          const observation = stock.data!.history[kind].find(
                            (r) => r.date === day,
                          );
                          return (
                            <div className="membership-summary" key={kind}>
                              <h3>{FAMILY[kind].label}</h3>
                              <p>
                                {day} ·{" "}
                                {observation ? (
                                  <ClusterBadge
                                    kind={kind}
                                    id={observation.cluster}
                                    labels={Object.keys(
                                      historyDataset(kind).history.find(
                                        (r) => r.date === day,
                                      )?.sizes || {},
                                    ).map(Number)}
                                  />
                                ) : (
                                  "Không có membership ở đúng kỳ này"
                                )}
                              </p>
                              <Link
                                className="text-link"
                                href={`/atlas?kind=${kind}&date=${day}&version=${encodeURIComponent(stock.data!.history_versions?.[kind] || s.data!.datasets[kind].version)}${observation ? `&cluster=${observation.cluster}` : ""}`}
                              >
                                Xem hồ sơ nhóm ↗
                              </Link>
                            </div>
                          );
                        },
                      )}
                    </div>
                    <ScopeNote kind={s.kind} />
                  </Panel>
                </div>
              </>
            )}
            {tab === "indicators" && (
              <>
                <IndicatorReference
                  key={ticker}
                  ticker={ticker}
                  view="history"
                />
                <Panel
                  className="section-gap"
                  title="Sáu ratios đầu vào B / C"
                  eyebrow="KHÁC BỘ EPS / P/E / P/B / F / M / Z"
                  action={
                    <select
                      aria-label="Năm tài chính của cổ phiếu"
                      value={fy}
                      onChange={(e) => s.set({ fy: e.target.value })}
                    >
                      {s.data.datasets.financial.dates.map((y) => (
                        <option key={y} value={y}>
                          FY{y}
                        </option>
                      ))}
                    </select>
                  }
                >
                  {annual ? (
                    <div className="stock-metrics">
                      {Object.entries(annual.features).map(([f, v]) => (
                        <div className="stock-metric" key={f}>
                          <span>
                            {s.data?.metadata.definitions[f]?.label || f}
                          </span>
                          <strong>{metric(v, f)}</strong>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      title="Không có dữ liệu tài chính ở kỳ này"
                      message="Mã không có trong cohort cố định đủ 10 năm; không lấy kỳ khác để thay."
                    />
                  )}
                  <p className="panel-note">
                    FY{fy} · {stock.data.financial_scope}
                  </p>
                  <details className="indicator-details">
                    <summary>Lịch sử sáu ratios theo FY</summary>
                    <div className="data-table-wrap">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>FY</th>
                            {s.data.datasets.financial.features.map((f) => (
                              <th key={f}>
                                {s.data?.metadata.definitions[f]?.label || f}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {stock.data.history.financial.map((r) => (
                            <tr key={r.date}>
                              <th>{r.date}</th>
                              {s.data!.datasets.financial.features.map((f) => (
                                <td key={f}>{metric(r.features[f], f)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                </Panel>
              </>
            )}
            {tab === "clusters" && (
              <>
                <Panel
                  title="Membership tại đúng kỳ đã chọn"
                  eyebrow={`${FAMILY[s.kind].label} · ${s.date}`}
                >
                  <div className="panel-body">
                    {stock.data.current ? (
                      <>
                        <ClusterBadge
                          kind={s.kind}
                          id={stock.data.current.cluster}
                          labels={Object.keys(
                            stock.data.current_snapshot.sizes,
                          ).map(Number)}
                        />
                        {Object.entries(stock.data.current.features).map(
                          ([f, v]) => (
                            <div className="feature-row" key={f}>
                              <span>
                                {s.data?.metadata.definitions[f]?.label || f}
                              </span>
                              <strong>{metric(v, f)}</strong>
                            </div>
                          ),
                        )}
                      </>
                    ) : (
                      <p>{stock.data.current_missing_reason}</p>
                    )}
                  </div>
                </Panel>
                <Panel
                  className="section-gap"
                  title="Hành trình phân cụm"
                  eyebrow="NHÃN GỐC · CÁC MODEL ĐỘC LẬP"
                >
                  <div className="data-table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Mô hình</th>
                          <th>Kỳ</th>
                          <th>Nhãn đã lưu</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(
                          ["market", "financial", "combined"] as Kind[]
                        ).flatMap((kind) =>
                          stock.data!.history[kind].map((r) => (
                            <tr key={`${kind}-${r.date}`}>
                              <th>{FAMILY[kind].label}</th>
                              <td>{r.date}</td>
                              <td>
                                <ClusterBadge
                                  kind={kind}
                                  id={r.cluster}
                                  labels={Object.keys(
                                    historyDataset(kind).history.find(
                                      (snap) => snap.date === r.date,
                                    )?.sizes || {},
                                  ).map(Number)}
                                />
                              </td>
                            </tr>
                          )),
                        )}
                      </tbody>
                    </table>
                  </div>
                  <p className="panel-note">
                    FY không phải ngày công bố; nhãn giữa các lần fit độc lập
                    không có cùng ý nghĩa kinh tế.
                  </p>
                </Panel>
                <Panel
                  className="section-gap"
                  title="So sánh cổ phiếu"
                  eyebrow={`${s.kind} · ${s.date}`}
                >
                  <form
                    className="stock-compare-input"
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = new FormData(e.currentTarget);
                      s.set({
                        compare: String(form.get("tickers") || "")
                          .split(",")
                          .map((t) => t.trim().toUpperCase())
                          .filter(Boolean)
                          .join(","),
                      });
                    }}
                  >
                    <input
                      key={comparison}
                      name="tickers"
                      aria-label="Các mã cần so sánh"
                      defaultValue={comparison}
                    />
                    <button className="button small">So sánh</button>
                  </form>
                  {compare.error ? (
                    <ErrorState message={compare.error} retry={compare.retry} />
                  ) : !compare.data ? (
                    <Skeleton />
                  ) : (
                    <div className="data-table-wrap">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Đặc trưng</th>
                            {compare.data.items.map((item) => (
                              <th key={item.security.ticker}>
                                {item.security.ticker}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {compare.data.features.map((f) => (
                            <tr key={f}>
                              <th>
                                {s.data?.metadata.definitions[f]?.label || f}
                              </th>
                              {compare.data!.items.map((item) => (
                                <td key={item.security.ticker}>
                                  {item.observation
                                    ? metric(item.observation.features[f], f)
                                    : item.missing_reason}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </Panel>
                {stock.data.current && (
                  <Panel
                    className="section-gap"
                    title="Thành viên cùng cụm"
                    eyebrow="RULE: CÙNG MODEL / KỲ / NHÃN · CHƯA PHẢI NEAREST PEERS"
                  >
                    <MembersTable
                      key={`${s.kind}:${s.date}`}
                      kind={s.kind}
                      version={s.dataset.version}
                      date={s.date}
                      clusterValue={String(stock.data.current.cluster)}
                      onSelect={(ticker) => s.set({ ticker, source: null })}
                    />
                  </Panel>
                )}
              </>
            )}
            {tab === "sources" && (
              <>
                <IndicatorReference
                  key={ticker}
                  ticker={ticker}
                  view="sources"
                />
                <Panel
                  className="section-gap"
                  title="Nguồn mô hình và dữ liệu giá"
                >
                  <div className="panel-body">
                    <p>{stock.data.price_scope}</p>
                    <p>
                      Coverage giá: {stock.data.price_coverage.start} —{" "}
                      {stock.data.price_coverage.end};{" "}
                      {number(stock.data.price_coverage.rows)} rows.
                    </p>
                    <p>
                      Ngày mô hình {s.date} · version {s.dataset.version}. Không
                      gán ngày mô hình cho valuation reference.
                    </p>
                  </div>
                  <details className="indicator-details">
                    <summary>Danh sách nguồn và SHA-256</summary>
                    {s.data.provenance.map((p) => (
                      <div className="artifact-row" key={p.path}>
                        <strong>{p.path}</strong>
                        <small>SHA-256 {p.sha256}</small>
                      </div>
                    ))}
                  </details>
                </Panel>
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}
