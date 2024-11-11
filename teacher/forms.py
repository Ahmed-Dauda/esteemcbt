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


# class CourseSelectionForm(forms.ModelForm):
#     class Meta:
#         model = Course
#         fields = [
#             'schools','show_questions','question_number',
#             'total_marks',
#             'num_attemps', 'duration_minutes'
#             # ,'course_name'
#         ]
    
#     def __init__(self, *args, **kwargs):
#         user_school = kwargs.pop('user_school', None)
#         initial = kwargs.pop('initial', None)
#         super(CourseSelectionForm, self).__init__(*args, **kwargs)
#         if user_school:
#             # Filter the schools field to only show the user's school
#             self.fields['schools'].queryset = School.objects.filter(school_name=user_school.school_name)
#             # Filter the course_name field to only show courses associated with the user's school
#             # self.fields['course_name'].queryset = Courses.objects.filter(schools=user_school)
#             # self.fields['course_name'].queryset = Courses.objects.filter(schools=user_school)
 
 
# class CourseSelectionForm(forms.ModelForm):
#     class Meta:
#         model = Course
#         # fields = [
#         #     'schools', 'course_name'
#         # ]
#         fields = [
#             'room_name', 'schools', 'course_name',
#             'question_number', 'total_marks',
#             'num_attemps', 'show_questions', 'duration_minutes',
#         ]

#     def __init__(self, *args, **kwargs):
#         user_school = kwargs.pop('user_school', None)
#         initial = kwargs.pop('initial', None)
#         super(CourseSelectionForm, self).__init__(*args, **kwargs)
#         if user_school:
#             # Filter the schools field to only show the user's school
#             self.fields['schools'].queryset = School.objects.filter(school_name=user_school.school_name)
#             # Filter the course_name field to only show courses associated with the user's school
#             self.fields['course_name'].queryset = Courses.objects.filter(schools=user_school)

from django import forms

