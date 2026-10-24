"use client";
import { useCallback, useState } from "react";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { FAMILY, clusterColor, number, metric, dateLabel } from "@/lib/format";
import type { SnapshotData, Migration } from "@/lib/types";
import {
  Panel,
  PageHeading,
  FamilyTabs,
  ScopeNote,
  Skeleton,
  ErrorState,
  ClusterBadge,
  Badge,
} from "@/components/ui";
import { ModelVersion, PreviewNote } from "@/components/model-version";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { SavedPeers } from "@/components/saved-peers";
import { SnapshotMetrics } from "@/components/snapshot-metrics";
import { TimeMachine } from "@/components/time-machine";
import { Scatter } from "@/components/scatter";
import { MembersTable } from "@/components/members-table";
import { StockDrawer } from "@/components/stock-drawer";
import { Chart, baseChart, axis } from "@/components/chart";
const tabs = [
  ["explore", "Khám phá"],
  ["profiles", "Hồ sơ & đối chiếu"],
  ["members", "Thành viên"],
  ["quality", "Chất lượng"],
] as const;
export default function Atlas() {
  const s = useSelection();
  const tab = tabs.some(([id]) => id === s.params.get("tab"))
    ? s.params.get("tab")!
    : "explore";
  const cluster = s.params.get("cluster") || "";
  const ticker = s.params.get("ticker");
  const [query, setQuery] = useState("");
  const setCluster = (value: string) =>
    s.set({ cluster: value || null, page: null });
  const close = useCallback(
    () =>
      window.history.pushState(
        null,
        "",
        (() => {
          const p = new URLSearchParams(window.location.search);
          p.delete("ticker");
          return `${window.location.pathname}?${p}`;
        })(),
      ),
    [],
  );
  const features = s.dataset?.features || [];
  const preset =
    s.kind === "financial"
      ? ["net_margin", "liabilities_to_assets"]
      : s.kind === "combined"
        ? ["mom_63", "net_margin"]
        : ["mom_63", "vol_63"];
  const x = s.params.get("x") || preset[0],
    y = s.params.get("y") || preset[1];
  const state = useApi<SnapshotData>(
    s.date
      ? url(`snapshots/${s.kind}`, {
          date: s.date,
          version: s.dataset?.version,
        })
      : null,
  );
  const index = s.dataset?.dates.indexOf(s.date) ?? -1;
  const previous =
    s.params.get("from") || s.dataset?.dates[Math.max(0, index - 1)];
  const migration = useApi<Migration>(
    tab === "quality" && previous && s.date
      ? url(`migration/${s.kind}`, {
          source: previous,
          target: s.date,
          version: s.dataset?.version,
        })
      : null,
  );
  const symlog = s.params.get("scale") === "symlog";
  const profile = state.data?.profiles.find(
    (p) => cluster !== "" && p.cluster === Number(cluster),
  );
  if (s.error) return <ErrorState message={s.error} retry={s.retry} />;
  if (!s.data || !s.dataset) return <Skeleton height={600} />;
  if (!features.includes(x) || !features.includes(y))
    return (
      <ErrorState
        message="Trục trong URL không có trong model đang chọn. Đặt lại trục để tiếp tục."
        retry={() => s.set({ x: null, y: null })}
      />
    );
  return (
    <>
      <PageHeading
        eyebrow="CẤU TRÚC / NHÓM DOANH NGHIỆP"
        title="Bản đồ phân cụm"
        description="Chọn mô hình và kỳ, rồi chọn một nhóm để khám phá đặc điểm và thành viên."
        action={<Badge tone="amber">Exploratory · cần review</Badge>}
      />
      <div className="toolbar">
        <FamilyTabs
          value={s.kind}
          onChange={(kind) =>
            s.set({
              kind,
              date: null,
              x: null,
              y: null,
              from: null,
              scale: null,
              cluster: null,
              sort: null,
              direction: null,
              page: null,
              ticker: null,
            })
          }
        />
        <ModelVersion
          options={s.options}
          value={s.dataset.version}
          onChange={(version) =>
            s.set({ version, cluster: null, page: null, ticker: null })
          }
        />
        <TimeMachine
          dates={s.dataset.dates}
          date={s.date}
          onChange={(date) => s.set({ date, page: null, ticker: null })}
        />
      </div>
      <ScopeNote kind={s.kind} />
      <PreviewNote dataset={s.dataset} />
      {s.kind === "market" && s.dataset.status !== "NOT_PROMOTED" && (
        <p className="cluster-diagnostic">
          A: liquidity_21 chiếm trung vị 99,997% phần tách centroid qua 84 tháng
          theo fitted metric. Đổi trục/log hiển thị không sửa geometry hoặc
          nhãn. Không tự kết luận input sai.
        </p>
      )}
      <WorkspaceTabs
        scope="atlas"
        tabs={tabs}
        value={tab}
        onChange={(tab) => s.set({ tab })}
      />
      <div id="atlas-panel" role="tabpanel" aria-labelledby={`atlas-${tab}`}>
        {state.error ? (
          <ErrorState message={state.error} retry={state.retry} />
        ) : !state.data ? (
          <Skeleton height={480} />
        ) : (
          <>
            <div className="size-bars" aria-label="Quy mô nhóm luôn hiển thị">
              <button
                className={cluster === "" ? "selected" : ""}
                onClick={() => setCluster("")}
              >
                Tất cả · {number(state.data.snapshot.n)} mã
              </button>
              {state.data.profiles.map((p) => (
                <button
                  key={p.cluster}
                  className={cluster === String(p.cluster) ? "selected" : ""}
                  onClick={() => setCluster(String(p.cluster))}
                >
                  <ClusterBadge
                    kind={s.kind}
                    id={p.cluster}
                    labels={Object.keys(state.data!.snapshot.sizes).map(Number)}
                  />
                  <strong>{number(p.size)}</strong>
                  <span className="size-track">
                    <i
                      style={{
                        width: `${(100 * p.size) / state.data!.snapshot.n}%`,
                        background: clusterColor(
                          p.cluster,
                          Object.keys(state.data!.snapshot.sizes).map(Number),
                        ),
                      }}
                    />
                  </span>
                  <small>
                    {p.size <
                    Math.max(10, Math.ceil(state.data!.snapshot.n * 0.01))
                      ? "Nhóm rất nhỏ · cần xem xét"
                      : `${number((100 * p.size) / state.data!.snapshot.n, 1)}% cohort`}
                  </small>
                </button>
              ))}
            </div>
            {tab === "explore" && (
              <div className="atlas-grid section-gap">
                <Panel
                  title="Không gian đặc trưng"
                  eyebrow={`${dateLabel(s.date)} · ${number(state.data.snapshot.n)} MÃ · NHÃN GỐC`}
                >
                  <div className="atlas-toolbar">
                    <div className="axis-controls">
                      {[
                        ["Trục X", x, "x"],
                        ["Trục Y", y, "y"],
                      ].map(([label, value, key]) => (
                        <label className="select-label" key={key}>
                          {label}
                          <select
                            aria-label={label}
                            value={value}
                            onChange={(e) => s.set({ [key]: e.target.value })}
                          >
                            {features.map((f) => (
                              <option key={f} value={f}>
                                {s.data?.metadata.definitions[f]?.label || f}
                              </option>
                            ))}
                          </select>
                        </label>
                      ))}
                    </div>
                    <select
                      aria-label="Thang hiển thị biểu đồ"
                      value={symlog ? "symlog" : "raw"}
                      onChange={(e) => s.set({ scale: e.target.value })}
                    >
                      <option value="raw">Trục gốc</option>
                      <option value="symlog">
                        Log1p có dấu · chỉ hiển thị
                      </option>
                    </select>
                    <input
                      aria-label="Làm nổi bật mã trên biểu đồ"
                      placeholder="Làm nổi bật mã…"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>
                  <Scatter
                    data={state.data}
                    x={x}
                    y={y}
                    kind={s.kind}
                    selected={cluster}
                    query={query}
                    symlog={symlog}
                    onSelect={(ticker) => s.set({ ticker })}
                  />
                  <p className="panel-note">
                    Preset{" "}
                    {s.kind === "market"
                      ? "động lượng × biến động: so sánh hành vi và rủi ro"
                      : s.kind === "financial"
                        ? "biên lợi nhuận × nợ/tài sản: hai khía cạnh tài chính"
                        : "động lượng × biên lợi nhuận: đối chiếu hai block"}
                    . Hai trục không đại diện chất lượng toàn model.{" "}
                    {symlog
                      ? "sign(x) × ln(1+|x|), tooltip giữ raw values; không transform model."
                      : "Giữ nguyên raw values và đơn vị."}
                  </p>
                  <button
                    className="button ghost"
                    onClick={() => s.set({ tab: "members" })}
                  >
                    Xem dữ liệu điểm bằng bảng ↗
                  </button>
                </Panel>
                <Panel
                  title="Hồ sơ nhóm đang chọn"
                  eyebrow="MEDIAN / IQR · RAW UNITS"
                >
                  <div className="panel-body">
                    <select
                      aria-label="Chọn cụm xem hồ sơ"
                      value={profile?.cluster ?? ""}
                      onChange={(e) => setCluster(e.target.value)}
                    >
                      <option value="">Tất cả · chọn nhóm để xem hồ sơ</option>
                      {state.data.profiles.map((p) => (
                        <option key={p.cluster} value={p.cluster}>
                          {FAMILY[s.kind].letter}
                          {p.cluster} · {number(p.size)} mã
                        </option>
                      ))}
                    </select>
                    {!profile && (
                      <p className="context-line">
                        Chọn một nhóm ở thanh quy mô hoặc menu này để xem
                        median/IQR. Biểu đồ và bảng thành viên dùng cùng lựa
                        chọn.
                      </p>
                    )}
                    {profile && (
                      <div className="profile-big">
                        {number(profile?.size)}
                        <small>
                          thành viên ·{" "}
                          {profile
                            ? `${FAMILY[s.kind].letter}${profile.cluster}`
                            : "Không có nhóm trong URL"}
                        </small>
                      </div>
                    )}
                    {profile &&
                      profile.size <
                        Math.max(
                          10,
                          Math.ceil(state.data.snapshot.n * 0.01),
                        ) && (
                        <p className="warning-line">
                          Nhóm rất nhỏ · cần xem xét; chưa phải anomaly.
                        </p>
                      )}
                    {profile &&
                      [x, y]
                        .filter((f, i, a) => a.indexOf(f) === i)
                        .map((f) => (
                          <div className="feature-row" key={f}>
                            <span>
                              {s.data?.metadata.definitions[f]?.label}
                              <small>Trung vị / Q1–Q3</small>
                            </span>
                            <strong>
                              {metric(profile?.medians[f], f)}
                              <small>
                                {metric(profile?.quartiles[f]?.[1], f)} —{" "}
                                {metric(profile?.quartiles[f]?.[3], f)}
                              </small>
                            </strong>
                          </div>
                        ))}
                    <button
                      className="text-link"
                      onClick={() => s.set({ tab: "profiles" })}
                    >
                      Xem toàn bộ hồ sơ ↗
                    </button>
                  </div>
                </Panel>
              </div>
            )}
            {tab === "profiles" && (
              <Panel
                className="section-gap"
                title="Hồ sơ và đối chiếu các nhóm"
                eyebrow="COHORT CÙNG MODEL / KỲ · RAW UNITS"
                action={
                  <select
                    aria-label="Đặc trưng đối chiếu"
                    value={x}
                    onChange={(e) => s.set({ x: e.target.value })}
                  >
                    {features.map((f) => (
                      <option key={f} value={f}>
                        {s.data?.metadata.definitions[f]?.label}
                      </option>
                    ))}
                  </select>
                }
              >
                <Chart
                  height={340}
                  label={`Min, Q1, median, Q3, max của ${x} theo cụm. Bảng phía dưới cung cấp cùng thông tin.`}
                  option={{
                    ...baseChart,
                    tooltip: { ...baseChart.tooltip, renderMode: "richText" },
                    xAxis: {
                      ...axis,
                      type: "category",
                      data: state.data.profiles.map(
                        (p) => `${FAMILY[s.kind].letter}${p.cluster}`,
                      ),
                    },
                    yAxis: { ...axis, type: "value", scale: true },
                    series: [
                      {
                        type: "boxplot",
                        data: state.data.profiles.map((p) => ({
                          value: p.quartiles[x] || [],
                          itemStyle: {
                            color:
                              clusterColor(
                                p.cluster,
                                Object.keys(state.data!.snapshot.sizes).map(
                                  Number,
                                ),
                              ) + "33",
                            borderColor: clusterColor(
                              p.cluster,
                              Object.keys(state.data!.snapshot.sizes).map(
                                Number,
                              ),
                            ),
                          },
                        })),
                      },
                    ],
                  }}
                />
                <p className="panel-note">
                  Mỗi biểu đồ chỉ có một feature và một đơn vị. Hộp là
                  Q1–median–Q3, hai đầu là min/max đã lưu, không phải Tukey
                  fences. Giá trị lớn không mặc định là tốt.
                </p>
                <div className="data-table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Đặc trưng</th>
                        {state.data.profiles.map((p) => (
                          <th key={p.cluster}>
                            {FAMILY[s.kind].letter}
                            {p.cluster} · median [Q1, Q3]
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {features.map((f) => (
                        <tr key={f}>
                          <th>{s.data?.metadata.definitions[f]?.label || f}</th>
                          {state.data!.profiles.map((p) => (
                            <td key={p.cluster}>
                              {metric(p.medians[f], f)}
                              <small className="block">
                                [{metric(p.quartiles[f]?.[1], f)},{" "}
                                {metric(p.quartiles[f]?.[3], f)}]
                              </small>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <details className="indicator-details">
                  <summary>Trung bình theo feature (thông tin bổ sung)</summary>
                  <div className="data-table-wrap">
                    <table className="data-table">
                      <tbody>
                        {features.map((f) => (
                          <tr key={f}>
                            <th>{s.data?.metadata.definitions[f]?.label}</th>
                            {state.data!.profiles.map((p) => (
                              <td key={p.cluster}>{metric(p.means[f], f)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              </Panel>
            )}
            {tab === "profiles" && (
              <SavedPeers
                key={`${s.kind}:${s.date}:${s.dataset.version}`}
                examples={state.data.peer_examples || []}
                onSelect={(ticker) => s.set({ ticker })}
              />
            )}
            {tab === "members" && (
              <Panel
                className="section-gap"
                title="Thành viên"
                eyebrow="CÙNG MODEL / KỲ / NHÃN · CHƯA CÓ KHOẢNG CÁCH PEER ĐƯỢC EXPORT"
              >
                <MembersTable
                  version={s.dataset.version}
                  kind={s.kind}
                  date={s.date}
                  clusterValue={cluster}
                  onClusterChange={setCluster}
                  onSelect={(ticker) => s.set({ ticker })}
                />
              </Panel>
            )}
            {tab === "quality" && (
              <>
                <SnapshotMetrics snapshot={state.data.snapshot} />
                <Panel
                  className="section-gap"
                  title="Chuyển dịch thành viên"
                  eyebrow="MAXIMUM OVERLAP · CHỈ CĂN NHÃN HIỂN THỊ"
                  action={
                    <select
                      aria-label="Thời điểm đối chiếu ban đầu"
                      value={previous}
                      onChange={(e) => s.set({ from: e.target.value })}
                    >
                      {s.dataset.dates.map((d) => (
                        <option key={d} value={d}>
                          {dateLabel(d)}
                        </option>
                      ))}
                    </select>
                  }
                >
                  {migration.error ? (
                    <ErrorState
                      message={migration.error}
                      retry={migration.retry}
                    />
                  ) : !migration.data ? (
                    <Skeleton />
                  ) : (
                    <>
                      <p className="panel-note">
                        Common {number(migration.data.common)} · entered{" "}
                        {number(migration.data.entered)} · exited{" "}
                        {number(migration.data.exited)} · stayed sau căn nhãn{" "}
                        {number(migration.data.stayed)}. Không xác lập cùng
                        trạng thái kinh tế.
                      </p>
                      <div className="data-table-wrap">
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>Nguồn · nhãn gốc</th>
                              <th>Đích · nhãn hiển thị</th>
                              <th>Thành viên</th>
                            </tr>
                          </thead>
                          <tbody>
                            {migration.data.cells.map((c) => (
                              <tr key={`${c.source}-${c.target}`}>
                                <td>{c.source}</td>
                                <td>{c.target}</td>
                                <td>{number(c.n)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="panel-note">
                        Đích gốc → nhãn hiển thị:{" "}
                        {Object.entries(migration.data.mapping)
                          .map(([a, b]) => `${a}→${b}`)
                          .join(", ")}
                        . Không đổi stored labels.
                      </p>
                    </>
                  )}
                </Panel>
                <p className="cluster-diagnostic">
                  Các diagnostics không có trong payload sẽ giữ trạng thái chưa
                  export. Baseline contribution / silhouette distribution chưa
                  có trong presentation bundle; không tính metric mới trong
                  browser. Xem saved metrics và quy mô cùng nhau; silhouette cao
                  không tự chứng minh peer grouping hữu ích.
                </p>
              </>
            )}
          </>
        )}
      </div>
      {ticker && (
        <StockDrawer
          ticker={ticker}
          kind={s.kind}
          date={s.date}
          close={close}
        />
      )}
    </>
  );
}
