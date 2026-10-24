"use client";
import { useEffect, useState } from "react";
import { localizePayload, vi } from "./vi";

export function url(
  path: string,
  params: Record<string, string | number | null | undefined> = {},
) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params))
    if (value !== null && value !== undefined && value !== "")
      search.set(key, String(value));
  return `/api/v2/${path}${search.size ? `?${search}` : ""}`;
}
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const [settledPath, setSettledPath] = useState<string | null>(null);
  useEffect(() => {
    if (!path) {
      setLoading(false);
      setData(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setData(null);
    fetch(path, { signal: controller.signal })
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok)
          throw new Error(
            typeof body.detail === "string"
              ? vi(body.detail)
              : "Không thể hoàn tất yêu cầu.",
          );
        return localizePayload(body as T);
      })
      .then((value) => {
        if (!controller.signal.aborted) {
          setData(value);
          setSettledPath(path);
          setLoading(false);
        }
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setError(reason.message || "Dịch vụ dữ liệu chưa sẵn sàng.");
          setSettledPath(path);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [path, revision]);
  const current = settledPath === path;
  return {
    data: current ? data : null,
    error: current ? error : null,
    loading: loading || (!!path && !current),
    retry: () => setRevision((x) => x + 1),
  };
}
export function useDebounced(value: string, delay = 250) {
  const [result, setResult] = useState(value);
  useEffect(() => {
    const timeout = setTimeout(() => setResult(value), delay);
    return () => clearTimeout(timeout);
  }, [value, delay]);
  return result;
}
