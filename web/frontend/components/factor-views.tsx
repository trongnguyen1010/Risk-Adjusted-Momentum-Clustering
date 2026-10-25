"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { FAMILY, clusterColor } from "@/lib/format";
import { FEATURE_HELP } from "@/lib/feature-help";
import { median, percentiles, spearman } from "@/lib/stats";
import type { Kind, SnapshotData } from "@/lib/types";

export const featureLabel = (key: string) => {
  const help = FEATURE_HELP[key];
  if (!help) return key;
  return help.group === "Động lượng giá" ? `Động lượng ${help.label}` : help.label;
};

const short = (key: string) => {
  const help = FEATURE_HELP[key];
  return help?.group === "Động lượng giá" ? `ĐL ${help.label}` : help?.label || key;
};

/**
 * Diverging tint for v in [-1, 1]: blue = below the middle / opposite direction, amber = above / same direction.
 * Neither colour means good or bad — high volatility is "high", not "good".
 */
const tint = (v: number) =>
  `color-mix(in srgb, var(${v >= 0 ? "--amber" : "--blue"}) ${Math.round(Math.min(1, Math.abs(v)) * 60)}%, transparent)`;

function Legend({ low, mid, high }: { low: string; mid: string; high: string }) {
  return (
    <div className="factor-legend" aria-hidden>
      <span>{low}</span>
      <i />
      <span>{mid}</span>
      <i className="up" />
      <span>{high}</span>
    </div>
  );
}

/**
 * Scroll container where a plain mouse wheel also scrolls sideways: when the table cannot scroll further
 * vertically in the wheel's direction, the wheel moves it horizontally (frozen header/column stay put).
 */
function FactorScroll({ children }: { children: React.ReactNode }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (e.ctrlKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      const canX = el.scrollWidth > el.clientWidth;
      const atTop = el.scrollTop <= 0, atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1;
      const canY = el.scrollHeight > el.clientHeight && !((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom));
      if (!canX || canY) return;
      const atLeft = el.scrollLeft <= 0, atRight = el.scrollLeft + el.clientWidth >= el.scrollWidth - 1;
      if ((e.deltaY < 0 && atLeft) || (e.deltaY > 0 && atRight)) return; // let the page scroll at the ends
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);
  return (
    <div ref={box} className="factor-scroll">
      {children}
    </div>
  );
}

/** Which features move with each map axis (Spearman), strongest two per axis. */
export function axisDrivers(data: SnapshotData, features: string[]) {
  const axis = (key: string) =>
    features
      .map((f) => ({ f, r: spearman(data.points.map((p) => p.features[key]), data.points.map((p) => p.features[f])) }))
      .filter((x): x is { f: string; r: number } => x.r !== null)
      .sort((a, b) => Math.abs(b.r) - Math.abs(a.r))
      .slice(0, 2);
  return { x: axis("_map_x"), y: axis("_map_y") };
}

export function DriverLine({ label, drivers }: { label: string; drivers: { f: string; r: number }[] }) {
  return (
    <span>
      <b>{label}</b>{" "}
      {drivers.map((d, i) => (
        <span key={d.f}>
          {i ? ", " : ""}
          {featureLabel(d.f)} {d.r >= 0 ? "↑" : "↓"} ({d.r.toFixed(2).replace(".", ",")})
        </span>
      ))}
    </span>
  );
}

