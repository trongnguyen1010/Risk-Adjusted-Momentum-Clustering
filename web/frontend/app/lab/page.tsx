"use client";
import Link from "next/link";
import { useSelection } from "@/lib/selection";
import {
  Panel,
  PageHeading,
  Badge,
  Skeleton,
  ErrorState,
} from "@/components/ui";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { FAMILY, number, compact } from "@/lib/format";
import type { Kind } from "@/lib/types";
const tabs = [
  ["methods", "Phương pháp"],
  ["quality", "Chất lượng"],
  ["provenance", "Nguồn & phiên bản"],
] as const;
export default function Lab() {
  const s = useSelection();
  const tab = tabs.some(([id]) => id === s.params.get("tab"))
    ? s.params.get("tab")!
    : "methods";
  const query = s.params.get("source_q") || "";
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;
  if (!s.data) return <Skeleton height={600} />;
  const { metadata: m, datasets: d, provenance } = s.data;
  return (
    <>
      <PageHeading
        eyebrow="BẰNG CHỨNG / KHẢ NĂNG TÁI LẬP"
        title="Phòng nghiên cứu"
        description="Đối chiếu phương pháp, chất lượng dữ liệu và phiên bản nguồn. Kiểm chứng kỹ thuật và research readiness được đánh giá riêng."
        action={<Badge>Chỉ đọc artifacts</Badge>}
      />
      <WorkspaceTabs
        tabs={tabs}
        scope="lab"
        value={tab}
        onChange={(tab) => s.set({ tab })}
      />
      <div id="lab-panel" role="tabpanel" aria-labelledby={`lab-${tab}`}>
        {tab === "methods" && (
          <>
            <div className="method-grid">
              {(Object.keys(FAMILY) as Kind[]).map((kind) => (
                <Panel
                  key={kind}
                  title={`${FAMILY[kind].letter} · ${FAMILY[kind].label}`}
                >
                  <div className="panel-body">
                    <p>{FAMILY[kind].subtitle}</p>
                    <p>
                      K-Means · {d[kind].scaling} · {d[kind].frequency}
                    </p>
                    <p>
                      {d[kind].features.length} features ·{" "}
                      {d[kind].dates.length} snapshots ·{" "}
                      {number(d[kind].latest.n)} mã ở kỳ cuối.
                    </p>
                    <p className="context-line">
                      Nhãn độc lập; không xếp hạng đầu tư. Version{" "}
                      {d[kind].version}.
                    </p>
                  </div>
                </Panel>
              ))}
            </div>
            {s.data.variants && (
              <Panel
                className="section-gap"
                title="R1 · bản thử nghiệm"
                eyebrow="MÔ HÌNH GỐC VẪN LÀ MẶC ĐỊNH"
              >
                <div className="panel-body">
                  <p>
                    202 snapshots P1/P3 đọc từ immutable R1 artifacts. Dùng
                    selector phiên bản để đối chiếu labels, median/IQR, saved
                    diagnostics và peer examples; không xem đây là release được
                    nghiệm thu.
                  </p>
                  {Object.entries(s.data.variants).map(([kind, items]) => (
                    <div className="membership-summary" key={kind}>
                      <h3>{FAMILY[kind as Kind].label}</h3>
                      {items?.map((item) => (
                        <Link
                          className="button ghost"
                          key={item.version}
                          href={`/atlas?kind=${kind}&date=${item.latest.date}&version=${encodeURIComponent(item.version)}`}
                        >
                          {item.label} ↗
                        </Link>
                      ))}
                    </div>
                  ))}
                </div>
              </Panel>
            )}
            <Panel className="section-gap" title="Cách diễn giải">
              <ul className="limitations">
                <li>
                  Ứng dụng chỉ đọc frozen artifacts. Không fit model hoặc tính
                  quality metrics trong browser.
                </li>
                <li>
                  A/B/C dùng dữ liệu khác nhau; không so điểm chất lượng giữa ba mô hình.
                </li>
                <li>
                  Financial FY có thể công bố sau ngày market; C và ma trận
                  same-FY là ex-post, không PIT/backtest.
                </li>
                <li>
                  Cân bằng variance hai block đầu vào C không đảm bảo mỗi block
                  đóng góp 50% separation.
                </li>
                <li>
                  Peer list chỉ là cùng nhãn/model/kỳ; chưa có distance/rank
                  được export thì không hiển thị nearest peers giả.
                </li>
              </ul>
            </Panel>
            <Panel className="section-gap" title="Cấu hình và định nghĩa">
              <details className="indicator-details">
                <summary>Protocol C đã duyệt và lưu</summary>
                <pre className="code-block">
                  {JSON.stringify(d.combined.protocol, null, 2)}
                </pre>
              </details>
              <details className="indicator-details">
                <summary>Từ điển 14 features và đơn vị</summary>
                <div className="data-table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Mã / nhóm</th>
                        <th>Đặc trưng</th>
                        <th>Công thức / đơn vị</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(m.definitions).map(([key, f]) => (
                        <tr key={key}>
                          <th>
                            {key}
                            <small className="block">
                              {FAMILY[f.family as Kind]?.label || f.family}
                            </small>
                          </th>
                          <td>{f.label}</td>
                          <td>
                            {f.formula}
                            <small className="block">{f.unit}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </Panel>
          </>
        )}
        {tab === "quality" && (
          <>
            <div className="grid-equal">
              <Panel
                title="Kiểm chứng kỹ thuật"
                eyebrow="ARITHMETIC / HASH / EXECUTION"
              >
                <div className="panel-body status-list">
                  {(Object.keys(FAMILY) as Kind[]).map((kind) => (
                    <div className="status-row" key={kind}>
                      <span>{FAMILY[kind].label}</span>
                      <Badge>{m.validations[kind]?.status}</Badge>
                      <Badge tone="amber">
                        {m.validations[kind]?.quality_status}
                      </Badge>
                    </div>
                  ))}
                  <div className="status-row">
                    <span>Kiểm thử toàn bộ</span>
                    <Badge tone="amber">{m.full_suite.status}</Badge>
                  </div>
                  <p>{m.full_suite.reason}</p>
                </div>
              </Panel>
              <Panel title="Mức sẵn sàng nghiên cứu" eyebrow="CHƯA DÙNG ĐỂ ĐẦU TƯ">
                <div className="panel-body">
                  <p>
                    Publication timing: {number(m.financial_publication_rows)} /{" "}
                    {number(m.financial_rows)} rows.
                  </p>
                  <p>
                    Strict PIT / historical identity / final backtest: chưa
                    nghiệm thu.
                  </p>
                  <p>
                    Kết quả ổn định khi chạy lại, nhưng chưa đủ để kết luận đầu tư.
                  </p>
                  <p className="warning-line section-gap">
                    Mô hình có nhóm quá nhỏ hoặc bị một đặc trưng chi phối cần kiểm tra thêm.
                  </p>
                </div>
              </Panel>
            </div>
            <Panel className="section-gap" title="Giới hạn đã lưu trong bundle">
              <ul className="limitations">
                {m.limitations.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </Panel>
          </>
        )}
        {tab === "provenance" && (
          <Panel
            title="Nguồn và phiên bản"
            eyebrow="ĐẦU VÀO ĐÃ KHÓA PHIÊN BẢN"
            action={
              <input
                aria-label="Lọc nguồn dữ liệu"
                placeholder="Tìm đường dẫn nguồn…"
                value={query}
                onChange={(e) => s.set({ source_q: e.target.value || null })}
              />
            }
          >
            <p className="panel-note">
              Bundle {m.version} · generated {m.generated_at}.{" "}
              {number(m.price_rows)} observations giá;{" "}
              {number(m.price_conflicts_held)} keys giá xung đột được giữ lại.
              Hash database được kiểm lúc API khởi động. Metadata này mô tả
              artifact, không phải chứng nhận release hiện tại.
            </p>
            <details className="indicator-details" open>
              <summary>Danh sách pins và kích thước</summary>
              {provenance
                .filter((p) =>
                  p.path.toLowerCase().includes(query.toLowerCase()),
                )
                .map((p) => (
                  <div className="artifact-row" key={p.path}>
                    <strong>{p.path}</strong>
                    <small>SHA-256 {p.sha256}</small>
                    <small>{compact(p.bytes)} bytes</small>
                  </div>
                ))}
            </details>
          </Panel>
        )}
      </div>
    </>
  );
}
