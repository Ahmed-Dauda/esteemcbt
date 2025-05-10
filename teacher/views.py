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
from .forms import JSONForm, TeacherSignupForm, TeacherLoginForm, QuestionForm, UploadCSVForm
from django.views.decorators.cache import cache_page
import csv
import json
from sms.models import Courses
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
from django.contrib import messages
from docx import Document
import latex2mathml.converter
from django.contrib.auth import authenticate, login
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from teacher import forms as QFORM
from quiz import models as QMODEL
from django.contrib import messages

@login_required(login_url='teacher:teacher_login')
def teacher_list_view(request):
    # Get the school of the logged-in user
    user_school = request.user.school

    # Filter teachers by school and prefetch related subjects and classes for optimization
    teachers = Teacher.objects.filter(school=user_school).prefetch_related('subjects_taught', 'classes_taught')

    # Print subjects taught for each teacher
    for teacher in teachers:
        # print(f"Teacher: {teacher.first_name} {teacher.last_name}")
        subjects = teacher.subjects_taught.all()
        # for subject in subjects:
        #     print(f"Subject Taught3: {subject.course_name}")
    
    context = {
        'subject_taught':subjects,
        'teachers': teachers,  # Pass the filtered teachers to the template
    }

    # Render the template and pass the context with teachers data
    return render(request, 'teacher/dashboard/teacher_list.html', context)


# @login_required(login_url='teacher:teacher_login')
# def teacher_list_view(request):
#     user_school = request.user.school  # Get the school of the logged-in user
#     teachers = Teacher.objects.filter(school=user_school)  # Filter teachers by school

#     context = {
#         'teachers': teachers,
#     }
#     return render(request, 'teacher/dashboard/teacher_list.html', context)


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
    print("Subjects Taught1:", form.initial['subjects_taught'])
    print("Classes Taught1:", form.initial['classes_taught'])

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


# def teacher_signup_view(request):
#     if request.method == 'POST':
#         form = TeacherSignupForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             email = form.cleaned_data.get('email')

#             if NewUser.objects.exclude(pk=form.instance.pk).filter(username=username).exists():
#                 form.add_error('username', "A user with this Username already exists.")
#             if NewUser.objects.exclude(pk=form.instance.pk).filter(email=email).exists():
#                 form.add_error('email', "A user with this Email already exists.")

#             if not form.errors:
#                 user = form.save(commit=False)
#                 form.save_teacher(user)
#                 return redirect('success_url')
# # Redirect to a success page or teacher list
#     else:
#         form = TeacherSignupForm()  # Provide an empty form for GET request

#     return render(request, 'teacher/dashboard/teacher_signup.html', {'form': form})

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

        context = {
            'school': user_school,
            'username': username,
            'teacher_class': teacher_class,
            'teacher_subjects': teacher_subjects,
        }
        return render(request, 'teacher/dashboard/teacher_dashboard.html', context=context)
    except Teacher.DoesNotExist:
        # Handle case where Teacher instance does not exist
        return redirect('account_login')


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

from quiz.models import Session, Term  # Import your models


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
from quiz.models import ExamType
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


# @cache_page(60 * 15)
@login_required(login_url='teacher:teacher_login')
def add_question_view(request):
    user = request.user

    # Get the teacher instance associated with the user
    try:
        teacher = Teacher.objects.select_related('user', 'school').get(user=user)
    except Teacher.DoesNotExist:
        return redirect('teacher_login')

    # Get the subjects taught by the teacher
    subjects_taught = teacher.subjects_taught.all()

    # Get the course names associated with the subjects taught by the teacher
    subjects_taught_titles = [course for course in subjects_taught]

    # Filter the courses based on the subjects taught
    courses = Course.objects.filter(course_name__title__in=subjects_taught_titles).prefetch_related('schools')

    # Create a formset with QuestionForm
    QuestionFormSet = formset_factory(QuestionForm, extra=1)
 
    if request.method == 'POST':
        formset = QuestionFormSet(request.POST, request.FILES)
        if formset.is_valid():
            for form in formset:
                if form.is_valid():
                    question = form.save(commit=False)
                    question.teacher = teacher  # Associate the question with the teacher
                    question.save()
            return redirect('teacher:add_question')  # Redirect to teacher dashboard after successfully adding questions
    else:
        # Pass the courses queryset to each form in the formset
        formset = QuestionFormSet(form_kwargs={'courses': courses})

    context = {
        'formset': formset,
        'subjects_taught': subjects_taught,
    }
    return render(request, 'teacher/dashboard/teacher_add_question.html', context)


# @login_required(login_url='teacher:teacher_login')
# def add_question_view(request):
#     # Retrieve the currently logged-in user
#     user = request.user

#     print('user', user)
#     # Get the teacher instance associated with the user
#     try:
#         # teacher = Teacher.objects.get(user=user)
#         teacher = Teacher.objects.select_related('user', 'school').only(
#                 'id', 'user__username', 'user__email', 'school__name',
#             ).get(user=user)
#     except Teacher.DoesNotExist:
#         # Redirect to some error page or handle the case where the user is not a teacher
#         return redirect('teacher_login')

#     # Get the subjects taught by the teacher
#     subjects_taught = teacher.subjects_taught.all()
#     print('subjects_taught', subjects_taught)

