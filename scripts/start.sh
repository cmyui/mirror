#!/usr/bin/env bash
set -euo pipefail

# wait for connected services to be ready
export WAITFORIT_TIMEOUT=0
wait-for-it $ELASTIC_HOST:$ELASTIC_PORT

case $APP_COMPONENT in
    "tests")
        /scripts/run-tests.sh
        ;;

    "crawler-daemon")
        python -m app.workers.daemons.crawler
        ;;

    "api")
        exec uvicorn \
            --host 0.0.0.0 \
            --port 80 \
            --reload \
            --no-access-log \
            --no-date-header \
            --no-server-header \
            app.http_boot:service_api
        ;;

    *)
        echo "Unknown APP_COMPONENT: $APP_COMPONENT"
        exit 1
        ;;
esac
