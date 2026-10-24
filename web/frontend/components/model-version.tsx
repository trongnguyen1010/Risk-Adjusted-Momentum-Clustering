"use client";
import type { Dataset } from "@/lib/types";
export function ModelVersion({
  options,
  value,
  onChange,
}: {
  options: Dataset[];
  value: string;
  onChange: (version: string) => void;
}) {
  if (options.length < 2) return null;
  return (
    <label className="select-label model-version">
      Phiên bản phân cụm
      <select
        aria-label="Phiên bản phân cụm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((d) => (
          <option key={d.version} value={d.version}>
            {d.label || "Baseline · frozen A/B/C"}
          </option>
        ))}
      </select>
    </label>
  );
}
export function PreviewNote({ dataset }: { dataset: Dataset | undefined }) {
  return dataset?.status === "NOT_PROMOTED" ? (
    <p className="cluster-diagnostic">
      <strong>{dataset.label}.</strong> Đây là research preview từ artifact R1
      đã kiểm chứng; chưa promote, chưa đóng source/peer usefulness review hoặc
      PIT. Baseline gốc vẫn chọn lại được.
    </p>
  ) : null;
}