#     subjects_taught_titles = [course.course_name.title for course in subjects_taught]
#     print("subjects_taughty", subjects_taught_titles)
#     courses = Courses.objects.filter(title__in=subjects_taught_titles).prefetch_related('schools').only('id', 'title')
#     print('courses', courses)
    
#     # Create a formset with QuestionForm
#     QuestionFormSet = formset_factory(QuestionForm, extra=1)

#     if request.method == 'POST':
#         formset = QuestionFormSet(request.POST, request.FILES)
#         if formset.is_valid():
#             for form in formset:
#                 form.save()
#             return redirect('teacher:add_question')  # Redirect to teacher dashboard after successfully adding questions
#     else:
#         # Pass the courses queryset to each form in the formset
#         formset = QuestionFormSet(form_kwargs={'courses': courses})

#     context = {
#         'formset': formset,
#         'subjects_taught': subjects_taught,
#     }
#     return render(request, 'teacher/dashboard/teacher_add_question.html', context)



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
 
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # user = NewUser.objects.get(id=request.user.id)
        user = NewUser.objects.select_related('school').get(id=request.user.id)
        user_school = user.school
     
        # Filter CourseGrade objects based on the user's school
        course_grades = CourseGrade.objects.filter(
                students__school=user_school
            ).distinct().prefetch_related('students', 'subjects')
        
        context = {     
            'course_grades': course_grades,
        }

        return render(request, 'teacher/dashboard/examiner_dashboard.html', context)


from .forms import CourseGradeForm 


