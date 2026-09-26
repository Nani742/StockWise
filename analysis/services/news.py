"""
News for the dashboard and stock pages.

Where the news comes from (tried in this order):
  1. GNews API        - needs a free key in .env (GNEWS_API_KEY). https://gnews.io
  2. Google News RSS  - free, no key. Used when there is no key, the daily
                        limit is used up, or GNews returns nothing.
  3. Yahoo Finance    - free, no key. Company news for one stock (via yfinance).

Every article is turned into the same simple dictionary:
  {"title", "url", "source", "published", "description", "image", "provider", "sentiment"}
"sentiment" comes from sentiment.py (FinBERT deep learning, or a basic word list).
"""
import email.utils
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache

from .sentiment import add_sentiment

logger = logging.getLogger("analysis")

GNEWS_URL = "https://gnews.io/api/v4/search"
GOOGLE_RSS_URL = "https://news.google.com/rss/search"
USER_AGENT = "Mozilla/5.0 (StockWise educational project)"
MAX_ARTICLES = 12

# ---------------------------------------------------------------- topics
# "gnews" = search words for GNews, "rss" = search words for Google News.
MARKET_TOPICS = {
    "india": {
        "label": "India / NSE",
        "gnews": "Nifty OR Sensex OR NSE",
        "rss": "Nifty OR Sensex OR NSE stock market",
        "india": True,
    },
    "global": {
        "label": "Global markets",
        "gnews": '"stock market" OR "Wall Street" OR "global markets"',
        "rss": "global stock markets Wall Street",
        "india": False,
    },
}

SECTORS = {
    "banking": ("Banking & Finance", "banking stocks"),
    "it": ("IT & Technology", "technology stocks"),
    "auto": ("Automobile", "auto stocks"),
    "pharma": ("Pharma & Healthcare", "pharma stocks"),
    "energy": ("Oil, Gas & Energy", "oil energy stocks"),
    "metals": ("Metals & Mining", "metal stocks"),
    "fmcg": ("FMCG / Consumer", "FMCG consumer stocks"),
    "telecom": ("Telecom", "telecom stocks"),
    "infra": ("Infrastructure & Capital Goods", "infrastructure stocks"),
    "realty": ("Real Estate", "real estate stocks"),
}


class NewsError(Exception):
    pass


# ---------------------------------------------------------------- helpers
def _http_get(url, params, timeout=8):
    full = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https URLs
        return resp.read()


def _safe_url(url):
    """Only allow normal web links (protects the page from bad links)."""
    url = (url or "").strip()
    return url if url.startswith(("http://", "https://")) else ""


def _iso(dt):
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(text):
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _article(title, url, source, published, description="", image="", provider=""):
    return {
        "title": (title or "").strip(),
        "url": _safe_url(url),
        "source": (source or "").strip(),
        "published": published or "",
        "description": (description or "").strip()[:300],
        "image": _safe_url(image),
        "provider": provider,
    }


