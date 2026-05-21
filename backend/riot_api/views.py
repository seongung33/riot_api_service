"""Riot API를 직접 호출하는 import workflow APIView."""

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
    """Riot ID 기반 최근 경기 import API."""

    def post(self, request):
        # APIView의 POST 흐름은 요청 serializer 검증 -> service 실행 -> 응답 serializer 변환 순서다.
        # serializer.is_valid가 실패하면 DRF가 400 응답을 자동으로 만든다.
        request_serializer = ImportRecentMatchesRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        try:
            # service는 Riot API 호출, 계정 저장, match/timeline 저장, phase metric 계산까지 묶어서 수행한다.
            account, imported_match_ids = import_recent_matches_for_account(
                game_name=data["game_name"],
                tag_line=data["tag_line"],
                region=data["region"],
                count=data["count"],
                queue=data["queue"],
            )

        except RiotApiError as exc:
            # Riot API 장애나 인증 실패는 우리 요청 schema 오류와 구분하기 위해 502로 응답한다.
            return Response(
                {"detail": str(exc), "status_code": exc.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 응답 serializer를 한 번 더 거치면 view가 반환하는 JSON 모양이 테스트와 문서에서 예측 가능해진다.
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
