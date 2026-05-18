"""Tests for accounts."""

from copy import deepcopy

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from matches.tests import sample_match_detail, sample_timeline_detail
from matches.services import save_match_bundle

from .models import RiotAccount


class AccountAnalysisApiTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.account = RiotAccount.objects.create(
            puuid="sample-puuid-1",
            game_name="SampleName",
            tag_line="KR1",
            region="asia",
        )
        save_match_bundle(sample_match_detail(), sample_timeline_detail())
        save_match_bundle(_second_match_detail(), sample_timeline_detail())

    def test_recent_matches_endpoint_returns_player_rows(self):
        response = self.api_client.get(
            reverse("accounts:recent_matches", args=[self.account.id]),
            {"limit": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["match_id"], "KR_1234567891")
        self.assertEqual(response.data[0]["champion_name"], "Ahri")
        self.assertEqual(response.data[0]["kda"], 9.0)
        self.assertEqual(response.data[0]["total_cs"], 151)

    def test_summary_endpoint_returns_basic_recent_metrics(self):
        response = self.api_client.get(reverse("accounts:summary", args=[self.account.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["game_count"], 2)
        self.assertEqual(response.data["win_rate"], 50.0)
        self.assertEqual(response.data["average_kda"], 7.33)
        self.assertEqual(response.data["average_deaths"], 2.5)
        self.assertEqual(response.data["average_cs"], 138.0)
        self.assertEqual(response.data["main_position"], "MIDDLE")
        self.assertEqual(response.data["champion_pool"], ["Ahri"])

    def test_champions_endpoint_returns_champion_performance(self):
        response = self.api_client.get(reverse("accounts:champions", args=[self.account.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["champion_name"], "Ahri")
        self.assertEqual(response.data[0]["game_count"], 2)
        self.assertEqual(response.data[0]["win_rate"], 50.0)
        self.assertEqual(response.data[0]["positions"], ["MIDDLE"])


def _second_match_detail():
    payload = deepcopy(sample_match_detail())
    payload["metadata"]["matchId"] = "KR_1234567891"
    payload["info"]["gameStartTimestamp"] = 1779066000000
    payload["info"]["teams"] = [
        {"teamId": 100, "win": False},
        {"teamId": 200, "win": True},
    ]

    player = payload["info"]["participants"][0]
    player.update(
        {
            "win": False,
            "kills": 6,
            "deaths": 2,
            "assists": 12,
            "goldEarned": 13200,
            "totalMinionsKilled": 144,
            "neutralMinionsKilled": 7,
            "visionScore": 28,
        }
    )
    return payload
