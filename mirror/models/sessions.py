from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OsuWebSession:
    username: str
    password: str

    xsrf_token: str
    osu_session_token: str
