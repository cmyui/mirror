from __future__ import annotations


class GameMode:
    ALL = -1
    OSU = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3


def gamemode_int_to_str(status: int) -> str:
    return {
        # GameMode.ALL: "all",
        GameMode.OSU: "osu",
        GameMode.TAIKO: "taiko",
        GameMode.CATCH: "catch",
        GameMode.MANIA: "mania",
    }[status]
