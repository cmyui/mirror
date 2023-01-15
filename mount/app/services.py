from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any
from typing import Literal
from typing import Sequence
from typing import Type

import httpx
from elasticsearch import AsyncElasticsearch

elastic_client: AsyncElasticsearch
osu_api_client: OsuAPIClient


class OsuAPIRequestError(Exception):
    def __init__(self, message: str, status_code: int, *args: object) -> None:
        super().__init__(*args)
        self.message = message
        self.status_code = status_code


class OsuAPIClient:
    def __init__(
        self,
        client_id: int,
        client_secret: str,
        request_interval: float = 1.0,
        max_requests_per_minute: int = 60,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

        self.request_interval_time = request_interval
        self._last_request_time = 0.0

        self.max_requests_per_minute = max_requests_per_minute
        self._requests_this_minute = 0
        self._minute_start_time = 0.0

        # NOTE: we disable timeouts here, as we trust the osu!api to be reliable
        self._http_client = httpx.AsyncClient(timeout=None)
        self._auth_data = {"token": None, "timeout": 0}

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self) -> OsuAPIClient:
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException | None] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def authorize(self) -> None:
        """Request authorization from the osu!api."""
        response = await self._http_client.post(
            url=f"https://osu.ppy.sh/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "public",  # TODO: support for others?
            },
        )
        if response.status_code != 200:
            raise Exception("Failed to authorize with osu!api.")

        response_data = response.json()

        self._auth_data = {
            "access_token": response_data["access_token"],
            "timeout": time.time() + response_data["expires_in"],
        }

    async def request(
        self,
        method: Literal[
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "HEAD",
            "OPTIONS",
            "TRACE",
        ],
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a request to the osu!api."""
        time_since_last_minute_start = time.time() - self._minute_start_time
        if time_since_last_minute_start > 60:
            # minute is over - reset
            self._minute_start_time = time.time()
            self._requests_this_minute = 0
        else:
            # validate per/min request count
            if self._requests_this_minute > self.max_requests_per_minute:
                await asyncio.sleep(60 - time_since_last_minute_start)

        time_since_last_request = time.time() - self._last_request_time

        if time_since_last_request < self.request_interval_time:
            await asyncio.sleep(self.request_interval_time - time_since_last_request)

        if time.time() > self._auth_data["timeout"]:
            await self.authorize()
            await asyncio.sleep(self.request_interval_time)

        if headers is None:
            headers = {}

        headers["Authorization"] = f"Bearer {self._auth_data['access_token']}"

        response = await self._http_client.request(
            method,
            url,
            params=params,
            headers=headers,
            follow_redirects=True,
        )

        self._last_request_time = time.time()
        self._requests_this_minute += 1

        if response.status_code != 200:
            raise OsuAPIRequestError(
                "Request returned non-200 status code",
                response.status_code,
            )

        content_type = response.headers.get("content-type", "")
        if content_type is None:
            raise OsuAPIRequestError(
                "No content-type header found in response.",
                response.status_code,
            )

        if content_type == "application/json":
            return response.json()
        elif content_type == "application/octet-stream":
            return await response.aread()
        elif content_type == "text/plain":
            return (await response.aread()).decode()
        else:
            return await response.aread()

    async def get_beatmapset(self, id: int) -> dict[str, Any]:
        """Fetch a beatmap set's metadata from it's id."""
        url = f"https://osu.ppy.sh/api/v2/beatmapsets/{id}"
        return await self.request("GET", url)

    async def get_beatmap(self, id: int) -> dict[str, Any]:
        """Fetch a beatmap's metadata from it's id."""
        url = f"https://osu.ppy.sh/api/v2/beatmaps/{id}"
        return await self.request("GET", url)

    async def get_beatmaps(self, ids: Sequence[int]) -> list[dict[str, Any]]:
        """Fetch beatmaps' metadata from their ids."""
        url = f"https://osu.ppy.sh/api/v2/beatmaps"
        params = {"ids[]": [str(id) for id in ids]}
        return (await self.request("GET", url, params))["beatmaps"]

    async def get_beatmap_osz2(self, id: int) -> bytes:
        """Fetch a beatmapset's osu! file from it's id."""
        url = f"https://osu.ppy.sh/api/v2/beatmapsets/{id}/download"
        headers = {"User-Agent": "osu-framework"}
        return await self.request("GET", url, headers=headers)
