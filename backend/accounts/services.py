"""Read-side account analysis helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from matches.models import MatchParticipant

from .models import RiotAccount


def get_recent_matches(account: RiotAccount, limit: int = 20) -> list[dict[str, Any]]:
    """Return recent match rows for one Riot account."""

    participants = _account_participants(account)[:limit]

    return [_serialize_recent_match(participant) for participant in participants]


def get_account_summary(account: RiotAccount, limit: int = 20) -> dict[str, Any]:
    """Return basic recent-game summary metrics for one Riot account."""

    participants = list(_account_participants(account)[:limit])
    game_count = len(participants)

    if game_count == 0:
        return {
            "account_id": account.id,
            "puuid": account.puuid,
            "game_name": account.game_name,
            "tag_line": account.tag_line,
            "region": account.region,
            "game_count": 0,
            "win_rate": 0.0,
            "average_kda": 0.0,
            "average_kills": 0.0,
            "average_deaths": 0.0,
            "average_assists": 0.0,
            "average_cs": 0.0,
            "average_gold": 0.0,
            "average_vision_score": 0.0,
            "main_position": None,
            "champion_pool": [],
        }

    wins = sum(1 for participant in participants if participant.win)
    position_counts = Counter(participant.individual_position for participant in participants)
    champion_counts = Counter(participant.champion_name for participant in participants)

    return {
        "account_id": account.id,
        "puuid": account.puuid,
        "game_name": account.game_name,
        "tag_line": account.tag_line,
        "region": account.region,
        "game_count": game_count,
        "win_rate": _percent(wins, game_count),
        "average_kda": _round(
            sum(_kda(participant.kills, participant.deaths, participant.assists) for participant in participants)
            / game_count
        ),
        "average_kills": _average([participant.kills for participant in participants]),
        "average_deaths": _average([participant.deaths for participant in participants]),
        "average_assists": _average([participant.assists for participant in participants]),
        "average_cs": _average([participant.total_cs for participant in participants]),
        "average_gold": _average([participant.gold_earned for participant in participants]),
        "average_vision_score": _average([participant.vision_score for participant in participants]),
        "main_position": position_counts.most_common(1)[0][0] if position_counts else None,
        "champion_pool": [champion for champion, _ in champion_counts.most_common()],
    }


def get_champion_performance(account: RiotAccount, limit: int = 50) -> list[dict[str, Any]]:
    """Return champion-level performance summaries for one Riot account."""

    participants = list(_account_participants(account)[:limit])
    champion_rows: dict[str, list[MatchParticipant]] = defaultdict(list)

    for participant in participants:
        champion_rows[participant.champion_name].append(participant)

    summaries = []
    for champion_name, rows in champion_rows.items():
        game_count = len(rows)
        wins = sum(1 for row in rows if row.win)
        summaries.append(
            {
                "champion_id": rows[0].champion_id,
                "champion_name": champion_name,
                "game_count": game_count,
                "win_rate": _percent(wins, game_count),
                "average_kda": _round(
                    sum(_kda(row.kills, row.deaths, row.assists) for row in rows) / game_count
                ),
                "average_cs": _average([row.total_cs for row in rows]),
                "average_gold": _average([row.gold_earned for row in rows]),
                "average_vision_score": _average([row.vision_score for row in rows]),
                "positions": sorted({row.individual_position for row in rows if row.individual_position}),
            }
        )

    return sorted(summaries, key=lambda row: (-row["game_count"], row["champion_name"]))


def _account_participants(account: RiotAccount):
    return (
        MatchParticipant.objects.filter(puuid=account.puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")
    )


def _serialize_recent_match(participant: MatchParticipant) -> dict[str, Any]:
    match = participant.match

    return {
        "match_id": match.match_id,
        "game_version": match.game_version,
        "queue_id": match.queue_id,
        "game_start_time": match.game_start_time,
        "game_duration": match.game_duration,
        "champion_id": participant.champion_id,
        "champion_name": participant.champion_name,
        "individual_position": participant.individual_position,
        "win": participant.win,
        "kills": participant.kills,
        "deaths": participant.deaths,
        "assists": participant.assists,
        "kda": _kda(participant.kills, participant.deaths, participant.assists),
        "total_cs": participant.total_cs,
        "gold_earned": participant.gold_earned,
        "vision_score": participant.vision_score,
        "total_damage_dealt_to_champions": participant.total_damage_dealt_to_champions,
        "total_damage_taken": participant.total_damage_taken,
    }


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return _round(sum(values) / len(values))


def _kda(kills: int, deaths: int, assists: int) -> float:
    if deaths == 0:
        return float(kills + assists)
    return _round((kills + assists) / deaths)


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return _round(numerator / denominator * 100)


def _round(value: float) -> float:
    return round(value, 2)
