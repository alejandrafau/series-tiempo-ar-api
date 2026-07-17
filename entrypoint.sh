#!/bin/bash
set -e

# Esperar a PostgreSQL
echo "Esperando a PostgreSQL en $DATABASE_HOST..."
until python -c "
import socket, time, sys
for _ in range(30):
    try:
        socket.create_connection(('$DATABASE_HOST', 5432), timeout=2)
        sys.exit(0)
    except Exception:
        time.sleep(2)
sys.exit(1)
"; do
    echo "Reintentando..."
done
echo "PostgreSQL listo."

# Esperar a Redis
echo "Esperando a Redis en $DEFAULT_REDIS_HOST..."
until python -c "
import socket, time, sys
for _ in range(30):
    try:
        socket.create_connection(('$DEFAULT_REDIS_HOST', int('${DEFAULT_REDIS_PORT:-6379}')), timeout=2)
        sys.exit(0)
    except Exception:
        time.sleep(2)
sys.exit(1)
"; do
    echo "Reintentando..."
done
echo "Redis listo."

if [ "$CONTAINER_ROLE" = "web" ]; then
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    exec gunicorn conf.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --timeout 300 \
        --log-level info

elif [ "$CONTAINER_ROLE" = "worker" ]; then
    exec python manage.py rqworker $WORKER_QUEUES

else
    echo "ERROR: CONTAINER_ROLE debe ser 'web' o 'worker'"
    exit 1
fi