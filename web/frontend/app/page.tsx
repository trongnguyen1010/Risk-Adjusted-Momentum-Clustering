"use client";
import Link from "next/link";
import { Search, ArrowUpRight } from "lucide-react";
import { useCatalog } from "@/components/providers";
import { useApi, url } from "@/lib/api";
import {
  Panel,
  Badge,
  Skeleton,
  ErrorState,
  PageHeading,
  ClusterBadge,
} from "@/components/ui";
import { Scatter } from "@/components/scatter";
import { FAMILY, number, dateLabel, clusterColor } from "@/lib/format";
import type { Kind, SnapshotData } from "@/lib/types";
export default function Overview() {
  const catalog = useCatalog();
  const state = useApi<SnapshotData>(
    catalog.data
      ? url("snapshots/combined", {
          date: catalog.data.datasets.combined.latest.date,
          version: catalog.data.datasets.combined.version,
        })
      : null,
  );
  if (catalog.error)
    return <ErrorState message={catalog.error} retry={catalog.retry} />;
  if (!catalog.data) return <Skeleton height={600} />;
  const d = catalog.data.datasets;
  return (
    <>
      <PageHeading
        eyebrow="DELTA / KHÁM PHÁ DOANH NGHIỆP"
        title="Bắt đầu từ một doanh nghiệp."
        description="Tra cứu chỉ số tài chính của doanh nghiệp, rồi khám phá các nhóm cổ phiếu."
      />
      <button
        className="home-search"
        onClick={() => window.dispatchEvent(new Event("delta:search"))}
      >
        <Search size={24} />
        <span>Tìm mã hoặc tên doanh nghiệp…</span>
        <kbd>Ctrl K</kbd>
      </button>
      <div className="quick-tickers">
        <span>Tra cứu nhanh</span>
        {["FPT", "VNM", "HPG"].map((t) => (
          <Link key={t} href={`/stocks?ticker=${t}`}>
            {t}
            <ArrowUpRight size={14} />
          </Link>
        ))}
        <Link href="/financial?tab=coverage">Độ phủ chỉ số tài chính ↗</Link>
      </div>
      <section
        className="model-cards section-gap"
        aria-label="Ba mô hình tại kỳ cuối"
      >
        {(Object.keys(FAMILY) as Kind[]).map((kind) => (
          <Link
            className="model-card"
            key={kind}
            href={`/atlas?kind=${kind}&date=${d[kind].latest.date}`}
          >
            <div>
              <Badge>
                {FAMILY[kind].letter} · {FAMILY[kind].label}
              </Badge>
              <ArrowUpRight size={18} />
            </div>
            <strong>{number(d[kind].latest.n)}</strong>
            <p>
              {kind === "market"
                ? "Cổ phiếu được phân nhóm theo hành vi giá"
                : kind === "financial"
                  ? "Doanh nghiệp được phân nhóm theo tài chính"
                  : "Cổ phiếu có cả dữ liệu giá và tài chính"}
            </p>
            <small>{dateLabel(d[kind].latest.date)}</small>
          </Link>
        ))}
      </section>
      <div className="grid-two section-gap">
        <Panel
          title="Cấu trúc kết hợp gần nhất"
          eyebrow={`Mô hình C · ${dateLabel(d.combined.latest.date)}`}
          action={
            <Link
              className="text-link"
              href={`/atlas?kind=combined&date=${d.combined.latest.date}`}
            >
              Khám phá ↗
            </Link>
          }
        >
          {state.error ? (
            <ErrorState message={state.error} retry={state.retry} />
          ) : !state.data ? (
            <Skeleton height={340} />
          ) : (
            <Scatter
              data={state.data}
              x={state.data.points.some((p) => p.features._map_x != null) ? "_map_x" : "mom_63"}
              y={state.data.points.some((p) => p.features._map_x != null) ? "_map_y" : "net_margin"}
              map={state.data.points.some((p) => p.features._map_x != null)}
              names={Object.fromEntries(state.data.profiles.map((pr) => [pr.cluster, pr.name]))}
              kind="combined"
              height={340}
              onSelect={(ticker) =>
                window.location.assign(
                  `/stocks?ticker=${encodeURIComponent(ticker)}&kind=combined&date=${d.combined.latest.date}`,
                )
              }
            />
          )}
          <p className="panel-note">
            Mỗi chấm là một cổ phiếu; chấm gần nhau là cổ phiếu giống nhau cả về giá lẫn tài chính.
            Bấm một chấm để mở trang cổ phiếu.
          </p>
        </Panel>
        <Panel title="Các nhóm cổ phiếu" eyebrow="Mô hình C · kỳ gần nhất">
          <div className="panel-body">
            {Object.entries(d.combined.latest.sizes).map(([id, n]) => (
              <Link
                className="size-row"
                key={id}
                href={`/atlas?kind=combined&date=${d.combined.latest.date}&cluster=${id}`}
              >
                <div>
                  <ClusterBadge
                    kind="combined"
                    id={Number(id)}
                    labels={Object.keys(d.combined.latest.sizes).map(Number)}
                  />
                  <strong>{number(n)} mã</strong>
                </div>
                {state.data?.profiles.find((pr) => pr.cluster === Number(id))?.name && (
                  <em className="cluster-name">{state.data.profiles.find((pr) => pr.cluster === Number(id))?.name}</em>
                )}
                <span className="size-track">
                  <i
                    style={{
                      width: `${(100 * n) / d.combined.latest.n}%`,
                      background: clusterColor(
                        Number(id),
                        Object.keys(d.combined.latest.sizes).map(Number),
                      ),
                    }}
                  />
                </span>
                <small>
                  {n < Math.max(10, Math.ceil(0.01 * d.combined.latest.n))
                    ? "Nhóm rất nhỏ · cần xem xét"
                    : `${number((100 * n) / d.combined.latest.n, 1)}% số mã`}
                </small>
              </Link>
            ))}
            <p className="warning-line section-gap">
              Nhóm là kết quả thống kê, không phải xếp hạng đầu tư.
            </p>
            <Link className="text-link" href="/lab?tab=quality">
              Đọc giới hạn và bằng chứng ↗
            </Link>
          </div>
        </Panel>
      </div>
      <p className="scope-note">
        Dữ liệu lịch sử, không phải giá trực tiếp. Báo cáo tài chính năm có thể công bố sau ngày giá được dùng.
      </p>
    </>
  );
}
