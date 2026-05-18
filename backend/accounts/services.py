"""Read-side account analysis helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from analytics.models import PlayerMatchPhaseMetric
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
                "average_kda": _round(sum(_kda(row.kills, row.deaths, row.assists) for row in rows) / game_count),
                "average_cs": _average([row.total_cs for row in rows]),
                "average_gold": _average([row.gold_earned for row in rows]),
                "average_vision_score": _average([row.vision_score for row in rows]),
                "positions": sorted({row.individual_position for row in rows if row.individual_position}),
            }
        )

    return sorted(summaries, key=lambda row: (-row["game_count"], row["champion_name"]))


def get_account_feedback(account: RiotAccount, limit: int = 20) -> list[dict[str, Any]]:
    """Return rule-based feedback cards from recent match and phase metrics."""

    summary = get_account_summary(account, limit=limit)
    if summary["game_count"] == 0:
        return []

    feedback = []
    phase_summary = _summarize_phase_metrics(account, limit=limit)

    if phase_summary["game_count"] > 0:
        _add_phase_feedback(feedback, phase_summary)

    if summary["average_deaths"] >= 6:
        feedback.append(
            {
                "category": "survival",
                "metric": "average_deaths",
                "value": summary["average_deaths"],
                "interpretation": "최근 경기의 평균 데스가 높은 편입니다.",
                "recommendation": "불리한 교전은 줄이고, 주요 오브젝트 1분 전에는 무리한 사이드 압박보다 시야 확보와 합류를 우선해보세요.",
            }
        )

    if summary["average_cs"] < 150:
        feedback.append(
            {
                "category": "laning",
                "metric": "average_cs",
                "value": summary["average_cs"],
                "interpretation": "최근 경기의 전체 CS 수급이 낮은 편입니다.",
                "recommendation": "초반 라인전뿐 아니라 중반 사이드 웨이브 회수까지 포함해, 빈 라인을 놓치는 시간을 줄여보세요.",
            }
        )

    if summary["average_vision_score"] < 20:
        feedback.append(
            {
                "category": "vision",
                "metric": "average_vision_score",
                "value": summary["average_vision_score"],
                "interpretation": "최근 경기의 시야 점수가 낮은 편입니다.",
                "recommendation": "라인 복귀 전 제어 와드를 준비하고, 드래곤과 전령이 나오기 전에 강가 시야를 먼저 잡아보세요.",
            }
        )

    if summary["win_rate"] < 45:
        feedback.append(
            {
                "category": "overall",
                "metric": "win_rate",
                "value": summary["win_rate"],
                "interpretation": "최근 경기 승률이 낮아 개선 우선순위를 정할 필요가 있습니다.",
                "recommendation": "다음 경기에서는 챔피언 폭을 넓히기보다 가장 익숙한 챔피언 1~2개로 플레이 패턴을 안정화해보세요.",
            }
        )

    weak_champion = _find_weak_champion(account, limit=limit)
    if weak_champion is not None:
        feedback.append(
            {
                "category": "champion_pool",
                "metric": "champion_win_rate",
                "value": weak_champion["win_rate"],
                "target": weak_champion["champion_name"],
                "interpretation": f"{weak_champion['champion_name']}의 최근 승률이 낮은 편입니다.",
                "recommendation": "해당 챔피언을 계속 사용한다면 라인전 손실, 데스 타이밍, 오브젝트 합류 중 어느 구간에서 손해가 나는지 먼저 확인해보세요.",
            }
        )

    return feedback


def get_phase_metrics(account: RiotAccount, limit: int = 20) -> list[dict[str, Any]]:
    """Return stored phase metrics for one Riot account."""

    metrics = list(
        PlayerMatchPhaseMetric.objects.filter(puuid=account.puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")[:limit]
    )

    participant_map = {
        participant.match_id: participant
        for participant in MatchParticipant.objects.filter(
            puuid=account.puuid,
            match_id__in=[metric.match_id for metric in metrics],
        )
    }

    return [_serialize_phase_metric(metric, participant_map.get(metric.match_id)) for metric in metrics]


def _account_participants(account: RiotAccount):
    return (
        MatchParticipant.objects.filter(puuid=account.puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")
    )


def _add_phase_feedback(feedback: list[dict[str, Any]], phase_summary: dict[str, Any]) -> None:
    avg_cs_diff = phase_summary["average_lane_cs_diff_10"]
    avg_gold_diff = phase_summary["average_lane_gold_diff_10"]
    avg_xp_diff = phase_summary["average_lane_xp_diff_10"]
    objective_deaths = phase_summary["objective_death_count"]
    early_death_rate = phase_summary["death_before_14_rate"]

    if avg_cs_diff is not None and avg_cs_diff <= -8:
        feedback.append(
            {
                "category": "laning",
                "metric": "average_lane_cs_diff_10",
                "value": avg_cs_diff,
                "interpretation": "최근 경기에서 10분 CS 차이가 상대보다 낮은 편입니다.",
                "recommendation": "첫 귀환 전 웨이브를 무리하게 버리지 말고, 10분 전까지 라인 손실과 정글 합류 타이밍을 함께 점검해보세요.",
            }
        )
    elif avg_cs_diff is not None and avg_cs_diff >= 8:
        feedback.append(
            {
                "category": "laning",
                "metric": "average_lane_cs_diff_10",
                "value": avg_cs_diff,
                "interpretation": "최근 경기에서 10분 CS 차이가 좋은 편입니다.",
                "recommendation": "라인전에서 만든 CS 우위를 귀환 타이밍, 시야 장악, 첫 오브젝트 합류로 연결하는 데 집중해보세요.",
            }
        )

    if avg_gold_diff is not None and avg_xp_diff is not None and avg_gold_diff < 0 and avg_xp_diff < 0:
        feedback.append(
            {
                "category": "laning",
                "metric": "lane_gold_xp_diff_10",
                "value": avg_gold_diff,
                "interpretation": "10분 골드와 경험치가 함께 밀리는 경향이 있습니다.",
                "recommendation": "초반 교전보다 라인 경험치 손실을 줄이는 선택을 우선하고, 불리한 매치업에서는 라인을 당겨 안정적으로 성장해보세요.",
            }
        )

    if early_death_rate >= 30:
        feedback.append(
            {
                "category": "laning",
                "metric": "death_before_14_rate",
                "value": early_death_rate,
                "interpretation": "14분 이전 데스가 자주 발생하고 있습니다.",
                "recommendation": "상대 정글 위치가 보이지 않을 때는 라인을 깊게 밀기보다 와드 타이밍과 미니언 위치를 먼저 확인해보세요.",
            }
        )

    if objective_deaths >= 2:
        feedback.append(
            {
                "category": "objective",
                "metric": "objective_death_count",
                "value": float(objective_deaths),
                "interpretation": "주요 오브젝트 직전에 죽는 횟수가 누적되고 있습니다.",
                "recommendation": "드래곤과 전령 1분 전에는 사이드 압박보다 귀환, 아이템 정비, 강가 시야 확보를 먼저 실행해보세요.",
            }
        )


def _summarize_phase_metrics(account: RiotAccount, limit: int) -> dict[str, Any]:
    metrics = list(
        PlayerMatchPhaseMetric.objects.filter(puuid=account.puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")[:limit]
    )

    return {
        "game_count": len(metrics),
        "average_lane_cs_diff_10": _average_optional([metric.lane_cs_diff_10 for metric in metrics]),
        "average_lane_gold_diff_10": _average_optional([metric.lane_gold_diff_10 for metric in metrics]),
        "average_lane_xp_diff_10": _average_optional([metric.lane_xp_diff_10 for metric in metrics]),
        "death_before_14_rate": _percent(sum(1 for metric in metrics if metric.death_before_14), len(metrics)),
        "objective_death_count": sum(metric.objective_death_count for metric in metrics),
    }


def _find_weak_champion(account: RiotAccount, limit: int) -> dict[str, Any] | None:
    weak_champions = [
        champion
        for champion in get_champion_performance(account, limit=limit)
        if champion["game_count"] >= 2 and champion["win_rate"] < 50
    ]
    if not weak_champions:
        return None
    return sorted(weak_champions, key=lambda row: (row["win_rate"], -row["game_count"], row["champion_name"]))[0]


def _serialize_phase_metric(
    metric: PlayerMatchPhaseMetric,
    participant: MatchParticipant | None,
) -> dict[str, Any]:
    return {
        "match_id": metric.match.match_id,
        "game_start_time": metric.match.game_start_time,
        "champion_id": metric.champion_id,
        "champion_name": participant.champion_name if participant is not None else "",
        "position": metric.position,
        "lane_cs_diff_10": metric.lane_cs_diff_10,
        "lane_gold_diff_10": metric.lane_gold_diff_10,
        "lane_xp_diff_10": metric.lane_xp_diff_10,
        "death_before_14": metric.death_before_14,
        "objective_death_count": metric.objective_death_count,
    }


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


def _average_optional(values: list[int | None]) -> float | None:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return _round(sum(valid_values) / len(valid_values))


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
