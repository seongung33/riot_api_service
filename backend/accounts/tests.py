"""accounts API와 계정 분석 service의 동작을 검증하는 테스트."""

from copy import deepcopy

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from analytics.models import PlayerMatchPhaseMetric
from matches.tests import sample_match_detail, sample_timeline_detail
from matches.services import save_match_bundle

from .models import RiotAccount


class AccountAnalysisApiTests(TestCase):
    def setUp(self):
        # APIClient는 DRF endpoint를 실제 HTTP 요청처럼 호출해 view/serializer/service 연결을 함께 검증한다.
        self.api_client = APIClient()
        # 계정 분석은 PUUID를 기준으로 MatchParticipant와 연결되므로 테스트 계정도 sample payload의 PUUID와 맞춘다.
        self.account = RiotAccount.objects.create(
            puuid="sample-puuid-1",
            game_name="SampleName",
            tag_line="KR1",
            region="asia",
        )
        # sample match를 저장해 summary/champion/recent match API가 읽을 원본 데이터를 준비한다.
        save_match_bundle(sample_match_detail(), sample_timeline_detail())
        save_match_bundle(_second_match_detail(), sample_timeline_detail())
        self.match = save_match_bundle(sample_match_detail(), sample_timeline_detail())

    def test_recent_matches_endpoint_returns_player_rows(self):
        # 최근 경기 endpoint는 account_id -> PUUID -> MatchParticipant 조회 -> RecentMatchSerializer 응답 흐름을 보장한다.
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
        # summary endpoint는 여러 경기의 승률, 평균 KDA, 평균 CS, 주 포지션 집계가 기대값과 맞는지 확인한다.
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
        # 챔피언 성과 endpoint는 동일 챔피언 플레이를 하나로 묶어 경기 수와 승률을 계산해야 한다.
        response = self.api_client.get(reverse("accounts:champions", args=[self.account.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["champion_name"], "Ahri")
        self.assertEqual(response.data[0]["game_count"], 2)
        self.assertEqual(response.data[0]["win_rate"], 50.0)
        self.assertEqual(response.data[0]["positions"], ["MIDDLE"])

    def test_feedback_endpoint_returns_rule_based_feedback_cards(self):
        # feedback endpoint는 summary 지표가 기준을 넘으면 개선 카드가 만들어지는지 검증한다.
        response = self.api_client.get(reverse("accounts:feedback", args=[self.account.id]))

        self.assertEqual(response.status_code, 200)
        metrics = {row["metric"]: row for row in response.data}
        self.assertIn("average_cs", metrics)
        self.assertEqual(metrics["average_cs"]["category"], "laning")
        self.assertEqual(metrics["average_cs"]["value"], 138.0)
        self.assertIn("CS", metrics["average_cs"]["interpretation"])

    def test_feedback_endpoint_uses_phase_metrics(self):
        # phase metric이 저장돼 있으면 라인전/오브젝트 관련 피드백도 함께 생성되어야 한다.
        participant = self.match.participants.get(puuid=self.account.puuid)
        PlayerMatchPhaseMetric.objects.create(
            match=self.match,
            puuid=self.account.puuid,
            champion_id=participant.champion_id,
            position=participant.individual_position,
            lane_cs_diff_10=10,
            lane_gold_diff_10=500,
            lane_xp_diff_10=300,
            death_before_14=True,
            objective_death_count=2,
        )

        response = self.api_client.get(reverse("accounts:feedback", args=[self.account.id]))

        self.assertEqual(response.status_code, 200)
        metrics = {row["metric"]: row for row in response.data}
        self.assertEqual(metrics["average_lane_cs_diff_10"]["category"], "laning")
        self.assertEqual(metrics["average_lane_cs_diff_10"]["value"], 10.0)
        self.assertEqual(metrics["death_before_14_rate"]["value"], 100.0)
        self.assertEqual(metrics["objective_death_count"]["category"], "objective")

    def test_feedback_endpoint_returns_empty_list_when_account_has_no_matches(self):
        # 저장된 경기가 없는 계정은 피드백을 만들 근거가 없으므로 빈 리스트를 반환한다.
        empty_account = RiotAccount.objects.create(
            puuid="empty-puuid",
            game_name="NoMatch",
            tag_line="KR1",
            region="asia",
        )

        response = self.api_client.get(reverse("accounts:feedback", args=[empty_account.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_phase_metrics_endpoint_returns_stored_account_metrics(self):
        # phase metric endpoint는 분석 모델과 participant 표시 정보를 조합해 응답해야 한다.
        participant = self.match.participants.get(puuid=self.account.puuid)
        PlayerMatchPhaseMetric.objects.create(
            match=self.match,
            puuid=self.account.puuid,
            champion_id=participant.champion_id,
            position=participant.individual_position,
            lane_cs_diff_10=8,
            lane_gold_diff_10=450,
            lane_xp_diff_10=300,
            death_before_14=False,
            objective_death_count=1,
        )

        response = self.api_client.get(reverse("accounts:phase_metrics", args=[self.account.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["match_id"], "KR_1234567890")
        self.assertEqual(response.data[0]["champion_name"], "Ahri")
        self.assertEqual(response.data[0]["lane_cs_diff_10"], 8)
        self.assertEqual(response.data[0]["lane_gold_diff_10"], 450)
        self.assertEqual(response.data[0]["lane_xp_diff_10"], 300)
        self.assertFalse(response.data[0]["death_before_14"])
        self.assertEqual(response.data[0]["objective_death_count"], 1)

    def test_search_endpoint_imports_and_returns_mvp_result(self):
        # search endpoint는 Riot API import service를 호출한 뒤 summary/champion/feedback을 한 응답으로 묶는다.
        # 외부 API 호출은 patch로 대체해 view의 요청/응답 흐름만 안정적으로 검증한다.
        with patch("accounts.views.import_recent_matches_for_account") as import_recent_matches:
            import_recent_matches.return_value = (self.account, ["KR_1234567890"])

            response = self.api_client.post(
                reverse("accounts:search"),
                {
                    "game_name": "SampleName",
                    "tag_line": "KR1",
                    "region": "asia",
                    "count": 1,
                    "queue": 420,
                },
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["account_id"], self.account.id)
        self.assertEqual(response.data["imported_match_ids"], ["KR_1234567890"])
        self.assertEqual(response.data["summary"]["game_count"], 2)
        self.assertEqual(response.data["champions"][0]["champion_name"], "Ahri")
        self.assertTrue(response.data["feedback"])
        import_recent_matches.assert_called_once_with(
            game_name="SampleName",
            tag_line="KR1",
            region="asia",
            count=1,
            queue=420,
        )


def _second_match_detail():
    # 두 번째 경기 payload는 같은 PUUID의 다른 경기 결과를 만들어 평균/승률 집계 테스트에 사용한다.
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
