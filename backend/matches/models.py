"""Riot match detail과 timeline 원본 데이터를 저장하는 모델."""

from django.db import models


class Match(models.Model):
    """Riot match detail 응답의 경기 단위 메타데이터."""

    # match_id는 Riot API가 부여하는 경기 고유값이며,
    # participant/timeline/phase metric이 모두 이 Match를 기준으로 연결된다.
    match_id = models.CharField(max_length=32, unique=True)
    game_version = models.CharField(max_length=40, blank=True)
    queue_id = models.PositiveIntegerField()
    game_start_time = models.DateTimeField()
    game_duration = models.PositiveIntegerField(help_text="Game duration in seconds.")
    winning_team_id = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "match"
        # 최근 경기 조회는 queue와 시작 시각을 함께 쓰는 경우가 많고,
        # 패치 버전별 분석을 확장할 수 있도록 game_version에도 인덱스를 둔다.
        indexes = [
            models.Index(fields=["match_id"], name="match_match_id_idx"),
            models.Index(fields=["queue_id", "game_start_time"], name="match_queue_start_idx"),
            models.Index(fields=["game_version"], name="match_game_version_idx"),
        ]

    def __str__(self) -> str:
        return self.match_id


class MatchParticipant(models.Model):
    """Riot match detail 응답에서 가져온 플레이어별 최종 통계."""

    # 한 Match에는 10명의 participant가 연결된다.
    # RiotAccount와 직접 FK를 걸지 않고 PUUID 문자열을 저장하는 이유는,
    # 검색하지 않은 상대 플레이어도 같은 구조로 저장할 수 있어야 하기 때문이다.
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="participants")
    puuid = models.CharField(max_length=128, db_index=True)
    participant_id = models.PositiveSmallIntegerField()
    team_id = models.PositiveSmallIntegerField()
    champion_id = models.PositiveIntegerField()
    champion_name = models.CharField(max_length=80)
    individual_position = models.CharField(max_length=20, blank=True)
    win = models.BooleanField()
    kills = models.PositiveSmallIntegerField(default=0)
    deaths = models.PositiveSmallIntegerField(default=0)
    assists = models.PositiveSmallIntegerField(default=0)
    total_damage_dealt_to_champions = models.PositiveIntegerField(default=0)
    total_damage_taken = models.PositiveIntegerField(default=0)
    gold_earned = models.PositiveIntegerField(default=0)
    total_minions_killed = models.PositiveIntegerField(default=0)
    neutral_minions_killed = models.PositiveIntegerField(default=0)
    vision_score = models.PositiveIntegerField(default=0)
    wards_placed = models.PositiveIntegerField(default=0)
    wards_killed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "match_participant"
        # participant_id는 한 경기 안에서 1~10으로 식별되는 timeline용 번호이고,
        # puuid는 계정 단위 분석에 쓰이는 전역 식별자다. 두 기준 모두 중복되면 안 된다.
        constraints = [
            models.UniqueConstraint(
                fields=["match", "participant_id"],
                name="unique_participant_per_match",
            ),
            models.UniqueConstraint(
                fields=["match", "puuid"],
                name="unique_puuid_per_match",
            ),
        ]
        # puuid 인덱스는 계정별 최근 경기 조회의 핵심이다.
        # champion/position 인덱스는 챔피언 성과나 포지션별 분석을 확장할 때 조회 비용을 줄인다.
        indexes = [
            models.Index(fields=["puuid"], name="participant_puuid_idx"),
            models.Index(fields=["champion_name", "individual_position"], name="participant_champ_pos_idx"),
            models.Index(fields=["match", "team_id"], name="participant_match_team_idx"),
        ]

    @property
    def total_cs(self) -> int:
        # Riot API는 라인 미니언과 정글 몬스터 처치를 나눠 제공한다.
        # 화면과 요약 지표에서는 둘을 더한 총 CS가 더 직관적이라 property로 계산한다.
        return self.total_minions_killed + self.neutral_minions_killed

    def __str__(self) -> str:
        return f"{self.match.match_id} - P{self.participant_id} {self.champion_name}"


class TimelineFrame(models.Model):
    """Riot timeline frame에서 가져온 분 단위 participant 상태."""

    # timeline frame은 "특정 분의 특정 participant 상태"를 나타낸다.
    # 10분 CS/골드/경험치 차이 같은 phase metric은 이 테이블의 스냅샷을 비교해 만든다.
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="timeline_frames")
    minute = models.PositiveSmallIntegerField()
    participant_id = models.PositiveSmallIntegerField()
    current_gold = models.PositiveIntegerField(default=0)
    total_gold = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    minions_killed = models.PositiveIntegerField(default=0)
    jungle_minions_killed = models.PositiveIntegerField(default=0)
    position_x = models.IntegerField(null=True, blank=True)
    position_y = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "timeline_frame"
        # 같은 경기, 같은 분, 같은 participant의 frame은 하나만 있어야 한다.
        # save_timeline을 여러 번 호출해도 중복 frame이 생기지 않도록 DB 레벨에서 보호한다.
        constraints = [
            models.UniqueConstraint(
                fields=["match", "minute", "participant_id"],
                name="unique_frame_per_minute_participant",
            ),
        ]
        # match+minute 인덱스는 특정 경기의 10분 전후 frame을 찾을 때 사용하고,
        # participant_id+minute 인덱스는 한 플레이어의 시간대별 상태 조회에 유리하다.
        indexes = [
            models.Index(fields=["match", "minute"], name="frame_match_minute_idx"),
            models.Index(fields=["participant_id", "minute"], name="frame_participant_minute_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.match.match_id} - {self.minute}m P{self.participant_id}"


class TimelineEvent(models.Model):
    """phase와 objective 분석에 쓰는 Riot timeline 이벤트 원본."""

    # event는 처치, 아이템 구매, 오브젝트 처치처럼 시간 순서가 중요한 기록이다.
    # objective_death_count는 CHAMPION_KILL과 ELITE_MONSTER_KILL의 timestamp 차이를 비교해 계산한다.
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="timeline_events")
    timestamp = models.PositiveIntegerField(help_text="Event timestamp in milliseconds.")
    minute = models.PositiveSmallIntegerField()
    event_type = models.CharField(max_length=60)
    participant_id = models.PositiveSmallIntegerField(null=True, blank=True)
    killer_id = models.PositiveSmallIntegerField(null=True, blank=True)
    victim_id = models.PositiveSmallIntegerField(null=True, blank=True)
    assisting_participant_ids = models.JSONField(default=list, blank=True)
    monster_type = models.CharField(max_length=40, blank=True)
    building_type = models.CharField(max_length=40, blank=True)
    lane_type = models.CharField(max_length=40, blank=True)
    item_id = models.PositiveIntegerField(null=True, blank=True)
    position_x = models.IntegerField(null=True, blank=True)
    position_y = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "timeline_event"
        # 이벤트 분석은 "어느 경기의 몇 분", "어떤 이벤트 타입", "어떤 오브젝트",
        # "누가 죽었는지"로 필터링하는 일이 많아 해당 필드에 인덱스를 둔다.
        indexes = [
            models.Index(fields=["match", "minute"], name="event_match_minute_idx"),
            models.Index(fields=["event_type"], name="event_type_idx"),
            models.Index(fields=["monster_type"], name="event_monster_type_idx"),
            models.Index(fields=["victim_id", "minute"], name="event_victim_minute_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.match.match_id} - {self.event_type} @ {self.minute}m"
