# projectname/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# from celery.schedules import crontab

# CELERY_BEAT_SCHEDULE = {
#     'cleanup_old_exam_sessions': {
#         'task': 'quiz.tasks.cleanup_old_exam_sessions',  # adjust path
#         'schedule': crontab(minute='*/1'),  # every 30 minutes
#     },
# }


from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school.settings")

app = Celery("school")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
