"use client";
import { useEffect, useRef } from "react";
import Link from "next/link";
import { X, ArrowUpRight } from "lucide-react";
import { useApi, url } from "@/lib/api";
import { metric } from "@/lib/format";
import { useSelection } from "@/lib/selection";
import { useCatalog } from "./providers";
import { ClusterBadge, ErrorState, Skeleton, ScopeNote } from "./ui";
import type { Kind, Stock } from "@/lib/types";
export function StockDrawer({
  ticker,
  kind,
  date,
  close,
}: {
  ticker: string;
  kind: Kind;
  date: string;
  close: () => void;
}) {
  const selection = useSelection(kind);
  const version = selection.dataset?.version;
  const state = useApi<Stock>(url(`stocks/${ticker}`, { kind, date, version }));
  const catalog = useCatalog();
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    ref.current?.focus();
    const fn = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key === "Tab" && ref.current) {
        const nodes = ref.current.querySelectorAll<HTMLElement>(
          'button,a[href],select,input,[tabindex="0"]',
        );
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (
          e.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === ref.current)
        ) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", fn);
    return () => {
      document.removeEventListener("keydown", fn);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [close]);
  return (
    <div className="drawer-backdrop" onClick={close}>
      <div
        className="stock-drawer"
        role="dialog"
        aria-modal="true"
        aria-label={`${ticker} chi tiết nghiên cứu`}
        tabIndex={-1}
        ref={ref}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-top">
          <div>
            <div className="eyebrow">Chi tiết cổ phiếu · {date}</div>
            <h2>{ticker}</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Đóng chi tiết"
            onClick={close}
          >
            <X size={18} />
          </button>
        </div>
        {state.error ? (
          <ErrorState message={state.error} />
        ) : !state.data ? (
          <Skeleton />
        ) : (
          <>
            <p className="drawer-sub">
              {state.data.security.name} · {state.data.security.exchange}
            </p>
            <ScopeNote kind={kind} />
            {state.data.current ? (
              <>
                <ClusterBadge
                  kind={kind}
                  id={state.data.current.cluster}
                  labels={Object.keys(state.data.current_snapshot.sizes).map(
                    Number,
                  )}
                />
                <div className="drawer-features">
                  {Object.entries(state.data.current.features).map(
                    ([key, v]) => (
                      <div className="feature-row" key={key}>
                        <span>
                          {catalog.data?.metadata.definitions[key]?.label ||
                            key}
                        </span>
                        <strong>{metric(v, key)}</strong>
                      </div>
                    ),
                  )}
                </div>
              </>
            ) : (
              <p>{state.data.current_missing_reason}</p>
            )}
            <Link
              className="button primary section-gap"
              href={`/stocks?ticker=${ticker}&kind=${kind}&date=${date}${version ? `&version=${encodeURIComponent(version)}` : ""}`}
            >
              Mở tra cứu cổ phiếu
              <ArrowUpRight size={14} />
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
