"""백엔드 import workflow에서 사용하는 Riot API HTTP client."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings


class RiotApiError(Exception):
    """Riot API 호출 실패를 view 계층에서 일관되게 처리하기 위한 예외."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RiotApiClient:
    """Riot Account-V1과 Match-V5 endpoint를 호출하는 작은 client."""

    def __init__(
        self,
        api_key: str | None = None,
        regional_route: str | None = None,
        timeout: int = 10,
    ):
        # API key와 기본 region은 settings에서 읽는다.
        # settings는 .env 환경변수를 통해 값을 받으므로 코드에 secret을 하드코딩하지 않는다.
        self.api_key = api_key if api_key is not None else settings.RIOT_API_KEY
        self.regional_route = regional_route or settings.RIOT_DEFAULT_REGION
        self.timeout = timeout
        self.session = requests.Session()

        if not self.api_key:
            raise RiotApiError("RIOT_API_KEY is not configured.")

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict[str, Any]:
        # Riot ID에는 공백이나 특수문자가 들어갈 수 있으므로 URL path에 넣기 전에 quote로 인코딩한다.
        # 이 응답에서 얻는 PUUID가 이후 match-v5 최근 경기 조회의 입력이 된다.
        game_name_path = quote(game_name, safe="")
        tag_line_path = quote(tag_line, safe="")
        url = (
            f"https://{self.regional_route}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{game_name_path}/{tag_line_path}"
        )
        return self._get(url)

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        count: int = 5,
        start: int = 0,
        queue: int | None = 420,
    ) -> list[str]:
        # match-v5의 최근 경기 목록 endpoint는 PUUID를 기준으로 match_id 리스트만 반환한다.
        # queue를 넘기면 솔로랭크(420)처럼 특정 큐만 가져올 수 있다.
        url = (
            f"https://{self.regional_route}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )
        params: dict[str, Any] = {"start": start, "count": count}

        if queue is not None:
            params["queue"] = queue

        return self._get(url, params=params)

    def get_match_detail(self, match_id: str) -> dict[str, Any]:
        # match detail은 경기 메타데이터와 participant 최종 통계를 저장하는 재료다.
        url = f"https://{self.regional_route}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self._get(url)

    def get_match_timeline(self, match_id: str) -> dict[str, Any]:
        # timeline은 분 단위 frame과 event를 제공하며,
        # 라인전/오브젝트 같은 phase metric 계산은 이 데이터가 있어야 가능하다.
        url = f"https://{self.regional_route}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        return self._get(url)

    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        # Riot API key는 X-Riot-Token 헤더로만 전달한다.
        # key는 환경변수에서 읽은 settings 값을 사용하며 코드나 로그에 직접 출력하지 않는다.
        response = self.session.get(
            url,
            headers={"X-Riot-Token": self.api_key},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            # 외부 API 오류를 그대로 삼키지 않고 status_code와 함께 예외로 올린다.
            # view는 이 예외를 502 응답으로 바꿔 프론트에 실패 원인을 전달한다.
            raise RiotApiError(
                f"Riot API request failed with status {response.status_code}.",
                status_code=response.status_code,
            )

        # 각 endpoint마다 응답 구조가 다르므로 client는 JSON parsing까지만 담당하고,
        # 저장/분석에 필요한 해석은 service 계층에서 수행한다.
        return response.json()
