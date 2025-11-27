from django.shortcuts import render, redirect, get_object_or_404
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group, AnonymousUser
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from teacher import forms as QFORM
from users.models import NewUser
from quiz.models import Course, Result, Question
from django.utils.datastructures import MultiValueDictKeyError
from .models import SampleCodes, Teacher
from .forms import EditSubjectFormId, ExaminerCreateClassForm, JSONForm, SchoolForm, SchoolOnboardingForm, SubjectEditForm, TeacherSignupForm, TeacherLoginForm, QuestionForm, UploadCSVForm
from django.views.decorators.cache import cache_page
import csv
import json
from django.http import JsonResponse
from sms.models import Courses, Session, ExamType, Term
from django.forms import formset_factory
from import_export import resources
from tablib import Dataset
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
from quiz.admin import QuestionResource
import codecs
import io
import logging
from django.views.decorators.http import require_POST
from django.contrib import messages
from docx import Document
import latex2mathml.converter
from django.contrib.auth import authenticate, login
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)
from sms.forms import SessionForm, TermForm, ExamTypeForm
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from teacher import forms as QFORM
from quiz import models as QMODEL
from django.contrib import messages
from .forms import CourseGradeForm 
from django.contrib import messages
from django.shortcuts import redirect

from portal.decorators import require_cbt_subscription, require_reportcard_subscription

@login_required(login_url='teacher:teacher_login')
def teacher_list_view(request):
    user_school = request.user.school

    # Get all teachers in this school with their subjects and classes
    teachers = Teacher.objects.filter(school=user_school).prefetch_related('subjects_taught', 'classes_taught')

    # Create a dictionary mapping each teacher to their subjects
    teacher_subjects = {
        teacher.id: teacher.subjects_taught.all()
        for teacher in teachers
    }

    context = {
        'teachers': teachers,
        'teacher_subjects': teacher_subjects,  # Pass all subjects per teacher
    }

    return render(request, 'teacher/dashboard/teacher_list.html', context)


from teacher.forms import TeacherEditForm 


def teacher_edit_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        form = TeacherEditForm(request.POST, instance=teacher, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('teacher:teacher_list')
    else:
        form = TeacherEditForm(instance=teacher, user=request.user)

    # Check if the form is initialized with correct data
    # print("Subjects Taught1:", form.initial['subjects_taught'])
    # print("Classes Taught1:", form.initial['classes_taught'])

    context = {
        'form': form,
        'teacher': teacher,
    }
    return render(request, 'teacher/dashboard/teacher_edit.html', context)



@login_required(login_url='teacher:teacher_login')
def teacher_delete_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.delete()
        return redirect('teacher:teacher_list')

    return render(request, 'teacher/dashboard/teacher_confirm_delete.html', {'teacher': teacher})


# real codes3
from django.core.exceptions import ValidationError


@login_required(login_url='teacher:teacher_login')
def teacher_signup_view(request):
    if request.method == 'POST':
        form = TeacherSignupForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=True)  # Save the user
            form.save_teacher(user)  # Save the teacher details and relationships
            messages.success(request, 'Teacher registered successfully!')
            return redirect('teacher:teacher_signup')  # Redirect to another page
        else:
            print(form.errors)  # Log errors for debugging
    else:
        form = TeacherSignupForm(user=request.user)
 
    return render(request, 'teacher/dashboard/teacher_signup.html', {'form': form})


from teacher.forms import OnboardingSignupForm

@login_required(login_url='teacher:teacher_login')
@user_passes_test(lambda u: u.is_superuser and u.is_staff)
def onboarding_signup_view(request):
    if request.method == 'POST':
        form = OnboardingSignupForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=True)  # Save the user
            form.save_teacher(user)  # Save the teacher details and relationships
            messages.success(request, 'Teacher registered successfully!')
            return redirect('teacher:onboarding_signup')  # Redirect to another page
        else:
            print(form.errors)  # Log errors for debugging
    else:
        form = OnboardingSignupForm(user=request.user)
 
    return render(request, 'teacher/dashboard/onboarding_signup.html', {'form': form})



@login_required(login_url='teacher:teacher_login')
@user_passes_test(lambda u: u.is_superuser and u.is_staff)
def onboard_school_view(request):
    if request.method == 'POST':
        form = SchoolOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            new_school = form.save()
            messages.success(request, f"✅ {new_school.school_name} onboarded successfully.")
            return redirect('teacher:onboard_school')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SchoolOnboardingForm()

    schools = School.objects.all().order_by('-created')
    return render(request, 'teacher/dashboard/onboard_school.html', {
        'form': form,
        'schools': schools
    })

@login_required(login_url='teacher:teacher_login')
@user_passes_test(lambda u: u.is_superuser and u.is_staff)
def edit_school_view(request, pk):
    """Edit existing school"""
    school = get_object_or_404(School, pk=pk)
    form = SchoolForm(request.POST or None, request.FILES or None, instance=school)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"✏️ {school.school_name} has been updated successfully.")
        return redirect('teacher:onboarding_dashboard')

    return render(request, 'teacher/dashboard/school_edit.html', {'form': form, 'school': school})


@login_required(login_url='teacher:teacher_login')
@user_passes_test(lambda u: u.is_superuser and u.is_staff)
def delete_school_view(request, pk):
    """Delete school"""
    school = get_object_or_404(School, pk=pk)
    name = school.school_name
    school.delete()
    messages.warning(request, f"🗑️ {name} has been deleted successfully.")
    return redirect('teacher:onboarding')


@login_required(login_url='teacher:teacher_login')
@user_passes_test(lambda u: u.is_superuser and u.is_staff)
def onboarding_dashboard_view(request):
    # Basic statistics for overview
    schools_count = School.objects.count()
    teachers_count = Teacher.objects.count()
    sessions_count = Session.objects.count()
    terms_count = Term.objects.count()
    exam_types_count = ExamType.objects.count()

    context = {
        'schools_count': schools_count,
        'teachers_count': teachers_count,
        'sessions_count': sessions_count,
        'terms_count': terms_count,
        'exam_types_count': exam_types_count,
    }
    return render(request, 'teacher/dashboard/onboarding_dashboard.html', context)

@cache_page(60 * 15)
def teacher_logout_view(request):

    return render(request, 'teacher/dashboard/teacher_logout.html')

@cache_page(60 * 15)
def student_logout_view(request):

    return render(request, 'teacher/dashboard/student_logout.html')


@cache_page(60 * 15)
def teacher_login_view(request):
    teachers = Teacher.objects.all()
    # print('teachers:',teachers)
    if request.method == 'POST':
       
        form = TeacherLoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # print('username:',username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page or dashboard
                return redirect('teacher:teacher-dashboard')
            else:
                # Handle invalid login credentials
                # For example, you can render a message to the user indicating that the login credentials are incorrect
                return render(request, 'teacher_login.html', {'form': form, 'error_message': 'Invalid username or password'})
    else:
        form = TeacherLoginForm()
    return render(request, 'teacher/dashboard/teacher_login.html', {'form': form, 'teachers': teachers})

from teacher.models import School


@login_required(login_url='teacher:teacher_login')
def teacher_dashboard_view(request):
    username = request.user.username
    user_school = request.user.school 

    try:
        # Optimize query to fetch related objects without using only
        teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught', 'classes_taught').get(username=username)

        # Prefetch subjects and classes taught
        teacher_subjects = teacher.subjects_taught.all()
        teacher_class = teacher.classes_taught.all()
        teacher_name = teacher.first_name
        # print(teacher_name)
        courses = Courses.objects.filter(schools=user_school)


        context = {
            'school': user_school,
            'username': username,
            'teacher_class': teacher_class,
            'teacher_subjects': teacher_subjects,
            'courses': courses,  # ✅ Add this
                
        }
        return render(request, 'teacher/dashboard/teacher_dashboard.html', context=context)
    except Teacher.DoesNotExist:
        # Handle case where Teacher instance does not exist
        return redirect('account_login')

from .forms import EditSubjectForm


@login_required(login_url='teacher:teacher_login')
def edit_subjects_view(request, course_id):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # ✅ For ManyToManyField, use __in or exact match with filter
    course = get_object_or_404(
        Courses.objects.prefetch_related('schools'),
        schools=user_school,
        id=course_id
    )

    if request.method == 'POST':
        form = EditSubjectForm(request.POST, instance=course, user_school=user_school)
        if form.is_valid():
            form.save()
            return redirect('teacher:teacher-dashboard')
    else:
        form = EditSubjectForm(instance=course, user_school=user_school)

    return render(request, 'teacher/dashboard/edit_subjects.html', {
        'form': form,
        'course': course
    })


@login_required(login_url='teacher:teacher_login')
def examiner_class_list_view(request):
    """List all classes belonging to the examiner's school."""
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    classes = CourseGrade.objects.filter(schools=user_school)
    return render(request, 'teacher/dashboard/examiner_class_list.html', {'classes': classes})


@login_required(login_url='teacher:teacher_login')
def examiner_create_class_view(request):
    user = request.user
    school = getattr(user, 'school', None)

    if request.method == 'POST':
        form = ExaminerCreateClassForm(request.POST)
        if form.is_valid():
            new_class = form.save(commit=False)
            new_class.schools = school  # assign the current teacher's school
            new_class.save()
            form.save_m2m()
            messages.success(request, "Class created successfully!")
            return redirect('teacher:examiner_class_list')
    else:
        form = ExaminerCreateClassForm()

    return render(request, 'teacher/dashboard/examiner_create_class.html', {'form': form})



def examiner_edit_class_view(request, pk):
    user = request.user
    school = getattr(user, 'school', None)

    course_grade = get_object_or_404(CourseGrade, id=pk, schools=school)

    if request.method == 'POST':
        form = ExaminerCreateClassForm(request.POST, instance=course_grade, user_school=school)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated successfully!")
            return redirect('teacher:examiner_class_list')
    else:
        form = ExaminerCreateClassForm(instance=course_grade, user_school=school)

    return render(request, 'teacher/dashboard/examiner_edit_class.html', {
        'form': form,
        'course_grade': course_grade
    })


@login_required(login_url='teacher:teacher_login')
def examiner_delete_class_view(request, class_id):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    class_instance = get_object_or_404(CourseGrade, id=class_id, schools=user_school)
    class_instance.delete()
    messages.success(request, "Class deleted successfully.")
    return redirect('teacher:examiner_class_list')


# @login_required(login_url='teacher:teacher_login')
# def edit_subjects_view(request, course_id):
#     user = NewUser.objects.select_related('school').get(id=request.user.id)
#     user_school = user.school

#     course = get_object_or_404(
#         Courses.objects.prefetch_related('schools').filter(schools=user_school, id=course_id)
#     )

#     if request.method == 'POST':
#         form = EditSubjectForm(request.POST, instance=course, user_school=user_school)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Course updated successfully.")
#             return redirect('teacher:teacher-dashboard')
#     else:
#         form = EditSubjectForm(instance=course, user_school=user_school)

#     return render(request, 'teacher/dashboard/edit_subjects.html', {
#         'form': form,
#         'course': course
#     })


@login_required(login_url='teacher:teacher_login')
def bulk_update_courses(request):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # All courses for this school
    courses = Courses.objects.filter(schools=user_school)

    if request.method == 'POST':
        form = EditSubjectForm(request.POST, user_school=user_school)
        if form.is_valid():
            session = form.cleaned_data.get('session')
            term = form.cleaned_data.get('term')
            exam_type = form.cleaned_data.get('exam_type')

            # ✅ Ensure these selections belong to the user's school
            if session and session.school != user_school:
                messages.error(request, "Invalid session selection.")
                return redirect('teacher:bulk_update_courses')
            if term and term.school != user_school:
                messages.error(request, "Invalid term selection.")
                return redirect('teacher:bulk_update_courses')
            if exam_type and exam_type.school != user_school:
                messages.error(request, "Invalid exam type selection.")
                return redirect('teacher:bulk_update_courses')

            # ✅ Bulk update safely
            for course in courses:
                if session:
                    course.session = session
                if term:
                    course.term = term
                if exam_type:
                    course.exam_type = exam_type
                course.save()

            messages.success(request, "All subjects updated successfully for your school.")
            return redirect('teacher:teacher-dashboard')
    else:
        form = EditSubjectForm(user_school=user_school)

    return render(request, 'teacher/dashboard/bulk_update_courses.html', {
        'form': form,
        'courses': courses
    })