class CourseGradeForm(forms.ModelForm):

    students = forms.ModelMultipleChoiceField(
        queryset=NewUser.objects.none(),  # Initialize with an empty queryset
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Courses.objects.none(),  # Initialize with an empty queryset
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
        self.fields['subjects'].queryset = Courses.objects.filter(schools=user_school).prefetch_related('schools')
        # self.fields['students'].queryset = NewUser.objects.filter(school=user_school)
        # self.fields['subjects'].queryset = Courses.objects.filter(schools=user_school)
  


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
   
# class QuestionForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         courses = kwargs.pop('courses', None)
#         super().__init__(*args, **kwargs)
#         if courses:
#             self.fields['course'].queryset = courses

#     class Meta:
#         model = Question
#         fields = ['course', 'marks','question', 'img_quiz','option1', 'option2', 'option3', 'option4', 'answer']
#         # fields = "__all__"
#         widgets = {
#             'option1': forms.Textarea(attrs={'style': 'height: 60px;'}),
#             'option2': forms.Textarea(attrs={'style': 'height: 60px;'}),
#             'option3': forms.Textarea(attrs={'style': 'height: 60px;'}),
#             'option4': forms.Textarea(attrs={'style': 'height: 60px;'}),
#         }

from django.core.exceptions import ValidationError       
from django import forms
from .models import NewUser, Teacher, Course, School, CourseGrade

from django import forms
from django.contrib.auth.forms import UserCreationForm

# class TeacherSignupFormEdit(forms.ModelForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)
    
#     # Use checkboxes for subjects taught and classes taught
#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Courses.objects.none(),
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.none(),
#         label='Classes Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'school', 'subjects_taught', 'classes_taught']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super(TeacherSignupForm, self).__init__(*args, **kwargs)
        
#         # Filter subjects and classes by the user's school if available
#         if user and user.school:
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Courses.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         # Pre-select the school based on the user
#         self.fields['school'].initial = user.school if user else None

#     def save(self, commit=True):
#         # Only save the teacher details, no username or password involved
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()
#         return user

#     def save_teacher(self, user):
#         # Create or update the teacher instance with the form data
#         first_name = self.cleaned_data['first_name']
#         last_name = self.cleaned_data['last_name']
#         email = user.email
#         school = self.cleaned_data.get('school', None)

#         # Get subjects and classes taught
#         subjects_taught = self.cleaned_data.get('subjects_taught', [])
#         classes_taught = self.cleaned_data.get('classes_taught', [])

#         # Create or update the teacher instance
#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             school=school,
#         )

#         # Set the Many-to-Many fields
#         teacher.subjects_taught.set(subjects_taught.values_list('id', flat=True))
#         teacher.classes_taught.set(classes_taught.values_list('id', flat=True))

#         return teacher

import logging

logger = logging.getLogger(__name__)

class TeacherSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=200, label='First Name')
    last_name = forms.CharField(max_length=200, label='Last Name')
    email = forms.EmailField(max_length=254, label='Email')
    username = forms.CharField(max_length=35, label='Username')
    school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)

    subjects_taught = forms.ModelMultipleChoiceField(
        queryset=Courses.objects.all(),  # Ensure courses are properly loaded
        label='Subjects Taught',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    classes_taught = forms.ModelMultipleChoiceField(
        queryset=CourseGrade.objects.all(),  # Ensure classes are properly loaded
        label='Classes Taught',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = NewUser
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TeacherSignupForm, self).__init__(*args, **kwargs)

        # Populate dropdowns with data related to the user's school
        if user and user.school:
            self.fields['school'].queryset = School.objects.filter(name=user.school.name)
            self.fields['subjects_taught'].queryset = Course.objects.filter(schools=user.school)
            self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

        self.fields['school'].initial = user.school if user else None

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




    # def save_teacher(self, user):
    #     first_name = self.cleaned_data['first_name']
    #     last_name = self.cleaned_data['last_name']
    #     email = user.email
    #     username = user.username
    #     school = self.cleaned_data.get('school', None)

    #     # Create or update the Teacher object
    #     teacher, created = Teacher.objects.update_or_create(
    #         user=user,
    #         defaults={
    #             'first_name': first_name,
    #             'last_name': last_name,
    #             'email': email,
    #             'username': username,
    #             'school': school,
    #         }
    #     )

    #     # Save the teacher object to ensure it has an ID before assigning many-to-many fields
    #     teacher.save()

    #     # Ensure that all subjects being assigned to subjects_taught are present in the Courses table
    #     subjects = self.cleaned_data.get('subjects_taught', [])
    #     valid_subjects = []

    #     for subject in subjects:
    #         # Try to filter by course_name and other fields to ensure uniqueness
    #         course_qs = Course.objects.filter(
    #             course_name=subject,  # Assuming 'subject' is an instance of the 'Courses' model
    #             session=subject.session,
    #             term=subject.term
    #         )

    #         if course_qs.exists():
    #             # If multiple courses are returned, you can choose the first one or handle this differently
    #             course = course_qs.first()  # Pick the first course if there are multiple
    #         else:
    #             # If no course exists, create a new one
    #             course = Course.objects.create(
    #                 course_name=subject,
    #                 room_name=f"Auto-created Room {subject.id}",
    #                 question_number=0,  # Set default values as necessary
    #                 session=subject.session,
    #                 term=subject.term,
    #             )

    #         valid_subjects.append(course.id)  # Pass the course ID, not the object itself

    #     # Assign valid subjects to the teacher (many-to-many relationship)
    #     teacher.subjects_taught.set(valid_subjects)

    #     # Handle classes_taught (many-to-many assignment)
    #     classes = self.cleaned_data.get('classes_taught', [])
    #     teacher.classes_taught.set(classes)

    #     return teacher

    # def save_teacher(self, user):
    #     first_name = self.cleaned_data['first_name']
    #     last_name = self.cleaned_data['last_name']
    #     email = user.email
    #     username = user.username
    #     school = self.cleaned_data.get('school', None)

    #     # Create or update the Teacher object
    #     teacher, created = Teacher.objects.update_or_create(
    #         user=user,
    #         defaults={
    #             'first_name': first_name,
    #             'last_name': last_name,
    #             'email': email,
    #             'username': username,
    #             'school': school,
    #         }
    #     )

    #     # Save the teacher object to ensure it has an ID before assigning many-to-many fields
    #     teacher.save()

    #     # Ensure that all subjects being assigned to subjects_taught are present in the Courses table
    #     subjects = self.cleaned_data.get('subjects_taught', [])
    #     valid_subjects = []

    #     for subject in subjects:
    #         # Check if the course exists by id in the Course model
    #         course, created = Course.objects.get_or_create(
    #             course_name=subject,  # Assuming 'subject' is an instance of the 'Courses' model
    #             defaults={
    #                 'room_name': f"Auto-created Room {subject.id}",
    #                 'question_number': 0,  # Set default values as necessary
    #                 # Add other fields as needed
    #             }
    #         )
    #         valid_subjects.append(course)

    #     # Assign valid subjects to the teacher (many-to-many relationship)
    #     teacher.subjects_taught.set(valid_subjects)

    #     # Handle classes_taught (many-to-many assignment)
    #     classes = self.cleaned_data.get('classes_taught', [])
    #     teacher.classes_taught.set(classes)

    #     return teacher


    

# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)

#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Courses.objects.none(),
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.none(),
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
#             self.fields['subjects_taught'].queryset = Courses.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         self.fields['school'].initial = user.school if user else None

#         # If editing, initialize subjects and classes taught
#         if self.instance.pk:
#             self.fields['subjects_taught'].initial = self.instance.subjects_taught.all()
#             self.fields['classes_taught'].initial = self.instance.classes_taught.all()

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if NewUser.objects.filter(username=username).exists():
#             raise ValidationError("A user with this Username already exists.")
#         return username

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if NewUser.objects.filter(email=email).exists():
#             raise ValidationError("A user with this email already exists.")
#         return email

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()  # Save user first
#             self.save_teacher(user)  # Save the teacher details
#         return user

#     def save_teacher(self, user):
#         first_name = self.cleaned_data['first_name']
#         last_name = self.cleaned_data['last_name']
#         email = user.email
#         username = user.username
#         school = self.cleaned_data.get('school', None)

#         # Create the Teacher object without setting the many-to-many fields yet
#         teacher, created = Teacher.objects.update_or_create(
#             email=email,
#             defaults={
#                 'user': user,
#                 'first_name': first_name,
#                 'last_name': last_name,
#                 'username': username,
#                 'school': school,
#             }
#         )

#         # Save the teacher object to ensure it has an ID
#         teacher.save()

#         # Handle subjects_taught and dynamically create missing courses
#         valid_subjects = []
#         for subject in self.cleaned_data.get('subjects_taught', []):
#             # Ensure the course exists before assigning it to the teacher
#             course, created = Courses.objects.get_or_create(
#                 id=subject.id,
#                 defaults={'title': f"Auto-created Course {subject.id}"}  # Adjust as necessary
#             )
#             valid_subjects.append(course)

#         # Assign the valid subjects to the teacher (many-to-many)
#         teacher.subjects_taught.set(valid_subjects)

#         # Handle classes_taught (many-to-many assignment)
#         teacher.classes_taught.set(self.cleaned_data.get('classes_taught', []))

#         return teacher

    
# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)

#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Courses.objects.none(),
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.none(),
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
#             self.fields['subjects_taught'].queryset = Courses.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         self.fields['school'].initial = user.school if user else None

#         # If editing, initialize subjects and classes taught
#         if self.instance.pk:
#             self.fields['subjects_taught'].initial = self.instance.subjects_taught.all()
#             self.fields['classes_taught'].initial = self.instance.classes_taught.all()

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if NewUser.objects.filter(username=username).exists():
#             raise ValidationError("A user with this Username already exists.")
#         return username

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if NewUser.objects.filter(email=email).exists():
#             raise ValidationError("A user with this email already exists.")
#         return email

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         if commit:
#             user.save()  # Save user first
#             self.save_teacher(user)  # Save the teacher details
#         return user

#     def save_teacher(self, user):
#         first_name = self.cleaned_data['first_name']
#         last_name = self.cleaned_data['last_name']
#         email = user.email
#         username = user.username
#         school = self.cleaned_data.get('school', None)

#         # Create the Teacher object
#         teacher = Teacher(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             username=username,
#             school=school,
#         )

#         # Save the teacher object to ensure it has an ID
#         teacher.save()  # Save the teacher first

#         # Handle subjects_taught and dynamically create missing courses
#         valid_subjects = []
#         for subject in self.cleaned_data.get('subjects_taught', []):
#             course, created = Courses.objects.get_or_create(
#                 id=subject.id,
#                 defaults={'title': f"Auto-created Course {subject.id}"}
#             )
#             valid_subjects.append(course)

#         # Assign the valid subjects to the teacher (many-to-many)
#         teacher.subjects_taught.set(valid_subjects)

#         # Handle classes_taught (direct many-to-many assignment)
#         teacher.classes_taught.set(self.cleaned_data.get('classes_taught', []))

#         return teacher
    
 
    
# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)

#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Courses.objects.none(),
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.none(),
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

#         if user and user.school:
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Courses.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         self.fields['school'].initial = user.school if user else None

#         # If editing, initialize subjects and classes taught
#         if self.instance.pk:
#             self.fields['subjects_taught'].initial = self.instance.subjects_taught.all()
#             self.fields['classes_taught'].initial = self.instance.classes_taught.all()

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if NewUser.objects.filter(username=username).exists():
#             raise ValidationError("A user with this Username already exists.")
#         return username

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

#         if subjects_taught:
#             teacher.subjects_taught.set(subjects_taught.values_list('id', flat=True))

#         if classes_taught:
#             teacher.classes_taught.set(classes_taught.values_list('id', flat=True))

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
            print("Subjects taught (from init):", self.instance.subjects_taught.all())
            print("Classes taught (from init):", self.instance.classes_taught.all())
            self.fields['subjects_taught'].initial = self.instance.subjects_taught.all()
            self.fields['classes_taught'].initial = self.instance.classes_taught.all()
       


  

# class TeacherEditForm(forms.ModelForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)

#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Course.objects.none(),
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.none(),
#         label='Classes Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple
#     )

#     class Meta:
#         model = Teacher  # Use Teacher model for editing subjects and classes
#         fields = ['first_name', 'last_name', 'school', 'subjects_taught', 'classes_taught']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super(TeacherEditForm, self).__init__(*args, **kwargs)

#         if user and user.school:
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Course.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         self.fields['school'].initial = user.school if user else None

#         # Pre-fill the form fields with the teacher's current subjects and classes
#         if self.instance.pk:
#             self.fields['subjects_taught'].initial = self.instance.subjects_taught.all()
#             self.fields['classes_taught'].initial = self.instance.classes_taught.all()


# real code2
# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)
    
#     # Make subjects_taught a checkbox with CheckboxSelectMultiple widget
#     subjects_taught = forms.ModelMultipleChoiceField(
#         queryset=Courses.objects.none(),
#         label='Subjects Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple  # Use checkboxes instead of multi-select
#     )

#     classes_taught = forms.ModelMultipleChoiceField(
#         queryset=CourseGrade.objects.none(),
#         label='Classes Taught',
#         required=False,
#         widget=forms.CheckboxSelectMultiple  # Also use checkboxes for classes
#     )

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super(TeacherSignupForm, self).__init__(*args, **kwargs)
        
#         if user and user.school:
#             # Filter subjects and classes by the user's school
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Courses.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         # Ensure the user's school is pre-selected
#         self.fields['school'].initial = user.school if user else None

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
        
#         # Fetch subjects_taught and classes_taught as actual instances
#         subjects_taught = self.cleaned_data.get('subjects_taught', [])
#         classes_taught = self.cleaned_data.get('classes_taught', [])

#         # Create the teacher instance
#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             username=username,
#             school=school,
#         )

#         # Add the Many-to-Many fields correctly
#         if subjects_taught:
#             teacher.subjects_taught.set(subjects_taught.values_list('id', flat=True))  # Get only the IDs

#         if classes_taught:
#             teacher.classes_taught.set(classes_taught.values_list('id', flat=True))  # Get only the IDs

#         return teacher


# real codes
# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)
#     subjects_taught = forms.ModelMultipleChoiceField(queryset=Courses.objects.none(), label='Subjects Taught', required=False)

#     classes_taught = forms.ModelMultipleChoiceField(queryset=CourseGrade.objects.none(), label='Classes Taught', required=False)

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super(TeacherSignupForm, self).__init__(*args, **kwargs)
        
#         if user and user.school:
#             # Filter subjects and classes by the user's school
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Courses.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(schools=user.school).distinct()

#         # Ensure the user's school is pre-selected
#         self.fields['school'].initial = user.school if user else None

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
        
#         # Fetch subjects_taught and classes_taught as actual instances
#         subjects_taught = self.cleaned_data.get('subjects_taught', [])
#         classes_taught = self.cleaned_data.get('classes_taught', [])

#         # Create the teacher instance
#         teacher = Teacher.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             username=username,
#             school=school,
#         )

#         # Add the Many-to-Many fields correctly
#         if subjects_taught:
#             teacher.subjects_taught.set(subjects_taught.values_list('id', flat=True))  # Get only the IDs

#         if classes_taught:
#             teacher.classes_taught.set(classes_taught.values_list('id', flat=True))  # Get only the IDs

#         return teacher


# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.none(), label='School', required=False)
#     subjects_taught = forms.ModelMultipleChoiceField(queryset=Course.objects.none(), label='Subjects Taught', required=False)
#     classes_taught = forms.ModelMultipleChoiceField(queryset=CourseGrade.objects.none(), label='Classes Taught', required=False)

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super(TeacherSignupForm, self).__init__(*args, **kwargs)
        
#         if user and user.school:
#             # Filter students, subjects, and classes by the user's school
#             self.fields['school'].queryset = School.objects.filter(name=user.school.name)
#             self.fields['subjects_taught'].queryset = Course.objects.filter(schools=user.school)
#             self.fields['classes_taught'].queryset = CourseGrade.objects.filter(subjects__schools=user.school).distinct()

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


# class TeacherSignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=200, label='First Name')
#     last_name = forms.CharField(max_length=200, label='Last Name')
#     email = forms.EmailField(max_length=254, label='Email')
#     username = forms.CharField(max_length=35, label='Username')
#     school = forms.ModelChoiceField(queryset=School.objects.all(), label='School', required=False)
#     subjects_taught = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), label='Subjects Taught', required=False)
#     classes_taught = forms.ModelMultipleChoiceField(queryset=CourseGrade.objects.all(), label='Classes Taught', required=False)

#     class Meta:
#         model = NewUser
#         fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'school', 'subjects_taught', 'classes_taught']

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


