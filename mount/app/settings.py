from __future__ import annotations

from starlette.config import Config

config = Config(".env")

# asgi + app
APP_ENV = config.get("APP_ENV")
APP_COMPONENT = config.get("APP_COMPONENT")
APP_HOST = config.get("APP_HOST")
APP_PORT = config.get("APP_PORT", cast=int)

# https://docs.python.org/3/library/logging.html#levels
LOG_LEVEL = config.get("LOG_LEVEL", cast=int)

# elasticsearch
ELASTIC_HOST = config.get("ELASTIC_HOST")
ELASTIC_PORT = config.get("ELASTIC_PORT")
ELASTIC_USER = config.get("ELASTIC_USER")
ELASTIC_PASS = config.get("ELASTIC_PASS")
BEATMAPS_INDEX = config.get("BEATMAPS_INDEX")
BEATMAPSETS_INDEX = config.get("BEATMAPSETS_INDEX")

# osu! api
OSU_API_CLIENT_ID = config.get("OSU_API_CLIENT_ID", cast=int)
OSU_API_CLIENT_SECRET = config.get("OSU_API_CLIENT_SECRET")

OSU_API_REQUEST_INTERVAL = config.get("OSU_API_REQUEST_INTERVAL", cast=float)
OSU_API_MAX_REQUESTS_PER_MINUTE = config.get(
    "OSU_API_MAX_REQUESTS_PER_MINUTE",
    cast=int,
)

# settings
MAX_DISK_USAGE_GB = config.get("MAX_DISK_USAGE_GB", cast=int)
MAX_RAM_USAGE_GB = config.get("MAX_RAM_USAGE_GB", cast=int)
