"""
Technical analysis: what is the PRICE and VOLUME doing?
All indicators are calculated with pandas. Pure Python - no Django needed.

Each signal is turned into a score between -1 (bearish) and +1 (bullish).
The weighted average of these scores is the "technical score".
"""
import numpy as np
import pandas as pd

WEIGHTS = {
    "trend": 0.20,       # Moving averages
    "macd": 0.20,        # MACD
    "rsi": 0.15,         # RSI
    "bollinger": 0.10,   # Bollinger Bands
    "bias": 0.10,        # BIAS (distance from average)
    "order_flow": 0.15,  # Buy vs sell pressure (order-book proxy)
    "footprint": 0.10,   # Volume footprint / volume profile
}

NAMES = {
    "trend": "Moving Averages (SMA 20 / 50)",
    "macd": "MACD (12, 26, 9)",
    "rsi": "RSI (14)",
    "bollinger": "Bollinger Bands (20, 2)",
    "bias": "BIAS (20-day)",
    "order_flow": "Order-flow pressure (order-book proxy)",
    "footprint": "Volume Footprint (Point of Control)",
}


# ------------------------------------------------------------------ indicators
def add_indicators(df):
    d = df.copy()
    c, h, l, v = d["Close"], d["High"], d["Low"], d["Volume"]

    # Moving averages
    d["SMA20"] = c.rolling(20).mean()
    d["SMA50"] = c.rolling(50).mean()

    # MACD
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    d["MACD"] = ema12 - ema26
    d["MACD_signal"] = d["MACD"].ewm(span=9, adjust=False).mean()
    d["MACD_hist"] = d["MACD"] - d["MACD_signal"]

    # RSI (Wilder's smoothing)
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.mask(avg_loss.eq(0) & avg_gain.gt(0), 100.0)  # only gains
    d["RSI"] = rsi.mask(avg_loss.eq(0) & avg_gain.eq(0), 50.0)  # no movement at all

    # Bollinger Bands
    std20 = c.rolling(20).std()
    d["BB_upper"] = d["SMA20"] + 2 * std20
    d["BB_lower"] = d["SMA20"] - 2 * std20

    # BIAS = % distance of price from its 20-day average
    d["BIAS"] = (c - d["SMA20"]) / d["SMA20"] * 100

    # Order-flow proxy: where did the candle close inside its range?
    # Close near the high -> buyers were stronger; near the low -> sellers.
    span = (h - l).replace(0, np.nan)
    clv = (((c - l) - (h - c)) / span).fillna(0.0)
    d["BuyVol"] = v * (1 + clv) / 2
    d["SellVol"] = v - d["BuyVol"]
    buy20 = d["BuyVol"].rolling(20).sum()
    sell20 = d["SellVol"].rolling(20).sum()
    d["FlowImbalance"] = (buy20 - sell20) / (buy20 + sell20).replace(0, np.nan)

    d["VolSMA20"] = v.rolling(20).mean()
    d["POC"] = rolling_poc(d)
    return d


def _profile(window, bins=20):
    lo, hi = float(window["Low"].min()), float(window["High"].max())
    if hi <= lo:
        hi = lo * 1.01 + 1e-9
    edges = np.linspace(lo, hi, bins + 1)
    typical = ((window["High"] + window["Low"] + window["Close"]) / 3).to_numpy()
    idx = np.clip(np.digitize(typical, edges) - 1, 0, bins - 1)
    vols = np.bincount(idx, weights=window["Volume"].to_numpy(dtype=float), minlength=bins)
    return edges, vols


def rolling_poc(d, lookback=60):
    """Point of Control = price level where the most volume traded (last 60 days)."""
    poc = np.full(len(d), np.nan)
    for i in range(lookback - 1, len(d)):
        edges, vols = _profile(d.iloc[i - lookback + 1: i + 1])
        j = int(np.argmax(vols))
        poc[i] = (edges[j] + edges[j + 1]) / 2
    return pd.Series(poc, index=d.index)


def volume_profile(d, bins=20, lookback=60):
    """Volume footprint: how much volume traded at each price level."""
    edges, vols = _profile(d.tail(lookback), bins)
    centers = (edges[:-1] + edges[1:]) / 2
    j = int(np.argmax(vols))
    # Value area: price zone holding 70% of the volume
    chosen, total, cum = [], vols.sum(), 0.0
    for i in np.argsort(vols)[::-1]:
        chosen.append(int(i))
        cum += vols[i]
        if cum >= 0.7 * total:
            break
    return {
        "prices": [round(float(x), 2) for x in centers],
        "volumes": [float(x) for x in vols],
        "poc": round(float(centers[j]), 2),
        "value_area_low": round(float(edges[min(chosen)]), 2),
        "value_area_high": round(float(edges[max(chosen) + 1]), 2),
    }


def order_flow_summary(d, lookback=20):
    r = d.tail(lookback)
    buy, sell = float(r["BuyVol"].sum()), float(r["SellVol"].sum())
    total = buy + sell
    imbalance = (buy - sell) / total if total else 0.0
    return {
        "buy_pct": round(buy / total * 100, 1) if total else 50.0,
        "sell_pct": round(sell / total * 100, 1) if total else 50.0,
        "imbalance": round(imbalance, 3),
        "last_volume": float(d["Volume"].iloc[-1]),
        "avg_volume": float(d["VolSMA20"].iloc[-1]) if pd.notna(d["VolSMA20"].iloc[-1]) else None,
    }


