"""Persistence helpers for Riot match detail and timeline payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.db import transaction

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame


def save_match_detail(match_detail: dict[str, Any]) -> Match:
    """Save a Riot match detail response without calling the Riot API."""

    metadata = match_detail.get("metadata", {})
    info = match_detail.get("info", {})
    match_id = metadata["matchId"]

    with transaction.atomic():
        match, created = Match.objects.get_or_create(
            match_id=match_id,
            defaults={
                "game_version": info.get("gameVersion", ""),
                "queue_id": info.get("queueId", 0),
                "game_start_time": _datetime_from_millis(info.get("gameStartTimestamp", 0)),
                "game_duration": info.get("gameDuration", 0),
                "winning_team_id": _extract_winning_team_id(info.get("teams", [])),
            },
        )

        if not created:
            return match

        participants = [
            _build_participant(match, participant)
            for participant in info.get("participants", [])
        ]
        MatchParticipant.objects.bulk_create(participants, ignore_conflicts=True)

    return match


def save_timeline(match: Match, timeline_detail: dict[str, Any]) -> None:
    """Save minute frames and events from a Riot timeline response."""

    if match.timeline_frames.exists() or match.timeline_events.exists():
        return

    frames = timeline_detail.get("info", {}).get("frames", [])
    timeline_frames: list[TimelineFrame] = []
    timeline_events: list[TimelineEvent] = []

    for frame in frames:
        timestamp = frame.get("timestamp", 0)
        minute = _minute_from_millis(timestamp)

        for participant_id, participant_frame in frame.get("participantFrames", {}).items():
            timeline_frames.append(
                _build_timeline_frame(
                    match=match,
                    minute=minute,
                    participant_id=int(participant_id),
                    participant_frame=participant_frame,
                )
            )

        for event in frame.get("events", []):
            timeline_events.append(
                _build_timeline_event(
                    match=match,
                    minute=_minute_from_millis(event.get("timestamp", timestamp)),
                    event=event,
                )
            )

    with transaction.atomic():
        TimelineFrame.objects.bulk_create(timeline_frames, ignore_conflicts=True)
        TimelineEvent.objects.bulk_create(timeline_events)


def save_match_bundle(match_detail: dict[str, Any], timeline_detail: dict[str, Any] | None = None) -> Match:
    """Save match detail first, then optional timeline data."""

    match = save_match_detail(match_detail)

    if timeline_detail is not None:
        save_timeline(match, timeline_detail)

    return match


def _build_participant(match: Match, participant: dict[str, Any]) -> MatchParticipant:
    return MatchParticipant(
        match=match,
        puuid=participant.get("puuid", ""),
        participant_id=participant.get("participantId", 0),
        team_id=participant.get("teamId", 0),
        champion_id=participant.get("championId", 0),
        champion_name=participant.get("championName", ""),
        individual_position=participant.get("individualPosition", ""),
        win=participant.get("win", False),
        kills=participant.get("kills", 0),
        deaths=participant.get("deaths", 0),
        assists=participant.get("assists", 0),
        total_damage_dealt_to_champions=participant.get("totalDamageDealtToChampions", 0),
        total_damage_taken=participant.get("totalDamageTaken", 0),
        gold_earned=participant.get("goldEarned", 0),
        total_minions_killed=participant.get("totalMinionsKilled", 0),
        neutral_minions_killed=participant.get("neutralMinionsKilled", 0),
        vision_score=participant.get("visionScore", 0),
        wards_placed=participant.get("wardsPlaced", 0),
        wards_killed=participant.get("wardsKilled", 0),
    )


def _build_timeline_frame(
    match: Match,
    minute: int,
    participant_id: int,
    participant_frame: dict[str, Any],
) -> TimelineFrame:
    position = participant_frame.get("position") or {}

    return TimelineFrame(
        match=match,
        minute=minute,
        participant_id=participant_id,
        current_gold=participant_frame.get("currentGold", 0),
        total_gold=participant_frame.get("totalGold", 0),
        level=participant_frame.get("level", 1),
        xp=participant_frame.get("xp", 0),
        minions_killed=participant_frame.get("minionsKilled", 0),
        jungle_minions_killed=participant_frame.get("jungleMinionsKilled", 0),
        position_x=position.get("x"),
        position_y=position.get("y"),
    )


def _build_timeline_event(match: Match, minute: int, event: dict[str, Any]) -> TimelineEvent:
    position = event.get("position") or {}

    return TimelineEvent(
        match=match,
        timestamp=event.get("timestamp", 0),
        minute=minute,
        event_type=event.get("type", ""),
        participant_id=event.get("participantId"),
        killer_id=event.get("killerId"),
        victim_id=event.get("victimId"),
        assisting_participant_ids=event.get("assistingParticipantIds", []),
        monster_type=event.get("monsterType", ""),
        building_type=event.get("buildingType", ""),
        lane_type=event.get("laneType", ""),
        item_id=event.get("itemId"),
        position_x=position.get("x"),
        position_y=position.get("y"),
    )


def _extract_winning_team_id(teams: list[dict[str, Any]]) -> int | None:
    for team in teams:
        if team.get("win"):
            return team.get("teamId")
    return None


def _datetime_from_millis(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def _minute_from_millis(timestamp: int) -> int:
    return timestamp // 1000 // 60
