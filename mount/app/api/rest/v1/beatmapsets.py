from __future__ import annotations

from fastapi import APIRouter
from app.api import responses
from app.usecases import beatmapsets

router = APIRouter()


# TODO: response_model


@router.get("/beatmapsets/{beatmapset_id}")
async def get_beatmapset(beatmapset_id: int):
    beatmapset = await beatmapsets.get_from_id(beatmapset_id)
    if beatmapset is None:
        return responses.error(404, "Beatmap not found")

    return responses.success(beatmapset)