@login_required(login_url='teacher:teacher_login')
def manage_academic_setup_view(request):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # ✅ Ensure defaults exist
   
    # Fetch all data after ensuring defaults
    sessions = Session.objects.filter(school=user_school)
    terms = Term.objects.filter(school=user_school)
    exam_types = ExamType.objects.filter(school=user_school)

    if request.method == 'POST':
        if 'add_session' in request.POST:
            session_form = SessionForm(request.POST)
            if session_form.is_valid():
                new_session = session_form.save(commit=False)
                new_session.school = user_school
                new_session.save()
                messages.success(request, "Session added successfully.")
                return redirect('teacher:manage_academic_setup')

        elif 'add_term' in request.POST:
            term_form = TermForm(request.POST)
            if term_form.is_valid():
                new_term = term_form.save(commit=False)
                new_term.school = user_school
                new_term.save()
                messages.success(request, "Term added successfully.")
                return redirect('teacher:manage_academic_setup')

        elif 'add_exam_type' in request.POST:
            exam_type_form = ExamTypeForm(request.POST)
            if exam_type_form.is_valid():
                new_exam_type = exam_type_form.save(commit=False)
                new_exam_type.school = user_school
                new_exam_type.save()
                messages.success(request, "Exam type added successfully.")
                return redirect('teacher:manage_academic_setup')
    else:
        session_form = SessionForm()
        term_form = TermForm()
        exam_type_form = ExamTypeForm()

    context = {
        'sessions': sessions,
        'terms': terms,
        'exam_types': exam_types,
        'session_form': session_form,
        'term_form': term_form,
        'exam_type_form': exam_type_form,
    }

    return render(request, 'teacher/dashboard/manage_academic_setup.html', context)

# --- Edit Views ---
@login_required(login_url='teacher:teacher_login')
def edit_session_view(request, pk):
    session = get_object_or_404(Session, pk=pk, school=request.user.school)
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect('teacher:manage_academic_setup')
    else:
        form = SessionForm(instance=session)
    return render(request, 'teacher/dashboard/edit_item.html', {'form': form, 'title': 'Edit Session'})


@login_required(login_url='teacher:teacher_login')
def edit_term_view(request, pk):
    term = get_object_or_404(Term, pk=pk, school=request.user.school)
    if request.method == 'POST':
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, "Term updated successfully.")
            return redirect('teacher:manage_academic_setup')
    else:
        form = TermForm(instance=term)
    return render(request, 'teacher/dashboard/edit_item.html', {'form': form, 'title': 'Edit Term'})


