"""Riot 계정 식별 정보를 저장하는 모델."""

from django.db import models


class RiotAccount(models.Model):
    """Riot ID(gameName#tagLine)를 Riot API의 고유 식별자인 PUUID와 연결한다."""

    # match-v5 API는 Riot ID가 아니라 PUUID를 기준으로 최근 매치를 조회하므로,
    # 계정 검색 시 얻은 PUUID를 계정 분석의 시작점으로 저장한다.
    puuid = models.CharField(max_length=128, unique=True)
    game_name = models.CharField(max_length=100)
    tag_line = models.CharField(max_length=20)
    region = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "riot_account"
        # 같은 지역에서 동일한 Riot ID가 중복 저장되지 않도록 막는다.
        # PUUID는 전역 고유값이지만, 사용자가 다시 검색할 때 Riot ID 기준으로도
        # 같은 계정을 안정적으로 찾을 수 있어야 하므로 복합 유니크 제약을 둔다.
        constraints = [
            models.UniqueConstraint(
                fields=["game_name", "tag_line", "region"],
                name="unique_riot_id_per_region",
            ),
        ]
        # PUUID는 match/participant/phase metric과 연결되는 핵심 키라 조회가 잦다.
        # Riot ID 복합 인덱스는 검색 입력(game_name, tag_line, region)으로
        # 기존 계정 여부를 빠르게 확인하기 위한 용도다.
        indexes = [
            models.Index(fields=["puuid"], name="riot_account_puuid_idx"),
            models.Index(
                fields=["game_name", "tag_line", "region"],
                name="riot_account_riot_id_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.game_name}#{self.tag_line} ({self.region})"
