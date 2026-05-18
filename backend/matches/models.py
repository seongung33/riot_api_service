"""Models for raw Riot match and timeline data."""

from django.db import models


class Match(models.Model):
    """Raw match-level metadata from Riot match detail responses."""

    match_id = models.CharField(max_length=32, unique=True)
    game_version = models.CharField(max_length=40, blank=True)
    queue_id = models.PositiveIntegerField()
    game_start_time = models.DateTimeField()
    game_duration = models.PositiveIntegerField(help_text="Game duration in seconds.")
    winning_team_id = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "match"
        indexes = [
            models.Index(fields=["match_id"], name="match_match_id_idx"),
            models.Index(fields=["queue_id", "game_start_time"], name="match_queue_start_idx"),
            models.Index(fields=["game_version"], name="match_game_version_idx"),
        ]

    def __str__(self) -> str:
        return self.match_id


class MatchParticipant(models.Model):
    """Per-player raw stats from a Riot match detail response."""

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
        indexes = [
            models.Index(fields=["puuid"], name="participant_puuid_idx"),
            models.Index(fields=["champion_name", "individual_position"], name="participant_champ_pos_idx"),
            models.Index(fields=["match", "team_id"], name="participant_match_team_idx"),
        ]

    @property
    def total_cs(self) -> int:
        return self.total_minions_killed + self.neutral_minions_killed

    def __str__(self) -> str:
        return f"{self.match.match_id} - P{self.participant_id} {self.champion_name}"


class TimelineFrame(models.Model):
    """Minute-level participant state from Riot timeline frames."""

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
        constraints = [
            models.UniqueConstraint(
                fields=["match", "minute", "participant_id"],
                name="unique_frame_per_minute_participant",
            ),
        ]
        indexes = [
            models.Index(fields=["match", "minute"], name="frame_match_minute_idx"),
            models.Index(fields=["participant_id", "minute"], name="frame_participant_minute_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.match.match_id} - {self.minute}m P{self.participant_id}"


class TimelineEvent(models.Model):
    """Raw timeline event data used for phase and objective analysis."""

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
        indexes = [
            models.Index(fields=["match", "minute"], name="event_match_minute_idx"),
            models.Index(fields=["event_type"], name="event_type_idx"),
            models.Index(fields=["monster_type"], name="event_monster_type_idx"),
            models.Index(fields=["victim_id", "minute"], name="event_victim_minute_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.match.match_id} - {self.event_type} @ {self.minute}m"