@login_required(login_url='teacher:teacher_login')
def edit_exam_type_view(request, pk):
    exam_type = get_object_or_404(ExamType, pk=pk, school=request.user.school)
    if request.method == 'POST':
        form = ExamTypeForm(request.POST, instance=exam_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam type updated successfully.")
            return redirect('teacher:manage_academic_setup')
    else:
        form = ExamTypeForm(instance=exam_type)
    return render(request, 'teacher/dashboard/edit_item.html', {'form': form, 'title': 'Edit Exam Type'})


# --- Delete Views ---
@login_required(login_url='teacher:teacher_login')
def delete_session_view(request, pk):
    session = get_object_or_404(Session, pk=pk, school=request.user.school)
    session.delete()
    messages.success(request, "Session deleted successfully.")
    return redirect('teacher:manage_academic_setup')


@login_required(login_url='teacher:teacher_login')
def delete_term_view(request, pk):
    term = get_object_or_404(Term, pk=pk, school=request.user.school)
    term.delete()
    messages.success(request, "Term deleted successfully.")
    return redirect('teacher:manage_academic_setup')


@login_required(login_url='teacher:teacher_login')
def delete_exam_type_view(request, pk):
    exam_type = get_object_or_404(ExamType, pk=pk, school=request.user.school)
    exam_type.delete()
    messages.success(request, "Exam type deleted successfully.")
    return redirect('teacher:manage_academic_setup')

# @login_required(login_url='teacher:teacher_login')
# def bulk_update_courses(request):
#     user = NewUser.objects.select_related('school').get(id=request.user.id)
#     user_school = user.school

#     # All courses for this school
#     courses = Courses.objects.filter(schools=user_school)

#     if request.method == 'POST':
#         form = EditSubjectForm(request.POST, user_school=user_school)
#         if form.is_valid():
#             session = form.cleaned_data.get('session')
#             term = form.cleaned_data.get('term')
#             exam_type = form.cleaned_data.get('exam_type')

#             # Update all
#             for course in courses:
#                 if session:
#                     course.session = session
#                 if term:
#                     course.term = term
#                 if exam_type:
#                     course.exam_type = exam_type
#                 course.save()

#             messages.success(request, "All subjects updated successfully.")
#             return redirect('teacher:teacher-dashboard')
#     else:
#         form = EditSubjectForm(user_school=user_school)

#     return render(request, 'teacher/dashboard/bulk_update_courses.html', {
#         'form': form,
#         'courses': courses
#     })


@login_required(login_url='teacher:teacher_login')
def delete_subject_view(request, course_id):
    user = request.user
    user_school = user.school

    course = get_object_or_404(
        Courses.objects.prefetch_related('schools').filter(
            schools=user_school,
            id=course_id
        )
    )

    if request.method == 'POST':
        course.delete()
        messages.success(request, "Subject deleted successfully.")
        return redirect('teacher:teacher-dashboard')

    return render(request, 'teacher/dashboard/confirm_delete_subject.html', {
        'course': course
    })


def some_view(request):
    # Assuming the user is logged in and has a school attribute
    school = request.user.school  # Replace with your actual relationship

    return render(request, 'sms/dashboard/teacherbase.html', {'school': school})  



@login_required(login_url='teacher:teacher_login')
@user_passes_test(lambda u: u.is_superuser)
def logged_in_superuser_view(request):
    # Logic for the view accessible only to logged-in superusers
    return render(request, 'sms/dashboard/adminbase.html')


from users.models import Profile  # Import your models here
from quiz.models import Course
# @cache_page(60 * 15)

@login_required(login_url='account_login')
def student_dashboard_view(request):
    # Fetch the student's profile based on the logged-in user
    student_profile = NewUser.objects.get(email=request.user.email)

    # Fetch the CourseGrade instances related to the student
    enrolled_grades = CourseGrade.objects.filter(students=student_profile)

    # Extract course information from the enrolled grades
    enrolled_courses = [grade.subjects.all() for grade in enrolled_grades]

    context = {
        'student_profile': student_profile,
        'enrolled_courses': enrolled_courses,
    }

    return render(request, 'teacher/dashboard/student_dashboard.html', context)


from django.db.models import Prefetch

from django.db.models import Q

from sms.models import Session, Term  # Import your models


def class_list_view(request):
    # Get the teacher and related information
    teacher = Teacher.objects.select_related('school').prefetch_related('subjects_taught', 'classes_taught').get(user=request.user)
    
    teacher_school = teacher.school
    # Get the subjects and classes taught by this teacher
    subjects_taught = teacher.subjects_taught.all()
    classes_taught = teacher.classes_taught.all()
    print(f"subjects_taught: {subjects_taught}")
    print(f"Teacher School: {teacher.school}")
    print(f"classes_taught: {classes_taught}")
    print(f"class: {classes_taught.values_list('name', flat=True)}")

    # Get all unique result_class and corresponding subjects from the Result model
    subject_tughts = subjects_taught.values_list('course_name__title', flat=True)
    results = Result.objects.select_related('exam', 'exam__course_name__schools').filter(
        schools=teacher.school,  # Filter by the teacher's school
        result_class__in=classes_taught.values_list('name', flat=True),
        exam__course_name__title__in=subject_tughts  # Filter by the subjects taught by the teacher
    ).values(
        'result_class', 'exam__course_name__title', 'schools__school_name', 'session__name', 'term__name'
    ).distinct()

    print(results, 'yyyy')

    # Organize results into a dictionary for easier access in the template
    class_subjects = {}
    for result in results:
        result_class = result['result_class']
        exam_name = result['exam__course_name__title']  # Get the subject name from the exam field
        school_name = result['schools__school_name']  # Get the school name

        if result_class not in class_subjects:
            class_subjects[result_class] = []

        if exam_name and exam_name not in class_subjects[result_class]:  # Ensure uniqueness
            class_subjects[result_class].append((exam_name, school_name))  # Store a tuple of (exam_name, school_name)

    # Get sessions and terms for dropdowns
    sessions = Session.objects.all().distinct()
    terms = Term.objects.all().distinct()

    # Get selected filters from request
    selected_class = request.GET.get('result_class')
    selected_subject = request.GET.get('subject')
    selected_session = request.GET.get('session')
    selected_term = request.GET.get('term')

    # Prepare subjects for the selected class
    subjects_for_selected_class = class_subjects.get(selected_class, [])

    # Filter Results based on selected criteria
    filtered_results = results  # Start with the results filtered by school

    if selected_class:
        filtered_results = filtered_results.filter(result_class=selected_class)

    if selected_subject and selected_subject in subject_tughts:
        filtered_results = filtered_results.filter(exam__course_name__title=selected_subject)

    if selected_session:
        filtered_results = filtered_results.filter(session__name=selected_session)

    if selected_term:
        filtered_results = filtered_results.filter(term__name=selected_term)

    # Apply distinct to ensure unique combinations of the filtered results
    filtered_results = filtered_results.values(
        'result_class', 'exam__course_name__title', 'schools__school_name', 'session__name', 'term__name'
    ).distinct()

    for result in filtered_results:
        print(result['schools__school_name'], 'uuuu')

    # Prepare context    
    context = {
        'class_subjects': class_subjects,
        'sessions': sessions,
        'terms': terms,   
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'selected_session': selected_session,
        'selected_term': selected_term,
        'subjects_for_selected_class': subjects_for_selected_class,
        'filtered_results': filtered_results,
        'subject_tughts': subject_tughts,  # Add this for displaying the subjects taught by the teacher
    }  

    return render(request, 'teacher/dashboard/class_list.html', context)




from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from teacher.models import ColumnLock

  
def control_list_view(request):
    # Get the teacher and related information
    teacher = Teacher.objects.select_related('school').prefetch_related('subjects_taught', 'classes_taught').get(user=request.user)
    
    teacher_school = teacher.school
    # Get the subjects and classes taught by this teacher
    subjects_taught = teacher.subjects_taught.all()
    classes_taught = teacher.classes_taught.all()
    # print(f"subjects_taught: {subjects_taught}")
    # print(f"Teacher School: {teacher.school}")
    # print(f"classes_taught: {classes_taught}")
    # print(f"class: {classes_taught.values_list('name', flat=True)}")

    # Get all unique result_class and corresponding subjects from the Result model
    subject_tughts = subjects_taught.values_list('course_name__title', flat=True)
    results = Result.objects.select_related('exam', 'exam__course_name__schools').filter(
        schools=teacher.school,  # Filter by the teacher's school
        result_class__in=classes_taught.values_list('name', flat=True),
        exam__course_name__title__in=subject_tughts  # Filter by the subjects taught by the teacher
    ).values(
        'result_class', 'exam__course_name__title', 'schools__school_name', 'session__name', 'term__name'
    ).distinct()

    # print(results, 'yyyy')

    # Organize results into a dictionary for easier access in the template
    class_subjects = {}
    for result in results:
        result_class = result['result_class']
        exam_name = result['exam__course_name__title']  # Get the subject name from the exam field
        school_name = result['schools__school_name']  # Get the school name

        if result_class not in class_subjects:
            class_subjects[result_class] = []

        if exam_name and exam_name not in class_subjects[result_class]:  # Ensure uniqueness
            class_subjects[result_class].append((exam_name, school_name))  # Store a tuple of (exam_name, school_name)

    # Get sessions and terms for dropdowns
    sessions = Session.objects.all().distinct()
    terms = Term.objects.all().distinct()

    # Get selected filters from request
    selected_class = request.GET.get('result_class')
    selected_subject = request.GET.get('subject')
    selected_session = request.GET.get('session')
    selected_term = request.GET.get('term')

    # Prepare subjects for the selected class
    subjects_for_selected_class = class_subjects.get(selected_class, [])

    # Filter Results based on selected criteria
    filtered_results = results  # Start with the results filtered by school

    if selected_class:
        filtered_results = filtered_results.filter(result_class=selected_class)

    if selected_subject and selected_subject in subject_tughts:
        filtered_results = filtered_results.filter(exam__course_name__title=selected_subject)

    if selected_session:
        filtered_results = filtered_results.filter(session__name=selected_session)

    if selected_term:
        filtered_results = filtered_results.filter(term__name=selected_term)

    # Apply distinct to ensure unique combinations of the filtered results
    filtered_results = filtered_results.values(
        'result_class', 'exam__course_name__title', 'schools__school_name', 'session__name', 'term__name'
    ).distinct()

    for result in filtered_results:
        print(result['schools__school_name'], 'uuuu')

    # Prepare context    
    context = {
        'class_subjects': class_subjects,
        'sessions': sessions,
        'terms': terms,   
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'selected_session': selected_session,
        'selected_term': selected_term,
        'subjects_for_selected_class': subjects_for_selected_class,
        'filtered_results': filtered_results,
        'subject_tughts': subject_tughts,  # Add this for displaying the subjects taught by the teacher
    }  


    return render(request, 'teacher/dashboard/control_list_view.html', context)


def control_view(request, result_class, subject, session_name, term_name):
    # Fetch the course based on the 'subject'
    course = get_object_or_404(Course, course_name__title__iexact=subject)
    # Fetch the session and term
    session = get_object_or_404(Session, name=session_name)
    term = get_object_or_404(Term, name=term_name)

    # Fetch the column lock object for the course
    column_lock, created = ColumnLock.objects.get_or_create(subject=course)

    # Fetch the students in the specified class
    all_students = Profile.objects.filter(student_class=result_class)

    if request.method == 'POST':
        # Update the locking status based on form submission
        column_lock.ca_locked = 'ca_locked' in request.POST
        column_lock.midterm_locked = 'midterm_locked' in request.POST
        column_lock.exam_locked = 'exam_locked' in request.POST
        column_lock.save()  # Save the updated locking status

        # Handle form submission for updating results
        for student in all_students:
            ca_marks = request.POST.get(f'ca_marks_{student.id}')
            midterm_marks = request.POST.get(f'midterm_marks_{student.id}')
            exam_marks = request.POST.get(f'exam_marks_{student.id}')

            # Handle CA Marks (only if CA is not locked)
            if ca_marks is not None and not column_lock.ca_locked:
                ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
                Result.objects.update_or_create(
                    student=student,
                    exam_type=ca_exam_type,
                    exam=course,
                    session=session,
                    term=term,
                    defaults={'marks': int(ca_marks) if ca_marks else 0}
                )

            # Handle Midterm Marks (only if Midterm is not locked)
            if midterm_marks is not None and not column_lock.midterm_locked:
                midterm_exam_type = get_object_or_404(ExamType, name__iexact='MIDTERM')
                Result.objects.update_or_create(
                    student=student,
                    exam_type=midterm_exam_type,
                    exam=course,
                    session=session,
                    term=term,
                    defaults={'marks': int(midterm_marks) if midterm_marks else 0}
                )

            # Handle Exam Marks (only if Exam is not locked)
            if exam_marks is not None and not column_lock.exam_locked:
                exam_exam_type = get_object_or_404(ExamType, name__iexact='EXAM')
                Result.objects.update_or_create(
                    student=student,
                    exam_type=exam_exam_type,
                    exam=course,
                    session=session,
                    term=term,
                    defaults={'marks': int(exam_marks) if exam_marks else 0}
                )

        # Redirect to the results view after updating
        return redirect('teacher:result_column_view', result_class=result_class, subject=course.course_name.title, session=session_name, term=term_name)

    else:
        # Retrieve existing results for the specified course, session, and term
        results = Result.objects.filter(
            student__student_class=result_class,
            exam__course_name__title=course,
            session=session,
            term=term
        ).select_related('student', 'exam_type')

        # Initialize a dictionary to hold student results
        student_results = {
            student: {
                'student': student,
                'admission_no': student.admission_no if hasattr(student, 'admission_no') else None,
                'ca_marks': 0,
                'midterm_marks': 0,
                'exam_marks': 0,
                'ca_total': 0,
                'midterm_total': 0,
                'exam_total': 0,
                'final_total': 0
            }
            for student in all_students
        }

        # Populate student results from existing records
        for result in results:
            student = result.student
            if student in student_results:
                if result.exam_type.name.lower() == 'ca':
                    student_results[student]['ca_marks'] = result.marks
                    student_results[student]['ca_total'] += result.marks
                elif result.exam_type.name.lower() == 'midterm':
                    student_results[student]['midterm_marks'] = result.marks
                    student_results[student]['midterm_total'] += result.marks
                elif result.exam_type.name.lower() == 'exam':
                    student_results[student]['exam_marks'] = result.marks
                    student_results[student]['exam_total'] += result.marks

                # Calculate the final total
                student_results[student]['final_total'] = (
                    student_results[student]['ca_total'] +
                    student_results[student]['midterm_total'] +
                    student_results[student]['exam_total']
                )

        context = {
            'student_results': student_results.values(),
            'result_class': result_class,
            'subject': subject,
            'session': session,
            'term': term,
            'course': course,  # Add 'course' to the context
            'lock_status': column_lock  # Pass lock status to the context
        }

        return render(request, 'teacher/dashboard/control_view.html', context)
    

# real
# def control_view(request, result_class, subject, session_name, term_name):
#     # Fetch the course based on the 'subject'
#     course = get_object_or_404(Course, course_name__title__iexact=subject)
#     print(course.course_name.title)          
#     # Fetch the session and term
#     session = get_object_or_404(Session, name=session_name)
#     term = get_object_or_404(Term, name=term_name)
    
#     # Fetch the students in the specified class
#     all_students = Profile.objects.filter(student_class=result_class)

#     if request.method == 'POST':
#         # Handle form submission for updating results
#         for student in all_students:
#             ca_marks = request.POST.get(f'ca_marks_{student.id}')
#             midterm_marks = request.POST.get(f'midterm_marks_{student.id}')
#             exam_marks = request.POST.get(f'exam_marks_{student.id}')

#             # Handle CA Marks
#             if ca_marks:
#                 ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
#                 Result.objects.update_or_create(
#                     student=student,
#                     exam_type=ca_exam_type,
#                     course=course,
#                     session=session,
#                     term=term,
#                     defaults={'marks': ca_marks}
#                 )

#             # Handle Midterm Marks
#             if midterm_marks:
#                 midterm_exam_type = get_object_or_404(ExamType, name__iexact='Midterm')
#                 Result.objects.update_or_create(
#                     student=student,
#                     exam_type=midterm_exam_type,
#                     course=course,
#                     session=session,
#                     term=term,
#                     defaults={'marks': midterm_marks}
#                 )

#             # Handle Exam Marks
#             if exam_marks:
#                 exam_exam_type = get_object_or_404(ExamType, name__iexact='Exam')
#                 Result.objects.update_or_create(
#                     student=student,
#                     exam_type=exam_exam_type,
#                     course=course,
#                     session=session,
#                     term=term,
#                     defaults={'marks': exam_marks}
#                 )

#         # Redirect to the results view after updating
#         return redirect('teacher:result_column_view', result_class=result_class, subject=course.course_name.title, session=session_name, term=term_name)

#     else:
#         # Retrieve existing results for the specified course, session, and term
#         results = Result.objects.filter(
#             student__student_class=result_class,
#             exam__course_name__title=course,
#             session=session,
#             term=term
#         ).select_related('student', 'exam_type')

#         # Initialize a dictionary to hold student results
#         student_results = {}
#         for student in all_students:
#             student_results[student] = {
#                 'student': student,
#                 'admission_no': student.admission_no if hasattr(student, 'admission_no') else None,
#                 'ca_marks': 0,
#                 'midterm_marks': 0,
#                 'exam_marks': 0,
#                 'ca_total': 0,
#                 'midterm_total': 0,
#                 'exam_total': 0,
#                 'final_total': 0
#             }

#         # Populate student results from existing records
#         for result in results:
#             student = result.student
#             if student in student_results:
#                 if result.exam_type.name.lower() == 'ca':
#                     student_results[student]['ca_marks'] = result.marks
#                     student_results[student]['ca_total'] += result.marks
#                 elif result.exam_type.name.lower() == 'midterm':
#                     student_results[student]['midterm_marks'] = result.marks
#                     student_results[student]['midterm_total'] += result.marks
#                 elif result.exam_type.name.lower() == 'exam':
#                     student_results[student]['exam_marks'] = result.marks
#                     student_results[student]['exam_total'] += result.marks

#                 # Calculate the final total
#                 student_results[student]['final_total'] = (
#                     student_results[student]['ca_total'] +
#                     student_results[student]['midterm_total'] +
#                     student_results[student]['exam_total']
#                 )

#         print(student_results)
#         print(result_class)
#         print(subject)
#         print(session)
#         print(term)

#         context = {
#             'student_results': student_results.values(),
#             'result_class': result_class,
#             'subject': subject,
#             'session': session,
#             'term': term,
#             'course': course,  # Add 'course' to the context
#         }

#         return render(request, 'teacher/dashboard/control_view.html', context)

        
def result_column_view(request, result_class, subject, session, term):
    # Fetch the course based on the 'subject'
    course = get_object_or_404(Course, course_name__title__iexact=subject)
    student = get_object_or_404(Profile, id=request.user.school.id)
    school_name = student.schools

    if request.method == 'POST':
        session_name = request.POST.get('session')
        term_name = request.POST.get('term')
        session = get_object_or_404(Session, name=session_name)
        term = get_object_or_404(Term, name=term_name)

        # Get lock status for the subject
        ca_locked = ColumnLock.objects.filter(subject__id=course.id, ca_locked=True).exists()

        # Iterate through each student to capture their marks
        for student in Profile.objects.filter(student_class=result_class):
            ca_marks = request.POST.get(f'ca_marks_{student.id}')
            midterm_marks = request.POST.get(f'midterm_marks_{student.id}')
            exam_marks = request.POST.get(f'exam_marks_{student.id}')

            # Handle CA Marks
            if ca_marks and not ca_locked:  # Only save CA marks if not locked
                ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
                Result.objects.update_or_create(
                    student=student,
                    exam_type=ca_exam_type,
                    course=course,
                    session=session,
                    term=term,
                    defaults={'marks': ca_marks}
                )

            # Handle Midterm Marks
            if midterm_marks:
                midterm_exam_type = get_object_or_404(ExamType, name__iexact='MIDTERM')
                Result.objects.update_or_create(
                    student=student,
                    exam_type=midterm_exam_type,
                    course=course,
                    session=session,
                    term=term,
                    defaults={'marks': midterm_marks}
                )

            # Handle Exam Marks
            if exam_marks:
                exam_exam_type = get_object_or_404(ExamType, name__iexact='EXAM')
                Result.objects.update_or_create(
                    student=student,
                    exam_type=exam_exam_type,
                    course=course,
                    session=session,
                    term=term,
                    defaults={'marks': exam_marks}
                )

        return redirect('teacher:result-column', result_class=result_class, subject=subject)

    else:
        all_students = Profile.objects.filter(student_class=result_class)

        # Fetch existing results for the specified course
        results = Result.objects.filter(student__student_class=result_class, exam__course_name__title=course).select_related('student', 'exam_type', 'session', 'term')

        student_results = {}
        session = results.first().session if results.exists() else None
        term = results.first().term if results.exists() else None

        # Initialize student results dictionary
        for student in all_students:
            student_results[student] = {
                'student': student,
                'admission_no': student.admission_no if hasattr(student, 'admission_no') else None,
                'ca_marks': 0,
                'midterm_marks': 0,
                'exam_marks': 0,
                'ca_total': 0,
                'midterm_total': 0,
                'exam_total': 0,
                'final_total': 0
            }

        # Populate student results from existing records
        for result in results:
            student = result.student
            if student in student_results:
                if result.exam_type.name.lower() == 'ca':
                    student_results[student]['ca_marks'] = result.marks
                    student_results[student]['ca_total'] = result.marks
                elif result.exam_type.name.lower() == 'midterm':
                    student_results[student]['midterm_marks'] = result.marks
                    student_results[student]['midterm_total'] = result.marks
                elif result.exam_type.name.lower() == 'exam':
                    student_results[student]['exam_marks'] = result.marks
                    student_results[student]['exam_total'] = result.marks

                # Calculate the final total
                student_results[student]['final_total'] = (
                    student_results[student]['ca_total'] +
                    student_results[student]['midterm_total'] +
                    student_results[student]['exam_total']
                )

        # Get lock status for the subject
        lock_status = {
            'ca_locked': ColumnLock.objects.filter(subject__id=course.id, ca_locked=True).exists(),
            'midterm_locked': ColumnLock.objects.filter(subject__id=course.id, midterm_locked=True).exists(),
            'exam_locked': ColumnLock.objects.filter(subject__id=course.id, exam_locked=True).exists(),
        }

        context = {
            'student_results': student_results.values(),
            'result_class': result_class,
            'subject': subject,
            'session': session,
            'term': term,
            'school_name': school_name,
            'lock_status': lock_status,
        }

        return render(request, 'teacher/dashboard/results_table.html', context)
   


from django.db import IntegrityError

# Set up logging
logger = logging.getLogger(__name__)


def save_results(request):
    if request.method == 'POST':
        result_class = request.POST.get('result_class')
        subject = request.POST.get('subject')
        session_name = request.POST.get('session')
        term_name = request.POST.get('term')

        # Fetch the course related to the subject
        course = get_object_or_404(Course, course_name__title__iexact=subject)

        # Fetch the session and term based on the provided names (case-insensitive)
        session = get_object_or_404(Session, name__iexact=session_name)
        term = get_object_or_404(Term, name__iexact=term_name)

        # Fetch the lock status for the columns of this subject/course
        column_lock = get_object_or_404(ColumnLock, subject=course)

        for key, value in request.POST.items():
            if key.startswith('marks_'):
                student_id = key.split('_')[2]  # Extract the student ID from the input name

                # Fetch the student
                student = get_object_or_404(Profile, id=student_id)

                # Get the student's school
                student_school = student.schools

                # Initialize marks
                ca_marks = request.POST.get(f'marks_ca_{student_id}', 0)
                midterm_marks = request.POST.get(f'marks_midterm_{student_id}', 0)
                exam_marks = request.POST.get(f'marks_exam_{student_id}', 0)

                try:
                    # Handle CA Marks (only if CA is not locked)
                    if ca_marks is not None and not column_lock.ca_locked:
                        ca_marks = min(int(ca_marks), 10)  # Ensure CA marks do not exceed 10
                        ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
                        Result.objects.update_or_create(
                            result_class=result_class,
                            schools=student_school,
                            student=student,
                            exam_type=ca_exam_type,
                            exam=course,
                            session=session,
                            term=term,
                            defaults={'marks': ca_marks}
                        )

                    # Handle Midterm Marks (only if Midterm is not locked)
                    if midterm_marks is not None and not column_lock.midterm_locked:
                        midterm_marks = min(int(midterm_marks), 20)  # Ensure Midterm marks do not exceed 20
                        midterm_exam_type = get_object_or_404(ExamType, name__iexact='MIDTERM')
                        Result.objects.update_or_create(
                            result_class=result_class,
                            schools=student_school,
                            student=student,
                            exam_type=midterm_exam_type,
                            exam=course,
                            session=session,
                            term=term,
                            defaults={'marks': midterm_marks}
                        )

                    # Handle Exam Marks (only if Exam is not locked)
                    if exam_marks is not None and not column_lock.exam_locked:
                        exam_marks = min(int(exam_marks), 70)  # Ensure Exam marks do not exceed 70
                        exam_exam_type = get_object_or_404(ExamType, name__iexact='EXAM')
                        Result.objects.update_or_create(
                            result_class=result_class,
                            schools=student_school,
                            student=student,
                            exam_type=exam_exam_type,
                            exam=course,
                            session=session,
                            term=term,
                            defaults={'marks': exam_marks}
                        )
                except IntegrityError:
                    pass  # Handle any integrity issues (like duplicate entries)

        return redirect('teacher:result_column_view', result_class=result_class, subject=subject, session=session.name, term=term.name)

    return redirect('teacher:result_column_view', result_class='default_class', subject='YourDefaultSubject', session='DefaultSession', term='DefaultTerm')


# real 2
# def save_results(request):
#     if request.method == 'POST':
#         result_class = request.POST.get('result_class')
#         subject = request.POST.get('subject')
#         session_name = request.POST.get('session')
#         term_name = request.POST.get('term')

#         # Fetch the course related to the subject
#         course = get_object_or_404(Course, course_name__title__iexact=subject)

#         # Fetch the session and term based on the provided names (case-insensitive)
#         session = get_object_or_404(Session, name__iexact=session_name)
#         term = get_object_or_404(Term, name__iexact=term_name)

#         # Fetch the lock status for the columns of this subject/course
#         column_lock = get_object_or_404(ColumnLock, subject=course)

#         for key, value in request.POST.items():
#             if key.startswith('marks_'):
#                 student_id = key.split('_')[2]  # Extract the student ID from the input name

#                 # Fetch the student
#                 student = get_object_or_404(Profile, id=student_id)

#                 # Get the student's school
#                 student_school = student.schools

#                 # Initialize marks as None
#                 ca_marks = request.POST.get(f'marks_ca_{student_id}', None)
#                 midterm_marks = request.POST.get(f'marks_midterm_{student_id}', None)
#                 exam_marks = request.POST.get(f'marks_exam_{student_id}', None)

#                 try:
#                     # Handle CA Marks (only if CA is not locked)
#                     if ca_marks is not None and not column_lock.ca_locked:
#                         ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
#                         Result.objects.update_or_create(
#                             result_class=result_class,
#                             schools=student_school,
#                             student=student,
#                             exam_type=ca_exam_type,
#                             exam=course,
#                             session=session,
#                             term=term,
#                             defaults={'marks': ca_marks or 0}  # Ensure non-null marks
#                         )

#                     # Handle Midterm Marks (only if Midterm is not locked)
#                     if midterm_marks is not None and not column_lock.midterm_locked:
#                         midterm_exam_type = get_object_or_404(ExamType, name__iexact='MIDTERM')
#                         Result.objects.update_or_create(
#                             result_class=result_class,
#                             schools=student_school,
#                             student=student,
#                             exam_type=midterm_exam_type,
#                             exam=course,
#                             session=session,
#                             term=term,
#                             defaults={'marks': midterm_marks or 0}
#                         )

#                     # Handle Exam Marks (only if Exam is not locked)
#                     if exam_marks is not None and not column_lock.exam_locked:
#                         exam_exam_type = get_object_or_404(ExamType, name__iexact='EXAM')
#                         Result.objects.update_or_create(
#                             result_class=result_class,
#                             schools=student_school,
#                             student=student,
#                             exam_type=exam_exam_type,
#                             exam=course,
#                             session=session,
#                             term=term,
#                             defaults={'marks': exam_marks or 0}
#                         )
#                 except IntegrityError:
#                     pass  # Handle any integrity issues (like duplicate entries)

#         return redirect('teacher:result_column_view', result_class=result_class, subject=subject, session=session.name, term=term.name)

#     return redirect('teacher:result_column_view', result_class='default_class', subject='YourDefaultSubject', session='DefaultSession', term='DefaultTerm')


# real
# def save_results(request):
#     if request.method == 'POST':
#         result_class = request.POST.get('result_class')  # Get result_class from the form
#         subject = request.POST.get('subject')  # Get subject from the form
#         session_name = request.POST.get('session')  # Get session from the form
#         term_name = request.POST.get('term')  # Get term from the form

#         # Fetch the course related to the subject
#         course = get_object_or_404(Course, course_name__title__iexact=subject)

#         # Fetch the session and term based on the provided names (case-insensitive)
#         session = get_object_or_404(Session, name__iexact=session_name)
#         term = get_object_or_404(Term, name__iexact=term_name)

#         for key, value in request.POST.items():
#             if key.startswith('ca_marks_'):
#                 student_id = key.split('_')[2]  # Extract the student ID from the input name

#                 ca_marks = request.POST.get(f'ca_marks_{student_id}')
#                 midterm_marks = request.POST.get(f'midterm_marks_{student_id}')
#                 exam_marks = request.POST.get(f'exam_marks_{student_id}')

#                 # Fetch the student
#                 student = get_object_or_404(Profile, id=student_id)

#                 # Get the student's school
#                 student_school = student.schools

#                 try:
#                     # Handle CA Marks
#                     if ca_marks is not None:
#                         ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
#                         Result.objects.update_or_create(
#                             result_class=result_class,
#                             schools=student_school,  # Save the student's school
#                             student=student,
#                             exam_type=ca_exam_type,
#                             exam=course,  # Include the course here
#                             session=session,  # Include the session here
#                             term=term,  # Include the term here
#                             defaults={'marks': ca_marks}
#                         )

#                     # Handle Midterm Marks
#                     if midterm_marks is not None:
#                         midterm_exam_type = get_object_or_404(ExamType, name__iexact='MIDTERM')
#                         Result.objects.update_or_create(
#                             result_class=result_class,
#                             schools=student_school,  # Save the student's school
#                             student=student,
#                             exam_type=midterm_exam_type,
#                             exam=course,  # Include the course here
#                             session=session,  # Include the session here
#                             term=term,  # Include the term here
#                             defaults={'marks': midterm_marks}
#                         )

#                     # Handle Exam Marks
                    
#                     if exam_marks is not None:
#                         exam_exam_type = get_object_or_404(ExamType, name__iexact='EXAM')
#                         Result.objects.update_or_create(
#                             result_class=result_class,
#                             schools=student_school,  # Save the student's school
#                             student=student,
#                             exam_type=exam_exam_type,
#                             exam=course,  # Include the course here
#                             session=session,  # Include the session here
#                             term=term,  # Include the term here
#                             defaults={'marks': exam_marks}
#                         )
#                 except IntegrityError:
#                     # Handle the case where a record with this combination already exists
#                     # You can either update the existing record or handle the error as necessary
#                     pass

#         # Redirect to result_column_view with all necessary parameters
#         return redirect('teacher:result_column_view', result_class=result_class, subject=subject, session=session.name, term=term.name)

#     # Redirect to a default view if the request method is not POST
#     return redirect('teacher:result_column_view', result_class='default_class', subject='YourDefaultSubject', session='DefaultSession', term='DefaultTerm')
   

# def save_results(request):

#     if request.method == 'POST':
#         result_class = request.POST.get('result_class')  # Get result_class from the form
#         subject = request.POST.get('subject')  # Get subject from the form
#         session_name = request.POST.get('session')  # Get session from the form
#         term_name = request.POST.get('term')  # Get term from the form

#         # Fetch the course related to the subject
#         course = get_object_or_404(Course, course_name__title__iexact=subject)

#         # Fetch the session and term based on the provided names (case-insensitive)
#         session = get_object_or_404(Session, name__iexact=session_name)
#         term = get_object_or_404(Term, name__iexact=term_name)

#         for key, value in request.POST.items():
#             if key.startswith('ca_marks_'):
#                 student_id = key.split('_')[2]  # Extract the student ID from the input name
                
#                 ca_marks = request.POST.get(f'ca_marks_{student_id}')
#                 midterm_marks = request.POST.get(f'midterm_marks_{student_id}')
#                 exam_marks = request.POST.get(f'exam_marks_{student_id}')
                
#                 # Fetch the student
#                 student = get_object_or_404(Profile, id= student_id)

#                 # Handle CA Marks
#                 if ca_marks is not None:
#                     ca_exam_type = get_object_or_404(ExamType, name__iexact='CA')
#                     Result.objects.update_or_create(
#                         result_class=result_class,
#                         schools = student.schools ,
#                         student=student,
#                         exam_type=ca_exam_type,
#                         exam=course,  # Include the course here
#                         session=session,  # Include the session here
#                         term=term,  # Include the term here
#                         defaults={'marks': ca_marks}
#                     )

#                 # Handle Midterm Marks
#                 if midterm_marks is not None:
#                     midterm_exam_type = get_object_or_404(ExamType, name__iexact='Midterm')
#                     Result.objects.update_or_create(
#                         student=student,
#                         result_class=result_class,
#                         exam_type=midterm_exam_type,
#                         exam=course,  # Include the course here
#                         session=session,  # Include the session here
#                         term=term,  # Include the term here
#                         defaults={'marks': midterm_marks}
#                     )

#                 # Handle Exam Marks
#                 if exam_marks is not None:
#                     exam_exam_type = get_object_or_404(ExamType, name__iexact='Exam')
#                     Result.objects.update_or_create(
#                         result_class=result_class,
#                         student=student,
#                         exam_type=exam_exam_type,
#                         exam=course,  # Include the course here
#                         session=session,  # Include the session here
#                         term=term,  # Include the term here
#                         defaults={'marks': exam_marks}
#                     )
       
#         # Redirect to result_column_view with all necessary parameters
#         return redirect('teacher:result_column_view', result_class=result_class, subject=subject, session=session.name, term=term.name)

#     # Redirect to a default view if the request method is not POST
#     return redirect('teacher:result_column_view', result_class='default_class', subject='YourDefaultSubject', session='DefaultSession', term='DefaultTerm')


# def save_results(request):
#     if request.method == 'POST':
#         result_class = request.POST.get('result_class')  # Get result_class from the form
#         subject = request.POST.get('subject')  # Get subject from the form

#         for key, value in request.POST.items():
#             if key.startswith('ca_marks_'):
#                 student_id = key.split('_')[2]  # Extract the student ID from the input name
#                 ca_marks = request.POST.get(f'ca_marks_{student_id}')
#                 midterm_marks = request.POST.get(f'midterm_marks_{student_id}')
#                 exam_marks = request.POST.get(f'exam_marks_{student_id}')
                
#                 # Fetch the student's result and update their marks
#                 results = Result.objects.filter(student_id=student_id, result_class=result_class)
#                 for result in results:
#                     if result.exam_type.name.lower() == 'ca':
#                         result.marks = ca_marks or 0
#                     elif result.exam_type.name.lower() == 'midterm':
#                         result.marks = midterm_marks or 0
#                     elif result.exam_type.name.lower() == 'exam':
#                         result.marks = exam_marks or 0
#                     result.save()
       
#         return redirect('teacher:result_column_view', result_class=result_class, subject=subject)

#     return redirect('teacher:result_column_view', result_class='default_class', subject='YourDefaultSubject')



# def result_column_view(request):

#     # Fetch all students and their results
#     results = Result.objects.all().select_related('student', 'exam', 'exam_type')

#     # Dictionary to store data for each student
#     student_results = {}

#     # Process each result entry and calculate totals
#     for result in results:
#         student = result.student

#         if student not in student_results:
#             student_results[student] = {
#                 'student': student,
#                 'admission_no': student.admission_no if hasattr(student, 'admission_no') else None,
#                 'ca_marks': 0,
#                 'midterm_marks': 0,
#                 'exam_marks': 0,
#                 'ca_total': 0,
#                 'midterm_total': 0,
#                 'exam_total': 0,
#                 'final_total': 0
#             }

#         # Log the current exam type to debug the issue
#         print(f"Exam type for {student}: {result.exam_type.name}")

#         # Identify the exam type (CA, Midterm, or Exam) and add the marks
#         if result.exam_type.name.lower() == 'ca':  # Case-insensitive comparison
#             student_results[student]['ca_marks'] = result.marks
#             student_results[student]['ca_total'] = result.marks * 10 / 10
#         elif result.exam_type.name.lower() == 'midterm':
#             student_results[student]['midterm_marks'] = result.marks
#             student_results[student]['midterm_total'] = result.marks * 20 / 20
#         elif result.exam_type.name.lower() == 'exam':
#             student_results[student]['exam_marks'] = result.marks
#             student_results[student]['exam_total'] = result.marks * 70 / 70

#         # Calculate the final total (CA + Midterm + Exam)
#         student_results[student]['final_total'] = (
#             student_results[student]['ca_total'] +
#             student_results[student]['midterm_total'] +
#             student_results[student]['exam_total']
#         )

#     # Pass the processed student results to the template
#     context = {
#         'student_results': student_results.values()
#     }

#     return render(request, 'teacher/dashboard/results_table.html', context)

from django.contrib import messages  # Add this import

@require_cbt_subscription
@login_required(login_url='teacher:teacher_login')
def add_question_view(request):
    user = request.user
    try:
        teacher = Teacher.objects.select_related('user', 'school').get(user=user)
    except Teacher.DoesNotExist:
        return redirect('teacher_login')

    subjects_taught = teacher.subjects_taught.all()
    subjects_taught_titles = [course for course in subjects_taught]
    courses = teacher.subjects_taught.all()

    QuestionFormSet = formset_factory(QuestionForm, extra=1)
 
    if request.method == 'POST':
        formset = QuestionFormSet(request.POST, request.FILES)
        if formset.is_valid():
            for form in formset:
                if form.is_valid():
                    question = form.save(commit=False)
                    question.teacher = teacher
                    question.save()
            # Add success message here
            messages.success(request, "Questions added successfully!")
            return redirect('teacher:add_question')
    else:
        formset = QuestionFormSet(form_kwargs={'courses': courses})

    context = {
        'formset': formset,
        'subjects_taught': subjects_taught,
    }
    return render(request, 'teacher/dashboard/teacher_add_question.html', context)




from .models import CourseGrade

from django.contrib.auth.decorators import login_required

# @login_required(login_url='teacher:teacher_login')
# def examiner_dashboard_view(request):
#     # Check if the user is authenticated
#     if request.user.is_authenticated:
#         user = NewUser.objects.select_related('school').get(id=request.user.id)
#         user_school = user.school

#         # Filter CourseGrade objects based on the user's school, without depending on the students relationship
#         course_grades = CourseGrade.objects.filter(
#             subjects__schools=user_school
#         ).distinct().prefetch_related('students', 'subjects')

#         context = {
#             'course_grades': course_grades,
#         }

#         return render(request, 'teacher/dashboard/examiner_dashboard.html', context)




@login_required(login_url='teacher:teacher_login')
def examiner_dashboard_view(request):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # Show ALL classes in this school (even empty ones)
    course_grades = (
        CourseGrade.objects.filter(schools=user_school)
        .prefetch_related('students', 'subjects')
        .order_by('name')
    )

    context = {
        'course_grades': course_grades,
    }

    return render(request, 'teacher/dashboard/examiner_dashboard.html', context)
    


@login_required(login_url='teacher:teacher_login')
def student_lists_view(request):
    students = NewUser.objects.filter(
        is_staff=False, 
        is_superuser=False, 
        school=request.user.school
    )
    
    # All active classes in this school
    all_classes = CourseGrade.objects.filter(schools=request.user.school, is_active=True).order_by('name')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        new_class_id = request.POST.get('new_class_id')

        if student_id and new_class_id:
            student = get_object_or_404(NewUser, id=student_id)
            new_class = get_object_or_404(CourseGrade, id=new_class_id)

            # Check if the target class already has students
            if new_class.students.exists():
                messages.error(request, f"Cannot move {student.first_name} to {new_class.name}. Class is not empty.")
            else:
                # Remove from old classes
                old_classes = CourseGrade.objects.filter(students=student)
                for c in old_classes:
                    c.students.remove(student)

                # Add to new class
                new_class.students.add(student)
                student.student_class = new_class.name
                student.save()

                messages.success(request, f"{student.first_name} moved to {new_class.name}")

            return redirect('teacher:student_lists')

    context = {
        'students': students,
        'all_classes': all_classes,
    }
    return render(request, 'teacher/dashboard/student_lists.html', context)

def bulk_move_students(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_students')
        new_class_id = request.POST.get('new_class_id')

        if selected_ids and new_class_id:
            new_class = CourseGrade.objects.get(id=new_class_id)
            students = NewUser.objects.filter(
                id__in=selected_ids,
                school=request.user.school,
            )
            for s in students:
                s.student_class = new_class.name
                s.save()
            messages.success(request, f"{len(selected_ids)} student(s) moved to {new_class.name}.")
        else:
            messages.warning(request, "Please select at least one student and a destination class.")

    return redirect('teacher:student_lists')

@login_required(login_url='teacher:teacher_login')
def bulk_action_students(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_students')
        if not selected_ids:
            messages.warning(request, "No students selected.")
            return redirect('teacher:student_lists')

        # Handle bulk delete
        if 'bulk_delete' in request.POST:
            students_to_delete = NewUser.objects.filter(id__in=selected_ids, school=request.user.school)
            count = students_to_delete.count()
            students_to_delete.delete()
            messages.success(request, f"{count} student(s) deleted successfully.")
            return redirect('teacher:student_lists')

        # Handle bulk move
        if 'bulk_move' in request.POST:
            selected_ids = request.POST.getlist('selected_students')
            new_class_id = request.POST.get('bulk_new_class_id')
            if selected_ids and new_class_id:
                new_class = get_object_or_404(CourseGrade, id=new_class_id)
                for student in NewUser.objects.filter(id__in=selected_ids):
                    old_classes = CourseGrade.objects.filter(students=student)
                    for c in old_classes:
                        c.students.remove(student)
                    new_class.students.add(student)
                    student.student_class = new_class.name
                    student.save()
                messages.success(request, f"{len(selected_ids)} student(s) moved to {new_class.name}.")

            return redirect('teacher:student_lists')

    return redirect('teacher:student_lists')



def bulk_delete_students(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_students')
        if selected_ids:
            deleted_count, _ = NewUser.objects.filter(
                id__in=selected_ids,
                school=request.user.school,
            ).exclude(student_class__isnull=True).exclude(student_class__exact='').delete()

            messages.success(request, f"{deleted_count} student(s) deleted successfully.")
        else:
            messages.warning(request, "No students selected for deletion.")
    
    return redirect('teacher:student_lists')

@login_required(login_url='teacher:teacher_login')
def edit_student(request, student_id):
    student = get_object_or_404(NewUser, id=student_id, school=request.user.school)
    all_classes = CourseGrade.objects.filter(schools=request.user.school, is_active=True)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        student_class_id = request.POST.get('student_class')

        # Update basic info
        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.gender = gender

        # Update class if changed
        if student_class_id:
            new_class = get_object_or_404(CourseGrade, id=student_class_id)
            old_classes = CourseGrade.objects.filter(students=student)
            for c in old_classes:
                c.students.remove(student)
            new_class.students.add(student)
            student.student_class = new_class.name

        student.save()
        messages.success(request, "Student information updated successfully.")
        return redirect('teacher:student_lists')

    context = {
        'student': student,
        'all_classes': all_classes,
    }
    return render(request, 'teacher/dashboard/edit_student.html', context)


def delete_student(request, student_id):
    student = get_object_or_404(NewUser, id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully.")
    return redirect('teacher:student_lists')




@login_required(login_url='teacher:teacher_login')
def edit_coursegrade_view(request, pk):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    course_grade = get_object_or_404(
        CourseGrade.objects.prefetch_related('students', 'subjects'),
        pk=pk,
        schools=user_school  # Ensures teachers can't access other schools' data
    )

    if request.method == 'POST':
        form = CourseGradeForm(request.POST, instance=course_grade, user_school=user_school)
        if form.is_valid():
            form.save()
            messages.success(request, "Course grade updated successfully.")
            # return redirect('teacher:examiner_dashboard')
    else:
        form = CourseGradeForm(instance=course_grade, user_school=user_school)

    context = {
        'form': form,
        'course_grade': course_grade,
    }

    return render(request, 'teacher/dashboard/edit_coursegrade.html', context)




@login_required(login_url='teacher:teacher_login')
def delete_coursegrade_view(request, pk):
    course_grade = get_object_or_404(
        CourseGrade.objects.prefetch_related('students', 'subjects'), 
        pk=pk)
    if request.method == 'POST':
        course_grade.delete()
        return redirect('teacher:examiner_dashboard')
    return render(request, 'teacher/dashboard/delete_coursegrade.html', {'course_grade': course_grade})



from .forms import CourseSelectionForm
from django.db.models import Q

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Teacher
from django.contrib import messages

def teacher_required(function=None, redirect_url='teacher:student-dashboard'):
    @login_required(login_url='teacher:teacher_login')
    def wrapper(request, *args, **kwargs):
        try:  
            # Check if the logged-in user is a teacher
            Teacher.objects.get(user=request.user)
            return function(request, *args, **kwargs)
        except Teacher.DoesNotExist:
            # If not a teacher, redirect to the student dashboard
            messages.error(request, "You do not have permission to view this page.")
            return redirect(redirect_url)
    return wrapper


@login_required(login_url='teacher:teacher_login')
@teacher_required
def examiner_start_exam(request):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # Get the existing Course instances that belong to the same school as the examiner
    # courses = Course.objects.filter(schools=user_school)
    courses = Course.objects.filter(
        Q(schools=user_school) | Q(course_name__schools=user_school)
    )

    context = {
        'courses': courses,  # Pass the queryset to the template
    }
    return render(request, 'teacher/dashboard/manage_exam.html', context)


from teacher.forms import SubjectsCreateForm

@teacher_required
def create_examiner_exam(request):
    # Get the current user's school
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # If the request method is POST, process the form data
    if request.method == 'POST':
        form = SubjectsCreateForm(request.POST, user_school=user_school)
        if form.is_valid():
            # Save the form but don't commit yet (to modify the instance)
            new_course = form.save(commit=False)
            # Set the user's school (if needed for the new exam creation)
            new_course.schools = user_school
            new_course.save()  # Save the new exam
            return redirect('teacher:manage_exam')  # Redirect after saving
    else:
        form = SubjectsCreateForm(user_school=user_school)
 
    context = {
        'form': form,
    }
    return render(request, 'teacher/dashboard/create_examiner_exam.html', context)


  
from .forms import CourseSelectionForm
from django.contrib.auth.decorators import login_required

@login_required(login_url='teacher:teacher_login')
def edit_examiner_exam(request, course_id):
    # Get the current user's school
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # Retrieve the course instance, ensuring it belongs to the user's school or related courses
    course = get_object_or_404(
    Course.objects.select_related('schools', 'course_name').filter(
        Q(schools=user_school) | Q(course_name__schools=user_school),
        id=course_id
            )
        )


    if request.method == 'POST':
        form = CourseSelectionForm(request.POST, instance=course, user_school=user_school)
        if form.is_valid():
            form.save()
            return redirect('teacher:manage_exam')  # Redirect after saving
    else:
        form = CourseSelectionForm(instance=course, user_school=user_school)

    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'teacher/dashboard/edit_examiner_exam.html', context)


@login_required(login_url='teacher:teacher_login')
def delete_examiner_exam(request, course_id):
    # Get the current user's school
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # Retrieve the course instance, ensuring it belongs to the user's school or related courses
    course = get_object_or_404(
        Course.objects.select_related('schools', 'course_name').filter(
            Q(schools=user_school) | Q(course_name__schools=user_school),
            id=course_id
        )
    )

    if request.method == 'POST':
        # Confirm deletion and delete the course
        course.delete()
        return redirect('teacher:manage_exam')  # Redirect to the exam management page after deletion

    context = {
        'course': course,
    }
    return render(request, 'teacher/dashboard/delete_examiner_exam.html', context)


# @login_required(login_url='teacher:teacher_login')
# def edit_examiner_exam(request, course_id):
#     # Get the current user's school
#     user = NewUser.objects.select_related('school').get(id=request.user.id)
#     user_school = user.school

#     # Get the course instance, ensuring it belongs to the user's school
#     course = get_object_or_404(
#         Course, id=course_id, schools=user_school)

#     if request.method == 'POST':
#         form = CourseSelectionForm(request.POST, instance=course, user_school=user_school)
#         if form.is_valid():
#             form.save()
#             return redirect('teacher:examiner_dashboard')  # Redirect after saving
#     else:
#         form = CourseSelectionForm(instance=course, user_school=user_school)

#     context = {
#         'form': form,
#         'course': course,
#     }
#     return render(request, 'teacher/dashboard/edit_examiner_exam.html', context)


from django.db.models import Avg, Max, Min, Count

from django.contrib.auth.decorators import login_required

@login_required(login_url='teacher:teacher_login')
def exam_list_view(request):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # Get all results filtered by the user's school
    courses_results = Result.objects.filter(exam__course_name__schools=user_school)

    # Extract unique courses from courses_results
    courses = Course.objects.filter(id__in=courses_results.values_list('exam__id', flat=True).distinct())

    # Get the selected course from the request (if any)
    selected_course_id = request.GET.get('course')
    selected_course = None
    filtered_courses_results = []

    if selected_course_id:
        selected_course = Course.objects.get(id=selected_course_id)
        # Filter results by the selected course
        filtered_courses_results = courses_results.filter(exam=selected_course)

        # Retrieve session and term based on selected course
        session_instance = selected_course.session
        term_instance = selected_course.term

        # Retrieve CA, Midterm, and Exam total marks
        ca_total_marks = Course.objects.filter(
            term=term_instance,
            session=session_instance,
            exam_type__name='CA'
        ).values('total_marks').first()
        ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0

        midterm_total_marks = Course.objects.filter(
            term=term_instance,
            session=session_instance,
            exam_type__name='MIDTERM'
        ).values('total_marks').first()
        midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0

        exam_total_marks = Course.objects.filter(
            term=term_instance,
            session=session_instance,
            exam_type__name='EXAM'
        ).values('total_marks').first()
        exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0

        # Add total marks calculation for each result
        for result in filtered_courses_results:
            # Query the CA, Midterm, and Exam marks for the student in the current course
            ca_marks = Result.objects.filter(
                student=result.student,
                exam__course_name=selected_course.course_name,
                exam__exam_type__name='CA',
                term=term_instance,
                session=session_instance
            ).values('marks').first()
            ca_marks = ca_marks['marks'] if ca_marks else 0

            midterm_marks = Result.objects.filter(
                student=result.student,
                exam__course_name=selected_course.course_name,
                exam__exam_type__name='MIDTERM',
                term=term_instance,
                session=session_instance
            ).values('marks').first()
            midterm_marks = midterm_marks['marks'] if midterm_marks else 0

            exam_marks = Result.objects.filter(
                student=result.student,
                exam__course_name=selected_course.course_name,
                exam__exam_type__name='EXAM',
                term=term_instance,
                session=session_instance
            ).values('marks').first()
            exam_marks = exam_marks['marks'] if exam_marks else 0

            # Calculate total marks based on CA, Midterm, and Exam marks
            if not midterm_marks and not exam_marks:
                result.total_marks = (ca_marks / ca_total_marks) * 100 if ca_total_marks > 0 else 0
            elif not exam_marks:
                result.total_marks = ((midterm_marks + ca_marks) / (ca_total_marks + midterm_total_marks)) * 100 if (ca_total_marks + midterm_total_marks) > 0 else 0
            else:
                total_weight = ca_total_marks + midterm_total_marks + exam_total_marks

                if total_weight > 0:
                    ca_weight = (ca_total_marks / total_weight) if ca_total_marks > 0 else 0
                    midterm_weight = (midterm_total_marks / total_weight) if midterm_total_marks > 0 else 0
                    exam_weight = (exam_total_marks / total_weight) if exam_total_marks > 0 else 0
                    
                    ca_percentage = ((ca_marks / ca_total_marks) * 100) if ca_total_marks > 0 else 0
                    midterm_percentage = ((midterm_marks / midterm_total_marks) * 100) if midterm_total_marks > 0 else 0
                    exam_percentage = ((exam_marks / exam_total_marks) * 100) if exam_total_marks > 0 else 0
                    
                    result.total_marks = (ca_percentage * ca_weight + midterm_percentage * midterm_weight + exam_percentage * exam_weight)
                else:
                    result.total_marks = 0

                # result.total_marks = (
                #     (ca_marks / ca_total_marks) * 100 * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                #     (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                #     (exam_marks / exam_total_marks) * 100 * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
                # ) if (ca_total_marks + midterm_total_marks + exam_total_marks) > 0 else 0


    # Data for visualization
    student_names = [f"{result.student.user.first_name} {result.student.user.last_name}" for result in filtered_courses_results]
    marks = [result.total_marks for result in filtered_courses_results]  # Use total_marks
    # print(filtered_courses_results, 'tot')

    context = {
        'courses': courses,
        'selected_course': selected_course,
        'total_students': len(filtered_courses_results),
        'average_score': round(sum(marks) / len(marks), 1) if marks else None,  # Rounded average of total marks

        # 'average_score': sum(marks) / len(marks) if marks else None,  # Average of total marks
        'highest_score': max(marks) if marks else None,  # Highest of total marks
        'lowest_score': min(marks) if marks else None,  # Lowest of total marks
        'courses_results': filtered_courses_results,
        'student_names': student_names,
        'marks': marks,
    }
    return render(request, 'teacher/dashboard/exam_list.html', context)

  
from sms.forms import CoursesForm

from django.contrib import messages  # Import the messages framework


#working
# @login_required(login_url='teacher:teacher_login')
# def add_course_view(request):
#     if request.method == 'POST':
#         form = CoursesForm(request.POST, user=request.user)  # Pass the user instance
#         if form.is_valid():
#             course = form.save(commit=False)
#             course.save()  # Save the course without saving schools yet

#             # Associate the course with the user's school
#             course.schools.add(request.user.school)  # Adjust this if necessary

#             # Add a success message
#             messages.success(request, 'Subject has been successfully added!')

#             return redirect('teacher:create_course_view')  # Replace with the name of the view to redirect to
#     else:
#         form = CoursesForm(user=request.user)  # Pass the user instance

#     context = {
#         'form': form,
#     }
#     return render(request, 'teacher/dashboard/exams_subjects.html', context)


@login_required
def add_course_view(request):
    if request.method == 'POST':
        form = CoursesForm(request.POST, user=request.user)
        if form.is_valid():
            # Save the Courses form
            courses_instance = form.save(commit=False)
            courses_instance.created_by = request.user
            courses_instance.save()
            courses_instance.schools.add(request.user.school)

            user = request.user
            if not hasattr(user, 'teacher'):
                messages.error(request, 'You are not assigned as a teacher yet.')
                return redirect('teacher:create_course_view')

            teacher = user.teacher

            # Check if Course instance already exists
            course_instance, created = Course.objects.get_or_create(
                course_name=courses_instance,
                session=courses_instance.session,
                term=courses_instance.term,
                schools=request.user.school,
                exam_type=courses_instance.exam_type,
                defaults={
                    'room_name': 'Some Room',  # You may update dynamically
                }
            )

            # Assign course to teacher if not already assigned
            if course_instance not in teacher.subjects_taught.all():
                teacher.subjects_taught.add(course_instance)
                messages.success(request, 'Subject has been successfully added and assigned to you!')
            else:
                messages.info(request, 'This course is already assigned to you.')

            return redirect('teacher:create_course_view')
    else:
        form = CoursesForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'teacher/dashboard/exams_subjects.html', context)


from django.db.models.signals import post_save
from django.dispatch import receiver
from quiz.models import Course
from teacher.models import Teacher  # Make sure the import is correct


from .forms import ResultForm  
  
@login_required(login_url='teacher:teacher_login')
def edit_result_view(request, result_id):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    # print(f"Attempting to edit Result ID: {result_id}")
    # print(f"User School: {user_school}")

    result = get_object_or_404(Result, id=result_id, exam__course_name__schools=user_school)

    # print(f"Found result: {result}")

    if request.method == 'POST':
        form = ResultForm(request.POST, instance=result, user_school=user_school)
        if form.is_valid():
            form.save()
            return redirect(reverse('teacher:exam_list'))
    else:
        form = ResultForm(instance=result, user_school=user_school)
    
    context = {
        'form': form,
        'result': result,
    }
    return render(request, 'teacher/dashboard/edit_result.html', context)


# @login_required(login_url='teacher:teacher_login')
# def edit_result_view(request, result_id):
#     user = NewUser.objects.select_related('school').get(id=request.user.id)
#     user_school = user.school

#     result = get_object_or_404(Result, id=result_id, exam__course_name__schools=user_school)
    
#     if request.method == 'POST':
#         form = ResultForm(request.POST, instance=result)
#         if form.is_valid():
#             form.save()
#             return redirect(reverse('teacher:exam_list'))
#     else:
#         form = ResultForm(instance=result)
    
#     context = {
#         'form': form,
#         'result': result,
#     }
#     return render(request, 'teacher/dashboard/edit_result.html', context)


from django.contrib import messages
from django.urls import reverse

@login_required(login_url='teacher:teacher_login')
def delete_result_view(request, result_id):
    result = get_object_or_404(Result, id=result_id, exam__course_name__schools=request.user.school)
    
    if request.method == 'POST':
        result.delete()
        messages.success(request, 'The result has been deleted successfully.')
        return redirect(reverse('teacher:exam_list'))
    
    context = {
        'result': result,
    }
    return render(request, 'teacher/dashboard/delete_result_confirm.html', context)



@login_required
def exam_statistics_view(request, course_id):
    course_results = Result.objects.filter(exam_id=course_id)

    statistics = {
        'average_score': course_results.aggregate(Avg('marks'))['marks__avg'],
        'max_score': course_results.aggregate(Max('marks'))['marks__max'],
        'min_score': course_results.aggregate(Min('marks'))['marks__min'],
        'total_students': course_results.count(),
        'pass_rate': (course_results.filter(marks__gte=pass_mark).count() / course_results.count()) * 100
    }

    context = {
        'statistics': statistics,
        'course': course_results.first().exam if course_results.exists() else None
    }
    return render(request, 'teacher/dashboard/exam_statistics.html', context)

from django.db.models.functions import Lower
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='teacher:teacher_login')
def teacher_course_results_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        selected_ids = request.POST.getlist('selected_results[]')  # note the []
        if selected_ids:
            count = Result.objects.filter(id__in=selected_ids).delete()[0]
            return JsonResponse({'status': 'success', 'deleted_count': count})
        return JsonResponse({'status': 'error', 'message': 'No results selected.'})

    results = (
        Result.objects
        .select_related('student', 'exam', 'term', 'session', 'exam_type')
        .filter(exam=course)
        .order_by(
            Lower('student__first_name').asc(nulls_last=True),
            Lower('student__last_name').asc(nulls_last=True)
        )
    )

    return render(request, 'teacher/dashboard/teacher_results_detail.html', {
        'course': course,
        'results': results,
    })



# @login_required(login_url='teacher:teacher_login')
# def teacher_course_results_view(request, course_id):
#     """Display all student results for a given course, ordered alphabetically by name."""
#     course = get_object_or_404(Course, id=course_id)

#     results = (
#         Result.objects
#         .select_related('student', 'exam', 'term', 'session', 'exam_type')
#         .filter(exam=course)
#         .order_by(Lower('student__first_name').asc(nulls_last=True), Lower('student__last_name').asc(nulls_last=True))

#     )
#     for r in Result.objects.order_by(Lower('student__first_name'), Lower('student__last_name')):
#         print(r.student.first_name, r.student.last_name)
        
#     return render(request, 'teacher/dashboard/teacher_results_detail.html', {
#         'course': course,
#         'results': results,
#     })


@login_required
def teacher_results_view(request):
    user = request.user

    try:
        teacher = Teacher.objects.select_related('user').get(user=user)
    except Teacher.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Get all courses this teacher teaches
    courses = teacher.subjects_taught.all()

    # Get selected course_id from query params
    course_id = request.GET.get('course_id')
    results = None
    selected_course = None

    if course_id:
        selected_course = get_object_or_404(Course, id=course_id, teachers=teacher)
        cache_key = f"teacher_results_{teacher.id}_course_{course_id}"
        results = cache.get(cache_key)

        if not results:
            results = Result.objects.select_related('exam', 'student', 'session', 'term', 'exam_type').filter(exam=selected_course)
            
            logger.info(f"Results cached for teacher {teacher.id} and course {course_id}")
        else:
            logger.info(f"Results fetched from cache for teacher {teacher.id} and course {course_id}")

    context = {
        'teacher': teacher,
        'courses': courses,
        'results': results,
        'selected_course': selected_course,
    }
    return render(request, 'teacher/dashboard/teacher_results.html', context)


@login_required(login_url='teacher:teacher_login')
def examiner_results_list_view(request):
    """List all available subjects (courses) that have results for the examiner's school."""
    user = request.user
    try:
        school = user.school  # assuming your NewUser model has school FK
    except AttributeError:
        return render(request, 'error_page.html', {'message': 'No school associated with your account.'})

    # Only show Courses linked to this examiner's school that have results
    courses = Course.objects.filter(schools=school, result__isnull=False).distinct().order_by('course_name')

    return render(request, 'teacher/dashboard/examiner_results_list.html', {
        'courses': courses,
        'school': school,
    })


@login_required(login_url='teacher:teacher_login')
def examiner_result_detail_view(request, course_id):
    """Show detailed results for a specific subject (course) within the examiner's school."""
    user = request.user
    try:
        school = user.school
    except AttributeError:
        return render(request, 'error_page.html', {'message': 'No school associated with your account.'})

    course = get_object_or_404(Course, id=course_id, schools=school)

    # Fetch all results for this course within the examiner’s school
    results = (
        Result.objects.filter(exam__course=course, schools=school)
        .select_related('student', 'term', 'session', 'exam_type')
        # .order_by('student__first_name', 'student__last_name')
    )

    return render(request, 'teacher/dashboard/examiner_result_detail.html', {
        'course': course,
        'results': results,
        'school': school,
    })




from .forms import ResultEditForm

@login_required
def edit_teacher_results_view(request, course_id, result_id):
    user = request.user

    # Verify teacher access
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Validate course
    course = get_object_or_404(Course, id=course_id)

    # Validate and fetch result
    result = get_object_or_404(Result, id=result_id, exam=course)

    # GET request - load form with result instance
    if request.method == 'GET':
        form = ResultEditForm(instance=result)

    # POST request - update the result
    elif request.method == 'POST':
        form = ResultEditForm(request.POST, instance=result)
        if form.is_valid():
            form.save()

            # Clear related cache
            cache_key = f"teacher_results_{teacher.id}_course_{course.id}"
            cache.delete(cache_key)

            messages.success(request, f"Result for {result.student.first_name} updated successfully.")
            return redirect('teacher:teacher_course_results', course_id=course.id)

    # Render the edit form template
    return render(request, 'teacher/dashboard/edit_teacher_results.html', {
        'teacher': teacher,
        'form': form,
        'result': result,
        'course': course,
    })


@login_required
def delete_teacher_result_view(request, course_id, result_id):
    user = request.user

    # Ensure the user is a teacher
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Validate course
    course = get_object_or_404(Course, id=course_id)

    # Check if the teacher teaches this course
    # if course not in teacher.subjects_taught.all():
    #     return render(request, 'error_page.html', {'message': 'Unauthorized access to this course.'})

    # Get the result to delete
    result_to_delete = get_object_or_404(Result, id=result_id, exam=course)

    # Delete the result
    result_to_delete.delete()

    # Clear the related cache
    cache_key = f"teacher_results_{teacher.id}_course_{course.id}"
    cache.delete(cache_key)

    # Redirect back to the course results view
    return redirect(reverse('teacher:teacher_course_results', args=[course.id]))



from quiz.admin import ResultResource
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


@require_cbt_subscription  
def export_results_csv(request):
    if request.method == 'POST':
        file_type = request.POST.get('file-type')
        selected_course_id = request.POST.get('course')

        try:
            # Attempt to retrieve the selected course
            selected_course = Course.objects.get(id=selected_course_id)

            # Fetch results associated with the selected course
            results = Result.objects.filter(exam__course_name=selected_course.course_name)
   
            # Use django-import-export for CSV
            result_resource = ResultResource()

            if file_type == 'csv':
                dataset = result_resource.export(results)
                response = HttpResponse(dataset.csv, content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'
                return response

            elif file_type == 'pdf':
                # Export to PDF
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="exam_results.pdf"'

                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []

                # Create table data
                data = [['Student Name', 'Exam Score', 'Exam Subject']]
                for result in results:
                    data.append([result.student, result.marks, result.exam.course_name])

                # Create table and add style
                table = Table(data)
                style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)])
                table.setStyle(style)

                elements.append(table)

                # Build PDF
                doc.build(elements)
                pdf = buffer.getvalue()
                buffer.close()
                response.write(pdf)
                return response

        except Course.DoesNotExist:
            return HttpResponse("Course does not exist.", status=404)

    else:
        user = request.user
        teacher = Teacher.objects.get(user=user)
        subjects_taught = teacher.subjects_taught.all()

        return render(request, 'teacher/dashboard/export_results.html', {'subjects_taught': subjects_taught})

    return redirect('export_results_csv')


 # Import your models
