from __future__ import annotations

from fastapi import APIRouter

from . import beatmaps
from . import beatmapsets

router = APIRouter()

router.include_router(beatmaps.router)
router.include_router(beatmapsets.router)
