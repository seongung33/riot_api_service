"""Views for Riot account lookup and account summaries."""

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
    """Return a stored account's recent match rows."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = RecentMatchSerializer(get_recent_matches(account, limit=limit), many=True)
        return Response(serializer.data)


class AccountSummaryView(APIView):
    """Return basic recent performance metrics for a stored account."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = AccountSummarySerializer(get_account_summary(account, limit=limit))
        return Response(serializer.data)


class AccountChampionPerformanceView(APIView):
    """Return champion-level performance metrics for a stored account."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=50, maximum=200)
        serializer = ChampionPerformanceSerializer(
            get_champion_performance(account, limit=limit),
            many=True,
        )
        return Response(serializer.data)


class AccountSearchView(APIView):
    """Import recent matches by Riot ID and return MVP summary data."""

    def post(self, request):
        request_serializer = AccountSearchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        try:
            account, imported_match_ids = import_recent_matches_for_account(
                game_name=data["game_name"],
                tag_line=data["tag_line"],
                region=data["region"],
                count=data["count"],
                queue=data["queue"],
            )
        except RiotApiError as exc:
            return Response(
                {"detail": str(exc), "status_code": exc.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )

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
    """Return rule-based feedback cards for a stored account."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = FeedbackSerializer(get_account_feedback(account, limit=limit), many=True)
        return Response(serializer.data)


class AccountPhaseMetricView(APIView):
    """Return stored phase metrics for a stored account."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = PhaseMetricSerializer(get_phase_metrics(account, limit=limit), many=True)
        return Response(serializer.data)


def _query_limit(request, default: int, maximum: int) -> int:
    try:
        limit = int(request.query_params.get("limit", default))
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, maximum))
