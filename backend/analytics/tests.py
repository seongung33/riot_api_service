"""Tests for analytics."""

from copy import deepcopy

from django.test import TestCase

from matches.services import save_match_bundle
from matches.tests import sample_match_detail, sample_timeline_detail

from .models import PlayerMatchPhaseMetric
from .services import calculate_account_phase_metrics, calculate_match_phase_metrics


class PhaseMetricServiceTests(TestCase):
    def test_calculate_match_phase_metrics_compares_lane_frames(self):
        match = save_match_bundle(_phase_match_detail(), _phase_timeline_detail())

        metrics = calculate_match_phase_metrics(match)

        self.assertEqual(len(metrics), 2)
        self.assertEqual(PlayerMatchPhaseMetric.objects.count(), 2)

        player_metric = PlayerMatchPhaseMetric.objects.get(puuid="sample-puuid-1")
        self.assertEqual(player_metric.lane_cs_diff_10, 8)
        self.assertEqual(player_metric.lane_gold_diff_10, 450)
        self.assertEqual(player_metric.lane_xp_diff_10, 300)
        self.assertFalse(player_metric.death_before_14)
        self.assertEqual(player_metric.objective_death_count, 0)

        opponent_metric = PlayerMatchPhaseMetric.objects.get(puuid="sample-puuid-2")
        self.assertEqual(opponent_metric.lane_cs_diff_10, -8)
        self.assertEqual(opponent_metric.lane_gold_diff_10, -450)
        self.assertEqual(opponent_metric.lane_xp_diff_10, -300)
        self.assertTrue(opponent_metric.death_before_14)
        self.assertEqual(opponent_metric.objective_death_count, 1)

    def test_calculate_match_phase_metrics_updates_existing_rows(self):
        match = save_match_bundle(_phase_match_detail(), _phase_timeline_detail())

        first_metrics = calculate_match_phase_metrics(match)
        second_metrics = calculate_match_phase_metrics(match)

        self.assertEqual([metric.id for metric in first_metrics], [metric.id for metric in second_metrics])
        self.assertEqual(PlayerMatchPhaseMetric.objects.count(), 2)

    def test_calculate_account_phase_metrics_returns_only_requested_player_metrics(self):
        match = save_match_bundle(_phase_match_detail(), _phase_timeline_detail())

        metrics = calculate_account_phase_metrics("sample-puuid-1")

        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].match, match)
        self.assertEqual(metrics[0].puuid, "sample-puuid-1")


def _phase_match_detail():
    payload = deepcopy(sample_match_detail())
    payload["metadata"]["matchId"] = "KR_PHASE_0001"
    return payload


def _phase_timeline_detail():
    payload = deepcopy(sample_timeline_detail())
    payload["metadata"]["matchId"] = "KR_PHASE_0001"
    frames = payload["info"]["frames"]
    frames.append(
        {
            "timestamp": 600000,
            "participantFrames": {
                "1": {
                    "currentGold": 650,
                    "totalGold": 3600,
                    "level": 8,
                    "xp": 4600,
                    "minionsKilled": 76,
                    "jungleMinionsKilled": 2,
                    "position": {"x": 5500, "y": 5300},
                },
                "2": {
                    "currentGold": 300,
                    "totalGold": 3150,
                    "level": 7,
                    "xp": 4300,
                    "minionsKilled": 68,
                    "jungleMinionsKilled": 2,
                    "position": {"x": 5600, "y": 5400},
                },
            },
            "events": [
                {
                    "timestamp": 570000,
                    "type": "CHAMPION_KILL",
                    "killerId": 1,
                    "victimId": 2,
                    "assistingParticipantIds": [],
                    "position": {"x": 9000, "y": 4200},
                },
                {
                    "timestamp": 600000,
                    "type": "ELITE_MONSTER_KILL",
                    "killerId": 1,
                    "monsterType": "DRAGON",
                    "position": {"x": 9866, "y": 4414},
                },
            ],
        }
    )
    return payload
