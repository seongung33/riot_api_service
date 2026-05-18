"""Admin registrations for analytics."""

from django.contrib import admin

from .models import PlayerMatchPhaseMetric


@admin.register(PlayerMatchPhaseMetric)
class PlayerMatchPhaseMetricAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "puuid",
        "champion_id",
        "position",
        "lane_score",
        "objective_score",
        "teamfight_score",
        "side_score",
    )
    search_fields = ("match__match_id", "puuid")
    list_filter = ("position", "champion_id")
