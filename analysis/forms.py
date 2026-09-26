import re

from django import forms

EXCHANGE_CHOICES = [
    ("NS", "NSE India (.NS)"),
    ("BO", "BSE India (.BO)"),
    ("US", "US / Global (no suffix)"),
]

SYMBOL_RE = re.compile(r"^[A-Z0-9^][A-Z0-9.\-&^=]{0,19}$")


def normalize_symbol(raw, exchange="NS"):
    """'tcs' + NSE -> 'TCS.NS'. Symbols that already have a suffix are kept."""
    symbol = (raw or "").strip().upper().replace(" ", "")
    if not symbol:
        return ""
    if "." not in symbol and not symbol.startswith("^") and exchange in ("NS", "BO"):
        symbol = f"{symbol}.{exchange}"
    return symbol


def is_valid_symbol(symbol):
    return bool(SYMBOL_RE.match(symbol or ""))


class StockSearchForm(forms.Form):
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "e.g. TCS, RELIANCE, INFY, AAPL"}),
    )
    exchange = forms.ChoiceField(
        choices=EXCHANGE_CHOICES,
        initial="NS",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )

    def clean(self):
        data = super().clean()
        full = normalize_symbol(data.get("symbol"), data.get("exchange", "NS"))
        if not is_valid_symbol(full):
            raise forms.ValidationError("That doesn't look like a valid stock symbol.")
        data["full_symbol"] = full
        return data
