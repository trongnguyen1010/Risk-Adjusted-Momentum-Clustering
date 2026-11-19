"use client";

import { useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import { Chart, axis, baseChart } from "@/components/chart";
import type {
  AssessmentFeature,
  AssessmentFeatureId,
  AssessmentHistoryPoint,
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
};

type ChartPoint = {
  value: number;
  status: string;
  usable_from_date: string | null;
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
  return `${label}<br/>Giá trị: ${formatValue(point.value)}<br/>Trạng thái: ${status}<br/>Khả dụng từ: ${point.usable_from_date}`;
}

function featureIsFinancial(feature: AssessmentFeature) {
  return feature.category === "FINANCIAL";
}

export function SingleFeatureChart({ response }: { response: AssessmentResponse }) {
  const [selectedId, setSelectedId] = useState<AssessmentFeatureId>("roe");
  const selectedFeature =
    response.features.find((feature) => feature.feature_id === selectedId) ??
    response.features[0];

  const chartModel = useMemo(() => {
    if (!selectedFeature) return null;

    if (featureIsFinancial(selectedFeature)) {
      const availableHistory = response.history.filter(
        (point) =>
          typeof point.usable_from_date === "string" &&
          point.usable_from_date <= response.as_of &&
          /^\d{4}$/.test(point.period) &&
          Number(point.period) <= Number(response.as_of.slice(0, 4)),
      );
      if (!availableHistory.length) return null;

      const firstYear = Math.min(...availableHistory.map((point) => Number(point.period)));
      const lastYear = Math.max(...availableHistory.map((point) => Number(point.period)));
      const periods = Array.from(
        { length: lastYear - firstYear + 1 },
        (_, index) => String(firstYear + index),
      );
      const selectedHistory = new Map(
        response.history
          .filter((point) => point.feature_id === selectedFeature.feature_id)
          .map((point) => [point.period, point]),
      );
      const data = periods.map((period) => {
        const point = selectedHistory.get(period);
        if (!point || !isPlottableHistoryPoint(point, response.as_of)) return null;
        return {
          value: point.value,
          status: point.status,
          usable_from_date: point.usable_from_date,
        } satisfies ChartPoint;
      });

      if (!data.some((point) => point !== null)) return null;
      return {
        periods,
        data,
        axisLabel: "Năm tài chính (FY)",
        note: "Chỉ vẽ giá trị có status hợp lệ và usable_from_date không sau as_of. Điểm điền trung vị được ghi rõ trong tooltip.",
      };
    }

    const snapshotDate = response.required_price_session;
    const isAtOrBeforeAsOf = snapshotDate <= response.as_of;
    const value =
      selectedFeature.status === "OK" &&
      typeof selectedFeature.value === "number" &&
      Number.isFinite(selectedFeature.value) &&
      selectedFeature.period === snapshotDate &&
      isAtOrBeforeAsOf
        ? {
            value: selectedFeature.value,
            status: selectedFeature.status,
            usable_from_date: selectedFeature.usable_from_date,
          }
        : null;

    if (!value) return null;
    return {
      periods: [snapshotDate],
      data: [value],
      axisLabel: "Snapshot thị trường",
      note: "Response chỉ cung cấp một điểm market tại phiên giá yêu cầu; biểu đồ không nội suy thành chuỗi lịch sử.",
    };
  }, [response, selectedFeature]);

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

  return (
    <section aria-label="Biểu đồ một chỉ số Assessment">
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

      {option && chartModel ? (
        <>
          <Chart
            height={300}
            label={`${response.ticker}: ${FEATURE_LABELS[selectedFeature.feature_id]} theo ${chartModel.axisLabel}`}
            option={option}
          />
          <p className="panel-note">{chartModel.note}</p>
        </>
      ) : (
        <p className="state-box" role="status">
          Không có điểm hợp lệ cho chỉ số này tại as_of {response.as_of}.
        </p>
      )}
    </section>
  );
}
