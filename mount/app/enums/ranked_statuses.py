from __future__ import annotations


class OsuAPIRankedStatus:
    GRAVEYARD = -2
    WORK_IN_PROGRESS = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


class OsuDirectStatus:
    RANKED = 0
    PENDING = 2
    QUALIFIED = 3
    RANKED = 4
    GRAVEYARD = 5
    # 6 is mia
    PLAYED_BEFORE = 7
    LOVED = 8


class MirrorRankedStatus(OsuAPIRankedStatus):
    ALL = -3


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
