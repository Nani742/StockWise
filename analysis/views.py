from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import StockSearchForm, is_valid_symbol
from .models import WatchlistItem
from .nifty50 import NIFTY50, NIFTY50_BY_SYMBOL, NIFTY50_INDEX, sectors
from .services.engine import analyze_symbol, compact
from .services.market_data import DataUnavailable
from .services.markets import market_pulse
from .services.news import MARKET_TOPICS, SECTORS, market_news, sector_news, stock_news

POPULAR = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS"]


@login_required
def nifty50(request):
    """All NIFTY 50 companies with mini charts and next-week outlook."""
    watched = set(request.user.watchlist.values_list("symbol", flat=True))
    companies = [dict(c, watched=c["symbol"] in watched) for c in NIFTY50]
    return render(request, "analysis/nifty50.html", {
        "companies": companies,
        "index": NIFTY50_INDEX,
        "sectors": sectors(),
        "watched_count": sum(1 for c in companies if c["watched"]),
    })


@login_required
@require_POST
def watchlist_add_nifty50(request):
    """Adds every NIFTY 50 company to the user's watchlist in one click."""
    existing = set(request.user.watchlist.values_list("symbol", flat=True))
    new_items = [WatchlistItem(user=request.user, symbol=c["symbol"])
                 for c in NIFTY50 if c["symbol"] not in existing]
    room = settings.WATCHLIST_LIMIT - len(existing)
    new_items = new_items[:max(room, 0)]
    WatchlistItem.objects.bulk_create(new_items, ignore_conflicts=True)
    if new_items:
        messages.success(request, f"Added {len(new_items)} NIFTY 50 companies to your watchlist.")
    else:
        messages.info(request, "All NIFTY 50 companies are already in your watchlist (or it is full).")
    return redirect("nifty50")


@login_required
def dashboard(request):
    items = request.user.watchlist.all()
    return render(request, "analysis/dashboard.html", {
        "items": items,
        "form": StockSearchForm(),
        "popular": POPULAR,
        "limit": settings.WATCHLIST_LIMIT,
        "market_topics": [(k, v["label"]) for k, v in MARKET_TOPICS.items()],
        "news_sectors": [(k, v[0]) for k, v in SECTORS.items()],
        "news_stocks": [i.symbol for i in items] or POPULAR,
        "has_news_key": bool(settings.GNEWS_API_KEY),
    })


# ---------------------------------------------------------------- news & market pulse (JSON)
@login_required
def news_api(request):
    """/api/news/?type=market&topic=india
       /api/news/?type=sector&sector=it&scope=global"""
    kind = request.GET.get("type", "market")
    if kind == "sector":
        sector = request.GET.get("sector", "banking")
        if sector not in SECTORS:
            return JsonResponse({"error": "Unknown sector"}, status=400)
        scope = "global" if request.GET.get("scope") == "global" else "india"
        return JsonResponse(sector_news(sector, scope))
    topic = request.GET.get("topic", "india")
    if topic not in MARKET_TOPICS:
        return JsonResponse({"error": "Unknown topic"}, status=400)
    return JsonResponse(market_news(topic))


@login_required
def stock_news_api(request, symbol):
    symbol = symbol.upper()
    if not is_valid_symbol(symbol):
        return JsonResponse({"error": "Invalid symbol"}, status=400)
    info = NIFTY50_BY_SYMBOL.get(symbol)
    name = request.GET.get("name", "")[:80] or (info["name"] if info else "")
    return JsonResponse(stock_news(symbol, name))


@login_required
def market_pulse_api(request):
    return JsonResponse(market_pulse())


@login_required
def search(request):
    form = StockSearchForm(request.GET or None)
    if form.is_valid():
        return redirect("stock_detail", symbol=form.cleaned_data["full_symbol"])
    messages.error(request, "Please enter a valid stock symbol.")
    return redirect("dashboard")


@login_required
def stock_detail(request, symbol):
    symbol = symbol.upper()
    if not is_valid_symbol(symbol):
        raise Http404("Invalid symbol")
    try:
        result = analyze_symbol(symbol)
    except DataUnavailable as exc:
        messages.error(request, str(exc))
        return redirect("dashboard")

    in_watchlist = request.user.watchlist.filter(symbol=symbol).first()
    return render(request, "analysis/stock_detail.html", {
        "r": result,
        "symbol": symbol,
        "watch_item": in_watchlist,
        "nifty_info": NIFTY50_BY_SYMBOL.get(symbol),
    })


@login_required
@require_POST
def watchlist_add(request):
    symbol = (request.POST.get("symbol") or "").strip().upper()
    if not is_valid_symbol(symbol):
        messages.error(request, "Invalid symbol.")
        return redirect("dashboard")
    if request.user.watchlist.count() >= settings.WATCHLIST_LIMIT:
        messages.warning(request, f"Your watchlist is full ({settings.WATCHLIST_LIMIT} stocks). Remove one first.")
        return redirect("dashboard")
    _, created = WatchlistItem.objects.get_or_create(user=request.user, symbol=symbol)
    if created:
        messages.success(request, f"{symbol} added to your watchlist.")
    else:
        messages.info(request, f"{symbol} is already in your watchlist.")
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("dashboard")


@login_required
@require_POST
def watchlist_remove(request, pk):
    item = get_object_or_404(WatchlistItem, pk=pk, user=request.user)
    symbol = item.symbol
    item.delete()
    messages.info(request, f"{symbol} removed from your watchlist.")
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("dashboard")


@login_required
def stock_api(request, symbol):
    """JSON used by the dashboard cards (JavaScript fetches this)."""
    symbol = symbol.upper()
    if not is_valid_symbol(symbol):
        return JsonResponse({"error": "Invalid symbol"}, status=400)
    try:
        result = analyze_symbol(symbol)
    except DataUnavailable as exc:
        return JsonResponse({"error": str(exc)}, status=404)
    if request.GET.get("full") == "1":
        return JsonResponse(result)
    return JsonResponse(compact(result))
