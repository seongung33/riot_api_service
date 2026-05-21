"""Riot 계정 조회와 분석 요약을 제공하는 APIView 모음."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from riot_api.client import RiotApiError
from riot_api.services import import_recent_matches_for_account

from .models import RiotAccount
from .serializers import (
    AccountSearchRequestSerializer,
    AccountSummarySerializer,
    ChampionPerformanceSerializer,
    FeedbackSerializer,
    PhaseMetricSerializer,
    RecentMatchSerializer,
)
from .services import (
    get_account_feedback,
    get_account_summary,
    get_champion_performance,
    get_phase_metrics,
    get_recent_matches,
)


class AccountRecentMatchesView(APIView):
    """저장된 계정의 최근 경기 행을 반환한다."""

    def get(self, request, account_id: int):
        # get_object_or_404는 id가 잘못된 경우 직접 예외 처리를 하지 않아도
        # DRF/Django가 404 응답으로 바꿔주기 때문에 APIView 흐름이 단순해진다.
        account = get_object_or_404(RiotAccount, id=account_id)
        # limit query parameter는 사용자가 볼 경기 수를 조절하되,
        # 과도한 조회를 막기 위해 _query_limit에서 상한을 적용한다.
        limit = _query_limit(request, default=20, maximum=100)
        # service에서 ORM 조회 결과를 화면용 dict로 만들고,
        # serializer가 최종 JSON 응답 필드 형태로 변환한다.
        serializer = RecentMatchSerializer(get_recent_matches(account, limit=limit), many=True)
        return Response(serializer.data)


class AccountSummaryView(APIView):
    """저장된 계정의 최근 경기 요약 지표를 반환한다."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        # 요약 API는 여러 participant row를 집계한 결과이므로 모델 serializer가 아니라
        # AccountSummarySerializer로 계산된 dict의 응답 구조를 명확히 고정한다.
        serializer = AccountSummarySerializer(get_account_summary(account, limit=limit))
        return Response(serializer.data)


class AccountChampionPerformanceView(APIView):
    """저장된 계정의 챔피언별 성과를 반환한다."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=50, maximum=200)
        # many=True는 service가 반환한 여러 챔피언 summary dict를
        # 동일한 필드 구조의 리스트 응답으로 직렬화한다는 뜻이다.
        serializer = ChampionPerformanceSerializer(
            get_champion_performance(account, limit=limit),
            many=True,
        )
        return Response(serializer.data)


class AccountSearchView(APIView):
    """Riot ID로 최근 경기를 가져오고, 첫 화면에 필요한 MVP 요약 응답을 만든다."""

    def post(self, request):
        # 요청 body를 먼저 serializer로 검증해 Riot API 호출 전에 기본값과 숫자 범위를 확정한다.
        # validated_data를 사용하면 문자열/숫자 변환과 필수값 검증이 끝난 안전한 데이터만 service로 전달된다.
        request_serializer = AccountSearchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        try:
            # Riot ID로 PUUID를 먼저 얻고, PUUID로 match-v5 최근 매치 id를 가져온 뒤,
            # 각 match detail/timeline을 저장하고 phase metric까지 계산하는 import 흐름이다.
            account, imported_match_ids = import_recent_matches_for_account(
                game_name=data["game_name"],
                tag_line=data["tag_line"],
                region=data["region"],
                count=data["count"],
                queue=data["queue"],
            )
        except RiotApiError as exc:
            # 외부 Riot API 실패는 우리 서버의 validation 오류가 아니므로 502로 감싸서
            # 프론트가 "상위 API 호출 실패"로 해석할 수 있게 한다.
            return Response(
                {"detail": str(exc), "status_code": exc.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # import가 끝난 직후 DB에 저장된 participant/phase metric을 다시 읽어
        # 프론트 첫 화면에 필요한 summary, champion table, feedback을 한 번에 내려준다.
        summary = AccountSummarySerializer(get_account_summary(account)).data
        champions = ChampionPerformanceSerializer(get_champion_performance(account), many=True).data
        feedback = FeedbackSerializer(get_account_feedback(account), many=True).data

        return Response(
            {
                "account_id": account.id,
                "puuid": account.puuid,
                "game_name": account.game_name,
                "tag_line": account.tag_line,
                "region": account.region,
                "imported_match_ids": imported_match_ids,
                "summary": summary,
                "champions": champions,
                "feedback": feedback,
            },
            status=status.HTTP_200_OK,
        )


class AccountFeedbackView(APIView):
    """저장된 계정의 룰 기반 피드백 카드를 반환한다."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = FeedbackSerializer(get_account_feedback(account, limit=limit), many=True)
        return Response(serializer.data)


class AccountPhaseMetricView(APIView):
    """저장된 계정의 최근 phase metric을 반환한다."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = PhaseMetricSerializer(get_phase_metrics(account, limit=limit), many=True)
        return Response(serializer.data)


def _query_limit(request, default: int, maximum: int) -> int:
    # API 사용자가 limit을 잘못 보내도 서버 오류로 만들지 않고 기본값으로 복구한다.
    # max/min 조합은 최소 1개 이상, 최대 maximum 이하만 조회하도록 방어한다.
    try:
        limit = int(request.query_params.get("limit", default))
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, maximum))