from .forms import UploadFileForm  
from tablib import Dataset

# Import logic  
from django.contrib import messages

@require_cbt_subscription
def import_results(request):
    if request.method == 'POST':
        # Check if it's a confirmation request (if 'confirm' is in POST)
        if 'confirm' in request.POST:
            # Retrieve the data from session
            preview_data = request.session.get('import_data')
            uploaded_file_content = request.session.get('uploaded_file')

            if preview_data and uploaded_file_content:
                dataset = Dataset()
                dataset.load(uploaded_file_content, format='csv')

                # Proceed with actual import now
                result_resource = ResultResource()

                try:
                    # Perform the import (no dry_run)
                    result = result_resource.import_data(dataset, dry_run=False)
                    return redirect('teacher:import-results')
                except Exception as e:
                    return HttpResponse(f"An error occurred during import: {str(e)}")
            else:
                return HttpResponse("No data to confirm import.")
        
        # Handle the first upload (preview step)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            result_resource = ResultResource()
            dataset = Dataset()

            try:
                # Load the dataset from the uploaded CSV file
                uploaded_file_content = uploaded_file.read().decode('utf-8')
                dataset.load(uploaded_file_content, format='csv')

                # Check if 'exam_course_name' is present and rename it to 'exam'
                if 'exam_course_name' in dataset.headers:
                    dataset.headers[dataset.headers.index('exam_course_name')] = 'exam'

                # Perform a dry run to test the import (no database changes yet)
                result = result_resource.import_data(dataset, dry_run=True)

                if not result.has_errors():
                    # Show a preview of the data before confirming import
                    preview_data = dataset.dict  # Convert dataset to list of dicts for preview

                    # Store the data and file in the session for confirmation later
                    request.session['import_data'] = preview_data
                    request.session['uploaded_file'] = uploaded_file_content

                    return render(request, 'teacher/dashboard/preview_import.html', {
                        'preview_data': preview_data
                    })
                else:
                    # Handle errors as before
                    error_messages = []
                    for row_num, error_details in result.row_errors():
                        for err in error_details:
                            field_name = getattr(err, 'field_name', 'Unknown field')
                            error_messages.append(f"Row {row_num}: {err} in field {field_name}")

                    return HttpResponse(f"Import failed due to errors: {', '.join(error_messages)}")

            except Exception as e:
                return HttpResponse(f"An error occurred during import: {str(e)}")
        else:
            return HttpResponse("Form is not valid.")
    else:
        form = UploadFileForm()

    return render(request, 'teacher/dashboard/import_results.html', {'form': form})
                 


