"""
Next-week (5 trading days) forecast.

Idea (kept simple on purpose):
  combined score = 75% technical score + 25% fundamental score
  expected move  = combined score x half of the normal weekly move (volatility)
  price range    = expected price ± one normal weekly move

This is an educational estimate, NOT a guarantee. Markets are uncertain.
"""
import math

import pandas as pd

TECH_WEIGHT = 0.75
FUND_WEIGHT = 0.25


def predict_next_week(d, tech_score, fund_score, horizon=5):
    close = d["Close"]
    last = float(close.iloc[-1])
    rets = close.pct_change().dropna().tail(60)
    daily_sigma = float(rets.std()) if len(rets) > 5 else 0.02
    weekly_sigma = daily_sigma * math.sqrt(horizon)

    if tech_score is None or tech_score != tech_score:
        combined = fund_score
    else:
        combined = TECH_WEIGHT * tech_score + FUND_WEIGHT * fund_score
    combined = max(-1.0, min(1.0, combined))

    expected = combined * 0.5 * weekly_sigma
    target = last * (1 + expected)

    dates = pd.bdate_range(d.index[-1] + pd.Timedelta(days=1), periods=horizon)
    path = []
    for k, dt in enumerate(dates, start=1):
        frac = k / horizon
        band = weekly_sigma * math.sqrt(frac)
        path.append({
            "date": dt.strftime("%Y-%m-%d"),
            "mid": round(last * (1 + expected * frac), 2),
            "low": round(last * (1 + expected * frac - band), 2),
            "high": round(last * (1 + expected * frac + band), 2),
        })

    if combined > 0.15:
        direction = "Likely Up"
    elif combined < -0.15:
        direction = "Likely Down"
    else:
        direction = "Sideways"

    return {
        "direction": direction,
        "combined_score": round(combined, 3),
        "strength": round(abs(combined) * 100),          # 0-100 signal strength
        "last_price": round(last, 2),
        "target": round(target, 2),
        "expected_pct": round(expected * 100, 2),
        "low": path[-1]["low"],
        "high": path[-1]["high"],
        "weekly_volatility_pct": round(weekly_sigma * 100, 2),
        "path": path,
    }
