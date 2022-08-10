from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import aiohttp.client_exceptions
from app import config
from app import services

id_cache: MutableMapping[int, Mapping[str, Any]] = {}


async def get_from_id(id: int) -> Mapping[str, Any] | None:
    """\
    Fetch a beatmap's metadata from it's id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    # fetch the beatmap from ram if possible
    if beatmap := id_cache.get(id):
        return beatmap

    # fetch the beatmap from elasticsearch if possible
    if await services.elastic_client.exists(
        index=config.BEATMAPS_INDEX,
        id=str(id),
    ):
        response = await services.elastic_client.get_source(
            index=config.BEATMAPS_INDEX,
            id=str(id),
        )

        # we found the map from elasticsearch
        beatmap_data = response.body
    else:
        try:
            beatmap = await services.osu_api_client.get_beatmap(beatmap=id)
        except aiohttp.client_exceptions.ClientResponseError as exc:
            if exc.code != 404:
                raise
            return None
        else:
            beatmap_data = {
                field: getattr(beatmap, field) for field in beatmap.__slots__
            }

            # save the beatmap into our elasticsearch index
            await services.elastic_client.index(
                index=config.BEATMAPS_INDEX,
                id=str(id),
                document=beatmap_data,
            )

    # cache the beatmap in ram
    id_cache[id] = beatmap_data

    return beatmap_data


async def get_from_checksum(checksum: str) -> Mapping[str, Any] | None:
    """Get a beatmap from it's md5 checksum."""
    ...
