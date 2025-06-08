from django.core.management.base import BaseCommand
from sms.models import Courses
from quiz.models import Course

class Command(BaseCommand):
    help = 'Deletes placeholder Courses not linked to any Course instance.'

    def handle(self, *args, **kwargs):
        # Find all Courses with no title or 'Placeholder Title'
        placeholder_courses = Courses.objects.filter(title__in=[None, '', 'Placeholder Title'])

        deleted_count = 0

        for course in placeholder_courses:
            # Check if any Course references this Courses instance
            is_referenced = Course.objects.filter(course_name=course).exists()

            if not is_referenced:
                self.stdout.write(f"Deleting unused placeholder course: {course.title or 'No Title'} (ID: {course.id})")
                course.delete()
                deleted_count += 1
            else:
                self.stdout.write(f"Skipping: {course.title or 'No Title'} (ID: {course.id}) is still in use.")

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} unused placeholder Courses."))
