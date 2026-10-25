"use client";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";
import { storyRows } from "@/lib/feature-help";

const WIDTH = 280;
const GAP = 8;

/** Split one stored sentence into readable lines: meaning, then "Công thức: …", one fact per line. */
export function tipLines(text: string) {
  const [meaning, formula] = text.split(/\.\s*=\s*/);
  const lines = meaning.split(/\n|;\s+/).map((l) => l.trim()).filter(Boolean);
  if (formula) lines.push(`Công thức: ${formula.replace(/\.$/, "")}`);
  return lines;
}

/**
 * (i) button with a short explanation; hover, focus or tap to open.
 * The bubble is portalled to <body> with fixed positioning so scrolling
 * tables, sticky columns and overflow:hidden panels cannot clip it.
 * `story` renders a cluster description as label / group value / overall rows.
 */
export function InfoTip({ text, label, story = false }: { text: string; label: string; story?: boolean }) {
  const [open, setOpen] = useState(false);
  const [style, setStyle] = useState<React.CSSProperties>({});
  const button = useRef<HTMLButtonElement>(null);
  const id = useId();
  const place = useCallback(() => {
    const r = button.current?.getBoundingClientRect();
    if (!r) return;
    const width = Math.min(WIDTH, window.innerWidth - 2 * GAP);
    const left = Math.min(Math.max(GAP, r.left + r.width / 2 - width / 2), window.innerWidth - width - GAP);
    const below = r.bottom + GAP + 120 < window.innerHeight;
    setStyle(below ? { left, width, top: r.bottom + GAP } : { left, width, bottom: window.innerHeight - r.top + GAP });
  }, []);
  useEffect(() => {
    if (!open) return;
    place();
    const close = () => setOpen(false);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [open, place]);
  const rows = story ? storyRows(text) : [];
  return (
    <span className="info-tip" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button
        ref={button}
        type="button"
        aria-label={`Giải thích ${label}`}
        aria-describedby={open ? id : undefined}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
      >
        <Info size={14} />
      </button>
      {open &&
        createPortal(
          <span role="tooltip" id={id} className="info-tip-body" style={style}>
            {story && rows.length ? (
              <>
                <span className="tip-title">{label}</span>
                {rows.map((r) => (
                  <span className="tip-row" key={r.label}>
                    <span>{r.label}</span>
                    <b>{r.value}</b>
                    {r.base && <small>chung {r.base}</small>}
                  </span>
                ))}
              </>
            ) : (
              tipLines(text).map((line, i) => (
                <span key={i} className={i === 0 ? "tip-line lead" : "tip-line"}>
                  {line}
                </span>
              ))
            )}
          </span>,
          document.body,
        )}
    </span>
  );
}
