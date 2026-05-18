"""Views for Riot account lookup and account summaries."""

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RiotAccount
from .serializers import (
    AccountSummarySerializer,
    ChampionPerformanceSerializer,
    FeedbackSerializer,
    RecentMatchSerializer,
)
from .services import (
    get_account_feedback,
    get_account_summary,
    get_champion_performance,
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


class AccountFeedbackView(APIView):
    """Return rule-based feedback cards for a stored account."""

    def get(self, request, account_id: int):
        account = get_object_or_404(RiotAccount, id=account_id)
        limit = _query_limit(request, default=20, maximum=100)
        serializer = FeedbackSerializer(get_account_feedback(account, limit=limit), many=True)
        return Response(serializer.data)


def _query_limit(request, default: int, maximum: int) -> int:
    try:
        limit = int(request.query_params.get("limit", default))
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, maximum))
