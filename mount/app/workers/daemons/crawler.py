#!/usr/bin/env python3.10
from __future__ import annotations

import asyncio
import datetime

from app import config
from app.services import OsuAPIClient
from app.services import OsuAPIRequestError
from elasticsearch import AsyncElasticsearch

MAXIMUM_BACKOFF = 32  # seconds


async def crawl_beatmaps() -> None:
    elastic_response = await elastic_client.search(
        aggs={"max_id": {"max": {"field": "data.id"}}},
        index=config.BEATMAPS_INDEX,
    )
    elastic_highest_id = elastic_response["aggregations"]["max_id"]["value"]
    highest_beatmap_id = (
        int(elastic_highest_id) if elastic_highest_id is not None else 0
    )
    backoff_time = 1

    while True:
        beatmap_ids = [highest_beatmap_id + 1 + i for i in range(50)]
        highest_beatmap_id += 50

        beatmaps = await osu_api_client.get_beatmaps(beatmap_ids)
        beatmaps_found = len(beatmaps)

        print(f"Ran & found {beatmaps_found} beatmaps")

        if beatmaps_found:
            backoff_time = 1

            operations = []
            for beatmap in beatmaps:
                operations.append(
                    {
                        "create": {
                            "_index": config.BEATMAPS_INDEX,
                            "_id": str(beatmap["id"]),
                        },
                    },
                )
                operations.append(
                    {
                        "data": beatmaps,
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat(),
                    },
                )

            await elastic_client.bulk(operations=operations)
        else:
            if backoff_time < MAXIMUM_BACKOFF:
                backoff_time **= 2

            print(f"Backing off on beatmap crawling - sleeping for {backoff_time}")
            await asyncio.sleep(backoff_time)


async def crawl_beatmapsets() -> None:
    elastic_response = await elastic_client.search(
        aggs={"max_id": {"max": {"field": "data.id"}}},
        index=config.BEATMAPSETS_INDEX,
    )
    elastic_highest_id = elastic_response["aggregations"]["max_id"]["value"]
    beatmapset_id = int(elastic_highest_id) if elastic_highest_id is not None else 0
    backoff_time = 1

    while True:
        beatmapset_id += 1

        try:
            beatmapset = await osu_api_client.get_beatmapset(beatmapset_id)
        except OsuAPIRequestError as exc:
            if exc.status_code == 404:
                return None
            else:
                raise

        if beatmapset:
            backoff_time = 1

            await elastic_client.create(
                index=config.BEATMAPSETS_INDEX,
                id=str(beatmapset["id"]),
                document={
                    "data": beatmapset,
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat(),
                },
            )
            print("Indexed beatmapset", beatmapset["id"])
        else:
            if backoff_time < MAXIMUM_BACKOFF:
                backoff_time **= 2

            print(f"Backing off on beatmapset crawling - sleeping for {backoff_time}")
            await asyncio.sleep(backoff_time)


async def async_main() -> int:
    global osu_api_client, elastic_client
    osu_api_client = OsuAPIClient(
        client_id=config.OSU_API_CLIENT_ID,
        client_secret=config.OSU_API_CLIENT_SECRET,
        scope=config.OSU_API_SCOPE,
        username=config.OSU_API_USERNAME,
        password=config.OSU_API_PASSWORD,
        request_interval=config.OSU_API_REQUEST_INTERVAL,
        max_requests_per_minute=config.OSU_API_MAX_REQUESTS_PER_MINUTE,
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
