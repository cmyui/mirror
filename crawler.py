#!/usr/bin/env python3.10
from __future__ import annotations

import asyncio
import base64
import json
import traceback
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Mapping

import aioredis
import elasticsearch

from mount.app import logger
from mount.app import settings
from mount.app.services import OsuAPIClient


MAXIMUM_BACKOFF = 32


def stringify_cursor(cursor: dict[str, Any]) -> str:
    return base64.b64encode(
        json.dumps(
            cursor,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).decode()


def should_reindex_beatmapset(
    beatmapset: Mapping[str, Any],
    last_updated: datetime,
) -> bool:
    if beatmapset["status"] in ("ranked", "approved"):
        # it is not possible to update a ranked or approved beatmapset
        return False

    match beatmapset["status"]:
        case "loved":
            # loved maps can *technically* be updated
            update_interval = timedelta(days=1)
        case "graveyard":
            # TODO: scale this with time since last beatmap update
            update_interval = timedelta(days=1)
        case "qualified":
            update_interval = timedelta(minutes=5)
        case "pending":
            update_interval = timedelta(minutes=10)
        case "wip":
            update_interval = timedelta(minutes=5)
        case _:
            raise Exception(f"Unknown beatmapset status: {beatmapset['status']}")

    return last_updated <= (datetime.now() - update_interval)


async def crawl_beatmapsets() -> None:
    saved_cursor: bytes | None = await redis_client.get("beatmapsets_cursor")
    if saved_cursor is not None:
        cursor = json.loads(saved_cursor.decode())
    else:
        cursor = {}

    backoff_time = 1

    while cursor is not None:
        try:
            result = await osu_api_client.search(
                query=None,
                general=None,
                mode=None,
                section="any",
                include_nsfw=True,
                genre=None,
                language=None,
                extra=None,
                rank_achieved=None,
                played=None,
                sort="updated_asc",
                cursor_string=stringify_cursor(cursor) if cursor else None,
            )
            if result["error"] is not None:
                raise Exception("Error while crawling beatmapsets: " + result["error"])
        except Exception as exc:
            logger.error("Search call to osu!api failed: ", error=exc)
            logger.error("Stack trace: ", error=traceback.format_exc())

            if backoff_time < MAXIMUM_BACKOFF:
                backoff_time **= 2

            print(f"Backing off on beatmap crawling - sleeping for {backoff_time}")
            await asyncio.sleep(backoff_time)
            continue
        else:
            backoff_time = 1

        crawl_time = datetime.now()
        operations = []

        for beatmapset in result["beatmapsets"]:
            # fetch last time this beatmapset was updated
            try:
                elastic_response = await elastic_client.get(
                    index=settings.BEATMAPSETS_INDEX,
                    id=beatmapset["id"],
                )
            except elasticsearch.NotFoundError:
                should_index_beatmapset = True
            else:
                should_index_beatmapset = should_reindex_beatmapset(
                    beatmapset=beatmapset,
                    last_updated=datetime.fromisoformat(
                        elastic_response["_source"]["updated_at"],
                    ),
                )

            if not should_index_beatmapset:
                logger.info(
                    "Skipping indexing of beatmapset",
                    beatmapset_id=beatmapset["id"],
                )
                continue

            logger.info(
                "Indexing beatmapset",
                beatmapset_id=beatmapset["id"],
            )

            # index beatmaps separately from beatmapsets
            beatmaps = beatmapset.pop("beatmaps")

            # add sets to sets index
            operations.append(
                {
                    "create": {
                        "_index": settings.BEATMAPSETS_INDEX,
                        "_id": str(beatmapset["id"]),
                    },
                },
            )
            operations.append(
                {
                    "data": beatmapset,
                    "created_at": crawl_time.isoformat(),
                    "updated_at": crawl_time.isoformat(),
                },
            )

            # add maps to maps index
            for beatmap in beatmaps:
                operations.append(
                    {
                        "create": {
                            "_index": settings.BEATMAPS_INDEX,
                            "_id": str(beatmap["id"]),
                        },
                    },
                )
                operations.append(
                    {
                        "data": beatmap,
                        "created_at": crawl_time.isoformat(),
                        "updated_at": crawl_time.isoformat(),
                    },
                )

        if operations:
            await elastic_client.bulk(operations=operations)

        cursor = result["cursor"]
        if cursor is None:
            print("Finished crawling beatmapsets")
            print(result)
            return

        await redis_client.set("beatmapsets_cursor", json.dumps(cursor))


async def async_main() -> int:
    global osu_api_client, elastic_client, redis_client
    osu_api_client = OsuAPIClient(
        client_id=settings.OSU_API_CLIENT_ID,
        client_secret=settings.OSU_API_CLIENT_SECRET,
        request_interval=settings.OSU_API_REQUEST_INTERVAL,
        max_requests_per_minute=settings.OSU_API_MAX_REQUESTS_PER_MINUTE,
    )
    elastic_client = elasticsearch.AsyncElasticsearch(
        f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}",
    )

    # create elasticsearch indices if they don't already exist
    for index in (settings.BEATMAPS_INDEX, settings.BEATMAPSETS_INDEX):
        if not await elastic_client.indices.exists(index=index):
            await elastic_client.indices.create(index=index)

    redis_client = aioredis.Redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    )
    await redis_client.initialize()

    try:
        await crawl_beatmapsets()
    except (KeyboardInterrupt, EOFError):
        pass

    await redis_client.close()
    await elastic_client.close()
    return 0


if __name__ == "__main__":
    # logger.overwrite_exception_hook()
    # atexit.register(logger.restore_exception_hook)

    logger.configure_logging(
        app_env=settings.APP_ENV,
        log_level=settings.LOG_LEVEL,
    )

    exit_code = asyncio.run(async_main())
    raise SystemExit(exit_code)
