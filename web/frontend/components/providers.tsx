"use client";
import { createContext, useContext, useLayoutEffect } from "react";
import { useApi, setApiRevision } from "@/lib/api";
import type { Catalog } from "@/lib/types";
const Context = createContext<ReturnType<typeof useApi<Catalog>> | null>(null);
export function Providers({ children }: { children: React.ReactNode }) {
  const value = useApi<Catalog>("/api/v2/catalog");
  useLayoutEffect(() => {
    if (value.data)
      setApiRevision(
        JSON.stringify([
          value.data.metadata.version,
          value.data.metadata.bundle_revision,
          value.data.metadata.generated_at,
          Object.values(value.data.datasets).map((d) => d.version),
        ]),
        value.data.metadata.bundle_revision,
      );
  }, [value.data]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useCatalog() {
  const value = useContext(Context);
  if (!value) throw new Error("Catalog provider missing");
  return value;
}
