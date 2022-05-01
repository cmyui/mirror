from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BeatmapSet(BaseModel):
    """\
    A model representing a beatmap set from the v1 osu! API.

    https://github.com/ppy/osu-api/wiki#apiget_beatmaps
    """

    ...
