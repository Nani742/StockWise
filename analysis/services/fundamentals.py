"""
Fundamental analysis: is the COMPANY good and is the PRICE reasonable?
Each ratio gets a score: +1 (good), 0 (okay), -1 (weak).  Pure Python.
"""

# key, display name, kind ("pct" or "x"), what it means, rule
FUNDAMENTALS = [
    ("roe", "ROE (Return on Equity)", "pct",
     "Profit earned on shareholders' money. Higher is better.", "Good ≥ 15%, Weak < 8%"),
    ("roic", "ROIC (Return on Invested Capital)", "pct",
     "Profit earned on ALL capital (equity + debt). Shows how well management uses money.", "Good ≥ 12%, Weak < 6%"),
    ("net_margin", "Net Profit Margin", "pct",
     "How many rupees of profit from every 100 rupees of sales.", "Good ≥ 15%, Weak < 5%"),
    ("pe", "P/E Ratio", "x",
     "Price you pay for ₹1 of yearly earnings. Lower = cheaper (compare within the same sector).", "Cheap < 20, Expensive > 40"),
    ("pb", "P/B Ratio", "x",
     "Price compared to the company's net assets (book value).", "Cheap < 1.5, Expensive > 5"),
    ("peg", "PEG Ratio", "x",
     "P/E divided by earnings growth. Around 1 or below suggests price is fair for the growth.", "Good < 1, Expensive > 2"),
]


def _score(key, v):
    if v is None:
        return None
    if key == "roe":
        return 1 if v >= 0.15 else (-1 if v < 0.08 else 0)
    if key == "roic":
        return 1 if v >= 0.12 else (-1 if v < 0.06 else 0)
    if key == "net_margin":
        return 1 if v >= 0.15 else (-1 if v < 0.05 else 0)
    if key == "pe":
        if v <= 0:
            return -1  # company is losing money
        return 1 if v < 20 else (-1 if v > 40 else 0)
    if key == "pb":
        if v <= 0:
            return -1
        return 1 if v < 1.5 else (-1 if v > 5 else 0)
    if key == "peg":
        if v <= 0:
            return -1
        return 1 if v < 1 else (-1 if v > 2 else 0)
    return None


def _display(kind, v):
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%" if kind == "pct" else f"{v:.2f}"


def _clean(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):  # NaN / infinity
        return None
    return v


def evaluate_fundamentals(raw):
    items, scores = [], []
    for key, name, kind, meaning, rule in FUNDAMENTALS:
        value = _clean((raw or {}).get(key))
        s = _score(key, value)
        if s is not None:
            scores.append(s)
        items.append({
            "key": key,
            "name": name,
            "value": value,
            "display": _display(kind, value),
            "score": s,
            "verdict": {1: "Good", 0: "Okay", -1: "Weak", None: "No data"}[s],
            "meaning": meaning,
            "rule": rule,
        })
    avg = sum(scores) / len(scores) if scores else 0.0
    label = "Strong" if avg > 0.3 else ("Weak" if avg < -0.3 else "Average")
    if not scores:
        label = "No data"
    return {"items": items, "score": round(avg, 3), "label": label, "available": len(scores)}
