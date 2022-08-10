from __future__ import annotations

from elasticsearch import AsyncElasticsearch
from osu import AsynchronousClient

elastic_client: AsyncElasticsearch
osu_api_client: AsynchronousClient
