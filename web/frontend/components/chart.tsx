"use client";
import { useEffect, useRef, useState } from "react";
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
        ...option,
        animation: !window.matchMedia("(prefers-reduced-motion: reduce)")
          .matches,
      },
      { notMerge: true },
    );
  }, [option]);
  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | null = null;
    import("echarts")
      .then((ec) => {
        if (disposed || !host.current) return;
        chart.current = ec.init(host.current, undefined, {
          renderer: "canvas",
        });
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
        chart.current.setOption({
          ...optionRef.current,
          animation: !reduced.matches,
        });
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
    textStyle: { color: "#f1f5f9", fontSize: 13 },
    confine: true,
  },
};
export const axis = {
  axisLine: { lineStyle: { color: "#29364a" } },
  axisLabel: { color: "#aab6ca", fontSize: 12, hideOverlap: true },
  nameTextStyle: { color: "#b8c2d4", fontSize: 12 },
  splitNumber: 3,
  splitLine: { lineStyle: { color: "#1c293b", type: "dashed" as const } },
  axisTick: { show: false },
};
