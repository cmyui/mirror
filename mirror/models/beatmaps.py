from __future__ import annotations

from datetime import datetime
from typing import Optional
from typing import TypedDict

from pydantic import BaseModel


class BeatmapCheesegull(TypedDict):
    """\
    A model representing a beatmap set from a cheesegull API.

    https://docs.ripple.moe/docs/cheesegull/cheesegull-api
    """

    BeatmapID: int  # ID of the beatmap.
    ParentSetID: int  # ID of the parent beatmap set.
    DiffName: str  # Name of the difficulty.
    FileMD5: str  # MD5 hash of the .osu file.
    Mode: int  # osu! game mode of this beatmap.
    BPM: float  # Beats per minute of the song. Probably inaccurate and wrong, and you probably shouldn’t use this for any calculation, just for display.
    AR: float  # Approach rate.
    OD: float  # Overall difficulty.
    CS: float  # Circle size.
    HP: float  # Health drain.
    TotalLength: int  # The total length of the song in seconds.
    HitLength: int  # The length of the part with objects in the beatmap.
    Playcount: int  # Number of plays on this beatmap.
    Passcount: int  # Number of passes on this beatmap.
    MaxCombo: int  # Maximum combo someone can achieve.
    DifficultyRating: float  # Star difficulty rating of the map. If this is an osu! standard map, this is the star rating for osu! standard. There’s no way to get the star rating for other modes in converted beatmaps.


class Beatmap(BaseModel):
    """\
    A model representing a beatmap from the v1 osu! API.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    beatmapset_id: int
    beatmap_id: int
    approved: int
    total_length: int
    hit_length: int
    version: str
    file_md5: str
    diff_size: float
    diff_overall: float
    diff_approach: float
    diff_drain: float
    mode: int
    count_normal: int
    count_slider: int
    count_spinner: int
    submit_date: datetime
    approved_date: Optional[datetime]
    last_update: datetime
    artist: str
    artist_unicode: Optional[str]
    title: str
    title_unicode: Optional[str]
    creator: str
    creator_id: int
    bpm: float  # TODO
    source: str
    tags: str  # TODO csv
    genre_id: int
    language_id: int
    favourite_count: int
    rating: float
    storyboard: bool
    video: bool
    download_unavailable: bool
    audio_unavailable: bool
    playcount: int
    passcount: int
    packs: Optional[str]  # TODO csv
    max_combo: Optional[int]
    diff_aim: Optional[float]
    diff_speed: Optional[float]
    difficultyrating: float

    def cheesegull_format(self) -> BeatmapCheesegull:
        """Convert the beatmap set to cheesegull API format."""
        return {
            "BeatmapID": self.beatmap_id,
            "ParentSetID": self.beatmapset_id,
            "DiffName": self.version,
            "FileMD5": self.file_md5,
            "Mode": self.mode,
            "BPM": self.bpm,
            "AR": self.diff_approach,
            "OD": self.diff_overall,
            "CS": self.diff_size,
            "HP": self.diff_drain,
            "TotalLength": self.total_length,
            "HitLength": self.hit_length,
            "Playcount": self.playcount,
            "Passcount": self.passcount,
            "MaxCombo": self.max_combo or 0,  # TODO: what to do here?
            "DifficultyRating": self.difficultyrating,
        }
