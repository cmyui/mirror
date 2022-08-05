from __future__ import annotations

from typing import MutableMapping
from typing import Optional

import orjson

import mirror.config
import mirror.services
from mirror.models.beatmap_sets import BeatmapSet
from mirror.models.beatmaps import Beatmap

id_cache: MutableMapping[int, BeatmapSet] = {}


async def from_id(id: int) -> Optional[BeatmapSet]:
    """\
    Fetch a beatmap set's metadata from it's id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    # fetch the beatmap set from ram if possible
    if beatmap_set := id_cache.get(id):
        return beatmap_set

    # fetch the beatmap set from elasticsearch if possible
    if await mirror.services.elastic_client.exists(
        index=mirror.config.BEATMAP_SETS_INDEX,
        id=str(id),
    ):
        response = await mirror.services.elastic_client.get(
            index=mirror.config.BEATMAPS_INDEX,
            id=str(id),
        )

        # we found the beatmap set from elasticsearch
        beatmap_set = BeatmapSet(**response.body["_source"])  # type: ignore
    else:
        # beatmap set not found in elasticsearch
        # send a response to the osu! api (v1)
        # to fetch it's up-to-date metadata
        response = await mirror.services.http_client.get(
            "https://osu.ppy.sh/api/get_beatmaps",
            params={
                "k": mirror.config.OSU_API_KEY,
                "s": id,
            },
        )
        if response.status_code != 200:
            return None

        # read the response data from the client
        response_data = orjson.loads(await response.aread())
        if not response_data:
            return None

        beatmaps: list[Beatmap] = []

        for beatmap_data in response_data:
            beatmaps.append(Beatmap(**beatmap_data))

        # parse into a beatmap set model
        beatmap_set = BeatmapSet(**response_data[0])

        # save the beatmap set into our elasticsearch index
        # await mirror.services.elastic_client.create(
        #     index=mirror.config.BEATMAP_SETS_INDEX,
        #     id=str(id),
        #     document=beatmap_set.dict(),  # TODO: __dict__?
        # )

    # cache the beatmap set in ram
    id_cache[id] = beatmap_set

    return beatmap_set
