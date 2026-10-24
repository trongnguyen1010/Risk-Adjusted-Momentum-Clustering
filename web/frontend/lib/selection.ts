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
  const dataset = catalog.data?.datasets[kind];
  const date = params.get("date") || dataset?.latest.date || "";
  function set(values: Record<string, string | null>) {
    const next = new URLSearchParams(params.toString());
    Object.entries(values).forEach(([k, v]) =>
      v === null ? next.delete(k) : next.set(k, v),
    );
    router.replace(`${path}?${next}`, { scroll: false });
  }
  const invalidKind =
    raw !== null && !["market", "financial", "combined"].includes(raw);
  return {
    ...catalog,
    error: invalidKind ? "Nhóm mô hình trong URL không hợp lệ." : catalog.error,
    kind,
    date,
    dataset,
    params,
    set,
  };
}
