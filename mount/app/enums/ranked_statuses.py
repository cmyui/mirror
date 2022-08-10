from __future__ import annotations


class OsuAPIRankedStatus:
    GRAVEYARD = -2
    WORK_IN_PROGRESS = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


class MirrorRankedStatus(OsuAPIRankedStatus):
    ALL = -3


def ranked_status_int_to_str(status: int) -> str:
    return {
        # MirrorRankedStatus.ALL: "all",
        MirrorRankedStatus.GRAVEYARD: "graveyard",
        MirrorRankedStatus.WORK_IN_PROGRESS: "pending",
        MirrorRankedStatus.PENDING: "pending",
        MirrorRankedStatus.RANKED: "ranked",
        MirrorRankedStatus.APPROVED: "approved",
        MirrorRankedStatus.QUALIFIED: "qualified",
        MirrorRankedStatus.LOVED: "loved",
    }[status]


class OsuDirectStatus:
    RANKED = 0
    PENDING = 2
    QUALIFIED = 3
    RANKED = 4  # TODO wtf
    GRAVEYARD = 5
    # 6 is mia
    PLAYED_BEFORE = 7
    LOVED = 8


def osu_api_to_osu_direct_status(osu_api_status: int) -> int:
    return {
        OsuAPIRankedStatus.GRAVEYARD: OsuDirectStatus.GRAVEYARD,
        OsuAPIRankedStatus.WORK_IN_PROGRESS: OsuDirectStatus.PENDING,
        OsuAPIRankedStatus.PENDING: OsuDirectStatus.PENDING,
        OsuAPIRankedStatus.RANKED: OsuDirectStatus.RANKED,
        OsuAPIRankedStatus.APPROVED: OsuDirectStatus.RANKED,
        OsuAPIRankedStatus.QUALIFIED: OsuDirectStatus.QUALIFIED,
        OsuAPIRankedStatus.LOVED: OsuDirectStatus.LOVED,
    }[osu_api_status]


def osu_direct_to_osu_api_status(osu_api_status: int) -> int:
    return {
        OsuDirectStatus.GRAVEYARD: OsuAPIRankedStatus.GRAVEYARD,
        OsuDirectStatus.PENDING: OsuAPIRankedStatus.WORK_IN_PROGRESS,
        OsuDirectStatus.PENDING: OsuAPIRankedStatus.PENDING,
        OsuDirectStatus.RANKED: OsuAPIRankedStatus.RANKED,
        OsuDirectStatus.RANKED: OsuAPIRankedStatus.APPROVED,
        OsuDirectStatus.QUALIFIED: OsuAPIRankedStatus.QUALIFIED,
        OsuDirectStatus.LOVED: OsuAPIRankedStatus.LOVED,
    }[osu_api_status]
