// =====================================================================
// StockWise charts (Chart.js 4)
//   - initDashboardCards(): small sparkline + next-week forecast per stock
//   - renderStockDetail(data): big charts on the stock page
// =====================================================================
const C = {
  green: "#22c55e", red: "#ef4444", blue: "#0ea5e9", gold: "#facc15",
  purple: "#a78bfa", grey: "#94a3b8", grid: "rgba(148,163,184,.12)",
};

if (window.Chart) {
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.borderColor = C.grid;
}

function fmt(n, d = 2) {
  if (n === null || n === undefined) return "–";
  return Number(n).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d });
}
function dirClass(direction) {
  return direction === "Likely Up" ? "sig-up" : direction === "Likely Down" ? "sig-down" : "sig-side";
}
function dirIcon(direction) {
  return direction === "Likely Up" ? "bi-arrow-up-right" : direction === "Likely Down" ? "bi-arrow-down-right" : "bi-arrow-left-right";
}

// History line + dashed forecast line + shaded forecast range
function priceWithForecast(canvas, dates, closes, path, opts = {}) {
  const futureDates = path.map((p) => p.date);
  const labels = dates.concat(futureDates);
  const pad = (arr, before, after) => Array(before).fill(null).concat(arr, Array(after).fill(null));
  const last = closes[closes.length - 1];
  const hist = pad(closes, 0, path.length);
  const mid = pad([last].concat(path.map((p) => p.mid)), closes.length - 1, 0);
  const hi = pad([last].concat(path.map((p) => p.high)), closes.length - 1, 0);
  const lo = pad([last].concat(path.map((p) => p.low)), closes.length - 1, 0);
  const up = path[path.length - 1].mid >= last;
  const fc = up ? C.green : C.red;

  const datasets = [
    { label: "Price", data: hist, borderColor: C.blue, borderWidth: opts.small ? 2 : 2.5, pointRadius: 0, tension: 0.25 },
    { label: "Forecast", data: mid, borderColor: fc, borderDash: [6, 4], borderWidth: 2, pointRadius: 0 },
    { label: "Range high", data: hi, borderColor: "transparent", pointRadius: 0, fill: "+1", backgroundColor: up ? "rgba(34,197,94,.15)" : "rgba(239,68,68,.15)" },
    { label: "Range low", data: lo, borderColor: "transparent", pointRadius: 0 },
  ];
  (opts.extra || []).forEach((ds) => datasets.push(Object.assign({ pointRadius: 0, borderWidth: 1.5, tension: 0.25 }, ds, { data: pad(ds.data, 0, path.length) })));

  return new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 600 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: !opts.small, labels: { filter: (i) => !i.text.startsWith("Range") } },
        tooltip: { enabled: !opts.small, filter: (i) => i.raw !== null && !i.dataset.label.startsWith("Range") },
      },
      scales: {
        x: { display: !opts.small, ticks: { maxTicksLimit: 8 }, grid: { display: false } },
        y: { display: !opts.small, grid: { color: C.grid } },
      },
    },
  });
}

// ---------------------------------------------------------------- dashboard + nifty 50
// Cards load only when they scroll into view, max 3 at a time,
// so 50 stocks don't hit Yahoo Finance all at once.
const cardQueue = [];
let activeLoads = 0;
const MAX_PARALLEL = 3;

function pumpQueue() {
  while (activeLoads < MAX_PARALLEL && cardQueue.length) {
    const card = cardQueue.shift();
    activeLoads++;
    loadCard(card).finally(() => { activeLoads--; pumpQueue(); });
  }
}

function enqueueCard(card) {
  if (card.dataset.queued) return;
  card.dataset.queued = "1";
  cardQueue.push(card);
  pumpQueue();
}

