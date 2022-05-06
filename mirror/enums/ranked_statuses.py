from __future__ import annotations


class CheesegullRankedStatus:
    NOT_SUBMITTED = -1
    PENDING = 0
    UPDATE_AVAILABLE = 1
    RANKED = 2
    APPROVED = 3
    QUALIFIED = 4
    LOVED = 5


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


def osu_api_to_cheesegull_status(osu_api_status: int) -> int:
    return {
        OsuAPIRankedStatus.GRAVEYARD: CheesegullRankedStatus.PENDING,
        OsuAPIRankedStatus.WORK_IN_PROGRESS: CheesegullRankedStatus.PENDING,
        OsuAPIRankedStatus.PENDING: CheesegullRankedStatus.PENDING,
        OsuAPIRankedStatus.RANKED: CheesegullRankedStatus.RANKED,
        OsuAPIRankedStatus.APPROVED: CheesegullRankedStatus.APPROVED,
        OsuAPIRankedStatus.QUALIFIED: CheesegullRankedStatus.QUALIFIED,
        OsuAPIRankedStatus.LOVED: CheesegullRankedStatus.LOVED,
    }[osu_api_status]
