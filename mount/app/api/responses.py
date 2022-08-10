from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.responses import ORJSONResponse


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
