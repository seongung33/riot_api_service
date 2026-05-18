"""Application services for Riot API import workflows."""

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
    """Fetch a Riot account and recent matches, then persist them locally."""

    client = RiotApiClient(regional_route=region)
    account_data = client.get_account_by_riot_id(game_name, tag_line)
    match_ids = client.get_match_ids_by_puuid(
        account_data["puuid"],
        count=count,
        queue=queue,
    )

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
        match_detail = client.get_match_detail(match_id)
        timeline_detail = client.get_match_timeline(match_id)
        match = save_match_bundle(match_detail, timeline_detail)
        calculate_match_phase_metrics(match)
        imported_match_ids.append(match.match_id)

    return account, imported_match_ids
