"use client";
import { useEffect, useState } from "react";
import type { Dataset, Definition, Kind, Profile, Snapshot } from "@/lib/types";
import { FAMILY } from "@/lib/format";

const PURPOSE: Record<Kind, string> = {
  market:
    "Chia cổ phiếu thành các nhóm có hành vi giá giống nhau trong cùng một tháng: đà tăng/giảm, mức biến động, độ nhạy với thị trường và thanh khoản.",
  financial:
    "Chia doanh nghiệp (trừ ngân hàng, chứng khoán, bảo hiểm) thành các nhóm có báo cáo tài chính năm giống nhau: sinh lời, biên lãi, nợ, dòng tiền, tăng trưởng.",
  combined:
    "Kết hợp hành vi giá cuối năm với báo cáo tài chính cùng năm, mỗi phần nặng 50%, để tìm nhóm cổ phiếu giống nhau ở cả hai mặt.",
};

const pct = (v: unknown) =>
  typeof v === "number" && Number.isFinite(v) ? `${Math.round(v * 100)}%` : "—";

/** Plain-language explanation of the served model; numbers come from the snapshot. */
export function ModelExplainer({
  kind,
  dataset,
  snapshot,
  profiles,
  definitions,
}: {
  kind: Kind;
  dataset: Dataset;
  snapshot: Snapshot;
  profiles: Profile[];
  definitions: Record<string, Definition>;
}) {
  const m = snapshot.metrics as Record<string, unknown>;
  const algorithm = /PCA/.test(dataset.scaling) ? "PCA + K-Means" : "K-Means";
  const illiquid = typeof m.illiquid_n === "number" ? m.illiquid_n : 0;
  const boundary = typeof m.boundary_share === "number" ? m.boundary_share : null;
  const period = kind === "market" ? "mỗi tháng" : "mỗi năm";
  // Open on desktop, folded on phones (decided after mount to keep SSR markup stable).
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(window.matchMedia("(min-width: 681px)").matches), []);
  return (
    <details
      className="model-explainer"
      open={open}
      onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
    >
      <summary>Mô hình {FAMILY[kind].letter} hoạt động thế nào?</summary>
      <dl>
        <div>
          <dt>Mục đích</dt>
          <dd>{PURPOSE[kind]}</dd>
        </div>
        <div>
          <dt>Dữ liệu dùng</dt>
          <dd>{dataset.features.map((f) => definitions[f]?.label || f).join(" · ")}.</dd>
        </div>
        <div>
          <dt>Cách chia nhóm</dt>
          <dd>
            {algorithm} chia thành {dataset.k} nhóm, chạy lại {period}. Mỗi chỉ số được chuẩn hóa và cắt bỏ giá trị
            cực đoan để vài mã bất thường không kéo lệch nhóm.
            {illiquid > 0 &&
              ` Nhóm được học trên các mã có giao dịch; ${illiquid.toLocaleString("vi-VN")} mã kém thanh khoản được xếp vào nhóm gần nhất và có nhãn riêng.`}
          </dd>
        </div>
        {profiles.some((p) => p.name) && (
          <div>
            <dt>Các nhóm kỳ này</dt>
            <dd>
              <ul>
                {profiles.map((p) => (
                  <li key={p.cluster}>
                    <b>
                      {FAMILY[kind].letter}
                      {p.cluster} · {p.name}
                    </b>{" "}
                    — {p.description}
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        )}
        <div>
          <dt>Độ tin cậy</dt>
          <dd>
            {boundary !== null
              ? `${pct(1 - boundary)} số mã thuộc rõ một nhóm; ${pct(boundary)} nằm sát ranh giới giữa hai nhóm. Ranh giới giữa các nhóm là mềm, không sắc như phân ngành.`
              : "Ranh giới giữa các nhóm là mềm, không sắc như phân ngành."}
            {dataset.stability_note && ` ${dataset.stability_note}`}
          </dd>
        </div>
        <div>
          <dt>Cách đọc bản đồ</dt>
          <dd>
            Mỗi chấm là một cổ phiếu. Bản đồ gộp {dataset.features.length} chỉ số thành 2 trục
            {typeof m.map_variance === "number" ? ` (giữ khoảng ${pct(m.map_variance)} thông tin)` : ""}; chấm gần nhau
            là cổ phiếu giống nhau. Chấm mờ là mã kém thanh khoản.
          </dd>
        </div>
        <div>
          <dt>Lưu ý</dt>
          <dd>Nhóm chỉ mô tả, không phải khuyến nghị mua bán. Nhóm ở các kỳ khác nhau được tính độc lập.</dd>
        </div>
      </dl>
    </details>
  );
}
