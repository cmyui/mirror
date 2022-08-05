#!/usr/bin/env python3.10
from __future__ import annotations

import asyncio
import logging
import time

import httpx
from elasticsearch import AsyncElasticsearch

import mirror.config
import mirror.repositories.beatmaps
import mirror.services

logging.basicConfig(
    level=mirror.config.LOG_LEVEL,
    format="%(asctime)s %(message)s",
)

REQUEST_INTERVAL = 60 / 200  # 1s / reqs


async def main() -> int:
    async with (
        AsyncElasticsearch(f"http://{mirror.config.ELASTIC_HOST}:{mirror.config.ELASTIC_PORT}") as mirror.services.elastic_client,
        httpx.AsyncClient() as mirror.services.http_client,
    ):
        resp = await mirror.services.elastic_client.search(
            index=mirror.config.BEATMAPS_INDEX,
            aggregations={"highest_set_id": {"max": {"field": "beatmapset_id"}}},
        )

        set_id = int(resp["aggregations"]["highest_set_id"]["value"]) + 1

        while True:
            start_time = time.perf_counter_ns()
            beatmaps = await mirror.repositories.beatmaps.from_set_id(set_id)
            end_time = time.perf_counter_ns()

            logging.info(
                f"Fetched ({len(beatmaps)} maps) from set {set_id} in {(end_time - start_time)/1e6}ms",
            )

            await asyncio.sleep(REQUEST_INTERVAL)
            set_id += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