def confirm_import(request):
    if request.method == 'POST':
        # Retrieve the stored data from session
        import_data = request.session.get('import_data', None)

        if import_data:
            dataset = Dataset()
            dataset.dict = import_data  # Load session data into the dataset

            # Perform the actual import (commit to database)
            result_resource = ResultResource()
            result = result_resource.import_data(dataset, dry_run=False)  # Now commit the data

            if not result.has_errors():
                # Clear session data after successful import
                del request.session['import_data']
                # Show a success message
                messages.success(request, "Results imported successfully.")
                return redirect('teacher:import-results')

    return redirect('teacher:import-results')

logger = logging.getLogger(__name__)

def tex_to_mathml(tex_input):
    try:
        if not tex_input:
            logger.warning("Received empty input for TeX to MathML conversion.")
            return tex_input

        logger.debug(f"Converting TeX input: {tex_input}")

        # Check if input is likely TeX
        if any(symbol in tex_input for symbol in ['$', '\\frac', '\\sqrt', '\\']):
            mathml_output = latex2mathml.converter.convert(tex_input)
            logger.debug(f"Converted MathML output: {mathml_output}")
            return mathml_output

        return tex_input

    except Exception as e:
        logger.error(f"Error converting TeX to MathML: {e}. Input: '{tex_input}'")
        return tex_input
    


