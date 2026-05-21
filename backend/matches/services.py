"""Riot match detail과 timeline payload를 DB에 저장하는 service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.db import transaction

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame


def save_match_detail(match_detail: dict[str, Any]) -> Match:
    """이미 받아온 Riot match detail 응답을 DB에 저장한다."""

    # 이 함수는 API 호출을 직접 하지 않고 저장만 담당한다.
    # Riot API client와 persistence를 분리해 테스트에서는 sample payload만으로 저장 흐름을 검증할 수 있다.
    metadata = match_detail.get("metadata", {})
    info = match_detail.get("info", {})
    match_id = metadata["matchId"]

    with transaction.atomic():
        # get_or_create는 같은 match_id가 이미 저장된 경우 기존 Match를 재사용한다.
        # 최근 경기 import를 반복해도 match/participant가 중복 생성되지 않아야 하기 때문이다.
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
            # 기존 Match가 있다면 participant도 이미 저장된 것으로 보고 조기 반환한다.
            # 이 분기 덕분에 import 재시도 시 같은 경기의 상세 row가 늘어나지 않는다.
            return match

        # Riot match detail의 participants 배열은 플레이어별 최종 결과다.
        # bulk_create로 10명 데이터를 한 번에 넣어 저장 쿼리 수를 줄인다.
        participants = [
            _build_participant(match, participant)
            for participant in info.get("participants", [])
        ]
        MatchParticipant.objects.bulk_create(participants, ignore_conflicts=True)

    return match


def save_timeline(match: Match, timeline_detail: dict[str, Any]) -> None:
    """Riot timeline 응답에서 minute frame과 event를 저장한다."""

    if match.timeline_frames.exists() or match.timeline_events.exists():
        # timeline은 한 경기당 한 번만 저장되면 충분하다.
        # 이미 frame/event가 있으면 재import 시 중복 분석 데이터가 생기지 않도록 종료한다.
        return

    frames = timeline_detail.get("info", {}).get("frames", [])
    timeline_frames: list[TimelineFrame] = []
    timeline_events: list[TimelineEvent] = []

    for frame in frames:
        # Riot timeline은 frame 단위로 participantFrames와 events를 함께 제공한다.
        # frame timestamp를 분으로 바꿔 라인전 10분 지표처럼 사람이 해석하기 쉬운 단위로 저장한다.
        timestamp = frame.get("timestamp", 0)
        minute = _minute_from_millis(timestamp)

        for participant_id, participant_frame in frame.get("participantFrames", {}).items():
            # participantFrames는 participant_id를 문자열 key로 내려주므로 int로 변환해 모델에 맞춘다.
            timeline_frames.append(
                _build_timeline_frame(
                    match=match,
                    minute=minute,
                    participant_id=int(participant_id),
                    participant_frame=participant_frame,
                )
            )

        for event in frame.get("events", []):
            # event timestamp는 frame timestamp와 다를 수 있어 event 자체 timestamp를 우선 사용한다.
            # 이렇게 해야 오브젝트 직전 데스처럼 밀리초 단위 순서가 중요한 분석이 정확해진다.
            timeline_events.append(
                _build_timeline_event(
                    match=match,
                    minute=_minute_from_millis(event.get("timestamp", timestamp)),
                    event=event,
                )
            )

    with transaction.atomic():
        # frame과 event는 한 timeline 안에서 함께 저장되어야 이후 phase metric 계산 기준이 일관된다.
        TimelineFrame.objects.bulk_create(timeline_frames, ignore_conflicts=True)
        TimelineEvent.objects.bulk_create(timeline_events)


def save_match_bundle(match_detail: dict[str, Any], timeline_detail: dict[str, Any] | None = None) -> Match:
    """match detail을 먼저 저장하고, 있으면 timeline까지 이어서 저장한다."""

    # MatchParticipant가 Match FK를 필요로 하므로 detail 저장이 항상 먼저다.
    # timeline은 phase metric 계산의 재료이므로 import workflow에서는 detail 뒤에 저장한다.
    match = save_match_detail(match_detail)

    if timeline_detail is not None:
        save_timeline(match, timeline_detail)

    return match


def _build_participant(match: Match, participant: dict[str, Any]) -> MatchParticipant:
    # Riot API 필드명은 camelCase이고 Django 모델 필드는 snake_case다.
    # 이 변환 레이어를 한 곳에 모아두면 저장 구조를 이해하고 테스트하기 쉽다.
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
    # position은 일부 frame/event에서 없을 수 있으므로 빈 dict로 대체해 안전하게 x/y를 꺼낸다.
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
    # 모든 event가 participantId, monsterType, position을 갖는 것은 아니다.
    # 없는 값은 None 또는 빈 문자열로 저장해 이벤트 타입별 차이를 허용한다.
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
    # match detail의 teams 배열에서 win=True인 팀을 찾아 경기 결과를 Match에 요약 저장한다.
    for team in teams:
        if team.get("win"):
            return team.get("teamId")
    return None


def _datetime_from_millis(timestamp: int) -> datetime:
    # Riot API timestamp는 밀리초 단위 Unix time이므로 Django DateTimeField에 맞게 UTC datetime으로 변환한다.
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def _minute_from_millis(timestamp: int) -> int:
    # phase metric은 10분, 14분처럼 분 단위 기준을 쓰므로 밀리초 timestamp를 정수 minute로 압축한다.
    return timestamp // 1000 // 60
