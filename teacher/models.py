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


class Teacher(models.Model):
    user = models.OneToOneField(NewUser, on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True, blank=True)
    username = models.CharField(max_length=35, blank=True)
    first_name = models.CharField(max_length=200, blank = True)
    last_name = models.CharField(max_length=200,blank = True)
    classes_taught = models.ManyToManyField(CourseGrade, related_name='teachers',blank = True)
    subjects_taught = models.ManyToManyField(Course, related_name='teachers',blank = True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='teachers', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
