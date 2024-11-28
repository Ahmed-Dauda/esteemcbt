from django import forms
from .models import StudentConduct
from users.models import NewUser
# class StudentConductForm(forms.ModelForm):
#     class Meta:
#         model = StudentConduct
#         fields = ['student', 'school', 'session', 'term', 'student_class', 'category', 'remarks']

#     student = forms.ModelChoiceField(queryset=NewUser.objects.all(), widget=forms.Select(attrs={'class': 'select2'}))

from django.forms import CheckboxSelectMultiple

class StudentConductForm(forms.ModelForm):
    class Meta:
        model = StudentConduct
        fields = ['student', 'school', 'session', 'term', 'student_class', 'category', 'remarks']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Example: Limit students to the ones from the logged-in user's school
        if 'user' in kwargs:
            school = kwargs['user'].school
            self.fields['student'].queryset = NewUser.objects.filter(school=school)


from dal import autocomplete

class StudentConductForm(forms.ModelForm):
    class Meta:
        model = StudentConduct
        fields = ['student', 'school', 'session', 'term', 'student_class', 'category', 'remarks']

    student = forms.ModelChoiceField(
        queryset=NewUser.objects.all(),
        widget=autocomplete.ModelSelect2(url='student-autocomplete')  # Use the autocomplete widget
    )
