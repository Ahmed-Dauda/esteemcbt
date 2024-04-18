
from django import forms
from .models import CourseGrade

from .models import School

# class GroupForm(forms.ModelForm):
#     class Meta:
#         model = Group
#         fields = ['name']

# class PromoteStudentsForm(forms.Form):
#     students = forms.ModelMultipleChoiceField(queryset=Student.objects.all(), widget=forms.CheckboxSelectMultiple)
#     destination_group = forms.ModelChoiceField(queryset=Group.objects.all())


class MoveGroupForm(forms.Form):
    from_group = forms.ModelChoiceField(queryset=CourseGrade.objects.all(), label='From Group')
    to_group = forms.ModelChoiceField(queryset=CourseGrade.objects.all(), empty_label="Move group", label='To Group', required=False)
    
# class MoveGroupForm(forms.Form):
#     from_group = forms.ModelChoiceField(queryset=Group.objects.all(), label='From Group')
#     to_group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label="Move group", label='To Group', required=False)


# class StudentForm(forms.ModelForm):
#     class Meta:
#         model = Student
#         fields = ['name', 'email', 'group', 'school']

#     def __init__(self, *args, **kwargs):
#         super(StudentForm, self).__init__(*args, **kwargs)
#         self.fields['school'].queryset = School.objects.all()


# class StudentRegistrationForm(forms.ModelForm):
#     class Meta:
#         model = Student
#         fields = ['name', 'admission_no', 'date_of_birth', 'address', 'school']

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Add a dropdown list for the 'school' field
#         self.fields['school'].queryset = School.objects.all()
#         self.fields['school'].empty_label = 'Select a school'

#     def save(self, commit=True):
#         student = super().save(commit=False)
#         # You can perform any additional actions before saving, if needed
#         if commit:
#             student.save()
#         return student
