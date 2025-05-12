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
from users.models import NewUser, Profile
from allauth.account.forms import SignupForm
from quiz.models import School, Course, CourseGrade, Question
from django.contrib.auth.forms import AuthenticationForm
from sms.models import Courses
from quiz.models import Result

class ResultEditForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['marks']  # Add any other fields you want to allow editing
        widgets = {
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Select a file to upload")


class DocumentUploadForm(forms.Form):
    file = forms.FileField()


# teacher edit ai questions num and learning objives
class TeacherUpdateForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['ai_question_num', 'learning_objectives']
        widgets = {
            'ai_question_num': forms.NumberInput(attrs={'min': 1, 'max': 20}),
            'learning_objectives': forms.Textarea(attrs={'rows': 3}),
        }


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'marks']

    def __init__(self, *args, **kwargs):
        user_school = kwargs.pop('user_school', None)
        super(ResultForm, self).__init__(*args, **kwargs)
        
        if user_school:
            self.fields['student'].queryset = Profile.objects.filter(
            result__exam__course_name__schools__school_name=user_school
        ).distinct()

# class ResultForm(forms.ModelForm):
#     class Meta:
#         model = Result
#         fields = ['student', 'exam', 'marks']
#         widgets = {
#             'student': forms.Select(attrs={'class': 'form-control'}),
#             'exam': forms.Select(attrs={'class': 'form-control'}),
#             'marks': forms.NumberInput(attrs={'class': 'form-control'}),
#         }

#     def __init__(self, *args, **kwargs):
#         user_school = kwargs.pop('user_school', None)
#         super(ResultForm, self).__init__(*args, **kwargs)

#         if user_school:
#             # Filter students to only those in courses associated with the user's school
#             # self.fields['student'].queryset = Profile.objects.filter(user__school__school_name=user_school)
#             self.fields['student'].queryset = Profile.objects.filter(
#             result__exam__course_name__schools__school_name=user_school
#         ).distinct()
#             # Filter exams to only those associated with courses in the user's school
#             self.fields['exam'].queryset = Course.objects.filter(schools=user_school)


class SubjectsCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'room_name',
            'schools',
            'course_name',
            'question_number',
            'course_pay',
            'total_marks',
            'session',
            'term',
            'exam_type',
            'num_attemps',    
            'show_questions',
            'duration_minutes'
        ]
        # fields = [ 
        #     'schools', 'show_questions', 'question_number',
        #     'total_marks', 'num_attemps', 'duration_minutes'
        # ]
    
    def __init__(self, *args, **kwargs):
        user_school = kwargs.pop('user_school', None)
        initial = kwargs.pop('initial', None)
        super(SubjectsCreateForm, self).__init__(*args, **kwargs)
        
        if user_school:
            # Filter the schools field to only show the user's school
            self.fields['schools'].queryset = School.objects.filter(school_name=user_school.school_name)
            # Filter the course_name field to only show courses associated with the user's school
            # self.fields['course_name'].queryset = Courses.objects.filter(schools=user_school)
        
        # Make question_number and total_marks fields read-only by disabling them
        self.fields['question_number'].widget.attrs['readonly'] = True
        self.fields['total_marks'].widget.attrs['readonly'] = True



class CourseSelectionForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'schools', 'show_questions', 'question_number',
            'total_marks', 'num_attemps', 'duration_minutes'
        ]
    
    def __init__(self, *args, **kwargs):
        user_school = kwargs.pop('user_school', None)
        initial = kwargs.pop('initial', None)
        super(CourseSelectionForm, self).__init__(*args, **kwargs)
        
        if user_school:
            # Filter the schools field to only show the user's school
            self.fields['schools'].queryset = School.objects.filter(school_name=user_school.school_name)
            # Filter the course_name field to only show courses associated with the user's school
            # self.fields['course_name'].queryset = Courses.objects.filter(schools=user_school)
        
        # Make question_number and total_marks fields read-only by disabling them
        self.fields['question_number'].widget.attrs['readonly'] = True
        self.fields['total_marks'].widget.attrs['readonly'] = True



from django import forms

class CourseGradeForm(forms.ModelForm):

    students = forms.ModelMultipleChoiceField(
        queryset=NewUser.objects.none(),  # Initialize with an empty queryset
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),  # Initialize with an empty queryset
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = CourseGrade
        fields = ['students', 'subjects']

    def __init__(self, *args, **kwargs):
        user_school = kwargs.pop('user_school')
        super(CourseGradeForm, self).__init__(*args, **kwargs)
        self.fields['students'].queryset = NewUser.objects.filter(school=user_school).select_related('school')
        self.fields['subjects'].queryset = Course.objects.filter(schools=user_school).prefetch_related('schools')
   


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
        # Set the course and marks fields as required
        self.fields['course'].required = True
        self.fields['marks'].required = True  # Making marks required

    class Meta:
        model = Question
        fields = ['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer']
        widgets = {
            'option1': forms.Textarea(attrs={'style': 'height: 60px;'}),
            'option2': forms.Textarea(attrs={'style': 'height: 60px;'}),
            'option3': forms.Textarea(attrs={'style': 'height: 60px;'}),
            'option4': forms.Textarea(attrs={'style': 'height: 60px;'}),
        }
   

