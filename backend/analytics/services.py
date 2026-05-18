"""Phase metric calculation helpers."""

from __future__ import annotations

from matches.models import Match, MatchParticipant, TimelineEvent, TimelineFrame

from .models import PlayerMatchPhaseMetric


OBJECTIVE_MONSTER_TYPES = {"DRAGON", "RIFTHERALD", "BARON_NASHOR"}
LANE_METRIC_MINUTE = 10
EARLY_DEATH_LIMIT_MINUTE = 14
OBJECTIVE_DEATH_WINDOW_MS = 60_000


def calculate_match_phase_metrics(match: Match) -> list[PlayerMatchPhaseMetric]:
    """Calculate and persist phase metrics for every participant in one match."""

    metrics = []
    participants = list(match.participants.all())

    for participant in participants:
        opponent = _find_lane_opponent(participant, participants)
        lane_diffs = _calculate_lane_diffs(match, participant, opponent)
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
    """Calculate recent phase metrics for matches played by one account."""

    participants = (
        MatchParticipant.objects.filter(puuid=puuid)
        .select_related("match")
        .order_by("-match__game_start_time", "-match__id")[:limit]
    )

    metrics = []
    for participant in participants:
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
    if not participant.individual_position:
        return None

    for candidate in participants:
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
        "cs": player_cs - opponent_cs,
        "gold": player_frame.total_gold - opponent_frame.total_gold,
        "xp": player_frame.xp - opponent_frame.xp,
    }


def _get_frame_at_or_before(
    match: Match,
    participant_id: int,
    minute: int,
) -> TimelineFrame | None:
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
    return TimelineEvent.objects.filter(
        match=match,
        event_type="CHAMPION_KILL",
        victim_id=participant.participant_id,
        minute__lt=EARLY_DEATH_LIMIT_MINUTE,
    ).exists()


def _count_objective_deaths(match: Match, participant: MatchParticipant) -> int:
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
            if 0 <= objective.timestamp - death.timestamp <= OBJECTIVE_DEATH_WINDOW_MS:
                count += 1
                break
    return count
