"""Root URL configuration for the backend API."""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/matches/", include("matches.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/riot/", include("riot_api.urls")),
]