@login_required(login_url='teacher:teacher_login')
def edit_coursegrade_view(request, pk):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    course_grade = get_object_or_404(
        CourseGrade.objects.prefetch_related('students', 'subjects'), 
        pk=pk)
        
  
    print(course_grade.subjects, 'ttt')
    if request.method == 'POST':
        form = CourseGradeForm(request.POST, instance=course_grade, user_school=user_school)
        if form.is_valid():
            form.save()
            return redirect('teacher:examiner_dashboard')  # Redirect to the dashboard after saving
    else:
        form = CourseGradeForm(instance=course_grade, user_school=user_school)

    context = {
        'form': form

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

# @receiver(post_save, sender=Courses)
# def create_course_for_subject(sender, instance, created, **kwargs):
#     if created:
#         # Use the first school (assuming one school per teacher)
#         school = instance.schools.first()
        
#         # Create related Course
#         course = Course.objects.create(
#             course_name=instance,
#             schools=school,
#             session=instance.session,
#             term=instance.term,
#             exam_type=instance.exam_type,
#             question_number=0,
#             total_marks=0,
#         )
        
#         # Find the teacher for this school and current user
#         from django.contrib.auth import get_user_model
#         User = get_user_model()
        
#         teacher = Teacher.objects.filter(user__school=school, user=instance.created_by).first()
        
#         if teacher:
#             teacher.subjects_taught.add(course)


# @login_required(login_url='teacher:teacher_login')
# def exam_list_view(request):
#     user = NewUser.objects.select_related('school').get(id=request.user.id)
#     user_school = user.school

#     # Get all results filtered by the user's school
#     courses_results = Result.objects.filter(exam__course_name__schools=user_school)
    
#     # Extract unique courses from courses_results
#     courses = Course.objects.filter(id__in=courses_results.values_list('exam__id', flat=True).distinct())

#     # Get the selected course from the request (if any)
#     selected_course_id = request.GET.get('course')
#     selected_course = None
#     filtered_courses_results = []

#     if selected_course_id:
#         selected_course = Course.objects.get(id=selected_course_id)
#         # Filter results by the selected course
#         filtered_courses_results = courses_results.filter(exam=selected_course)

#     # Data for visualization
#     student_names = [f"{result.student.user.first_name} {result.student.user.last_name}" for result in filtered_courses_results]
#     marks = [result.marks for result in filtered_courses_results]

#     context = {
#         'courses': courses,
#         'selected_course': selected_course,
#         'total_students': len(filtered_courses_results),
#         'average_score': filtered_courses_results.aggregate(Avg('marks'))['marks__avg'] if filtered_courses_results else None,
#         'highest_score': filtered_courses_results.aggregate(Max('marks'))['marks__max'] if filtered_courses_results else None,
#         'lowest_score': filtered_courses_results.aggregate(Min('marks'))['marks__min'] if filtered_courses_results else None,
#         'courses_results': filtered_courses_results,
#         'student_names': student_names,
#         'marks': marks,
#     }
#     return render(request, 'teacher/dashboard/exam_list.html', context)


# @login_required(login_url='teacher:teacher_login')
# def exam_list_view(request):
#     user = NewUser.objects.select_related('school').get(id=request.user.id)
#     user_school = user.school

#     courses_results = Result.objects.filter(exam__course_name__schools=user_school)
#     print(courses_results)
#     # Data for visualization
#     student_names = [f"{result.student.user.first_name} {result.student.user.last_name}" for result in courses_results]
#     marks = [result.marks for result in courses_results]

#     context = {
#         'total_students': courses_results.count(),
#         'average_score': courses_results.aggregate(Avg('marks'))['marks__avg'],
#         'highest_score': courses_results.aggregate(Max('marks'))['marks__max'],
#         'lowest_score': courses_results.aggregate(Min('marks'))['marks__min'],
#         'courses_results': courses_results,
#         'student_names': student_names,
#         'marks': marks,
#     }
#     return render(request, 'teacher/dashboard/exam_list.html', context)


from .forms import ResultForm  
  
@login_required(login_url='teacher:teacher_login')
def edit_result_view(request, result_id):
    user = NewUser.objects.select_related('school').get(id=request.user.id)
    user_school = user.school

    print(f"Attempting to edit Result ID: {result_id}")
    print(f"User School: {user_school}")

    result = get_object_or_404(Result, id=result_id, exam__course_name__schools=user_school)

    print(f"Found result: {result}")

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



@login_required
def teacher_results_view(request):
    user = request.user

    # Check if the user is authenticated
    if not user.is_authenticated:
        return redirect('login')  # Redirect to login if user is not authenticated

    # Get the teacher instance associated with the user
    try:
        teacher = Teacher.objects.select_related('user').get(user=user)
    except Teacher.DoesNotExist:
        # Handle the case where the user is not a teacher
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Cache key for the teacher's results
    cache_key = f"teacher_results_{teacher.id}"
    results = cache.get(cache_key)

    if not results:
        # Get the subjects (Courses) taught by the teacher
        subjects_taught = teacher.subjects_taught.all()  # This should be related to the "Course" model

        # If you want to filter by `course_name`, extract the names:
        subjects_taught_titles = [course.course_name for course in subjects_taught]

        # Use actual Course instances in the filter
        results = Result.objects.select_related('exam', 'student').only(
                'id', 'marks', 'schools','exam__id', 'exam__course_name', 'student__id'
            ).filter(exam__course_name__in=subjects_taught_titles)
        
        # Cache the results for 5 minutes
        cache.set(cache_key, results, 60 * 1)
        logger.info(f"Results cached for teacher {teacher.id}")
    else:
        logger.info(f"Results fetched from cache for teacher {teacher.id}")

    context = {
        'teacher': teacher,
        'results': results,
    }
    return render(request, 'teacher/dashboard/teacher_results.html', context)


from .forms import ResultEditForm

@login_required
def edit_teacher_results_view(request, result_id):
    user = request.user

    # Ensure the user is a teacher
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Fetch the specific result to be edited
    result = get_object_or_404(Result, id=result_id)

    # Check if the teacher is allowed to edit this result (e.g., if the result is for one of the teacher's subjects)
    if result.exam.course_name not in [course.course_name for course in teacher.subjects_taught.all()]:
        return render(request, 'error_page.html', {'message': 'You are not authorized to edit this result.'})

    # Initialize the form with the current data if it's a GET request
    if request.method == 'GET':
        form = ResultEditForm(instance=result)

    # Handle form submission
    if request.method == 'POST':
        form = ResultEditForm(request.POST, instance=result)
        if form.is_valid():
            # Save the updated result
            form.save()

            # Show success message
            messages.success(request, f"Result for {result.student} updated successfully!")

            # Clear the cache for the teacher's results to refresh the data
            cache_key = f"teacher_results_{teacher.id}"
            cache.delete(cache_key)

            # Redirect back to the teacher's result page after updating
            return redirect('teacher:teacher_results')

    # Render the edit result page with the form
    context = {
        'teacher': teacher,
        'form': form,
        'result': result,
    }
    return render(request, 'teacher/dashboard/edit_teacher_results.html', context)


def delete_teacher_result_view(request, result_id):
    user = request.user

    # Ensure the user is a teacher
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Get the result to be deleted
    result_to_delete = get_object_or_404(Result, id=result_id)

  
    # Delete the result
    result_to_delete.delete()

    # Cache key for the teacher's results
    cache_key = f"teacher_results_{teacher.id}"

    # Delete the cached results
    cache.delete(cache_key)

    # Redirect back to the results page
    return redirect(reverse('teacher:teacher_results'))  # Use the correct view name


# @login_required
# def teacher_results_view(request):
#     user = request.user

#     # Check if the user is authenticated
#     if not user.is_authenticated:
#         return redirect('login')  # Redirect to login if user is not authenticated

#     # Get the teacher instance associated with the user
#     try:
#         # teacher = Teacher.objects.get(user=user)
#         teacher = Teacher.objects.select_related('user').get(user=user)
#     except Teacher.DoesNotExist:
#         # Handle the case where the user is not a teacher
#         return render(request, 'error_page.html', {'message': 'You are not a teacher'})

#     # Cache key for the teacher's results
#     cache_key = f"teacher_results_{teacher.id}"
#     results = cache.get(cache_key)
    
#     if not results:
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()
#         subjects_taught_titles = [course for course in subjects_taught]
        
#         # Retrieve the results associated with the subjects taught by the teacher
#         # results = Result.objects.filter(exam__course_name__in=subjects_taught_titles)
#         # Optimize the query with select_related and only for Result
#         results = Result.objects.select_related('exam', 'student').only(
#                 'id', 'marks','exam__id', 'exam__course_name','student__id',
#             ).filter(exam__course_name__in=subjects_taught_titles)
            
        
#         # Cache the results for 15 minutes
#         cache.set(cache_key, results, 60 * 5)
#         logger.info(f"Results cached for teacher {teacher.id}")
#     else:
#         logger.info(f"Results fetched from cache for teacher {teacher.id}")

#     context = {
#         'teacher': teacher,
#         'results': results,
#     }
#     return render(request, 'teacher/dashboard/teacher_results.html', context)


# @login_required
# def teacher_results_view(request):
#     user = request.user

#     # Check if the user is authenticated
#     if not user.is_authenticated:
#         return redirect('login')  # Redirect to login if user is not authenticated

#     # Get the teacher instance associated with the user
#     try:
#         teacher = Teacher.objects.get(user=user)
#     except Teacher.DoesNotExist:
#         # Handle the case where the user is not a teacher
#         return render(request, 'error_page.html', {'message': 'You are not a teacher'})

#     # Get the subjects taught by the teacher
#     subjects_taught = teacher.subjects_taught.all()
    
#     subjects_taught_titles = [course.course_name for course in subjects_taught]
#     print("subjects_taught66", subjects_taught_titles)
    
#     # Retrieve the results associated with the subjects taught by the teacher
#     results = Result.objects.filter(exam__course_name__in=subjects_taught_titles)
#     print('results', results)

#     context = {
#         'teacher': teacher,
#         'results': results,
#     }
#     return render(request, 'teacher/dashboard/teacher_results.html', context)


# @cache_page(60 * 15)
# def teacher_results_view(request):
#     # Retrieve the currently logged-in user
#     user = request.user

#     # Get the teacher instance associated with the user
#     try:
#         teacher = Teacher.objects.get(user=user)
#     except Teacher.DoesNotExist:
#         # Handle the case where the user is not a teacher
#         # Redirect to an error page or return an appropriate response
#         return render(request, 'error_page.html', {'message': 'You are not a teacher'})

#     # Get the subjects taught by the teacher
#     subjects_taught = teacher.subjects_taught.all()
    
#     subjects_taught_titles = [course.course_name for course in subjects_taught]
#     print("subjects_taught66", subjects_taught_titles)
#     # Retrieve the results associated with the subjects taught by the teacher
#     results = Result.objects.filter(exam__course_name__in=subjects_taught_titles)
#     print('results', results)

#     context = {
#         'teacher': teacher,
#         'results': results,
#     }
#     return render(request, 'teacher/dashboard/teacher_results.html', context)



from quiz.admin import ResultResource
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


  
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


from quiz.models import Session, Term  # Import your models
from .forms import UploadFileForm  
from tablib import Dataset

# Import logic  
from django.contrib import messages

# def import_results(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             uploaded_file = request.FILES['file']
#             result_resource = ResultResource()
#             dataset = Dataset()
#             try:
#                 dataset.load(uploaded_file.read().decode('utf-8'), format='csv')

#                 # Check if 'exam_course_name' is present and rename it to 'exam'
#                 if 'exam_course_name' in dataset.headers:
#                     dataset.headers[dataset.headers.index('exam_course_name')] = 'exam'

#                 # Perform a dry run to test the import
#                 result = result_resource.import_data(dataset, dry_run=True)

#                 if not result.has_errors():
#                     result_resource.import_data(dataset, dry_run=False)
                    
#                     # Add success message
#                     messages.success(request, 'Results imported successfully!')
                    
#                     return redirect("teacher:import-results")
#                 else:
#                     # Handle errors as before
#                     error_messages = []
#                     for row_num, error_details in result.row_errors():
#                         for err in error_details:
#                             field_name = getattr(err, 'field_name', 'Unknown field')
#                             error_messages.append(f"Row {row_num}: {err} in field {field_name}")
                    
#                     return HttpResponse(f"Import failed due to errors: {', '.join(error_messages)}")
#             except Exception as e:
#                 return HttpResponse(f"An error occurred during import: {str(e)}")
#         else:
#             return HttpResponse("Form is not valid.")
#     else:
#         form = UploadFileForm()

#     return render(request, 'teacher/dashboard/import_results.html', {'form': form})

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

# @cache_page(60 * 15)
# def export_results_csv(request):
#     if request.method == 'POST':
#         file_type = request.POST.get('file-type')
#         selected_course_id = request.POST.get('course')

#         try:
#             # Attempt to retrieve the selected course
#             selected_course = Course.objects.get(course_name__id=selected_course_id)
#             # print(f"Retrieved Course: {selected_course}")  # Debugging print

#             # Fetch results associated with the selected course
#             results = Result.objects.filter(exam=selected_course)

#             if file_type == 'csv':
#                 # Export to CSV
#                 response = HttpResponse(content_type='text/csv')
#                 response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'

#                 writer = csv.writer(response)
#                 writer.writerow(['Student Name', 'Exam Score', 'Exam Subject'])

#                 for result in results:
#                     writer.writerow([result.student, result.marks, result.exam.course_name])

#                 return response

#             elif file_type == 'pdf':
#                 # Export to PDF
#                 response = HttpResponse(content_type='application/pdf')
#                 response['Content-Disposition'] = 'attachment; filename="exam_results.pdf"'

#                 buffer = BytesIO()
#                 doc = SimpleDocTemplate(buffer, pagesize=letter)
#                 elements = []

#                 # Create table data
#                 data = [['Student Name', 'Exam Score', 'Exam Subject']]
#                 for result in results:
#                     data.append([result.student, result.marks, result.exam.course_name])

#                 # Create table and add style
#                 table = Table(data)
#                 style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                                     ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                                     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                                     ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                                     ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                                     ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                                     ('GRID', (0, 0), (-1, -1), 1, colors.black)])
#                 table.setStyle(style)

#                 elements.append(table)

#                 # Build PDF
#                 doc.build(elements)
#                 pdf = buffer.getvalue()
#                 buffer.close()
#                 response.write(pdf)
#                 return response

#         except Course.DoesNotExist:
            
#             return HttpResponse("Course does not exist.", status=404)

#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         teacher = Teacher.objects.get(user=user)
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()

#         return render(request, 'teacher/dashboard/export_results.html', {'subjects_taught': subjects_taught})

#     return redirect('export_results_csv')



# def export_results_csv(request):
#     if request.method == 'POST':
#         file_type = request.POST.get('file-type')
#         selected_course_id = request.POST.get('course')

#         # Retrieve the selected course object
#         # selected_course = Course.objects.get(id=selected_course_id)
#         selected_course = Course.objects.select_related('schools', 'course_name').only(
#                 'id', 'room_name', 'schools__id', 'schools__name', 'course_name__id', 'course_name__title',
#                 'question_number', 'course_pay', 'total_marks', 'num_attemps', 'show_questions', 'duration_minutes'
#             ).get(id=selected_course_id)

#         # results = Result.objects.filter(exam=selected_course)
#         results = Result.objects.select_related('exam', 'student').only(
#                 'id', 'marks', 'date', 'created', 'updated',
#                 'exam__id', 'exam__course_name', 'exam__room_name',
#                 'student__id', 'student__first_name', 'student__last_name'
#             ).filter(exam=selected_course)


#         if file_type == 'csv':
#             # Export to CSV
#             response = HttpResponse(content_type='text/csv')
#             response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'

#             writer = csv.writer(response)
#             writer.writerow(['Student Name', 'Exam Score', 'Exam Subject'])

#             for result in results:
#                 writer.writerow([result.student, result.marks, result.exam.course_name])

#             return response

#         elif file_type == 'pdf':
#             # Export to PDF
#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="exam_results.pdf"'

#             buffer = BytesIO()
#             doc = SimpleDocTemplate(buffer, pagesize=letter)
#             elements = []

#             # Create table data
#             data = [['Student Name', 'Exam Score', 'Exam Subject']]
#             for result in results:
#                 data.append([result.student, result.marks, result.exam.course_name])

#             # Create table and add style
#             table = Table(data)
#             style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                                 ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                                 ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                                 ('GRID', (0, 0), (-1, -1), 1, colors.black)])
#             table.setStyle(style)

#             elements.append(table)

#             # Build PDF
#             doc.build(elements)
#             pdf = buffer.getvalue()
#             buffer.close()
#             response.write(pdf)
#             return response

#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         teacher = Teacher.objects.get(user=user)
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()

#         return render(request, 'teacher/dashboard/export_results.html', {'subjects_taught': subjects_taught})

#     return redirect('export_results_csv')




# def tex_to_mathml(tex_input):
#     try:
#         # Log the input being converted
#         logger.debug(f"Converting TeX input: {tex_input}")
#         # Attempt to convert only if input likely contains TeX
#         if '$' in tex_input or '\\' in tex_input:
#             mathml_output = latex2mathml.converter.convert(tex_input)
#             logger.debug(f"Converted MathML output: {mathml_output}")
#             return mathml_output
#         return tex_input
#     except Exception as e:
#         logger.error(f"Error converting TeX to MathML: {e}, Input: {tex_input}")
#         return tex_input  # If conversion fails, return the original TeX input

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
@login_required(login_url='teacher:teacher_login')
def import_data(request):
    if request.method == 'POST':
        dataset = Dataset()
        new_file = request.FILES['myfile']

        # Check if the uploaded file format is supported
        allowed_formats = ['xlsx', 'xls', 'csv', 'docx']
        file_extension = new_file.name.split('.')[-1]
        if file_extension not in allowed_formats:
            messages.error(request, 'File format not supported. Supported formats: XLSX, XLS, CSV, DOCX')
            return redirect(request.path_info)

        imported_data = None

        try:
            if file_extension == 'csv':
                # Handle CSV
                data = io.TextIOWrapper(new_file, encoding='utf-8')
                imported_data = dataset.load(data, format=file_extension)
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
                        # Handle the question mark for MathML questions
                        if key == 'question' and original_value.endswith('?'):
                            # Remove the question mark before conversion
                            processed_value = original_value[:-1].strip()
                        else:
                            processed_value = original_value

                        row[key] = tex_to_mathml(processed_value) + ('?' if key == 'question' else '')  # Add question mark back if it was a question
                        logger.debug(f"Converted {key} from {original_value} to {row[key]}")

            resource = QuestionResource()
            result = resource.import_data(imported_data, dry_run=True)  # Dry run first

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
            messages.error(request, "You do not have permission to import this subject, or the subject name does not match your assigned subject. Please check the dashboard for your assigned subjects.")
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


def import_word(request):
    if request.method == 'POST':
        allowed_formats = ['docx']
        uploaded_file = request.FILES.get('myfile')

        if not uploaded_file:
            messages.error(request, 'No file uploaded.')
            return render(request, 'teacher/dashboard/importdocs.html')

        file_extension = uploaded_file.name.split('.')[-1]
        if file_extension.lower() not in allowed_formats:
            messages.error(request, 'File format not supported. Supported format: DOCX')
            return render(request, 'teacher/dashboard/importdocs.html')

        try:
            document = Document(uploaded_file)
            questions = []

            for table_idx, table in enumerate(document.tables):
                for row_idx, row in enumerate(table.rows):
                    question_data = [cell.text.strip() for cell in row.cells]

                    if len(question_data) >= 8:  # Ensure there are enough data fields
                        equations = []
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                equations.extend(extract_equations_from_paragraph(paragraph))

                        if equations:  # Check if any equations were found
                            question = Question(
                                course=question_data[0],
                                marks=int(question_data[1]),
                                question_text=question_data[2],
                                option1=question_data[3],
                                option2=question_data[4],
                                option3=question_data[5],
                                option4=question_data[6],
                                answer=question_data[7],
                                equations=', '.join(equations)  # Store equations
                            )
                            question.save()
                            questions.append(question_data)
                        else:
                            logger.warning(f"No equations found for table {table_idx + 1}, row {row_idx + 1}.")

                    else:
                        messages.warning(request, f"Ignored invalid line in table {table_idx + 1}, row {row_idx + 1}: {', '.join(question_data)}")

            if questions:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="imported_questions.csv"'

                writer = csv.writer(response)
                writer.writerow(['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer', 'equations'])

                for question in questions:
                    writer.writerow(question)

                messages.success(request, "Data imported and saved successfully.")
                return response
            else:
                messages.warning(request, "No valid data found in the document.")

        except Exception as e:
            messages.error(request, f"An error occurred while processing the file: {str(e)}")
            logger.error(f"Error processing file: {str(e)}")
            return render(request, 'teacher/dashboard/importdocs.html')

    return render(request, 'teacher/dashboard/importdocs.html')



# def import_word(request):
#     if request.method == 'POST':
#         # Check if the uploaded file format is supported
#         allowed_formats = ['docx']
#         uploaded_file = request.FILES.get('myfile')
#         if not uploaded_file:
#             return HttpResponse('No file uploaded.')

#         file_extension = uploaded_file.name.split('.')[-1]
#         if file_extension not in allowed_formats:
#             return HttpResponse('File format not supported. Supported format: DOCX')

#         # Handle Word document file
#         document = Document(uploaded_file)
#         questions = []

#         for table_idx, table in enumerate(document.tables):
#             for row_idx, row in enumerate(table.rows):
#                 question = [cell.text.strip() for cell in row.cells]
#                 if len(question) == 9:  # Assuming answer is included
#                     questions.append(question)
#                 else:
#                     messages.warning(request, f"Ignored invalid line in table {table_idx + 1}, row {row_idx + 1}: {', '.join(question)}")

#         if questions:
#             # Create CSV content
#             response = HttpResponse(content_type='text/csv')
#             response['Content-Disposition'] = 'attachment; filename="imported_questions.csv"'

#             writer = csv.writer(response)
#             # writer.writerow(['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer'])

#             for question in questions:
#                 writer.writerow(question)

#             messages.success(request, "Data imported successfully.")
            
#             return response
#         else:
#             messages.warning(request, "No valid data found in the document.")

#     return render(request, 'teacher/dashboard/importdocs.html')


from .forms import TeacherUpdateForm

def update_teacher_settings(request):
    teacher = Teacher.objects.select_related('user', 'school').get(user__username=request.user.username)

    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher settings updated successfully!')
            return redirect('teacher:update_teacher_settings')  # Redirect to the same page to see changes
    else:
        form = TeacherUpdateForm(instance=teacher)

    context = {
        'form': form,
        'teacher': teacher,
    }

    return render(request, 'teacher/dashboard/update_teacher_settings.html', context)




from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import os

import csv
import json
# def write_to_csv(data, filename):
#     with open(filename, 'w', newline='') as csvfile:
#         fieldnames = ['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
        
#         for response in data:
#             row = {
#                 'course': response.get('course', ''),
#                 'marks': response.get('marks', ''),
#                 'question': response.get('question', ''),
#                 'img_quiz': response.get('img_quiz', ''),
#                 'option1': response.get('option1', '').strip('"'),
#                 'option2': response.get('option2', '').strip('"'),
#                 'option3': response.get('option3', '').strip('"'),
#                 'option4': response.get('option4', '').strip('"'),
#                 'answer': response.get('answer', '')
#             }
            
#             correct_option = row['answer'].upper()
#             if correct_option == "A":
#                 row['answer'] = "Option1"
#             elif correct_option == "B":
#                 row['answer'] = "Option2"
#             elif correct_option == "C":
#                 row['answer'] = "Option3"
#             elif correct_option == "D":
#                 row['answer'] = "Option4"
            
#             writer.writerow(row)



from django.utils.timezone import now

import json
import csv
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


def generate_csv(request):
    sample_codes = SampleCodes.objects.all()

    user_school = request.user.school
    
    # Optimize query to fetch related objects
    teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught', 'classes_taught').get(user__username=request.user.username)
    
    # Prefetch subjects and retrieve additional teacher details
    teacher_subjects = teacher.subjects_taught.all()
    ai_question_num = teacher.ai_question_num
    learning_objectives = teacher.learning_objectives


    if request.method == 'POST':
        form = JSONForm(request.POST)
        if form.is_valid():
            # Parse JSON data
            json_data = form.cleaned_data['json_data']
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError:
                return render(request, 'teacher/dashboard/error.html', {'message': 'Invalid JSON data'})

            # Generate CSV
            try:
                # Create a dynamic filename with a timestamp
                filename = f"generated_questions_{now().strftime('%Y%m%d%H%M%S')}.csv"
                
                # Prepare the response with appropriate CSV headers
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                # Write CSV data to the response
                write_to_csv(data, response)
                return response
            except Exception as e:
                return render(request, 'teacher/dashboard/error.html', {'message': str(e)})

    else:
        form = JSONForm()
        
    # context =  {
    #         'form': form,
    #          'sample_codes': sample_codes
    #         }
    context = {
        'school': user_school,
        'teacher_subjects': teacher_subjects,
        'ai_question_num': ai_question_num,
        'learning_objectives': learning_objectives,
        'form1': form  # Include the JSON form
    }  
    return render(request, 'teacher/dashboard/generate_csv.html', context = context)



def download_csv(request):
    # Assuming the CSV file is generated and saved as 'generated_questions.csv'
    filename = 'generated_questions.csv'

    # Open the CSV file and read its contents
    with open(filename, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=' + filename
        return response
       

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
        print(queryset)  # Debug the queryset

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
        print(f"Courses fetched: {courses}")  # Debug courses
        
        # Render the export template with the courses
        return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})
      

