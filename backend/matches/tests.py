"""match detail/timeline 저장 service를 검증하는 테스트."""

from django.test import TestCase

from .models import Match, MatchParticipant, TimelineEvent, TimelineFrame
from .services import save_match_bundle


class MatchPersistenceServiceTests(TestCase):
    def test_save_match_bundle_persists_sample_riot_payload(self):
        # detail과 timeline을 함께 저장했을 때 Match, Participant, Frame, Event가 모두 생성되는지 확인한다.
        match = save_match_bundle(sample_match_detail(), sample_timeline_detail())

        self.assertEqual(match.match_id, "KR_1234567890")
        self.assertEqual(match.queue_id, 420)
        self.assertEqual(match.winning_team_id, 100)
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(MatchParticipant.objects.count(), 2)
        self.assertEqual(TimelineFrame.objects.count(), 4)
        self.assertEqual(TimelineEvent.objects.count(), 2)

        ahri = MatchParticipant.objects.get(puuid="sample-puuid-1")
        self.assertEqual(ahri.champion_name, "Ahri")
        self.assertEqual(ahri.total_cs, 125)
        self.assertTrue(ahri.win)

        frame = TimelineFrame.objects.get(match=match, minute=1, participant_id=1)
        self.assertEqual(frame.total_gold, 560)
        self.assertEqual(frame.position_x, 5200)

        event = TimelineEvent.objects.get(event_type="CHAMPION_KILL")
        self.assertEqual(event.killer_id, 1)
        self.assertEqual(event.victim_id, 2)
        self.assertEqual(event.assisting_participant_ids, [3, 5])

    def test_save_match_bundle_does_not_duplicate_existing_match(self):
        # 같은 match_id를 다시 저장해도 get_or_create와 중복 방어 로직 때문에 row가 늘어나면 안 된다.
        first_match = save_match_bundle(sample_match_detail(), sample_timeline_detail())
        second_match = save_match_bundle(sample_match_detail(), sample_timeline_detail())

        self.assertEqual(first_match.id, second_match.id)
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(MatchParticipant.objects.count(), 2)
        self.assertEqual(TimelineFrame.objects.count(), 4)
        self.assertEqual(TimelineEvent.objects.count(), 2)


def sample_match_detail():
    # Riot match-v5 detail 응답 형태를 최소한으로 흉내 낸 fixture다.
    # participant 최종 통계와 team 승패가 Match/MatchParticipant 저장의 원본이 된다.
    return {
        "metadata": {
            "matchId": "KR_1234567890",
            "participants": ["sample-puuid-1", "sample-puuid-2"],
        },
        "info": {
            "gameVersion": "16.10.1",
            "queueId": 420,
            "gameStartTimestamp": 1779062400000,
            "gameDuration": 1800,
            "teams": [
                {"teamId": 100, "win": True},
                {"teamId": 200, "win": False},
            ],
            "participants": [
                {
                    "puuid": "sample-puuid-1",
                    "participantId": 1,
                    "teamId": 100,
                    "championId": 103,
                    "championName": "Ahri",
                    "individualPosition": "MIDDLE",
                    "win": True,
                    "kills": 8,
                    "deaths": 3,
                    "assists": 9,
                    "totalDamageDealtToChampions": 22000,
                    "totalDamageTaken": 13000,
                    "goldEarned": 12500,
                    "totalMinionsKilled": 118,
                    "neutralMinionsKilled": 7,
                    "visionScore": 24,
                    "wardsPlaced": 10,
                    "wardsKilled": 3,
                },
                {
                    "puuid": "sample-puuid-2",
                    "participantId": 2,
                    "teamId": 200,
                    "championId": 157,
                    "championName": "Yasuo",
                    "individualPosition": "MIDDLE",
                    "win": False,
                    "kills": 5,
                    "deaths": 8,
                    "assists": 4,
                    "totalDamageDealtToChampions": 18000,
                    "totalDamageTaken": 21000,
                    "goldEarned": 10800,
                    "totalMinionsKilled": 132,
                    "neutralMinionsKilled": 2,
                    "visionScore": 15,
                    "wardsPlaced": 7,
                    "wardsKilled": 1,
                },
            ],
        },
    }


def sample_timeline_detail():
    # Riot timeline 응답 형태를 흉내 낸 fixture다.
    # frame은 분 단위 성장 지표, event는 처치/아이템/오브젝트 분석의 원본으로 쓰인다.
    return {
        "metadata": {"matchId": "KR_1234567890"},
        "info": {
            "frames": [
                {
                    "timestamp": 0,
                    "participantFrames": {
                        "1": {
                            "currentGold": 500,
                            "totalGold": 500,
                            "level": 1,
                            "xp": 0,
                            "minionsKilled": 0,
                            "jungleMinionsKilled": 0,
                            "position": {"x": 5000, "y": 5000},
                        },
                        "2": {
                            "currentGold": 500,
                            "totalGold": 500,
                            "level": 1,
                            "xp": 0,
                            "minionsKilled": 0,
                            "jungleMinionsKilled": 0,
                            "position": {"x": 5200, "y": 5200},
                        },
                    },
                    "events": [],
                },
                {
                    "timestamp": 60000,
                    "participantFrames": {
                        "1": {
                            "currentGold": 180,
                            "totalGold": 560,
                            "level": 2,
                            "xp": 280,
                            "minionsKilled": 6,
                            "jungleMinionsKilled": 0,
                            "position": {"x": 5200, "y": 5100},
                        },
                        "2": {
                            "currentGold": 120,
                            "totalGold": 530,
                            "level": 2,
                            "xp": 260,
                            "minionsKilled": 5,
                            "jungleMinionsKilled": 0,
                            "position": {"x": 5300, "y": 5150},
                        },
                    },
                    "events": [
                        {
                            "timestamp": 45000,
                            "type": "ITEM_PURCHASED",
                            "participantId": 1,
                            "itemId": 1056,
                        },
                        {
                            "timestamp": 59000,
                            "type": "CHAMPION_KILL",
                            "killerId": 1,
                            "victimId": 2,
                            "assistingParticipantIds": [3, 5],
                            "position": {"x": 5250, "y": 5120},
                        },
                    ],
                },
            ]
        },
    }
