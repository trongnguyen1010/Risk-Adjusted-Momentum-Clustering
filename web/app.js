const app = document.querySelector("#app");
const form = document.querySelector("#ticker-form");
const input = document.querySelector("#ticker-input");
const badge = document.querySelector("#data-badge");
let current;

if (location.protocol === "file:") {
  badge.textContent = "Cần local server";
  const section = document.createElement("section"); section.className = "error";
  const eyebrow = document.createElement("div"); eyebrow.className = "eyebrow"; eyebrow.textContent = "CHƯA CHẠY API SERVER";
  const title = document.createElement("h1"); title.textContent = "Không mở index.html trực tiếp";
  const help = document.createElement("p"); help.className = "muted";
  help.textContent = "Hãy chạy lệnh serve trong README rồi mở http://127.0.0.1:8000/?ticker=FPT để CSS, JavaScript và dữ liệu hoạt động cùng nhau.";
  section.append(eyebrow, title, help); app.replaceChildren(section);
}

const fmtNumber = (value, digits = 2) => value == null ? "—" : new Intl.NumberFormat("vi-VN", {maximumFractionDigits: digits}).format(value);
const fmtPercent = (value) => value == null ? "—" : `${value >= 0 ? "+" : ""}${fmtNumber(value * 100)}%`;
const setText = (root, field, value) => { const node = root.querySelector(`[data-field="${field}"]`); if (node) node.textContent = value ?? "—"; };

