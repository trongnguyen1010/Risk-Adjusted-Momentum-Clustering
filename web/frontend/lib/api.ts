"use client";
import { useEffect, useRef, useState } from "react";
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
// A full URL (including run/version/query) plus the catalog revision is the cache identity.
let revisionKey = "bootstrap";
let expectedBundle: string | undefined;
export function setApiRevision(value: string, bundle?: string) {
  expectedBundle = bundle;
  if (revisionKey !== value) {
    revisionKey = value;
    cache.clear();
  }
}
const cache = new Map<string, { value: unknown; expires: number }>();
const pending = new Map<
  string,
  { promise: Promise<unknown>; controller: AbortController; users: number }
>();
function acquire(path: string, force: boolean) {
  const key = `${revisionKey}:${path}`;
  if (force) cache.delete(key);
  const saved = cache.get(key);
  if (saved && saved.expires > Date.now())
    return { promise: Promise.resolve(saved.value), release() {} };
  let entry = pending.get(key);
  if (!entry || entry.controller.signal.aborted) {
    const controller = new AbortController();
    const timeout = setTimeout(
      () =>
        controller.abort(
          new Error("Dịch vụ chưa sẵn sàng sau 75 giây. Hãy thử lại."),
        ),
      75000,
    );
    const requestPath =
      expectedBundle && !/^\/api\/v2\/(catalog|health)(\?|$)/.test(path)
        ? `${path}${path.includes("?") ? "&" : "?"}revision=${encodeURIComponent(expectedBundle)}`
        : path;
    const promise = fetch(requestPath, { signal: controller.signal })
      .then(async (response) => {
        const body = await response.json().catch(() => ({
          detail:
            "Dịch vụ dữ liệu đang khởi động hoặc trả phản hồi không hợp lệ.",
        }));
        if (!response.ok)
          throw new Error(
            typeof body.detail === "string"
              ? vi(body.detail)
              : "Không thể hoàn tất yêu cầu.",
          );
        // Indicator endpoints already speak Vietnamese and carry codes (e.g.
        // sector_group=SECURITIES) that the legacy dictionary would rewrite.
        const value = /^\/api\/v2\/stocks\/[^/?]+\/(overview|fundamentals|scores|peers)/.test(path)
          ? body
          : localizePayload(body);
        if (cache.size >= 80) cache.delete(cache.keys().next().value!);
        cache.set(key, { value, expires: Date.now() + 300000 });
        return value;
      })
      .finally(() => {
        clearTimeout(timeout);
        if (pending.get(key)?.controller === controller) pending.delete(key);
      });
    entry = { promise, controller, users: 0 };
    pending.set(key, entry);
  }
  entry.users++;
  const used = entry;
  return {
    promise: used.promise,
    release() {
      used.users--;
      // Allow StrictMode's immediate resubscription without issuing a second request.
      setTimeout(() => {
        if (!used.users && pending.get(key) === used) used.controller.abort();
      }, 0);
    },
  };
}
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const retried = useRef(0);
  const [settledPath, setSettledPath] = useState<string | null>(null);
  useEffect(() => {
    if (!path) {
      setLoading(false);
      setData(null);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    setData(null);
    const force = revision > retried.current;
    retried.current = revision;
    const request = acquire(path, force);
    request.promise
      .then((value) => {
        if (active) {
          setData(value as T);
          setSettledPath(path);
          setLoading(false);
        }
      })
      .catch((reason) => {
        if (active) {
          setError(reason.message || "Dịch vụ dữ liệu chưa sẵn sàng.");
          setSettledPath(path);
          setLoading(false);
        }
      });
    return () => {
      active = false;
      request.release();
    };
  }, [path, revision]);
  const current = settledPath === path;
  return {
    data: current ? data : null,
    error: current ? error : null,
    loading: loading || (!!path && !current),
    retry: () => setRevision((x) => x + 1),
  };
}
/** Keep showing the last loaded value while a new request is in flight (`stale` = true meanwhile). */
export function useStale<T>(value: T | null) {
  const last = useRef<T | null>(null);
  if (value !== null) last.current = value;
  return { data: value ?? last.current, stale: value === null && last.current !== null };
}
export function useDebounced(value: string, delay = 250) {
  const [result, setResult] = useState(value);
  useEffect(() => {
    const timeout = setTimeout(() => setResult(value), delay);
    return () => clearTimeout(timeout);
  }, [value, delay]);
  return result;
}
