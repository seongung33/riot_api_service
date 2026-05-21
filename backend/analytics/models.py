"""원본 match/timeline에서 계산한 분석 지표를 저장하는 모델."""

from django.db import models

from matches.models import Match


class PlayerMatchPhaseMetric(models.Model):
    """한 경기의 한 플레이어에 대해 phase별 분석 결과를 저장한다."""

    # MatchParticipant는 원본 경기 통계이고, PlayerMatchPhaseMetric은 그 원본을 해석한 결과다.
    # match+puuid 조합으로 "이 경기에서 이 계정이 어떤 구간 성과를 냈는지"를 표현한다.
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="phase_metrics")
    puuid = models.CharField(max_length=128, db_index=True)
    champion_id = models.PositiveIntegerField()
    position = models.CharField(max_length=20, blank=True)
    lane_cs_diff_10 = models.IntegerField(null=True, blank=True)
    lane_gold_diff_10 = models.IntegerField(null=True, blank=True)
    lane_xp_diff_10 = models.IntegerField(null=True, blank=True)
    death_before_14 = models.BooleanField(default=False)
    objective_death_count = models.PositiveSmallIntegerField(default=0)
    teamfight_participation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percent participation in identified teamfight events.",
    )
    side_death_count = models.PositiveSmallIntegerField(default=0)
    lane_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    objective_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    teamfight_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    side_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "player_match_phase_metric"
        # 같은 경기의 같은 플레이어 phase metric은 하나만 존재해야 한다.
        # calculate_match_phase_metrics가 update_or_create를 쓰는 이유도 이 제약과 맞물려 있다.
        constraints = [
            models.UniqueConstraint(
                fields=["match", "puuid"],
                name="unique_phase_metric_per_match_player",
            ),
        ]
        # puuid 인덱스는 계정별 최근 phase metric 조회에 사용된다.
        # champion/position, match/position 인덱스는 챔피언/라인별 분석을 확장할 때 유용하다.
        indexes = [
            models.Index(fields=["puuid"], name="phase_metric_puuid_idx"),
            models.Index(fields=["champion_id", "position"], name="phase_metric_champ_pos_idx"),
            models.Index(fields=["match", "position"], name="phase_metric_match_pos_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.match.match_id} - {self.puuid[:8]} phase metrics"
