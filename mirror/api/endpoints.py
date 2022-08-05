from __future__ import annotations

import asyncio
import os.path
from typing import Any
from typing import MutableMapping
from typing import Optional

from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.routing import APIRouter

import mirror.config
import mirror.models.beatmap_sets
import mirror.models.beatmaps
import mirror.repositories.beatmap_sets
import mirror.repositories.beatmaps
import mirror.services
import mirror.sessions
import mirror.usecases.downloads
import mirror.usecases.sessions
from mirror.enums.ranked_statuses import MirrorRankedStatus

OSZ2_PATH = os.path.join(os.path.dirname(__file__), "osz2")

router = APIRouter()


@router.get("/")
async def root():
    return RedirectResponse(url="/docs")


@router.get("/b/{beatmap_id}")
async def get_beatmap_metadata(beatmap_id: int):
    """Get a beatmap's metadata from it's id."""
    beatmap = await mirror.repositories.beatmaps.from_id(beatmap_id)
    if beatmap is None:
        return {"error": f"beatmap {beatmap_id} not found"}

    # make sure we retrieve all set information
    # TODO: we need to make sure we don't end up with
    #       beatmaps which don't have all difficulties
    asyncio.create_task(mirror.repositories.beatmaps.from_set_id(beatmap.beatmapset_id))

    return beatmap


@router.get("/s/{set_id}")
async def get_beatmap_set_metadata(set_id: int):
    """Get a beatmap set's metadata from it's id."""
    beatmap_set = await mirror.repositories.beatmaps.from_set_id(set_id)
    if beatmap_set is None:
        return {"error": f"beatmap set {set_id} not found"}

    return beatmap_set


DOWNLOAD_FAILED_ERROR = (
    "Could not retrieve beatmap - this error has been reported to our devs."
)


@router.get("/d/{set_id}")
async def download_beatmap_set(set_id: int):
    """Download a beatmap set's .osz file from it's id."""
    if not mirror.config.DOWNLOADS_ENABLED:
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


@router.get("/search")
async def search(
    query: Optional[str] = None,
    amount: int = 100,
    offset: int = 0,
    mode: int = GameMode.OSU,
    status: int = MirrorRankedStatus.ALL,
    osu_direct: bool = False,
):
    """Search for beatmaps by query string."""

    query_conditions: list[dict[str, Any]] = []

    if query is not None:
        # match the query string against any fields
        query_conditions.append({"query_string": {"query": query}})

    if mode != GameMode.ALL:
        # ensure the mode matches
        query_conditions.append({"term": {"mode": mode}})

    if status != MirrorRankedStatus.ALL:
        # ensure the ranked status matches
        query_conditions.append({"term": {"approved": status}})

    response = await mirror.services.elastic_client.search(
        index=mirror.config.BEATMAPS_INDEX,
        query={"bool": {"must": query_conditions}},
        size=max(amount, 100),  # TODO: should i max() here?
        from_=offset,
    )

    beatmap_sets: MutableMapping[int, mirror.models.beatmap_sets.BeatmapSet] = {}

    for hit in response.body["hits"]["hits"]:
        beatmap_data = mirror.models.beatmaps.Beatmap(**hit["_source"])

        set_id = beatmap_data.beatmapset_id
        if set_id in beatmap_sets:
            # already have this set, add the beatmap to it
            beatmap_sets[set_id].beatmaps.append(beatmap_data)
        else:
            # create a new set
            beatmap_sets[set_id] = mirror.models.beatmap_sets.BeatmapSet(
                id=set_id,
                favourites=0,
                star_rating=0,
                beatmaps=[beatmap_data],
            )

    if osu_direct:
        # pack into the osu!direct api response foramt
        resp_data = bytearray()
        beatmap_count = 0

        for beatmap_set in beatmap_sets.values():
            resp_data += beatmap_set.osu_direct_format()
            beatmap_count += 1

        resp_data = Response(content=f"{beatmap_count}\n".encode() + bytes(resp_data))
    else:
        # pack into the cheesegull api response format
        resp_data = [
            beatmap_set.cheesegull_format() for beatmap_set in beatmap_sets.values()
        ]

    return resp_data
