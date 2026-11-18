"use client";
import { Check, Minus, X } from "lucide-react";
import { useApi, url } from "@/lib/api";
import type { ScoreHead, StockScores } from "@/lib/types";
import { ratingTone, statusText } from "@/lib/indicator-format";
import { EmptyState, ErrorState, Panel, Skeleton } from "@/components/ui";
import { InfoTip } from "./info-tip";

const vn = (v: number | null, digits = 2) =>
  v == null || !Number.isFinite(v)
    ? "—"
    : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: digits }).format(v);

function Head({
  title,
  tip,
  score,
  year,
  suffix = "",
}: {
  title: string;
  tip: string;
  score: ScoreHead;
  year: number;
  suffix?: string;
}) {
  return (
    <div className="score-head">
      <div className="stock-card-label">
        <span>{title}</span>
        <InfoTip label={title} text={tip} />
      </div>
      <strong className={score.value == null ? "is-empty" : ""}>
        {score.value == null ? "—" : `${vn(score.value, suffix ? 0 : 2)}${suffix}`}
      </strong>
      {score.value == null ? (
        <small>{statusText({ value: null, status: score.status }, year)}</small>
      ) : (
        score.rating && <span className={`badge ${ratingTone(score.rating)}`}>{score.rating}</span>
      )}
    </div>
  );
}

export function ScoresPanel({
  ticker,
  year,
  years,
  onYear,
  sectorLabel,
}: {
  ticker: string;
  year: number;
  years: number[];
  onYear: (year: number) => void;
  sectorLabel: string;
}) {
  const scores = useApi<StockScores>(url(`stocks/${encodeURIComponent(ticker)}/scores/${year}`));
  const select = (
    <select aria-label="Năm báo cáo" value={year} onChange={(e) => onYear(Number(e.target.value))}>
      {years.map((y) => (
        <option key={y} value={y}>
          Năm {y}
        </option>
      ))}
    </select>
  );
  if (scores.error)
    return (
      <Panel title="Điểm sức khỏe" action={select}>
        <EmptyState title={`Chưa có dữ liệu năm ${year}`} message="Chọn năm khác để xem điểm." />
      </Panel>
    );
  if (!scores.data) return <Skeleton height={420} />;
  const d = scores.data;
  if (!d.applicable)
    return (
      <Panel title="Điểm sức khỏe" action={select}>
        <EmptyState
          title="Không áp dụng"
          message={`F-score, M-score và Z-score dành cho doanh nghiệp sản xuất, thương mại, dịch vụ; không dùng cho ${sectorLabel.toLowerCase()}.`}
        />
      </Panel>
    );
  return (
    <>
      <Panel title="Điểm sức khỏe" eyebrow={`NĂM ${year}`} action={select}>
        <div className="score-heads">
          <Head title="F-score" tip="Sức khỏe tài chính 0–9 điểm; càng cao càng tốt." score={d.f_score} year={year} suffix="/9" />
          <Head title="M-score" tip="Dấu hiệu bất thường trong số liệu kế toán; trên −1,78 cần chú ý." score={d.m_score} year={year} />
          <Head title="Z-score" tip="Nguy cơ kiệt quệ tài chính; dưới 1,81 là rủi ro cao." score={d.z_score} year={year} />
        </div>
      </Panel>
      <div className="grid-three section-gap">
        <Panel title="9 tín hiệu F-score" eyebrow={`${d.f_score.known_signals}/9 TÍN HIỆU CÓ DỮ LIỆU`}>
          <ul className="signal-list">
            {d.f_score.signals.map((s) => (
              <li key={s.name} className={s.passed == null ? "unknown" : s.passed ? "pass" : "fail"}>
                {s.passed == null ? <Minus size={16} /> : s.passed ? <Check size={16} /> : <X size={16} />}
                <span>{s.text}</span>
                <span className="sr-only">
                  {s.passed == null ? "Chưa đủ dữ liệu" : s.passed ? "Đạt" : "Không đạt"}
                </span>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="8 biến M-score" eyebrow="1,0 LÀ BÌNH THƯỜNG (TRỪ TATA)">
          <dl className="variable-list">
            {d.m_score.variables.map((v) => (
              <div key={v.name}>
                <dt>
                  <b>{v.name}</b> {v.text}
                </dt>
                <dd>{vn(v.value, 3)}</dd>
              </div>
            ))}
          </dl>
        </Panel>
        <Panel title="5 thành phần Z-score" eyebrow="Z = 1,2·X1 + 1,4·X2 + 3,3·X3 + 0,6·X4 + X5">
          <dl className="variable-list">
            {d.z_score.components.map((v) => (
              <div key={v.name}>
                <dt>
                  <b>{v.name}</b> {v.text}
                </dt>
                <dd>{vn(v.value, 3)}</dd>
              </div>
            ))}
          </dl>
          {d.z_score.value == null && d.z_score_dp.value != null && (
            <p className="panel-note">
              Chưa có giá cuối năm; Z&apos;&apos; (không cần giá) = {vn(d.z_score_dp.value)}.
            </p>
          )}
        </Panel>
      </div>
    </>
  );
}
