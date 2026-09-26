"""
Downloads FinBERT (~440 MB, only once) and tests it on sample headlines.

Usage:   python manage.py setup_finbert
"""
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

SAMPLES = [
    "Reliance Industries reports record quarterly profit, shares surge 5%",
    "Infosys cuts revenue guidance as clients delay spending",
    "Nifty ends flat ahead of RBI policy decision",
    "TCS wins $2 billion deal from European bank",
    "SEBI launches probe into accounting irregularities at mid-cap firm",
]


class Command(BaseCommand):
    help = "Download the FinBERT deep learning model and test it."

    def handle(self, *args, **options):
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError as exc:
            raise CommandError(
                "PyTorch / transformers are not installed.\n"
                "Run this first (inside the venv):   pip install -r requirements-ml.txt"
            ) from exc

        from analysis.services import sentiment

        self.stdout.write(f"Downloading / loading {settings.FINBERT_MODEL} (first time ~440 MB, please wait)...")
        start = time.time()
        try:
            sentiment.load_finbert(allow_download=True)
        except RuntimeError as exc:
            raise CommandError(f"Could not load FinBERT: {exc}\nCheck your internet connection and try again.") from exc
        self.stdout.write(self.style.SUCCESS(f"FinBERT ready in {time.time() - start:.0f} s\n"))

        self.stdout.write("Test on sample headlines:")
        probs = sentiment.finbert_predict(SAMPLES)
        for text, p in zip(SAMPLES, probs):
            label = max(p, key=p.get)
            colour = {"positive": self.style.SUCCESS, "negative": self.style.ERROR}.get(label, self.style.WARNING)
            self.stdout.write(f"  {colour(f'{label:>8} {p[label]:.0%}')}  {text}")

        self.stdout.write(self.style.SUCCESS(
            "\nDone! Restart the server (python manage.py runserver). "
            "News lists will now say 'FinBERT (deep learning)'."
        ))
