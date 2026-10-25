"use client";
import { Chart, baseChart, axis } from "./chart";
import { clusterColor, FAMILY, metric } from "@/lib/format";
import type { SnapshotData, Kind } from "@/lib/types";
export function Scatter({
  data,
  x,
  y,
  kind,
  onSelect,
  height = 420,
  selected = "",
  query = "",
  mini = false,
  symlog = false,
  map = false,
  names = {},
}: {
  data: SnapshotData;
  x: string;
  y: string;
  kind: Kind;
  onSelect?: (t: string) => void;
  height?: number;
  selected?: string;
  query?: string;
  mini?: boolean;
  symlog?: boolean;
  /** Model map: _map_x/_map_y are PCA axes without units. */
  map?: boolean;
  names?: Record<number, string | null | undefined>;
}) {
  const transform = (v: number | null) =>
    v === null ? null : symlog ? Math.sign(v) * Math.log1p(Math.abs(v)) : v;
  const axisName = (field: string) =>
    map
      ? field === "_map_x"
        ? "Trục chính 1"
        : "Trục chính 2"
      : `${data.definitions[field]?.label || field} (${data.definitions[field]?.unit === "percent" ? "%" : data.definitions[field]?.unit === "vnd" ? "VND" : "lần"})`;
  return (
    <Chart
      height={height}
      label={`${FAMILY[kind].label} scatter: ${x} versus ${y}. Mỗi điểm tương ứng một cổ phiếu.`}
      onClick={(p) => {
        const value = (p as { data?: { ticker?: string } }).data?.ticker;
        if (value) onSelect?.(value);
      }}
      option={{
        ...baseChart,
        grid: mini
          ? { left: 20, right: 20, top: 20, bottom: 20 }
          : baseChart.grid,
        tooltip: {
          ...baseChart.tooltip,
          trigger: "item",
          renderMode: "richText",
          formatter: (p: unknown) => {
            const d = (
              p as {
                data: {
                  ticker: string;
                  value: number[];
                  raw: number[];
                  cluster: number;
                  illiquid?: boolean;
                };
              }
            ).data;
            if (map)
              return `${d.ticker} · ${FAMILY[kind].letter}${d.cluster}${names[d.cluster] ? ` · ${names[d.cluster]}` : ""}${d.illiquid ? "\nKém thanh khoản: được xếp vào nhóm gần nhất" : ""}`;
            return `${d.ticker} · ${FAMILY[kind].letter}${d.cluster} · ${data.snapshot.date}\n${data.definitions[x]?.label || x}: ${metric(d.raw[0], x)}\n${data.definitions[y]?.label || y}: ${metric(d.raw[1], y)}`;
          },
        },
        xAxis: {
          ...axis,
          type: "value",
          name: mini ? undefined : symlog ? `log1p có dấu · ${x}` : axisName(x),
          axisLabel: {
            ...axis.axisLabel,
            ...(!symlog && !map ? { formatter: (v: number) => metric(v, x) } : {}),
          },
          scale: true,
          show: !mini,
          nameLocation: "middle",
          nameGap: 28,
        },
        yAxis: {
          ...axis,
          type: "value",
          name: mini ? undefined : symlog ? `log1p có dấu · ${y}` : axisName(y),
          axisLabel: {
            ...axis.axisLabel,
            ...(!symlog && !map ? { formatter: (v: number) => metric(v, y) } : {}),
          },
          scale: true,
          show: !mini,
          nameTextStyle: {
            fontSize: 12,
            align: "left",
            width: 200,
            overflow: "truncate",
          },
        },
        dataZoom: mini
          ? []
          : [
              { type: "inside", xAxisIndex: 0, filterMode: "none" },
              { type: "inside", yAxisIndex: 0, filterMode: "none" },
            ],
        series: Object.keys(data.snapshot.sizes)
          .map(Number)
          .sort((a, b) => a - b)
          .map((cluster) => ({
            type: "scatter" as const,
            name: `${FAMILY[kind].letter}${cluster}${names[cluster] ? ` · ${names[cluster]}` : ""}`,
            symbolSize: mini ? 4 : 7,
            emphasis: {
              scale: 1.7,
              itemStyle: { borderColor: "#fff", borderWidth: 1 },
            },
            itemStyle: {
              color: clusterColor(
                cluster,
                Object.keys(data.snapshot.sizes).map(Number),
              ),
              opacity: 0.72,
            },
            data: data.points
              .filter(
                (p) =>
                  p.cluster === cluster &&
                  p.features[x] != null &&
                  p.features[y] != null,
              )
              .map((p) => ({
                ticker: p.ticker,
                cluster,
                illiquid: p.liquidity === "ILLIQUID",
                symbolSize: mini ? 4 : p.liquidity === "ILLIQUID" ? 5 : 7,
                value: [transform(p.features[x]), transform(p.features[y])],
                raw: [p.features[x], p.features[y]],
                itemStyle: {
                  opacity:
                    (selected !== "" && Number(selected) !== cluster) ||
                    (query &&
                      !p.ticker.toLowerCase().includes(query.toLowerCase()))
                      ? 0.08
                      : p.liquidity === "ILLIQUID"
                        ? 0.3
                        : 0.78,
                },
              })),
          })),
      }}
    />
  );
}
