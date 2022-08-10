from __future__ import annotations

from enum import IntEnum


class OsuAPIRankedStatus(IntEnum):
    GRAVEYARD = -2
    WORK_IN_PROGRESS = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4

    # NOTE: this is not an official osu!api ranked status
    ALL = -3


def ranked_status_int_to_str(status: OsuAPIRankedStatus) -> str:
    return {
        OsuAPIRankedStatus.GRAVEYARD: "graveyard",
        OsuAPIRankedStatus.WORK_IN_PROGRESS: "pending",
        OsuAPIRankedStatus.PENDING: "pending",
        OsuAPIRankedStatus.RANKED: "ranked",
        OsuAPIRankedStatus.APPROVED: "approved",
        OsuAPIRankedStatus.QUALIFIED: "qualified",
        OsuAPIRankedStatus.LOVED: "loved",
        # OsuAPIRankedStatus.ALL: "all",
    }[status]


class OsuDirectStatus(IntEnum):
    RANKED = 0
    PENDING = 2
    QUALIFIED = 3
    # RANKED = 4  # TODO wtf
    GRAVEYARD = 5
    # 6 is mia
    PLAYED_BEFORE = 7
    LOVED = 8


def osu_api_to_osu_direct_status(osu_api_status: OsuAPIRankedStatus) -> OsuDirectStatus:
    return {
        OsuAPIRankedStatus.GRAVEYARD: OsuDirectStatus.GRAVEYARD,
        OsuAPIRankedStatus.WORK_IN_PROGRESS: OsuDirectStatus.PENDING,
        OsuAPIRankedStatus.PENDING: OsuDirectStatus.PENDING,
        OsuAPIRankedStatus.RANKED: OsuDirectStatus.RANKED,
        OsuAPIRankedStatus.APPROVED: OsuDirectStatus.RANKED,
        OsuAPIRankedStatus.QUALIFIED: OsuDirectStatus.QUALIFIED,
        OsuAPIRankedStatus.LOVED: OsuDirectStatus.LOVED,
    }[osu_api_status]


def osu_direct_to_osu_api_status(osu_api_status: OsuDirectStatus) -> OsuAPIRankedStatus:
    return {
        OsuDirectStatus.GRAVEYARD: OsuAPIRankedStatus.GRAVEYARD,
        OsuDirectStatus.PENDING: OsuAPIRankedStatus.WORK_IN_PROGRESS,
        OsuDirectStatus.PENDING: OsuAPIRankedStatus.PENDING,
        OsuDirectStatus.RANKED: OsuAPIRankedStatus.RANKED,
        OsuDirectStatus.RANKED: OsuAPIRankedStatus.APPROVED,
        OsuDirectStatus.QUALIFIED: OsuAPIRankedStatus.QUALIFIED,
        OsuDirectStatus.LOVED: OsuAPIRankedStatus.LOVED,
    }[osu_api_status]
