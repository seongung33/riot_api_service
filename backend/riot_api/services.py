"""Riot API에서 계정/매치 데이터를 가져와 저장하는 application service."""

from __future__ import annotations

from accounts.models import RiotAccount
from analytics.services import calculate_match_phase_metrics
from matches.services import save_match_bundle

from .client import RiotApiClient


def import_recent_matches_for_account(
    *,
    game_name: str,
    tag_line: str,
    region: str = "asia",
    count: int = 5,
    queue: int | None = 420,
) -> tuple[RiotAccount, list[str]]:
    """Riot ID로 계정을 찾고 최근 match detail/timeline을 저장한다."""

    # region은 Account-V1/Match-V5 regional route(예: asia)를 의미한다.
    # Riot ID -> PUUID -> match_id 목록 -> match detail/timeline 순서로 호출해야 데이터가 이어진다.
    client = RiotApiClient(regional_route=region)
    account_data = client.get_account_by_riot_id(game_name, tag_line)
    match_ids = client.get_match_ids_by_puuid(
        account_data["puuid"],
        count=count,
        queue=queue,
    )

    # PUUID는 Riot 계정의 안정적인 고유 식별자라 update_or_create의 기준으로 사용한다.
    # Riot ID가 바뀌거나 다시 검색되어도 같은 PUUID라면 기존 계정 row를 갱신한다.
    account, _ = RiotAccount.objects.update_or_create(
        puuid=account_data["puuid"],
        defaults={
            "game_name": account_data.get("gameName", game_name),
            "tag_line": account_data.get("tagLine", tag_line),
            "region": region,
        },
    )

    imported_match_ids = []
    for match_id in match_ids:
        # 각 match_id마다 detail은 최종 통계 저장에, timeline은 phase metric 계산에 필요하다.
        # 두 payload를 모두 저장한 뒤 분석 metric을 계산해야 feedback API가 최신 데이터를 사용할 수 있다.
        match_detail = client.get_match_detail(match_id)
        timeline_detail = client.get_match_timeline(match_id)
        match = save_match_bundle(match_detail, timeline_detail)
        calculate_match_phase_metrics(match)
        imported_match_ids.append(match.match_id)

    # view는 account 정보와 실제 저장된 match_id 목록을 응답으로 내려준다.
    return account, imported_match_ids
