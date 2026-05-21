"""Riot API client와 import workflow를 검증하는 테스트."""

from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import RiotAccount
from analytics.models import PlayerMatchPhaseMetric
from matches.models import Match, MatchParticipant, TimelineEvent, TimelineFrame
from matches.tests import sample_match_detail, sample_timeline_detail

from .client import RiotApiClient, RiotApiError


class RiotApiClientTests(TestCase):
    @patch("riot_api.client.requests.Session.get")
    def test_get_account_by_riot_id_encodes_path_and_uses_api_key_header(self, mock_get):
        # Riot ID의 공백이 URL path에서 인코딩되고, API key가 헤더로 전달되는지 확인한다.
        mock_get.return_value = Mock(status_code=200, json=lambda: {"puuid": "sample-puuid"})
        client = RiotApiClient(api_key="test-key", regional_route="asia")

        result = client.get_account_by_riot_id("Hide on bush", "KR1")

        self.assertEqual(result["puuid"], "sample-puuid")
        mock_get.assert_called_once()
        url = mock_get.call_args.args[0]
        headers = mock_get.call_args.kwargs["headers"]
        self.assertIn("Hide%20on%20bush", url)
        self.assertEqual(headers["X-Riot-Token"], "test-key")

    @patch("riot_api.client.requests.Session.get")
    def test_riot_api_error_is_raised_for_error_status(self, mock_get):
        # Riot API가 4xx/5xx를 반환하면 view에서 처리할 수 있도록 RiotApiError로 올려야 한다.
        mock_get.return_value = Mock(status_code=403, json=lambda: {"status": "forbidden"})
        client = RiotApiClient(api_key="test-key", regional_route="asia")

        with self.assertRaises(RiotApiError):
            client.get_match_detail("KR_1234567890")


class ImportRecentMatchesViewTests(TestCase):
    def test_import_recent_matches_saves_account_and_match_payloads(self):
        # 외부 Riot API는 mock으로 대체하고,
        # import endpoint가 계정/경기/timeline/phase metric 저장까지 이어지는지 검증한다.
        api_client = APIClient()

        with patch("riot_api.services.RiotApiClient") as client_class:
            riot_client = client_class.return_value
            riot_client.get_account_by_riot_id.return_value = {
                "puuid": "sample-puuid-1",
                "gameName": "SampleName",
                "tagLine": "KR1",
            }
            riot_client.get_match_ids_by_puuid.return_value = ["KR_1234567890"]
            riot_client.get_match_detail.return_value = sample_match_detail()
            riot_client.get_match_timeline.return_value = sample_timeline_detail()

            response = api_client.post(
                reverse("riot_api:import_recent_matches"),
                {
                    "game_name": "SampleName",
                    "tag_line": "KR1",
                    "region": "asia",
                    "count": 1,
                    "queue": 420,
                },
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(RiotAccount.objects.count(), 1)
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(MatchParticipant.objects.count(), 2)
        self.assertEqual(TimelineFrame.objects.count(), 4)
        self.assertEqual(TimelineEvent.objects.count(), 2)
        self.assertEqual(PlayerMatchPhaseMetric.objects.count(), 2)
        self.assertEqual(response.data["imported_match_ids"], ["KR_1234567890"])
