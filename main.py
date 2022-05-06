#!/usr/bin/env python3.9
from __future__ import annotations

import os.path
import random
import time
from typing import Any
from typing import MutableMapping

import httpx
import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi.applications import FastAPI
from fastapi.requests import Request
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette_exporter import handle_metrics
from starlette_exporter import PrometheusMiddleware

import mirror.config
import mirror.models.beatmap_sets
import mirror.repositories.beatmap_sets
import mirror.repositories.beatmaps
import mirror.services
import mirror.sessions
import mirror.usecases.downloads
import mirror.usecases.sessions
from mirror.enums.ranked_statuses import MirrorRankedStatus

# TODO: support for MAX_DISK_USAGE_GB & MAX_RAM_USAGE_GB in config

OSZ2_PATH = os.path.join(os.path.dirname(__file__), "osz2")

DOWNLOAD_FAILED_ERROR = (
    "Could not retrieve beatmap - this error has been reported to our devs."
)

app = FastAPI()


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    # TODO: can i replace this with prometheus middleware's timing?

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.perf_counter_ns()
        response = await call_next(request)
        end = time.perf_counter_ns()

        response.headers["process-time"] = str((end - start) / 1_000_000)  # ns -> ms
        return response


app.add_middleware(ProcessTimeMiddleware)

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)


# TODO: move this elsewhere?
# INDEX_DEFINITION = {
#     "settings": {"number_of_shards": 1, "number_of_replicas": 0},
#     "mappings": {
#         "properties": {
#             # https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html
#             "beatmap_id": {"type": "integer"},
#             "beatmapset_id": {"type": "integer"},
#             "approved": {"type": "integer"},
#             "total_length": {"type": "integer"},
#             "hit_length": {"type": "integer"},
#             "version": {"type": "text"},
#             "file_md5": {"type": "text"},
#             "diff_size": {"type": "float"},
#             "diff_overall": {"type": "float"},
#             "diff_approach": {"type": "float"},
#             "diff_drain": {"type": "float"},
#             "mode": {"type": "integer"},
#             "count_normal": {"type": "integer"},
#             "count_slider": {"type": "integer"},
#             "count_spinner": {"type": "integer"},
#             "submit_date": {"type": "date"},
#             "approved_date": {"type": "date"},  # TODO handle optional
#             "last_update": {"type": "date"},
#             "artist": {"type": "text"},
#             "artist_unicode": {"type": "text"},
#             "title": {"type": "text"},
#             "title_unicode": {"type": "text"},
#             "creator": {"type": "text"},
#             "creator_id": {"type": "integer"},
#             "bpm": {"type": "float"},
#             "source": {"type": "text"},
#             "tags": {"type": "text"},  # TODO: keep as string?
#             "genre_id": {"type": "integer"},
#             "language_id": {"type": "integer"},
#             "favourite_count": {"type": "integer"},
#             "rating": {"type": "float"},
#             "storyboard": {"type": "text"},  # TODO: prob bool?
#             "video": {"type": "text"},  # TODO: prob bool?
#             "download_unavailable": {"type": "boolean"},
#             "audio_unavailable": {"type": "boolean"},
#             "playcount": {"type": "integer"},
#             "passcount": {"type": "integer"},
#             "packs": {"type": "text"},  # TODO
#             "max_combo": {"type": "integer"},
#             "diff_aim": {"type": "float"},
#             "diff_speed": {"type": "float"},
#             "difficultyrating": {"type": "float"},
#         },
#     },
# }


@app.on_event("startup")
async def on_startup() -> None:

    # TODO: setup basic elasticsearch security features
    # https://www.elastic.co/guide/en/elasticsearch/reference/7.17/security-minimal-setup.html

    mirror.services.elastic_client = AsyncElasticsearch("http://localhost:9200")

    # create elasticsearch index if it doesn't already exist
    if not await mirror.services.elastic_client.indices.exists(
        index=mirror.config.ELASTIC_BEATMAPS_INDEX,
    ):
        await mirror.services.elastic_client.indices.create(
            index=mirror.config.ELASTIC_BEATMAPS_INDEX,
            # body=INDEX_DEFINITION,
        )

    mirror.services.http_client = httpx.AsyncClient()

    # connect to a single account now
    if DOWNLOADS_ENABLED:
        osu_session = await mirror.usecases.sessions.osu_login(
            mirror.config.OSU_ACCOUNTS[0],
        )
        assert osu_session is not None
        mirror.sessions.sessions.append(osu_session)

        # login to the other accounts in the background gradually
        for osu_account in mirror.config.OSU_ACCOUNTS[1:]:
            await mirror.usecases.sessions.osu_login_after_delay(
                osu_account=osu_account,
                # next 30 seconds to 5 minutes
                # TODO: make this configurable
                delay=random.randrange(30, 300),
            )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await mirror.services.elastic_client.close()
    await mirror.services.http_client.aclose()

    # TODO: logout accounts..? is that weird?


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/b/{beatmap_id}")
async def get_beatmap_metadata(beatmap_id: int):
    """Get a beatmap's metadata from it's id."""
    beatmap = await mirror.repositories.beatmaps.from_id(beatmap_id)
    if beatmap is None:
        return {"error": f"beatmap {beatmap_id} not found"}

    return beatmap


