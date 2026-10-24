"use client";
import { useState } from "react";
import type { SnapshotData } from "@/lib/types";
import { number } from "@/lib/format";
import { Panel, EmptyState } from "./ui";
export function SavedPeers({
  examples,
  onSelect,
}: {
  examples: NonNullable<SnapshotData["peer_examples"]>;
  onSelect: (ticker: string) => void;
}) {
  const [ticker, setTicker] = useState("FPT");
  const example = examples.find((p) => p.ticker === ticker) || examples[0];
  return (
    <Panel
      className="section-gap"
      title="Peer examples đã lưu"
      eyebrow="CHỈ CÁC MÃ CÓ ARTIFACT · KHÔNG XẾP HẠNG ĐẦU TƯ"
      action={
        example && (
          <select
            aria-label="Mã có peer example"
            value={example.ticker}
            onChange={(e) => setTicker(e.target.value)}
          >
            {examples.map((p) => (
              <option key={p.ticker}>{p.ticker}</option>
            ))}
          </select>
        )
      }
    >
      {!example ? (
        <EmptyState
          title="Chưa export khoảng cách peers cho model này"
          message="Bảng thành viên dùng rule cùng cluster/model/kỳ; không tự suy nearest peers."
        />
      ) : (
        <>
          <p className="panel-note">
            {example.ticker}: khoảng cách Euclidean trong đúng recipe space đã
            lưu, chỉ trong cùng cụm, loại chính mã đó, tie-break theo ticker.
            Không có taxonomy ngành được nghiệm thu; không gọi đây là peers cùng
            ngành.
          </p>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mã</th>
                  <th>Khoảng cách đã lưu</th>
                </tr>
              </thead>
              <tbody>
                {example.peers.map((p) => (
                  <tr key={p.ticker}>
                    <th>
                      <button onClick={() => onSelect(p.ticker)}>
                        {p.ticker} ↗
                      </button>
                    </th>
                    <td>{number(p.distance, 5)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Panel>
  );
}
