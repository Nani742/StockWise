"""
Downloads prices and company ratios from Yahoo Finance (free, via yfinance).
Indian stocks: add .NS (NSE) or .BO (BSE), e.g. TCS.NS
"""
import logging

from django.conf import settings

from .demo import demo_bundle

logger = logging.getLogger("analysis")


class DataUnavailable(Exception):
    pass


def _first(df, keys):
    """Latest value of the first matching row in a yfinance financial table."""
    if df is None or getattr(df, "empty", True):
        return None
    for k in keys:
        if k in df.index:
            vals = df.loc[k].dropna()
            if len(vals):
                return float(vals.iloc[0])
    return None


def _compute_roic(ticker):
    """ROIC = EBIT x (1 - tax rate) / (debt + equity - cash)"""
    try:
        inc, bs = ticker.income_stmt, ticker.balance_sheet
        ebit = _first(inc, ["EBIT", "Operating Income"])
        if ebit is None:
            return None
        tax = _first(inc, ["Tax Provision"])
        pretax = _first(inc, ["Pretax Income"])
        rate = tax / pretax if tax is not None and pretax else 0.25
        rate = min(max(rate, 0.0), 0.5)
        equity = _first(bs, ["Stockholders Equity", "Common Stock Equity"])
        debt = _first(bs, ["Total Debt"]) or 0.0
        cash = _first(bs, ["Cash And Cash Equivalents"]) or 0.0
        if equity is None:
            return None
        invested = equity + debt - cash
        return ebit * (1 - rate) / invested if invested > 0 else None
    except Exception as exc:  # noqa: BLE001 - financial tables are often incomplete
        logger.info("ROIC unavailable: %s", exc)
        return None


def fetch_yahoo(symbol):
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty or len(hist) < 60:
        raise DataUnavailable(
            f"No price data found for '{symbol}'. Check the symbol "
            f"(Indian stocks need .NS or .BO, e.g. TCS.NS) and your internet connection."
        )
    hist = hist[["Open", "High", "Low", "Close", "Volume"]].dropna()
    if getattr(hist.index, "tz", None) is not None:
        hist.index = hist.index.tz_localize(None)

    try:
        info = ticker.info or {}
    except Exception as exc:  # noqa: BLE001
        logger.info("info unavailable for %s: %s", symbol, exc)
        info = {}

    pe = info.get("trailingPE") or info.get("forwardPE")
    peg = info.get("pegRatio") or info.get("trailingPegRatio")
    growth = info.get("earningsGrowth")
    if peg is None and pe and growth and growth > 0:
        peg = pe / (growth * 100)

    fundamentals = {
        "roe": info.get("returnOnEquity"),
        "roic": _compute_roic(ticker),
        "net_margin": info.get("profitMargins"),
        "pe": pe,
        "pb": info.get("priceToBook"),
        "peg": peg,
    }
    return {
        "symbol": symbol,
        "name": info.get("longName") or info.get("shortName") or symbol,
        "currency": info.get("currency") or "",
        "history": hist,
        "fundamentals": fundamentals,
        "is_demo": False,
    }


def get_stock_data(symbol):
    if settings.FORCE_DEMO_DATA:
        return demo_bundle(symbol)
    try:
        return fetch_yahoo(symbol)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Yahoo fetch failed for %s: %s", symbol, exc)
        if settings.DEMO_FALLBACK:
            return demo_bundle(symbol)
        if isinstance(exc, DataUnavailable):
            raise
        raise DataUnavailable(f"Could not download data for '{symbol}' right now: {exc}") from exc
