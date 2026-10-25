"use client";
import { useRef } from "react";
import { X } from "lucide-react";
import type { StockFundamentals } from "@/lib/types";

/** All formulas plus the technical trail; the only place run ids appear. */
export function MethodDialog({ data }: { data: StockFundamentals | null }) {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <button type="button" className="text-link" onClick={() => dialog.current?.showModal()}>
        Cách tính
      </button>
      <dialog ref={dialog} className="method-dialog" aria-labelledby="method-title">
        <div className="method-head">
          <h2 id="method-title">Cách tính các chỉ số</h2>
          <button type="button" className="icon-button" aria-label="Đóng" onClick={() => dialog.current?.close()}>
            <X size={18} />
          </button>
        </div>
        {data ? (
          <>
            {data.groups.map((g) => (
              <section key={g.name}>
                <h3>{g.name}</h3>
                <dl>
                  {g.metrics.map((m) => (
                    <div key={m}>
                      <dt>{data.definitions[m].label}</dt>
                      <dd>{data.definitions[m].description}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
            <section>
              <h3>Quy ước</h3>
              <ul>
                <li>Số cổ phiếu = vốn góp cổ phiếu phổ thông / 10.000 đ.</li>
                <li>EBIT = lợi nhuận trước thuế + chi phí lãi vay.</li>
                <li>P/E, P/B dùng giá đóng cửa phiên cuối cùng của năm tài chính.</li>
                <li>Thiếu số liệu thì để trống, không điền 0 và không lấy năm khác thay.</li>
              </ul>
            </section>
            <section className="method-tech">
              <h3>Thông tin kỹ thuật</h3>
              <p>Bộ dữ liệu: {data.run_id || "—"}</p>
              <p>Giá: {data.price_basis || "—"}</p>
            </section>
          </>
        ) : (
          <p>Đang tải…</p>
        )}
      </dialog>
    </>
  );
}
