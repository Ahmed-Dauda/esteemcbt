from django.core.management.base import BaseCommand
from sms.models import Courses
from quiz.models import CourseGrade, Course

class Command(BaseCommand):
    help = 'Deletes placeholder Courses not linked to any Course instance and unlinks them from CourseGrade.'

    def handle(self, *args, **kwargs):
        placeholder_courses = Courses.objects.filter(title__in=[None, '', 'Placeholder Title'])

        deleted_count = 0
        skipped_count = 0

        for course in placeholder_courses:
            # Check if it's referenced in Course (quiz.models.Course)
            in_use = Course.objects.filter(course_name=course).exists()

            if in_use:
                self.stdout.write(f"SKIPPED: '{course.title}' (ID: {course.id}) is still used in quiz.models.Course.")
                skipped_count += 1
                continue

            # Remove from any CourseGrade M2M relation
            course_grades = CourseGrade.objects.filter(subjects=course)
            if course_grades.exists():
                for cg in course_grades:
                    cg.subjects.remove(course)
                    self.stdout.write(f"Removed link to CourseGrade: {cg.name} (ID: {cg.id})")

            # Now delete the course
            course.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted: '{course.title}' (ID: {course.id})"))
            deleted_count += 1

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} placeholder courses. Skipped {skipped_count}."))
