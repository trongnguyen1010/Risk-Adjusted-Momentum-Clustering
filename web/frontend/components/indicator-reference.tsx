"use client";
import { useApi, url } from "@/lib/api";
import { Panel, ErrorState, Skeleton } from "./ui";
export { FinancialIndicators as IndicatorReference } from "./financial-indicators";
const families = ["EPS", "PE", "PB", "F_SCORE", "M_SCORE", "Z_SCORE"];
const labels: Record<string, string> = { EPS: "EPS cơ bản", PE: "P/E", PB: "P/B", F_SCORE: "F-Score", M_SCORE: "M-Score", Z_SCORE: "Z-Score" };
export function IndicatorCoverage() {
  const state = useApi<{
    packages: {
      id: string;
      numeric_values: number;
      symbols: number;
      full6_cohorts: number;
      families: Record<string, number>;
    }[];
    unavailable_sources: string[];
  }>(url("indicator-coverage"));
  return (
    <Panel
      title="Coverage EPS / P/E / P/B / F / M / Z"
      eyebrow="OBSERVATIONS THEO GÓI · KHÔNG PHẢI TOÀN THỊ TRƯỜNG"
    >
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
                  <th>Gói</th>
                  <th>Numeric rows</th>
                  <th>Mã</th>
                  <th>Cohorts đủ sáu</th>
                  {families.map((f) => (
                    <th key={f}>{labels[f]}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {state.data.packages.map((p) => (
                  <tr key={p.id}>
                    <th>{p.id}</th>
                    <td>{p.numeric_values}</td>
                    <td>{p.symbols}</td>
                    <td>{p.full6_cohorts}</td>
                    {families.map((f) => (
                      <td key={f}>{p.families[f]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="panel-note">
            Pilot5 là tập con của reviewed85; không cộng hai gói. Mỗi
            observation giữ kỳ/vintage/basis riêng. Hai Z bổ sung chỉ thêm kỳ,
            không thêm mã. Full6 không chứng minh current/PIT hoặc
            production-ready.
          </p>
          {state.data.unavailable_sources.length > 0 && (
            <p className="panel-note amber">
              Gói không sẵn sàng: {state.data.unavailable_sources.join(", ")}
            </p>
          )}
        </>
      )}
    </Panel>
  );
}
