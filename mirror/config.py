from starlette.config import Config
from ast import literal_eval

config = Config(".env")

ELASTIC_BEATMAPS_INDEX = config.get("ELASTIC_BEATMAPS_INDEX")
# ELASTIC_BEATMAP_SETS_INDEX = config.get("ELASTIC_BEATMAP_SETS_INDEX")

# authentication
OSU_ACCOUNTS = config.get("OSU_ACCOUNTS", cast=literal_eval)  # downloads
OSU_API_KEY = config.get("OSU_API_KEY")  # metadata
