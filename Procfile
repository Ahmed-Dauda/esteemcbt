# web: gunicorn school.wsgi --log-file -

web: gunicorn school.wsgi --workers 3 --timeout 30

worker: celery -A school worker --loglevel=info

flower: celery -A school flower --port=5555

# web: uvicorn school.asgi:application --host=0.0.0.0 --port=${PORT:-5000}
# web: uvicorn fastapi_app.main:app --host=0.0.0.0 --port=$PORT

# web: uvicorn school.asgi:main_app --host=0.0.0.0 --port=${PORT:-5000}
