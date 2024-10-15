from django.db import models
from quiz.models import Course,CourseGrade, School
from users.models import NewUser

# from django.contrib.auth.models import User

# class Teacher(models.Model):
#     user=models.OneToOneField(NewUser,on_delete=models.CASCADE, blank=True, null = True)
#     salary=models.PositiveIntegerField(null=True)
#     # @property
#     # def get_name(self):
#     #     return self.user.first_name+" "+self.user.last_name
#     # @property
#     # def get_instance(self):
#     #     return self
#     def __str__(self):
#         return f'{self.salary}'

from django.db import models

class SampleCodes(models.Model):
    code = models.TextField()

    def __str__(self):
        return f"{self.code}"

from django.core.exceptions import ValidationError
from sms.models import Courses

from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from quiz.models import Courses  # Make sure to import your Courses model
from django.utils.translation import gettext_lazy as _

     
class Teacher(models.Model):

    # Choices for the form_teacher field (if you want specific roles)
    FORM_TEACHER_ROLES = [
        
        ('form_teacher', 'form_teacher'),
        ('not_form_teacher', 'Not Form Teacher'),
    ]

    user = models.OneToOneField(NewUser, on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True, blank=True)
    username = models.CharField(max_length=35, blank=True)
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    classes_taught = models.ManyToManyField(CourseGrade, related_name='teachers', blank=True,null=True)
    subjects_taught = models.ManyToManyField(Course, related_name='teachers', blank=True,null=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='teachers', blank=True, null=True)
    learning_objectives = models.CharField(max_length=200, blank=True, default='Input your learning objectives')
    ai_question_num = models.PositiveIntegerField(default=10, blank=True, null=True)
    id = models.AutoField(primary_key=True)

    # Updated fields
    form_teacher_remark = models.CharField(max_length=300, blank=True)
    form_teacher_role = models.CharField(
        max_length=50,
        choices=FORM_TEACHER_ROLES,
        default='not_form_teacher'
    )  # Role of the form teacher


    def clean(self):
        super().clean()
        if self.ai_question_num is not None and self.ai_question_num > 20:
            raise ValidationError('ai_question_num cannot exceed 20.')
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
