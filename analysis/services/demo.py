"""
Practice ("demo") market data.
Generates realistic-looking but FAKE prices so you can use the app offline.
Every page that shows demo data displays a clear "DEMO DATA" badge.
Pure Python - no Django needed.
"""
import hashlib

import numpy as np
import pandas as pd


def _seed(symbol):
    return int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)


def demo_history(symbol, days=260):
    # Build the trading-day calendar first; on weekends pandas may return
    # one fewer day than asked, so all arrays follow the calendar's length.
    index = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    days = len(index)
    rng = np.random.default_rng(_seed(symbol))
    start = 100 + _seed(symbol) % 2900
    drift = rng.normal(0.0004, 0.0006)
    rets = rng.normal(drift, 0.016, days)
    close = start * np.exp(np.cumsum(rets))
    open_ = np.empty(days)
    open_[0] = close[0]
    open_[1:] = close[:-1] * (1 + rng.normal(0, 0.004, days - 1))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.007, days)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.007, days)))
    volume = rng.integers(500_000, 5_000_000, days).astype(float)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=index)


def demo_fundamentals(symbol):
    rng = np.random.default_rng(_seed(symbol) + 7)
    pe = float(rng.uniform(8, 55))
    growth = float(rng.uniform(-0.05, 0.35))
    return {
        "roe": float(rng.uniform(0.02, 0.30)),
        "roic": float(rng.uniform(0.02, 0.25)),
        "net_margin": float(rng.uniform(0.01, 0.28)),
        "pe": pe,
        "pb": float(rng.uniform(0.7, 9)),
        "peg": pe / (growth * 100) if growth > 0.005 else None,
    }


def demo_bundle(symbol):
    return {
        "symbol": symbol,
        "name": f"{symbol} (practice data)",
        "currency": "INR" if symbol.endswith((".NS", ".BO")) or symbol.startswith("^NSE") else "USD",
        "history": demo_history(symbol),
        "fundamentals": demo_fundamentals(symbol),
        "is_demo": True,
    }
