"use client";
import { useId, useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { Observation } from "@/lib/types";

/** Ticker search with suggestions (ticker prefix first, then company name). */
export function TickerFinder({
  points,
  onSelect,
  placeholder = "Tìm mã trên bản đồ…",
  className = "",
}: {
  points: Observation[];
  onSelect: (t: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const listId = useId();
  const needle = q.trim().toUpperCase();
  const hits = useMemo(() => {
    if (!needle) return [];
    const starts = points
      .filter((p) => p.ticker.startsWith(needle))
      .sort((a, b) => a.ticker.length - b.ticker.length || a.ticker.localeCompare(b.ticker));
    const named = points.filter((p) => !p.ticker.startsWith(needle) && (p.name || "").toUpperCase().includes(needle));
    return [...starts, ...named].slice(0, 8);
  }, [points, needle]);
  const pick = (t: string) => {
    onSelect(t);
    setQ("");
    setOpen(false);
  };
  return (
    <div className={`insp-find ${className}`}>
      <Search size={15} />
      <input
        role="combobox"
        aria-expanded={open && !!needle}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-label={placeholder}
        placeholder={placeholder}
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setActive(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((a) => Math.min(a + 1, hits.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((a) => Math.max(a - 1, 0));
          } else if (e.key === "Enter" && hits[active]) {
            e.preventDefault();
            pick(hits[active].ticker);
          } else if (e.key === "Escape") setOpen(false);
        }}
      />
      {open && needle && (
        <ul className="insp-suggest" id={listId} role="listbox">
          {hits.length ? (
            hits.map((p, i) => (
              <li
                key={p.ticker}
                role="option"
                aria-selected={i === active}
                onMouseEnter={() => setActive(i)}
                onMouseDown={(e) => {
                  e.preventDefault();
                  pick(p.ticker);
                }}
              >
                <b>{p.ticker}</b>
                <span>{p.name || ""}</span>
                <small>{p.exchange || ""}</small>
              </li>
            ))
          ) : (
            <li className="empty">Không có mã này trong mô hình đang xem</li>
          )}
        </ul>
      )}
    </div>
  );
}
