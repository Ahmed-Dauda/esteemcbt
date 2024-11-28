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

    def get_conduct_count(self):
        """Get the count of conduct records for this student in the same session and term."""
        return StudentConduct.objects.filter(
            student=self.student, session=self.session, term=self.term
        ).count()

    def __str__(self):
        return f"{self.student} - {self.category} - {self.date}"

    class Meta:
        ordering = ['-date']

