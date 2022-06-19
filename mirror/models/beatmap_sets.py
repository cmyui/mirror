from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from typing import TypedDict

from pydantic import BaseModel

from mirror.enums.ranked_statuses import (
    osu_api_to_cheesegull_status,
)
from mirror.models.beatmaps import Beatmap  # TODO: fuck

if TYPE_CHECKING:
    from mirror.models.beatmaps import BeatmapCheesegull


class BeatmapSetCheesegull(TypedDict):
    """\
    A model representing a beatmap set from a cheesegull API.

    https://docs.ripple.moe/docs/cheesegull/cheesegull-api
    """

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
        """Convert the beatmap set to cheesegull API format."""
        first_beatmap = self.beatmaps[0]  # is this what other mirrors do?

        return {
            "SetID": self.id,
            "ChildrenBeatmaps": [b.cheesegull_format() for b in self.beatmaps],
            "RankedStatus": osu_api_to_cheesegull_status(first_beatmap.approved),
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

    def osu_direct_format(self) -> bytes:
        """Convert the beatmap set to osu!direct format."""
        # create a list of difficult names sorted by difficulty
        # '[5.19⭐] Insane {cs: 6.0 / od: 7.0 / ar: 7.0 / hp: 2.0}@0'
        sorted_beatmaps = sorted(self.beatmaps, key=lambda m: m.difficultyrating)
        diffs_str = ",".join(
            [
                (
                    "[{difficultyrating:.2f}⭐] {version} "
                    "{{cs: {diff_size} / od: {diff_overall} / ar: {diff_approach} / hp: {diff_drain}}}@{mode}"
                ).format(**row.__dict__)
                for row in sorted_beatmaps
            ],
        )

        first_beatmap = sorted_beatmaps[0]

        # b'1141.osz|FAIRY FORE|Vivid|Hitoshirenu Shourai|1|10.0|2007-11-01 05:09:15|141|0|False|0|0|0|[5.19⭐] Insane {cs: 6.0 / od: 7.0 / ar: 7.0 / hp: 2.0}@0'
        return (
            (
                "{beatmapset_id}.osz|{artist}|{title}|{creator}|"
                "{approved}|10.0|{last_update}|{beatmapset_id}|"
                "0|{video}|0|0|0|{diffs}\n"  # 0s are threadid, has_story,
                # filesize, filesize_novid.
            )
            .format(
                **self.__dict__,
                **first_beatmap.__dict__,
                diffs=diffs_str,
            )
            .encode()
        )
