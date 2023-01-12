#!/usr/bin/env python3.10
from __future__ import annotations

import logging

import uvicorn

from mount.app import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(message)s",
)


def main() -> int:
    # run the server
    uvicorn.run(
        "mount.api.rest.init_api:asgi_app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
        server_header=False,
        date_header=False,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
