
from django.forms import ModelForm
from student.models import Payment
from django import forms
from .models import PDFDocument
from .models import ReferrerMentor
from users.models import NewUser

class StudentEditForm(forms.ModelForm):
    class Meta:
        model = NewUser
        fields = ['first_name', 'last_name', 'email', 'admission_no', 'student_class', 'gender', 'phone_number']


class ReferrerMentorUpdateForm(forms.ModelForm):
    class Meta:
        model = ReferrerMentor
        fields = ['account_number', 'bank', 'phone_no','name']


class PDFDocumentForm(forms.ModelForm):
    class Meta:
        model = PDFDocument
        fields = ['title', 'desc','price']




