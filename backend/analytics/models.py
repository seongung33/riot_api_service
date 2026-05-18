"""Models for processed analysis metrics and feedback outputs."""

from django.db import models

from matches.models import Match


class PlayerMatchPhaseMetric(models.Model):
    """Processed per-player phase metrics derived from match and timeline data."""

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
        constraints = [
            models.UniqueConstraint(
                fields=["match", "puuid"],
                name="unique_phase_metric_per_match_player",
            ),
        ]
        indexes = [
            models.Index(fields=["puuid"], name="phase_metric_puuid_idx"),
            models.Index(fields=["champion_id", "position"], name="phase_metric_champ_pos_idx"),
            models.Index(fields=["match", "position"], name="phase_metric_match_pos_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.match.match_id} - {self.puuid[:8]} phase metrics"
