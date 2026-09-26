"""
NLP: news sentiment (is a headline good or bad news for the market?).

Two engines:
  1. FinBERT (deep learning)  - a BERT neural network trained on financial news
                                (Hugging Face model "ProsusAI/finbert").
                                Needs: pip install -r requirements-ml.txt
                                and:   python manage.py setup_finbert   (downloads ~440 MB once)
  2. Word list (basic)        - counts finance words like "surge", "loss".
                                Always available, used when FinBERT is not set up.

Every headline gets:  {"label": "positive|negative|neutral", "confidence": 0-1, "score": -1..+1}
score = P(positive) - P(negative)
"""
import logging
import re
import threading
import time

from django.conf import settings

logger = logging.getLogger("analysis")

FINBERT = "FinBERT (deep learning)"
WORDLIST = "Word list (basic)"

# ---------------------------------------------------------------- 1) FinBERT
_lock = threading.Lock()
_model = None            # (tokenizer, model, torch) once loaded
_failed_at = 0.0         # when loading last failed (so we don't retry on every request)
_fail_reason = ""
RETRY_AFTER = 600        # seconds


def load_finbert(allow_download=False):
    """Loads FinBERT once and keeps it in memory. Returns (tokenizer, model, torch)."""
    global _model, _failed_at, _fail_reason
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        if not allow_download and _failed_at and time.time() - _failed_at < RETRY_AFTER:
            raise RuntimeError(_fail_reason)
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            name = settings.FINBERT_MODEL
            # local_files_only=True: never start a 440 MB download in the middle of a web request.
            # The download happens once with:  python manage.py setup_finbert
            tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=not allow_download)
            model = AutoModelForSequenceClassification.from_pretrained(name, local_files_only=not allow_download)
            model.eval()
            _model = (tokenizer, model, torch)
            _failed_at, _fail_reason = 0.0, ""
            logger.info("FinBERT loaded")
            return _model
        except ImportError:
            _fail_reason = "PyTorch/transformers not installed (pip install -r requirements-ml.txt)"
        except Exception as exc:  # noqa: BLE001 - model not downloaded yet, etc.
            _fail_reason = f"FinBERT model not available ({exc.__class__.__name__}). Run: python manage.py setup_finbert"
        _failed_at = time.time()
        raise RuntimeError(_fail_reason)


def finbert_predict(texts, batch_size=16):
    """Returns one {"positive": p, "negative": p, "neutral": p} per text."""
    tokenizer, model, torch = load_finbert()
    id2label = {int(k): str(v).lower() for k, v in model.config.id2label.items()}
    out = []
    for i in range(0, len(texts), batch_size):
        batch = [t[:512] for t in texts[i:i + batch_size]]
        enc = tokenizer(batch, padding=True, truncation=True, max_length=96, return_tensors="pt")
        with torch.no_grad():
            probs = torch.softmax(model(**enc).logits, dim=-1).tolist()
        for row in probs:
            p = {id2label[j]: float(v) for j, v in enumerate(row)}
            out.append({"positive": p.get("positive", 0.0), "negative": p.get("negative", 0.0),
                        "neutral": p.get("neutral", 0.0)})
    return out


# ---------------------------------------------------------------- 2) word list
POSITIVE = {
    "gain", "gains", "gained", "rise", "rises", "rising", "rose", "rally", "rallies", "surge", "surges", "surged",
    "jump", "jumps", "jumped", "soar", "soars", "soared", "climb", "climbs", "record", "high", "highs", "beat",
    "beats", "upgrade", "upgraded", "strong", "stronger", "growth", "grows", "profit", "profits", "win", "wins",
    "won", "bullish", "outperform", "outperforms", "expand", "expands", "expansion", "dividend", "buyback",
    "approval", "approves", "boost", "boosts", "recovery", "recovers", "rebound", "rebounds", "upbeat", "optimism",
    "robust", "positive", "higher", "inflows", "buying", "deal", "order", "orders", "launch", "launches",
}
NEGATIVE = {
    "fall", "falls", "fell", "drop", "drops", "dropped", "slump", "slumps", "plunge", "plunges", "plunged",
    "decline", "declines", "declined", "loss", "losses", "miss", "misses", "missed", "downgrade", "downgraded",
    "weak", "weaker", "weakness", "bearish", "crash", "crashes", "fraud", "probe", "penalty", "fine", "lawsuit",
    "slip", "slips", "slipped", "lower", "selloff", "sell-off", "concern", "concerns", "fear", "fears", "default",
    "resigns", "resignation", "tumble", "tumbles", "sink", "sinks", "slowdown", "recession", "inflation",
    "outflows", "selling", "warning", "warns", "cut", "cuts", "layoffs", "negative", "volatile", "pressure",
}
NEGATORS = {"not", "no", "never", "without", "fails", "failed"}


