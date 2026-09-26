// =====================================================================
// StockWise news + market pulse
//   initMarketPulse(el)          - sector / world performance tiles
//   initDashboardNews(el)        - news tabs on the dashboard
//   loadNews(listEl, url)        - fetch news JSON and show it
// =====================================================================

// News comes from other websites, so NEVER insert it as raw HTML.
function esc(text) {
  const d = document.createElement("div");
  d.textContent = text == null ? "" : String(text);
  return d.innerHTML;
}

function timeAgo(iso) {
  if (!iso) return "";
  const secs = (Date.now() - new Date(iso).getTime()) / 1000;
  if (isNaN(secs)) return "";
  if (secs < 3600) return Math.max(1, Math.round(secs / 60)) + " min ago";
  if (secs < 86400) return Math.round(secs / 3600) + " h ago";
  return Math.round(secs / 86400) + " d ago";
}

function newsSkeleton() {
  return Array(4).fill('<div class="skeleton mb-3" style="height:64px"></div>').join("");
}

// ----- NLP sentiment helpers -----
const SENT = {
  positive: { cls: "sig-Bullish", icon: "bi-emoji-smile", text: "Positive" },
  negative: { cls: "sig-Bearish", icon: "bi-emoji-frown", text: "Negative" },
  neutral: { cls: "sig-Neutral", icon: "bi-emoji-neutral", text: "Neutral" },
};

function sentimentBadge(s) {
  if (!s) return "";
  const m = SENT[s.label] || SENT.neutral;
  return `<span class="badge-signal ${m.cls}" title="AI confidence ${Math.round(s.confidence * 100)}%">
            <i class="bi ${m.icon}"></i> ${m.text} ${Math.round(s.confidence * 100)}%</span>`;
}

function moodBar(d) {
  const m = d.mood;
  if (!m) return "";
  const pct = (n) => (n / m.count * 100).toFixed(0);
  const cls = m.label === "Positive" ? "sig-Bullish" : m.label === "Negative" ? "sig-Bearish" : "sig-Neutral";
  const isAI = d.sentiment_engine.startsWith("FinBERT");
  return `
    <div class="mood-box mb-3">
      <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
        <div><span class="small text-muted-sw">News mood</span>
          <span class="badge-signal ${cls} ms-1">${esc(m.label)} (${m.score >= 0 ? "+" : ""}${m.score.toFixed(2)})</span></div>
        <div class="small text-muted-sw">
          <i class="bi ${isAI ? "bi-cpu text-accent" : "bi-list-check"}"></i> Analysed by ${esc(d.sentiment_engine)}
        </div>
      </div>
      <div class="mood-bar">
        <span style="width:${pct(m.positive)}%" class="mb-pos"></span><span style="width:${pct(m.neutral)}%" class="mb-neu"></span><span style="width:${pct(m.negative)}%" class="mb-neg"></span>
      </div>
      <div class="d-flex gap-3 small mt-1">
        <span class="up">${m.positive} positive</span><span class="text-muted-sw">${m.neutral} neutral</span><span class="down">${m.negative} negative</span>
      </div>
      ${!isAI && d.sentiment_note ? `<div class="small text-muted-sw mt-1"><i class="bi bi-info-circle"></i> ${esc(d.sentiment_note)}</div>` : ""}
    </div>`;
}

async function loadNews(listEl, url) {
  listEl.innerHTML = newsSkeleton();
  try {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    let d;
    try { d = await res.json(); } catch (e) { throw new Error("Session expired — please log in again"); }
    if (!res.ok) throw new Error(d.error || "Failed to load news");
    if (!d.articles || !d.articles.length) throw new Error(d.error || "No news found right now.");

    const items = d.articles.map((a) => `
      <a class="news-item" href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">
        ${a.image ? `<img src="${esc(a.image)}" alt="" loading="lazy" onerror="this.remove()">` : '<div class="news-icon"><i class="bi bi-newspaper"></i></div>'}
        <div class="flex-grow-1">
          <div class="news-title">${esc(a.title)}</div>
          ${a.description ? `<div class="news-desc">${esc(a.description)}</div>` : ""}
          <div class="news-meta">${sentimentBadge(a.sentiment)} ${esc(a.source)}${a.source && a.published ? " · " : ""}${timeAgo(a.published)}</div>
        </div>
      </a>`).join("");

    const foot = `<div class="small text-muted-sw mt-2"><i class="bi bi-info-circle"></i>
      Source: ${esc(d.provider)}. ${esc(d.note || "")} Sentiment is the AI's reading of headlines and can be wrong. Headlines are information, not buy/sell tips.</div>`;
    listEl.innerHTML = moodBar(d) + items + foot;
    document.dispatchEvent(new CustomEvent("news-loaded", { detail: { el: listEl, data: d } }));
  } catch (err) {
    listEl.innerHTML = `<div class="text-muted-sw small py-3"><i class="bi bi-exclamation-triangle text-warning"></i> ${esc(err.message)}
      <div><button type="button" class="btn btn-sm btn-outline-sw mt-2">Retry</button></div></div>`;
    listEl.querySelector("button").addEventListener("click", () => loadNews(listEl, url));
  }
}