# original codes
logger = logging.getLogger(__name__)

@require_cbt_subscription
@login_required(login_url='teacher:teacher_login')
def import_data(request):
    if request.method == 'POST':
        dataset = Dataset()
        new_file = request.FILES.get('myfile')

        if not new_file:
            messages.error(request, 'No file was uploaded. Please choose a file to import.')
            return redirect(request.path_info)

        # Check if the uploaded file format is supported
        allowed_formats = ['xlsx', 'xls', 'csv', 'docx']
        file_extension = new_file.name.split('.')[-1].lower()
        if file_extension not in allowed_formats:
            messages.error(request, 'File format not supported. Supported formats: XLSX, XLS, CSV, DOCX')
            return redirect(request.path_info)

        imported_data = None

        try:
            if file_extension == 'csv':
                # Handle CSV
                data = io.TextIOWrapper(new_file, encoding='utf-8')
                imported_data = dataset.load(data, format='csv')
            elif file_extension in ['xlsx', 'xls']:
                # Handle Excel files
                imported_data = dataset.load(new_file.read(), format=file_extension)
            elif file_extension == 'docx':
                # Handle Word documents
                document = Document(new_file)
                rows = []
                for table in document.tables:
                    for row in table.rows:
                        row_data = [tex_to_mathml(cell.text) for cell in row.cells]
                        rows.append(row_data)
                csv_data = io.StringIO()
                writer = csv.writer(csv_data)
                writer.writerows(rows)
                csv_data.seek(0)
                imported_data = dataset.load(csv_data, format='csv')
            else:
                messages.error(request, 'An error occurred while importing the file.')
                return redirect(request.path_info)

            # Convert TeX to MathML for imported data
            for row in imported_data.dict:
                for key in ['question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer']:
                    if key in row:
                        original_value = row[key]
                        if key == 'question' and original_value.endswith('?'):
                            processed_value = original_value[:-1].strip()
                        else:
                            processed_value = original_value

                        row[key] = tex_to_mathml(processed_value) + ('?' if key == 'question' else '')
                        logger.debug(f"Converted {key} from {original_value} to {row[key]}")

            resource = QuestionResource()
            result = resource.import_data(imported_data, dry_run=True)

            if result.has_errors():
                messages.error(request, "Errors occurred during import: {}".format(result.errors))
            else:
                result = resource.import_data(imported_data, dry_run=False)
                if result.has_errors():
                    messages.error(request, "Errors occurred during saving: {}".format(result.errors))
                else:
                    messages.success(request, "Data imported and saved successfully.")
                    logger.info("Data saved successfully.")

            return redirect(request.path_info)

        except Exception as e:
            messages.error(
                request,
                "You do not have permission to import this subject, or the subject name does not match your assigned subject. Please check the dashboard for your assigned subjects."
            )
            logger.error(f"An error occurred while processing the file: {e}")
            return redirect(request.path_info)

    return render(request, 'teacher/dashboard/import.html')





