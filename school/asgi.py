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
# school/asgi.py
import os
import django
from fastapi import FastAPI
from fastapi_app.main import app as fastapi_app
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school.settings")
django.setup()

# Django ASGI app
django_asgi_app = get_asgi_application()

# Create FastAPI parent app
main_app = FastAPI()

# Mount Django at root and FastAPI under /api
main_app.mount("/", django_asgi_app)
main_app.mount("/api", fastapi_app)
