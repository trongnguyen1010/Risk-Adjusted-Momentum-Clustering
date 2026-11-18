"use client";
import { useApi, url } from "@/lib/api";
import type { StockPeers } from "@/lib/types";
import { formatMetric } from "@/lib/indicator-format";
import { ErrorState, Panel, Skeleton } from "@/components/ui";

export function PeersTable({
  ticker,
  onSelect,
}: {
  ticker: string;
  onSelect: (ticker: string) => void;
}) {
  const peers = useApi<StockPeers>(url(`stocks/${encodeURIComponent(ticker)}/peers`));
  if (peers.error) return <ErrorState message={peers.error} retry={peers.retry} />;
  if (!peers.data) return <Skeleton height={360} />;
  const basis = peers.data.basis.startsWith("CLUSTER")
    ? "Các mã cùng nhóm hành vi giá và tài chính, gần quy mô vốn hóa nhất."
    : "Các mã cùng nhóm ngành, gần quy mô vốn hóa nhất.";
  return (
    <Panel title="So sánh cùng nhóm" eyebrow="CHỈ SỐ NĂM GẦN NHẤT">
      <p className="panel-intro">{basis}</p>
      <div className="data-table-wrap">
        <table className="data-table peers-table">
          <thead>
            <tr>
              <th scope="col">Mã</th>
              <th scope="col">Sàn</th>
              <th scope="col">Vốn hóa (tỷ đ)</th>
              <th scope="col">EPS (đ)</th>
              <th scope="col">P/E</th>
              <th scope="col">P/B</th>
              <th scope="col">ROE</th>
            </tr>
          </thead>
          <tbody>
            {peers.data.items.map((r) => (
              <tr key={r.ticker} className={r.ticker === ticker ? "is-current" : ""}>
                <th scope="row">
                  {r.ticker === ticker ? (
                    <span aria-current="true">{r.ticker}</span>
                  ) : (
                    <button type="button" className="text-link" onClick={() => onSelect(r.ticker)}>
                      {r.ticker}
                    </button>
                  )}
                </th>
                <td>{r.exchange || "—"}</td>
                <td>{formatMetric(r.market_cap, "vnd", "market_cap", false)}</td>
                <td>{formatMetric(r.eps, "vnd", "eps", false)}</td>
                <td>{formatMetric(r.pe, "times", "pe", false)}</td>
                <td>{formatMetric(r.pb, "times", "pb", false)}</td>
                <td>{formatMetric(r.roe, "percent")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
