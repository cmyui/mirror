from __future__ import annotations
from typing import Any, Mapping

from app.repositories import beatmaps


async def get_from_id(id: int) -> Mapping[str, Any] | None:
    """Fetch a beatmap from it's id."""
    beatmap = await beatmaps.get_from_id(id)
    return beatmap


async def get_from_checksum(checksum: str) -> Mapping[str, Any] | None:
    """Fetch a beatmap from it's checksum."""
    beatmap = await beatmaps.get_from_checksum(checksum)
    return beatmap
