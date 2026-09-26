from django.conf import settings
from django.db import models


class WatchlistItem(models.Model):
    """A stock a user wants to follow on their dashboard."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlist")
    symbol = models.CharField(max_length=20)  # e.g. "TCS.NS", "RELIANCE.NS", "AAPL"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "symbol"], name="unique_user_symbol"),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.symbol}"


class PredictionLog(models.Model):
    """Every time a stock is analysed we store the forecast, so later you can
    check how often the model was right (great for learning!)."""

    symbol = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_price = models.FloatField()
    direction = models.CharField(max_length=20)
    target_price = models.FloatField()
    low_price = models.FloatField()
    high_price = models.FloatField()
    tech_score = models.FloatField()
    fund_score = models.FloatField()
    is_demo = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.symbol} {self.direction} @ {self.created_at:%Y-%m-%d}"


class SentimentLog(models.Model):
    """News mood saved every time fresh news is analysed.
    key = a stock symbol (e.g. TCS.NS) or a topic (e.g. market:india, sector:it:global).
    Over time this builds a history of news sentiment (useful for Stage 2 / deep learning)."""

    key = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField()          # -1 (very negative) ... +1 (very positive)
    positive = models.PositiveSmallIntegerField(default=0)
    negative = models.PositiveSmallIntegerField(default=0)
    neutral = models.PositiveSmallIntegerField(default=0)
    count = models.PositiveSmallIntegerField(default=0)
    engine = models.CharField(max_length=40)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.key} {self.score:+.2f} ({self.engine})"
