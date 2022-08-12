from __future__ import annotations

from typing import Any
from typing import Mapping

from fastapi import status
from fastapi.responses import ORJSONResponse
from fastapi.responses import Response


def success(data: Any) -> ORJSONResponse:
    return ORJSONResponse(
        content={"status": "success", "data": data},
        status_code=status.HTTP_200_OK,
    )


def _format_beatmap_set_osu_direct(beatmap_set_data: Mapping[str, Any]) -> bytes:
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


def osu_direct(beatmapsets: list[Mapping[str, Any]]) -> Response:
    # special case - return binary data
    resp_data = bytearray()
    beatmapset_count = 0

    for beatmapset_data in beatmapsets:
        difficulties_string = ",".join(
            [
                (
                    "[{difficulty_rating:.2f}⭐] {version} "
                    "{{cs: {cs} / od: {accuracy} / ar: {ar} / hp: {drain}}}@{mode_int}"
                ).format(**beatmap)
                # TODO: sort beatmaps by difficulty?
                for beatmap in beatmapset_data["beatmaps"]
            ],
        )

        beatmapset_string = (
            "{id}.osz|{artist}|{title}|{creator}|"
            "{ranked}|10.0|{last_updated}|{id}|"
            "0|{video}|0|0|0|{difficulties_string}\n"  # 0s are threadid, has_story,
            # filesize, filesize_novid.
        ).format(**beatmapset_data, difficulties_string=difficulties_string)

        resp_data.extend(beatmapset_string.encode())
        beatmapset_count += 1

    return Response(content=f"{beatmapset_count}\n".encode() + bytes(resp_data))


def error(status_code: int, message: str) -> ORJSONResponse:
    return ORJSONResponse(
        content={"status": "error", "message": message},
        status_code=status_code,
    )
