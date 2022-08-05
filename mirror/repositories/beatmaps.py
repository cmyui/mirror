from __future__ import annotations

import logging
from typing import MutableMapping
from typing import Optional

import orjson

import mirror.config
import mirror.models.beatmaps
import mirror.services
from mirror.models.beatmaps import Beatmap


id_cache: MutableMapping[int, Beatmap] = {}
md5_cache: MutableMapping[str, Beatmap] = {}

# TODO: where should this go?
async def get_beatmaps_from_osu_api_v1(**kwargs) -> list[Beatmap]:
    """Fetch a sequence of beatmaps from osu!'s api (v1)."""
    assert len(kwargs) == 1 and next(iter(kwargs.keys())) in ("h", "b", "s")

    # map not found in elasticsearch
    # send a response to the osu! api (v1)
    # to fetch it's up-to-date metadata
    response = await mirror.services.http_client.get(
        "https://osu.ppy.sh/api/get_beatmaps",
        params={"k": mirror.config.OSU_API_KEY, **kwargs},
    )
    if response.status_code != 200:
        return []

    # read the response data from the client
    response_data = orjson.loads(await response.aread())
    if not response_data:
        return []

    # TODO: clean this up once we have a better understanding of the behaviour
    beatmaps = []
    for beatmap_data in response_data:
        if beatmap_data["beatmapset_id"] is None:
            logging.info(f"the osu!api returned a null set for {kwargs}")
            continue

        try:
            beatmap = Beatmap(**beatmap_data)
        except:
            import traceback

            traceback.print_exc()
            # breakpoint()
        else:
            beatmaps.append(beatmap)

    return beatmaps


async def from_id(id: int) -> Optional[Beatmap]:
    """\
    Fetch a beatmap's metadata from it's id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    # fetch the beatmap from ram if possible
    if beatmap := id_cache.get(id):
        return beatmap

    # fetch the beatmap from elasticsearch if possible
    if await mirror.services.elastic_client.exists(
        index=mirror.config.BEATMAPS_INDEX,
        id=str(id),
    ):
        response = await mirror.services.elastic_client.get_source(
            index=mirror.config.BEATMAPS_INDEX,
            id=str(id),
        )

        # we found the map from elasticsearch
        beatmap = Beatmap(**response.body)  # type: ignore
    else:
        beatmaps = await get_beatmaps_from_osu_api_v1(b=id)
        assert len(beatmaps) == 1
        beatmap = beatmaps[0]

        # save the beatmap into our elasticsearch index
        await mirror.services.elastic_client.create(
            index=mirror.config.BEATMAPS_INDEX,
            id=str(id),
            document=beatmap.__dict__,  # TODO: __dict__?
        )

    # cache the beatmap in ram
    id_cache[beatmap.beatmap_id] = beatmap
    md5_cache[beatmap.file_md5] = beatmap

    return beatmap


async def from_md5(md5: int) -> Optional[Beatmap]:
    """Get a beatmap from it's md5."""
    ...


async def from_set_id(set_id: int) -> list[Beatmap]:
    """\
    Fetch all beatmaps in a set from it's set id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    response = await mirror.services.elastic_client.search(
        index=mirror.config.BEATMAPS_INDEX,
        query={"term": {"beatmapset_id": set_id}},
    )

    if hits := response.body["hits"]["hits"]:
        return [hit["_source"] for hit in hits]

    # no maps found in elasticsearch
    # send a request to the osu! api (v1)
    # to fetch up-to-date metadata
    beatmaps = await get_beatmaps_from_osu_api_v1(s=set_id)

    # add beatmaps to our elasticsearch index
    for beatmap in beatmaps:
        # TODO: use `elastic_client.bulk` to do all in 1 conn?
        await mirror.services.elastic_client.index(
            index=mirror.config.BEATMAPS_INDEX,
            id=str(beatmap.beatmap_id),
            document=beatmap.__dict__,
        )

        # add beatmap to our cache as well
        id_cache[beatmap.beatmap_id] = beatmap
        md5_cache[beatmap.file_md5] = beatmap

    return beatmaps
