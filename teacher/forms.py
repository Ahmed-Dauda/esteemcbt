
# from django.contrib.auth.models import User
from users.models import NewUser
from . import models
from django.contrib.auth.forms import UserCreationForm
from django import forms
# from .models import Teacher
from quiz import models as QMODEL

from django import forms
from .models import Teacher
from django.contrib.auth.forms import UserCreationForm
from .models import NewUser
from allauth.account.forms import SignupForm
from quiz.models import School, Course, CourseGrade, Question
from django.contrib.auth.forms import AuthenticationForm


# forms.py
class JSONForm(forms.Form):
    json_data = forms.CharField(widget=forms.Textarea)
   

class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label='Upload CSV')

class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        courses = kwargs.pop('courses', None)
        super().__init__(*args, **kwargs)
        if courses:
            self.fields['course'].queryset = courses

    class Meta:
        model = Question
        fields = "__all__"
        widgets = {
            'option1': forms.Textarea(attrs={'style': 'height: 60px;'}),
            'option2': forms.Textarea(attrs={'style': 'height: 60px;'}),
            'option3': forms.Textarea(attrs={'style': 'height: 60px;'}),
            'option4': forms.Textarea(attrs={'style': 'height: 60px;'}),
        }
        # fields = ['question', 'marks', 'course']

# class QuestionForm(forms.ModelForm):
#     class Meta:
#         model = Question
#         fields = ['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer']
#         # widgets = {
#         #     'course': forms.Select(attrs={'disabled': 'disabled'}),}
        


from django import forms
from .models import NewUser, Teacher, Course, School, CourseGrade


class TeacherSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=200, label='First Name')
    last_name = forms.CharField(max_length=200, label='Last Name')
    email = forms.EmailField(max_length=254, label='Email')
    username = forms.CharField(max_length=35, label='Username')
    school = forms.ModelChoiceField(queryset=School.objects.all(), label='School', required=False)
    subjects_taught = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), label='Subjects Taught', required=False)
    classes_taught = forms.ModelMultipleChoiceField(queryset=CourseGrade.objects.all(), label='Classes Taught', required=False)

    class Meta:
        model = NewUser
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def save_teacher(self, user):
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = user.email
        username = user.username
        school = self.cleaned_data.get('school', None)
        subjects_taught = self.cleaned_data.get('subjects_taught', [])
        classes_taught = self.cleaned_data.get('classes_taught', [])

        teacher = Teacher.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            school=school,
        )
        teacher.subjects_taught.add(*subjects_taught)
        teacher.classes_taught.add(*classes_taught)
        return teacher


    
# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     school = forms.ModelChoiceField(queryset=School.objects.all(), label='School', required=False)

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']

#     def __init__(self, *args, **kwargs):
#         subjects_taught = kwargs.pop('subjects_taught', None)
#         super().__init__(*args, **kwargs)
#         if subjects_taught:
#             self.fields['subjects_taught'].queryset = subjects_taught

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()
#         return user

#     def save_teacher(self, user):
#         first_name = self.cleaned_data['first_name']
#         last_name = self.cleaned_data['last_name']
#         email = user.email
#         username = user.username
#         school = self.cleaned_data.get('school', None)
#         subjects_taught = self.cleaned_data.get('subjects_taught', [])

#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             username=username,
#             school=school,
#         )
#         teacher.subjects_taught.add(*subjects_taught)
#         return teacher


# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     classes_taught = forms.ModelMultipleChoiceField(queryset=CourseGrade.objects.all(), label='Classes Taught', required=False)
#     subjects_taught = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), label='Subjects Taught', required=False)
#     school = forms.ModelChoiceField(queryset=School.objects.all(), label='School', required=False)

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()
#         return user

#     def save_teacher(self, user):
#         first_name = self.cleaned_data['first_name']
#         last_name = self.cleaned_data['last_name']
#         email = user.email
#         username = user.username
#         classes_taught = self.cleaned_data.get('classes_taught', [])
#         subjects_taught = self.cleaned_data.get('subjects_taught', [])
#         school = self.cleaned_data.get('school', None)

#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             username=username,
#             school=school,
#         )
#         teacher.classes_taught.add(*classes_taught)
#         teacher.subjects_taught.add(*subjects_taught)
#         return teacher
    
# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()
#         return user

#     def save_teacher(self, user):
#         first_name = self.cleaned_data['first_name']
#         last_name = self.cleaned_data['last_name']

#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=user.email,
#             username=user.username,
#         )
#         return teacher


class TeacherLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}))
    password = forms.CharField(label="Password", max_length=30, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))

# class TeacherSignupForm(SignupForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
#     password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#     def save(self, request):
#         user = super().save(request)
#         user.first_name = self.cleaned_data['first_name']
#         user.last_name = self.cleaned_data['last_name']
#         user.email = self.cleaned_data['email']
#         user.username = self.cleaned_data['username']
#         user.set_password(self.cleaned_data['password1'])
#         user.save()
#         return user

#     class Meta:
#         model = Teacher
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']



# class TeacherLoginForm(forms.Form):
#     email = forms.EmailField(max_length=254)
#     password = forms.CharField(widget=forms.PasswordInput)


# class TeacherUserForm(forms.ModelForm):
#     class Meta:
#         model= NewUser
#         fields=['username','password']
#         widgets = {
#         'password': forms.PasswordInput()
#         }

# class TeacherForm(forms.ModelForm):
#     class Meta:
#         model=models.Teacher
#         fields= "__all__"


# class TeacherRegistrationForm(UserCreationForm):
#     email = forms.EmailField(max_length=254, help_text='Required. Please enter a valid email address.')
#     username = forms.CharField(max_length=35, help_text='Optional.')
    
#     class Meta:
#         model = Teacher
#         fields = '__all__'

        # fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']




# class TeacherRegistrationForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, required=True)
#     last_name = forms.CharField(max_length=200, required=True)
#     classes_taught = forms.ModelMultipleChoiceField(queryset=CourseGrade.objects.all(), required=False)
#     subjects_taught = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), required=False)
#     school = forms.ModelChoiceField(queryset=School.objects.all(), required=False)

#     class Meta:
#         model = Teacher
#         fields = ['first_name', 'last_name', 'classes_taught', 'subjects_taught', 'school', 'password1', 'password2']


