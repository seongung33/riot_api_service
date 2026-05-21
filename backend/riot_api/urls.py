from django.urls import path

from .views import ImportRecentMatchesView


app_name = "riot_api"

urlpatterns = [
    # accounts/search와 달리 이 endpoint는 import 결과 자체에 초점을 둔 별도 workflow다.
    path("import-recent-matches/", ImportRecentMatchesView.as_view(), name="import_recent_matches"),
]
