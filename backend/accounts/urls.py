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
    # search는 Riot ID를 입력받아 import와 초기 분석 응답을 한 번에 수행하는 진입점이다.
    path("search/", AccountSearchView.as_view(), name="search"),
    # 아래 endpoint들은 이미 저장된 account_id를 기준으로 화면 일부를 다시 조회할 때 사용한다.
    path("<int:account_id>/matches/", AccountRecentMatchesView.as_view(), name="recent_matches"),
    path("<int:account_id>/summary/", AccountSummaryView.as_view(), name="summary"),
    path("<int:account_id>/champions/", AccountChampionPerformanceView.as_view(), name="champions"),
    path("<int:account_id>/feedback/", AccountFeedbackView.as_view(), name="feedback"),
    path("<int:account_id>/phase-metrics/", AccountPhaseMetricView.as_view(), name="phase_metrics"),
]
