from django.db import models
from quiz.models import School, NewUser  # Update these based on your project structure
from quiz.models import CourseGrade
from sms.models import  Session, Term  # Assuming `CourseGrade` is the model for student classes

class ConductCategory(models.Model):
    """Categories of student conduct (e.g., Punctuality, Behavior, etc.)."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

from django.db import models
from django.db.models import Count

class StudentConduct(models.Model):
    """Daily conduct records for students."""
    teacher = models.ForeignKey(
        NewUser, on_delete=models.CASCADE, related_name='conducted_records', blank=True, null=True
    )  # Teacher who recorded the conduct
    student = models.ForeignKey(NewUser, on_delete=models.CASCADE, related_name='conducts')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='conducts')
    student_class = models.ForeignKey(
        CourseGrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducts'
    )
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducts')
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducts')
    date = models.DateField(auto_now_add=True, blank=True, null=True) 
    category = models.ForeignKey(ConductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)  # Optional: score to quantify conduct

    def save(self, *args, **kwargs):
        """Override save to update the score with the count of conduct records."""
        # Only update score if the student, session, or term is changed
        if not self.id or self.student or self.session or self.term:
            self.score = self.get_conduct_count()  # Ensure score is updated
        super().save(*args, **kwargs)

    def get_conduct_count(self):
        """Get the count of conduct records for this student in the same session and term."""
        return StudentConduct.objects.filter(
            student=self.student, session=self.session, term=self.term
        ).count()

    def __str__(self):
        return f"{self.student} - {self.category} - {self.date}"

    class Meta:
        ordering = ['-date']

    @staticmethod
    def get_conducts_for_teacher(teacher_email):
        """Helper method to fetch conducts for a specific teacher with efficient queries."""
        return StudentConduct.objects.filter(teacher__email=teacher_email).select_related(
            'teacher', 'student', 'school', 'student_class', 'session', 'term', 'category'
        ).only('teacher__email', 'student__first_name', 'student__last_name', 'student__email', 'category__name')

    @staticmethod
    def get_conducts_for_school(school_id):
        """Helper method to fetch conducts for a specific school with efficient queries."""
        return StudentConduct.objects.filter(school_id=school_id).select_related(
            'teacher', 'student', 'school', 'student_class', 'session', 'term', 'category'
        ).only('teacher__email', 'student__first_name', 'student__last_name', 'student__email', 'category__name')


# class StudentConduct(models.Model):
#     """Daily conduct records for students."""
#     teacher = models.ForeignKey(
#         NewUser, on_delete=models.CASCADE, related_name='conducted_records', blank=True, null=True
#     )  # Teacher who recorded the conduct
#     student = models.ForeignKey(NewUser, on_delete=models.CASCADE, related_name='conducts')
#     school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='conducts')
#     student_class = models.ForeignKey(
#         CourseGrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducts'
#     )
#     session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducts')
#     term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducts')
#     date = models.DateField(auto_now_add=True, blank=True, null=True) 
#     category = models.ForeignKey(ConductCategory, on_delete=models.SET_NULL, null=True, blank=True)
#     remarks = models.TextField(blank=True, null=True)
#     score = models.IntegerField(default=0)  # Optional: score to quantify conduct

#     def save(self, *args, **kwargs):
#         # Assign the score based on the count of conduct records for the same student, session, and term
#         self.score = self.get_conduct_count()
#         super().save(*args, **kwargs)

#     def get_conduct_count(self):
#         """Get the count of conduct records for this student in the same session and term."""
#         return StudentConduct.objects.filter(
#             student=self.student, session=self.session, term=self.term
#         ).count()

#     def __str__(self):
#         return f"{self.student} - {self.category} - {self.date}"

#     class Meta:
#         ordering = ['-date']

