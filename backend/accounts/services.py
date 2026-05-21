"""계정 화면에서 필요한 읽기 전용 분석 데이터를 만드는 service."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from analytics.models import PlayerMatchPhaseMetric
from matches.models import MatchParticipant

from .models import RiotAccount


def get_recent_matches(account: RiotAccount, limit: int = 20) -> list[dict[str, Any]]:
    """한 계정의 최근 경기 목록을 participant 중심 행으로 반환한다."""

    # RiotAccount의 PUUID와 MatchParticipant.puuid가 연결점이다.
    # match detail 저장 시 participant별 PUUID가 들어가므로, 계정별 최근 경기는 participant 테이블에서 시작한다.
    participants = _account_participants(account)[:limit]

    return [_serialize_recent_match(participant) for participant in participants]


def get_account_summary(account: RiotAccount, limit: int = 20) -> dict[str, Any]:
    """최근 경기들을 모아 승률/평균 KDA/주 포지션 같은 계정 요약 지표를 만든다."""

    # QuerySet을 list로 고정해 같은 participant 묶음을 여러 번 순회하며 집계한다.
    # 이후 win rate, 평균값, champion pool 모두 동일한 최근 경기 범위를 기준으로 계산된다.
    participants = list(_account_participants(account)[:limit])
    game_count = len(participants)

    if game_count == 0:
        # 아직 import된 경기가 없는 계정도 프론트가 동일한 응답 구조를 기대하므로
        # None/빈 리스트/0.0으로 채운 기본 summary를 반환한다.
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

    # Counter는 "가장 많이 나온 포지션/챔피언"을 구하기 위해 사용한다.
    # 주 포지션과 champion pool은 포트폴리오 설명에서 플레이 성향을 요약하는 지표가 된다.
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
    """최근 경기를 챔피언 이름별로 묶어 챔피언별 성과를 계산한다."""

    participants = list(_account_participants(account)[:limit])
    champion_rows: dict[str, list[MatchParticipant]] = defaultdict(list)

    # 같은 챔피언으로 플레이한 경기들을 한 그룹으로 묶어야
    # 챔피언별 승률/평균 KDA/평균 CS가 의미 있는 비교 지표가 된다.
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

    # 많이 플레이한 챔피언을 먼저 보여주고, 경기 수가 같으면 이름순으로 정렬해 응답 순서를 안정화한다.
    return sorted(summaries, key=lambda row: (-row["game_count"], row["champion_name"]))


def get_account_feedback(account: RiotAccount, limit: int = 20) -> list[dict[str, Any]]:
    """최근 경기 요약과 phase metric을 기반으로 룰 기반 개선 피드백을 만든다."""

    summary = get_account_summary(account, limit=limit)
    if summary["game_count"] == 0:
        return []

    feedback = []
    # phase metric은 단순 KDA보다 "언제/어떤 구간에서 손해가 났는지"를 설명한다.
    # 라인전 10분 차이, 14분 전 데스, 오브젝트 직전 데스는 개선 액션으로 연결하기 쉽다.
    phase_summary = _summarize_phase_metrics(account, limit=limit)

    if phase_summary["game_count"] > 0:
        _add_phase_feedback(feedback, phase_summary)

    if summary["average_deaths"] >= 6:
        # 평균 데스가 높으면 KDA뿐 아니라 오브젝트 합류와 시야 장악 타이밍도 흔들리기 쉽다.
        # 그래서 생존 카테고리 피드백으로 우선순위를 알려준다.
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
        # 평균 CS는 성장 안정성을 보는 가장 직관적인 지표다.
        # 낮은 CS는 라인전 손실뿐 아니라 사이드 웨이브 회수 부족으로도 해석할 수 있다.
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
        # vision score가 낮으면 갱킹 회피, 오브젝트 준비, 사이드 운영 판단의 근거가 줄어든다.
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
        # 낮은 승률은 개별 지표보다 넓은 문제 신호라서 챔피언 폭/운영 안정성 관점으로 안내한다.
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
        # 충분히 여러 번 플레이했지만 승률이 낮은 챔피언은 개선 우선순위를 잡기 좋은 대상이다.
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
    """저장된 phase metric을 최근 경기 순으로 반환한다."""

    # PlayerMatchPhaseMetric은 match FK를 갖고 있으므로 select_related로 match를 함께 가져온다.
    # 이렇게 하면 serializer용 dict를 만들 때 match.game_start_time 접근으로 추가 쿼리가 늘어나는 일을 줄인다.
    metrics = list(
        PlayerMatchPhaseMetric.objects.filter(puuid=account.puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")[:limit]
    )

    # phase metric에는 champion_name이 없고 champion_id만 있으므로,
    # 같은 match_id의 MatchParticipant를 찾아 화면 표시용 챔피언 이름을 보강한다.
    participant_map = {
        participant.match_id: participant
        for participant in MatchParticipant.objects.filter(
            puuid=account.puuid,
            match_id__in=[metric.match_id for metric in metrics],
        )
    }

    return [_serialize_phase_metric(metric, participant_map.get(metric.match_id)) for metric in metrics]


def _account_participants(account: RiotAccount):
    # 계정 분석의 기본 조회 단위는 MatchParticipant다.
    # filter(puuid=...)로 해당 계정의 경기 참여 row만 고르고,
    # select_related("match")로 경기 시작 시간 정렬에 필요한 Match를 함께 로드한다.
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
        # 10분 CS 차이가 -8 이하이면 초반 라인 주도권이나 웨이브 관리에서 밀린 것으로 해석한다.
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
        # 반대로 +8 이상이면 라인전 우위를 만든 상태라서, 그 우위를 오브젝트/시야로 전환하는 방향을 제안한다.
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
        # 골드와 경험치가 모두 뒤처지면 단순 CS 손실보다 성장 곡선 전체가 늦는 상황으로 본다.
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
        # 14분 전 데스는 라인전 단계의 손해를 크게 키우므로 비율로 집계해 반복 패턴을 찾는다.
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
        # 오브젝트 직전 데스는 팀이 드래곤/전령/바론을 시도하거나 막을 인원 수를 잃는 문제라 별도 카테고리로 본다.
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
    # 최근 N경기의 phase metric을 평균/합계로 압축한다.
    # lane diff는 경기마다 상대가 다르므로 평균 방향성을 보고, objective death는 누적 횟수로 위험도를 본다.
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
    # 1판만 한 챔피언은 표본이 너무 작으므로 2판 이상이면서 승률이 낮은 챔피언만 개선 대상으로 본다.
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
    # 저장 모델에는 분석 계산에 필요한 값만 있으므로,
    # API 응답에서는 match 시작 시각과 champion_name을 합쳐 화면에서 바로 렌더링할 수 있게 만든다.
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

    # 최근 경기 행은 Match의 경기 메타데이터와 MatchParticipant의 개인 성과를 합친 형태다.
    # 프론트는 이 평탄화된 구조 덕분에 별도 조인 로직 없이 리스트를 렌더링할 수 있다.
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
    # lane opponent를 찾지 못했거나 timeline frame이 부족한 경기는 None이 될 수 있다.
    # 그런 결측치는 평균에서 제외해야 실제 계산 가능한 경기만 반영된다.
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return _round(sum(valid_values) / len(valid_values))


def _kda(kills: int, deaths: int, assists: int) -> float:
    # death가 0이면 나눗셈이 불가능하므로 kills+assists를 그대로 사용한다.
    # 무데스 경기는 일반 KDA 공식에서도 매우 높은 생존 성과로 해석한다.
    if deaths == 0:
        return float(kills + assists)
    return _round((kills + assists) / deaths)


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return _round(numerator / denominator * 100)


def _round(value: float) -> float:
    return round(value, 2)
