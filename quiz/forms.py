
from django import forms
from .models import CourseGrade, Course
from users.models import NewUser
from .models import School
from django.contrib import admin
from django.db.models import Count
try:
    from sms.models import Courses
except Exception:
    Courses = None

class CourseGradeForm(forms.ModelForm):
    class Meta:
        model = CourseGrade
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply width to 'students' and 'subjects' fields using style attribute
        self.fields['students'].widget.attrs.update({'style': 'width: 70%; height: 200px;'})
        self.fields['subjects'].widget.attrs.update({'style': 'width: 70%; height: 200px;'})

        # Set querysets for students and subjects
        self.fields['students'].queryset = NewUser.objects.all()
        self.fields['subjects'].queryset = Course.objects.all()


class MoveGroupForm(forms.Form):
    from_group = forms.ModelChoiceField(queryset=CourseGrade.objects.none(), label='From Group')
    to_group = forms.ModelChoiceField(
        queryset=CourseGrade.objects.none(), 
        empty_label="Select target class (must be empty)", 
        label='To Group',
        required=True
    )

    def __init__(self, *args, **kwargs):
        user_school = kwargs.pop('user_school', None)
        super(MoveGroupForm, self).__init__(*args, **kwargs)

        if user_school:
            self.fields['from_group'].queryset = CourseGrade.objects.filter(schools=user_school).order_by('name')
            # Only allow empty classes as target
            self.fields['to_group'].queryset = CourseGrade.objects.filter(schools=user_school).filter(students__isnull=True).order_by('name')
            


