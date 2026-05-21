"""match/timeline 모델을 API 응답 JSON으로 변환하는 serializer."""

from rest_framework import serializers

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame


class MatchParticipantSerializer(serializers.ModelSerializer):
    """플레이어별 최종 통계를 응답으로 보낼 때 사용하는 serializer."""

    # total_cs는 모델 DB 컬럼이 아니라 property로 계산되는 값이므로 read_only로 노출한다.
    total_cs = serializers.IntegerField(read_only=True)

    class Meta:
        model = MatchParticipant
        # match detail에서 온 원본 수치와 화면에서 바로 쓰는 total_cs를 함께 제공한다.
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
    """분 단위 timeline frame을 응답으로 변환한다."""

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
    """timeline event 원본을 응답으로 변환한다."""

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
    """경기 단위 메타데이터를 응답으로 변환한다."""

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
    """경기 메타데이터와 participant 목록을 함께 내려주는 상세 응답."""

    # related_name="participants"로 연결된 MatchParticipant들을 중첩 응답으로 포함한다.
    # 경기 상세 화면을 만들 때 별도 API 호출 없이 참가자 목록까지 렌더링할 수 있다.
    participants = MatchParticipantSerializer(many=True, read_only=True)

    class Meta(MatchSerializer.Meta):
        fields = MatchSerializer.Meta.fields + ["participants"]