# def export_data(request):
#     if request.method == 'POST':
#         try:
#             selected_courses_ids = request.POST.getlist('courses')
#         except MultiValueDictKeyError:
#             # Handle the case when 'courses' key is not found in the POST data
#             selected_courses_ids = []

#         resource = QuestionResource()
#         # Query questions using the selected course IDs
#         queryset = Question.objects.filter(course__id__in=selected_courses_ids)
#         print(queryset, 'queryset')
#         dataset = resource.export(request=request, queryset=queryset)
#         response = HttpResponse(dataset.csv, content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="questions.csv"'
#         return response
#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         teacher = Teacher.objects.get(user=user)
#         print(teacher, 'teacher')
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()
#         # Extract course IDs from the list of course objects
#         selected_courses_ids = [course.id for course in subjects_taught]
#         # Query courses using the extracted IDs
#         courses = Course.objects.filter(id__in=selected_courses_ids)
#         return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})


# def generate_csv(request):
#     user_school = request.user.school
    
#     # Optimize query to fetch related objects
#     teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught', 'classes_taught').get(user__username=request.user.username)
    
#     # Prefetch subjects and retrieve additional teacher details
#     teacher_subjects = teacher.subjects_taught.all()
#     ai_question_num = teacher.ai_question_num
#     learning_objectives = teacher.learning_objectives

