#!/usr/bin/env python3.10
from __future__ import annotations

import logging

import uvicorn

import mirror.config

logging.basicConfig(
    level=mirror.config.LOG_LEVEL,
    format="%(asctime)s %(message)s",
)


def main() -> int:
    # run the server
    uvicorn.run(
        "mirror.api.rest.init_api:asgi_app",
        host=mirror.config.APP_HOST,
        port=mirror.config.APP_PORT,
        reload=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