# ------------------------------------------------------------------ scoring
def component_scores(d):
    """Score every indicator for every day (-1 bearish ... +1 bullish)."""
    c = d["Close"]
    s = pd.DataFrame(index=d.index)

    s["trend"] = np.select(
        [(c > d.SMA20) & (d.SMA20 > d.SMA50), (c < d.SMA20) & (d.SMA20 < d.SMA50), c > d.SMA50, c < d.SMA50],
        [1.0, -1.0, 0.4, -0.4], 0.0)
    s.loc[d.SMA50.isna(), "trend"] = np.nan

    hist, prev = d.MACD_hist, d.MACD_hist.shift(1)
    s["macd"] = np.select(
        [(hist > 0) & (hist > prev), hist > 0, (hist < 0) & (hist < prev), hist < 0],
        [1.0, 0.5, -1.0, -0.5], 0.0)
    s.loc[prev.isna() | d.index.isin(d.index[:35]), "macd"] = np.nan

    rsi = d.RSI
    s["rsi"] = np.where(rsi < 30, 1.0, np.where(rsi > 70, -1.0, (rsi - 50) / 40))
    s.loc[rsi.isna(), "rsi"] = np.nan

    width = (d.BB_upper - d.BB_lower).replace(0, np.nan)
    pctb = (c - d.BB_lower) / width
    s["bollinger"] = np.where(pctb < 0, 1.0, np.where(pctb > 1, -1.0, 0.5 - pctb))
    s.loc[pctb.isna(), "bollinger"] = np.nan

    s["bias"] = np.clip(-d.BIAS / 8, -1, 1)

    s["order_flow"] = np.clip(d.FlowImbalance * 4, -1, 1)

    surge = d.Volume > 1.5 * d.VolSMA20
    side = np.sign(c - d.POC)
    s["footprint"] = np.clip(side * np.where(surge, 1.0, 0.5), -1, 1)
    s.loc[d.POC.isna(), "footprint"] = np.nan
    return s


def composite_score(scores):
    """Weighted average of the available indicator scores."""
    w = np.array([WEIGHTS[k] for k in scores.columns])
    arr = scores.to_numpy(dtype=float)
    mask = ~np.isnan(arr)
    num = (np.nan_to_num(arr) * w).sum(axis=1)
    den = (mask * w).sum(axis=1)
    out = np.where(den >= 0.5, num / np.where(den == 0, 1, den), np.nan)
    return pd.Series(out, index=scores.index)


def label(score, threshold=0.15):
    if score is None or score != score:
        return "Neutral"
    return "Bullish" if score > threshold else ("Bearish" if score < -threshold else "Neutral")


def technical_signals(d, scores, profile, flow):
    """Human-readable explanation of the latest value of every indicator."""
    last = d.iloc[-1]
    sc = scores.iloc[-1]
    c = last.Close

    def f(x, n=2):
        return "N/A" if x is None or x != x else f"{x:,.{n}f}"

    rows = {
        "trend": (f"Price {f(c)} · SMA20 {f(last.SMA20)} · SMA50 {f(last.SMA50)}",
                  "Price above rising averages = uptrend; below falling averages = downtrend."),
        "macd": (f"MACD {f(last.MACD)} · Signal {f(last.MACD_signal)} · Hist {f(last.MACD_hist)}",
                 "MACD above its signal line and growing = momentum turning up."),
        "rsi": (f"RSI {f(last.RSI, 1)}",
                "Below 30 = oversold (may bounce). Above 70 = overbought (may pull back)."),
        "bollinger": (f"Upper {f(last.BB_upper)} · Lower {f(last.BB_lower)}",
                      "Price near the lower band is stretched down; near the upper band stretched up."),
        "bias": (f"BIAS {f(last.BIAS, 2)}%",
                 "Large positive BIAS = price far above its average (overheated)."),
        "order_flow": (f"Buy {flow['buy_pct']}% vs Sell {flow['sell_pct']}% (20 days)",
                       "Estimated from where each day closed within its high-low range. Real order-book (Level-2) data needs a paid broker feed."),
        "footprint": (f"POC {f(profile['poc'])} · Value area {f(profile['value_area_low'])}–{f(profile['value_area_high'])}",
                      "Price above the highest-volume level (POC) means buyers defend it as support."),
    }
    out = []
    for key, (value, note) in rows.items():
        v = sc[key]
        score = None if v != v else round(float(v), 2)
        out.append({"key": key, "name": NAMES[key], "value": value, "score": score,
                    "signal": label(score), "weight": int(WEIGHTS[key] * 100), "note": note})
    return out


def backtest(composite, close, horizon=5, threshold=0.15):
    """How often did the technical score's direction match the next 5 days' move?"""
    fwd = close.shift(-horizon) / close - 1
    valid = composite.notna() & fwd.notna() & (composite.abs() >= threshold)
    n = int(valid.sum())
    if n < 20:
        return {"samples": n, "hit_rate": None}
    hits = (np.sign(composite[valid]) == np.sign(fwd[valid])).mean()
    return {"samples": n, "hit_rate": round(float(hits) * 100, 1)}