#     # Handle JSON form submission for CSV generation
#     if request.method == 'POST':
#         form = JSONForm(request.POST)
#         if form.is_valid():
#             # Parse JSON data
#             json_data = form.cleaned_data['json_data']
#             try:
#                 data = json.loads(json_data)
#                 # Generate CSV
#                 write_to_csv(data, 'generated_questions.csv')
#             except json.JSONDecodeError:
#                 return render(request, 'teacher/dashboard/error.html', {'message': 'Invalid JSON data'})
#             except Exception as e:
#                 return render(request, 'teacher/dashboard/error.html', {'message': str(e)})

#             return render(request, 'teacher/dashboard/success.html')
#     else:
#         form = JSONForm()

#     # Prepare the context with teacher and form data
#     context = {
#         'school': user_school,
#         'teacher_subjects': teacher_subjects,
#         'ai_question_num': ai_question_num,
#         'learning_objectives': learning_objectives,
#         'form1': form  # Include the JSON form
#     }
      
#     # Render the template with the context
#     return render(request, 'teacher/dashboard/generate_csv.html', context)
    

# def export_data(request):
#     if request.method == 'POST':
#         try:
#             selected_courses_ids = request.POST.getlist('courses')
#         except MultiValueDictKeyError:
#             # Handle the case when 'courses' key is not found in the POST data
#             selected_courses_ids = []

