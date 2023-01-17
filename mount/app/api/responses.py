from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Sequence

from fastapi import status
from fastapi.responses import ORJSONResponse
from fastapi.responses import Response


def success(data: Any) -> ORJSONResponse:
    return ORJSONResponse(
        content={"status": "success", "data": data},
        status_code=status.HTTP_200_OK,
    )


def error(status_code: int, message: str) -> ORJSONResponse:
    return ORJSONResponse(
        content={"status": "error", "message": message},
        status_code=status_code,
    )


# special cases


def osu_direct(beatmapsets: Sequence[Mapping[str, Any]]) -> Response:
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
        print(beatmapset_data)
        beatmapset_string = (
            "{id}.osz|{artist}|{title}|{creator}|"
            # TODO: the 10.0 is beatmap rating, which we don't have yet.
            # this is what creates the bar in osu!direct
            # https://i.cmyui.xyz/mt693h9hjl6km4hCgw.png
            "{ranked}|10.0|{last_updated}|{id}|"
            "0|{video}|0|0|0|{difficulties_string}\n"  # 0s are threadid, has_story,
            # filesize, filesize_novid.
        ).format(**beatmapset_data, difficulties_string=difficulties_string)

        resp_data.extend(beatmapset_string.encode())
        beatmapset_count += 1

    return Response(
        content=f"{beatmapset_count}\n".encode() + bytes(resp_data),
        media_type="text/plain",
    )
