"""
Market pulse: how world markets and every sector are moving.

  - World indices        (S&P 500, Nasdaq, FTSE, Nikkei, ...)
  - India sector indices (Nifty Bank, Nifty IT, Nifty Auto, ...)
  - Global sectors       (iShares Global sector ETFs = big companies worldwide per sector)
  - Commodities & currency (Gold, Crude oil, USD/INR)

All prices come from Yahoo Finance in ONE download (fast, no API key).
"""
import logging
import math

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("analysis")

GROUPS = [
    ("India", [
        ("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX"), ("^NSEBANK", "Nifty Bank"), ("^INDIAVIX", "India VIX"),
    ]),
    ("India sectors", [
        ("^CNXIT", "Nifty IT"), ("^CNXAUTO", "Nifty Auto"), ("^CNXPHARMA", "Nifty Pharma"),
        ("^CNXFMCG", "Nifty FMCG"), ("^CNXMETAL", "Nifty Metal"), ("^CNXENERGY", "Nifty Energy"),
        ("^CNXREALTY", "Nifty Realty"), ("^CNXINFRA", "Nifty Infra"), ("^CNXPSUBANK", "Nifty PSU Bank"),
        ("^CNXMEDIA", "Nifty Media"),
    ]),
    ("World indices", [
        ("^GSPC", "S&P 500 (US)"), ("^IXIC", "Nasdaq (US)"), ("^DJI", "Dow Jones (US)"),
        ("^FTSE", "FTSE 100 (UK)"), ("^GDAXI", "DAX (Germany)"), ("^N225", "Nikkei 225 (Japan)"),
        ("^HSI", "Hang Seng (HK)"), ("000001.SS", "Shanghai (China)"),
    ]),
    ("Global sectors", [
        ("IXN", "Technology"), ("IXG", "Financials"), ("IXJ", "Healthcare"), ("IXC", "Energy"),
        ("EXI", "Industrials"), ("MXI", "Materials"), ("RXI", "Consumer Discretionary"),
        ("KXI", "Consumer Staples"), ("IXP", "Communication"), ("JXI", "Utilities"),
    ]),
    ("Commodities & currency", [
        ("GC=F", "Gold"), ("SI=F", "Silver"), ("CL=F", "Crude oil (WTI)"), ("BZ=F", "Brent crude"),
        ("INR=X", "USD / INR"),
    ]),
]

ALL_SYMBOLS = [s for _, items in GROUPS for s, _ in items]


def _pct(series, days_back):
    """% change between the last close and the close `days_back` trading days earlier."""
    s = series.dropna()
    if len(s) <= days_back:
        return None
    old, new = float(s.iloc[-1 - days_back]), float(s.iloc[-1])
    if old == 0 or math.isnan(old) or math.isnan(new):
        return None
    return round((new / old - 1) * 100, 2)


def build_pulse(close):
    """close = DataFrame, one column per symbol, one row per day."""
    groups = []
    for title, items in GROUPS:
        rows = []
        for symbol, name in items:
            if symbol not in close.columns:
                continue
            s = close[symbol].dropna()
            if len(s) < 2:
                continue
            rows.append({
                "symbol": symbol,
                "name": name,
                "price": round(float(s.iloc[-1]), 2),
                "d1": _pct(s, 1),
                "w1": _pct(s, 5),
                "m1": _pct(s, min(21, len(s) - 1)),
            })
        if rows:
            groups.append({"title": title, "items": rows})
    return groups


def _download_close():
    import yfinance as yf

    data = yf.download(ALL_SYMBOLS, period="2mo", interval="1d", auto_adjust=True,
                       progress=False, threads=True, group_by="column")
    if data is None or data.empty:
        raise ValueError("no data returned")
    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
    return close


def _demo_close():
    rng = np.random.default_rng(42)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=45)
    cols = {}
    for i, s in enumerate(ALL_SYMBOLS):
        start = 100 + (i * 37) % 900
        cols[s] = start * np.exp(np.cumsum(rng.normal(0.0003, 0.012, len(idx))))
    return pd.DataFrame(cols, index=idx)


def market_pulse():
    key = f"pulse:v1:{int(settings.FORCE_DEMO_DATA)}"
    result = cache.get(key)
    if result is not None:
        return result
    try:
        if settings.FORCE_DEMO_DATA:
            close, demo = _demo_close(), True
        else:
            close, demo = _download_close(), False
        result = {"groups": build_pulse(close), "is_demo": demo, "error": ""}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Market pulse failed: %s", exc)
        result = {"groups": [], "is_demo": False, "error": f"Market data unavailable right now ({exc})."}
    cache.set(key, result, settings.ANALYSIS_CACHE_SECONDS if result["groups"] else 120)
    return result
