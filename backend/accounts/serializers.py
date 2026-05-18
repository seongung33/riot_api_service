"""DRF serializers for account endpoints."""

from rest_framework import serializers

from .models import RiotAccount


class RiotAccountSerializer(serializers.ModelSerializer):
    """Serializer for Riot account identity data."""

    class Meta:
        model = RiotAccount
        fields = [
            "id",
            "puuid",
            "game_name",
            "tag_line",
            "region",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecentMatchSerializer(serializers.Serializer):
    """Serializer for a player's recent match row."""

    match_id = serializers.CharField()
    game_version = serializers.CharField()
    queue_id = serializers.IntegerField()
    game_start_time = serializers.DateTimeField()
    game_duration = serializers.IntegerField()
    champion_id = serializers.IntegerField()
    champion_name = serializers.CharField()
    individual_position = serializers.CharField()
    win = serializers.BooleanField()
    kills = serializers.IntegerField()
    deaths = serializers.IntegerField()
    assists = serializers.IntegerField()
    kda = serializers.FloatField()
    total_cs = serializers.IntegerField()
    gold_earned = serializers.IntegerField()
    vision_score = serializers.IntegerField()
    total_damage_dealt_to_champions = serializers.IntegerField()
    total_damage_taken = serializers.IntegerField()


class AccountSummarySerializer(serializers.Serializer):
    """Serializer for basic account-level recent performance summary."""

    account_id = serializers.IntegerField()
    puuid = serializers.CharField()
    game_name = serializers.CharField()
    tag_line = serializers.CharField()
    region = serializers.CharField()
    game_count = serializers.IntegerField()
    win_rate = serializers.FloatField()
    average_kda = serializers.FloatField()
    average_kills = serializers.FloatField()
    average_deaths = serializers.FloatField()
    average_assists = serializers.FloatField()
    average_cs = serializers.FloatField()
    average_gold = serializers.FloatField()
    average_vision_score = serializers.FloatField()
    main_position = serializers.CharField(allow_null=True)
    champion_pool = serializers.ListField(child=serializers.CharField())


class ChampionPerformanceSerializer(serializers.Serializer):
    """Serializer for champion-level account performance."""

    champion_id = serializers.IntegerField()
    champion_name = serializers.CharField()
    game_count = serializers.IntegerField()
    win_rate = serializers.FloatField()
    average_kda = serializers.FloatField()
    average_cs = serializers.FloatField()
    average_gold = serializers.FloatField()
    average_vision_score = serializers.FloatField()
    positions = serializers.ListField(child=serializers.CharField())


class FeedbackSerializer(serializers.Serializer):
    """Serializer for rule-based improvement feedback cards."""

    category = serializers.CharField()
    metric = serializers.CharField()
    value = serializers.FloatField()
    interpretation = serializers.CharField()
    recommendation = serializers.CharField()
    target = serializers.CharField(required=False, allow_null=True, allow_blank=True)
