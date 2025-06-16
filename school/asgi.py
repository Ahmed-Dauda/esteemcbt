"""
ASGI config for school project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school.settings')

# application = get_asgi_application()



# This file is used to configure the ASGI application for the Django project.
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school.settings")
django.setup()

from django.core.asgi import get_asgi_application
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.routing import Mount
from starlette.applications import Starlette
from fastapi_app.main import app as fastapi_app

application = Starlette(
    routes=[
        Mount("/fastapi", app=fastapi_app),  # FastAPI mounted here
        Mount("/", app=WSGIMiddleware(get_asgi_application())),
    ]
)