// ---------------------------------------------------------------- dashboard news tabs
function initDashboardNews(root) {
  const list = root.querySelector("[data-news-list]");
  const base = root.dataset.newsUrl;          // /api/news/
  const stockBase = root.dataset.stockNewsUrl; // /api/news/stock/SYMBOL/
  const sectorBox = root.querySelector("[data-sector-controls]");
  const stockBox = root.querySelector("[data-stock-controls]");
  const sectorSel = root.querySelector("#news-sector");
  const scopeBtns = root.querySelectorAll("[data-scope]");
  const stockSel = root.querySelector("#news-stock");
  let mode = "india", scope = "india";

  function refresh() {
    sectorBox.classList.toggle("d-none", mode !== "sector");
    stockBox.classList.toggle("d-none", mode !== "stock");
    let url;
    if (mode === "sector") url = `${base}?type=sector&sector=${encodeURIComponent(sectorSel.value)}&scope=${scope}`;
    else if (mode === "stock") url = stockBase.replace("SYMBOL", encodeURIComponent(stockSel.value));
    else url = `${base}?type=market&topic=${mode}`;
    loadNews(list, url);
  }

  root.querySelectorAll("[data-news-tab]").forEach((btn) => btn.addEventListener("click", () => {
    root.querySelectorAll("[data-news-tab]").forEach((b) => b.classList.remove("active-chip"));
    btn.classList.add("active-chip");
    mode = btn.dataset.newsTab;
    refresh();
  }));
  scopeBtns.forEach((btn) => btn.addEventListener("click", () => {
    scopeBtns.forEach((b) => b.classList.remove("active-chip"));
    btn.classList.add("active-chip");
    scope = btn.dataset.scope;
    refresh();
  }));
  sectorSel.addEventListener("change", refresh);
  stockSel.addEventListener("change", refresh);
  refresh();
}

// ---------------------------------------------------------------- market pulse tiles
function pulseColor(p) {
  if (p === null || p === undefined) return "rgba(148,163,184,.10)";
  const a = Math.min(Math.abs(p) / 3, 1) * 0.45 + 0.08;   // stronger colour for bigger moves
  return p >= 0 ? `rgba(34,197,94,${a})` : `rgba(239,68,68,${a})`;
}

async function initMarketPulse(root) {
  const body = root.querySelector("[data-pulse-body]");
  const btns = root.querySelectorAll("[data-period]");
  let period = "d1", data = null;

  function render() {
    body.innerHTML = data.groups.map((g) => `
      <div class="mb-3">
        <div class="small text-muted-sw text-uppercase fw-semibold mb-2">${esc(g.title)}</div>
        <div class="pulse-grid">
          ${g.items.map((it) => {
            const p = it[period];
            const txt = p === null || p === undefined ? "–" : (p >= 0 ? "+" : "") + p.toFixed(2) + "%";
            return `<div class="pulse-tile" style="background:${pulseColor(p)}" title="${esc(it.symbol)}">
                      <div class="pulse-name">${esc(it.name)}</div>
                      <div class="pulse-pct">${txt}</div>
                      <div class="pulse-price">${fmt(it.price)}</div>
                    </div>`;
          }).join("")}
        </div>
      </div>`).join("") +
      (data.is_demo ? '<span class="badge demo-badge">DEMO DATA</span>' : "");
  }

  btns.forEach((b) => b.addEventListener("click", () => {
    btns.forEach((x) => x.classList.remove("active-chip"));
    b.classList.add("active-chip");
    period = b.dataset.period;
    if (data) render();
  }));

  body.innerHTML = '<div class="skeleton" style="height:220px"></div>';
  try {
    const res = await fetch(root.dataset.url, { headers: { Accept: "application/json" } });
    data = await res.json();
    if (!data.groups || !data.groups.length) throw new Error(data.error || "Market data unavailable");
    render();
  } catch (err) {
    body.innerHTML = `<div class="text-muted-sw small"><i class="bi bi-exclamation-triangle text-warning"></i> ${esc(err.message)}</div>`;
  }
}
