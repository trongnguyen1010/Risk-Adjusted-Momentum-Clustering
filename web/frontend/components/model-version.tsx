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
      <strong>{dataset.label}.</strong> Bản thử nghiệm, chưa thay mô hình gốc;
      mô hình gốc vẫn chọn lại được.
    </p>
  ) : null;
}
