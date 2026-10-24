"use client";
import { createContext, useContext } from "react";
import { useApi } from "@/lib/api";
import type { Catalog } from "@/lib/types";
const Context = createContext<ReturnType<typeof useApi<Catalog>> | null>(null);
export function Providers({ children }: { children: React.ReactNode }) {
  const value = useApi<Catalog>("/api/v2/catalog");
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useCatalog() {
  const value = useContext(Context);
  if (!value) throw new Error("Catalog provider missing");
  return value;
}
