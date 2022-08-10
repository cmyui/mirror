from __future__ import annotations

import datetime
from typing import Any
from typing import Mapping
from typing import MutableMapping
from typing import Optional

from aiohttp.client_exceptions import ClientResponseError
from app import config
from app import services
from osu.path import Path as OsuAPIPath

# TODO: typeddict model for mapping?
id_cache: MutableMapping[int, Mapping[str, Any]] = {}


async def get_from_id(id: int) -> Optional[Mapping[str, Any]]:
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

        beatmapset_data = response.body["_source"]["data"]
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
            # save the beatmap set into our elasticsearch index
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
    id_cache[id] = beatmapset_data

    return beatmapset_data


async def get_from_checksum(checksum: str) -> Optional[Mapping[str, Any]]:
    """Fetch a beatmapset from it's md5 checksum."""
    raise NotImplementedError
