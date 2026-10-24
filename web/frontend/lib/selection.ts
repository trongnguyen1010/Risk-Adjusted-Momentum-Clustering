"use client";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCatalog } from "@/components/providers";
import type { Kind } from "./types";
export function useSelection(defaultKind: Kind = "market") {
  const params = useSearchParams(),
    router = useRouter(),
    path = usePathname();
  const catalog = useCatalog();
  const raw = params.get("kind");
  const kind: Kind =
    raw === "market" || raw === "financial" || raw === "combined"
      ? raw
      : defaultKind;
  const options = catalog.data
    ? [catalog.data.datasets[kind], ...(catalog.data.variants?.[kind] || [])]
    : [];
  const dataset =
    options.find((d) => d.version === params.get("version")) ||
    catalog.data?.datasets[kind];
  const date = params.get("date") || dataset?.latest.date || "";
  function set(values: Record<string, string | null>) {
    const next = new URLSearchParams(params.toString());
    if (catalog.data?.metadata.bundle_revision)
      next.set("revision", catalog.data.metadata.bundle_revision);
    const selectedKind = values.kind || kind;
    if (catalog.data?.datasets[selectedKind as Kind]) {
      const choices = [
        catalog.data.datasets[selectedKind as Kind],
        ...(catalog.data.variants?.[selectedKind as Kind] || []),
      ];
      next.set(
        "version",
        choices.find((d) => d.version === dataset?.version)?.version ||
          catalog.data.datasets[selectedKind as Kind].version,
      );
    }
    Object.entries(values).forEach(([k, v]) =>
      v === null ? next.delete(k) : next.set(k, v),
    );
    router.push(`${path}?${next}`, { scroll: false });
  }
  const invalidKind =
    raw !== null && !["market", "financial", "combined"].includes(raw);
  const invalidRevision = !!(
    catalog.data &&
    params.get("revision") &&
    params.get("revision") !== catalog.data.metadata.bundle_revision
  );
  const invalidVersion = !!(
    dataset &&
    params.get("version") &&
    !options.some((d) => d.version === params.get("version"))
  );
  return {
    ...catalog,
    error: invalidKind
      ? "Nhóm mô hình trong URL không hợp lệ."
      : invalidRevision || invalidVersion
        ? "Phiên bản trong liên kết khác với gói dữ liệu đang được phục vụ. Không thay thế bằng model/nhãn khác; hãy mở lại workspace từ Tổng quan."
        : catalog.error,
    kind,
    date,
    dataset,
    options,
    params,
    set,
  };
}
