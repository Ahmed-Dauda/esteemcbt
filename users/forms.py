from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
from django import forms
from django.db import models 
from django.forms import ModelForm
from student.models import ReferrerMentor
from django.contrib.auth import get_user_model
# from allauth.account.forms import SignupForm
from .models import *
from users.models import NewUser

# models.py

from django.contrib.auth.forms import UserCreationForm
from teacher.models import Teacher
from quiz.models import Course, CourseGrade,School



country_choice = [
    ('select country here', 'select country here'),('Nigeria', 'Nigeria'), ('United State', 'United State'), ('Afghanistan', 'Afghanistan'),
    ('Albania', 'Albania'),('Algeria', 'Algeria'), ('Andorra', 'Andorra'), ('Angola', 'Angola'),
    ('Antigua and Barbuda', 'Antigua and Barbuda'),('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Australia', 'Australia'),
    ('Austria', 'Austria'),('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('	Bahrain', '	Bahrain'),
    ('Bahamas', 'Bahamas'),('Bahrain', 'Bahrain'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'),
    ('Belarus', 'Belarus'),('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'),
    ('Bhutan', 'Bhutan'),('Bolivia', 'Bolivia'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'),
    ('Brazil', 'Brazil'),('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'),
    ('Burundi', 'Burundi'),('Côte d"Ivoire', 'Côte d"Ivoire'), ('Cabo Verde', '	Cabo Verde'), ('Cambodia', 'Cambodia'),
    ('Cameroon', 'Cameroon'),('Canada', 'Canada'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'),
    ('Chile', 'Chile'),('China', 'China'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Congo ','Congo'),
    ('Costa Rica', 'Costa Rica'),('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Cyprus', 'Cyprus'),('Dominican Republic','Dominican Republic'),
    ('Czechia ', 'Czechia'),('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'),

]


from django import forms

from quiz.models import School

# class SchoolStudentForm(SignupForm):
#     first_name = forms.CharField(max_length=12, label='First Name 1')
#     last_name = forms.CharField(max_length=50, label='Last Name')
#     referral_code = forms.CharField(max_length=20, required=False, label='Referral Code')
#     phone_number = forms.CharField(max_length=225, widget=forms.HiddenInput(), required=False)
#     countries = forms.ChoiceField(choices=country_choice, label='Country')
#     school = forms.CharField(max_length=100, label='School')  # Add the school field
    
#     def save(self, request):
#         user = super(SchoolStudentForm, self).save(request)
#         user.phone_number = self.cleaned_data.get('phone_number', '')
#         user.first_name = self.cleaned_data['first_name 1']
#         user.last_name = self.cleaned_data['last_name']
#         user.countries = self.cleaned_data['countries']
#         user.referral_code = self.cleaned_data.get('referral_code', '')
#         user.school = self.cleaned_data.get('school', '')  # Handle the school field
        
#         user.save()
      
#         return user
    


class SimpleSignupForm(SignupForm):
    first_name = forms.CharField(max_length=12, label='First-name')
    last_name = forms.CharField(max_length=225, label='Last-name')
    # referral_code = forms.CharField(max_length=20, required=False, label='Referral Code')
    phone_number = forms.CharField(max_length=225, widget=forms.HiddenInput(), required=False)
    # phone_number = forms.CharField(max_length=225, label='Referral Code', widget=forms.TextInput(attrs={'placeholder': 'if available'}),required=False)
    countries = forms.ChoiceField(choices=country_choice, label='Country')
    
    def save(self, request):
        user = super(SimpleSignupForm, self).save(request)
        user.phone_number = self.cleaned_data.get('phone_number', '')  # Use get() to handle the case when phone_number is not provided.
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.countries = self.cleaned_data['countries']
        # user.referral_code  = self.cleaned_data['referral_code']
        # Check if the school field is empty
        if not user.school:
            # Assign the user to the "Codethinkers Academy" school
            # Get or create the School instance for "Codethinkers Academy"
            default_school, created = School.objects.get_or_create(school_name="Codethinkers Academy")
            user.school = default_school
            user.save()
        
        return user


from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone


from django import forms
from django.core.exceptions import ValidationError

from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils import timezone

class SchoolStudentSignupForm(SignupForm):
    first_name = forms.CharField(max_length=222, label='First-name')
    last_name = forms.CharField(max_length=225, label='Last-name')
    admission_no = forms.CharField(max_length=50, label='Admission Number')
    student_class = forms.ChoiceField(choices=[], label='Student Class')  # Initially empty
    countries = forms.ChoiceField(choices=country_choice, label='Country')
    school = forms.ModelChoiceField(queryset=School.objects.all(), label='School', required=True)

    # Anti-bot fields
    honeypot = forms.CharField(required=False,widget=forms.HiddenInput())
    js_honeypot = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SchoolStudentSignupForm, self).__init__(*args, **kwargs)

        if self.request and self.request.user.is_authenticated:
            user = NewUser.objects.get(id=self.request.user.id)
            user_school = user.school
            self.fields['school'].queryset = School.objects.filter(id=user_school.id)
            self.fields['student_class'].choices = [
                (cg.name, cg.name) for cg in CourseGrade.objects.filter(schools=user_school).only('name').distinct()
            ]

        # Show honeypot in debug mode
        if self.request and self.request.GET.get('debug') == '1':
            self.fields['honeypot'].widget = forms.TextInput(attrs={'placeholder': 'Leave this empty'})
            self.fields['js_honeypot'].widget = forms.TextInput(attrs={'placeholder': 'Should be "human"'})

    def clean(self):
        cleaned = super().clean()

        # 1. Honeypot field should be empty
        if cleaned.get('honeypot'):
            raise ValidationError("Something went wrong. Please try again.")

        # 2. JS honeypot should be 'human'
        if cleaned.get('js_honeypot') != 'human':
            raise ValidationError("Something went wrong. Please try again.")

        # 3. Check time elapsed since form render
        if self.request:
            ts = self.request.session.get('form_created_at')
            if ts:
                try:
                    elapsed = timezone.now() - datetime.fromisoformat(ts)
                    if elapsed < timedelta(seconds=3):
                        raise ValidationError("Form submitted too quickly. Try again.")
                except Exception:
                    pass  # Ignore if datetime fails

        return cleaned

    def save(self, request):
        user = super(SchoolStudentSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')  # Optional
        user.admission_no = self.cleaned_data['admission_no']
        user.student_class = self.cleaned_data['student_class']
        user.countries = self.cleaned_data['countries']
        user.school = self.cleaned_data['school']
        user.save()
        return user




class SchoolSignupForm(forms.ModelForm):
    class Meta:
        model = School
        fields = "__all__"

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')

        return logo

    def clean_principal_signature(self):
        principal_signature = self.cleaned_data.get('principal_signature')

        # Perform additional validation for the principal_signature field if needed

        return principal_signature




class ReferrerMentorForm(forms.ModelForm):
    class Meta:
        model = ReferrerMentor
        fields = ['name', 'phone_no']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude the 'referrer' field from the form
        if 'referrer' in self.fields:
            self.fields['referrer'].widget = forms.HiddenInput()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.referrer_code = self.cleaned_data.get('referrer_code', '')
        if commit:
            instance.save()
        return instance



