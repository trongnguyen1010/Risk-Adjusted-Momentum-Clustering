"use client";
import { useState, useCallback } from "react";
import Link from "next/link";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { number, COLORS, metric } from "@/lib/format";
import type { SnapshotData, Matrix } from "@/lib/types";
import {
  Panel,
  PageHeading,
  Badge,
  Skeleton,
  ErrorState,
  EmptyState,
  ScopeNote,
  ClusterBadge,
} from "@/components/ui";
import { Chart, baseChart, axis } from "@/components/chart";
import { MembersTable } from "@/components/members-table";
import { StockDrawer } from "@/components/stock-drawer";
export default function Financial() {
  const s = useSelection("financial");
  const year = s.params.get("year") || "2025";
  const [field, setField] = useState("net_margin"),
    [ticker, select] = useState<string | null>(null),
    [cell, setCell] = useState<{ market: number; financial: number } | null>(
      null,
    );
  const close = useCallback(() => select(null), []);
  const state = useApi<SnapshotData>(
    url("snapshots/financial", { date: year }),
  );
  const matrix = useApi<Matrix>(url(`matrix/${year}`));
  if (s.error) return <ErrorState message={s.error} />;
  if (!s.data) return <Skeleton height={600} />;
  return (
    <>
      <PageHeading
        eyebrow="NỀN TẢNG DOANH NGHIỆP / LÁT CẮT THEO NĂM"
        title="Góc nhìn tài chính"
        description="Khám phá cấu trúc tài chính theo năm và đối chiếu với hành vi thị trường trên nhóm cổ phiếu giao nhau."
        action={
          <select
            aria-label="Năm tài chính"
            value={year}
            onChange={(e) => {
              setCell(null);
              s.set({ year: e.target.value });
            }}
          >
            {s.data.datasets.financial.dates.map((y) => (
              <option key={y} value={y}>
                Năm TC {y}
              </option>
            ))}
          </select>
        }
      />
      <div className="inline-actions">
        <Badge tone="purple">Tham chiếu năm tài chính</Badge>
        <Badge tone="amber">
          0 / {number(s.data.metadata.financial_rows)} mốc thời gian công bố
        </Badge>
      </div>
      <ScopeNote kind="financial" />
      {state.error ? (
        <ErrorState message={state.error} />
      ) : !state.data ? (
        <Skeleton />
      ) : (
        <>
          <div className="grid-equal section-gap">
            <Panel
              title="Phân bố cụm tài chính"
              eyebrow={`Năm TC ${year} · NHÓM CỐ ĐỊNH ĐỦ 10 NĂM`}
            >
              <div className="lens-metrics">
                {state.data.profiles.map((p) => (
                  <div key={p.cluster}>
                    <ClusterBadge kind="financial" id={p.cluster} />
                    <strong style={{ display: "block", marginTop: 10 }}>
                      {number(p.size)}
                    </strong>
                    <span>
                      {number((p.size / state.data!.snapshot.n) * 100, 1)}% nhóm
                      cổ phiếu theo năm
                    </span>
                  </div>
                ))}
              </div>
              <Chart
                height={230}
                label="Kích thước các cụm tài chính"
                option={{
                  ...baseChart,
                  xAxis: {
                    ...axis,
                    type: "category",
                    data: state.data.profiles.map((p) => `B${p.cluster}`),
                  },
                  yAxis: { ...axis, type: "value" },
                  series: [
                    {
                      type: "bar",
                      barMaxWidth: 65,
                      label: { show: true, position: "top", color: "#b4c9d7" },
                      data: state.data.profiles.map((p) => ({
                        value: p.size,
                        itemStyle: { color: COLORS[p.cluster] },
                      })),
                    },
                  ],
                }}
              />
              <p className="panel-note">
                Các nhóm mất cân bằng có thể chịu ảnh hưởng bởi giá trị tài
                chính cực đoan. Nhãn cụm không phải đánh giá chất lượng, độ an
                toàn hay thứ hạng đầu tư.
              </p>
            </Panel>
            <Panel
              title="Phân bố và giá trị cực đoan"
              eyebrow="TỨ PHÂN VỊ THỰC TẾ · KHÔNG CẮT NGỌN"
              action={
                <select
                  aria-label="Chỉ tiêu tài chính cần xem phân bố"
                  value={field}
                  onChange={(e) => setField(e.target.value)}
                >
                  {s.data.datasets.financial.features.map((f) => (
                    <option key={f} value={f}>
                      {s.data?.metadata.definitions[f]?.label}
                    </option>
                  ))}
                </select>
              }
            >
              <Chart
                height={305}
                label={`Biểu đồ hộp của ${field} theo các cụm tài chính`}
                option={{
                  ...baseChart,
                  tooltip: { ...baseChart.tooltip, renderMode: "richText" },
                  xAxis: {
                    ...axis,
                    type: "category",
                    data: state.data.profiles.map((p) => `B${p.cluster}`),
                  },
                  yAxis: { ...axis, type: "value", scale: true },
                  series: [
                    {
                      type: "boxplot",
                      data: state.data.profiles.map((p) => ({
                        value: p.quartiles[field] || [],
                        itemStyle: {
                          color: COLORS[p.cluster] + "33",
                          borderColor: COLORS[p.cluster],
                        },
                      })),
                    },
                  ],
                }}
              />
              <p className="panel-note">
                Giá trị nhỏ nhất, Q1, trung vị, Q3 và lớn nhất trong nhóm đã
                lưu. Khoảng giá trị rộng có thể nén phần trung tâm; hãy đổi chỉ
                tiêu để xem thêm.
              </p>
            </Panel>
          </div>
          <div className="grid-equal section-gap">
            <Panel
              title="Giao thị trường × tài chính"
              eyebrow={`THỊ TRƯỜNG CUỐI NĂM × NĂM TÀI CHÍNH ${year}`}
              action={<Badge tone="amber">Sau kỳ báo cáo</Badge>}
            >
              {matrix.error ? (
                <ErrorState message={matrix.error} />
              ) : !matrix.data ? (
                <Skeleton />
              ) : !matrix.data.available ? (
                <EmptyState
                  title="Chưa có phần giao thị trường trong năm này"
                  message={matrix.data.reason}
                />
              ) : (
                <>
                  <div className="matrix-cells">
                    <span />
                    <span className="matrix-axis">Thị trường A0</span>
                    <span className="matrix-axis">Thị trường A1</span>
                    {[0, 1, 2].map((b) => (
                      <div style={{ display: "contents" }} key={b}>
                        <span className="matrix-axis">Tài chính B{b}</span>
                        {[0, 1].map((a) => {
                          const n =
                            matrix.data!.cells.find(
                              (c) =>
                                c.market_cluster === a &&
                                c.financial_cluster === b,
                            )?.n || 0;
                          return (
                            <button
                              aria-label={`Xem thị trường A${a} × Tài chính B${b}: ${n} cổ phiếu`}
                              className={`matrix-cell ${cell?.market === a && cell.financial === b ? "selected" : ""}`}
                              key={a}
                              onClick={() =>
                                setCell({ market: a, financial: b })
                              }
                            >
                              <strong>{number(n)}</strong>
                              <small>Xem thành viên ↗</small>
                            </button>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                  <p className="panel-note">
                    {number(matrix.data.total)} cổ phiếu giao nhau · thị trường{" "}
                    {matrix.data.date}. {matrix.data.reason}
                  </p>
                </>
              )}
            </Panel>
            <Panel title="Tham chiếu kết hợp C" eyebrow="MỘT THỬ NGHIỆM RIÊNG">
              <div className="panel-body">
                <Badge tone="amber">
                  14 đặc trưng · hai nhóm có trọng số bằng nhau
                </Badge>
                <h3 style={{ fontSize: 22, margin: "20px 0 12px" }}>
                  Khám phá cấu trúc kết hợp
                </h3>
                <p className="muted">
                  Tám đặc trưng thị trường và sáu tỷ số tài chính cốt lõi, chuẩn
                  hóa trên nhóm giao nhau từng năm. K-Means K=3, seed 42. Các
                  cụm nhỏ được giữ nguyên.
                </p>
                <p className="warning-line" style={{ marginTop: 15 }}>
                  Chưa xác minh thời điểm báo cáo sẵn có. Thử nghiệm chỉ có ý
                  nghĩa mô tả, chưa thể dùng cho backtest PIT.
                </p>
                <Link
                  className="button section-gap"
                  href={`/atlas?kind=combined&date=${s.data.datasets.combined.dates.find((d) => d.startsWith(year)) || s.data.datasets.combined.latest.date}`}
                >
                  Mở bản đồ kết hợp ·{" "}
                  {s.data.datasets.combined.dates.find((d) =>
                    d.startsWith(year),
                  )
                    ? year
                    : `gần nhất ${s.data.datasets.combined.latest.date.slice(0, 4)}`}{" "}
                  ↗
                </Link>
              </div>
            </Panel>
          </div>
          <Panel
            className="section-gap"
            title={
              cell
                ? `Thành viên giao nhau · A${cell.market} × B${cell.financial}`
                : "Thành viên tài chính theo năm"
            }
            action={
              cell ? (
                <button className="button small" onClick={() => setCell(null)}>
                  Bỏ lọc phần giao
                </button>
              ) : undefined
            }
          >
            <MembersTable
              kind="financial"
              date={year}
              onSelect={select}
              matrix={cell}
            />
          </Panel>
          <Panel
            className="section-gap"
            title="Tâm cụm · chỉ tiêu tài chính đang chọn"
          >
            <div className="panel-body">
              {state.data.profiles.map((p) => (
                <div className="feature-row" key={p.cluster}>
                  <ClusterBadge kind="financial" id={p.cluster} />
                  <span>Trung bình {metric(p.means[field], field)}</span>
                  <span>Trung vị {metric(p.medians[field], field)}</span>
                </div>
              ))}
            </div>
          </Panel>
        </>
      )}
      {ticker && (
        <StockDrawer
          ticker={ticker}
          kind="financial"
          date={year}
          close={close}
        />
      )}
    </>
  );
}
