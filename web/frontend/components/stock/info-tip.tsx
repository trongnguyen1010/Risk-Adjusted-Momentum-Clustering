"use client";
import { useId, useState } from "react";
import { Info } from "lucide-react";

/** (i) button with a one-sentence explanation; hover, focus or tap to open. */
export function InfoTip({ text, label }: { text: string; label: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <span
      className="info-tip"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
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
      {open && (
        <span role="tooltip" id={id} className="info-tip-body">
          {text}
        </span>
      )}
    </span>
  );
}
