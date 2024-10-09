# from tkinter import Widget
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
from django import forms
from django.db import models 
from django.forms import ModelForm
from django import forms

from users.models import NewUser, BaseUserManager
from student.models import Payment
from tinymce.widgets import TinyMCE

# forms.py

from .models import Courses
from quiz.models import School

class CoursesForm(forms.ModelForm):
    class Meta:
        model = Courses
        fields = ['title', 'session', 'term', 'exam_type', 'schools']  # Include 'schools'

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user instance, default to None
        super().__init__(*args, **kwargs)
        if user:
            self.fields['schools'].queryset = School.objects.filter(id=user.school.id)  # Ensure queryset contains only the user's school
           

class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ('amount', 'email',)

     
       