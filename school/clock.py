# clock.py
from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import call_command
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school.settings')
django.setup()

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', minutes=1)
def cleanup_sessions():
    call_command('cleanup_old_sessions')

scheduler.start()