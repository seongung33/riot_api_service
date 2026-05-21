"""분석 지표 모델을 Django admin에서 확인하기 위한 등록."""

from django.contrib import admin

from .models import PlayerMatchPhaseMetric


@admin.register(PlayerMatchPhaseMetric)
class PlayerMatchPhaseMetricAdmin(admin.ModelAdmin):
    # phase score와 lane/objective/teamfight/side 지표를 한 화면에서 비교해
    # 특정 계정의 약점 구간이 어디인지 빠르게 점검할 수 있게 한다.
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
