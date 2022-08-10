from __future__ import annotations

import datetime
from typing import Any
from typing import Mapping
from typing import MutableMapping

from aiohttp.client_exceptions import ClientResponseError
from app import config
from app import services
from osu.path import Path as OsuAPIPath

# TODO: typeddict model for mapping?
id_cache: MutableMapping[int, Mapping[str, Any]] = {}


async def get_from_id(id: int) -> Mapping[str, Any] | None:
    """\
    Fetch a beatmap's metadata from it's id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    # fetch the beatmap from ram if possible
    if beatmap_data := id_cache.get(id):
        return beatmap_data

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
        beatmap_data = response.body["data"]
    else:
        try:
            beatmap_data = await services.osu_api_client.http.make_request(
                method="get",
                path=OsuAPIPath.beatmap(id),
            )
        except ClientResponseError as exc:
            if exc.code != 404:
                raise
            return None
        else:
            # save the beatmap into our elasticsearch index
            await services.elastic_client.index(
                index=config.BEATMAPS_INDEX,
                id=str(id),
                document={
                    "data": beatmap_data,
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat(),
                },
            )

    # cache the beatmap in ram
    id_cache[id] = beatmap_data

    return beatmap_data


async def get_from_checksum(checksum: str) -> Mapping[str, Any] | None:
    """Get a beatmap from it's md5 checksum."""
    ...
