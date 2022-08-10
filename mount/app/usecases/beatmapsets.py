from __future__ import annotations

from typing import Any
from typing import Mapping

from app.repositories import beatmapsets


async def get_from_id(id: int) -> Mapping[str, Any] | None:
    """Fetch a beatmapset from it's id."""
    beatmapset = await beatmapsets.get_from_id(id)
    return beatmapset


async def get_from_checksum(checksum: str) -> Mapping[str, Any] | None:
    """Fetch a beatmapset from it's checksum."""
    beatmapset = await beatmapsets.get_from_checksum(checksum)
    return beatmapset
