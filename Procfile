# web: gunicorn school.wsgi --log-file -
# web: gunicorn school.wsgi --log-file -
# worker: celery -A school worker --loglevel=info
#flower: celery -A school flower --port=5555
# Procfile
# web: gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 1 --threads 1 --timeout 90 --max-requests 1000 --max-requests-jitter 50

#professional setup
# web: bin/start-pgbouncer gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 2 --threads 2 --timeout 90 --max-requests 1000 --max-requests-jitter 50
# worker: celery -A school worker --loglevel=info --concurrency=1 --pool=solo

web: bin/start-pgbouncer gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 1 --threads 1 --timeout 60
worker: celery -A school worker --loglevel=info --concurrency=1 --pool=solo

