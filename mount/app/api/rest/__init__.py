from __future__ import annotations

import logging

from app import config
from app import services
from app.api.rest import v1
from elasticsearch import AsyncElasticsearch
from fastapi.applications import FastAPI
from starlette_exporter import handle_metrics
from starlette_exporter import PrometheusMiddleware
from osu import AsynchronousClient

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
            f"http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}",
        )

        # create elasticsearch index if it doesn't already exist
        if not await services.elastic_client.indices.exists(
            index=config.BEATMAPS_INDEX,
        ):
            await services.elastic_client.indices.create(
                index=config.BEATMAPS_INDEX,
                # body=INDEX_DEFINITION,
            )

        services.osu_api_client = AsynchronousClient.from_client_credentials(
            client_id=config.OSU_API_CLIENT_ID,
            client_secret=config.OSU_API_CLIENT_SECRET,
            redirect_url=config.OSU_API_REDIRECT_URL,
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
        level=config.LOG_LEVEL,
        format="%(asctime)s %(message)s",
    )

    init_middlewares(app)
    init_exception_handlers(app)
    init_events(app)
    init_endpoints(app)

    return app
