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
  focus = "",
  labelled = [],
  centroids = false,
  dim = false,
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
  /** Ticker drawn enlarged with an accent ring (inspector selection). */
  focus?: string;
  /** Tickers drawn as labelled chips; when non-empty every other point is dimmed ("Mã lớn" mode). */
  labelled?: string[];
  /** Draw each cluster's name at the median position of its members (map mode). */
  centroids?: boolean;
  /** Fade every point except the focused stock (its own cluster stays a little brighter). */
  dim?: boolean;
}) {
  const focusCluster = dim && focus ? data.points.find((p) => p.ticker === focus)?.cluster : undefined;
  const transform = (v: number | null) =>
    v === null ? null : symlog ? Math.sign(v) * Math.log1p(Math.abs(v)) : v;
  const labelSet = new Set(labelled);
  const clusterIds = Object.keys(data.snapshot.sizes).map(Number);
  const usable = data.points.filter((p) => p.features[x] != null && p.features[y] != null);
  const mid = (vals: number[]) => {
    const v = [...vals].sort((a, b) => a - b);
    return v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2;
  };
  const point = (p: (typeof usable)[number]) => ({
    ticker: p.ticker,
    cluster: p.cluster,
    illiquid: p.liquidity === "ILLIQUID",
    value: [transform(p.features[x]), transform(p.features[y])],
    raw: [p.features[x], p.features[y]],
  });
  const chip = { fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#f1f5f9", backgroundColor: "#152235", padding: [2, 5] };
  const extras = mini
    ? []
    : [
        ...(labelSet.size
          ? [{
              type: "scatter" as const,
              id: "big",
              name: "Mã lớn",
              z: 5,
              symbolSize: 9,
              labelLayout: { hideOverlap: true },
              label: { show: true, position: "right" as const, distance: 6, formatter: (q: { data: { ticker: string } }) => q.data.ticker, ...chip },
              itemStyle: { borderColor: "#b8c2d4", borderWidth: 1 },
              data: usable.filter((p) => labelSet.has(p.ticker)).map((p) => ({ ...point(p), itemStyle: { color: clusterColor(p.cluster, clusterIds) } })),
            }]
          : []),
        ...(centroids
          ? [{
              type: "scatter" as const,
              id: "centroids",
              name: "Tâm nhóm",
              z: 6,
              silent: true,
              symbol: "rect",
              symbolSize: 8,
              label: {
                show: true,
                position: "top" as const,
                distance: 6,
                formatter: (q: { data: { cluster: number } }) => `${FAMILY[kind].letter}${q.data.cluster}`,
                ...chip,
                fontSize: 13,
                fontWeight: 700,
                padding: [3, 7],
              },
              data: clusterIds.map((c) => {
                const members = usable.filter((p) => p.cluster === c && p.liquidity !== "ILLIQUID");
                const pts = (members.length ? members : usable.filter((p) => p.cluster === c)).map(point);
                return { cluster: c, ticker: "", value: [mid(pts.map((q) => q.value[0] as number)), mid(pts.map((q) => q.value[1] as number))], itemStyle: { color: clusterColor(c, clusterIds), borderColor: "#eef1f6", borderWidth: 1 } };
              }),
            }]
          : []),
        ...(focus && usable.some((p) => p.ticker === focus)
          ? [{
              type: "effectScatter" as const,
              id: "focus",
              name: "Đang chọn",
              z: 7,
              symbolSize: 12,
              rippleEffect: { brushType: "stroke" as const, scale: 3.2, period: 2.4, number: 2 },
              itemStyle: { color: "#ff5500" },
              label: { show: true, position: "right" as const, distance: 8, formatter: (q: { data: { ticker: string } }) => q.data.ticker, ...chip, fontWeight: 700 },
              data: usable.filter((p) => p.ticker === focus).map(point),
            }]
          : []),
      ];
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
        animationDurationUpdate: 550,
        animationEasingUpdate: "cubicOut",
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
            id: `cluster-${cluster}`,
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
                symbolSize: p.ticker === focus ? 16 : mini ? 4 : p.liquidity === "ILLIQUID" ? 5 : 7,
                value: [transform(p.features[x]), transform(p.features[y])],
                raw: [p.features[x], p.features[y]],
                itemStyle: {
                  ...(p.ticker === focus ? { borderColor: "#ff5500" /* themed: --accent */, borderWidth: 3 } : {}),
                  opacity: p.ticker === focus ? 1 :
                    focusCluster !== undefined ? (cluster === focusCluster ? 0.3 : 0.1) :
                    labelSet.size ? 0.12 :
                    (selected !== "" && Number(selected) !== cluster) ||
                    (query &&
                      !p.ticker.toLowerCase().includes(query.toLowerCase()))
                      ? 0.08
                      : p.liquidity === "ILLIQUID"
                        ? 0.3
                        : 0.78,
                },
              })),
          }))
          .concat(extras as never[]),
      }}
    />
  );
}
