from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from typing import TypedDict

from pydantic import BaseModel

from mirror.models.beatmaps import Beatmap  # TODO: fuck

if TYPE_CHECKING:
    from mirror.models.beatmaps import BeatmapCheesegull


class BeatmapSetCheesegull(TypedDict):
    SetID: int  # ": 1668433,
    ChildrenBeatmaps: list[BeatmapCheesegull]  # ": [],
    RankedStatus: int  # ": -2,
    LastUpdate: datetime  # ": "2022-01-08T02:40:21Z",
    LastChecked: datetime  # ": "2022-03-24T00:40:17Z",
    Artist: str  # ": "ABCDIsStuff",
    Title: str  # ": "Camel Man Speed",
    Creator: str  # ": "Takalaka1",
    Source: str  # ": "",
    Tags: str  # ": "",
    HasVideo: int  # ": 0,
    Genre: int  # ": 1,
    Language: int  # ": 1,
    Favourites: int  # ": 0,
    StarRating: float  # ": 0,


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
    beatmaps: list[Beatmap]

    def cheesegull_format(self) -> BeatmapSetCheesegull:
        """\
        Convert the beatmap set to cheesegull API format.

        https://docs.ripple.moe/docs/cheesegull/cheesegull-api
        """

        first_beatmap = self.beatmaps[0]  # is this what other mirrors do?

        return {
            "SetID": self.id,
            "ChildrenBeatmaps": [b.cheesegull_format() for b in self.beatmaps],
            "RankedStatus": first_beatmap.approved,  # TODO: convert
            "LastUpdate": first_beatmap.last_update,
            "LastChecked": datetime.now(),  # TODO
            "Artist": first_beatmap.artist,
            "Title": first_beatmap.title,
            "Creator": first_beatmap.creator,
            "Source": first_beatmap.source,
            "Tags": first_beatmap.tags,
            "HasVideo": first_beatmap.video,
            "Genre": first_beatmap.genre_id,
            "Language": first_beatmap.language_id,
            "Favourites": first_beatmap.favourite_count,
            "StarRating": first_beatmap.rating,
        }
