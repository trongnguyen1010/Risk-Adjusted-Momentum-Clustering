"use client";
import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { useCatalog } from "@/components/providers";
import {
  Panel,
  PageHeading,
  Badge,
  Skeleton,
  ErrorState,
} from "@/components/ui";
import { FAMILY, number, compact } from "@/lib/format";
import type { Kind } from "@/lib/types";
export default function Lab() {
  const c = useCatalog();
  const [tab, setTab] = useState("methods"),
    [query, setQuery] = useState("");
  if (c.error) return <ErrorState message={c.error} retry={c.retry} />;
  if (!c.data) return <Skeleton height={600} />;
  const { metadata: m, datasets: d, provenance } = c.data;
  return (
    <>
      <PageHeading
        eyebrow="BẰNG CHỨNG / KHẢ NĂNG TÁI LẬP"
        title="Phòng nghiên cứu"
        description="Kiểm tra nguồn tạo biểu đồ, những kết luận có bằng chứng và các giới hạn còn lại."
        action={<Badge>Kết quả nghiên cứu chỉ đọc</Badge>}
      />
      <div className="tabs-line">
        {[
          ["methods", "Phương pháp"],
          ["definitions", "Từ điển đặc trưng"],
          ["quality", "Chất lượng và giới hạn"],
          ["provenance", "Nguồn gốc dữ liệu"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={tab === id ? "active" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "methods" ? (
        <>
          <div className="method-grid">
            {(Object.keys(FAMILY) as Kind[]).map((kind) => (
              <Panel key={kind}>
                <div className="method-card">
                  <div>
                    <Badge
                      tone={
                        kind === "market"
                          ? "teal"
                          : kind === "financial"
                            ? "purple"
                            : "amber"
                      }
                    >
                      MÔ HÌNH {FAMILY[kind].letter}
                    </Badge>
                    <h3>{FAMILY[kind].label}</h3>
                    <p>{FAMILY[kind].subtitle}</p>
                    <p style={{ marginTop: 15 }}>
                      K-Means · {d[kind].scaling}
                      <br />
                      {d[kind].frequency}
                      <br />
                      {d[kind].version}
                    </p>
                  </div>
                  <div className="method-stats">
                    <div>
                      <strong>{d[kind].k}</strong>
                      <span>Số cụm đã chốt</span>
                    </div>
                    <div>
                      <strong>{d[kind].features.length}</strong>
                      <span>Đặc trưng đầu vào</span>
                    </div>
                    <div>
                      <strong>{d[kind].dates.length}</strong>
                      <span>Mô hình đã lưu</span>
                    </div>
                    <div>
                      <strong>{number(d[kind].latest.n)}</strong>
                      <span>Nhóm cổ phiếu gần nhất</span>
                    </div>
                  </div>
                </div>
              </Panel>
            ))}
          </div>
          <Panel
            className="section-gap"
            title="Tham chiếu kết hợp · cấu hình đã duyệt"
            eyebrow="ỨNG DỤNG KHÔNG FIT MÔ HÌNH"
          >
            <pre className="code-block">
              {JSON.stringify(d.combined.protocol, null, 2)}
            </pre>
          </Panel>
          <Panel className="section-gap" title="Nguyên tắc diễn giải">
            <ul className="limitations">
              {[
                "A, B và C có hệ nhãn riêng. Nhãn cụm không phải xếp hạng đầu tư.",
                "Căn nhãn chuyển cụm chỉ hoán vị nhãn đích khi hiển thị để tối đa số thành viên trùng nhau, không xác lập cùng một trạng thái kinh tế.",
                "Đặc trưng thị trường theo điều kiện nghiên cứu market-only đã chốt. Mô hình tài chính và kết hợp là tham chiếu theo năm sau kỳ báo cáo.",
                "Không huấn luyện khi chạy ứng dụng, không chọn mô hình theo lợi nhuận, không tuyên bố hiệu quả danh mục.",
                "Sáu tỷ số cốt lõi chưa cung cấp đầy đủ EPS / P/E / P/B / điểm F / M / Z.",
              ].map((t) => (
                <li key={t}>
                  <AlertTriangle size={14} />
                  {t}
                </li>
              ))}
            </ul>
          </Panel>
        </>
      ) : tab === "definitions" ? (
        <Panel
          title="Từ điển đặc trưng"
          eyebrow="14 ĐẦU VÀO QUAN SÁT · METADATA NGUỒN"
        >
          <div className="data-table-wrap">
            <table className="definition-table">
              <thead>
                <tr>
                  <th>MÃ / NHÓM</th>
                  <th>ĐẶC TRƯNG</th>
                  <th>ĐỊNH NGHĨA / ĐƠN VỊ</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(m.definitions).map(([key, f]) => (
                  <tr id={key} key={key}>
                    <td>
                      {key}
                      <br />
                      <Badge>
                        {FAMILY[f.family as Kind]?.label || f.family}
                      </Badge>
                    </td>
                    <td>{f.label}</td>
                    <td>
                      {key === "vol_63"
                        ? "Độ lệch chuẩn mẫu lợi suất ngày trong 63 phiên × √252; quy đổi theo năm"
                        : f.formula}
                      <br />
                      <small>
                        {{ percent: "Tỷ lệ (%)", ratio: "Tỷ số", vnd: "VND" }[
                          f.unit
                        ] || f.unit}
                      </small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      ) : tab === "quality" ? (
        <>
          <div className="grid-equal">
            <Panel
              title="Kiểm chứng kết quả nghiên cứu"
              eyebrow="KIỂM CHỨNG ≠ ĐỦ ĐIỀU KIỆN NGHIÊN CỨU"
            >
              <div className="panel-body status-list">
                {(Object.keys(FAMILY) as Kind[]).map((kind) => (
                  <div className="status-row" key={kind}>
                    <span>{FAMILY[kind].label}</span>
                    <span>
                      <Badge tone="teal">{m.validations[kind]?.status}</Badge>{" "}
                      <Badge tone="amber">
                        {m.validations[kind]?.quality_status}
                      </Badge>
                    </span>
                  </div>
                ))}
                <div className="status-row">
                  <span>Bộ kiểm thử toàn project</span>
                  <Badge tone="amber">{m.full_suite.status}</Badge>
                </div>
                <p className="muted text-small">{m.full_suite.reason}</p>
              </div>
            </Panel>
            <Panel
              title="Mức độ sẵn có của dữ liệu"
              eyebrow="KHÔNG ĐIỀN CHỈ SỐ GIẢ"
            >
              <div className="panel-body status-list">
                {[
                  ["Quan sát giá", number(m.price_rows)],
                  [
                    "Mốc công bố báo cáo tài chính",
                    `${m.financial_publication_rows} / ${number(m.financial_rows)}`,
                  ],
                  ["PIT / backtest cuối cùng", "Chưa sẵn sàng"],
                  [
                    "Bộ EPS/P/E/P/B/F/M/Z",
                    "Có ở nhóm đã review; chưa đủ mọi mã/năm",
                  ],
                  ["Giá thị trường trực tiếp", "Chưa có dữ liệu"],
                  [
                    "Khóa giá xung đột được giữ lại",
                    number(m.price_conflicts_held),
                  ],
                ].map(([a, b]) => (
                  <div className="status-row" key={a}>
                    <span>{a}</span>
                    <span>{b}</span>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
          <Panel className="section-gap" title="Giới hạn đã biết">
            <ul className="limitations">
              {m.limitations.map((t) => (
                <li key={t}>
                  <AlertTriangle size={15} />
                  {t}
                </li>
              ))}
            </ul>
          </Panel>
        </>
      ) : (
        <Panel
          title="Nguồn gốc dữ liệu"
          eyebrow="ĐẦU VÀO ĐÃ GHIM SHA-256"
          action={
            <input
              aria-label="Lọc nguồn dữ liệu"
              placeholder="Tìm đường dẫn nguồn…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          }
        >
          <p className="panel-note">
            Gói dữ liệu hiển thị {m.version} · xuất lúc {m.generated_at}.
            Checksum SQLite được kiểm tra khi API khởi động. Đường dẫn là nguồn
            nghiên cứu local, không phải liên kết tải công khai.
          </p>
          {provenance
            .filter((p) => p.path.toLowerCase().includes(query.toLowerCase()))
            .map((p) => (
              <div className="artifact-row" key={p.path}>
                <strong>{p.path}</strong>
                <small>SHA-256 {p.sha256}</small>
                <small>{compact(p.bytes)} bytes</small>
              </div>
            ))}
        </Panel>
      )}
    </>
  );
}
