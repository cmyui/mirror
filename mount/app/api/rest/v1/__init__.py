from fastapi import APIRouter

from . import beatmaps
from . import beatmap_sets

router = APIRouter()

router.include_router(beatmaps.router)
router.include_router(beatmap_sets.router)
