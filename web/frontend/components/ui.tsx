"use client";
import { AlertCircle, ArrowUpRight, Database, RefreshCw } from "lucide-react";
import Link from "next/link";
import { clusterColor, FAMILY } from "@/lib/format";
import type { Kind } from "@/lib/types";
export function Panel({
  title,
  eyebrow,
  action,
  children,
  className = "",
}: {
  title?: string;
  eyebrow?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {title && (
        <div className="panel-heading">
          <div>
            {eyebrow && <div className="eyebrow">{eyebrow}</div>}
            <h2>{title}</h2>
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </header>
  );
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function ClusterBadge({
  kind,
  id,
  labels,
}: {
  kind: Kind;
  id: number;
  labels?: number[];
}) {
  return (
    <span
      className="cluster-badge"
      style={{
        color: clusterColor(id, labels),
        background: `${clusterColor(id, labels)}13`,
      }}
    >
      <i style={{ background: clusterColor(id, labels) }} />
      {id < 0 ? "Chưa gán / noise" : `${FAMILY[kind].letter}${id}`}
    </span>
  );
}
export function FamilyTabs({
  value,
  onChange,
}: {
  value: Kind;
  onChange: (value: Kind) => void;
}) {
  return (
    <div className="segmented" role="group" aria-label="Nhóm mô hình">
      {(Object.keys(FAMILY) as Kind[]).map((kind) => (
        <button
          aria-pressed={kind === value}
          className={kind === value ? "active" : ""}
          key={kind}
          onClick={() => onChange(kind)}
        >
          <span className="family-letter">{FAMILY[kind].letter}</span>
          {FAMILY[kind].label}
        </button>
      ))}
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="state-box error">
      <AlertCircle size={22} />
      <h3>Không tải được dữ liệu</h3>
      <p>{message}</p>
      {retry && (
        <button className="button small" onClick={retry}>
          <RefreshCw size={14} />
          Thử lại
        </button>
      )}
    </div>
  );
}
export function EmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="state-box">
      <Database size={24} />
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}
export function Skeleton({ height = 320 }: { height?: number }) {
  return (
    <div
      aria-label="Đang tải dữ liệu nghiên cứu"
      className="skeleton"
      role="status"
      style={{ height }}
    >
      <div />
      <div />
      <div />
      <p className="loading-note">
        Đang tải dữ liệu đã lưu. Dịch vụ có thể cần khoảng một phút để khởi
        động.
      </p>
    </div>
  );
}
export function ScopeNote({ kind }: { kind: Kind }) {
  return (
    <div className="scope-note">
      <span className="scope-dot" />
      {kind === "market"
        ? "Nghiên cứu thị trường lịch sử · định danh chứng khoán còn tạm thời"
        : "Tham chiếu khám phá · báo cáo tài chính có thể công bố sau ngày thị trường · chưa bảo đảm PIT"}
    </div>
  );
}
export function FeatureLink({
  href,
  title,
  text,
  icon,
}: {
  href: string;
  title: string;
  text: string;
  icon: React.ReactNode;
}) {
  return (
    <Link href={href} className="feature-link">
      <span className="feature-icon">{icon}</span>
      <div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
      <ArrowUpRight size={18} />
    </Link>
  );
}
