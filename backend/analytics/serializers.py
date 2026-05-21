"""분석 지표 API 응답을 위한 DRF serializer."""

from rest_framework import serializers

from .models import PlayerMatchPhaseMetric


class PlayerMatchPhaseMetricSerializer(serializers.ModelSerializer):
    """PlayerMatchPhaseMetric 모델을 JSON 응답 구조로 변환한다."""

    class Meta:
        model = PlayerMatchPhaseMetric
        # phase metric은 계산 결과이므로 일반적으로 클라이언트가 직접 수정하지 않고,
        # 백엔드 분석 service가 저장한 값을 읽기 API에서 내려주는 용도다.
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
