"""Admin registrations for matches."""

from django.contrib import admin

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("match_id", "queue_id", "game_version", "game_start_time", "game_duration")
    search_fields = ("match_id", "game_version")
    list_filter = ("queue_id", "game_version")
    readonly_fields = ("created_at",)


@admin.register(MatchParticipant)
class MatchParticipantAdmin(admin.ModelAdmin):
    list_display = ("match", "participant_id", "champion_name", "individual_position", "win", "kills", "deaths", "assists")
    search_fields = ("match__match_id", "puuid", "champion_name")
    list_filter = ("individual_position", "win", "champion_name")


@admin.register(TimelineFrame)
class TimelineFrameAdmin(admin.ModelAdmin):
    list_display = ("match", "minute", "participant_id", "total_gold", "level", "xp")
    search_fields = ("match__match_id",)
    list_filter = ("minute",)


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ("match", "minute", "event_type", "participant_id", "killer_id", "victim_id", "monster_type")
    search_fields = ("match__match_id", "event_type", "monster_type")
    list_filter = ("event_type", "monster_type", "lane_type")
