"use client";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";

const WIDTH = 260;
const GAP = 8;

/**
 * (i) button with a one-sentence explanation; hover, focus or tap to open.
 * The bubble is portalled to <body> with fixed positioning so scrolling
 * tables, sticky columns and overflow:hidden panels cannot clip it.
 */
export function InfoTip({ text, label }: { text: string; label: string }) {
  const [open, setOpen] = useState(false);
  const [style, setStyle] = useState<React.CSSProperties>({});
  const button = useRef<HTMLButtonElement>(null);
  const id = useId();
  const place = useCallback(() => {
    const r = button.current?.getBoundingClientRect();
    if (!r) return;
    const width = Math.min(WIDTH, window.innerWidth - 2 * GAP);
    const left = Math.min(Math.max(GAP, r.left + r.width / 2 - width / 2), window.innerWidth - width - GAP);
    const below = r.bottom + GAP + 80 < window.innerHeight;
    setStyle(
      below
        ? { left, width, top: r.bottom + GAP }
        : { left, width, bottom: window.innerHeight - r.top + GAP },
    );
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
            {text}
          </span>,
          document.body,
        )}
    </span>
  );
}
