"use client";
import { useState } from "react";
import { useApi, url } from "@/lib/api";
import { number } from "@/lib/format";
import { Panel, Badge, EmptyState, ErrorState, Skeleton } from "./ui";

type Metric = {
  family: string;
  value: string | null;
  status: string;
  variant: string | null;
  unit: string;
  year: string;
  input_period: string | null;
  input_scope: string | null;
  price_date: string | null;
  reference_date: string | null;
  period_kind: string | null;
  price_basis: string | null;
  balance_date: string | null;
  share_basis: string | null;
  missing_inputs: string | null;
  temporal_status: string | null;
};
type Group = {
  id: string;
  source_id: string;
  source_label: string;
  cohort: string;
  year: string;
  metrics: Metric[];
  source_path: string;
  source_sha256: string;
};
type Payload = {
  available: boolean;
  groups: Group[];
  missing_reason: string | null;
  note: string;
  sources: { id: string; numeric_values: number; symbols: number }[];
};
const labels: Record<string, string> = {
  EPS: "EPS cơ bản",
  PE: "P/E",
  PB: "P/B",
  F_SCORE: "F-Score",
  M_SCORE: "M-Score",
  Z_SCORE: "Z-Score",
};
function groupLabel(group: Group) {
  const date = group.metrics.find(m => m.reference_date)?.reference_date
    || group.metrics.find(m => m.price_date)?.price_date;
  const families = group.metrics.filter(m => m.value !== null).map(m => labels[m.family]).join(" / ");
  const period = group.metrics.find(m => m.period_kind && m.period_kind !== "ANNUAL")?.period_kind;
  return `${group.source_id === "pilot5" ? "Pilot5" : "Tổng hợp đã review"} · ${group.year}${date ? ` · tham chiếu ${date}` : ""}${period ? ` · ${period}` : ""} · ${families}`;
}
export function IndicatorReference({ ticker }: { ticker: string }) {
  const state = useApi<Payload>(
    url(`indicators/${encodeURIComponent(ticker)}`),
  );
  const [selected, setSelected] = useState("");
  const group =
    state.data?.groups.find((g) => g.id === selected) || state.data?.groups[0];
  return (
    <Panel
      className="section-gap"
      title="Sáu chỉ số tài chính đã tính"
      eyebrow="EPS · P/E · P/B · F-SCORE · M-SCORE · Z-SCORE"
      action={<Badge tone="amber">Tham chiếu đã review · chưa phải PIT</Badge>}
    >
      {state.error ? (
        <ErrorState message={state.error} retry={state.retry} />
      ) : !state.data ? (
        <Skeleton height={220} />
      ) : !group ? (
        <EmptyState
          title="Chưa có bộ chỉ số đã review cho mã này"
          message={
            state.data.missing_reason || "Không thay dữ liệu thiếu bằng 0."
          }
        />
      ) : (
        <>
          <div className="panel-body">
            <label className="select-label">
              Gói / kỳ tham chiếu
              <select
                aria-label="Gói sáu chỉ số tham chiếu"
                value={group.id}
                onChange={(e) => setSelected(e.target.value)}
                style={{ maxWidth: "100%" }}
              >
                {state.data.groups.map((g) => (
                  <option key={g.id} value={g.id}>
                    {groupLabel(g)}
                  </option>
                ))}
              </select>
            </label>
            <p className="warning-line" style={{ marginTop: 12 }}>
              Đây là bộ EPS/P/E/P/B/F/M/Z đã tính riêng, khác sáu core ratios
              của mô hình B/C. Ngày giá có thể sau thời điểm thị trường đang
              chọn; không dùng bộ này như thông tin đã biết tại ngày đó.
            </p>
          </div>
          <div className="indicator-cards">
            {group.metrics.map((m) => (
              <div className="indicator-card" key={m.family}>
                <span>{labels[m.family]}</span>
                <strong>
                  {m.value === null
                    ? "Chưa đủ input"
                    : `${number(Number(m.value), m.family === "F_SCORE" ? 0 : m.family === "EPS" ? 2 : 4)}${m.family === "F_SCORE" ? " / 9" : ""}`}
                </strong>
                <small>
                  {m.family === "EPS" ? "VND / cổ phiếu" : ""}
                  {m.price_date
                    ? `Giá ngày ${m.price_date}`
                    : `Năm tài chính ${m.year || group.year}`}
                </small>
                {m.period_kind && m.period_kind !== "ANNUAL" && (
                  <small>
                    Kỳ gốc: {m.period_kind}; không quy đổi annual/TTM.
                  </small>
                )}
                {m.reference_date && (
                  <small>Ngày tham chiếu {m.reference_date}</small>
                )}
                {m.value === null && (
                  <small>
                    Giữ thiếu; không coi là 0 hoặc tự hoàn thiện điểm.
                  </small>
                )}
              </div>
            ))}
          </div>
          <p className="panel-note">
            {group.metrics.filter((m) => m.value !== null).length}/6 chỉ số có
            số trong đúng gói đang chọn. {state.data.note} Các biến thể F/M/Z có
            giới hạn riêng; không áp ngưỡng gian lận hoặc phá sản một cách máy
            móc.
          </p>
          <details className="indicator-details">
            <summary>Xem công thức/biến thể, kỳ dữ liệu và nguồn</summary>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Chỉ số</th>
                    <th>Giá trị gốc đã lưu</th>
                    <th>Biến thể</th>
                    <th>Kỳ / sổ sách</th>
                    <th>Giá / basis</th>
                    <th>Scope / trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {group.metrics.map((m) => (
                    <tr key={m.family}>
                      <td>{labels[m.family]}</td>
                      <td className="mono">{m.value ?? "null"}</td>
                      <td>{m.variant || "—"}</td>
                      <td>
                        {m.input_period || m.year}
                        <br />
                        {m.balance_date || "—"}
                      </td>
                      <td>
                        {m.price_date || "—"}
                        <br />
                        {m.price_basis || "—"}
                        <br />
                        {m.share_basis || ""}
                      </td>
                      <td>
                        {m.input_scope || "Theo gói nguồn"}
                        <br />
                        {m.status}
                        <br />
                        {m.temporal_status}
                        <br />
                        {m.missing_inputs}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="panel-note mono">
              {group.source_path}
              <br />
              SHA-256: {group.source_sha256}
            </p>
          </details>
        </>
      )}
    </Panel>
  );
}
