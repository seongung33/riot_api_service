"""DRF serializers for match endpoints."""

from rest_framework import serializers

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame


class MatchParticipantSerializer(serializers.ModelSerializer):
    """Serializer for participant-level match stats."""

    total_cs = serializers.IntegerField(read_only=True)

    class Meta:
        model = MatchParticipant
        fields = [
            "id",
            "match",
            "puuid",
            "participant_id",
            "team_id",
            "champion_id",
            "champion_name",
            "individual_position",
            "win",
            "kills",
            "deaths",
            "assists",
            "total_damage_dealt_to_champions",
            "total_damage_taken",
            "gold_earned",
            "total_minions_killed",
            "neutral_minions_killed",
            "total_cs",
            "vision_score",
            "wards_placed",
            "wards_killed",
        ]
        read_only_fields = ["id", "total_cs"]


class TimelineFrameSerializer(serializers.ModelSerializer):
    """Serializer for minute-level timeline participant state."""

    class Meta:
        model = TimelineFrame
        fields = [
            "id",
            "match",
            "minute",
            "participant_id",
            "current_gold",
            "total_gold",
            "level",
            "xp",
            "minions_killed",
            "jungle_minions_killed",
            "position_x",
            "position_y",
        ]
        read_only_fields = ["id"]


class TimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for raw timeline events."""

    class Meta:
        model = TimelineEvent
        fields = [
            "id",
            "match",
            "timestamp",
            "minute",
            "event_type",
            "participant_id",
            "killer_id",
            "victim_id",
            "assisting_participant_ids",
            "monster_type",
            "building_type",
            "lane_type",
            "item_id",
            "position_x",
            "position_y",
        ]
        read_only_fields = ["id"]


class MatchSerializer(serializers.ModelSerializer):
    """Serializer for match metadata."""

    class Meta:
        model = Match
        fields = [
            "id",
            "match_id",
            "game_version",
            "queue_id",
            "game_start_time",
            "game_duration",
            "winning_team_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MatchDetailSerializer(MatchSerializer):
    """Serializer for match metadata with participant rows."""

    participants = MatchParticipantSerializer(many=True, read_only=True)

    class Meta(MatchSerializer.Meta):
        fields = MatchSerializer.Meta.fields + ["participants"]