def _clean(articles, limit=MAX_ARTICLES):
    """Remove empty and duplicate headlines, newest first."""
    seen, out = set(), []
    for a in articles:
        if not a["title"] or not a["url"]:
            continue
        key = re.sub(r"[^a-z0-9]", "", a["title"].lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    out.sort(key=lambda a: a["published"], reverse=True)
    return out[:limit]


# ---------------------------------------------------------------- 1) GNews
def fetch_gnews(query, india=False, limit=10):
    key = settings.GNEWS_API_KEY
    if not key:
        raise NewsError("No GNews API key")
    params = {"q": query, "lang": "en", "max": limit, "sortby": "publishedAt", "apikey": key}
    if india:
        params["country"] = "in"
    try:
        data = json.loads(_http_get(GNEWS_URL, params))
    except urllib.error.HTTPError as exc:
        reasons = {400: "bad search words", 401: "API key is wrong",
                   403: "daily limit reached (100/day on free plan)", 429: "too many requests, slow down"}
        raise NewsError(f"GNews: {reasons.get(exc.code, f'HTTP {exc.code}')}") from exc
    except Exception as exc:  # noqa: BLE001 - network problems
        raise NewsError(f"GNews unreachable: {exc}") from exc
    return [
        _article(a.get("title"), a.get("url"), (a.get("source") or {}).get("name"),
                 a.get("publishedAt"), a.get("description"), a.get("image"), "GNews")
        for a in data.get("articles", [])
    ]


# ---------------------------------------------------------------- 2) Google News RSS
def parse_google_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.iter("item"):
        title = item.findtext("title") or ""
        source = item.findtext("source") or ""
        # Google adds " - Source name" to the end of every headline; remove it
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        try:
            published = _iso(email.utils.parsedate_to_datetime(item.findtext("pubDate")))
        except (TypeError, ValueError):
            published = ""
        items.append(_article(title, item.findtext("link"), source, published, provider="Google News"))
    return items


def fetch_google_rss(query, india=True):
    region = {"hl": "en-IN", "gl": "IN", "ceid": "IN:en"} if india else {"hl": "en-US", "gl": "US", "ceid": "US:en"}
    params = {"q": f"{query} when:7d", **region}
    try:
        return parse_google_rss(_http_get(GOOGLE_RSS_URL, params))
    except Exception as exc:  # noqa: BLE001
        raise NewsError(f"Google News unreachable: {exc}") from exc


# ---------------------------------------------------------------- 3) Yahoo Finance (per stock)
def parse_yahoo_news(items):
    """yfinance has returned two different formats over time - support both."""
    out = []
    for it in items or []:
        c = it.get("content") if isinstance(it.get("content"), dict) else None
        if c:  # new format (yfinance 0.2.50+)
            url = ((c.get("canonicalUrl") or {}).get("url")
                   or (c.get("clickThroughUrl") or {}).get("url"))
            thumb = (c.get("thumbnail") or {}).get("originalUrl", "")
            out.append(_article(c.get("title"), url, (c.get("provider") or {}).get("displayName"),
                                _iso(_parse_iso(c.get("pubDate"))), c.get("summary") or c.get("description"),
                                thumb, "Yahoo Finance"))
        else:  # old format
            ts = it.get("providerPublishTime")
            published = _iso(datetime.fromtimestamp(ts, tz=timezone.utc)) if ts else ""
            out.append(_article(it.get("title"), it.get("link"), it.get("publisher"),
                                published, "", "", "Yahoo Finance"))
    return out


def fetch_yahoo_news(symbol):
    try:
        import yfinance as yf
        return parse_yahoo_news(yf.Ticker(symbol).news)
    except Exception as exc:  # noqa: BLE001
        raise NewsError(f"Yahoo news unavailable: {exc}") from exc


# ---------------------------------------------------------------- public functions (used by views)
def _collect(sources):
    """Try each source in order; stop at the first that gives articles."""
    errors = []
    for name, func in sources:
        try:
            articles = _clean(func())
            if articles:
                return articles, name, errors
            errors.append(f"{name}: no articles found")
        except NewsError as exc:
            errors.append(str(exc))
    return [], None, errors


def _result(articles, provider, errors):
    note = ""
    if provider == "GNews":
        note = "GNews free plan: headlines can be up to 12 hours old."
    elif provider and settings.GNEWS_API_KEY:
        gnews_errors = [e for e in errors if e.startswith("GNews")]
        if gnews_errors:
            note = f"Showing free backup source ({gnews_errors[0]})."
    return {"articles": articles, "provider": provider, "note": note,
            "error": "" if articles else "News is unavailable right now. " + "; ".join(errors)}


def _cached(key, builder, log_key=None):
    """Reuse news for NEWS_CACHE_SECONDS. Sentiment (NLP) runs once per fresh download."""
    key = "v2:" + key
    result = cache.get(key)
    if result is None:
        result = add_sentiment(builder(), log_key=log_key)
        # cache good results for longer than failures
        timeout = settings.NEWS_CACHE_SECONDS if result["articles"] else 120
        cache.set(key, result, timeout)
    return result


def market_news(topic="india"):
    t = MARKET_TOPICS.get(topic, MARKET_TOPICS["india"])

    def build():
        return _result(*_collect([
            ("GNews", lambda: fetch_gnews(t["gnews"], india=t["india"])),
            ("Google News", lambda: fetch_google_rss(t["rss"], india=t["india"])),
        ]))
    return _cached(f"news:market:{topic}", build, log_key=f"market:{topic}")


def sector_news(sector="banking", scope="india"):
    label, words = SECTORS.get(sector, SECTORS["banking"])
    india = scope != "global"
    gnews_q = words if india else f"global {words}"

    def build():
        return _result(*_collect([
            ("GNews", lambda: fetch_gnews(gnews_q, india=india)),
            ("Google News", lambda: fetch_google_rss(f"{words} {'India' if india else 'global'}", india=india)),
        ]))
    return _cached(f"news:sector:{sector}:{scope}", build, log_key=f"sector:{sector}:{scope}")


def company_search_name(name):
    """'Tata Consultancy Services Ltd.' -> 'Tata Consultancy Services'"""
    name = re.sub(r"\(.*?\)", "", name or "")
    name = re.sub(r"\b(limited|ltd\.?|inc\.?|corp\.?|corporation|plc)\s*$", "", name.strip(), flags=re.I)
    return name.strip(" .,") or name


def stock_news(symbol, company_name=""):
    name = company_search_name(company_name) or symbol.split(".")[0]
    india = symbol.endswith((".NS", ".BO")) or symbol.startswith("^NSE")

    def build():
        return _result(*_collect([
            ("Yahoo Finance", lambda: fetch_yahoo_news(symbol)),
            ("GNews", lambda: fetch_gnews(f'"{name}"', india=india)),
            ("Google News", lambda: fetch_google_rss(f'"{name}" stock', india=india)),
        ]))
    return _cached(f"news:stock:{symbol}", build, log_key=symbol)
