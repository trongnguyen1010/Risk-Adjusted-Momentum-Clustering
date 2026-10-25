/** Plain-language names, groups and one-line meanings for model features (Atlas). */
export interface FeatureHelp {
  label: string;
  group: string;
  help: string;
  isNew?: boolean;
}

export const FEATURE_HELP: Record<string, FeatureHelp> = {
  mom_21: { group: "Động lượng giá", label: "1 tháng", help: "Giá tăng/giảm bao nhiêu % trong 1 tháng (21 phiên)." },
  mom_63: { group: "Động lượng giá", label: "3 tháng", help: "Giá tăng/giảm bao nhiêu % trong 3 tháng (63 phiên)." },
  mom_126: { group: "Động lượng giá", label: "6 tháng", help: "Giá tăng/giảm bao nhiêu % trong 6 tháng (126 phiên)." },
  mom_252: { group: "Động lượng giá", label: "12 tháng", help: "Giá tăng/giảm bao nhiêu % trong 12 tháng (252 phiên)." },
  vol_63: { group: "Rủi ro", label: "Biến động", help: "Giá dao động mạnh hay yếu mỗi ngày, tính trên 63 phiên." },
  downside_vol_63: {
    group: "Rủi ro",
    label: "Biến động giảm",
    help: "Chỉ đo dao động ở các phiên giảm giá: phần biến động làm nhà đầu tư mất tiền.",
    isNew: true,
  },
  mdd_126: { group: "Rủi ro", label: "Sụt giảm tối đa", help: "Giá từng rơi sâu nhất bao nhiêu % từ đỉnh trong 126 phiên." },
  beta_126: { group: "Rủi ro", label: "Beta", help: "Cổ phiếu biến động mạnh hơn (>1) hay yếu hơn (<1) VN-Index." },
  liquidity_21: { group: "Thanh khoản", label: "Giá trị giao dịch", help: "Giá trị khớp lệnh trung bình mỗi ngày trong 21 phiên." },
  roe: { group: "Sinh lời", label: "ROE", help: "Lãi trên vốn chủ sở hữu." },
  roa: { group: "Sinh lời", label: "ROA", help: "Lãi trên tổng tài sản." },
  gross_margin: { group: "Biên lãi", label: "Biên lãi gộp", help: "Phần lãi gộp trên mỗi đồng doanh thu." },
  net_margin: { group: "Biên lãi", label: "Biên lãi ròng", help: "Phần lãi ròng trên mỗi đồng doanh thu." },
  debt_to_equity: { group: "Sức khỏe tài chính", label: "Nợ / VCSH", help: "Mức dùng nợ so với vốn chủ." },
  current_ratio: { group: "Sức khỏe tài chính", label: "Thanh toán hiện hành", help: "Tài sản ngắn hạn đủ trả nợ ngắn hạn không." },
  asset_turnover: { group: "Hiệu quả & tăng trưởng", label: "Vòng quay tài sản", help: "Mỗi đồng tài sản tạo ra bao nhiêu doanh thu." },
  revenue_growth: { group: "Hiệu quả & tăng trưởng", label: "Tăng trưởng doanh thu", help: "Doanh thu tăng bao nhiêu % so với năm trước." },
  cfo_to_ni: { group: "Hiệu quả & tăng trưởng", label: "Dòng tiền / lợi nhuận", help: "Lợi nhuận có thu về thành tiền thật không." },
};

/** Features grouped in display order; unknown features fall into "Khác". */
export function groupFeatures(features: string[]) {
  const groups: { name: string; items: (FeatureHelp & { key: string })[] }[] = [];
  for (const key of features) {
    const help = FEATURE_HELP[key] || { group: "Khác", label: key, help: "" };
    let group = groups.find((g) => g.name === help.group);
    if (!group) groups.push((group = { name: help.group, items: [] }));
    group.items.push({ key, ...help });
  }
  return groups;
}

/** "Label trung vị X (chung: Y); ..." -> rows for tooltips and profile cards. */
export function storyRows(description?: string | null) {
  if (!description) return [];
  return description
    .replace(/\.$/, "")
    .split(/;\s+/)
    .map((part) => {
      const m = /^(.*) trung vị (.*) \(chung: (.*)\)$/.exec(part.trim());
      return m ? { label: m[1], value: m[2], base: m[3] } : { label: part.trim(), value: "", base: "" };
    });
}