@app.get("/s/{set_id}")
async def get_beatmap_set_metadata(set_id: int):
    """Get a beatmap set's metadata from it's id."""
    beatmap_set = await mirror.repositories.beatmaps.from_set_id(set_id)
    if beatmap_set is None:
        return {"error": f"beatmap set {set_id} not found"}

    return beatmap_set


@app.get("/d/{set_id}")
async def download_beatmap_set(set_id: int):
    """Download a beatmap set's .osz file from it's id."""
    if not DOWNLOADS_ENABLED:
        return {"error": "downloads are disabled"}

    osz2_path = os.path.join(OSZ2_PATH, f"{set_id}.osz")

    if not os.path.exists(osz2_path):
        # download the .osz file from osu!'s servers
        downloaded = await mirror.usecases.downloads.download_beatmap_set(
            beatmap_set_id=set_id,
            osz2_path=osz2_path,
        )

        if not downloaded:
            return {"error": DOWNLOAD_FAILED_ERROR}

    return FileResponse(
        osz2_path,
        media_type="application/octet-stream",
        headers={
            "Content-Description": "File Transfer",
            "Content-Disposition": f'attachment; filename="{os.path.basename(osz2_path)}"',
        },
    )


class GameMode:
    ALL = -1
    OSU = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3


@app.get("/search/{query}")
async def search(
    query: str,
    amount: int = 100,
    offset: int = 0,
    mode: int = GameMode.OSU,
    status: int = MirrorRankedStatus.ALL,
    raw: bool = False,
):
    """Search for beatmaps by query string."""

    query_conditions: list[dict[str, Any]] = [
        # match the query string against any fields
        {"query_string": {"query": query}},
    ]

    if mode != GameMode.ALL:
        # ensure the mode matches
        query_conditions.append({"term": {"mode": mode}})

    if status != MirrorRankedStatus.ALL:
        # ensure the ranked status matches
        query_conditions.append({"term": {"approved": status}})

    response = await mirror.services.elastic_client.search(
        index=mirror.config.ELASTIC_BEATMAPS_INDEX,
        query={"bool": {"must": query_conditions}},
        size=amount,
        from_=offset,
    )

    beatmap_sets: MutableMapping[int, mirror.models.beatmap_sets.BeatmapSet] = {}

    for hit in response.body["hits"]["hits"]:
        beatmap_data = hit["_source"]

        set_id: int = beatmap_data["beatmapset_id"]
        if set_id in beatmap_sets:
            # already have this set, add the beatmap to it
            beatmap_sets[set_id].beatmaps.append(beatmap_data)
        else:
            # create a new set
            beatmap_sets[set_id] = mirror.models.beatmap_sets.BeatmapSet(
                id=beatmap_data["beatmapset_id"],
                favourites=0,
                star_rating=0,
                beatmaps=[beatmap_data],
            )

    if raw:
        # pack into the format expected by osu!
        # when searching for maps in osu!direct
        resp_data = bytearray()

        for beatmap_set in beatmap_sets.values():
            resp_data += beatmap_set.osu_direct_format()

        resp_data = Response(content=bytes(resp_data))
    else:
        resp_data = [
            beatmap_set.cheesegull_format() for beatmap_set in beatmap_sets.values()
        ]

    return resp_data


DOWNLOADS_ENABLED = False


def main() -> int:
    # must have at least 1 account's details for downloads
    global DOWNLOADS_ENABLED
    DOWNLOADS_ENABLED = len(mirror.config.OSU_ACCOUNTS) > 0

    # run the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=4378,
        reload=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
