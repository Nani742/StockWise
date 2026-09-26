"""
Joins everything together: prices -> indicators -> scores -> forecast -> chart data.
Pure Python (no Django), so it can be tested on its own.
"""
import math

from .fundamentals import evaluate_fundamentals
from .predictor import predict_next_week
from .technicals import (
    add_indicators, backtest, component_scores, composite_score, label,
    order_flow_summary, technical_signals, volume_profile,
)


def _num(x, n=2):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return round(x, n)


def _series(s, n=2):
    return [_num(v, n) for v in s.tolist()]


def build_analysis(bundle, chart_days=120, spark_days=60):
    hist = bundle["history"]
    if hist is None or len(hist) < 60:
        raise ValueError("Need at least 60 days of price history")

    d = add_indicators(hist)
    scores = component_scores(d)
    composite = composite_score(scores)
    profile = volume_profile(d)
    flow = order_flow_summary(d)
    signals = technical_signals(d, scores, profile, flow)

    tech_score = _num(composite.iloc[-1], 3)
    fund = evaluate_fundamentals(bundle.get("fundamentals"))
    prediction = predict_next_week(d, tech_score, fund["score"])
    bt = backtest(composite, d["Close"])

    last, prev = float(d["Close"].iloc[-1]), float(d["Close"].iloc[-2])
    c = d.tail(chart_days)
    s = d.tail(spark_days)

    return {
        "symbol": bundle["symbol"],
        "name": bundle.get("name") or bundle["symbol"],
        "currency": bundle.get("currency") or "",
        "is_demo": bool(bundle.get("is_demo")),
        "as_of": d.index[-1].strftime("%d %b %Y"),
        "last_price": round(last, 2),
        "change": round(last - prev, 2),
        "change_pct": round((last / prev - 1) * 100, 2),
        "high_52w": _num(d["High"].max()),
        "low_52w": _num(d["Low"].min()),
        "tech_score": tech_score,
        "tech_label": label(tech_score),
        "fundamentals": fund,
        "signals": signals,
        "prediction": prediction,
        "backtest": bt,
        "order_flow": flow,
        "profile": profile,
        "spark": {
            "dates": [x.strftime("%Y-%m-%d") for x in s.index],
            "close": _series(s["Close"]),
        },
        "chart": {
            "dates": [x.strftime("%Y-%m-%d") for x in c.index],
            "close": _series(c["Close"]),
            "sma20": _series(c["SMA20"]),
            "sma50": _series(c["SMA50"]),
            "bb_upper": _series(c["BB_upper"]),
            "bb_lower": _series(c["BB_lower"]),
            "rsi": _series(c["RSI"], 1),
            "macd": _series(c["MACD"], 3),
            "macd_signal": _series(c["MACD_signal"], 3),
            "macd_hist": _series(c["MACD_hist"], 3),
            "buy_vol": _series(c["BuyVol"], 0),
            "sell_vol": _series(c["SellVol"], 0),
            "bias": _series(c["BIAS"], 2),
        },
    }
