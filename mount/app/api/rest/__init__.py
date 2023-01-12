from __future__ import annotations

import logging

from app import services
from app import settings
from app.api.rest import v1
from app.services import OsuAPIClient
from elasticsearch import AsyncElasticsearch
from fastapi.applications import FastAPI
from starlette_exporter import handle_metrics
from starlette_exporter import PrometheusMiddleware

from . import middlewares


def init_middlewares(app: FastAPI) -> None:
    """Initialize the app's middlewares."""
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(middlewares.ProcessTimeMiddleware)


def init_exception_handlers(app: FastAPI) -> None:
    """Initialize the app's exception handlers."""
    pass  # TODO?


def init_events(app: FastAPI) -> None:
    """Setup the app's startup & shutdown events."""

    @app.on_event("startup")
    async def on_startup() -> None:

        # TODO: setup basic elasticsearch security features
        # https://www.elastic.co/guide/en/elasticsearch/reference/7.17/security-minimal-setup.html

        services.elastic_client = AsyncElasticsearch(
            f"https://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}",
            basic_auth=(settings.ELASTIC_USER, settings.ELASTIC_PASS),
            verify_certs=False,  # TODO: not this
        )

        # create elasticsearch indices if they don't already exist
        for index in (settings.BEATMAPS_INDEX, settings.BEATMAPSETS_INDEX):
            if not await services.elastic_client.indices.exists(index=index):
                await services.elastic_client.indices.create(index=index)

        services.osu_api_client = OsuAPIClient(
            client_id=settings.OSU_API_CLIENT_ID,
            client_secret=settings.OSU_API_CLIENT_SECRET,
            scope=settings.OSU_API_SCOPE,
            username=settings.OSU_API_USERNAME,
            password=settings.OSU_API_PASSWORD,
            request_interval=settings.OSU_API_REQUEST_INTERVAL,
            max_requests_per_minute=settings.OSU_API_MAX_REQUESTS_PER_MINUTE,
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await services.elastic_client.close()

        # TODO: logout accounts..? is that weird?


def init_endpoints(app: FastAPI) -> None:
    """Initialize the app's endpoints."""
    app.include_router(v1.router)

    app.add_route("/metrics", handle_metrics)


def init_api() -> FastAPI:
    """Initialize the API."""
    app = FastAPI()

    # init logging
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(message)s",
    )

    init_middlewares(app)
    init_exception_handlers(app)
    init_events(app)
    init_endpoints(app)

    return app
