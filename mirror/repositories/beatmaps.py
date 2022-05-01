import mirror.config
import mirror.services
from typing import MutableMapping, Optional, Sequence
import mirror.models.beatmaps
from mirror.models.beatmaps import Beatmap
import orjson


id_cache: MutableMapping[int, Beatmap] = {}
md5_cache: MutableMapping[str, Beatmap] = {}

# TODO: where should this go?
async def getbeatmaps_osuapiv1(**kwargs) -> Sequence[Beatmap]:
    """Fetch a sequence of beatmaps from osu!'s api (v1)."""
    assert len(kwargs) == 1 and next(iter(kwargs.values())) in ("h", "b", "s")

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

    return [Beatmap(**beatmap_data) for beatmap_data in response_data]


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
        index=mirror.config.ELASTIC_BEATMAPS_INDEX,
        id=str(id),
    ):
        response = await mirror.services.elastic_client.get(
            index=mirror.config.ELASTIC_BEATMAPS_INDEX,
            id=str(id),
        )

        # we found the map from elasticsearch
        beatmap = Beatmap(**response.body["_source"])  # type: ignore
    else:
        beatmaps = await getbeatmaps_osuapiv1(b=id)
        assert len(beatmaps) == 1
        beatmap = beatmaps[0]

        # save the beatmap into our elasticsearch index
        await mirror.services.elastic_client.create(
            index=mirror.config.ELASTIC_BEATMAPS_INDEX,
            id=str(id),
            document=beatmap.dict(),  # TODO: __dict__?
        )

    # cache the beatmap in ram
    id_cache[beatmap.beatmap_id] = beatmap
    md5_cache[beatmap.file_md5] = beatmap

    return beatmap


async def from_md5(md5: int) -> Optional[Beatmap]:
    """Get a beatmap from it's md5."""
    ...


async def from_set_id(set_id: int) -> Sequence[Beatmap]:
    """\
    Fetch all beatmaps in a set from it's set id.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    response = await mirror.services.elastic_client.search(
        index=mirror.config.ELASTIC_BEATMAPS_INDEX,
        query={"term": {"beatmapset_id": set_id}},
    )

    if hits := response.body["hits"]["hits"]:
        return [hit["_source"] for hit in hits]

    # no maps found in elasticsearch
    # send a response to the osu! api (v1)
    # to fetch up-to-date metadata
    beatmaps = await getbeatmaps_osuapiv1(s=set_id)

    # add beatmaps to our elasticsearch index
    for beatmap in beatmaps:
        # TODO: use `elastic_client.bulk` to do all in 1 conn?
        await mirror.services.elastic_client.index(
            index=mirror.config.ELASTIC_BEATMAPS_INDEX,
            id=str(beatmap.beatmap_id),
            document=beatmap.dict(),
        )

        # add beatmap to our cache as well
        id_cache[beatmap.beatmap_id] = beatmap
        md5_cache[beatmap.file_md5] = beatmap

    return beatmaps
