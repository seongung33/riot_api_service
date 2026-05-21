"""timeline과 participant 원본 데이터로 phase metric을 계산하는 service."""

from __future__ import annotations

from matches.models import Match, MatchParticipant, TimelineEvent, TimelineFrame

from .models import PlayerMatchPhaseMetric


OBJECTIVE_MONSTER_TYPES = {"DRAGON", "RIFTHERALD", "BARON_NASHOR"}
# 라인전 지표는 초반 주도권을 보기 위해 10분 시점을 기준으로 삼는다.
LANE_METRIC_MINUTE = 10
# 14분 전은 포탑 방패와 라인전 영향이 큰 구간이라 early death 기준으로 사용한다.
EARLY_DEATH_LIMIT_MINUTE = 14
# 오브젝트 직전 60초 안의 데스는 드래곤/전령/바론 교전 준비 실패로 해석하기 쉽다.
OBJECTIVE_DEATH_WINDOW_MS = 60_000


def calculate_match_phase_metrics(match: Match) -> list[PlayerMatchPhaseMetric]:
    """한 경기의 모든 participant에 대해 phase metric을 계산하고 저장한다."""

    metrics = []
    # match.participants는 MatchParticipant.related_name으로 연결된 10명의 최종 통계다.
    # list로 고정해 같은 경기의 상대 라이너 탐색을 메모리에서 반복 수행한다.
    participants = list(match.participants.all())

    for participant in participants:
        # 라인전 비교는 같은 포지션의 상대 팀 participant와 비교해야 의미가 있다.
        opponent = _find_lane_opponent(participant, participants)
        lane_diffs = _calculate_lane_diffs(match, participant, opponent)
        # update_or_create는 같은 match+puuid metric을 다시 계산할 때 새 row를 만들지 않고 갱신한다.
        # Riot match import를 재실행하거나 분석 로직을 보강해도 최신 계산 결과가 한 row에 유지된다.
        metric, _ = PlayerMatchPhaseMetric.objects.update_or_create(
            match=match,
            puuid=participant.puuid,
            defaults={
                "champion_id": participant.champion_id,
                "position": participant.individual_position,
                "lane_cs_diff_10": lane_diffs["cs"],
                "lane_gold_diff_10": lane_diffs["gold"],
                "lane_xp_diff_10": lane_diffs["xp"],
                "death_before_14": _has_death_before_14(match, participant),
                "objective_death_count": _count_objective_deaths(match, participant),
            },
        )
        metrics.append(metric)

    return metrics


def calculate_account_phase_metrics(puuid: str, limit: int = 20) -> list[PlayerMatchPhaseMetric]:
    """특정 PUUID가 참여한 최근 경기들의 phase metric을 계산한다."""

    # 계정 기준 분석은 MatchParticipant.puuid에서 시작한다.
    # select_related("match")는 경기 정렬과 calculate_match_phase_metrics 호출 때 필요한 Match를 함께 가져온다.
    participants = (
        MatchParticipant.objects.filter(puuid=puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")[:limit]
    )

    metrics = []
    for participant in participants:
        # 한 경기를 계산하면 양 팀 모든 participant metric이 만들어진다.
        # 이 함수는 요청한 계정의 metric만 반환해야 하므로 puuid로 다시 필터링한다.
        metrics.extend(
            metric
            for metric in calculate_match_phase_metrics(participant.match)
            if metric.puuid == puuid
        )
    return metrics


def _find_lane_opponent(
    participant: MatchParticipant,
    participants: list[MatchParticipant],
) -> MatchParticipant | None:
    # Riot API의 individualPosition이 비어 있으면 라인 상대를 신뢰할 수 없으므로 diff 계산을 생략한다.
    if not participant.individual_position:
        return None

    for candidate in participants:
        # 같은 포지션이면서 팀이 다른 participant를 라인 상대라고 본다.
        # 이 단순 규칙은 솔로랭크 일반 포지션 분석에 충분하고, 별도 매칭 테이블 없이 계산 가능하다.
        if (
            candidate.team_id != participant.team_id
            and candidate.individual_position == participant.individual_position
        ):
            return candidate
    return None


def _calculate_lane_diffs(
    match: Match,
    participant: MatchParticipant,
    opponent: MatchParticipant | None,
) -> dict[str, int | None]:
    # 10분 시점 또는 그 직전 frame을 비교해 라인전 초반 성장 차이를 계산한다.
    # frame이 없거나 상대를 찾지 못한 경우 None으로 두어 평균 계산에서 제외한다.
    player_frame = _get_frame_at_or_before(match, participant.participant_id, LANE_METRIC_MINUTE)
    opponent_frame = (
        _get_frame_at_or_before(match, opponent.participant_id, LANE_METRIC_MINUTE)
        if opponent is not None
        else None
    )

    if player_frame is None or opponent_frame is None:
        return {"cs": None, "gold": None, "xp": None}

    player_cs = player_frame.minions_killed + player_frame.jungle_minions_killed
    opponent_cs = opponent_frame.minions_killed + opponent_frame.jungle_minions_killed

    return {
        # 양수면 해당 플레이어가 상대보다 앞선 상태, 음수면 뒤처진 상태로 해석한다.
        "cs": player_cs - opponent_cs,
        "gold": player_frame.total_gold - opponent_frame.total_gold,
        "xp": player_frame.xp - opponent_frame.xp,
    }


def _get_frame_at_or_before(
    match: Match,
    participant_id: int,
    minute: int,
) -> TimelineFrame | None:
    # timeline frame이 정확히 10분에 없을 수도 있으므로 minute__lte로 이전 frame까지 허용하고,
    # order_by("-minute").first()로 기준 시점에 가장 가까운 스냅샷을 사용한다.
    return (
        TimelineFrame.objects.filter(
            match=match,
            participant_id=participant_id,
            minute__lte=minute,
        )
        .order_by("-minute")
        .first()
    )


def _has_death_before_14(match: Match, participant: MatchParticipant) -> bool:
    # 14분 전 CHAMPION_KILL의 victim이면 라인전 단계에서 사망한 것으로 본다.
    # exists()는 실제 row 전체를 가져오지 않고 존재 여부만 확인해 효율적이다.
    return TimelineEvent.objects.filter(
        match=match,
        event_type="CHAMPION_KILL",
        victim_id=participant.participant_id,
        minute__lt=EARLY_DEATH_LIMIT_MINUTE,
    ).exists()


def _count_objective_deaths(match: Match, participant: MatchParticipant) -> int:
    # 먼저 플레이어의 모든 사망 이벤트와 주요 오브젝트 처치 이벤트를 나눠 가져온다.
    # 두 이벤트의 timestamp 차이를 비교해 "오브젝트 직전 사망"을 계산한다.
    death_events = TimelineEvent.objects.filter(
        match=match,
        event_type="CHAMPION_KILL",
        victim_id=participant.participant_id,
    )
    objective_events = TimelineEvent.objects.filter(
        match=match,
        event_type="ELITE_MONSTER_KILL",
        monster_type__in=OBJECTIVE_MONSTER_TYPES,
    )

    count = 0
    for death in death_events:
        for objective in objective_events:
            # death 이후 60초 안에 오브젝트가 처치되면,
            # 해당 데스가 팀의 오브젝트 손실 또는 교전 실패와 연결됐을 가능성이 높다고 본다.
            if 0 <= objective.timestamp - death.timestamp <= OBJECTIVE_DEATH_WINDOW_MS:
                count += 1
                break
    return count