from django.core.exceptions import ValidationError       
from django import forms
from .models import NewUser, Teacher, Course, School, CourseGrade

from django import forms
from django.contrib.auth.forms import UserCreationForm
import logging

logger = logging.getLogger(__name__)


class TeacherSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=200, label='First Name')
    last_name = forms.CharField(max_length=200, label='Last Name')
    email = forms.EmailField(max_length=254, label='Email')
    username = forms.CharField(max_length=35, label='Username')
    school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)
    subjects_taught = forms.ModelMultipleChoiceField(
        queryset=Courses.objects.all().order_by('title'),  # Sort alphabetically by title
        label='Subjects Taught',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    # subjects_taught = forms.ModelMultipleChoiceField(
    #     queryset=Courses.objects.all(),  # Ensure courses are properly loaded
    #     label='Subjects Taught',
    #     required=False,
    #     widget=forms.CheckboxSelectMultiple
    # )

    classes_taught = forms.ModelMultipleChoiceField(
        queryset=CourseGrade.objects.all(),  # Ensure classes are properly loaded
        label='Classes Taught',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = NewUser
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)  # ✅ Pop 'user' first
    #     super(TeacherSignupForm, self).__init__(*args, **kwargs)  # THEN call super

    #     if user and user.school:
    #         self.fields['school'].queryset = School.objects.filter(id=user.school.id)
    #         self.fields['school'].initial = user.school
    #         self.fields['subjects_taught'].queryset = Course.objects.filter(
    #             schools=user.school
    #         ).order_by('course_name__title')  # or 'title'
    #         self.fields['subjects_taught'].label_from_instance = lambda obj: str(obj)

    #         self.fields['classes_taught'].queryset = CourseGrade.objects.filter(
    #             schools=user.school
    #         ).distinct()

    #     self.fields['school'].widget.attrs['readonly'] = True
    #     self.fields['school'].disabled = True


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TeacherSignupForm, self).__init__(*args, **kwargs)

        # Populate dropdowns with data related to the user's school
        if user and user.school:
            # Show only the user's school in the school field
            self.fields['school'].queryset = School.objects.filter(id=user.school.id)
            self.fields['school'].initial = user.school  # Set the initial value to the user's school
            # Populate subjects and classes based on the user's school
            self.fields['subjects_taught'].queryset = Course.objects.filter(schools=user.school).order_by('course_name__title')
            self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

        # Make the 'school' field read-only (disabled in the form)
        self.fields['school'].widget.attrs['readonly'] = True
        self.fields['school'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Teacher.objects.filter(email=email).exists():
            raise ValidationError("A teacher with this email already exists.")
        return email

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
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)

#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Courses.objects.all(),  # Ensure courses are properly loaded
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.all(),  # Ensure classes are properly loaded
#         label='Classes Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super(TeacherSignupForm, self).__init__(*args, **kwargs)


#         # Populate dropdowns with data related to the user's school
#         if user and user.school:
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Course.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         self.fields['school'].initial = user.school if user else None

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if Teacher.objects.filter(email=email).exists():
#             raise ValidationError("A teacher with this email already exists.")
#         return email

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
#         classes_taught = self.cleaned_data.get('classes_taught', [])

#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             username=username,
#             school=school,
#         )
#         teacher.subjects_taught.add(*subjects_taught)
#         teacher.classes_taught.add(*classes_taught)
#         return teacher

  

class TeacherEditForm(forms.ModelForm):
    subjects_taught = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        label='Subjects Taught',
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    classes_taught = forms.ModelMultipleChoiceField(
        queryset=CourseGrade.objects.none(),
        label='Classes Taught',
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'school', 'subjects_taught', 'classes_taught', 'form_teacher_role', 'learning_objectives', 'ai_question_num']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TeacherEditForm, self).__init__(*args, **kwargs)

        if user and user.school:
            self.fields['school'].queryset = School.objects.filter(name=user.school.name)
            self.fields['subjects_taught'].queryset = Course.objects.filter(schools=user.school)
            self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

        self.fields['school'].initial = user.school if user else None

        # Pre-fill the form fields with the teacher's current subjects and classes
        if self.instance.pk:

            self.fields['subjects_taught'].initial = self.instance.subjects_taught.all()
            self.fields['classes_taught'].initial = self.instance.classes_taught.all()
       


class TeacherLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}))
    password = forms.CharField(label="Password", max_length=30, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))


