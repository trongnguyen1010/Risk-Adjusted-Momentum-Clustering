"use client";
import { useMemo, useState, useEffect } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type VisibilityState,
} from "@tanstack/react-table";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
} from "lucide-react";
import { useApi, useDebounced, url } from "@/lib/api";
import { metric, number } from "@/lib/format";
import type { Kind, Members, Observation } from "@/lib/types";
import { useCatalog } from "./providers";
import { ClusterBadge, ErrorState, Skeleton, EmptyState } from "./ui";
import { useSelection } from "@/lib/selection";
export function MembersTable({
  kind,
  date,
  onSelect,
  matrix,
  clusterValue,
  onClusterChange,
  version: selectedVersion,
  matrixMarketVersion,
}: {
  kind: Kind;
  date: string;
  onSelect: (s: string) => void;
  matrix?: { market: number; financial: number } | null;
  clusterValue?: string;
  onClusterChange?: (value: string) => void;
  version?: string;
  matrixMarketVersion?: string;
}) {
  const selection = useSelection(kind);
  const q = selection.params.get("q") || "",
    exchange = selection.params.get("exchange") || "";
  const cluster = clusterValue ?? selection.params.get("cluster") ?? "";
  const page = Math.max(1, Number(selection.params.get("page")) || 1);
  const sorting: SortingState = selection.params.get("sort")
    ? [
        {
          id: selection.params.get("sort")!,
          desc: selection.params.get("direction") === "desc",
        },
      ]
    : [];
  const setQ = (q: string) => selection.set({ q: q || null, page: null });
  const setExchange = (exchange: string) =>
    selection.set({ exchange: exchange || null, page: null });
  const setCluster = (cluster: string) =>
    onClusterChange
      ? onClusterChange(cluster)
      : selection.set({ cluster: cluster || null, page: null });
  const search = useDebounced(q);
  const [visibility, setVisibility] = useState<VisibilityState>({});
  const catalog = useCatalog();
  const version =
    selectedVersion ||
    selection.params.get("version") ||
    catalog.data?.datasets[kind].version;
  const dataset = catalog.data
    ? [
        catalog.data.datasets[kind],
        ...(catalog.data.variants?.[kind] || []),
      ].find((d) => d.version === version)
    : undefined;
  const state = useApi<Members>(
    date
      ? url(`members/${kind}`, {
          date,
          version,
          q: search,
          exchange,
          cluster,
          page,
          page_size: 20,
          sort: sorting[0]?.id || "ticker",
          direction: sorting[0]?.desc ? "desc" : "asc",
          matrix_market: matrix?.market,
          matrix_financial: matrix?.financial,
          matrix_market_version: matrixMarketVersion,
        })
      : null,
  );
  const features = dataset?.features || [];
  const columns = useMemo<ColumnDef<Observation>[]>(
    () => [
      {
        id: "ticker",
        header: "Cổ phiếu",
        accessorKey: "ticker",
        cell: ({ row }) => (
          <button
            className="ticker-cell"
            onClick={() => onSelect(row.original.ticker)}
          >
            <span className="ticker-mini">
              {row.original.ticker.slice(0, 2)}
            </span>
            <span>
              <strong>{row.original.ticker}</strong>
              <small className="company-cell">{row.original.name}</small>
            </span>
          </button>
        ),
      },
      {
        accessorKey: "exchange",
        header: "Sàn",
        enableSorting: false,
        cell: ({ getValue }) => (
          <span className="exchange">{String(getValue() || "—")}</span>
        ),
      },
      {
        id: "cluster",
        header: "Cụm",
        accessorKey: "cluster",
        cell: ({ getValue }) => (
          <ClusterBadge
            kind={kind}
            id={getValue() as number}
            labels={Object.keys(
              dataset?.history.find((s) => s.date === date)?.sizes || {},
            ).map(Number)}
          />
        ),
      },
      ...features.map((key) => ({
        id: key,
        header: catalog.data?.metadata.definitions[key]?.label || key,
        accessorFn: (r: Observation) => r.features[key],
        cell: ({ getValue }: { getValue: () => unknown }) =>
          metric(getValue() as number | null, key),
      })),
    ],
    [kind, date, features, catalog.data, dataset, onSelect],
  );
  const table = useReactTable({
    data: state.data?.items || [],
    columns,
    state: {
      sorting,
      columnVisibility: {
        ...Object.fromEntries(features.slice(3).map((f) => [f, false])),
        ...visibility,
      },
    },
    onSortingChange: (updater) => {
      const next = typeof updater === "function" ? updater(sorting) : updater;
      selection.set({
        sort: next[0]?.id || null,
        direction: next[0]?.desc ? "desc" : "asc",
        page: null,
      });
    },
    onColumnVisibilityChange: setVisibility,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    manualPagination: true,
  });
  return (
    <div>
      <div className="table-toolbar">
        <label className="search-field">
          <Search size={14} />
          <input
            aria-label="Lọc cổ phiếu"
            placeholder="Tìm mã hoặc tên doanh nghiệp…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <div className="table-actions">
          <select
            aria-label="Lọc theo sàn"
            value={exchange}
            onChange={(e) => setExchange(e.target.value)}
          >
            <option value="">Tất cả các sàn</option>
            {["HOSE", "HNX", "UPCOM"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
          <select
            aria-label="Lọc theo cụm"
            value={cluster}
            onChange={(e) => setCluster(e.target.value)}
          >
            <option value="">Tất cả các cụm</option>
            {Object.keys(
              state.data?.snapshot.sizes ||
                catalog.data?.datasets[kind].history.find(
                  (s) => s.date === date,
                )?.sizes ||
                {},
            )
              .map(Number)
              .sort((a, b) => a - b)
              .map((i) => (
                <option value={i} key={i}>
                  Cụm {i}
                </option>
              ))}
          </select>
          <details className="columns-menu">
            <summary>
              <SlidersHorizontal size={12} />
              Cột hiển thị
            </summary>
            <div className="columns-popover">
              {table
                .getAllLeafColumns()
                .filter((c) => c.id !== "ticker")
                .map((c) => (
                  <label key={c.id}>
                    <input
                      type="checkbox"
                      checked={c.getIsVisible()}
                      onChange={c.getToggleVisibilityHandler()}
                    />
                    {String(c.columnDef.header)}
                  </label>
                ))}
            </div>
          </details>
        </div>
      </div>
      {state.error ? (
        <ErrorState message={state.error} retry={state.retry} />
      ) : !state.data ? (
        <Skeleton height={280} />
      ) : state.data.total === 0 ? (
        <EmptyState
          title="Không có cổ phiếu phù hợp"
          message="Điều chỉnh bộ lọc để khám phá dữ liệu tại thời điểm này."
        />
      ) : (
        <>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                {table.getHeaderGroups().map((g) => (
                  <tr key={g.id}>
                    {g.headers.map((h) => (
                      <th key={h.id}>
                        <button
                          disabled={!h.column.getCanSort()}
                          onClick={h.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            h.column.columnDef.header,
                            h.getContext(),
                          )}{" "}
                          {h.column.getIsSorted() === "asc"
                            ? "↑"
                            : h.column.getIsSorted() === "desc"
                              ? "↓"
                              : ""}
                        </button>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((r) => (
                  <tr key={r.id}>
                    {r.getVisibleCells().map((c) => (
                      <td key={c.id}>
                        {flexRender(c.column.columnDef.cell, c.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-footer">
            <span>
              {number(state.data.total)} cổ phiếu · chỉ gồm quan sát đã lưu
            </span>
            <div className="pagination">
              <button
                aria-label="Trang trước"
                className="icon-button"
                disabled={page <= 1}
                onClick={() => selection.set({ page: String(page - 1) })}
              >
                <ChevronLeft size={14} />
              </button>
              <span>
                {page} / {Math.ceil(state.data.total / 20)}
              </span>
              <button
                aria-label="Trang sau"
                className="icon-button"
                disabled={page * 20 >= state.data.total}
                onClick={() => selection.set({ page: String(page + 1) })}
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
