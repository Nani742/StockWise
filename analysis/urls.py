from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("nifty50/", views.nifty50, name="nifty50"),
    path("watchlist/add-nifty50/", views.watchlist_add_nifty50, name="watchlist_add_nifty50"),
    path("search/", views.search, name="stock_search"),
    path("stock/<str:symbol>/", views.stock_detail, name="stock_detail"),
    path("watchlist/add/", views.watchlist_add, name="watchlist_add"),
    path("watchlist/<int:pk>/remove/", views.watchlist_remove, name="watchlist_remove"),
    path("api/stock/<str:symbol>/", views.stock_api, name="stock_api"),
    path("api/news/", views.news_api, name="news_api"),
    path("api/news/stock/<str:symbol>/", views.stock_news_api, name="stock_news_api"),
    path("api/market-pulse/", views.market_pulse_api, name="market_pulse_api"),
]
