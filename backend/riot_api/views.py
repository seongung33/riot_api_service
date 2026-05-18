"""Views for Riot API-backed workflows."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import RiotAccount
from matches.services import save_match_bundle

from .client import RiotApiClient, RiotApiError
from .serializers import (
    ImportRecentMatchesRequestSerializer,
    ImportRecentMatchesResponseSerializer,
)


class ImportRecentMatchesView(APIView):
    """Fetch a Riot account and recent matches, then persist them locally."""

    def post(self, request):
        request_serializer = ImportRecentMatchesRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        try:
            client = RiotApiClient(regional_route=data["region"])
            account_data = client.get_account_by_riot_id(data["game_name"], data["tag_line"])
            match_ids = client.get_match_ids_by_puuid(
                account_data["puuid"],
                count=data["count"],
                queue=data["queue"],
            )

            account, _ = RiotAccount.objects.update_or_create(
                puuid=account_data["puuid"],
                defaults={
                    "game_name": account_data.get("gameName", data["game_name"]),
                    "tag_line": account_data.get("tagLine", data["tag_line"]),
                    "region": data["region"],
                },
            )

            imported_match_ids = []
            for match_id in match_ids:
                match_detail = client.get_match_detail(match_id)
                timeline_detail = client.get_match_timeline(match_id)
                match = save_match_bundle(match_detail, timeline_detail)
                imported_match_ids.append(match.match_id)

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
