"use client";
import { useState, useCallback } from "react";
import { useSelection } from "@/lib/selection";
import { useApi, url } from "@/lib/api";
import { FAMILY, COLORS, number, metric, dateLabel } from "@/lib/format";
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
import { SnapshotMetrics } from "@/components/snapshot-metrics";
import { TimeMachine } from "@/components/time-machine";
import { Scatter } from "@/components/scatter";
import { MembersTable } from "@/components/members-table";
import { StockDrawer } from "@/components/stock-drawer";
import { Chart, baseChart, axis } from "@/components/chart";
export default function Atlas() {
  const s = useSelection();
  const [ticker, select] = useState<string | null>(null),
    [cluster, setCluster] = useState(""),
    [query, setQuery] = useState("");
  const close = useCallback(() => select(null), []);
  const features = s.dataset?.features || [];
  const x = s.params.get("x") || features[0] || "",
    y = s.params.get("y") || features[1] || "";
  const state = useApi<SnapshotData>(
    s.date ? url(`snapshots/${s.kind}`, { date: s.date }) : null,
  );
  const index = s.dataset?.dates.indexOf(s.date) ?? -1;
  const previous =
    s.params.get("from") || s.dataset?.dates[Math.max(0, index - 1)];
  const migration = useApi<Migration>(
    previous && s.date
      ? url(`migration/${s.kind}`, { source: previous, target: s.date })
      : null,
  );
  const symlog = s.params.get("scale") === "symlog";
  const profile = state.data?.profiles.find(
    (p) => p.cluster === Number(cluster || 0),
  );
  if (s.error) return <ErrorState message={s.error} />;
  if (!s.data || !s.dataset) return <Skeleton height={600} />;
  if (!features.includes(x) || !features.includes(y))
    return (
      <ErrorState message="Đặc trưng trên trục không hợp lệ. Chọn lại nhóm mô hình từ menu để đặt lại màn hình." />
    );
  return (
    <>
      <PageHeading
        eyebrow="CẤU TRÚC / KHÁM PHÁ"
        title="Bản đồ phân cụm"
        description="Khám phá cấu trúc tập cổ phiếu. Mỗi điểm là một quan sát đã lưu của một mã."
        action={<Badge tone="teal">{s.dataset.frequency}</Badge>}
      />
      <div className="toolbar">
        <FamilyTabs
          value={s.kind}
          onChange={(kind) => {
            setCluster("");
            s.set({
              kind,
              date: null,
              x: null,
              y: null,
              from: null,
              scale: null,
            });
          }}
        />
        <TimeMachine
          dates={s.dataset.dates}
          date={s.date}
          onChange={(date) => s.set({ date })}
        />
      </div>
      <ScopeNote kind={s.kind} />
      {s.kind === "market" && (
        <div className="cluster-diagnostic">
          <strong>Baseline A đang cần rà soát chất lượng.</strong> Nhãn được fit
          trên 8 đặc trưng, còn biểu đồ chỉ hiển thị 2 trục. Review 84 tháng cho
          thấy thanh khoản chiếm khoảng 99,997% phần tách tâm cụm (trung vị); vì
          vậy đổi sang trục thanh khoản sẽ nhìn tách rõ hơn. Đổi trục hoặc lấy
          log để hiển thị không đổi nhãn hay khắc phục sự chi phối này. A là
          nhóm hành vi thị trường, không phải nhóm sức khỏe tài chính.
        </div>
      )}
      {state.error ? (
        <ErrorState message={state.error} retry={state.retry} />
      ) : !state.data ? (
        <Skeleton height={480} />
      ) : (
        <>
          <div className="atlas-grid section-gap">
            <Panel
              title={`Không gian đặc trưng · ${FAMILY[s.kind].label}`}
              eyebrow={`${dateLabel(s.date)} · ${number(state.data.snapshot.n)} CỔ PHIẾU`}
              action={<Badge>{state.data.snapshot.k} cụm</Badge>}
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
                  <option value="symlog">Trục log1p có dấu</option>
                </select>
                <input
                  aria-label="Làm nổi bật mã trên biểu đồ"
                  placeholder="Làm nổi bật mã…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  style={{ width: 150, fontSize: 10 }}
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
                onSelect={select}
              />
              <div className="scatter-legend">
                <button
                  onClick={() => setCluster("")}
                  className={cluster === "" ? "teal" : "muted"}
                >
                  Tất cả các cụm
                </button>
                {state.data.profiles.map((p) => (
                  <button
                    key={p.cluster}
                    onClick={() => setCluster(String(p.cluster))}
                  >
                    <ClusterBadge kind={s.kind} id={p.cluster} />
                    <span>{number(p.size)}</span>
                  </button>
                ))}
              </div>
              <p className="panel-note">
                {symlog
                  ? "Display: sign(x) × ln(1 + |x|); tooltip retains raw values. No model transformation."
                  : "Tọa độ đặc trưng gốc."}{" "}
                Cuộn / chụm để thu phóng · bấm một điểm để xem chi tiết. Giữ
                nguyên giá trị cực đoan; đổi trục để xem nhóm bị nén.
              </p>
            </Panel>
            <Panel
              title="Hồ sơ cụm"
              eyebrow="THÀNH VIÊN ĐÃ LƯU · THỐNG KÊ MÔ TẢ"
            >
              <div className="panel-body">
                <select
                  aria-label="Chọn cụm xem hồ sơ"
                  className="profile-select"
                  value={cluster || "0"}
                  onChange={(e) => setCluster(e.target.value)}
                >
                  {state.data.profiles.map((p) => (
                    <option key={p.cluster} value={p.cluster}>
                      {FAMILY[s.kind].letter}
                      {p.cluster} · {number(p.size)} cổ phiếu
                    </option>
                  ))}
                </select>
                <div className="profile-big">
                  {number(profile?.size)}
                  <small>cổ phiếu trong cụm đã chọn</small>
                </div>
                {profile &&
                  profile.size < Math.max(10, state.data.snapshot.n * 0.01) && (
                    <p className="warning-line">
                      Cụm rất nhỏ · cần kiểm tra ngoại lệ trước khi diễn giải.
                    </p>
                  )}
                <div className="feature-list">
                  {features.map((f) => (
                    <div className="feature-row" key={f}>
                      <span>
                        {s.data?.metadata.definitions[f]?.label || f}
                        <small>trung bình / trung vị</small>
                      </span>
                      <strong>
                        {metric(profile?.means[f], f)}
                        <small>{metric(profile?.medians[f], f)}</small>
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            </Panel>
          </div>
          <div className="grid-equal section-gap">
            <Panel
              title="So sánh các cụm"
              eyebrow="CÙNG ĐẶC TRƯNG · TRUNG BÌNH GỐC"
            >
              <Chart
                height={255}
                label={`Trung bình ${x} theo cụm`}
                option={{
                  ...baseChart,
                  xAxis: {
                    ...axis,
                    type: "category",
                    data: state.data.profiles.map(
                      (p) => `${FAMILY[s.kind].letter}${p.cluster}`,
                    ),
                  },
                  yAxis: { ...axis, type: "value" },
                  series: [
                    {
                      type: "bar",
                      barMaxWidth: 60,
                      data: state.data.profiles.map((p) => ({
                        value: p.means[x],
                        itemStyle: { color: COLORS[p.cluster] },
                      })),
                    },
                  ],
                }}
              />
              <p className="panel-note">
                {s.data.metadata.definitions[x]?.label} · giữ nguyên đơn vị;
                không so sánh trực tiếp các đơn vị khác nhau.
              </p>
            </Panel>
            <Panel
              title="Chuyển dịch thành viên"
              eyebrow="CĂN NHÃN THEO CẶP ĐỂ HIỂN THỊ"
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
                <ErrorState message={migration.error} />
              ) : !migration.data ? (
                <Skeleton height={240} />
              ) : (
                <>
                  <div className="migration-summary">
                    {[
                      ["Giao chung", migration.data.common],
                      ["Giữ cụm sau căn nhãn", migration.data.stayed],
                      [
                        "Thêm / rời nhóm",
                        `${migration.data.entered} / ${migration.data.exited}`,
                      ],
                    ].map(([label, n]) => (
                      <div key={label}>
                        <strong>{n}</strong>
                        <small>{label}</small>
                      </div>
                    ))}
                  </div>
                  <Chart
                    height={210}
                    label="Số cổ phiếu chuyển cụm sau khi căn nhãn đích"
                    option={{
                      ...baseChart,
                      tooltip: { ...baseChart.tooltip, renderMode: "richText" },
                      xAxis: {
                        ...axis,
                        type: "category",
                        data: Array.from(
                          { length: state.data.snapshot.k },
                          (_, i) => `Đích đã căn ${i}`,
                        ),
                      },
                      yAxis: {
                        ...axis,
                        type: "category",
                        data: Array.from(
                          { length: state.data.snapshot.k },
                          (_, i) => `Nguồn ${i}`,
                        ),
                      },
                      visualMap: {
                        show: false,
                        min: 0,
                        max: Math.max(
                          1,
                          ...migration.data.cells.map((c) => c.n),
                        ),
                        inRange: { color: ["#152938", "#26796d", "#4ee1bb"] },
                      },
                      series: [
                        {
                          type: "heatmap",
                          label: { show: true, color: "#eaf6f2" },
                          data: migration.data.cells.map((c) => [
                            c.target,
                            c.source,
                            c.n,
                          ]),
                        },
                      ],
                    }}
                  />
                  <p className="panel-note">
                    {migration.data.alignment} Ánh xạ nhãn đích:{" "}
                    {Object.entries(migration.data.mapping)
                      .map(([a, b]) => `${a}→${b}`)
                      .join(", ")}
                    .
                  </p>
                </>
              )}
            </Panel>
          </div>
          <SnapshotMetrics snapshot={state.data.snapshot} />
          <Panel
            className="section-gap"
            title="Thành viên tại thời điểm chọn"
            eyebrow="TÌM KIẾM · LỌC · SẮP XẾP · XEM CHI TIẾT"
          >
            <MembersTable kind={s.kind} date={s.date} onSelect={select} />
          </Panel>
        </>
      )}
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
