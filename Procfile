# web: gunicorn school.wsgi --log-file -

web: gunicorn school.wsgi --log-file -

worker: celery -A school worker --loglevel=info

#flower: celery -A school flower --port=5555

web: gunicorn school.asgi:application -k uvicorn.workers.UvicornWorker --workers 4 --threads 2 --timeout 90