from docx import Document
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
import csv

# @cache_page(60 * 15)
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from docx import Document
import csv

logger = logging.getLogger(__name__)

def extract_equations_from_paragraph(paragraph):
    equations = []
    for run in paragraph.runs:
        if run._element.xpath('.//w:drawing'):
            equations.append(run.text.strip())
        else:
            equations.append(run.text.strip())
    return equations



from .forms import TeacherUpdateForm

from django.forms import modelformset_factory

@login_required(login_url='teacher:teacher_login')
def update_teacher_settings(request):
    teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught').get(user=request.user)

    if request.method == 'POST':
        # Update each subject's learning objectives and AI question number
        for subject in teacher.subjects_taught.all():
            learning_obj = request.POST.get(f'learning_objectives_{subject.id}')
            ai_num = request.POST.get(f'ai_question_num_{subject.id}')

            if learning_obj is not None:
                subject.learning_objectives = learning_obj

            if ai_num:
                try:
                    subject.ai_question_num = int(ai_num)
                except ValueError:
                    pass

            subject.save()

        messages.success(request, 'Subjects updated successfully!')
        return redirect('teacher:update_teacher_settings')

    subjects = teacher.subjects_taught.all()

    context = {
        'teacher': teacher,
        'subjects': subjects,
    }

    return render(request, 'teacher/dashboard/update_teacher_settings.html', context)





