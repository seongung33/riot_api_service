"""DRF serializers for analytics endpoints."""

from rest_framework import serializers

from .models import PlayerMatchPhaseMetric


class PlayerMatchPhaseMetricSerializer(serializers.ModelSerializer):
    """Serializer for processed per-player phase metrics."""

    class Meta:
        model = PlayerMatchPhaseMetric
        fields = [
            "id",
            "match",
            "puuid",
            "champion_id",
            "position",
            "lane_cs_diff_10",
            "lane_gold_diff_10",
            "lane_xp_diff_10",
            "death_before_14",
            "objective_death_count",
            "teamfight_participation",
            "side_death_count",
            "lane_score",
            "objective_score",
            "teamfight_score",
            "side_score",
        ]
        read_only_fields = ["id"]
