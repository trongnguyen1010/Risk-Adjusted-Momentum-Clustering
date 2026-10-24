"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowUpRight,
  Boxes,
  Check,
  ChevronRight,
  Command,
  FlaskConical,
  Layers3,
  LayoutDashboard,
  Menu,
  Search,
  Sparkles,
  Telescope,
  X,
} from "lucide-react";
import { useApi, useDebounced, url } from "@/lib/api";
import type { Security } from "@/lib/types";
import { useCatalog } from "./providers";
import { Badge } from "./ui";
const nav = [
  { href: "/", label: "Tổng quan", icon: LayoutDashboard, tag: "01" },
  { href: "/atlas", label: "Bản đồ phân cụm", icon: Telescope, tag: "02" },
  { href: "/stocks", label: "Tra cứu cổ phiếu", icon: Search, tag: "03" },
  { href: "/financial", label: "Góc nhìn tài chính", icon: Layers3, tag: "04" },
  { href: "/lab", label: "Phòng nghiên cứu", icon: FlaskConical, tag: "05" },
];
const steps = [
  {
    path: "/",
    title: "Toàn cảnh tập dữ liệu nghiên cứu",
    text: "Bắt đầu từ độ phủ dữ liệu và ba mô hình đã lưu. Mọi số liệu đều lấy từ kết quả nghiên cứu của project.",
  },
  {
    path: "/atlas?kind=market&date=2025-12-31",
    title: "Khám phá cấu trúc thị trường",
    text: "Di chuột lên cổ phiếu, chọn cụm rồi bấm một điểm để xem chi tiết. Các trục sử dụng đặc trưng thực tế.",
  },
  {
    path: "/stocks?ticker=FPT",
    title: "Theo dõi cổ phiếu qua thời gian",
    text: "Xem giá lịch sử điều chỉnh theo nhà cung cấp của FPT, cụm thị trường theo tháng và tham chiếu tài chính theo năm.",
  },
  {
    path: "/financial?year=2025",
    title: "Kết nối hai góc nhìn",
    text: "Ma trận đối chiếu cụm thị trường cuối năm với cùng năm tài chính. Bấm vào ô để xem cổ phiếu. Đây là tham chiếu sau kỳ báo cáo, chưa xác minh PIT.",
  },
  {
    path: "/lab",
    title: "Kiểm tra bằng chứng",
    text: "Xem cấu hình mô hình, định nghĩa đặc trưng, dấu vân tay dữ liệu và các điều kiện chưa hoàn tất.",
  },
];
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobile, setMobile] = useState(false);
  const [compact, setCompact] = useState(false);
  const [search, setSearch] = useState(false);
  const [step, setStep] = useState<number | null>(null);
  const { data } = useCatalog();
  const page = nav.find((n) => n.href === pathname)?.label || "Nghiên cứu";
  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const update = () => setCompact(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearch((x) => !x);
      }
      if (e.key === "Escape") setMobile(false);
    };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, []);
  useEffect(() => {
    setMobile(false);
  }, [pathname]);
  const move = (next: number) => {
    if (next >= steps.length) {
      setStep(null);
      return;
    }
    setStep(next);
    router.push(steps[next].path);
  };
  return (
    <div className="app-shell">
      {mobile && (
        <button
          className="mobile-backdrop"
          aria-label="Đóng menu"
          onClick={() => setMobile(false)}
        />
      )}
      <aside
        className={`sidebar ${mobile ? "expanded" : ""}`}
        inert={compact && !mobile}
      >
        <Link
          className="brand"
          href="/"
          aria-label="Trang chủ DELTA Intelligence"
        >
          <span className="brand-mark">
            <svg width="30" height="31" viewBox="0 0 30 31" fill="none">
              <path
                d="M15 2 29 27H20L15 18 10 27H1L15 2Z"
                fill="currentColor"
              />
              <path d="M15 9 21 20H9L15 9Z" fill="#0c1421" />
            </svg>
          </span>
          <span>
            DELTA<span className="brand-sub">INTELLIGENCE</span>
          </span>
        </Link>
        <div className="workspace-label">
          <span className="small-dot" />
          Không gian nghiên cứu <span className="version-tag">V1</span>
        </div>
        <div className="nav-label">KHÁM PHÁ</div>
        <nav>
          {nav.map(({ href, icon: Icon, label, tag }) => (
            <Link
              key={href}
              href={href}
              className={`nav-item ${pathname === href ? "selected" : ""}`}
              aria-current={pathname === href ? "page" : undefined}
            >
              <Icon size={18} strokeWidth={1.6} />
              <span>{label}</span>
              <span className="nav-index">{tag}</span>
            </Link>
          ))}
        </nav>
        <div className="nav-label source-title">CÁC NHÓM MÔ HÌNH</div>
        <Link href="/atlas?kind=market" className="source-link">
          <span className="source-letter teal">A</span>
          <span>
            Mô hình thị trường<small>84 thời điểm theo tháng</small>
          </span>
          <span className="small-dot teal" />
        </Link>
        <Link href="/atlas?kind=financial" className="source-link">
          <span className="source-letter purple">B</span>
          <span>
            Mô hình tài chính<small>10 năm tài chính</small>
          </span>
          <span className="small-dot purple" />
        </Link>
        <Link href="/atlas?kind=combined" className="source-link">
          <span className="source-letter amber">C</span>
          <span>
            Tham chiếu kết hợp<small>7 thời điểm theo năm</small>
          </span>
          <span className="small-dot amber" />
        </Link>
        <div className="sidebar-bottom">
          <div className="archive-box">
            <Boxes size={20} />
            <h3>Nghiên cứu từ bằng chứng.</h3>
            <p>
              Khám phá kết quả đã lưu. Không cung cấp giá trực tiếp hay khuyến
              nghị danh mục.
            </p>
            <Link href="/lab">
              Giới hạn nghiên cứu <ArrowUpRight size={13} />
            </Link>
          </div>
          <button className="tour-button" onClick={() => move(0)}>
            <Sparkles size={16} />
            Hướng dẫn khám phá
            <ArrowRight size={14} />
          </button>
          <div className="sidebar-footer">
            <span className="avatar">Δ</span>
            <div>
              DELTA Research<small>Cổ phiếu Việt Nam · dữ liệu lịch sử</small>
            </div>
            <Check size={14} />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button mobile-menu"
              aria-label="Mở menu"
              aria-expanded={mobile}
              onClick={() => setMobile((x) => !x)}
            >
              <Menu size={20} />
            </button>
            <span>Trạm nghiên cứu</span>
            <ChevronRight size={14} />
            <strong>{page}</strong>
          </div>
          <div className="topbar-actions">
            <Badge tone="subtle">
              <span className="small-dot" />
              Dữ liệu lịch sử
            </Badge>
            <button className="global-search" onClick={() => setSearch(true)}>
              <Search size={15} />
              <span>Tìm cổ phiếu</span>
              <kbd>⌘ K</kbd>
            </button>
          </div>
        </header>
        <main id="main-content" className="main-content">
          {children}
        </main>
        <footer className="page-footer">
          <span>
            <span className="small-dot" />
            Dữ liệu nghiên cứu chỉ đọc
          </span>
          <span>
            Dữ liệu đến ngày {data?.datasets.market.latest.date || "—"}
            <span className="footer-divider">/</span>DELTA · Phiên bản nghiên
            cứu
          </span>
        </footer>
      </div>
      <CommandSearch open={search} close={() => setSearch(false)} />
      {step !== null && (
        <aside className="guide-card" aria-label="Hướng dẫn khám phá">
          <div className="guide-top">
            <span>
              <Sparkles size={14} />
              HƯỚNG DẪN KHÁM PHÁ
            </span>
            <button
              className="icon-button"
              onClick={() => setStep(null)}
              aria-label="Đóng hướng dẫn"
            >
              <X size={16} />
            </button>
          </div>
          <h3>{steps[step].title}</h3>
          <p>{steps[step].text}</p>
          <div className="guide-bottom">
            <span>
              {step + 1} / {steps.length}
            </span>
            <div>
              {step > 0 && (
                <button
                  className="button ghost small"
                  onClick={() => move(step - 1)}
                >
                  Quay lại
                </button>
              )}
              <button
                className="button small primary"
                onClick={() => move(step + 1)}
              >
                {step === steps.length - 1 ? "Hoàn tất" : "Tiếp theo"}
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
function CommandSearch({ open, close }: { open: boolean; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [q, setQ] = useState("");
  const [index, setIndex] = useState(0);
  const router = useRouter();
  const debounced = useDebounced(q);
  const { data, loading, error } = useApi<{ items: Security[] }>(
    open ? url("search", { q: debounced, limit: 10 }) : null,
  );
  useEffect(() => {
    if (open) {
      dialog.current?.showModal();
      setTimeout(() => input.current?.focus(), 50);
    } else dialog.current?.close();
  }, [open]);
  useEffect(() => setIndex(0), [debounced]);
  const select = (ticker: string) => {
    close();
    router.push(`/stocks?ticker=${encodeURIComponent(ticker)}`);
  };
  return (
    <dialog
      ref={dialog}
      className="command-dialog"
      onClose={close}
      onClick={(e) => {
        if (e.target === dialog.current) close();
      }}
    >
      <div className="command-input">
        <Search size={21} />
        <input
          ref={input}
          aria-label="Tìm cổ phiếu"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Tìm mã hoặc tên doanh nghiệp…"
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setIndex((i) => Math.min(i + 1, (data?.items.length || 1) - 1));
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              setIndex((i) => Math.max(0, i - 1));
            }
            if (e.key === "Enter" && data?.items[index])
              select(data.items[index].ticker);
          }}
        />
        <button
          className="icon-button"
          aria-label="Đóng tìm kiếm"
          onClick={close}
        >
          <X size={18} />
        </button>
      </div>
      <div className="command-results">
        <div className="eyebrow">TẬP CỔ PHIẾU NGHIÊN CỨU</div>
        {loading ? (
          <p className="muted">Đang tìm kiếm…</p>
        ) : error ? (
          <p className="muted">{error}</p>
        ) : data?.items.length ? (
          data.items.map((s, i) => (
            <button
              key={s.ticker}
              className={`command-result ${i === index ? "highlighted" : ""}`}
              onClick={() => select(s.ticker)}
            >
              <span className="ticker-avatar">{s.ticker.slice(0, 2)}</span>
              <span>
                <strong>{s.ticker}</strong>
                <small>{s.name}</small>
              </span>
              <span className="exchange">{s.exchange}</span>
              <ArrowUpRight size={15} />
            </button>
          ))
        ) : (
          <p className="muted">Không tìm thấy cổ phiếu phù hợp.</p>
        )}
      </div>
      <div className="command-footer">
        <span>
          <kbd>↑</kbd>
          <kbd>↓</kbd> di chuyển <kbd>↵</kbd> mở
        </span>
        <span>
          <Command size={12} />
          Tập trung vào dữ liệu nghiên cứu.
        </span>
      </div>
    </dialog>
  );
}
