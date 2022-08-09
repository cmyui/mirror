from __future__ import annotations

from pydantic import BaseModel


class BeatmapSet(BaseModel):
    """\
    A model representing a beatmap set from the v1 osu! API.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    id: int
    # ranked_status: int
    # last_updated: datetime
    # last_checked: datetime
    # artist: str
    # title: str
    # creator: str
    # source: str
    # tags: str
    # has_video: bool
    # genre: int
    # language: int
    favourites: int
    star_rating: float  # float?
    # beatmaps: list[Beatmap]
