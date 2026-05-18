"""Views for Riot API-backed workflows."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .client import RiotApiError
from .serializers import (
    ImportRecentMatchesRequestSerializer,
    ImportRecentMatchesResponseSerializer,
)
from .services import import_recent_matches_for_account


class ImportRecentMatchesView(APIView):
    """Fetch a Riot account and recent matches, then persist them locally."""

    def post(self, request):
        request_serializer = ImportRecentMatchesRequestSerializer(data=request.data)
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

        response_serializer = ImportRecentMatchesResponseSerializer(
            {
                "account_id": account.id,
                "puuid": account.puuid,
                "game_name": account.game_name,
                "tag_line": account.tag_line,
                "region": account.region,
                "requested_count": data["count"],
                "imported_match_ids": imported_match_ids,
            }
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
