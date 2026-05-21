"""백엔드 API의 최상위 URL 라우팅."""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    # 프론트는 /api/accounts/search/로 계정 검색과 import를 시작한다.
    # 세부 도메인 URL은 각 앱의 urls.py에 위임해 view 책임을 분리한다.
    path("api/accounts/", include("accounts.urls")),
    path("api/matches/", include("matches.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/riot/", include("riot_api.urls")),
]
