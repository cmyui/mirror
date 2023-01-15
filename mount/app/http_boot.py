from __future__ import annotations

import atexit

from app import logger
from app import settings
from app.api.rest import init_api

logger.overwrite_exception_hook()
atexit.register(logger.restore_exception_hook)

logger.configure_logging(
    app_env=settings.APP_ENV,
    log_level=settings.LOG_LEVEL,
)

service_api = init_api()
