import os
import django
from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from fastapi_app.main import app as fastapi_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school.settings')
django.setup()

django_app = get_asgi_application()

main_app = FastAPI()

# Mount Django and FastAPI
main_app.mount("/", django_app)         # Django handles root (e.g. /about-us/)
main_app.mount("/api", fastapi_app)     # FastAPI handles /api/exam-rules/

# This is the ASGI application
application = main_app
