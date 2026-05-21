from django import forms
from .models import StudentConduct
from users.models import NewUser
# class StudentConductForm(forms.ModelForm):
#     class Meta:
#         model = StudentConduct
#         fields = ['student', 'school', 'session', 'term', 'student_class', 'category', 'remarks']

#     student = forms.ModelChoiceField(queryset=NewUser.objects.all(), widget=forms.Select(attrs={'class': 'select2'}))

from django_select2.forms import Select2Widget

class StudentConductForm(forms.ModelForm):
    class Meta:
        model = StudentConduct
        fields = ['student', 'school', 'session', 'term', 'student_class', 'category', 'remarks']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the user from kwargs
        super().__init__(*args, **kwargs)

        # Store the user in the form instance so it can be accessed later
        self.user = user

        # If a user (teacher) is provided, filter the student queryset based on their school
        if user:
            school = user.school  # Get the school of the logged-in teacher
            # Filter students by the school of the teacher
            self.fields['student'].queryset = NewUser.objects.filter(school=school)

        # Add class to student field for Select2 (optional styling)
        self.fields['student'].widget.attrs['class'] = 'student-select'

    def save(self, commit=True):
        # Create or get the instance
        instance = super().save(commit=False)
        
        # Automatically assign the logged-in teacher to the teacher field
        if self.user:  # Ensure user is passed and exists
            instance.teacher = self.user  # Automatically set the teacher field to the logged-in teacher
        
        if commit:
            instance.save()
        return instance
    

# class StudentConductForm(forms.ModelForm):
#     class Meta:
#         model = StudentConduct
#         fields = ['student', 'school', 'session', 'term', 'student_class', 'category', 'remarks']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#         if user:
#             school = user.school
#             self.fields['student'].queryset = NewUser.objects.filter(school=school)

#         # Add class to student field for Select2
#         self.fields['student'].widget.attrs['class'] = 'student-select'  # Add this line
        

