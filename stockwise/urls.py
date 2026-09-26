from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "StockWise Administration"
admin.site.site_title = "StockWise Admin"

urlpatterns = [
    path("admin/", admin.site.urls),          # Django's built-in admin
    path("", include("core.urls")),           # Home, Features, Help, Contact, Login, Register, Admin panel
    path("", include("analysis.urls")),       # Dashboard, stock pages, API
]
