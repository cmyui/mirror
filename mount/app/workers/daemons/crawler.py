#!/usr/bin/env python3.10
from __future__ import annotations

import asyncio
import datetime
from typing import Any

import aiohttp.client_exceptions
import osu
from app import config
from elasticsearch import AsyncElasticsearch

MAXIMUM_BACKOFF = 32  # seconds

# TODO: where should this live?
def slotted_obj_to_dict(obj: object) -> dict[str, Any]:
    result = {}
    for cls in obj.__class__.__mro__:
        slots = getattr(cls, "__slots__", None)
        if slots is not None:
            result |= {k: getattr(obj, k) for k in slots if hasattr(obj, k)}
    return result


async def crawl_beatmaps() -> None:
    elastic_response = await elastic_client.search(
        aggs={"max_id": {"max": {"field": "data.id"}}},
        index=config.BEATMAPS_INDEX,
    )
    elastic_highest_id = elastic_response["aggregations"]["max_id"]["value"]
    highest_beatmap_id = (
        int(elastic_highest_id) if elastic_highest_id is not None else 0
    )
    backoff_time = 0

    while True:
        beatmap_ids = [highest_beatmap_id + 1 + i for i in range(50)]
        highest_beatmap_id += 50

        beatmaps = await osu_api_client.get_beatmaps(beatmap_ids)
        beatmaps_found = len(beatmaps)

        print(f"Ran & found {beatmaps_found} beatmaps")

        if beatmaps_found:
            backoff_time = 0

            operations = []
            for beatmap in beatmaps:
                operations.append(
                    {
                        "create": {
                            "_index": config.BEATMAPS_INDEX,
                            "_id": str(beatmap.id),
                        },
                    },
                )
                operations.append(
                    {
                        "data": {k: getattr(beatmap, k) for k in beatmap.__slots__},
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat(),
                    },
                )

            await elastic_client.bulk(operations=operations)
        else:
            if not backoff_time:
                backoff_time = 1
            else:
                backoff_time **= 2

            await asyncio.sleep(min(backoff_time, MAXIMUM_BACKOFF))


async def crawl_beatmapsets() -> None:
    elastic_response = await elastic_client.search(
        aggs={"max_id": {"max": {"field": "data.id"}}},
        index=config.BEATMAPSETS_INDEX,
    )
    elastic_highest_id = elastic_response["aggregations"]["max_id"]["value"]
    highest_beatmapset_id = (
        int(elastic_highest_id) if elastic_highest_id is not None else 0
    )
    backoff_time = 0

    while True:
        highest_beatmapset_id += 1

        try:
            beatmapset = await osu_api_client.get_beatmapset(highest_beatmapset_id)
        except aiohttp.client_exceptions.ClientResponseError as exc:
            if exc.status == 404:
                continue
            else:
                raise exc

        if beatmapset:
            backoff_time = 0

            beatmapset_data = slotted_obj_to_dict(beatmapset)
            del beatmapset_data["beatmaps"]  # don't include beatmaps in the set index

            await elastic_client.create(
                index=config.BEATMAPSETS_INDEX,
                id=str(beatmapset.id),
                document={
                    "data": {k: getattr(beatmapset, k) for k in beatmapset.__slots__}
                    | {"id": beatmapset.id},
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat(),
                },
            )
            print("Indexed beatmapset", beatmapset.id)
        else:
            if not backoff_time:
                backoff_time = 1
            else:
                backoff_time **= 2

            await asyncio.sleep(min(backoff_time, MAXIMUM_BACKOFF))


async def async_main() -> int:
    global osu_api_client, elastic_client
    osu_api_client = osu.AsynchronousClient.from_client_credentials(
        client_id=config.OSU_API_CLIENT_ID,
        client_secret=config.OSU_API_CLIENT_SECRET,
        redirect_url=config.OSU_API_REDIRECT_URL,
        request_wait_time=1,
        limit_per_minute=60,
    )
    elastic_client = AsyncElasticsearch(
        f"http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}",
    )

    # create elasticsearch indices if they don't already exist
    for index in (config.BEATMAPS_INDEX, config.BEATMAPSETS_INDEX):
        if not await elastic_client.indices.exists(index=index):
            await elastic_client.indices.create(index=index)

    await asyncio.gather(crawl_beatmaps(), crawl_beatmapsets())

    await elastic_client.close()
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(async_main())
    raise SystemExit(exit_code)
