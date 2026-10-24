"use client";
import Link from "next/link";
import {
  ArrowUpRight,
  Layers3,
  ScanLine,
  FlaskConical,
  ArrowRight,
} from "lucide-react";
import { useCatalog } from "@/components/providers";
import { useApi, url } from "@/lib/api";
import {
  Panel,
  Badge,
  Skeleton,
  ErrorState,
  FeatureLink,
} from "@/components/ui";
import { Chart, baseChart, axis } from "@/components/chart";
import { Scatter } from "@/components/scatter";
import { COLORS, FAMILY, number, dateLabel } from "@/lib/format";
import type { Kind, SnapshotData } from "@/lib/types";
export default function Overview() {
  const catalog = useCatalog();
  const scatter = useApi<SnapshotData>(url("snapshots/market"));
  if (catalog.error)
    return <ErrorState message={catalog.error} retry={catalog.retry} />;
  if (!catalog.data) return <Skeleton height={600} />;
  const { metadata: m, datasets: d } = catalog.data;
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">CỔ PHIẾU VIỆT NAM / TRẠM NGHIÊN CỨU</div>
          <h1>
            Khám phá cấu trúc.
            <br />
            <span className="teal">Thấu hiểu thị trường.</span>
          </h1>
          <p>
            Khám phá hành vi thị trường và nền tảng doanh nghiệp qua ba mô hình
            phân cụm độc lập. Mọi kết quả đều có nguồn dữ liệu để đối chiếu.
          </p>
          <div className="hero-actions">
            <Link href="/atlas" className="button primary">
              Khám phá bản đồ phân cụm
              <ArrowUpRight size={15} />
            </Link>
            <Link href="/lab" className="button ghost">
              Xem phương pháp
              <ArrowRight size={14} />
            </Link>
          </div>
          <div className="hero-footnote">
            <span className="small-dot" />
            Dữ liệu lịch sử · {dateLabel(d.market.latest.date)} · Không có dữ
            liệu trực tiếp
          </div>
        </div>
        <div className="hero-visual">
          {scatter.data ? (
            <Scatter
              data={scatter.data}
              x="mom_63"
              y="vol_63"
              kind="market"
              height={300}
              mini
            />
          ) : (
            <Skeleton height={300} />
          )}
          <span className="hero-visual-label">
            CẤU TRÚC THỊ TRƯỜNG / A · {number(d.market.latest.n)} CỔ PHIẾU
          </span>
          <span className="hero-visual-corner">
            Động lượng × biến động
            <br />
            Tọa độ đặc trưng quan sát
          </span>
        </div>
      </section>
      <section className="stats-strip">
        {[
          [
            "Tập cổ phiếu thị trường",
            d.market.latest.n,
            `${number(m.candidates)} mã trong nguồn dữ liệu`,
          ],
          [
            "Thời điểm lịch sử",
            m.market_snapshots,
            "Theo tháng · 01/2019 — 12/2025",
          ],
          [
            "Doanh nghiệp có BCTC",
            d.financial.latest.n,
            "Nhóm cố định đủ 10 năm · 2016 — 2025",
          ],
          [
            "Quan sát kết hợp",
            d.combined.history.reduce((s, r) => s + r.n, 0),
            "7 mô hình tham chiếu cuối năm",
          ],
        ].map(([label, value, note]) => (
          <div className="stat" key={String(label)}>
            <div className="stat-top">
              {label}
              <ArrowUpRight size={12} />
            </div>
            <div className="stat-value">{number(Number(value))}</div>
            <div className="muted text-small">{note}</div>
          </div>
        ))}
      </section>
      <div className="grid-two section-gap">
        <Panel
          title="Độ phủ cổ phiếu qua thời gian"
          eyebrow="ĐỘ PHỦ QUAN SÁT"
          action={<Badge tone="teal">84 mô hình theo tháng</Badge>}
        >
          <Chart
            height={265}
            label="Số cổ phiếu thị trường đủ điều kiện theo tháng"
            option={{
              ...baseChart,
              tooltip: { ...baseChart.tooltip, trigger: "axis" },
              xAxis: {
                ...axis,
                type: "category",
                data: d.market.history.map((s) => s.date),
                axisLabel: {
                  ...axis.axisLabel,
                  formatter: (s: string) => s.slice(0, 7),
                },
              },
              yAxis: { ...axis, type: "value", min: "dataMin" },
              series: [
                {
                  type: "line",
                  data: d.market.history.map((s) => s.n),
                  symbol: "none",
                  lineStyle: { width: 2, color: COLORS[0] },
                  areaStyle: { color: "#2dd4bf12" },
                },
              ],
            }}
          />
          <p className="panel-note">
            Thành viên theo tiêu chí thị trường đã chốt tại từng thời điểm. Số
            lượng này không đồng nghĩa với tập cổ phiếu lịch sử đã xác minh PIT.
          </p>
        </Panel>
        <Panel
          title="Ba góc nhìn. Một không gian."
          eyebrow="CÁC NHÓM THỬ NGHIỆM"
        >
          {(Object.keys(FAMILY) as Kind[]).map((kind) => (
            <Link
              key={kind}
              href={`/atlas?kind=${kind}`}
              className="research-family"
            >
              <div className="family-heading">
                <span
                  className={`source-letter ${kind === "market" ? "teal" : kind === "financial" ? "purple" : "amber"}`}
                >
                  {FAMILY[kind].letter}
                </span>
                <div>
                  <strong>{FAMILY[kind].label}</strong>
                  <small>{FAMILY[kind].subtitle}</small>
                </div>
                <span className="family-count">
                  {number(d[kind].latest.n)}
                  <small>{dateLabel(d[kind].latest.date)}</small>
                </span>
              </div>
              <div className="distribution">
                {Object.entries(d[kind].latest.sizes).map(([id, n]) => (
                  <span
                    key={id}
                    style={{
                      width: `${(100 * n) / d[kind].latest.n}%`,
                      background: COLORS[Number(id)],
                    }}
                  />
                ))}
              </div>
              <div className="distribution-labels">
                {Object.entries(d[kind].latest.sizes).map(([id, n]) => (
                  <span key={id}>
                    {FAMILY[kind].letter}
                    {id} · {number(n)}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </Panel>
      </div>
      <Panel
        className="section-gap"
        title="Bản đồ độ phủ"
        eyebrow="THỜI ĐIỂM CÓ MÔ HÌNH · KHÔNG PHẢI NGÀY CÔNG BỐ"
      >
        <div className="coverage-grid">
          <span />{" "}
          {Array.from({ length: 10 }, (_, i) => (
            <span key={i}>{2016 + i}</span>
          ))}
          {(Object.keys(FAMILY) as Kind[]).map((kind) => (
            <div style={{ display: "contents" }} key={kind}>
              <span>{FAMILY[kind].label}</span>
              {Array.from({ length: 10 }, (_, i) => {
                const count = d[kind].dates.filter((s) =>
                  s.startsWith(String(2016 + i)),
                ).length;
                return (
                  <Link
                    key={i}
                    title={`${FAMILY[kind].label}: ${count} mô hình đã lưu trong năm ${2016 + i}`}
                    href={
                      count
                        ? `/atlas?kind=${kind}&date=${d[kind].dates.filter((s) => s.startsWith(String(2016 + i))).at(-1)}`
                        : "/lab"
                    }
                    className={`coverage-cell ${count ? "" : "empty"}`}
                  >
                    {count
                      ? `${count} ${count === 1 ? "mô hình" : "mô hình"}`
                      : "—"}
                  </Link>
                );
              })}
            </div>
          ))}
        </div>
      </Panel>
      <div className="overview-bottom section-gap">
        <FeatureLink
          href="/stocks?ticker=FPT"
          title="Từ cấu trúc đến cổ phiếu"
          text="Giá, đặc trưng và hành trình phân cụm."
          icon={<ScanLine size={20} />}
        />
        <FeatureLink
          href="/financial"
          title="Đối chiếu hai góc nhìn"
          text="Giao của nhóm thị trường × tài chính."
          icon={<Layers3 size={20} />}
        />
        <FeatureLink
          href="/lab"
          title="Kiểm tra bằng chứng"
          text="Định nghĩa, cấu hình và điều kiện chất lượng."
          icon={<FlaskConical size={20} />}
        />
      </div>
      <div className="scope-note">
        Chỉ dùng để tham khảo nghiên cứu. Dữ liệu tài chính còn thiếu ngày công
        bố; mô hình kết hợp có cụm rất nhỏ. Xem đầy đủ giới hạn tại Phòng nghiên
        cứu.
      </div>
    </>
  );
}
