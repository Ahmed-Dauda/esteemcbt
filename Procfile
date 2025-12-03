# web: gunicorn school.wsgi --log-file -
# web: gunicorn school.wsgi --log-file -
# worker: celery -A school worker --loglevel=info
#flower: celery -A school flower --port=5555
# Procfile
# web: gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 1 --threads 1 --timeout 90 --max-requests 1000 --max-requests-jitter 50

# web: bin/start-pgbouncer gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 2 --threads 2 --timeout 90 --max-requests 1000 --max-requests-jitter 50
# celery -A school worker --loglevel=info --concurrency=4

# Web dyno: Uvicorn + Gunicorn
# web: gunicorn esteemcbt.wsgi:application --log-file -
# # Celery worker
# worker: celery -A school worker \
#         --loglevel=info \
#         --concurrency=4 \
#         --prefetch-multiplier=1 \
#         --max-tasks-per-child=50