#         resource = QuestionResource()
#         # Query questions using the selected course IDs
#         queryset = Question.objects.filter(course__id__in=selected_courses_ids)
        
#         dataset = resource.export(request=request, queryset=queryset)
#         response = HttpResponse(dataset.csv, content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="questions.csv"'
#         return response
#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         teacher = Teacher.objects.get(user=user)
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()
#         # Extract course IDs from the list of course objects
#         selected_courses_ids = [course.id for course in subjects_taught]
#         # Query courses using the extracted IDs
#         courses = Course.objects.filter(id__in=selected_courses_ids)
#         return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})


# @login_required
# def generate_csv(request):
#     sample_codes = SampleCodes.objects.all()
#     # Get the current user's username and school
#     user_school = request.user.school
#     try:
#         # Optimize query to fetch related objects without using only
#         teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught', 'classes_taught').get(user__username=request.user.username)
#         # Prefetch subjects and classes taught
#         teacher_subjects = teacher.subjects_taught.all()
#         # Retrieve ai_question_num
#         ai_question_num = teacher.ai_question_num
#         # Retrieve learning_objectives
#         learning_objectives = teacher.learning_objectives

#          # Handle the form submission for updating Teacher data
#         if request.method == 'POST':
#             form = TeacherUpdateForm(request.POST, instance=teacher)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, 'Teacher settings updated successfully!')
#                 return redirect('teacher:generate_csv')  # Redirect to the same page to see the changes
#         else:
#             form1 = TeacherUpdateForm(instance=teacher)

