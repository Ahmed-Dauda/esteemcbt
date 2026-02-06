# clock.py
from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import call_command
import django
import os

# myapp/management/commands/cleanup_old_sessions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from quiz.models import StudentExamSession
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Delete StudentExamSession records older than 1 minute'

    def handle(self, *args, **kwargs):
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        deleted_count, _ = StudentExamSession.objects.filter(
            created__lt=one_minute_ago
        ).delete()
        
        logger.info(f'Cleanup ran at {timezone.now()}: Deleted {deleted_count} sessions')
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted_count} old sessions')
        )