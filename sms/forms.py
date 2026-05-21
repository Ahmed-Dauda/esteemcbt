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



class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ('amount', 'email',)
