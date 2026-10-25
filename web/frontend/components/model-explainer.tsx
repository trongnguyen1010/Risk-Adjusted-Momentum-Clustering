"use client";
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { Dataset, Kind, Snapshot } from "@/lib/types";
import { FAMILY } from "@/lib/format";
import { groupFeatures } from "@/lib/feature-help";
import { InfoTip } from "@/components/stock/info-tip";

const PURPOSE: Record<Kind, string> = {
  market: "Gom các cổ phiếu có hành vi giá giống nhau trong cùng một tháng.",
  financial: "Gom các doanh nghiệp có báo cáo tài chính năm giống nhau (trừ ngân hàng, chứng khoán, bảo hiểm).",
  combined: "Gom cổ phiếu giống nhau ở cả hành vi giá cuối năm lẫn báo cáo tài chính cùng năm.",
};
const NAME: Record<Kind, string> = { market: "thị trường", financial: "tài chính", combined: "kết hợp" };

const num = (v: unknown) => (typeof v === "number" ? v.toLocaleString("vi-VN") : "—");
const pct = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? `${Math.round(v * 100)}%` : "—");

function Tile({ value, label, tip, tone }: { value: string; label: string; tip?: string; tone?: string }) {
  return (
    <div className={`model-tile ${tone || ""}`}>
      <strong>{value}</strong>
      <span>
        {label}
        {tip && <InfoTip label={label} text={tip} />}
      </span>
    </div>
  );
}

/**
 * Model summary for Atlas: four key numbers always visible, details on demand
 * (data used, how groups are made, how to read the map).
 */
export function ModelExplainer({ kind, dataset, snapshot }: { kind: Kind; dataset: Dataset; snapshot: Snapshot }) {
  const [open, setOpen] = useState(false);
  const m = snapshot.metrics as Record<string, unknown>;
  const algorithm = /PCA/.test(dataset.scaling) ? "PCA + K-Means" : "K-Means";
  const period = kind === "market" ? "mỗi tháng" : "mỗi năm";
  const illiquid = typeof m.illiquid_n === "number" ? m.illiquid_n : 0;
  const boundary = typeof m.boundary_share === "number" ? m.boundary_share : null;
  const groups = groupFeatures(dataset.features);
  return (
    <section className="model-summary" aria-label={`Tóm tắt mô hình ${FAMILY[kind].letter}`}>
      <div className="model-summary-head">
        <div>
          <h2>
            <span className="model-letter">{FAMILY[kind].letter}</span>
            Mô hình {NAME[kind]}
          </h2>
          <p>{PURPOSE[kind]}</p>
        </div>
        <button type="button" className="button ghost small" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          {open ? "Thu gọn" : "Mô hình hoạt động thế nào?"}
          <ChevronDown size={16} className={open ? "rotated" : ""} />
        </button>
      </div>
      <div className="model-tiles">
        <Tile value={`${dataset.k} nhóm`} label={`${algorithm}, cập nhật ${period}`} />
        {illiquid > 0 && (
          <>
            <Tile value={num(m.fitted_n ?? m.liquid_n)} label="mã có giao dịch dùng để học nhóm" />
            <Tile
              value={num(illiquid)}
              label="mã kém thanh khoản"
              tip={`${dataset.liquidity_filter || "Ít giao dịch"}\nKhông dùng để học nhóm, chỉ được xếp vào nhóm gần nhất.`}
            />
          </>
        )}
        {boundary !== null && (
          <Tile
            value={pct(1 - boundary)}
            label="mã thuộc rõ một nhóm"
            tip={`${pct(boundary)} số mã nằm sát ranh giới giữa hai nhóm.\nRanh giới giữa các nhóm là mềm, không sắc như phân ngành.`}
          />
        )}
        {dataset.stability_note && (
          <Tile value="Chưa ổn định" label="chỉ để tham khảo" tip={dataset.stability_note} tone="warn" />
        )}
      </div>
      {open && (
        <div className="model-detail">
          <div className="model-info-card">
            <h3>Dữ liệu dùng · {dataset.features.length} chỉ số</h3>
            {groups.map((g) => (
              <div className="feature-group" key={g.name}>
                <span className="feature-group-name">{g.name}</span>
                <div className="feature-chips">
                  {g.items.map((f) => (
                    <span className={`feature-chip${f.isNew ? " is-new" : ""}`} key={f.key}>
                      {f.label}
                      {f.isNew && <em>Mới</em>}
                      {f.help && <InfoTip label={f.label} text={f.help} />}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="model-info-card">
            <h3>Cách chia nhóm</h3>
            <ol>
              <li>Chuẩn hóa từng chỉ số và cắt bỏ giá trị cực đoan, để vài mã bất thường không kéo lệch nhóm.</li>
              <li>
                {algorithm} chia thành {dataset.k} nhóm{illiquid > 0 ? " chỉ trên các mã có giao dịch" : ""}, tính lại {period}.
              </li>
              {illiquid > 0 && <li>Mã kém thanh khoản được xếp vào nhóm có đặc điểm gần nhất và mang nhãn riêng.</li>}
            </ol>
          </div>
          <div className="model-info-card">
            <h3>Đọc kết quả</h3>
            <ul>
              <li>
                Bản đồ gộp {dataset.features.length} chỉ số thành 2 trục
                {typeof m.map_variance === "number" ? ` (giữ khoảng ${pct(m.map_variance)} thông tin)` : ""}.
              </li>
              <li>Chấm gần nhau là cổ phiếu giống nhau{illiquid > 0 ? "; chấm mờ là mã kém thanh khoản" : ""}.</li>
              <li>Nhóm ở mỗi kỳ được tính riêng; cùng tên nhóm ở hai kỳ không nhất thiết cùng thành viên.</li>
              <li>Nhóm chỉ mô tả dữ liệu lịch sử, không phải khuyến nghị mua bán.</li>
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