async function loadCard(card) {
  const body = card.querySelector(".card-body-js");
  try {
    const res = await fetch(card.dataset.api, { headers: { Accept: "application/json" } });
    let d;
    try { d = await res.json(); } catch (e) { throw new Error("Session expired — please log in again"); }
    if (!res.ok) throw new Error(d.error || "Failed to load");
    const p = d.prediction;
    const chg = d.change_pct >= 0 ? "up" : "down";
    card.dataset.direction = p.direction;
    body.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-1">
          <div>
            <div class="small text-muted-sw text-truncate" style="max-width:180px">${card.dataset.name || d.name}</div>
            <div class="price">${fmt(d.last_price)} <span class="small text-muted-sw">${d.currency}</span></div>
            <div class="small ${chg}">${d.change_pct >= 0 ? "+" : ""}${fmt(d.change_pct)}% today</div>
          </div>
          <span class="badge-signal ${dirClass(p.direction)}"><i class="bi ${dirIcon(p.direction)}"></i> ${p.direction}</span>
        </div>
        <div class="spark-wrap my-2"><canvas></canvas></div>
        <div class="d-flex justify-content-between small">
          <span class="text-muted-sw">Next week range</span>
          <span>${fmt(p.low)} – ${fmt(p.high)}</span>
        </div>
        <div class="d-flex justify-content-between small mt-1">
          <span class="text-muted-sw">Technical / Fundamental</span>
          <span><span class="badge-signal sig-${d.tech_label}">${d.tech_label}</span> · ${d.fund_label}</span>
        </div>
        ${d.is_demo ? '<div class="mt-2"><span class="badge demo-badge">DEMO DATA</span></div>' : ""}`;
    priceWithForecast(body.querySelector("canvas"), d.spark.dates, d.spark.close, p.path, { small: true });
    document.dispatchEvent(new CustomEvent("card-loaded", { detail: { card, data: d } }));
  } catch (err) {
    body.innerHTML = `<div class="text-danger small py-4"><i class="bi bi-exclamation-triangle"></i> ${err.message}
      <div><button type="button" class="btn btn-sm btn-outline-sw mt-2 retry-btn">Retry</button></div></div>`;
    body.querySelector(".retry-btn").addEventListener("click", () => {
      delete card.dataset.queued;
      body.innerHTML = '<div class="skeleton mb-2" style="height:48px"></div><div class="skeleton" style="height:120px"></div>';
      enqueueCard(card);
    });
  }
}

function initDashboardCards() {
  const cards = document.querySelectorAll("[data-stock-card]");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { io.unobserve(e.target); enqueueCard(e.target); }
      });
    }, { rootMargin: "300px" });
    cards.forEach((c) => io.observe(c));
  } else {
    cards.forEach(enqueueCard);
  }
}

// ---------------------------------------------------------------- stock page
function renderStockDetail(d) {
  const ch = d.chart;

  priceWithForecast(document.getElementById("priceChart"), ch.dates, ch.close, d.prediction.path, {
    extra: [
      { label: "SMA 20", data: ch.sma20, borderColor: C.gold },
      { label: "SMA 50", data: ch.sma50, borderColor: C.purple },
      { label: "Bollinger upper", data: ch.bb_upper, borderColor: "rgba(148,163,184,.5)", borderDash: [3, 3] },
      { label: "Bollinger lower", data: ch.bb_lower, borderColor: "rgba(148,163,184,.5)", borderDash: [3, 3] },
    ],
  });

  const smallOpts = (extra = {}) => Object.assign({
    responsive: true, maintainAspectRatio: false, animation: { duration: 500 },
    interaction: { mode: "index", intersect: false },
    scales: { x: { ticks: { maxTicksLimit: 6 }, grid: { display: false } }, y: { grid: { color: C.grid } } },
  }, extra);

  // RSI with 30 / 70 lines
  new Chart(document.getElementById("rsiChart"), {
    type: "line",
    data: {
      labels: ch.dates,
      datasets: [
        { label: "RSI", data: ch.rsi, borderColor: C.blue, pointRadius: 0, borderWidth: 2 },
        { label: "Overbought 70", data: ch.dates.map(() => 70), borderColor: "rgba(239,68,68,.6)", borderDash: [4, 4], pointRadius: 0, borderWidth: 1 },
        { label: "Oversold 30", data: ch.dates.map(() => 30), borderColor: "rgba(34,197,94,.6)", borderDash: [4, 4], pointRadius: 0, borderWidth: 1 },
      ],
    },
    options: smallOpts({ scales: { x: { ticks: { maxTicksLimit: 6 }, grid: { display: false } }, y: { min: 0, max: 100, grid: { color: C.grid } } } }),
  });

  // MACD
  new Chart(document.getElementById("macdChart"), {
    data: {
      labels: ch.dates,
      datasets: [
        { type: "bar", label: "Histogram", data: ch.macd_hist, backgroundColor: ch.macd_hist.map((v) => (v >= 0 ? "rgba(34,197,94,.6)" : "rgba(239,68,68,.6)")) },
        { type: "line", label: "MACD", data: ch.macd, borderColor: C.blue, pointRadius: 0, borderWidth: 2 },
        { type: "line", label: "Signal", data: ch.macd_signal, borderColor: C.gold, pointRadius: 0, borderWidth: 1.5 },
      ],
    },
    options: smallOpts(),
  });

  // Volume: estimated buying vs selling
  new Chart(document.getElementById("volumeChart"), {
    type: "bar",
    data: {
      labels: ch.dates,
      datasets: [
        { label: "Buy volume (est.)", data: ch.buy_vol, backgroundColor: "rgba(34,197,94,.65)", stack: "v" },
        { label: "Sell volume (est.)", data: ch.sell_vol, backgroundColor: "rgba(239,68,68,.65)", stack: "v" },
      ],
    },
    options: smallOpts({ scales: { x: { stacked: true, ticks: { maxTicksLimit: 6 }, grid: { display: false } }, y: { stacked: true, grid: { color: C.grid } } } }),
  });

  // Volume profile / footprint (horizontal bars)
  const pr = d.profile;
  new Chart(document.getElementById("profileChart"), {
    type: "bar",
    data: {
      labels: pr.prices.map((p) => fmt(p)),
      datasets: [{
        label: "Volume at price (60 days)",
        data: pr.volumes,
        backgroundColor: pr.prices.map((p) =>
          Math.abs(p - pr.poc) < 1e-6 ? C.gold : p >= pr.value_area_low && p <= pr.value_area_high ? "rgba(14,165,233,.7)" : "rgba(148,163,184,.35)"),
      }],
    },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { reverse: true, ticks: { autoSkip: true, maxTicksLimit: 10 } }, x: { display: false } },
    },
  });

  // BIAS
  new Chart(document.getElementById("biasChart"), {
    type: "bar",
    data: { labels: ch.dates, datasets: [{ label: "BIAS %", data: ch.bias, backgroundColor: ch.bias.map((v) => (v >= 0 ? "rgba(34,197,94,.55)" : "rgba(239,68,68,.55)")) }] },
    options: smallOpts({ plugins: { legend: { display: false } } }),
  });
}
