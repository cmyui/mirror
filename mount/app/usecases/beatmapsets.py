from __future__ import annotations

from typing import Any

from app.repositories import beatmapsets


async def get_from_id(id: int) -> dict[str, Any] | None:
    """Fetch a beatmapset from it's id."""
    beatmapset = await beatmapsets.get_from_id(id)
    return beatmapset


async def get_from_checksum(checksum: str) -> dict[str, Any] | None:
    """Fetch a beatmapset from it's checksum."""
    beatmapset = await beatmapsets.get_from_checksum(checksum)
    return beatmapset


async def get_osz2_from_id(id: int) -> dict[str, Any] | None:
    """Fetch a beatmapset from it's id."""
    beatmapset = await beatmapsets.get_osz2_from_id(id)
    return beatmapset


async def search(
    query: str | None,
    amount: int,
    offset: int,
    mode: int,
    status: int,
) -> list[dict[str, Any]]:
    """Search for beatmapsets."""
    search_results = await beatmapsets.search(query, amount, offset, mode, status)
    return search_results