def wordlist_predict(texts):
    out = []
    for text in texts:
        words = re.findall(r"[a-z][a-z\-]*", (text or "").lower())
        pos = neg = 0
        for i, w in enumerate(words):
            flip = i > 0 and words[i - 1] in NEGATORS
            if w in POSITIVE:
                neg, pos = (neg + 1, pos) if flip else (neg, pos + 1)
            elif w in NEGATIVE:
                pos, neg = (pos + 1, neg) if flip else (pos, neg + 1)
        total = pos + neg
        if total == 0:
            out.append({"positive": 0.1, "negative": 0.1, "neutral": 0.8})
            continue
        if pos == neg:  # mixed news, e.g. "Sensex gains but metal stocks fall"
            out.append({"positive": 0.2, "negative": 0.2, "neutral": 0.6})
            continue
        strength = min(1.0, 0.45 + 0.2 * total)   # 1 word = 65% sure, 3+ words = ~100%
        p = pos / total * strength
        n = neg / total * strength
        out.append({"positive": p, "negative": n, "neutral": max(0.0, 1 - p - n)})
    return out


# ---------------------------------------------------------------- public
def engine_status():
    mode = settings.SENTIMENT_ENGINE
    if mode == "off":
        return None, "Sentiment analysis is turned off (SENTIMENT_ENGINE=off)."
    if mode in ("auto", "finbert"):
        try:
            load_finbert()
            return FINBERT, ""
        except RuntimeError as exc:
            return WORDLIST, str(exc)
    return WORDLIST, ""


def analyze(texts):
    """Returns (list of results, engine name, note)."""
    engine, note = engine_status()
    if engine is None or not texts:
        return [None] * len(texts), engine, note
    probs = None
    if engine == FINBERT:
        try:
            probs = finbert_predict(texts)
        except Exception as exc:  # noqa: BLE001
            logger.warning("FinBERT failed, using word list: %s", exc)
            engine, note = WORDLIST, f"FinBERT error: {exc}"
    if probs is None:
        probs = wordlist_predict(texts)

    results = []
    for p in probs:
        label = max(p, key=p.get)
        results.append({
            "label": label,
            "confidence": round(p[label], 3),
            "score": round(p["positive"] - p["negative"], 3),
        })
    return results, engine, note


def summarize(results):
    results = [r for r in results if r]
    if not results:
        return None
    avg = sum(r["score"] for r in results) / len(results)
    label = "Positive" if avg > 0.15 else ("Negative" if avg < -0.15 else "Neutral")
    return {
        "label": label,
        "score": round(avg, 3),
        "count": len(results),
        "positive": sum(r["label"] == "positive" for r in results),
        "negative": sum(r["label"] == "negative" for r in results),
        "neutral": sum(r["label"] == "neutral" for r in results),
    }


def add_sentiment(news_result, log_key=None):
    """Adds a sentiment tag to every article and a 'mood' summary to the news result."""
    articles = news_result.get("articles") or []
    texts = [f"{a['title']}. {a.get('description') or ''}".strip(" .") for a in articles]
    results, engine, note = analyze(texts)
    for a, r in zip(articles, results):
        a["sentiment"] = r
    news_result["mood"] = summarize(results)
    news_result["sentiment_engine"] = engine or ""
    news_result["sentiment_note"] = note
    if log_key and news_result["mood"]:
        _log(log_key, news_result["mood"], engine)
    return news_result


def _log(key, mood, engine):
    from analysis.models import SentimentLog
    try:
        SentimentLog.objects.create(
            key=key[:40], score=mood["score"], positive=mood["positive"], negative=mood["negative"],
            neutral=mood["neutral"], count=mood["count"], engine=engine[:40],
        )
    except Exception as exc:  # noqa: BLE001 - logging must never break the page
        logger.warning("Could not save sentiment log: %s", exc)
