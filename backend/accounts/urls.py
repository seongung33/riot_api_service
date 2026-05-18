from django.urls import path

from .views import (
    AccountChampionPerformanceView,
    AccountFeedbackView,
    AccountPhaseMetricView,
    AccountRecentMatchesView,
    AccountSearchView,
    AccountSummaryView,
)


app_name = "accounts"

urlpatterns = [
    path("search/", AccountSearchView.as_view(), name="search"),
    path("<int:account_id>/matches/", AccountRecentMatchesView.as_view(), name="recent_matches"),
    path("<int:account_id>/summary/", AccountSummaryView.as_view(), name="summary"),
    path("<int:account_id>/champions/", AccountChampionPerformanceView.as_view(), name="champions"),
    path("<int:account_id>/feedback/", AccountFeedbackView.as_view(), name="feedback"),
    path("<int:account_id>/phase-metrics/", AccountPhaseMetricView.as_view(), name="phase_metrics"),
]
