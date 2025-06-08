from django.core.management.base import BaseCommand
from sms.models import Courses
from quiz.models import CourseGrade, Course

class Command(BaseCommand):
    help = 'Deletes placeholder Courses not linked to any Course instance and unlinks them from CourseGrade.'

    def handle(self, *args, **kwargs):
        placeholder_courses = Courses.objects.filter(title__in=[None, '', 'Placeholder Title'])

        deleted_count = 0
        skipped_count = 0

        for courses_instance in placeholder_courses:
            # Check if it's used in any Course (quiz.models.Course)
            related_courses = Course.objects.filter(course_name=courses_instance)

            if related_courses.exists():
                self.stdout.write(f"SKIPPED: '{courses_instance.title}' (ID: {courses_instance.id}) is used in Course.")
                skipped_count += 1
                continue

            # Remove related Course instances from CourseGrade.subjects
            for course in Course.objects.filter(course_name=courses_instance):
                grades = CourseGrade.objects.filter(subjects=course)
                for grade in grades:
                    grade.subjects.remove(course)
                    self.stdout.write(f"Removed Course '{course}' from CourseGrade '{grade.name}'")

            # Now safe to delete the Courses entry
            courses_instance.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted placeholder Courses '{courses_instance.title}' (ID: {courses_instance.id})"))
            deleted_count += 1

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} placeholder subjects. Skipped {skipped_count}."))