#         # Prepare context for the template
#         context = {
#             'school': user_school,
#             'teacher_subjects': teacher_subjects,
#             'sample_codes': sample_codes,
#             'ai_question_num':ai_question_num,
#             'learning_objectives':learning_objectives,
#             'form1': form1,  # Include the form in the context
#         }

#     except Teacher.DoesNotExist:
#         return render(request, 'teacher/dashboard/error.html', {'message': 'Teacher not found'})

#     if request.method == 'POST':
#         form = JSONForm(request.POST)
#         if form.is_valid():
#             # Parse JSON data
#             json_data = form.cleaned_data['json_data']
#             try:
#                 data = json.loads(json_data)
#             except json.JSONDecodeError:
#                 context['message'] = 'Invalid JSON data'
#                 return render(request, 'teacher/dashboard/error.html', context)

#             # Generate CSV
#             try:
#                 write_to_csv(data, 'generated_questions.csv')
#             except Exception as e:
#                 context['message'] = str(e)
#                 return render(request, 'teacher/dashboard/error.html', context)

#             return render(request, 'teacher/dashboard/success.html', context)
#     else:
#         form = JSONForm()

#     # Add form to context
#     context['form'] = form

#     return render(request, 'teacher/dashboard/generate_csv.html', context)



# def generate_csv(request):