/** Median percentile (0–100) of each cluster's members on each feature, vs the whole snapshot. */
export function ClusterHeatmap({ data, kind, features }: { data: SnapshotData; kind: Kind; features: string[] }) {
  const ids = Object.keys(data.snapshot.sizes).map(Number).sort((a, b) => a - b);
  const names = Object.fromEntries(data.profiles.map((p) => [p.cluster, p.name]));
  const grid = useMemo(() => {
    const pct = Object.fromEntries(features.map((f) => [f, percentiles(data.points.map((p) => p.features[f]))]));
    return Object.fromEntries(
      ids.map((c) => [c, Object.fromEntries(features.map((f) => [f, median(data.points.map((p, i) => (p.cluster === c ? pct[f][i] : null)))]))]),
    );
  }, [data, features]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="factor-view">
      <div className="factor-head">
        <p className="factor-note">
          Mỗi ô: nhóm đứng ở đâu trên chỉ số đó so với toàn bộ {data.points.length.toLocaleString("vi-VN")} mã
          (trung vị, 0 = thấp nhất, 100 = cao nhất).
        </p>
        <Legend low="Thấp hơn thị trường" mid="50" high="Cao hơn thị trường" />
      </div>
      <FactorScroll>
        <table className="factor-table">
          <thead>
            <tr>
              <th className="corner">Nhóm</th>
              {features.map((f) => (
                <th key={f} title={`${featureLabel(f)}: ${FEATURE_HELP[f]?.help || ""}`}>
                  {short(f)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ids.map((c) => (
              <tr key={c}>
                <th scope="row" title={names[c] || ""}>
                  <i style={{ background: clusterColor(c, ids) }} />
                  <b>
                    {FAMILY[kind].letter}
                    {c}
                  </b>{" "}
                  <span>{names[c] || ""}</span>
                </th>
                {features.map((f) => {
                  const v = grid[c]?.[f] ?? null;
                  return (
                    <td key={f} style={v === null ? undefined : { background: tint((v - 0.5) * 2) }}>
                      {v === null ? "—" : Math.round(v * 100)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </FactorScroll>
    </div>
  );
}

/** Representative features shown first in the correlation matrix (the rest can be added). */
const DEFAULT_CORR: Record<Kind, string[]> = {
  market: ["mom_63", "mom_252", "vol_63", "mdd_126", "beta_126", "liquidity_21"],
  financial: ["roe", "net_margin", "debt_to_equity", "current_ratio", "revenue_growth", "cfo_to_ni"],
  combined: ["mom_63", "vol_63", "liquidity_21", "roe", "net_margin", "debt_to_equity"],
};

/** Spearman correlation between selected features of the model in this snapshot. */
export function CorrelationMatrix({ data, kind, features }: { data: SnapshotData; kind: Kind; features: string[] }) {
  const defaults = DEFAULT_CORR[kind].filter((f) => features.includes(f));
  const [chosen, setChosen] = useState<string[] | null>(null);
  const picked = (chosen ?? defaults).filter((f) => features.includes(f));
  const order = features.filter((f) => picked.includes(f));
  const cols = useMemo(
    () => Object.fromEntries(features.map((f) => [f, data.points.map((p) => p.features[f])])),
    [data, features],
  );
  const toggle = (f: string) =>
    setChosen((cur) => {
      const base = cur ?? defaults;
      return base.includes(f) ? (base.length > 2 ? base.filter((x) => x !== f) : base) : [...base, f];
    });
  return (
    <div className="factor-view">
      <div className="factor-head">
        <p className="factor-note">
          Hai chỉ số đi cùng nhau đến đâu trong kỳ này (tương quan hạng Spearman, −1 đến +1). Gần ±1 nghĩa là gần như
          trùng thông tin.
        </p>
        <Legend low="−1 ngược chiều" mid="0" high="+1 cùng chiều" />
      </div>
      <div className="chip-row" role="group" aria-label="Chọn chỉ số">
        {features.map((f) => (
          <button key={f} aria-pressed={picked.includes(f)} onClick={() => toggle(f)} title={featureLabel(f)}>
            {short(f)}
          </button>
        ))}
        <button className="chip-reset" onClick={() => setChosen(features)}>
          Tất cả
        </button>
        <button className="chip-reset" onClick={() => setChosen(null)}>
          Mặc định
        </button>
      </div>
      <FactorScroll>
        <table className="factor-table corr">
          <thead>
            <tr>
              <th className="corner" />
              {order.map((f) => (
                <th key={f} title={featureLabel(f)}>
                  {short(f)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {order.map((f, i) => (
              <tr key={f}>
                <th scope="row" title={featureLabel(f)}>
                  {short(f)}
                </th>
                {order.map((g, j) => {
                  const r = i === j ? 1 : spearman(cols[f], cols[g]);
                  return (
                    <td key={g} className={i === j ? "diag" : ""} style={r === null || i === j ? undefined : { background: tint(r) }}>
                      {r === null ? "—" : (r > 0 && i !== j ? "+" : "") + r.toFixed(2).replace(".", ",")}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </FactorScroll>
    </div>
  );
}
