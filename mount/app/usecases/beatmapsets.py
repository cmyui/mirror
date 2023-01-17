from __future__ import annotations

import traceback
from typing import Any

import httpx
from app.common import logger
from app.common import services
from app.repositories import beatmapsets


async def get_from_id(id: int) -> dict[str, Any] | None:
    data = await beatmapsets.get_from_id(id)
    if data is None:
        try:
            osu_api_data = await services.osu_api_client.get_beatmapset(id)
        except services.OsuAPIRequestError as exc:
            if exc.status_code == 404:
                return None
            else:
                raise

        data = await beatmapsets.create(osu_api_data)

    return data


async def get_osz2_from_id(id: int) -> bytes | None:
    try:
        response = await services.http_client.get(f"https://kitsu.moe/api/d/{id}")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        else:
            logger.error(
                "Received unhandled status code while downloading osz2",
                beatmapset_id=id,
                status_code=exc.response.status_code,
            )
            return None
    except httpx.RequestError as exc:
        logger.error(
            "Unhandled request error while downloading osz2",
            beatmapset_id=id,
            stacktrace=traceback.format_exc(),
        )
        return None

    data = await response.aread()

    # TODO: cache this (unzipped) to disk

    return data


async def search(
    query: str | None,
    mode: int,
    status: int,
    amount: int,
    offset: int,
) -> list[dict[str, Any]]:
    search_results = await beatmapsets.search(
        query=query,
        mode=mode,
        status=status,
        amount=amount,
        offset=offset,
    )
    return search_results
