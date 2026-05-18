"""Small Riot API client used by backend workflows."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings


class RiotApiError(Exception):
    """Raised when Riot API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RiotApiClient:
    """HTTP client for the Riot Account-V1 and Match-V5 endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        regional_route: str | None = None,
        timeout: int = 10,
    ):
        self.api_key = api_key if api_key is not None else settings.RIOT_API_KEY
        self.regional_route = regional_route or settings.RIOT_DEFAULT_REGION
        self.timeout = timeout
        self.session = requests.Session()

        if not self.api_key:
            raise RiotApiError("RIOT_API_KEY is not configured.")

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict[str, Any]:
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
        url = (
            f"https://{self.regional_route}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )
        params: dict[str, Any] = {"start": start, "count": count}

        if queue is not None:
            params["queue"] = queue

        return self._get(url, params=params)

    def get_match_detail(self, match_id: str) -> dict[str, Any]:
        url = f"https://{self.regional_route}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self._get(url)

    def get_match_timeline(self, match_id: str) -> dict[str, Any]:
        url = f"https://{self.regional_route}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        return self._get(url)

    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = self.session.get(
            url,
            headers={"X-Riot-Token": self.api_key},
            params=params,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise RiotApiError(
                f"Riot API request failed with status {response.status_code}.",
                status_code=response.status_code,
            )

        return response.json()
