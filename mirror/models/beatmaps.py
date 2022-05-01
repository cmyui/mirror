from datetime import datetime
from typing import Optional
from pydantic import BaseModel


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
    packs: str  # TODO csv
    max_combo: int
    diff_aim: float
    diff_speed: float
    difficultyrating: float
