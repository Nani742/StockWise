from django.contrib import admin

from .models import PredictionLog, SentimentLog, WatchlistItem


@admin.register(SentimentLog)
class SentimentLogAdmin(admin.ModelAdmin):
    list_display = ("key", "score", "positive", "neutral", "negative", "engine", "created_at")
    list_filter = ("engine",)
    search_fields = ("key",)


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("symbol", "user", "created_at")
    search_fields = ("symbol", "user__username")


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ("symbol", "direction", "last_price", "target_price", "is_demo", "created_at")
    list_filter = ("direction", "is_demo")
    search_fields = ("symbol",)
