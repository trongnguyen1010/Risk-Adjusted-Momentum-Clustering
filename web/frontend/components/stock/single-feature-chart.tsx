"use client";

import { useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import { Chart, axis, baseChart } from "@/components/chart";
import type {
  AssessmentFeature,
  AssessmentFeatureId,
  AssessmentHistoryPoint,
  AssessmentQuery,
  AssessmentResponse,
} from "@/lib/types";

const FEATURE_LABELS: Record<AssessmentFeatureId, string> = {
  roe: "ROE",
  roa: "ROA",
  gross_margin: "Biên lợi nhuận gộp",
  net_margin: "Biên lợi nhuận ròng",
  debt_to_equity: "Nợ trên vốn chủ sở hữu",
  current_ratio: "Hệ số thanh toán hiện hành",
  asset_turnover: "Vòng quay tài sản",
  revenue_growth: "Tăng trưởng doanh thu",
  cfo_to_ni: "CFO trên lợi nhuận ròng",
  mom_21: "Momentum 21 phiên",
  mom_63: "Momentum 63 phiên",
  mom_126: "Momentum 126 phiên",
  mom_252: "Momentum 252 phiên",
  vol_63: "Biến động 63 phiên",
  mdd_126: "Drawdown tối đa 126 phiên",
  beta_126: "Beta 126 phiên",
  liquidity_21: "Thanh khoản 21 phiên",
  downside_vol_63: "Biến động giảm 63 phiên",
};

const HISTORY_STATUS_LABELS: Record<string, string> = {
  OK: "Quan sát hợp lệ",
  IMPUTED_MEDIAN: "Được điền bằng trung vị",
  MISSING_INPUT: "Thiếu dữ liệu đầu vào",
  NEGATIVE_EARNINGS: "Lợi nhuận âm; không có giá trị hợp lệ",
  NEGATIVE_EQUITY: "Vốn chủ sở hữu âm; không có giá trị hợp lệ",
};

type ChartPoint = {
  value: number;
  status: string;
  usable_from_date: string | null;
  source: string | null;
};

function isPlottableHistoryPoint(
  point: AssessmentHistoryPoint,
  asOf: string,
): point is AssessmentHistoryPoint & { value: number; usable_from_date: string } {
  return (
    (point.status === "OK" || point.status === "IMPUTED_MEDIAN") &&
    typeof point.value === "number" &&
    Number.isFinite(point.value) &&
    typeof point.usable_from_date === "string" &&
    point.usable_from_date <= asOf
  );
}

function formatValue(value: number) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 4 }).format(value);
}

function tooltipContent(params: unknown) {
  const first = (Array.isArray(params) ? params[0] : params) as
    | { axisValueLabel?: unknown; data?: unknown }
    | undefined;
  const label = typeof first?.axisValueLabel === "string" ? first.axisValueLabel : "Kỳ";
  const data = first?.data;

  if (!data || typeof data !== "object" || !("value" in data)) return label;
  const point = data as ChartPoint;
  const status = HISTORY_STATUS_LABELS[point.status] ?? point.status;
  return `${label}<br/>Giá trị: ${formatValue(point.value)}<br/>Trạng thái: ${status}<br/>Khả dụng từ: ${point.usable_from_date ?? "Chưa có"}<br/>Nguồn: ${point.source ?? "Không có trong response"}`;
}

function featureIsFinancial(feature: AssessmentFeature) {
  return feature.category === "FINANCIAL";
}

export interface SingleFeatureChartProps {
  response: AssessmentResponse;
  lookbackYears?: 5 | 10;
  onLookbackChange?: (query: AssessmentQuery) => void;
}

