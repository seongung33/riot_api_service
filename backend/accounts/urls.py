from django.urls import path

from .views import (
    AccountChampionPerformanceView,
    AccountRecentMatchesView,
    AccountSummaryView,
)


app_name = "accounts"

urlpatterns = [
    path("<int:account_id>/matches/", AccountRecentMatchesView.as_view(), name="recent_matches"),
    path("<int:account_id>/summary/", AccountSummaryView.as_view(), name="summary"),
    path("<int:account_id>/champions/", AccountChampionPerformanceView.as_view(), name="champions"),
]
