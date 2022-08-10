#!/usr/bin/env python3.10
from __future__ import annotations

import logging

import uvicorn

from mount.app import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s %(message)s",
)


def main() -> int:
    # run the server
    uvicorn.run(
        "mount.api.rest.init_api:asgi_app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
