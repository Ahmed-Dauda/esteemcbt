from django import forms
from django.forms import ModelForm
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
        model = Courses
        # include exam_type later after fixing quiz load order
        fields = ['title', 'session', 'term', 'schools']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Lazy import to avoid circular import problem
            from quiz.models import School  
            self.fields['schools'].queryset = School.objects.filter(id=user.school.id)


class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ('amount', 'email',)