#     sample_codes = SampleCodes.objects.all()
#     # print('sample',sample_codes)
#     if request.method == 'POST':
#         form = JSONForm(request.POST)
#         if form.is_valid():
#             # Parse JSON data
#             json_data = form.cleaned_data['json_data']
#             try:
#                 data = json.loads(json_data)
#             except json.JSONDecodeError:
#                 return render(request, 'teacher/dashboard/error.html', {'message': 'Invalid JSON data'})

#             # Generate CSV
#             try:
#                 write_to_csv(data, 'generated_questions.csv')
#             except Exception as e:
#                 return render(request, 'teacher/dashboard/error.html', {'message': str(e)})

#             return render(request, 'teacher/dashboard/success.html')
#     else:
#         form = JSONForm()
    
        
#     return render(request, 'teacher/dashboard/generate_csv.html', {'form': form, 'sample_codes':sample_codes})



def download_csv(request):
    # Assuming the CSV file is generated and saved as 'generated_questions.csv'
    filename = 'generated_questions.csv'

    # Open the CSV file and read its contents
    with open(filename, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=' + filename
        return response
    
# uu
# def export_data(request):
#     if request.method == 'POST':
#         try:
#             selected_courses_ids = request.POST.getlist('courses')
#         except MultiValueDictKeyError:
#             # Handle the case when 'courses' key is not found in the POST data
#             selected_courses_ids = []

#         resource = QuestionResource()
#         # Query questions using the selected course IDs
#         # queryset = Question.objects.filter(course__id__in=selected_courses_ids)
#         queryset = Question.objects.filter(course__id__in=selected_courses_ids).select_related('course').only(
#     'id', 'course__course_name', 'question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer'
# )
#         dataset = resource.export(request=request, queryset=queryset)
#         response = HttpResponse(dataset.csv, content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="questions.csv"'
#         return response
#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         # teacher = Teacher.objects.get(user=user)
#         teacher = Teacher.objects.select_related('user', 'school').only(
#                 'id', 'user__username', 'user__email', 'school__name',
#             ).get(user=user)

#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()
#         # Extract course IDs from the list of course objects
#         selected_courses_ids = [course.id for course in subjects_taught]
#         # Query courses using the extracted IDs
#         courses = Course.objects.filter(id__in=selected_courses_ids)

#         return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})


# def export_data(request):
#     if request.method == 'POST':
#         selected_courses = request.POST.getlist('courses')
#         resource = QuestionResource()
#         dataset = resource.export(request=request, queryset=Question.objects.filter(course__in=selected_courses))
#         response = HttpResponse(dataset.csv, content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="questions.csv"'
#         return response
#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         teacher = Teacher.objects.get(user=user)
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()
#         subjects_taught_titles = [course.course_name for course in subjects_taught]
#         print("subjects_taught66", subjects_taught_titles)
#         courses = Course.objects.filter(course_name = subjects_taught_titles)
#         print('cor',courses)
#         return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})



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
    
    # Filter questions based on the subjects taught by the teacher
    # questions = Question.objects.filter(course__in=teacher.subjects_taught.all())
  
    questions = Question.objects.filter(course__in=teacher.subjects_taught.all()).select_related('course').order_by('id')

    # print('q',questions)
    context = {
        'questions': questions
    }

    # Render the template with the questions
    return render(request, 'teacher/dashboard/view_questions.html', context)


# @cache_page(60 * 5)
def edit_question(request, question_id):
    # question = get_object_or_404(Question, id=question_id)
    question = get_object_or_404(
        Question.objects.select_related('course').only(
            'id', 'course__course_name', 'question','img_quiz','marks', 'option1', 'option2', 'option3', 'option4', 'answer'
        ),
        id=question_id
    )
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES,instance=question)
        if form.is_valid():
            form.save()
            return redirect('teacher:view_questions')  # Redirect to the view questions page
    else:
        form = QuestionForm(instance=question)
    return render(request, 'teacher/dashboard/edit_questions.html', {'form': form})



# @cache_page(60 * 5)
def delete_question_view(request, question_id):
    # question = get_object_or_404(Question, id=question_id)
    question = get_object_or_404(
        Question.objects.select_related('course').only(
            'id', 'course__course_name', 'question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer'
        ),
        id=question_id
    )
    if request.method == 'POST':
        # Handle form submission for deleting the question
        question.delete()
        return redirect('teacher:view_questions')  # Redirect to the teacher dashboard after deleting
    else:
        # Render a confirmation page before deleting the question
        return render(request, 'teacher/dashboard/delete_question.html', {'question': question})
    

