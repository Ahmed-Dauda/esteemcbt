# web: gunicorn school.wsgi --log-file -
# web: gunicorn school.wsgi --log-file -
# worker: celery -A school worker --loglevel=info
#flower: celery -A school flower --port=5555
# Procfile
web: gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 2 --threads 1 --timeout 90
