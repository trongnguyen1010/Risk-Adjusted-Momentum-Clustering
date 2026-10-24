import type { Kind } from "./types";
export const COLORS = ["#2dd4bf", "#9c8cff", "#f4b860"];
export const FAMILY: Record<
  Kind,
  { label: string; letter: string; subtitle: string }
> = {
  market: {
    label: "Thị trường",
    letter: "A",
    subtitle: "Động lượng · rủi ro · thanh khoản",
  },
  financial: {
    label: "Tài chính",
    letter: "B",
    subtitle: "Nền tảng doanh nghiệp",
  },
  combined: {
    label: "Kết hợp",
    letter: "C",
    subtitle: "Tham chiếu thị trường × tài chính",
  },
};
export function number(value: number | null | undefined, digits = 0) {
  return value == null || !Number.isFinite(value)
    ? "—"
    : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: digits }).format(
        value,
      );
}
export function compact(value: number | null | undefined) {
  return value == null || !Number.isFinite(value)
    ? "—"
    : new Intl.NumberFormat("vi-VN", {
        notation: "compact",
        maximumFractionDigits: 2,
      }).format(value);
}
export function metric(value: number | null | undefined, field: string) {
  if (value == null || !Number.isFinite(value)) return "—";
  if (
    field.startsWith("mom_") ||
    [
      "gross_margin",
      "net_margin",
      "operating_cashflow_to_assets",
      "mdd_126",
    ].includes(field)
  )
    return `${number(value * 100, 2)}%`;
  if (field === "liquidity_21") return `₫${compact(value)}`;
  return number(value, 3);
}
export function dateLabel(value: string, short = false) {
  if (value.length === 4) return `Năm TC ${value}`;
  const parsed = new Date(`${value}T00:00:00Z`);
  if (!Number.isFinite(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("vi-VN", {
    day: short ? undefined : "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(parsed);
}
