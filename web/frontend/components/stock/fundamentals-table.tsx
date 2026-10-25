"use client";
import type { StockFundamentals } from "@/lib/types";
import { formatMetric, statusText, unitHint } from "@/lib/indicator-format";
import { InfoTip } from "./info-tip";

function Sparkline({ values }: { values: (number | null)[] }) {
  const known = values.filter((v): v is number => v != null);
  if (known.length < 2) return <span className="sparkline-empty" aria-hidden />;
  const min = Math.min(...known);
  const max = Math.max(...known);
  const x = (i: number) => (i / (values.length - 1)) * 76 + 2;
  const y = (v: number) => (max === min ? 12 : 22 - ((v - min) / (max - min)) * 20);
  // Gaps stay gaps: a missing year breaks the line instead of being bridged.
  const segments: string[][] = [[]];
  values.forEach((v, i) => {
    if (v == null) segments.push([]);
    else segments.at(-1)!.push(`${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  });
  return (
    <svg className="sparkline" viewBox="0 0 80 24" aria-hidden>
      {segments
        .filter((s) => s.length > 1)
        .map((s, i) => (
          <polyline key={i} points={s.join(" ")} />
        ))}
      {segments
        .filter((s) => s.length === 1)
        .map((s, i) => {
          const [cx, cy] = s[0].split(",");
          return <circle key={`d${i}`} cx={cx} cy={cy} r={1.6} />;
        })}
    </svg>
  );
}

export function FundamentalsTable({
  data,
  sector,
}: {
  data: StockFundamentals;
  sector: string;
}) {
  return (
    <div className="data-table-wrap fundamentals-wrap">
      <table className="data-table fundamentals-table">
        <caption className="sr-only">
          Chỉ số tài chính {data.ticker} theo năm {data.years[0]}–{data.years.at(-1)}
        </caption>
        <thead>
          <tr>
            <th scope="col">Chỉ số</th>
            <th scope="col" className="spark-col">
              Xu hướng
            </th>
            {data.years.map((y) => (
              <th scope="col" key={y}>
                {y}
              </th>
            ))}
          </tr>
        </thead>
        {data.groups.map((group) => (
          <tbody key={group.name}>
            <tr className="group-row">
              <th colSpan={data.years.length + 2} scope="colgroup">
                {group.name}
              </th>
            </tr>
            {group.metrics.map((m) => {
              const def = data.definitions[m];
              const row = data.metrics[m] || {};
              return (
                <tr key={m} data-metric={m}>
                  <th scope="row">
                    <span className="metric-name">
                      {def.label}
                      <small className="unit-hint">{unitHint(def.unit, m)}</small>
                      <InfoTip label={def.label} text={def.description} />
                    </span>
                  </th>
                  <td className="spark-col">
                    <Sparkline values={data.years.map((y) => row[String(y)]?.value ?? null)} />
                  </td>
                  {data.years.map((y) => {
                    const cell = row[String(y)];
                    const missing = !cell || cell.value == null;
                    return (
                      <td
                        key={y}
                        className={missing ? "cell-missing" : ""}
                        title={missing ? statusText(cell, y, sector) : undefined}
                      >
                        {missing ? (
                          <>
                            <span aria-hidden>—</span>
                            <span className="sr-only">{statusText(cell, y, sector)}</span>
                          </>
                        ) : (
                          formatMetric(cell.value, def.unit, m, false)
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        ))}
      </table>
    </div>
  );
}
