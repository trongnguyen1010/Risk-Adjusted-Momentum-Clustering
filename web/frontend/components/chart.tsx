"use client";
import { useEffect, useRef, useState } from "react";
import type { ECharts, EChartsOption } from "echarts";
// Chart option constants are written for the dark theme; at render time these
// colours are swapped for the current theme's tokens (see globals.css).
const THEMED: Record<string, string> = {
  "#b8c2d4": "--text-2",
  "#aab6ca": "--muted",
  "#29364a": "--line-strong",
  "#1c293b": "--line",
  "#152235": "--tooltip-bg",
  "#2a3b51": "--tooltip-bg",
  "#ff5500": "--accent",
};
function paint<T>(value: T, vars: Record<string, string>): T {
  if (typeof value === "string") return (vars[value] ?? value) as T;
  if (Array.isArray(value)) return value.map((v) => paint(v, vars)) as T;
  if (value && typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype)
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, paint(v, vars)])) as T;
  return value;
}
function themeVars() {
  const css = getComputedStyle(document.documentElement);
  return Object.fromEntries(Object.entries(THEMED).map(([hex, token]) => [hex, css.getPropertyValue(token).trim() || hex]));
}
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
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const chart = useRef<ECharts | null>(null);
  const click = useRef(onClick);
  const optionRef = useRef(option);
  useEffect(() => {
    click.current = onClick;
  }, [onClick]);
  useEffect(() => {
    optionRef.current = option;
    chart.current?.setOption(
      {
        ...paint(option, themeVars()),
        animation: !window.matchMedia("(prefers-reduced-motion: reduce)")
          .matches,
      },
      { notMerge: true },
    );
  }, [option]);
  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | null = null;
    let cleanup = () => {};
    import("echarts")
      .then((ec) => {
        if (disposed || !host.current) return;
        chart.current = ec.init(host.current, undefined, {
          renderer: "canvas",
        });
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
        chart.current.setOption({
          ...paint(optionRef.current, themeVars()),
          animation: !reduced.matches,
        });
        const repaint = () =>
          chart.current?.setOption({ ...paint(optionRef.current, themeVars()), animation: false }, { notMerge: true });
        window.addEventListener("delta:theme", repaint);
        cleanup = () => window.removeEventListener("delta:theme", repaint);
        setReady(true);
        chart.current.on("click", (params) => click.current?.(params));
        observer = new ResizeObserver(() => chart.current?.resize());
        observer.observe(host.current);
      })
      .catch(() => {
        if (!disposed) setFailed(true);
      });
    return () => {
      disposed = true;
      cleanup();
      observer?.disconnect();
      chart.current?.dispose();
      chart.current = null;
    };
  }, []);
  return (
    <div className="chart-frame" style={{ height }}>
      <div
        ref={host}
        className="chart"
        style={{ height }}
        role="img"
        aria-label={label}
        aria-busy={!ready}
      />
      {!ready && (
        <div className="chart-loading" role="status">
          {failed
            ? "Không dựng được biểu đồ. Xem bảng dữ liệu thay thế hoặc tải lại trang."
            : "Đang dựng biểu đồ từ dữ liệu đã lưu…"}
        </div>
      )}
    </div>
  );
}
export const baseChart = {
  backgroundColor: "transparent",
  textStyle: {
    fontFamily: "Inter, sans-serif",
    color: "#b8c2d4",
    fontSize: 13,
  },
  animationDuration: 160,
  animationDurationUpdate: 160,
  grid: { left: 20, right: 28, top: 38, bottom: 48, containLabel: true },
  tooltip: {
    backgroundColor: "#152235",
    borderColor: "#2a3b51",
    textStyle: { color: "#f1f5f9", fontSize: 13, fontFamily: "JetBrains Mono, monospace" },
    borderRadius: 2,
    confine: true,
  },
};
export const axis = {
  axisLine: { lineStyle: { color: "#29364a" } },
  axisLabel: { color: "#aab6ca", fontSize: 12, fontFamily: "JetBrains Mono, monospace", hideOverlap: true },
  nameTextStyle: { color: "#b8c2d4", fontSize: 12 },
  splitNumber: 3,
  splitLine: { lineStyle: { color: "#1c293b", type: "dashed" as const } },
  axisTick: { show: false },
};
