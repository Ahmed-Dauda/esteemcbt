from django import forms
from django.forms import ModelForm
from quiz.models import School
from users.models import NewUser
from student.models import Payment
from sms.models import Courses
from tinymce.widgets import TinyMCE
from .models import Session, Term, ExamType


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['name']

class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'order']

class ExamTypeForm(forms.ModelForm):
    class Meta:
        model = ExamType
        fields = ['name', 'description']

class CoursesForm(forms.ModelForm):
    class Meta:
        model = Courses  # Reference the 'Courses' model correctly
        fields = ['title', 'session', 'term', 'exam_type', 'schools']  # Define the fields to display in the form

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Retrieve the 'user' argument passed during form initialization
        super().__init__(*args, **kwargs)  # Call the parent constructor to set up the form

        if user:
            # Filter the 'schools' field to show only the school associated with the user
            self.fields['schools'].queryset = School.objects.filter(id=user.school.id)


class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ('amount', 'email',)