export function SingleFeatureChart({
  response,
  lookbackYears: controlledLookbackYears,
  onLookbackChange,
}: SingleFeatureChartProps) {
  const [localLookbackYears, setLocalLookbackYears] = useState<5 | 10>(10);
  const lookbackYears = controlledLookbackYears ?? localLookbackYears;
  const [selectedId, setSelectedId] = useState<AssessmentFeatureId>("roe");
  const selectedFeature =
    response.features.find((feature) => feature.feature_id === selectedId) ??
    response.features[0];

  const changeLookback = (value: string) => {
    const next = Number(value);
    if (next !== 5 && next !== 10) return;
    const query: AssessmentQuery = { lookback_years: next };
    if (controlledLookbackYears === undefined) setLocalLookbackYears(next);
    onLookbackChange?.(query);
  };

  const chartModel = useMemo(() => {
    if (!selectedFeature) return null;

    if (featureIsFinancial(selectedFeature)) {
      const endYear = Number(response.as_of.slice(0, 4));
      const startYear = endYear - lookbackYears + 1;
      const periods = Array.from({ length: lookbackYears }, (_, index) =>
        String(startYear + index),
      );
      const rowsInWindow = response.history.filter((point) => {
        const year = Number(point.period);
        return (
          point.feature_id === selectedFeature.feature_id &&
          /^\d{4}$/.test(point.period) &&
          year >= startYear &&
          year <= endYear
        );
      });
      const rowsAvailableAtAsOf = rowsInWindow.filter(
        (point) =>
          typeof point.usable_from_date === "string" &&
          point.usable_from_date <= response.as_of,
      );
      const selectedHistory = new Map(
        rowsAvailableAtAsOf.map((point) => [point.period, point]),
      );
      const data = periods.map((period) => {
        const point = selectedHistory.get(period);
        if (!point || !isPlottableHistoryPoint(point, response.as_of)) return null;
        return {
          value: point.value,
          status: point.status,
          usable_from_date: point.usable_from_date,
          source: point.source,
        } satisfies ChartPoint;
      });

      const plottedCount = data.filter((point) => point !== null).length;
      const imputedCount = data.filter(
        (point) => point?.status === "IMPUTED_MEDIAN",
      ).length;
      return {
        periods,
        data,
        axisLabel: "Năm tài chính (FY)",
        coverage: {
          records: rowsAvailableAtAsOf.length,
          plotted: plottedCount,
          imputed: imputedCount,
          expected: lookbackYears,
        },
        details: rowsAvailableAtAsOf.sort(
          (left, right) => Number(left.period) - Number(right.period),
        ),
        note: "Khoảng trống trên trục FY biểu thị kỳ không có điểm hợp lệ; không nội suy hoặc tạo giá trị.",
      };
    }

    const snapshotDate = response.required_price_session;
    const isAtOrBeforeAsOf = snapshotDate <= response.as_of;
    const snapshotMatchesResponse = selectedFeature.period === snapshotDate;
    const value =
      selectedFeature.status === "OK" &&
      typeof selectedFeature.value === "number" &&
      Number.isFinite(selectedFeature.value) &&
      snapshotMatchesResponse &&
      isAtOrBeforeAsOf
        ? {
            value: selectedFeature.value,
            status: selectedFeature.status,
            usable_from_date: null,
            source: selectedFeature.evidence_ref,
          }
        : null;

    const snapshotInResponse = snapshotMatchesResponse && isAtOrBeforeAsOf;
    return {
      periods: [snapshotDate],
      data: [value],
      axisLabel: "Snapshot thị trường",
      coverage: {
        records: snapshotInResponse ? 1 : 0,
        plotted: value ? 1 : 0,
        imputed: 0,
        expected: 1,
      },
      details: snapshotInResponse
        ? [
            {
              period: snapshotDate,
              value: value?.value ?? null,
              status: selectedFeature.status,
              usable_from_date: null,
              source: selectedFeature.evidence_ref ?? "Không có trong response",
            },
          ]
        : [],
      note: "Response chỉ có một snapshot market tại phiên giá yêu cầu; coverage không đại diện cho chuỗi lịch sử.",
    };
  }, [response, selectedFeature, lookbackYears]);

  if (!selectedFeature) {
    return (
      <section className="state-box" role="status">
        <h3>Chưa có danh sách chỉ số</h3>
        <p>Assessment response hiện không có feature để vẽ.</p>
      </section>
    );
  }

  const option: EChartsOption | null = chartModel
    ? {
        ...baseChart,
        tooltip: {
          ...baseChart.tooltip,
          trigger: "axis",
          formatter: tooltipContent,
        },
        xAxis: {
          ...axis,
          type: "category",
          name: chartModel.axisLabel,
          data: chartModel.periods,
          boundaryGap: false,
        },
        yAxis: {
          ...axis,
          type: "value",
          name: selectedFeature.unit,
          scale: true,
        },
        series: [
          {
            type: "line",
            name: FEATURE_LABELS[selectedFeature.feature_id],
            showSymbol: true,
            connectNulls: false,
            data: chartModel.data,
            lineStyle: { color: "#67d5bf", width: 2 },
            itemStyle: { color: "#67d5bf" },
          },
        ],
      }
    : null;

  const asOfYear = Number(response.as_of.slice(0, 4));
  const windowStartYear = asOfYear - lookbackYears + 1;

  return (
    <section aria-label="Biểu đồ một chỉ số Assessment">
      <div className="filter-row">
        <label htmlFor="assessment-feature-selector">Chỉ số cần xem</label>
        <select
          id="assessment-feature-selector"
          onChange={(event) => setSelectedId(event.target.value as AssessmentFeatureId)}
          value={selectedFeature.feature_id}
        >
          {response.features.map((feature) => (
            <option key={feature.feature_id} value={feature.feature_id}>
              {FEATURE_LABELS[feature.feature_id]}
            </option>
          ))}
        </select>

        <label htmlFor="assessment-lookback-selector">Khoảng lịch sử</label>
        <select
          id="assessment-lookback-selector"
          onChange={(event) => changeLookback(event.target.value)}
          value={lookbackYears}
        >
          <option value={10}>10 năm</option>
          <option value={5}>5 năm</option>
        </select>
      </div>

      {option && chartModel?.data.some((point) => point !== null) ? (
        <Chart
          height={300}
          label={`${response.ticker}: ${FEATURE_LABELS[selectedFeature.feature_id]} theo ${chartModel.axisLabel}`}
          option={option}
        />
      ) : (
        <p className="state-box" role="status">
          Không có điểm hợp lệ cho chỉ số này tại as_of {response.as_of}.
        </p>
      )}

      {chartModel && (
        <>
          <p aria-live="polite" className="panel-note" role="status">
            {featureIsFinancial(selectedFeature)
              ? `Cửa sổ FY ${windowStartYear}–${asOfYear}: ${chartModel.coverage.records}/${lookbackYears} kỳ có bản ghi khả dụng, ${chartModel.coverage.plotted} điểm được vẽ, ${chartModel.coverage.imputed} điểm impute.`
              : `Snapshot tại ${response.required_price_session}: ${chartModel.coverage.plotted}/${chartModel.coverage.expected} điểm được vẽ.`}
            {" "}
            {chartModel.note}
          </p>

          {chartModel.details.length > 0 && (
            <div className="table-wrap">
              <table>
                <caption>
                  Dữ liệu thực và provenance cho {FEATURE_LABELS[selectedFeature.feature_id]}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Kỳ / ngày</th>
                    <th scope="col">Giá trị</th>
                    <th scope="col">Trạng thái</th>
                    <th scope="col">Khả dụng từ</th>
                    <th scope="col">Nguồn</th>
                  </tr>
                </thead>
                <tbody>
                  {chartModel.details.map((point) => (
                    <tr key={point.period}>
                      <td>{point.period}</td>
                      <td>{point.value == null ? "—" : formatValue(point.value)}</td>
                      <td>{HISTORY_STATUS_LABELS[point.status] ?? point.status}</td>
                      <td>{point.usable_from_date ?? "Không có trong response"}</td>
                      <td>{point.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}
