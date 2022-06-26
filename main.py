#!/usr/bin/env python3.10
from __future__ import annotations

import logging

import uvicorn

from mirror import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s %(message)s",
)


def main() -> int:
    # run the server
    uvicorn.run(
        "mirror.init_api:asgi_app",
        host="127.0.0.1",
        port=4378,
        reload=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
