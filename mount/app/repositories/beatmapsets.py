from __future__ import annotations

import datetime
from typing import Any

from aiohttp.client_exceptions import ClientResponseError
from app import config
from app import services
from app.enums.gamemodes import GameMode
from app.enums.ranked_statuses import OsuAPIRankedStatus
from osu.path import Path as OsuAPIPath

# TODO: typeddict model for mapping?
id_cache: dict[int, dict[str, Any]] = {}


async def get_from_id(id: int) -> dict[str, Any] | None:
    """\
    Fetch a beatmap set's metadata from it's id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    # fetch the beatmap set from ram if possible
    if beatmapset := id_cache.get(id):
        return beatmapset

    # fetch the beatmap set from elasticsearch if possible
    if await services.elastic_client.exists(
        index=config.BEATMAPSETS_INDEX,
        id=str(id),
    ):
        response = await services.elastic_client.get(
            index=config.BEATMAPSETS_INDEX,
            id=str(id),
        )

        beatmapset_data: dict[str, Any] = response.body["_source"]["data"]
    else:
        try:
            beatmapset_data = await services.osu_api_client.http.make_request(
                method="get",
                path=OsuAPIPath.get_beatmapset(id),
            )
        except ClientResponseError as exc:
            if exc.code != 404:
                raise
            return None
        else:
            # extract beatmap info from the set
            beatmaps_data = beatmapset_data.pop("beatmaps")

            # save the beatmaps into our elastic index
            # TODO: use bulk query
            for beatmap_data in beatmaps_data:
                await services.elastic_client.index(
                    index=config.BEATMAPS_INDEX,
                    id=str(beatmap_data["id"]),
                    document={
                        "data": beatmap_data,
                        # TODO: should we really be setting created_at here?
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat(),
                    },
                )

            # save the beatmap set into our elastic index
            await services.elastic_client.create(
                index=config.BEATMAPSETS_INDEX,
                id=str(id),
                document={
                    "data": beatmapset_data,
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat(),
                },
            )

    # cache the beatmap set in ram
    # id_cache[id] = beatmapset_data

    return beatmapset_data


async def get_from_checksum(checksum: str) -> dict[str, Any] | None:
    """Fetch a beatmapset from it's md5 checksum."""
    raise NotImplementedError


async def get_osz2_from_id(id: int) -> dict[str, Any] | None:
    """Fetch a beatmapset's osz2 file from it's id."""
    raise NotImplementedError


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
        query_conditions.append({"term": {"data.beatmaps.mode_int": mode}})

    if status != OsuAPIRankedStatus.ALL:
        query_conditions.append({"term": {"data.beatmaps.ranked": status}})

    elastic_response = await services.elastic_client.search(
        index=config.BEATMAPSETS_INDEX,
        query={"bool": {"must": query_conditions}},
        size=amount,
        from_=offset,
    )

    return [hit["_source"]["data"] for hit in elastic_response["hits"]["hits"]]
