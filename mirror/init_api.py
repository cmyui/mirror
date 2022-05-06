from __future__ import annotations

import random

import httpx
from elasticsearch import AsyncElasticsearch
from fastapi.applications import FastAPI
from starlette_exporter import handle_metrics
from starlette_exporter import PrometheusMiddleware

import mirror.config
import mirror.models.beatmap_sets
import mirror.repositories.beatmap_sets
import mirror.repositories.beatmaps
import mirror.services
import mirror.sessions
import mirror.usecases.downloads
import mirror.usecases.sessions
from mirror.api import endpoints
from mirror.api.middlewares import ProcessTimeMiddleware

app = FastAPI()

app.add_middleware(PrometheusMiddleware)
app.add_middleware(ProcessTimeMiddleware)

app.add_route("/metrics", handle_metrics)
app.include_router(endpoints.router)


@app.on_event("startup")
async def on_startup() -> None:

    # TODO: setup basic elasticsearch security features
    # https://www.elastic.co/guide/en/elasticsearch/reference/7.17/security-minimal-setup.html

    mirror.services.elastic_client = AsyncElasticsearch("http://localhost:9200")

    # create elasticsearch index if it doesn't already exist
    if not await mirror.services.elastic_client.indices.exists(
        index=mirror.config.ELASTIC_BEATMAPS_INDEX,
    ):
        await mirror.services.elastic_client.indices.create(
            index=mirror.config.ELASTIC_BEATMAPS_INDEX,
            # body=INDEX_DEFINITION,
        )

    mirror.services.http_client = httpx.AsyncClient()

    # must have at least 1 account configured for downloads to work
    downloads_available = len(mirror.config.OSU_ACCOUNTS) > 0
    if mirror.config.DOWNLOADS_ENABLED and not downloads_available:
        print("WARNING: no osu! accounts configured, downloads will not work")
        mirror.config.DOWNLOADS_ENABLED = False

    # connect to a single account now
    if mirror.config.DOWNLOADS_ENABLED:
        osu_session = await mirror.usecases.sessions.osu_login(
            mirror.config.OSU_ACCOUNTS[0],
        )
        assert osu_session is not None
        mirror.sessions.sessions.append(osu_session)

        # login to the other accounts in the background gradually
        for osu_account in mirror.config.OSU_ACCOUNTS[1:]:
            await mirror.usecases.sessions.osu_login_after_delay(
                osu_account=osu_account,
                # next 30 seconds to 5 minutes
                # TODO: make this configurable
                delay=random.randrange(30, 300),
            )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await mirror.services.elastic_client.close()
    await mirror.services.http_client.aclose()

    # TODO: logout accounts..? is that weird?
