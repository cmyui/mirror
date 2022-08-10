from __future__ import annotations

from app.api import responses
from app.usecases import beatmaps
from fastapi import APIRouter

router = APIRouter()


# TODO: response_model


@router.get("/beatmaps/{beatmap_id}")
async def get_beatmap(beatmap_id: int):
    beatmap = await beatmaps.get_from_id(beatmap_id)
    if beatmap is None:
        return responses.error(404, "Beatmap not found")

    return responses.success(beatmap)
