"""match/timeline 모델을 Django admin에서 확인하기 위한 등록."""

from django.contrib import admin

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    # match_id와 queue/version/start time을 함께 보면 import된 경기의 출처와 패치 구간을 빠르게 확인할 수 있다.
    list_display = ("match_id", "queue_id", "game_version", "game_start_time", "game_duration")
    search_fields = ("match_id", "game_version")
    list_filter = ("queue_id", "game_version")
    readonly_fields = ("created_at",)


@admin.register(MatchParticipant)
class MatchParticipantAdmin(admin.ModelAdmin):
    # participant admin은 특정 경기에서 각 플레이어의 챔피언, 포지션, KDA를 확인하는 용도다.
    list_display = ("match", "participant_id", "champion_name", "individual_position", "win", "kills", "deaths", "assists")
    search_fields = ("match__match_id", "puuid", "champion_name")
    list_filter = ("individual_position", "win", "champion_name")


@admin.register(TimelineFrame)
class TimelineFrameAdmin(admin.ModelAdmin):
    # frame admin은 10분 골드/경험치 차이처럼 phase metric 원본 스냅샷을 추적할 때 사용한다.
    list_display = ("match", "minute", "participant_id", "total_gold", "level", "xp")
    search_fields = ("match__match_id",)
    list_filter = ("minute",)


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    # event admin은 처치/오브젝트 이벤트가 phase metric 계산에 어떻게 반영됐는지 확인할 때 유용하다.
    list_display = ("match", "minute", "event_type", "participant_id", "killer_id", "victim_id", "monster_type")
    search_fields = ("match__match_id", "event_type", "monster_type")
    list_filter = ("event_type", "monster_type", "lane_type")