function drawPriceChart(rows, days) {
  const host = document.querySelector("#price-chart");
  const data = days ? rows.slice(-days) : rows;
  if (data.length < 2) { host.innerHTML = '<div class="empty-state">Chưa đủ dữ liệu để vẽ biểu đồ.</div>'; return; }
  const width = 760, height = 270, pad = 34;
  const values = data.map(row => row.price).filter(value => value != null);
  const min = Math.min(...values), max = Math.max(...values), span = max - min || 1;
  const points = data.map((row, i) => `${pad + i * (width - pad * 2) / (data.length - 1)},${height - pad - (row.price - min) * (height - pad * 2) / span}`).join(" ");
  const area = `${pad},${height-pad} ${points} ${width-pad},${height-pad}`;
  host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Biểu đồ giá">
    <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f7b54" stop-opacity=".24"/><stop offset="1" stop-color="#0f7b54" stop-opacity="0"/></linearGradient></defs>
    <line class="axis" x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}"/><polygon class="area" points="${area}"/><polyline class="line" points="${points}"/>
    <text x="${pad}" y="${height-8}">${data[0].date}</text><text x="${width-pad}" y="${height-8}" text-anchor="end">${data.at(-1).date}</text><text x="${pad}" y="18">${fmtNumber(max,0)}</text><text x="${pad}" y="${height-pad-7}">${fmtNumber(min,0)}</text>
  </svg>`;
}

function renderUnavailable(node, state) {
  node.textContent = state?.reason || "Dữ liệu chưa sẵn sàng.";
}

function render(detail) {
  current = detail;
  const fragment = document.querySelector("#company-template").content.cloneNode(true);
  setText(fragment, "exchange", detail.company.exchange);
  setText(fragment, "ticker", detail.company.ticker);
  setText(fragment, "name", detail.company.name);
  setText(fragment, "description", detail.company.description || "Company profile sẽ được bổ sung sau khi source contract được duyệt.");
  setText(fragment, "price", fmtNumber(detail.quote?.price, 0));
  setText(fragment, "quote-date", detail.quote ? `Cập nhật ${detail.quote.as_of_date} · ${detail.quote.price_basis}` : "Không có dữ liệu");
  const changeNode = fragment.querySelector('[data-field="change"]');
  if (detail.quote) {
    changeNode.textContent = `${detail.quote.change >= 0 ? "+" : ""}${fmtNumber(detail.quote.change, 0)} (${fmtPercent(detail.quote.change_pct)})`;
    changeNode.classList.add(detail.quote.change >= 0 ? "positive" : "negative");
  }
  setText(fragment, "cluster-label", detail.cluster?.label || "Chưa có phân nhóm");
  setText(fragment, "cluster-id", detail.cluster?.cluster_id);
  setText(fragment, "cluster-date", detail.cluster ? `Snapshot ${detail.cluster.as_of_date} · ${detail.cluster.size ?? "—"} mã trong nhóm` : detail.cluster_state.reason);
  setText(fragment, "feature-date", detail.analytics.as_of_date ? `Snapshot ${detail.analytics.as_of_date}` : "");

  const peers = fragment.querySelector('[data-role="peers"]');
  (detail.cluster?.peers || []).forEach(ticker => {
    const link = document.createElement("a"); link.className = "chip"; link.href = `/?ticker=${encodeURIComponent(ticker)}`; link.textContent = ticker; peers.append(link);
  });
  if (!peers.children.length) peers.textContent = "Chưa có peer khả dụng.";

  const history = fragment.querySelector("#cluster-history");
  (detail.cluster?.history || []).forEach(row => {
    const bar = document.createElement("div"); bar.className = "cluster-bar"; bar.style.height = `${26 + (row.cluster_id + 1) * 12}px`; bar.title = `${row.date}: nhóm ${row.cluster_id}`; history.append(bar);
  });

  const labels = {mom_21:"Momentum 1T",mom_63:"Momentum 3T",mom_126:"Momentum 6T",mom_252:"Momentum 12T",vol_63:"Biến động 3T",vol_126:"Biến động 6T",downside_vol_63:"Downside vol",beta_126:"Beta",mdd_126:"Max drawdown"};
  const metrics = fragment.querySelector('[data-role="metrics"]');
  Object.entries(detail.analytics.values).forEach(([key,value]) => {
    const box = document.createElement("div"); box.className="metric";
    const label = document.createElement("span"); label.textContent = labels[key] || key;
    const number = document.createElement("strong"); number.textContent = key.startsWith("beta") ? fmtNumber(value) : fmtPercent(value);
    box.append(label, number); metrics.append(box);
  });

  const warnings = fragment.querySelector('[data-role="warnings"]');
  detail.quality.warnings.forEach(message => { const node=document.createElement("div"); node.className="warning"; node.textContent=message; warnings.append(node); });
  renderUnavailable(fragment.querySelector('[data-role="fundamentals-state"]'), detail.fundamentals.state);
  renderUnavailable(fragment.querySelector('[data-role="sentiment-state"]'), detail.sentiment.state);
  const dl = fragment.querySelector(".provenance");
  Object.entries(detail.provenance).forEach(([key,value]) => { const dt=document.createElement("dt"); dt.textContent=key; const dd=document.createElement("dd"); dd.textContent=value ?? "—"; dl.append(dt,dd); });

  app.replaceChildren(fragment);
  drawPriceChart(detail.market_history, 252);
  app.querySelectorAll("[data-days]").forEach(button => button.addEventListener("click", () => {
    app.querySelectorAll("[data-days]").forEach(item => item.classList.remove("active")); button.classList.add("active"); drawPriceChart(current.market_history, Number(button.dataset.days));
  }));
  badge.textContent = `Bundle ${detail.provenance.experiment_run_id || "không có model"}`;
  document.title = `${detail.company.ticker} · Delta Intelligence`;
}

async function load(ticker) {
  const symbol = String(ticker || "").trim().toUpperCase();
  if (!symbol) return;
  input.value = symbol;
  try {
    const response = await fetch(`/api/v1/companies/${encodeURIComponent(symbol)}`);
    if (!response.ok) throw new Error(`Không tìm thấy mã ${symbol} trong bundle hiện tại.`);
    render(await response.json());
    history.replaceState({}, "", `/?ticker=${encodeURIComponent(symbol)}`);
  } catch (error) {
    const section = document.createElement("section"); section.className = "error";
    const eyebrow = document.createElement("div"); eyebrow.className = "eyebrow"; eyebrow.textContent = "KHÔNG THỂ HIỂN THỊ";
    const title = document.createElement("h1"); title.textContent = error.message;
    const help = document.createElement("p"); help.className = "muted"; help.textContent = "Hãy chọn một mã đã có trong immutable product bundle.";
    section.append(eyebrow, title, help); app.replaceChildren(section);
  }
}

if (location.protocol !== "file:") {
  form.addEventListener("submit", event => { event.preventDefault(); load(input.value); });
  const requested = new URLSearchParams(location.search).get("ticker");
  fetch("/api/v1/companies").then(response => response.json()).then(catalog => load(requested || catalog.companies[0]?.ticker || "FPT")).catch(() => load(requested || "FPT"));
}
