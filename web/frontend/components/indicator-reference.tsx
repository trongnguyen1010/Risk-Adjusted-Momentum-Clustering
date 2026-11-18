"use client";
import { useApi, url } from "@/lib/api";
import { number } from "@/lib/format";
import { Panel, ErrorState, Skeleton } from "./ui";

interface Coverage {
  total_tickers: number;
  years: number[];
  metrics: { metric: string; label: string; group: string; counts: Record<string, number> }[];
}

/** How many tickers have each computed indicator, per fiscal year. */
export function IndicatorCoverage() {
  const state = useApi<Coverage>(url("fundamentals-coverage"));
  return (
    <Panel title="Độ phủ chỉ số tài chính" eyebrow="SỐ MÃ CÓ GIÁ TRỊ THEO NĂM">
      {state.error ? (
        <ErrorState message={state.error} retry={state.retry} />
      ) : !state.data ? (
        <Skeleton />
      ) : (
        <>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Chỉ số</th>
                  {state.data.years.map((y) => (
                    <th scope="col" key={y}>
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {state.data.metrics.map((m) => (
                  <tr key={m.metric}>
                    <th scope="row">{m.label}</th>
                    {state.data!.years.map((y) => (
                      <td key={y}>{number(m.counts[String(y)] ?? 0)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="panel-note">
            Trên tổng {number(state.data.total_tickers)} mã. Ngân hàng, chứng khoán, bảo hiểm không tính F/M/Z.
          </p>
        </>
      )}
    </Panel>
  );
}
