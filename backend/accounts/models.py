"""Models for Riot account identity data."""

from django.db import models


class RiotAccount(models.Model):
    """A Riot account searched by Riot ID and resolved to a PUUID."""

    puuid = models.CharField(max_length=128, unique=True)
    game_name = models.CharField(max_length=100)
    tag_line = models.CharField(max_length=20)
    region = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "riot_account"
        constraints = [
            models.UniqueConstraint(
                fields=["game_name", "tag_line", "region"],
                name="unique_riot_id_per_region",
            ),
        ]
        indexes = [
            models.Index(fields=["puuid"], name="riot_account_puuid_idx"),
            models.Index(
                fields=["game_name", "tag_line", "region"],
                name="riot_account_riot_id_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.game_name}#{self.tag_line} ({self.region})"
