from django.urls import path

from .views import ImportRecentMatchesView


app_name = "riot_api"

urlpatterns = [
    path("import-recent-matches/", ImportRecentMatchesView.as_view(), name="import_recent_matches"),
]
