from django.core.management.base import BaseCommand
from sms.models import Courses  # or Course if that's the correct model name
from django.db import transaction

class Command(BaseCommand):
    help = 'Deletes all Courses titled "Placeholder Title" safely.'

    def handle(self, *args, **kwargs):
        placeholder_courses = Courses.objects.filter(title="Placeholder Title")
        total = placeholder_courses.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No Placeholder Title courses found.'))
            return

        with transaction.atomic():
            for course in placeholder_courses:
                course.course_grade.clear()  # Clear M2M references
                course.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {total} Placeholder Title course(s).'))
