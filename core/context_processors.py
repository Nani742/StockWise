from django.conf import settings


def site_info(request):
    """Values available in every template."""
    return {
        "SITE_NAME": "StockWise",
        "DEMO_MODE": settings.FORCE_DEMO_DATA,
    }
