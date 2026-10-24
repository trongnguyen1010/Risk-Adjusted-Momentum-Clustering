"use client";
import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Play, Pause } from "lucide-react";
import { dateLabel } from "@/lib/format";
export function TimeMachine({
  dates,
  date,
  onChange,
}: {
  dates: string[];
  date: string;
  onChange: (v: string) => void;
}) {
  const [playing, play] = useState(false);
  const index = dates.indexOf(date);
  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => {
      if (index < 0 || index >= dates.length - 1) play(false);
      else onChange(dates[index + 1]);
    }, 1600);
    return () => clearTimeout(timer);
  }, [playing, index, dates, onChange]);
  return (
    <div className="date-controls">
      <button
        aria-label={playing ? "Dừng dòng thời gian" : "Phát dòng thời gian"}
        className="icon-button"
        onClick={() => play(!playing)}
      >
        {playing ? <Pause size={14} /> : <Play size={14} />}
      </button>
      <button
        className="icon-button"
        aria-label="Thời điểm trước"
        disabled={index <= 0}
        onClick={() => onChange(dates[index - 1])}
      >
        <ChevronLeft size={16} />
      </button>
      <select
        aria-label="Thời điểm dữ liệu"
        value={date}
        onChange={(e) => {
          play(false);
          onChange(e.target.value);
        }}
      >
        {dates.map((d) => (
          <option key={d} value={d}>
            {dateLabel(d)}
          </option>
        ))}
      </select>
      <button
        className="icon-button"
        aria-label="Thời điểm sau"
        disabled={index < 0 || index >= dates.length - 1}
        onClick={() => onChange(dates[index + 1])}
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
