from __future__ import annotations

from elasticsearch import AsyncElasticsearch
from httpx import AsyncClient

elastic_client: AsyncElasticsearch
http_client: AsyncClient
