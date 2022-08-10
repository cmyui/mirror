from __future__ import annotations

from ast import literal_eval

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
BEATMAPS_INDEX = config.get("BEATMAPS_INDEX")
BEATMAPSETS_INDEX = config.get("BEATMAPSETS_INDEX")

# rabbitmq
AMQP_HOST = config.get("AMQP_HOST")
AMQP_PORT = config.get("AMQP_PORT", cast=int)
AMQP_USER = config.get("AMQP_USER")
AMQP_PASS = config.get("AMQP_PASS")

# osu! api
OSU_API_CLIENT_ID = config.get("OSU_API_CLIENT_ID", cast=int)
OSU_API_CLIENT_SECRET = config.get("OSU_API_CLIENT_SECRET")
OSU_API_REDIRECT_URL = config.get("OSU_API_REDIRECT_URL")

# settings
MAX_DISK_USAGE_GB = config.get("MAX_DISK_USAGE_GB", cast=int)
MAX_RAM_USAGE_GB = config.get("MAX_RAM_USAGE_GB", cast=int)

# feature flags
DOWNLOADS_ENABLED = config.get("DOWNLOADS_ENABLED", cast=bool)
