# myapp/management/commands/cleanup_old_sessions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from quiz.models import StudentExamSession,Result

class Command(BaseCommand):
    help = 'Delete StudentExamSession records older than 2 hours'

    def handle(self, *args, **kwargs):
        two_hours_ago = timezone.now() - timedelta(hours=2)
        deleted_count, _ = StudentExamSession.objects.filter(
            created__lt=two_hours_ago
        ).delete()

        thirty_days_ago = timezone.now() - timedelta(days=30)
        deleted_results, _ = Result.objects.filter(
            created__lt=thirty_days_ago
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted_count} old sessions and {deleted_results} old results')
        )

# class Command(BaseCommand):
#     help = 'Delete StudentExamSession records older than 1 minute'

#     def handle(self, *args, **kwargs):
#         one_minute_ago = timezone.now() - timedelta(minutes=1)
#         deleted_count, _ = StudentExamSession.objects.filter(
#             created__lt=one_minute_ago
#         ).delete()
        
#         self.stdout.write(
#             self.style.SUCCESS(f'Deleted {deleted_count} old sessions')
#         )