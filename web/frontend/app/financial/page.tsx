"use client";
import { useCallback } from "react";
import Link from "next/link";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { number, clusterColor, metric } from "@/lib/format";
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
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { ModelVersion, PreviewNote } from "@/components/model-version";
import { IndicatorCoverage } from "@/components/indicator-reference";
const tabs = [
  ["distribution", "Phân bố"],
  ["compare", "Đối chiếu A/B/C"],
  ["coverage", "Độ phủ chỉ số"],
] as const;
export default function Financial() {
  const s = useSelection("financial");
  const year =
    s.params.get("year") || s.data?.datasets.financial.latest.date || "2025";
  const tab = tabs.some(([id]) => id === s.params.get("tab"))
    ? s.params.get("tab")!
    : "distribution";
  const field = s.params.get("field") || "net_margin";
  const a = s.params.get("matrix_a"),
    b = s.params.get("matrix_b");
  const cell =
    a !== null && b !== null
      ? { market: Number(a), financial: Number(b) }
      : null;
  const ticker = s.params.get("ticker");
  const close = useCallback(() => {
    const p = new URLSearchParams(window.location.search);
    p.delete("ticker");
    window.history.pushState(null, "", `${window.location.pathname}?${p}`);
  }, []);
  const selectedVersion = s.dataset?.version;
  const marketVersion = s.data
    ? [s.data.datasets.market, ...(s.data.variants?.market || [])].find(
        (d) => d.version === selectedVersion,
      )?.version || s.data.datasets.market.version
    : undefined;
  const combinedVersion = s.data
    ? [s.data.datasets.combined, ...(s.data.variants?.combined || [])].find(
        (d) => d.version === selectedVersion,
      )?.version || s.data.datasets.combined.version
    : undefined;
  const state = useApi<SnapshotData>(
    tab !== "coverage" && s.data
      ? url("snapshots/financial", {
          date: year,
          version: selectedVersion,
          include_points: 0,
        })
      : null,
  );
  const matrix = useApi<Matrix>(
    tab === "compare" && s.data
      ? url(`matrix/${year}`, {
          version: selectedVersion,
          market_version: marketVersion,
        })
      : null,
  );
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;
  if (!s.data) return <Skeleton height={600} />;
  const marketLabels =
    matrix.data?.market_labels ||
    [...new Set(matrix.data?.cells.map((c) => c.market_cluster) || [])].sort(
      (a, b) => a - b,
    );
  const financialLabels =
    matrix.data?.financial_labels ||
    [...new Set(matrix.data?.cells.map((c) => c.financial_cluster) || [])].sort(
      (a, b) => a - b,
    );
  const combinedDate = s.data.datasets.combined.dates.find((d) =>
    d.startsWith(year),
  );
  return (
    <>
      <PageHeading
        eyebrow="FINANCIAL / NỀN TẢNG DOANH NGHIỆP"
        title="Góc nhìn tài chính"
        description="Xem một phân bố, đối chiếu nhóm và kiểm tra độ phủ theo từng năm."
        action={
          <select
            aria-label="Năm tài chính"
            value={year}
            onChange={(e) =>
              s.set({
                year: e.target.value,
                matrix_a: null,
                matrix_b: null,
                page: null,
                ticker: null,
              })
            }
          >
            {s.data.datasets.financial.dates.map((y) => (
              <option key={y} value={y}>
                FY{y}
              </option>
            ))}
          </select>
        }
      />
      <Badge tone="amber">
        {number(s.data.metadata.financial_publication_rows)} /{" "}
        {number(s.data.metadata.financial_rows)} rows có mốc công bố
      </Badge>
      <ScopeNote kind="financial" />
      {s.dataset && (
        <ModelVersion
          options={s.options}
          value={s.dataset.version}
          onChange={(version) =>
            s.set({
              version,
              matrix_a: null,
              matrix_b: null,
              cluster: null,
              page: null,
            })
          }
        />
      )}
      <PreviewNote dataset={s.dataset} />
      <WorkspaceTabs
        tabs={tabs}
        scope="financial"
        value={tab}
        onChange={(tab) => s.set({ tab })}
      />
      <div
        role="tabpanel"
        id="financial-panel"
        aria-labelledby={`financial-${tab}`}
      >
        {tab === "coverage" ? (
          <IndicatorCoverage />
        ) : state.error ? (
          <ErrorState message={state.error} retry={state.retry} />
        ) : !state.data ? (
          <Skeleton />
        ) : (
          <>
            {tab === "distribution" && (
              <div className="grid-two">
                <Panel
                  title="Phân bố một chỉ tiêu"
                  eyebrow={`FY${year} · MIN / Q1 / MEDIAN / Q3 / MAX ĐÃ LƯU`}
                  action={
                    <select
                      aria-label="Chỉ tiêu tài chính cần xem phân bố"
                      value={field}
                      onChange={(e) => s.set({ field: e.target.value })}
                    >
                      {s.data.datasets.financial.features.map((f) => (
                        <option key={f} value={f}>
                          {s.data?.metadata.definitions[f]?.label || f}
                        </option>
                      ))}
                    </select>
                  }
                >
                  {!s.data.datasets.financial.features.includes(field) ? (
                    <ErrorState
                      message="Feature trong URL không có trong model này."
                      retry={() => s.set({ field: null })}
                    />
                  ) : (
                    <Chart
                      height={360}
                      label={`Phân bố ${field} theo cụm; cùng thông tin trong bảng bên cạnh.`}
                      option={{
                        ...baseChart,
                        tooltip: {
                          ...baseChart.tooltip,
                          renderMode: "richText",
                        },
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
                                color:
                                  clusterColor(
                                    p.cluster,
                                    Object.keys(state.data!.snapshot.sizes).map(
                                      Number,
                                    ),
                                  ) + "33",
                                borderColor: clusterColor(
                                  p.cluster,
                                  Object.keys(state.data!.snapshot.sizes).map(
                                    Number,
                                  ),
                                ),
                              },
                            })),
                          },
                        ],
                      }}
                    />
                  )}
                  <p className="panel-note">
                    Một feature trên một thang đơn vị gốc. Hộp Q1–median–Q3, hai
                    đầu là min/max, giữ tails; không cắt ngọn hoặc đổi input
                    model.
                  </p>
                </Panel>
                <Panel
                  title="Đối chiếu nhóm"
                  eyebrow={`FY${year} · ${number(state.data.snapshot.n)} MÃ`}
                >
                  <div className="data-table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Nhóm / số mã</th>
                          <th>Median</th>
                          <th>Q1 – Q3</th>
                        </tr>
                      </thead>
                      <tbody>
                        {state.data.profiles.map((p) => (
                          <tr key={p.cluster}>
                            <th>
                              <ClusterBadge
                                kind="financial"
                                id={p.cluster}
                                labels={Object.keys(
                                  state.data!.snapshot.sizes,
                                ).map(Number)}
                              />
                              <span className="block">{number(p.size)} mã</span>
                            </th>
                            <td>{metric(p.medians[field], field)}</td>
                            <td>
                              {metric(p.quartiles[field]?.[1], field)} —{" "}
                              {metric(p.quartiles[field]?.[3], field)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="panel-note">
                    Chỉ gồm doanh nghiệp đủ 10 năm báo cáo. Nhóm không phải xếp hạng đầu tư.
                  </p>
                  <Link
                    className="button ghost"
                    href={`/atlas?kind=financial&date=${year}&tab=profiles`}
                  >
                    Mở hồ sơ đầy đủ ↗
                  </Link>
                </Panel>
              </div>
            )}
            {tab === "compare" && (
              <>
                <div className="grid-two">
                  <Panel
                    title="Thị trường A × tài chính B"
                    eyebrow={`MARKET CUỐI NĂM × FY${year} · EX-POST, CHƯA PIT`}
                  >
                    {matrix.error ? (
                      <ErrorState message={matrix.error} retry={matrix.retry} />
                    ) : !matrix.data ? (
                      <Skeleton />
                    ) : !matrix.data.available ? (
                      <EmptyState
                        title="Không có mô hình thị trường cho FY này"
                        message={matrix.data.reason}
                      />
                    ) : (
                      <>
                        <div className="data-table-wrap">
                          <table className="data-table matrix-table">
                            <caption>
                              {number(matrix.data.total)} mã có cả hai mô hình ·
                              thị trường {matrix.data.date}. Bấm một ô để xem thành
                              viên.
                            </caption>
                            <thead>
                              <tr>
                                <th>B / A</th>
                                {marketLabels.map((label) => (
                                  <th key={label}>A{label}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {financialLabels.map((label) => (
                                <tr key={label}>
                                  <th>B{label}</th>
                                  {marketLabels.map((market) => {
                                    const n =
                                      matrix.data!.cells.find(
                                        (c) =>
                                          c.market_cluster === market &&
                                          c.financial_cluster === label,
                                      )?.n || 0;
                                    return (
                                      <td key={market}>
                                        <button
                                          aria-label={`Xem A${market} × B${label}: ${n} cổ phiếu`}
                                          aria-pressed={
                                            cell?.market === market &&
                                            cell?.financial === label
                                          }
                                          className="matrix-cell"
                                          onClick={() =>
                                            s.set({
                                              matrix_a: String(market),
                                              matrix_b: String(label),
                                              cluster: null,
                                              page: null,
                                            })
                                          }
                                        >
                                          <strong>{number(n)}</strong>
                                          <small>Xem thành viên ↗</small>
                                        </button>
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <p className="panel-note">{matrix.data.reason}</p>
                      </>
                    )}
                  </Panel>
                  <Panel
                    title="C · mô hình kết hợp độc lập"
                    eyebrow="KHÔNG PHẢI NHÃN GỘP A / B"
                  >
                    <div className="panel-body">
                      <p>
                        C kết hợp tám đặc trưng thị trường và sáu tỷ số tài chính
                        trên các mã có đủ cả hai loại dữ liệu mỗi năm.
                      </p>
                      {combinedDate ? (
                        <>
                          <p className="warning-line section-gap">
                            Kỳ {combinedDate}. Giữ tiny clusters và các evidence
                            bất lợi; mô hình chỉ có ý nghĩa mô tả.
                          </p>
                          <Link
                            className="button section-gap"
                            href={`/atlas?kind=combined&date=${combinedDate}&version=${encodeURIComponent(combinedVersion || "")}`}
                          >
                            Xem nhóm C đúng năm {year} ↗
                          </Link>
                        </>
                      ) : (
                        <EmptyState
                          title={`Không có C năm ${year}`}
                          message="C chỉ có artifact trong các năm 2019–2025. Không thay bằng năm khác."
                        />
                      )}
                    </div>
                  </Panel>
                </div>
                {cell && matrix.data?.available && (
                  <Panel
                    className="section-gap"
                    title={`Thành viên A${cell.market} × B${cell.financial}`}
                    action={
                      <button
                        className="button small"
                        onClick={() =>
                          s.set({ matrix_a: null, matrix_b: null, page: null })
                        }
                      >
                        Bỏ chọn ô
                      </button>
                    }
                  >
                    <MembersTable
                      key={`${year}:${a}:${b}`}
                      kind="financial"
                      version={selectedVersion}
                      matrixMarketVersion={marketVersion}
                      date={year}
                      matrix={cell}
                      onSelect={(ticker) => s.set({ ticker })}
                    />
                  </Panel>
                )}
              </>
            )}
          </>
        )}
      </div>
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
