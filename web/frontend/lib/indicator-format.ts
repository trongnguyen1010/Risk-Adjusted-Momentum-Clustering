import type { CellStatus, IndicatorCell, MetricUnit } from "./types";

const vn = (value: number, digits: number) =>
  new Intl.NumberFormat("vi-VN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  }).format(value);

/** Value with its unit, vi-VN formatting. Missing values render as an em dash. */
export function formatMetric(
  value: number | null | undefined,
  unit: MetricUnit,
  metric = "",
  withUnit = true,
) {
  if (value == null || !Number.isFinite(value)) return "—";
  if (metric === "market_cap")
    return `${vn(value / 1e9, 0)}${withUnit ? " tỷ đ" : ""}`;
  switch (unit) {
    case "vnd":
      return `${vn(value, 0)}${withUnit ? " đ" : ""}`;
    case "percent":
      return `${vn(value * 100, 1)}%`;
    case "times":
      return `${vn(value, 2)}${withUnit ? " lần" : ""}`;
    case "points":
      return `${vn(value, 0)}/9`;
    default:
      return vn(value, 2);
  }
}

export function signedPercent(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value > 0 ? "+" : ""}${vn(value * 100, 2)}%`;
}

const SECTOR: Record<string, string> = {
  BANK: "ngân hàng",
  SECURITIES: "công ty chứng khoán",
  INSURANCE: "công ty bảo hiểm",
};

/** One short sentence explaining why a cell has no value. */
export function statusText(
  cell: IndicatorCell | undefined,
  year: number | string,
  sector?: string,
) {
  if (!cell) return `Chưa có báo cáo năm ${year}.`;
  const reasons: Record<CellStatus, string> = {
    OK: "",
    MISSING_INPUT:
      cell.reason === "NO_ANNUAL_REPORT"
        ? `Chưa có báo cáo năm ${year}.`
        : `Thiếu số liệu đầu vào năm ${year}.`,
    NOT_APPLICABLE: `Không áp dụng cho ${SECTOR[sector || ""] || "nhóm ngành này"}.`,
    NEGATIVE_EARNINGS: "Công ty lỗ nên không tính.",
    NEGATIVE_EQUITY: "Vốn chủ sở hữu âm nên không tính.",
    NO_PRICE: `Chưa có giá cuối năm ${year}.`,
  };
  return reasons[cell.status];
}

export function ratingTone(rating: string | null | undefined) {
  if (!rating) return "subtle";
  if (["Mạnh", "An toàn", "Bình thường"].includes(rating)) return "teal";
  if (["Trung bình", "Cảnh báo"].includes(rating)) return "amber";
  return "red";
}

/** Short unit hint for table row labels (cells omit the unit). */
export function unitHint(unit: string, metric = "") {
  if (metric === "market_cap") return "tỷ đ";
  return { vnd: "đ", percent: "%", times: "lần", points: "điểm", score: "điểm" }[unit] || "";
}
