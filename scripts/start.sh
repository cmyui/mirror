#!/usr/bin/env bash
set -euo pipefail

wait-for-it $WRITE_DB_HOST:$WRITE_DB_PORT
wait-for-it $ELASTIC_HOST:$ELASTIC_PORT
# wait-for-it $REDIS_HOST:$REDIS_PORT
# wait-for-it $RABBITMQ_HOST:$RABBITMQ_PORT

case $APP_COMPONENT in
    "tests")
        /scripts/run-tests.sh
        ;;
    "api" | *)
    exec uvicorn \
        --host 0.0.0.0 \
        --port 80 \
        --no-access-log \
        $EXTRA_PARAMS \
        app.http_boot:systemic
    ;;
