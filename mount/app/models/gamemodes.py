from __future__ import annotations

from enum import IntEnum


class GameMode(IntEnum):
    OSU = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3

    # NOTE: this is not an official osu!api gamemode
    ALL = -1


def gamemode_int_to_str(gamemode: GameMode) -> str:
    return {
        GameMode.OSU: "osu",
        GameMode.TAIKO: "taiko",
        GameMode.CATCH: "catch",
        GameMode.MANIA: "mania",
        # GameMode.ALL: "all",
    }[gamemode]
