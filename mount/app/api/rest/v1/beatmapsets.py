from __future__ import annotations

from app.api import responses
from app.models.gamemodes import GameMode
from app.models.ranked_statuses import OsuAPIRankedStatus
from app.usecases import beatmapsets
from fastapi import APIRouter
from fastapi.param_functions import Query
from fastapi.responses import Response

router = APIRouter()


# TODO: response_model


@router.get("/beatmapsets/search")
async def get_beatmapset_search(
    # TODO: are any of these default weird?
    query: str | None = None,
    amount: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: OsuAPIRankedStatus = OsuAPIRankedStatus.ALL,
    mode: GameMode = GameMode.ALL,
    osu_direct: bool = False,
):
    search_results = await beatmapsets.search(
        query=query,
        mode=mode,
        status=status,
        amount=amount,
        offset=offset,
    )
    if osu_direct:
        return responses.osu_direct(search_results)

    return responses.success(search_results)


@router.get("/beatmapsets/{beatmapset_id}")
async def get_beatmapset(beatmapset_id: int):
    beatmapset = await beatmapsets.get_from_id(beatmapset_id)
    if beatmapset is None:
        return responses.error(404, "Beatmapset not found")

    return responses.success(beatmapset)


@router.get("/beatmapsets/{beatmapset_id}/osz2")
async def get_beatmapset_osz2(beatmapset_id: int):
    beatmapset_osz = await beatmapsets.get_osz2_from_id(beatmapset_id)
    if beatmapset_osz is None:
        return responses.error(404, "Beatmapset not found")

    return Response(
        content=beatmapset_osz,
        headers={"Content-Disposition": f'attachment; filename="{beatmapset_id}.osz"'},
    )