from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import os

import csv
import json

import html
from django.http import HttpResponse
from django.utils.timezone import now


def write_to_csv(data, file):
    writer = csv.writer(file)
    
    # Write the CSV header (column names) first
    headers = ["course", "marks", "question", "img_quiz", "option1", "option2", "option3", "option4", "answer"]
    writer.writerow(headers)

    # Iterate through each row in the data (JSON objects)
    for row in data:
        # Update the answer field based on the given option
        correct_option = row['answer'].upper()
        if correct_option == "A":
            row['answer'] = "Option1"
        elif correct_option == "B":
            row['answer'] = "Option2"
        elif correct_option == "C":
            row['answer'] = "Option3"
        elif correct_option == "D":
            row['answer'] = "Option4"

        # Ensure the data corresponds to the headers
        data_row = [
            row.get('course', ''),
            row.get('marks', ''),
            row.get('question', ''),
            row.get('img_quiz', ''),
            row.get('option1', ''),
            row.get('option2', ''),
            row.get('option3', ''),
            row.get('option4', ''),
            row.get('answer', '')
        ]
        
        # Write the row to the CSV file
        writer.writerow(data_row)


@require_cbt_subscription
@login_required(login_url='teacher:teacher_login')
def generate_csv(request):
    sample_codes = SampleCodes.objects.all()
    user_school = request.user.school

    # Optimize query to fetch related objects
    teacher = Teacher.objects.select_related('user', 'school').prefetch_related(
        'subjects_taught', 'classes_taught'
    ).get(user__username=request.user.username)

    # Prefetch subjects and retrieve additional teacher details
    teacher_subjects = teacher.subjects_taught.all()

    # Debugging (optional)
    for course in teacher_subjects:
        print(course.course_name, course.learning_objectives, course.ai_question_num)

    if request.method == 'POST':
        form = JSONForm(request.POST)
        if form.is_valid():
            # Parse JSON data
            json_data = form.cleaned_data['json_data']
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError:
                return render(request, 'teacher/dashboard/error.html', {'message': 'Invalid JSON data'})

            try:
                filename = f"generated_questions_{now().strftime('%Y%m%d%H%M%S')}.csv"
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                write_to_csv(data, response)
                return response
            except Exception as e:
                return render(request, 'teacher/dashboard/error.html', {'message': str(e)})

    else:
        form = JSONForm()

    context = {
        'school': user_school,
        'teacher_subjects': teacher_subjects,  # each subject now includes learning_objectives + ai_question_num
        'form1': form
    }

    return render(request, 'teacher/dashboard/generate_csv.html', context)



def download_csv(request):
    # Assuming the CSV file is generated and saved as 'generated_questions.csv'
    filename = 'generated_questions.csv'

    # Open the CSV file and read its contents
    with open(filename, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=' + filename
        return response
       

@require_cbt_subscription
@login_required
def export_data(request):
    if request.method == 'POST':
        try:
            selected_courses_ids = request.POST.getlist('courses')
            # print(f"Selected course IDs: {selected_courses_ids}")  # Debug selected course IDs
        except MultiValueDictKeyError:
            selected_courses_ids = []
            # print("No courses selected.")

        resource = QuestionResource()

        # Filter questions based on the selected course IDs
        queryset = Question.objects.filter(course__id__in=selected_courses_ids)
        # print(queryset)  # Debug the queryset

        dataset = resource.export(request=request, queryset=queryset)
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="questions.csv"'
        return response

    else:
        user = request.user
        # Get the teacher instance associated with the user
        teacher = Teacher.objects.get(user=user)
        # print(f"Teacher: {teacher}")  # Debug teacher instance

        # Fetch subjects taught by the teacher
        subjects_taught = teacher.subjects_taught.all()
        # print(f"Subjects taught: {subjects_taught}")  # Debug subjects taught

        # Fetch the courses that the teacher teaches (based on the subjects_taught)
        courses = Course.objects.filter(id__in=subjects_taught.values_list('id', flat=True)).distinct()
        # print(f"Courses fetched: {courses}")  # Debug courses
        
        # Render the export template with the courses
        return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})
      


def download_csv(request):
    # Assuming the CSV file is generated and saved as 'generated_questions.csv'
    filename = 'generated_questions.csv'

    # Open the CSV file and read its contents
    with open(filename, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=' + filename
        return response
    

def teacher_subjects_view(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    subjects = teacher.subjects_taught.all()  # M2M to Course
    
    context = {
        'subjects': subjects,
    }
    return render(request, 'teacher/dashboard/subjects_list.html', context)


def subject_questions_view(request, subject_id):
    subject = get_object_or_404(Course, id=subject_id)
    # Assuming your Question model has a ForeignKey to Course named 'course'
    questions = subject.question_set.all()  # or Question.objects.filter(course=subject)
    
    context = {
        'subject': subject,
        'questions': questions,
    }
    return render(request, 'teacher/dashboard/subject_questions.html', context)

  
# @cache_page(60 * 15)
def view_questions(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Redirect to login page or handle authentication
        return redirect('teacher:teacher_login')
    
    # Check if user is a teacher
    if not isinstance(request.user, AnonymousUser):
        # Get the teacher instance associated with the user
        try:
            # teacher = Teacher.objects.get(user=request.user)
             teacher = Teacher.objects.select_related('user', 'school').get(user=request.user)
            
        except Teacher.DoesNotExist:
            # Handle the case where the user is not a teacher
            return redirect('teacher:teacher_login')  # or any other appropriate action
    
  
    questions = Question.objects.filter(course__in=teacher.subjects_taught.all()).select_related('course').order_by('id')
  
    context = {
        'questions': questions,
        'teacher': teacher,  # Add teacher object
    }

    # Render the template with the questions
    return render(request, 'teacher/dashboard/view_questions.html', context)


# views.py
# @login_required(login_url='teacher:teacher_login')
# def view_questions(request):
#     teacher = get_object_or_404(Teacher, user=request.user)
#     questions = Question.objects.filter(course__in=teacher.subjects_taught.all()).order_by('id')
#     context = {
#         'questions': questions,
#         'teacher': teacher,
#         'selected_subject': None,
#     }
#     return render(request, 'teacher/dashboard/view_questions.html', context)


# @login_required(login_url='teacher:teacher_login')
# def subject_questions(request, subject_id):
#     teacher = get_object_or_404(Teacher.objects.select_related('user', 'school'), user=request.user)
#     course = get_object_or_404(teacher.subjects_taught, id=subject_id)
#     questions = Question.objects.filter(course=course).select_related('course').order_by('id')
#     context = {
#         'questions': questions,
#         'teacher': teacher,
#         'selected_subject': course,
#     }
#     return render(request, 'teacher/dashboard/view_questions.html', context)


# @login_required(login_url='teacher:teacher_login')
# def subject_questions(request, subject_id):
#     # Get the currently logged-in teacher
#     teacher = get_object_or_404(Teacher.objects.select_related('user', 'school'), user=request.user)

#     # Ensure the teacher teaches the selected subject
#     course = get_object_or_404(teacher.subjects_taught, id=subject_id)

#     # Get all questions for that course
#     questions = Question.objects.filter(course=course).select_related('course').order_by('id')

#     context = {
#         'questions': questions,
#         'teacher': teacher,
#         'selected_subject': course,
#     }

#     return render(request, 'teacher/dashboard/view_questions.html', context)


# @login_required(login_url='teacher:teacher_login')
# def subject_questions(request, subject_id):
#     teacher = get_object_or_404(Teacher.objects.select_related('user', 'school'), user=request.user)

#     # Ensure the teacher teaches the subject
#     course = get_object_or_404(teacher.subjects_taught, id=subject_id)

#     questions = Question.objects.filter(course=course).select_related('course').order_by('id')

#     context = {
#         'questions': questions,
#         'teacher': teacher,
#         'selected_subject': course,
#     }
#     return render(request, 'teacher/dashboard/view_questions.html', context)


@login_required
def edit_question(request, question_id):
    # Get the logged-in teacher
    teacher = get_object_or_404(Teacher, user=request.user)
    assigned_courses = teacher.subjects_taught.all()

    # Fetch the question only if it belongs to a course assigned to the teacher
    question = get_object_or_404(
        Question.objects.select_related('course').only(
            'id', 'course__course_name', 'question', 'img_quiz', 'marks',
            'option1', 'option2', 'option3', 'option4', 'answer'
        ).filter(course__in=assigned_courses),
        id=question_id
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES, instance=question, courses=assigned_courses)
        if form.is_valid():
            form.save()
            return redirect('teacher:view_questions')
    else:
        form = QuestionForm(instance=question, courses=assigned_courses)

    return render(request, 'teacher/dashboard/edit_questions.html', {'form': form})


#real view
# @cache_page(60 * 5)
# def edit_question(request, question_id):
#     # question = get_object_or_404(Question, id=question_id)
#     question = get_object_or_404(
#         Question.objects.select_related('course').only(
#             'id', 'course__course_name', 'question','img_quiz','marks', 'option1', 'option2', 'option3', 'option4', 'answer'
#         ),
#         id=question_id
#     )
#     if request.method == 'POST':
#         form = QuestionForm(request.POST, request.FILES,instance=question)
#         if form.is_valid():
#             form.save()
#             return redirect('teacher:view_questions')  # Redirect to the view questions page
#     else:
#         form = QuestionForm(instance=question)
#     return render(request, 'teacher/dashboard/edit_questions.html', {'form': form})



# @cache_page(60 * 5)
def delete_question_view(request, question_id):
    question = get_object_or_404(
        Question.objects.select_related('course').only(
            'id', 'course__id', 'course__course_name', 'question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer'
        ),
        id=question_id
    )

    if request.method == 'POST':
        subject_id = question.course.id  # Get the course/subject ID before deletion
        question.delete()
        return redirect('teacher:subject_questions', subject_id=subject_id)  # Redirect to subject-specific question list
    else:
        return render(request, 'teacher/dashboard/delete_question.html', {'question': question})
    

from django.contrib import messages
from django.views.decorators.http import require_POST

from django.shortcuts import redirect

@require_POST
def bulk_delete_questions_view(request):
    ids = request.POST.getlist('selected_questions')
    
    if ids:
        # Get the course ID from the first selected question to redirect properly
        first_question = Question.objects.filter(id__in=ids).first()
        subject_id = first_question.course.id if first_question else None

        Question.objects.filter(id__in=ids).delete()

        if subject_id:
            return redirect('teacher:subject_questions', subject_id=subject_id)

    # If no ID or subject found, fallback
    return redirect('teacher:view_questions')
