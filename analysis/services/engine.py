"""
The one function the views call: analyze_symbol("TCS.NS").
Adds caching (so we don't download the same stock again and again)
and saves each forecast to the PredictionLog table in PostgreSQL.
"""
import logging

from django.conf import settings
from django.core.cache import cache

from .market_data import DataUnavailable, get_stock_data
from .pipeline import build_analysis

logger = logging.getLogger("analysis")


def analyze_symbol(symbol):
    key = f"analysis:v1:{symbol}:{int(settings.FORCE_DEMO_DATA)}"
    result = cache.get(key)
    if result is not None:
        return result

    bundle = get_stock_data(symbol)
    try:
        result = build_analysis(bundle)
    except ValueError as exc:
        raise DataUnavailable(f"Not enough data to analyse {symbol}: {exc}") from exc

    cache.set(key, result, settings.ANALYSIS_CACHE_SECONDS)
    _log_prediction(result)
    return result


def _log_prediction(r):
    from analysis.models import PredictionLog

    p = r["prediction"]
    try:
        PredictionLog.objects.create(
            symbol=r["symbol"],
            last_price=p["last_price"],
            direction=p["direction"],
            target_price=p["target"],
            low_price=p["low"],
            high_price=p["high"],
            tech_score=r["tech_score"] or 0.0,
            fund_score=r["fundamentals"]["score"],
            is_demo=r["is_demo"],
        )
    except Exception as exc:  # noqa: BLE001 - logging must never break the page
        logger.warning("Could not save prediction log: %s", exc)


def compact(r):
    """Small version for dashboard cards."""
    return {
        "symbol": r["symbol"],
        "name": r["name"],
        "currency": r["currency"],
        "is_demo": r["is_demo"],
        "last_price": r["last_price"],
        "change_pct": r["change_pct"],
        "tech_label": r["tech_label"],
        "fund_label": r["fundamentals"]["label"],
        "prediction": r["prediction"],
        "spark": r["spark"],
    }
