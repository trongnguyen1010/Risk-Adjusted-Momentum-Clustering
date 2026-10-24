"use client";
import { useEffect, useRef } from "react";
import type { ECharts, EChartsOption } from "echarts";
export function Chart({
  option,
  height = 320,
  onClick,
  label,
}: {
  option: EChartsOption;
  height?: number;
  onClick?: (value: unknown) => void;
  label: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const chart = useRef<ECharts | null>(null);
  const click = useRef(onClick);
  const optionRef = useRef(option);
  useEffect(() => {
    click.current = onClick;
  }, [onClick]);
  useEffect(() => {
    optionRef.current = option;
    chart.current?.setOption(option, { notMerge: true });
  }, [option]);
  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | null = null;
    import("echarts").then((ec) => {
      if (disposed || !host.current) return;
      chart.current = ec.init(host.current, undefined, { renderer: "canvas" });
      chart.current.setOption(optionRef.current);
      chart.current.on("click", (params) => click.current?.(params));
      observer = new ResizeObserver(() => chart.current?.resize());
      observer.observe(host.current);
    });
    return () => {
      disposed = true;
      observer?.disconnect();
      chart.current?.dispose();
      chart.current = null;
    };
  }, []);
  return (
    <div
      ref={host}
      className="chart"
      style={{ height }}
      role="img"
      aria-label={label}
    />
  );
}
export const baseChart = {
  backgroundColor: "transparent",
  textStyle: { fontFamily: "Inter, sans-serif", color: "#94a3b8" },
  animationDuration: 350,
  grid: { left: 56, right: 24, top: 30, bottom: 42 },
  tooltip: {
    backgroundColor: "#152235",
    borderColor: "#2a3b51",
    textStyle: { color: "#f1f5f9", fontSize: 12 },
    confine: true,
  },
};
export const axis = {
  axisLine: { lineStyle: { color: "#29364a" } },
  axisLabel: { color: "#718198", fontSize: 10 },
  splitLine: { lineStyle: { color: "#1c293b", type: "dashed" as const } },
  axisTick: { show: false },
};
