import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school.settings')

app = Celery("school")
app.conf.broker_url = "redis://localhost:6379/0"

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# use Redis from Heroku
app.conf.broker_url = os.environ.get('REDIS_URL')