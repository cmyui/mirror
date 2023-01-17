from __future__ import annotations

import datetime
from typing import Any

import elasticsearch
from app.common import services
from app.common import settings
from app.models.gamemodes import GameMode
from app.models.ranked_statuses import OsuAPIRankedStatus

# TODO: these return ["data"]; this is probably wrong


async def get_from_id(id: int) -> dict[str, Any] | None:
    try:
        response = await services.elastic_client.get(
            index=settings.BEATMAPSETS_INDEX,
            id=str(id),
        )
    except elasticsearch.NotFoundError:
        return None

    return response.body["_source"]["data"]


async def create(osuapi_data: dict[str, Any]) -> dict[str, Any]:
    creation_time = datetime.datetime.now()

    # TODO: use bulk api

    await services.elastic_client.create(
        index=settings.BEATMAPSETS_INDEX,
        id=str(osuapi_data["id"]),
        document={
            "data": osuapi_data,
            "created_at": creation_time.isoformat(),
            "updated_at": creation_time.isoformat(),
        },
    )

    for beatmap_data in osuapi_data["beatmaps"]:
        await services.elastic_client.create(
            index=settings.BEATMAPS_INDEX,
            id=str(beatmap_data["id"]),
            document={
                "data": beatmap_data,
                "created_at": creation_time.isoformat(),
                "updated_at": creation_time.isoformat(),
            },
        )

    return osuapi_data


async def search(
    query: str | None,
    amount: int,
    offset: int,
    mode: int,
    status: int,
) -> list[dict[str, Any]]:
    """Search for beatmapsets."""
    query_conditions: list[dict[str, Any]] = []

    if query is not None:
        query_conditions.append(
            {
                "simple_query_string": {
                    "query": query,
                    "fields": [
                        "data.artist",
                        "data.creator",
                        "data.title",
                        "data.title_unicode",
                        "data.tags",
                        # "data.beatmaps.version",
                    ],
                },
            },
        )

    if mode != GameMode.ALL:
        query_conditions.append({"term": {"data.beatmaps.mode_int": int(mode)}})

    if status != OsuAPIRankedStatus.ALL:
        query_conditions.append({"term": {"data.beatmaps.ranked": int(status)}})

    elastic_response = await services.elastic_client.search(
        index=settings.BEATMAPSETS_INDEX,
        query={"bool": {"must": query_conditions}},
        size=amount,
        from_=offset,
    )

    return [hit["_source"]["data"] for hit in elastic_response["hits"]["hits"]]
