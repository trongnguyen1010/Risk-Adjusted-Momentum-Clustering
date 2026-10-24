"use client";
import { useState } from "react";
/** Keep large tables out of the DOM until a reader explicitly opens them. */
export function LazyDetails({
  summary,
  children,
}: {
  summary: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <details
      className="indicator-details"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary>{summary}</summary>
      {open ? children : null}
    </details>
  );
}
