from __future__ import annotations

from typing import Any
from typing import Mapping

from app.api import responses
from app.enums.gamemodes import GameMode
from app.enums.ranked_statuses import OsuAPIRankedStatus
from app.usecases import beatmapsets
from fastapi import APIRouter
from fastapi.param_functions import Query
from fastapi.responses import Response

router = APIRouter()


# TODO: response_model


# TODO: where should this live?
def osu_direct_format(beatmap_set_data: Mapping[str, Any]) -> bytes:
    difficulties_string = ",".join(
        [
            (
                "[{difficulty_rating:.2f}⭐] {version} "
                "{{cs: {cs} / od: {accuracy} / ar: {ar} / hp: {drain}}}@{mode_int}"
            ).format(**beatmap)
            # TODO: sort beatmaps by difficulty?
            for beatmap in beatmap_set_data["beatmaps"]
        ],
    )

    return (
        (
            "{id}.osz|{artist}|{title}|{creator}|"
            "{ranked}|10.0|{last_updated}|{id}|"
            "0|{video}|0|0|0|{difficulties_string}\n"  # 0s are threadid, has_story,
            # filesize, filesize_novid.
        )
        .format(**beatmap_set_data, difficulties_string=difficulties_string)
        .encode()
    )


@router.get("/beatmapsets/search")
async def get_beatmapset_search(
    # TODO: are any of these default weird?
    query: str | None = None,
    amount: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: OsuAPIRankedStatus = OsuAPIRankedStatus.RANKED,
    mode: GameMode = GameMode.OSU,
    osu_direct: bool = False,
):
    search_results = await beatmapsets.search(query, amount, offset, mode, status)

    if osu_direct:
        # special case - return binary data
        resp_data = bytearray()
        beatmapset_count = 0

        for beatmap_set_data in search_results:
            resp_data.extend(osu_direct_format(beatmap_set_data))
            beatmapset_count += 1

        return Response(content=f"{beatmapset_count}\n".encode() + bytes(resp_data))

    return responses.success(search_results)


@router.get("/beatmapsets/{beatmapset_id}")
async def get_beatmapset(beatmapset_id: int):
    beatmapset = await beatmapsets.get_from_id(beatmapset_id)
    if beatmapset is None:
        return responses.error(404, "Beatmapset not found")

    return responses.success(beatmapset)


@router.get("/beatmapsets/{beatmapset_id}/osz2")
async def get_beatmapset_osz2(beatmapset_id: int):
    beatmapset = await beatmapsets.get_osz2_from_id(beatmapset_id)
    if beatmapset is None:
        return responses.error(404, "Beatmapset not found")

    return responses.success(beatmapset)
