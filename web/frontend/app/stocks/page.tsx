"use client";
import { useState, useCallback } from "react";
import { Search } from "lucide-react";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { number, metric, COLORS, FAMILY } from "@/lib/format";
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
export default function Stocks() {
  const s = useSelection();
  const ticker = (s.params.get("ticker") || "FPT").toUpperCase();
  const [input, setInput] = useState(""),
    [basis, setBasis] = useState("adj_close"),
    [compareText, setCompareText] = useState("FPT, VNM, HPG"),
    [comparison, setComparison] = useState("FPT,VNM,HPG"),
    [fy, setFy] = useState("2025");
  const stock = useApi<Stock>(
    s.date
      ? url(`stocks/${encodeURIComponent(ticker)}`, {
          kind: s.kind,
          date: s.date,
        })
      : null,
  );
  const prices = useApi<PriceData>(
    s.date
      ? url(`prices/${encodeURIComponent(ticker)}`, {
          basis,
          end: s.date.length === 4 ? `${s.date}-12-31` : s.date,
        })
      : null,
  );
  const compare = useApi<Comparison>(
    s.date
      ? url("compare", { tickers: comparison, kind: s.kind, date: s.date })
      : null,
  );
  const choose = useCallback((ticker: string) => s.set({ ticker }), [s.set]);
  if (s.error) return <ErrorState message={s.error} />;
  if (!s.data || !s.dataset) return <Skeleton height={600} />;
  const annual = stock.data?.history.financial.find((r) => r.date === fy);
  const last = prices.data?.points.filter((p) => p.close !== null).at(-1);
  return (
    <>
      <PageHeading
        eyebrow="CỔ PHIẾU / PHÂN TÍCH CHI TIẾT"
        title="Tra cứu cổ phiếu"
        description="Theo dõi doanh nghiệp qua lịch sử giá, các đặc trưng và thành viên của từng mô hình độc lập."
        action={
          <form
            className="search-field"
            onSubmit={(e) => {
              e.preventDefault();
              if (input.trim()) s.set({ ticker: input.trim().toUpperCase() });
            }}
          >
            <Search size={14} />
            <input
              aria-label="Tra cứu mã cổ phiếu"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nhập mã, ví dụ FPT"
            />
            <button className="button small" type="submit">
              Xem
            </button>
          </form>
        }
      />
      <div className="toolbar">
        <FamilyTabs
          value={s.kind}
          onChange={(kind) => s.set({ kind, date: null })}
        />
        <TimeMachine
          dates={s.dataset.dates}
          date={s.date}
          onChange={(date) => s.set({ date })}
        />
      </div>
      <ScopeNote kind={s.kind} />
      {stock.error ? (
        <ErrorState message={stock.error} retry={stock.retry} />
      ) : !stock.data ? (
        <Skeleton height={360} />
      ) : (
        <>
          <div className="stock-header section-gap">
            <div className="stock-avatar">{ticker.slice(0, 2)}</div>
            <div>
              <h1>{ticker}</h1>
              <p>{stock.data.security.name}</p>
            </div>
            <div className="stock-header-actions">
              <Badge>
                {stock.data.security.exchange || "Chưa xác minh sàn"}
              </Badge>
              {stock.data.current ? (
                <ClusterBadge kind={s.kind} id={stock.data.current.cluster} />
              ) : (
                <Badge tone="amber">Không có nhãn cụm tại ngày này</Badge>
              )}
            </div>
          </div>
          <IndicatorReference ticker={ticker} />
          <div className="grid-two">
            <Panel
              title="Giá đóng cửa lịch sử"
              eyebrow="VND / CỔ PHIẾU · DỮ LIỆU NGÀY QUAN SÁT"
              action={
                <select
                  aria-label="Loại giá"
                  value={basis}
                  onChange={(e) => setBasis(e.target.value)}
                >
                  <option value="adj_close">
                    Giá điều chỉnh theo nhà cung cấp
                  </option>
                  <option value="raw_close">Giá đóng cửa gốc</option>
                </select>
              }
            >
              {prices.error ? (
                <ErrorState message={prices.error} />
              ) : !prices.data ? (
                <Skeleton />
              ) : !prices.data.available ? (
                <EmptyState
                  title="Không có lịch sử giá"
                  message={prices.data.missing_reason || "Chưa có dữ liệu"}
                />
              ) : (
                <>
                  <div className="price-header">
                    <div>
                      <strong>₫{number(last?.close, 2)}</strong>
                      <small>
                        Quan sát gần nhất {last?.date} · đến kỳ đang chọn
                      </small>
                    </div>
                    <Badge>Lịch sử</Badge>
                  </div>
                  <Chart
                    height={300}
                    label={`${ticker} historical ${basis} đóng cửa, VND/cổ phiếu`}
                    option={{
                      ...baseChart,
                      tooltip: { ...baseChart.tooltip, trigger: "axis" },
                      grid: { ...baseChart.grid, bottom: 65 },
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
                          height: 18,
                          bottom: 10,
                          borderColor: "#293c51",
                          textStyle: { color: "#70859e" },
                        },
                      ],
                      series: [
                        {
                          type: "line",
                          symbol: "none",
                          connectNulls: false,
                          data: prices.data.points.map((p) => p.close),
                          lineStyle: { color: COLORS[0], width: 1.7 },
                          areaStyle: { color: "#2dd4bf09" },
                        },
                      ],
                    }}
                  />
                  <p className="panel-note">
                    {stock.data.price_scope} Giá thiếu hoặc xung đột được giữ
                    trống. Giá điều chỉnh là dữ liệu tham chiếu từ nhà cung cấp,
                    chưa phải chuỗi tổng lợi nhuận đã xác minh.
                  </p>
                </>
              )}
            </Panel>
            <Panel
              title="Đặc trưng tại thời điểm chọn"
              eyebrow={`${FAMILY[s.kind].label.toUpperCase()} · ${s.date}`}
            >
              <div className="panel-body">
                {stock.data.current ? (
                  Object.entries(stock.data.current.features).map(([f, v]) => (
                    <div className="feature-row" key={f}>
                      <span>{s.data?.metadata.definitions[f]?.label || f}</span>
                      <strong>{metric(v, f)}</strong>
                    </div>
                  ))
                ) : (
                  <p className="warning-line">
                    {stock.data.current_missing_reason}
                  </p>
                )}
              </div>
            </Panel>
          </div>
          <Panel
            className="section-gap"
            title="Hành trình phân cụm"
            eyebrow="NHÃN GỐC ĐÃ LƯU · MÔ HÌNH ĐỘC LẬP"
          >
            <Chart
              height={280}
              label={`${ticker} lịch sử nhãn cụm gốc của A, B và C`}
              option={{
                ...baseChart,
                tooltip: {
                  ...baseChart.tooltip,
                  trigger: "item",
                  renderMode: "richText",
                  formatter: (p: unknown) => {
                    const v = p as {
                      seriesName: string;
                      data: {
                        value: [string, number];
                        date: string;
                        cluster: number;
                      };
                    };
                    return `${v.seriesName}\n${v.data.date} · nhãn cụm gốc ${v.data.cluster}`;
                  },
                },
                xAxis: { ...axis, type: "time" },
                yAxis: {
                  ...axis,
                  type: "category",
                  data: ["A · Thị trường", "B · Năm tài chính", "C · Kết hợp"],
                  splitLine: { show: true, lineStyle: { color: "#233448" } },
                },
                series: (["market", "financial", "combined"] as Kind[]).map(
                  (kind, i) => ({
                    name: FAMILY[kind].label,
                    type: "scatter" as const,
                    symbolSize: kind === "market" ? 6 : 12,
                    data: stock.data!.history[kind].map((r) => ({
                      value: [
                        r.date.length === 4 ? `${r.date}-12-31` : r.date,
                        i,
                      ],
                      date: r.date,
                      cluster: r.cluster,
                      itemStyle: { color: COLORS[r.cluster] },
                    })),
                  }),
                ),
              }}
            />
            <p className="panel-note">
              Mốc năm tài chính được đặt ở cuối năm chỉ để bố trí biểu đồ, không
              phải ngày công bố. Nhãn có thể đổi ý nghĩa giữa các lần fit độc
              lập. Lịch sử sau ngày chọn chỉ là ngữ cảnh lưu trữ, không phải
              thông tin đã biết tại ngày đó.
            </p>
          </Panel>
          <Panel
            className="section-gap"
            title="Thẻ tham chiếu tài chính"
            eyebrow="CHỌN NĂM TÀI CHÍNH RIÊNG · THAM CHIẾU SAU KỲ BÁO CÁO"
            action={
              <select
                aria-label="Năm tài chính của cổ phiếu"
                value={fy}
                onChange={(e) => setFy(e.target.value)}
              >
                {s.data.datasets.financial.dates.map((y) => (
                  <option key={y}>{y}</option>
                ))}
              </select>
            }
          >
            <div className="panel-body">
              {annual ? (
                <>
                  <ClusterBadge kind="financial" id={annual.cluster} />
                  <div
                    className="stock-metrics"
                    style={{ padding: 0, marginTop: 15 }}
                  >
                    {Object.entries(annual.features).map(([f, v]) => (
                      <div className="stock-metric" key={f}>
                        <span>{s.data?.metadata.definitions[f]?.label}</span>
                        <strong>{metric(v, f)}</strong>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="warning-line">
                  Doanh nghiệp không có nhãn tài chính trong nhóm cố định đủ 10
                  năm.
                </p>
              )}
              <p className="muted text-small">{stock.data.financial_scope}</p>
            </div>
          </Panel>
        </>
      )}
      <Panel
        className="section-gap"
        title="So sánh cổ phiếu"
        eyebrow={`CÙNG MỘT ${FAMILY[s.kind].label.toUpperCase()} THỜI ĐIỂM · ${s.date}`}
      >
        <form
          className="stock-compare-input"
          onSubmit={(e) => {
            e.preventDefault();
            setComparison(
              compareText
                .split(",")
                .map((t) => t.trim().toUpperCase())
                .filter(Boolean)
                .join(","),
            );
          }}
        >
          <input
            aria-label="Các mã cần so sánh"
            value={compareText}
            onChange={(e) => setCompareText(e.target.value)}
            placeholder="Nhập 1–4 mã, phân cách bằng dấu phẩy"
          />
          <button className="button small">So sánh</button>
        </form>
        {compare.error ? (
          <ErrorState message={compare.error} />
        ) : !compare.data ? (
          <Skeleton height={200} />
        ) : (
          <div className="data-table-wrap">
            <table className="data-table compare-table">
              <thead>
                <tr>
                  <th>Đặc trưng</th>
                  {compare.data.items.map((item, i) => (
                    <th key={i}>{item.security.ticker}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Thành viên cụm</td>
                  {compare.data.items.map((item, i) => (
                    <td key={i}>
                      {item.observation ? (
                        <ClusterBadge
                          kind={s.kind}
                          id={item.observation.cluster}
                        />
                      ) : (
                        <span title={item.missing_reason || ""}>
                          Chưa có dữ liệu
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
                {compare.data.features.map((f) => (
                  <tr key={f}>
                    <td>{s.data?.metadata.definitions[f]?.label}</td>
                    {compare.data!.items.map((item, i) => (
                      <td key={i}>
                        {metric(item.observation?.features[f], f)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="panel-note">
          Không có nhãn thì giữ trống; không thay bằng quan sát của ngày khác.
        </p>
      </Panel>
      <Panel
        className="section-gap"
        title="Tập cổ phiếu nghiên cứu"
        eyebrow="MỞ CHI TIẾT BẤT KỲ CỔ PHIẾU NÀO"
      >
        <MembersTable kind={s.kind} date={s.date} onSelect={choose} />
      </Panel>
    </>
  );
}
