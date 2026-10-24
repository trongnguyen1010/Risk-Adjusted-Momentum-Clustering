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
export function MembersTable({
  kind,
  date,
  onSelect,
  matrix,
}: {
  kind: Kind;
  date: string;
  onSelect: (s: string) => void;
  matrix?: { market: number; financial: number } | null;
}) {
  const [q, setQ] = useState(""),
    [exchange, setExchange] = useState(""),
    [cluster, setCluster] = useState("");
  const search = useDebounced(q);
  const [page, setPage] = useState(1),
    [sorting, setSorting] = useState<SortingState>([]),
    [visibility, setVisibility] = useState<VisibilityState>({});
  const catalog = useCatalog();
  useEffect(() => setPage(1), [search, exchange, cluster, kind, date, matrix]);
  const state = useApi<Members>(
    date
      ? url(`members/${kind}`, {
          date,
          q: search,
          exchange,
          cluster,
          page,
          page_size: 20,
          sort: sorting[0]?.id || "ticker",
          direction: sorting[0]?.desc ? "desc" : "asc",
          matrix_market: matrix?.market,
          matrix_financial: matrix?.financial,
        })
      : null,
  );
  const features = catalog.data?.datasets[kind].features || [];
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
          <ClusterBadge kind={kind} id={getValue() as number} />
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
    [kind, features, catalog.data, onSelect],
  );
  const table = useReactTable({
    data: state.data?.items || [],
    columns,
    state: { sorting, columnVisibility: visibility },
    onSortingChange: setSorting,
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
            {Array.from(
              { length: catalog.data?.datasets[kind].k || 3 },
              (_, i) => (
                <option value={i} key={i}>
                  Cụm {i}
                </option>
              ),
            )}
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
                onClick={() => setPage((p) => p - 1)}
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
                onClick={() => setPage((p) => p + 1)}
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
