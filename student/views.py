from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.template import loader
from django.template.loader import get_template
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Max, Subquery, OuterRef, Count
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
import json

from datetime import datetime
from django.http import JsonResponse, HttpResponseForbidden
from .models import Payment, Profile, CertificatePayment, EbooksPayment

from pytz import timezone
# from inspect import signature
from datetime import datetime
from requests import delete
from datetime import date, timedelta
from sms.models import Categories, Courses
from student.models import PDFDocument, DocPayment
from sms.paystack import Paystack
from .models import Payment, Profile, CertificatePayment, EbooksPayment
from quiz import models as QMODEL
from teacher import models as TMODEL
from users.models import NewUser, Profile

from quiz.models import Result, Course
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
from django.views.decorators.cache import cache_page
from quiz.models import School
from teacher.models import Teacher,CourseGrade
from django.db.models import Min, Max, Avg, Sum
from django.db import models




# report card codes started
def calculate_grade(marks, school):
    if school.A_min <= marks <= school.A_max:
        return 'A'
    elif school.B_min <= marks <= school.B_max:
        return 'B'
    elif school.C_min <= marks <= school.C_max:
        return 'C'
    elif school.P_min <= marks <= school.P_max:
        return 'P'
    elif school.F_min <= marks <= school.F_max:
        return 'F'
    else:
        return 'Invalid Marks'  # In case the marks fall outside defined range
        

def ordinal(n):
    """Returns the ordinal number for a given integer."""
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = suffixes.get(n % 10, 'th')
    return f"{n}{suffix}"

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


@login_required
def report_card_list(request):
    # Get the currently logged-in student's profile
    student = request.user.profile  # Assuming a OneToOne relationship with Profile
  
    # Fetch distinct sessions and terms where the student has results
    report_cards = Result.objects.filter(student=student).select_related('session','term').values('session__name', 'term__name').distinct()

    context = {
        'report_cards': report_cards,
    }

    return render(request, 'student/dashboard/report_card_list.html', context)
     



from django.db.models import Max, Min, Avg, Sum

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Avg, Max, Min
from .models import Profile, NewUser, Result, Course


# working codes
from django.db.models import Sum, Q


@login_required
def generate_report_card(request, session, term):
    student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

    # Fetch the session and term instances
    session = get_object_or_404(Session, name=session)
    term = get_object_or_404(Term, name=term)

    results = Result.objects.filter(
        student=student,
        result_class=student.student_class,
        session=session,
        term=term,
    ).select_related('student').distinct()
  
    subject_total_scores = results.values('student').annotate(total_marks=Sum('marks')).order_by('-total_marks')
    if not results.exists():
        return render(request, 'student/dashboard/report_card.html', {'message': 'No results found for this session, term, and exam type.'})

    student_name = f"{student.first_name} {student.last_name}"
    # student_gender = newusers.gender
    student_gender = student.gender
    # student_admission_no = newusers.admission_no
    student_admission_no = student.admission_no
    student_class = student.user.student_class
    student_school = student.user.school

    profile_picture_url = student.user.pro_img.url if student.user.pro_img and hasattr(student.user.pro_img, 'url') else None
    # Get school logo URL
    school_logo_url = student_school.logo.url if student_school and student_school.logo and hasattr(student_school.logo, 'url') else None
    school_motto = student_school.school_motto if student_school else None
    
    school_address = student_school.school_address if student_school else None
    student_class_count = NewUser.objects.filter(student_class=student_class).count()
    
    grading_system = {
        'A': f"{student_school.A_min}-{student_school.A_max}",
        'B': f"{student_school.B_min}-{student_school.B_max}",
        'C': f"{student_school.C_min}-{student_school.C_max}",
        'P': f"{student_school.P_min}-{student_school.P_max}",
        'F': f"{student_school.F_min}-{student_school.F_max}",
    }
    
    grade_comments = {
        'A': student_school.A_comment,
        'B': student_school.B_comment,
        'C': student_school.C_comment,
        'P': student_school.P_comment,
        'F': student_school.F_comment
    }

    subject_grades = {}
    subject_comments = {}
    subject_positions = {}
    subject_statistics = {}
    # Initialize total marks and maximum possible marks
    total_marks_obtained = 0
    total_max_marks = 0


    for result in results:
        subject = result.exam.course_name
        # Calculate marks for CA, MIDTERM, and EXAM
        ca_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='CA').aggregate(Sum('marks'))['marks__sum'] or 0
        midterm_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session ,student=student, exam_type__name='MIDTERM').aggregate(Sum('marks'))['marks__sum'] or 0
        exam_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='EXAM').aggregate(Sum('marks'))['marks__sum'] or 0

        ca_total_marks = Course.objects.filter(
        term=term,
        session=session,
        exam_type__name='CA'
        ).values('total_marks').first()
        ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0  # Total possible marks for CA exam
        # print(ca_total_marks, 'ca_total_marks11')
       
        midterm_total_marks = Course.objects.filter(
        term=term,
        session=session,
        exam_type__name='MIDTERM'
            ).values('total_marks').first()

        midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0  # Total possible marks for MIDTERM exam
        # print(midterm_total_marks, 'midterm_total_marks')

        exam_total_marks = Course.objects.filter(
        term=term,
        session=session,
        exam_type__name='EXAM'
        ).values('total_marks').first()

        exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0  # Total possible marks for EXAM

        if not midterm_marks and not exam_marks:
            # Only CA marks are present
            if ca_total_marks > 0:  # Check if ca_total_marks is greater than zero
                total_marks = (ca_marks / ca_total_marks) * 100
            else:
                total_marks = 0  # Set to 0 or handle as needed if ca_total_marks is zero

        elif not exam_marks:
            # Only CA marks and midterm marks are present
            c_m = midterm_marks + ca_marks
            t_c_m = ca_total_marks + midterm_total_marks
            
            if t_c_m > 0:  # Check if the total of CA and midterm marks is greater than zero
                total_marks = round((c_m / t_c_m) * 100, 1)
            else:
                total_marks = 0  # Set to 0 or handle as needed if both totals are zero

        else:
            # All marks are present: CA, midterm, and exam
            total_marks = ca_total_marks + midterm_total_marks + exam_total_marks
           
            if total_marks > 0:  # Check if the total marks are greater than zero
                total_marks = (
                    (ca_marks / ca_total_marks) * 100 * (ca_total_marks / total_marks) +
                    (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / total_marks) +
                    (exam_marks / exam_total_marks) * 100 * (exam_total_marks / total_marks)
                )
            else:
                total_marks = 0  # Set to 0 or handle as needed if all total marks are zero

        total_marks_obtained += total_marks
        # print(total_marks_obtained, 'tmo')
        total_max_marks += result.exam.total_marks
        # print(total_max_marks, 'total_max_marks')
        grade = calculate_grade(total_marks, student.user.school)
        
        subject_statistics[subject] = {
            'CA': ca_marks,
            'MIDTERM': midterm_marks,
            'EXAM': exam_marks,
            'total_score': total_marks,
        }

        subject_grades[subject] = {
            'grade': grade,  # Assuming `grade` is calculated elsewhere
        }

        # Calculate the count of subjects from various dictionaries
        subject_count_statistics = len(subject_statistics)
        subject_inf = subject_statistics
        # Initialize the total marks obtained
        total_marks_obtaine = 0
        # Loop through the subjects in subject_inf and add the total score for each subject
        for student_subjects, stats in subject_inf.items():
            # print(stats, 'stats')
            total_marks_obtaine += stats['total_score']  # Add the 'total_score' for each subject
           

        subject_student_count = {}  # Dictionary to store the number of students offering each subject
  
        subject_total_marks = {}
        # Initialize a set to store unique total marks for all students across all subjects
        all_students_total_marks_set = []
        # Initialize variables to calculate the overall class average
        total_marks_all_subjects = 0
        total_students_all_subjects = 0
        # Dictionary to store each student's overall total marks and number of subjects they took
        student_total_marks = {}
        student_subject_count = {}
        # Dictionaries to store the highest and lowest marks per subject in the class
        highest_marks_in_class_per_subject = {}
        lowest_marks_in_class_per_subject = {}
        subject_statistics2 = {}
        

        for result in results:
            subject1 = result.exam.course_name
            print(subject1, 'subject1')

            # Calculate total marks for each student in the class for the specific subject
            students_total_marks = Result.objects.filter(
                exam__course_name=subject1,
                session=session,
                term=term,
                student__user__student_class=student_class
            ).values('student').annotate(
                ca_marks=Sum('marks', filter=Q(exam_type__name='CA')),
                midterm_marks=Sum('marks', filter=Q(exam_type__name='MIDTERM')),
                exam_marks=Sum('marks', filter=Q(exam_type__name='EXAM'))
            ) 

            # Count the number of students offering this subject
            subject_student_count[subject1] = students_total_marks.count()

            # Initialize a list for this subject
            subject_total_marks[subject1] = []

            for student_marks in students_total_marks:
                student_id = student_marks['student']
                
                # Get the marks for CA, Midterm, and Exam
                ca_marks = student_marks.get('ca_marks', 0) or 0
                midterm_marks = student_marks.get('midterm_marks', 0) or 0
                exam_marks = student_marks.get('exam_marks', 0) or 0
                
                # Fetch total possible marks
                ca_total_marks = Course.objects.filter(course_name = subject1,schools = request.user.school,term=term, session=session, exam_type__name='CA').values('total_marks').first()
                ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0

                midterm_total_marks = Course.objects.filter(course_name = subject1,schools = request.user.school,term=term, session=session, exam_type__name='MIDTERM').values('total_marks').first()
                midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0

                exam_total_marks = Course.objects.filter(course_name = subject1,schools = request.user.school,term=term, session=session, exam_type__name='EXAM').values('total_marks').first()
                exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0
                 
                # Calculate total marks
                if not midterm_marks and not exam_marks:
                    total_marks = (ca_marks / ca_total_marks) * 100 if ca_total_marks > 0 else 0
                elif not exam_marks:
                    c_m = midterm_marks + ca_marks
                    t_c_m = ca_total_marks + midterm_total_marks
                    total_marks = round((c_m / t_c_m) * 100, 1) if t_c_m > 0 else 0
                else:
                    total_marks = (
                        (ca_marks / ca_total_marks) * 100 * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                        (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                        (exam_marks / exam_total_marks) * 100 * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
                    ) if (ca_total_marks + midterm_total_marks + exam_total_marks) > 0 else 0

                subject_total_marks[subject1].append(total_marks)

                # Update the highest and lowest marks for the subject in the class
                if subject1 not in highest_marks_in_class_per_subject:
                    highest_marks_in_class_per_subject[subject1] = total_marks
                    lowest_marks_in_class_per_subject[subject1] = total_marks
                    # print(lowest_marks_in_class_per_subject, 'ca')
                else:
                    highest_marks_in_class_per_subject[subject1] = max(highest_marks_in_class_per_subject[subject1], total_marks)
                    lowest_marks_in_class_per_subject[subject1] = min(lowest_marks_in_class_per_subject[subject1], total_marks)

                # Add total marks to the global set for all students across all subjects
                
                all_students_total_marks_set.append(total_marks)

                # Add the calculated total_marks to the student_marks dictionary
                student_marks['total_marks'] = total_marks
               
                # Update the student's overall total marks and subject count
                if student_id not in student_total_marks:
                    student_total_marks[student_id] = total_marks
                    student_subject_count[student_id] = 1

                else:
                    student_total_marks[student_id] += total_marks
                    student_subject_count[student_id] += 1

                # Calculate the average marks for each subject
                subject_averages2 = {}

                for subject2, marks in subject_total_marks.items():
                    if len(marks) > 0:
                        subject_averages2[subject2] = sum(marks) / len(marks)
                    else:
                        subject_averages2[subject2] = 'N/A'

                # Populate the subject_statistics2 dictionary
                for subject2, marks in subject_total_marks.items(): 
                    subject_statistics2[subject2] = {
                        'average': subject_averages2.get(subject2, 'N/A'),
                        'lowest': lowest_marks_in_class_per_subject.get(subject2, 'N/A'),
                        'highest': highest_marks_in_class_per_subject.get(subject2, 'N/A'),
            
                    }


            # Update overall totals for class average calculation
            total_marks_all_subjects += sum(subject_total_marks[subject1])
            total_students_all_subjects += subject_student_count[subject1]
           
        # Convert the set back to a list
        all_students_total_marks = list(all_students_total_marks_set)
        sum_of_total_marks = sum(all_students_total_marks) / 2
        
        # Calculate the overall class average across all subjects
        if total_students_all_subjects > 0:
            overall_class_average = total_marks_all_subjects / total_students_all_subjects
            # print(f"Overall class average: {overall_class_average}")
        else:
            overall_class_average = 0
 
        student_averages = []
        for student_id, total_marks in student_total_marks.items():
            if student_subject_count[student_id] > 0:
                student_average = total_marks / student_subject_count[student_id]
                student_averages.append(student_average)

        # Find the highest and lowest averages
        if student_averages:
            highest_average_in_class = max(student_averages)
            lowest_average_in_class = min(student_averages)
            highest_average_in_class = highest_average_in_class
            lowest_average_in_class = lowest_average_in_class

        else:
            highest_average_in_class = 0
            lowest_average_in_class = 0

        # all_students_total_marks_subj = Result.objects.filter(
        #     exam__course_name=subject, 
        #     session = session,
        #     term= term,
        #     student__user__student_class=student_class
        # ).values('student').annotate(total_marks=Sum('marks'))
 
        all_students_total_marks_subj = Result.objects.filter(
            exam__course_name=subject, 
            session=session,
            term=term,
            student__user__student_class=student_class
        ).values('student').annotate(total_marks=Sum('marks'))

        # Sort the students by total marks in descending order
        sorted_marks = sorted(all_students_total_marks_subj, key=lambda x: x['total_marks'], reverse=True)

        # Initialize variables for ranking
        rank = 1
        last_total_marks = None
        rank_map = {}

        # Iterate over sorted marks and assign dense ranks
        for index, marks in enumerate(sorted_marks):
            if marks['total_marks'] != last_total_marks:
                rank = index + 1  # Update rank if the total marks are different
                last_total_marks = marks['total_marks']
            rank_map[marks['student']] = rank  # Assign dense rank to the student

        # Get the current student's subject position based on their rank
        subject_positions[subject] = rank_map.get(student.id, None)  
  
        # students_total_marks = sum(total_result.marks for total_result in total_results)
        class_average = sum_of_total_marks / student_class_count if student_class_count > 0 else 0
        final_grade = calculate_grade(total_marks_obtaine / subject_count_statistics, student.user.school)
        comment = grade_comments.get(grade, 'No comment available')
        subject_comments[subject] = comment

            # Calculate total marks for all students in the class
        all_students_total_marks = Result.objects.filter(
            session=session,
            term=term,
            student__user__student_class=student.student_class
        ).values('student').annotate(total_marks=Sum('marks')).order_by('-total_marks')

        # Calculate dense ranking
        sorted_marks = sorted(all_students_total_marks, key=lambda x: x['total_marks'], reverse=True)
        rank = 1
        last_total_marks = None
        rank_map = {}

        for index, marks in enumerate(sorted_marks):
            if marks['total_marks'] != last_total_marks:
                rank = index + 1  # Move to the next rank
                last_total_marks = marks['total_marks']
            rank_map[marks['student']] = rank  # Assign dense rank
            
         # Get the current student's final position
        final_position = rank_map.get(student.id, None)

    # end of student class position
    exam_types = Result.objects.filter(
        student=student, 
        session=session, 
        term=term
    ).only('exam_type__name').values('exam_type__name').distinct()


   
    context = {
    
        'grade_comments': grade_comments,
        'subject_statistics2': subject_statistics2,
         'highest_marks_in_class_per_subject': highest_marks_in_class_per_subject,
         'lowest_marks_in_class_per_subject': lowest_marks_in_class_per_subject,
        'overall_class_average':overall_class_average,
        'sum_of_total_marks': sum_of_total_marks,
        'subject_student_count':subject_student_count,
        # 'subject_grades1': subject_grades1,
        'ca_total_marks':ca_total_marks,
        'midterm_total_marks':midterm_total_marks,
        'exam_total_marks':exam_total_marks,
        'student': student,
        'session': session,
        'term': term,
        'exam_types': exam_types,
        'class_average': round(class_average, 2), 
        'student_name': student_name,
        'student_gender': student_gender,
        'student_admission_no': student_admission_no,
        'student_class': student_class,
        'student_school': student_school,
        'profile_picture': profile_picture_url,
        'school_logo_url': school_logo_url,  # Pass the logo URL to the templat
        'results': results,
        'subject_count_statistics': subject_count_statistics,
        # 'total_marks_obtained': total_marks_obtained,
        'total_marks_obtaine': total_marks_obtaine,
        'total_max_marks': total_max_marks,
        'school_motto': school_motto,
        'school_address': school_address,
        'student_averages1':round(total_marks_obtaine / subject_count_statistics, 1),
        'student_class_count': student_class_count,
        'grading_system': grading_system,
        'subject_statistics': subject_statistics,
        'subject_grades': subject_grades,
        'subject_positions': subject_positions,
        'subject_comments': subject_comments,
        # 'subj_class_averages': sub_class_averages,
        'final_position2': final_position,
        'final_grade': final_grade, 
        'highest_average_in_class': highest_average_in_class,
        'lowest_average_in_class': lowest_average_in_class,
        'subject_total_scores': subject_total_scores,
    }

    return render(request, 'student/dashboard/report_card.html', context)




# @login_required
# def generate_report_card(request, session, term):
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)
#     newusers = NewUser.objects.get(id=request.user.id)

    
#     results = Result.objects.filter(

#         student=student,
#         result_class=student.student_class,
#         session=session,
#         term=term,  
#     ).distinct()
   
            
#     subject_total_scores = results.values('student').annotate(total_marks=Sum('marks')).order_by('-total_marks')
#     # print(subject_total_scores, 'subject_total_scores')


#     if not results.exists():
#         return render(request, 'student/dashboard/report_card.html', {'message': 'No results found for this session, term, and exam type.'})

#     student_name = f"{student.first_name} {student.last_name}"
#     student_gender = newusers.gender
#     student_admission_no = newusers.admission_no
#     student_class = student.user.student_class
#     student_school = student.user.school

#     profile_picture_url = student.user.pro_img.url if student.user.pro_img and hasattr(student.user.pro_img, 'url') else None
#     school_motto = student_school.school_motto if student_school else None
#     school_address = student_school.school_address if student_school else None

#     student_class_count = NewUser.objects.filter(student_class=student_class).count()
    
#     total_results = Result.objects.filter(result_class=student.student_class, session=session, term=term)
#     students_total_marks = sum(total_result.marks for total_result in total_results)
#     class_average = students_total_marks / student_class_count if student_class_count > 0 else 0
    

#     grading_system = {
#         'A': f"{student_school.A_min}-{student_school.A_max}",
#         'B': f"{student_school.B_min}-{student_school.B_max}",
#         'C': f"{student_school.C_min}-{student_school.C_max}",
#         'P': f"{student_school.P_min}-{student_school.P_max}",
#         'F': f"{student_school.F_min}-{student_school.F_max}",
#     }
    
#     grade_comments = {
#         'A': student_school.A_comment,
#         'B': student_school.B_comment,
#         'C': student_school.C_comment,
#         'P': student_school.P_comment,
#         'F': student_school.F_comment
#     }

#     subject_grades = {}
#     class_averages = {}
#     subject_comments = {}
#     positions = {}
#     subject_statistics = {}
    
#     # Initialize total marks and maximum possible marks
#     total_marks_obtained = 0
#     total_max_marks = 0

#     for result in results:
#         subject = result.exam.course_name
#         # Calculate marks for CA, MIDTERM, and EXAM
#         ca_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='CA').aggregate(Sum('marks'))['marks__sum'] or 0
#         midterm_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session ,student=student, exam_type__name='MIDTERM').aggregate(Sum('marks'))['marks__sum'] or 0
#         exam_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='EXAM').aggregate(Sum('marks'))['marks__sum'] or 0

#         ca_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='CA'
#         ).values('total_marks').first()
#         ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0  # Total possible marks for CA exam
#         # print(ca_total_marks, 'ca_total_marks11')
       
#         midterm_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='MIDTERM'
#             ).values('total_marks').first()

#         midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0  # Total possible marks for MIDTERM exam
#         # print(midterm_total_marks, 'midterm_total_marks')

#         exam_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='EXAM'
#         ).values('total_marks').first()

#         exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0  # Total possible marks for EXAM
#         # print(exam_total_marks, 'exam_total_marks')
#         # print(exam_marks, 'exam_marks')
#         # print(ca_show_questions, 'ca_show_questions')
#         if not midterm_marks and not exam_marks:
#             # Only CA marks are present
#             total_marks = (ca_marks / ca_total_marks) * 100
#         elif not exam_marks:
#             # Only CA marks and midterm marks are present
#             c_m = midterm_marks + ca_marks
#             t_c_m = ca_total_marks + midterm_total_marks
#             total_marks = round((c_m / t_c_m) * 100, 1)  # Rounds to 2 decimal places

#         else:
#             # All marks are present: CA, midterm, and exam
#             total_marks = (
#                 (ca_marks / ca_total_marks) * 100 * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
#                 (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
#                 (exam_marks / exam_total_marks) * 100 * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
#             )

#         # Add total marks for this subject to total_marks_obtained
#         total_marks_obtained += total_marks
#         # print(total_marks_obtained, 'tmo')
#         total_max_marks += result.exam.total_marks
#         # print(total_max_marks, 'total_max_marks')
#         grade = calculate_grade(total_marks, student.user.school)
        
#         subject_statistics[subject] = {
#             'CA': ca_marks,
#             'MIDTERM': midterm_marks,
#             'EXAM': exam_marks,
#             'total_score': total_marks,
#         }

#         # Calculate the count of subjects from various dictionaries
#         subject_count_statistics = len(subject_statistics)
#         subject_inf = subject_statistics
#         subject_count_grades = len(subject_grades)
#         subject_count_total_scores = len(subject_total_scores)

#         print('Number of subjects in subject_statistics:', subject_count_statistics)
#         print('subject_inf:', subject_inf)
#         print('Number of subjects in subject_grades:', subject_count_grades)
#         print('Number of subjects in subject_total_scores:', subject_count_total_scores)

#         student_averages = Result.objects.filter(
            
#         result_class=student.student_class, 
#         session=session,
#           term=term
#       ).values('student').annotate(average_marks=Avg('marks'))

#         highest_average_in_class = student_averages.aggregate(Max('average_marks'))['average_marks__max']
#         lowest_average_in_class = student_averages.aggregate(Min('average_marks'))['average_marks__min']
        
#         highest_average_in_class = round(highest_average_in_class, 2) if highest_average_in_class is not None else 0
#         lowest_average_in_class = round(lowest_average_in_class, 2) if lowest_average_in_class is not None else 0

#         all_students_total_marks = Result.objects.filter(
#             exam__course_name=subject, 
#             session = session,
#             term= term,
#             student__user__student_class=student_class
#         ).values('student').annotate(total_marks=Sum('marks'))


#         low = all_students_total_marks.aggregate(Min('total_marks'))['total_marks__min']
#         high = all_students_total_marks.aggregate(Max('total_marks'))['total_marks__max']
        
#         # Get total marks for all students in the class for the given exam type
#         students_subject_total = Result.objects.filter(
#             student__user__student_class=student_class, 
#             session=session, 
#             term=term, 
            
#         ).values('student').annotate(total_marks=Sum('marks')).order_by('-total_marks')
#         # print(students_subject_total, 'students_subject_total')
#         # Initialize the final position as None
#         final_position = None

#         # Loop through the sorted list to determine the position
#         for idx, student_total in enumerate(students_subject_total, start=1):
#             if student_total['student'] == student.id:
#                 final_position = ordinal(idx)  # Convert to ordinal (1st, 2nd, 3rd, etc.)
#                 break


#         subject_grades[subject] = {
#             'grade': grade,
#             'low': low,
#             'high': high
#         }

#         num_subjects = results.count()
        
#         final_average = total_marks_obtained / num_subjects if num_subjects > 0 else 0
#         final_grade = calculate_grade(final_average, student.user.school)

#         sorted_marks = sorted(all_students_total_marks, key=lambda x: x['total_marks'], reverse=True)
#         position = next((i + 1 for i, marks in enumerate(sorted_marks) if marks['student'] == student.id), None)
#         positions[subject] = position

#         comment = grade_comments.get(grade, 'No comment available')
#         subject_comments[subject] = comment

#         avg_marks = all_students_total_marks.aggregate(Avg('total_marks'))['total_marks__avg']
#         class_averages[subject] = round(avg_marks, 2) if avg_marks else 0


#     subject_low_averages = []
#     for result in results:
#         subject_name = result.exam.course_name
#         lowest_marks = Result.objects.filter(
#             exam__course_name=subject_name,
#             student__user__student_class=student_class,
           
#         ).values('student').annotate(total_marks=Sum('marks')).aggregate(Min('total_marks'))['total_marks__min']
#         if lowest_marks is not None:
#             subject_low_averages.append(lowest_marks)

#     overall_lowest_average = sum(subject_low_averages) / len(subject_low_averages) if subject_low_averages else 0
#     overall_lowest_average = round(overall_lowest_average, 1)

#     exam_types = Result.objects.filter(
#         student=student, 
#         session=session, 
#         term=term
#     ).values('exam_type__name').distinct()


#     context = {
#         'ca_total_marks':ca_total_marks,
#         'midterm_total_marks':midterm_total_marks,
#         'exam_total_marks':exam_total_marks,
#         'student': student,
#         'session': session,
#         'term': term,
#         'exam_types': exam_types,
#         'class_average': round(class_average, 2), 
#         'student_name': student_name,
#         'student_gender': student_gender,
#         'student_admission_no': student_admission_no,
#         'student_class': student_class,
#         'student_school': student_school,
#         'profile_picture': profile_picture_url,
#         'results': results,
#         'results_count': subject_count_statistics,
#         'total_marks_obtained': total_marks_obtained,
#         'total_max_marks': total_max_marks,
#         'school_motto': school_motto,
#         'school_address': school_address,
#         'average_marks_obtained': round(final_average, 2),
#         'student_class_count': student_class_count,
#         'grading_system': grading_system,
#         'subject_statistics': subject_statistics,
#         'subject_grades': subject_grades,
#         'positions': positions,
#         'subject_comments': subject_comments,
#         'subj_class_averages': class_averages,
#         'final_position': final_position,
#         'final_grade': final_grade,
#         'highest_average_in_class': highest_average_in_class,
#         'lowest_average_in_class': lowest_average_in_class,
#         'overall_lowest_average': overall_lowest_average,
#         'subject_total_scores': subject_total_scores,
#     }

#     return render(request, 'student/dashboard/report_card.html', context)



from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Profile, Result, Course, Badge


from django.shortcuts import get_object_or_404

@login_required
def leaderboard(request, session, term):
    student = Profile.objects.select_related('user', 'user__school').get(user=request.user)
    students_in_class = Profile.objects.filter(student_class=student.student_class)

    # Fetch the session and term instances
    session_instance = get_object_or_404(Session, name=session)
    term_instance = get_object_or_404(Term, name=term)

    leaderboard_data = []

    for student in students_in_class:
        results = Result.objects.filter(
            student=student,
            result_class=student.student_class,
            session=session_instance,
            term=term_instance,
        ).select_related('student', 'exam').distinct()

        total_marks_obtained = 0
        subject_statistics = {}

        for result in results:
            subject = result.exam.course_name

            # Initialize total_marks
            total_marks = 0

            # Calculate marks for CA, MIDTERM, and EXAM for this subject
            ca_marks = Result.objects.filter(
                exam__course_name=subject,
                term=term_instance,
                session=session_instance,
                student=student,
                exam_type__name='CA'
            ).aggregate(Sum('marks'))['marks__sum'] or 0

            midterm_marks = Result.objects.filter(
                exam__course_name=subject,
                term=term_instance,
                session=session_instance,
                student=student,
                exam_type__name='MIDTERM'
            ).aggregate(Sum('marks'))['marks__sum'] or 0

            exam_marks = Result.objects.filter(
                exam__course_name=subject,
                term=term_instance,
                session=session_instance,
                student=student,
                exam_type__name='EXAM'
            ).aggregate(Sum('marks'))['marks__sum'] or 0

            # Calculate total marks logic here
            ca_total_marks = Course.objects.filter(term=term_instance, session=session_instance, exam_type__name='CA').values('total_marks').first()
            ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0
            
            midterm_total_marks = Course.objects.filter(term=term_instance, session=session_instance, exam_type__name='MIDTERM').values('total_marks').first()
            midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0
            
            exam_total_marks = Course.objects.filter(term=term_instance, session=session_instance, exam_type__name='EXAM').values('total_marks').first()
            exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0

            if not midterm_marks and not exam_marks:
                if ca_total_marks > 0:
                    total_marks = (ca_marks / ca_total_marks) * 100
                else:
                    total_marks = 0
            elif not exam_marks:
                total_marks = (ca_marks + midterm_marks) / (ca_total_marks + midterm_total_marks) * 100 if ca_total_marks + midterm_total_marks > 0 else 0
            else:
                total_marks = (
                    (ca_marks / ca_total_marks) * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                    (midterm_marks / midterm_total_marks) * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                    (exam_marks / exam_total_marks) * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
                ) * 100 if (ca_total_marks + midterm_total_marks + exam_total_marks) > 0 else 0

            subject_statistics[subject] = {
                'CA': ca_marks,
                'MIDTERM': midterm_marks,
                'EXAM': exam_marks,
                'total_score': total_marks
            }

            total_marks_obtained += total_marks  # Now total_marks is defined

        # Calculate average score across all subjects for the student
        subject_count = len(subject_statistics)
        final_average = total_marks_obtained / subject_count if subject_count > 0 else 0

        # Append the student data to leaderboard
        leaderboard_data.append({
            'student': student,
            'total_marks': total_marks_obtained,
            'final_average': final_average
        })

    # Sort students by total marks obtained in descending order
    leaderboard_data.sort(key=lambda x: x['total_marks'], reverse=True)

    # Add rank to each student
    current_rank = 1
    for idx, student_data in enumerate(leaderboard_data):
        if idx == 0:
            student_data['rank'] = current_rank
        else:
            if student_data['total_marks'] == leaderboard_data[idx - 1]['total_marks']:
                student_data['rank'] = leaderboard_data[idx - 1]['rank']
            else:
                current_rank = idx + 1
                student_data['rank'] = current_rank

    context = {
        'session': session_instance,
        'term': term_instance,
        'leaderboard': leaderboard_data,
    }

    return render(request, 'student/dashboard/leaderboard.html', context)

# original codes
# @login_required
# def leaderboard(request, session, term):
#     # Fetch all students in the same class as the logged-in student
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)
    
#     # Get all students in the same class
#     # students_in_class = Profile.objects.filter(school = request.user.school,student_class=student.student_class)
#     students_in_class = Profile.objects.filter(student_class=student.student_class)
#     # print(students_in_class, 'students_in_class')
#     # print(request.user.school, 'schools')    
#     # Calculate total marks for each student
#     leaderboard_data = []

#     for student in students_in_class:
#         results = Result.objects.filter(
#             student=student,
#             result_class=student.student_class,
#             session=session,
#             term=term,
#         ).select_related('student', 'exam').distinct()

#         total_marks_obtained = 0
#         total_max_marks = 0
#         subject_statistics = {}

#         for result in results:
#             subject = result.exam.course_name

#             # Calculate marks for CA, MIDTERM, and EXAM for this subject
#             ca_marks = Result.objects.filter(exam__course_name=subject, term=term, session=session, student=student, exam_type__name='CA').aggregate(Sum('marks'))['marks__sum'] or 0
#             midterm_marks = Result.objects.filter(exam__course_name=subject, term=term, session=session, student=student, exam_type__name='MIDTERM').aggregate(Sum('marks'))['marks__sum'] or 0
#             exam_marks = Result.objects.filter(exam__course_name=subject, term=term, session=session, student=student, exam_type__name='EXAM').aggregate(Sum('marks'))['marks__sum'] or 0

#             ca_total_marks = Course.objects.filter(term=term, session=session, exam_type__name='CA').values('total_marks').first()
#             ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0
#             midterm_total_marks = Course.objects.filter(term=term, session=session, exam_type__name='MIDTERM').values('total_marks').first()
#             midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0
#             exam_total_marks = Course.objects.filter(term=term, session=session, exam_type__name='EXAM').values('total_marks').first()
#             exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0

#             if not midterm_marks and not exam_marks:
#                 if ca_total_marks > 0:
#                     total_marks = (ca_marks / ca_total_marks) * 100
#                 else:
#                     total_marks = 0
#             elif not exam_marks:
#                 total_marks = (ca_marks + midterm_marks) / (ca_total_marks + midterm_total_marks) * 100 if ca_total_marks + midterm_total_marks > 0 else 0
#             else:
#                 total_marks = (
#                     (ca_marks / ca_total_marks) * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
#                     (midterm_marks / midterm_total_marks) * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
#                     (exam_marks / exam_total_marks) * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
#                 ) * 100 if (ca_total_marks + midterm_total_marks + exam_total_marks) > 0 else 0

#             subject_statistics[subject] = {
#                 'CA': ca_marks,
#                 'MIDTERM': midterm_marks,
#                 'EXAM': exam_marks,
#                 'total_score': total_marks
#             }

#             # print(total_marks_obtained)

#             total_marks_obtained += total_marks

#         # Calculate average score across all subjects for the student
#         subject_count = len(subject_statistics)
#         final_average = total_marks_obtained / subject_count if subject_count > 0 else 0

#         # Append the student data to leaderboard
#         leaderboard_data.append({
#             'student': student,
#             'total_marks': total_marks_obtained,
#             'final_average': final_average
#         })

#     # leaderboard_data.sort(key=lambda x: x['total_marks'], reverse=True)
    
#     # Sort students by total marks obtained in descending order
#     leaderboard_data.sort(key=lambda x: x['total_marks'], reverse=True)

#     # Add rank to each student and handle ties (same total marks)
#     current_rank = 1
#     for idx, student_data in enumerate(leaderboard_data):
#         if idx == 0:
#             student_data['rank'] = current_rank  # First student gets the 1st rank
#         else:
#             # Check if the current student has the same total marks as the previous one
#             if student_data['total_marks'] == leaderboard_data[idx - 1]['total_marks']:
#                 student_data['rank'] = leaderboard_data[idx - 1]['rank']  # Same rank as previous student
#             else:
#                 # Increment rank by the number of students considered so far (i.e., current index + 1)
#                 current_rank = idx + 1  # Skip ranks for ties
#                 student_data['rank'] = current_rank


#     # Add rank to each student
#     # for idx, student_data in enumerate(leaderboard_data, start=1):
#     #     student_data['rank'] = idx

#     context = {
#         'session': session,
#         'term': term,
#         'leaderboard': leaderboard_data,
#     }

#     return render(request, 'student/dashboard/leaderboard.html', context)


# @login_required
# def leaderboard(request, session, term):
#     # Fetch the student's profile
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

#     # Get all students in the student's class
#     student_class = student.student_class

#     # Get all students in the class
#     students_in_class = Profile.objects.filter(student_class=student_class)

#     # Initialize an empty list to store the leaderboard data
#     leaderboard_data = []

#     for student in students_in_class:
#         # Get the total marks for the student by summing CA, MIDTERM, and EXAM
#         ca_marks = Result.objects.filter(
#             student=student, 
#             result_class=student_class, 
#             session=session, 
#             term=term, 
#             exam_type__name='CA'
#         ).aggregate(Sum('marks'))['marks__sum'] or 0

#         midterm_marks = Result.objects.filter(
#             student=student, 
#             result_class=student_class, 
#             session=session, 
#             term=term, 
#             exam_type__name='MIDTERM'
#         ).aggregate(Sum('marks'))['marks__sum'] or 0

#         exam_marks = Result.objects.filter(
#             student=student, 
#             result_class=student_class, 
#             session=session, 
#             term=term, 
#             exam_type__name='EXAM'
#         ).aggregate(Sum('marks'))['marks__sum'] or 0

#         # Calculate the total marks by summing CA, MIDTERM, and EXAM marks
#         total_marks = ca_marks + midterm_marks + exam_marks
#         print(total_marks, 'l')
#         # Add the student data to the leaderboard list
#         leaderboard_data.append({
#             'student_name': f"{student.first_name} {student.last_name}",
#             'total_marks': total_marks
#         })

#     # Sort the leaderboard by total marks in descending order
#     leaderboard_data = sorted(leaderboard_data, key=lambda x: x['total_marks'], reverse=True)

#     # Assign rank/position to each student
#     for idx, student_data in enumerate(leaderboard_data, start=1):
#         student_data['rank'] = ordinal(idx)

#     # Send the leaderboard data to the template
#     context = {
#         'leaderboard': leaderboard_data,
#         'session': session,
#         'term': term,
       
#     }

#     return render(request, 'student/dashboard/leaderboard.html', context)



# Helper function to convert numbers to ordinals
def ordinal(n):
    suffix = ['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th']
    if 10 <= n % 100 <= 20:
        suffix_idx = 0
    else:
        suffix_idx = n % 10
    return f"{n}{suffix[suffix_idx]}"

@login_required
def leaderboard_list(request):
    # Get the currently logged-in student's profile
    try:
        student = Profile.objects.select_related('user', 'user__school').get(user=request.user)
    except Profile.DoesNotExist:
        return HttpResponseNotFound("Profile not found")

    # Fetch distinct sessions, terms, and exam types where the student has results
    leaderboards = Result.objects.filter(student=student).select_related('session','term').values('session__name', 'term__name').distinct()
   
    context = {
        'leaderboards': leaderboards,
    }

    return render(request, 'student/dashboard/leaderboard_list.html', context)

# ordinal codes 9/28/2024
# @login_required
# def leaderboard_list(request):
#     # Get the currently logged-in student's profile
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

#     # Fetch distinct sessions, terms, and exam types where the student has results
#     leaderboards = Result.objects.filter(student=student).values('session', 'term').distinct()

#     context = {
#         'leaderboards': leaderboards,
#     }

#     return render(request, 'student/dashboard/leaderboard_list.html', context)



from student.models import Badge

@login_required
def award_student_badges(request, session, term):
    student = Profile.objects.select_related('user').get(user=request.user)
    
    results = Result.objects.filter(
        student=student,
        result_class=student.student_class,
        session=session,
        term=term,
    )
    
    awarded_badges = []

    for result in results:
        ca_marks = Result.objects.filter(
            exam__course_name=result.exam.course_name,
            student=student,
            exam_type__name='CA'
        ).aggregate(Sum('marks'))['marks__sum'] or 0
        
        midterm_marks = Result.objects.filter(
            exam__course_name=result.exam.course_name,
            student=student,
            exam_type__name='MIDTERM'
        ).aggregate(Sum('marks'))['marks__sum'] or 0
        
        exam_marks = Result.objects.filter(
            exam__course_name=result.exam.course_name,
            student=student,
            exam_type__name='EXAM'
        ).aggregate(Sum('marks'))['marks__sum'] or 0
        
        total_marks = ca_marks + midterm_marks + exam_marks
        grade = calculate_grade(total_marks, student.user.school)
        # print(total_marks, 'total_marks')
        
        if grade == 'A':
            badge_type = 'Gold'
            description = 'Awarded for scoring an A'
        elif grade == 'B':
            badge_type = 'Silver'
            description = 'Awarded for scoring a B'
        elif grade == 'C':
            badge_type = 'Bronze'
            description = 'Awarded for scoring a C'
        else:
            continue
        
        badge, created = Badge.objects.get_or_create(
            student=student, 
            badge_type=badge_type, 
            defaults={'description': description}
        )
        
        awarded_badges.append({
            'badge': badge,
            'subject': result.exam.course_name,
            'session': session,  # Pass session here
            'term': term  # Pass term here
        })
    
    context = {
        'student': student,
        'session': session,  # Ensure session is in the context
        'term': term,  # Ensure term is in the context
        'awarded_badges': awarded_badges,
    }

    return render(request, 'student/dashboard/award_badges.html', context)



from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Profile, Badge



@login_required
def badge_list_view(request):
    # Get the currently logged-in student's profile
    student = Profile.objects.select_related('user').get(user=request.user)
     
    # Fetch distinct sessions and terms where the student has results
    badge_list = Result.objects.filter(student=student).select_related('session', 'term').values('session__name', 'term__name').distinct()
    # print(badge_list, 'll')

    # badge_list = Result.objects.filter(student=student).values('session', 'term').distinct()
    # print(badge_list, 'll')
    context = {
        'badge_list': badge_list,
    }

    return render(request, 'student/dashboard/badge_list.html', context)


from io import BytesIO
from django.shortcuts import render
from django.db.models import Sum
from .models import Profile, Result, Badge
from django.http import Http404
from django.contrib.auth.decorators import login_required
from sms.models import Session, Term
from django.http import HttpResponseNotFound

@login_required
def badge_details_view(request, session, term):
    # Fetch the session and term instances based on the provided values
    try:
        session_instance = Session.objects.get(name=session)
        term_instance = Term.objects.get(name=term)
    except (Session.DoesNotExist, Term.DoesNotExist):
        return HttpResponseNotFound("Session or Term not found")

    student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

    # Use the session_instance and term_instance in your query
    results = Result.objects.filter(
        student=student,
        result_class=student.student_class,
        session=session_instance,  # Use session_instance here
        term=term_instance,        # Use term_instance here
    ).select_related('student').distinct()

    subject_statistics = {}
    total_marks_obtained = 0

    for result in results:
        subject = result.exam.course_name
        # Calculate marks for CA, MIDTERM, and EXAM
        ca_marks = Result.objects.filter(
            exam__course_name=subject,
            term=term_instance,
            session=session_instance,
            student=student,
            exam_type__name='CA'
        ).aggregate(Sum('marks'))['marks__sum'] or 0

        midterm_marks = Result.objects.filter(
            exam__course_name=subject,
            term=term_instance,
            session=session_instance,
            student=student,
            exam_type__name='MIDTERM'
        ).aggregate(Sum('marks'))['marks__sum'] or 0

        exam_marks = Result.objects.filter(
            exam__course_name=subject,
            term=term_instance,
            session=session_instance,
            student=student,
            exam_type__name='EXAM'
        ).aggregate(Sum('marks'))['marks__sum'] or 0

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

        if not midterm_marks and not exam_marks:
            if ca_total_marks > 0:
                total_marks = (ca_marks / ca_total_marks) * 100
            else:
                total_marks = 0

        elif not exam_marks:
            c_m = midterm_marks + ca_marks
            t_c_m = ca_total_marks + midterm_total_marks
            
            if t_c_m > 0:
                total_marks = round((c_m / t_c_m) * 100, 1)
            else:
                total_marks = 0

        else:
            total_marks = ca_total_marks + midterm_total_marks + exam_total_marks
            
            if total_marks > 0:
                total_marks = (
                    (ca_marks / ca_total_marks) * 100 * (ca_total_marks / total_marks) +
                    (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / total_marks) +
                    (exam_marks / exam_total_marks) * 100 * (exam_total_marks / total_marks)
                )
            else:
                total_marks = 0

        subject_statistics[subject] = {
            'CA': ca_marks,
            'MIDTERM': midterm_marks,
            'EXAM': exam_marks,
            'total_score': total_marks,
        }

    subject_count_statistics = len(subject_statistics)
    total_marks_obtaine = sum(stats['total_score'] for stats in subject_statistics.values())
  
    final_average = total_marks_obtaine / subject_count_statistics if subject_count_statistics > 0 else 0
    final_grade = calculate_grade(final_average, student.user.school)

    # Determine badge type and description
    if final_grade == 'A':
        badge_type = 'Gold'
        description = 'Awarded for scoring an A'
    elif final_grade == 'B':
        badge_type = 'Silver'
        description = 'Awarded for scoring a B'
    elif final_grade == 'C':
        badge_type = 'Bronze'
        description = 'Awarded for scoring a C'
    else:
        badge_type = None
        description = 'No badge awarded'

    # Fetch existing badge or create new one
    badge, created = Badge.objects.update_or_create(
        student=student,
        session=session_instance,
        term=term_instance,
        defaults={
            'final_average': final_average,
            'final_grade': final_grade,
            'badge_type': badge_type,
            'description': description,
        }
    )

    context = {
        'student': student,
        'badges': [badge],  # Ensure it's always a list
        'session': session,
        'term': term,
        'final_grade': final_grade,
        'description': description,
    }

    return render(request, 'student/dashboard/badge_detail.html', context)

# orinal codes
# @login_required
# def badge_details_view(request, session, term):

#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

#     # ).distinct()
#     results = Result.objects.filter(
#         student=student,
#         result_class=student.student_class,
#         session=session,
#         term=term,
#     ).select_related('student').distinct()

#     subject_statistics = {}
#     # Initialize total marks and maximum possible marks
#     total_marks_obtained = 0
#     total_max_marks = 0

#     for result in results:
#         subject = result.exam.course_name
#         # Calculate marks for CA, MIDTERM, and EXAM
#         ca_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='CA').aggregate(Sum('marks'))['marks__sum'] or 0
#         midterm_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session ,student=student, exam_type__name='MIDTERM').aggregate(Sum('marks'))['marks__sum'] or 0
#         exam_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='EXAM').aggregate(Sum('marks'))['marks__sum'] or 0

#         ca_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='CA'
#         ).values('total_marks').first()
#         ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0  # Total possible marks for CA exam
#         # print(ca_total_marks, 'ca_total_marks11')
       
#         midterm_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='MIDTERM'
#             ).values('total_marks').first()

#         midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0  # Total possible marks for MIDTERM exam
#         # print(midterm_total_marks, 'midterm_total_marks')

#         exam_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='EXAM'
#         ).values('total_marks').first()

#         exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0  # Total possible marks for EXAM

#         if not midterm_marks and not exam_marks:
#             # Only CA marks are present
#             if ca_total_marks > 0:  # Check if ca_total_marks is greater than zero
#                 total_marks = (ca_marks / ca_total_marks) * 100
#             else:
#                 total_marks = 0  # Set to 0 or handle as needed if ca_total_marks is zero

#         elif not exam_marks:
#             # Only CA marks and midterm marks are present
#             c_m = midterm_marks + ca_marks
#             t_c_m = ca_total_marks + midterm_total_marks
            
#             if t_c_m > 0:  # Check if the total of CA and midterm marks is greater than zero
#                 total_marks = round((c_m / t_c_m) * 100, 1)
#             else:
#                 total_marks = 0  # Set to 0 or handle as needed if both totals are zero

#         else:
#             # All marks are present: CA, midterm, and exam
#             total_marks = ca_total_marks + midterm_total_marks + exam_total_marks
            
#             if total_marks > 0:  # Check if the total marks are greater than zero
#                 total_marks = (
#                     (ca_marks / ca_total_marks) * 100 * (ca_total_marks / total_marks) +
#                     (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / total_marks) +
#                     (exam_marks / exam_total_marks) * 100 * (exam_total_marks / total_marks)
#                 )
#             else:
#                 total_marks = 0  # Set to 0 or handle as needed if all total marks are zero

        
#         subject_statistics[subject] = {
#             'CA': ca_marks,
#             'MIDTERM': midterm_marks,
#             'EXAM': exam_marks,
#             'total_score': total_marks,
#         }

#         # Calculate the count of subjects from various dictionaries
#         subject_count_statistics = len(subject_statistics)
#         subject_inf = subject_statistics
#         # Initialize the total marks obtained  
#         total_marks_obtaine = 0
#         # Loop through the subjects in subject_inf and add the total score for each subject
#         for student_subjects, stats in subject_inf.items():
#             # print(stats, 'stats')
#             total_marks_obtaine += stats['total_score']  # Add the 'total_score' for each subject
      
#     final_average = total_marks_obtaine / subject_count_statistics if subject_count_statistics > 0 else 0
#     final_grade = calculate_grade(final_average, student.user.school)
#     # print(total_marks_obtaine, 'total_marks_obtaine')
  
#     badge_type = None
#     description = None
#     if final_grade == 'A':
#         badge_type = 'Gold'
#         description = 'Awarded for scoring an A'
#     elif final_grade == 'B':
#         badge_type = 'Silver'
#         description = 'Awarded for scoring a B'
#     elif final_grade == 'C':
#         badge_type = 'Bronze'
#         description = 'Awarded for scoring a C'
#     else:
#         badge_type = None
#         description = 'No badge awarded'

#     # Fetch existing badge or create new one
#     badge, created = Badge.objects.update_or_create(
#         student=student,
#         session=session,
#         term=term,
#         defaults={
#             'final_average': final_average,
#             'final_grade': final_grade,
#             'badge_type': badge_type,
#             'description': description,
#         }
#     )

#     context = {
#         'student': student,
#         'badges': [badge],  # Ensure it's always a list
#         'session': session,
#         'term': term,
#         'final_grade': final_grade,
#         'description': description,
#     }

#     return render(request, 'student/dashboard/badge_detail.html', context)


# @login_required
# def badge_details_view(request, session, term):
#     # Get the currently logged-in student's profile
#     student = Profile.objects.select_related('user').get(user=request.user)
    
#     # Get all results for the student for the specified session and term
#     results = Result.objects.filter(
#         student=student,
#         result_class=student.student_class,
#         session=session,
#         term=term,
#     )

#     # Initialize the total marks and count of subjects
#     total_marks = 0
#     subject_count = 0
    
#     for result in results:
#         ca_marks = Result.objects.filter(
#             exam__course_name=result.exam.course_name,
#             student=student,
#             exam_type__name='CA',
#             session=session,
#             term=term
#         ).aggregate(Sum('marks'))['marks__sum'] or 0
        
#         midterm_marks = Result.objects.filter(
#             exam__course_name=result.exam.course_name,
#             student=student,
#             exam_type__name='MIDTERM',
#             session=session,
#             term=term
#         ).aggregate(Sum('marks'))['marks__sum'] or 0
        
#         exam_marks = Result.objects.filter(
#             exam__course_name=result.exam.course_name,
#             student=student,
#             exam_type__name='EXAM',
#             session=session,
#             term=term
#         ).aggregate(Sum('marks'))['marks__sum'] or 0
        
#         # Calculate total marks for the subject
#         subject_total_marks = ca_marks + midterm_marks + exam_marks
#         total_marks += subject_total_marks
#         subject_count += 1

#     # Calculate the final average grade
#     average_marks = total_marks / subject_count if subject_count > 0 else 0
#     final_grade = calculate_grade(average_marks, student.user.school)
#     print(final_grade)
#     # Assign badge based on final grade
#     badge_type = None
#     description = None
#     if final_grade == 'A':
#         badge_type = 'Gold'
#         description = 'Awarded for scoring an A'
#     elif final_grade == 'B':
#         badge_type = 'Silver'
#         description = 'Awarded for scoring a B'
#     elif final_grade == 'C':
#         badge_type = 'Bronze'
#         description = 'Awarded for scoring a C'
#     else:
#         badge_type = None
#         description = 'No badge awarded'

#     # Fetch the badge for the student for the specific session and term, or create if it doesn't exist
#     # Fetch or create the badge
#     badges = Badge.objects.filter(
#         student=student,
#         session=session,
#         term=term,
#         final_average=average_marks,
#         final_grade=final_grade,
#         badge_type=badge_type,
#         description=description
#     ).first()
    
#     if badges is None:
#         badges = Badge.objects.create(
#             student=student,
#             session=session,
#             term=term,
#             final_average=average_marks,
#             final_grade=final_grade,
#             badge_type=badge_type,
#             description=description
#         )
#     else:
#         badges = get_object_or_404(Badge, id=badges.id)

#     context = {
#         'student': student,
#         'badges': badges,
#         'session': session,
#         'term': term,
#         'final_grade': final_grade,
#         'description': description,
#     }

#     return render(request, 'student/dashboard/badge_detail.html', context)

from django.utils.timezone import now
from django.db.models import F
from student.models import BadgeDownloadStats

from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from xhtml2pdf import pisa
from io import BytesIO
from django.utils.timezone import now


from django.db.models import F
from django.utils.timezone import now

from django.http import HttpResponse
from io import BytesIO
from django.db.models import Sum, F
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.utils.timezone import now

from django.db import IntegrityError


@login_required
def badge_pdf_view(request, session, term):
    student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

    # Check if the session and term exist
    try:
        session_instance = Session.objects.get(name=session)
        term_instance = Term.objects.get(name=term)
    except (Session.DoesNotExist, Term.DoesNotExist):
        return HttpResponseNotFound("Session or Term not found")

    # Retrieve results for the student
    results = Result.objects.filter(
        student=student,
        result_class=student.student_class,
        session=session_instance,
        term=term_instance,
    ).select_related('student').distinct()

    subject_statistics = {}

    # Process results to calculate marks and totals
    for result in results:
        subject = result.exam.course_name
        ca_marks = Result.objects.filter(
            exam__course_name=subject, 
            term=term_instance, 
            session=session_instance, 
            student=student, 
            exam_type__name='CA'
        ).aggregate(Sum('marks'))['marks__sum'] or 0

        midterm_marks = Result.objects.filter(
            exam__course_name=subject, 
            term=term_instance, 
            session=session_instance, 
            student=student, 
            exam_type__name='MIDTERM'
        ).aggregate(Sum('marks'))['marks__sum'] or 0
        
        exam_marks = Result.objects.filter(
            exam__course_name=subject, 
            term=term_instance, 
            session=session_instance, 
            student=student, 
            exam_type__name='EXAM'
        ).aggregate(Sum('marks'))['marks__sum'] or 0

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

        if not midterm_marks and not exam_marks:
            total_marks = (ca_marks / ca_total_marks) * 100 if ca_total_marks > 0 else 0
        elif not exam_marks:
            total_marks = ((midterm_marks + ca_marks) / (ca_total_marks + midterm_total_marks)) * 100 if (ca_total_marks + midterm_total_marks) > 0 else 0
        else:
            total_marks = (
                (ca_marks / ca_total_marks) * 100 * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
                (exam_marks / exam_total_marks) * 100 * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
            ) if (ca_total_marks + midterm_total_marks + exam_total_marks) > 0 else 0

        subject_statistics[subject] = {
            'CA': ca_marks,
            'MIDTERM': midterm_marks,
            'EXAM': exam_marks,
            'total_score': total_marks,
        }

    subject_count_statistics = len(subject_statistics)
    total_marks_obtained = sum([stats['total_score'] for stats in subject_statistics.values()])
    
    final_average = total_marks_obtained / subject_count_statistics if subject_count_statistics > 0 else 0
    final_grade = calculate_grade(final_average, student.user.school)

    # Badge assignment based on the final grade
    badge_type, description = None, None
    if final_grade == 'A':
        badge_type, description = 'Gold', 'Award for achieving a final grade of A'
    elif final_grade == 'B':
        badge_type, description = 'Silver', 'Award for achieving a final grade of B'
    elif final_grade == 'C':
        badge_type, description = 'Bronze', 'Award for achieving a final grade of C'
    
    # Fetch existing badges (if applicable, based on your logic)
    badges = Badge.objects.filter(student=student, session=session_instance, term=term_instance)

    # Get the current month and year
    current_month = now().month
    current_year = now().year

    # Update or create download statistics for the school
    try:
        download_stats, created = BadgeDownloadStats.objects.get_or_create(
            school=student.user.school,  # Assuming `school` is linked to the user
            month=current_month,
            year=current_year,
        )
        download_stats.download_count += 1  # Increment download count
        download_stats.save()
    except IntegrityError:
        # Handle case where duplicates exist in the database
        download_stats = BadgeDownloadStats.objects.filter(
            school=student.user.school,
            month=current_month,
            year=current_year,
        ).first()  # Get the first record

        if download_stats:
            download_stats.download_count += 1
            download_stats.save()
    
    # Prepare context for PDF generation
    context = {
        'student': student,
        'badges': badges,
        'session': session_instance,
        'term': term_instance,
        'final_grade': final_grade,
        'badge_type': badge_type,
        'description': description,
    }

    # Render the PDF
    template_path = 'student/dashboard/badge_pdf.html'
    template = get_template(template_path)
    html = template.render(context)

    # Generate PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.first_name}_badges_{session}_{term}.pdf"'
    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=result)

    if pdf.err:
        return HttpResponse(f'Error generating PDF: {pdf.err}', status=500)

    response.write(result.getvalue())
    return response

# ordinal codes
# @login_required
# def badge_pdf_view(request, session, term):
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

#     # Retrieve results for the student
#     results = Result.objects.filter(
#         student=student,
#         result_class=student.student_class,
#         session=session,
#         term=term,
#     ).select_related('student').distinct()

#     subject_statistics = {}

#     # Process results to calculate marks and totals
#     for result in results:
#         subject = result.exam.course_name
#         ca_marks = Result.objects.filter(exam__course_name=subject, term=term, session=session, student=student, exam_type__name='CA').aggregate(Sum('marks'))['marks__sum'] or 0
#         midterm_marks = Result.objects.filter(exam__course_name=subject, term=term, session=session, student=student, exam_type__name='MIDTERM').aggregate(Sum('marks'))['marks__sum'] or 0
#         exam_marks = Result.objects.filter(exam__course_name=subject, term=term, session=session, student=student, exam_type__name='EXAM').aggregate(Sum('marks'))['marks__sum'] or 0

#         ca_total_marks = Course.objects.filter(term=term, session=session, exam_type__name='CA').values('total_marks').first()
#         ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0
        
#         midterm_total_marks = Course.objects.filter(term=term, session=session, exam_type__name='MIDTERM').values('total_marks').first()
#         midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0

#         exam_total_marks = Course.objects.filter(term=term, session=session, exam_type__name='EXAM').values('total_marks').first()
#         exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0

#         if not midterm_marks and not exam_marks:
#             total_marks = (ca_marks / ca_total_marks) * 100 if ca_total_marks > 0 else 0
#         elif not exam_marks:
#             total_marks = ((midterm_marks + ca_marks) / (ca_total_marks + midterm_total_marks)) * 100 if (ca_total_marks + midterm_total_marks) > 0 else 0
#         else:
#             total_marks = (
#                 (ca_marks / ca_total_marks) * 100 * (ca_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
#                 (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks)) +
#                 (exam_marks / exam_total_marks) * 100 * (exam_total_marks / (ca_total_marks + midterm_total_marks + exam_total_marks))
#             ) if (ca_total_marks + midterm_total_marks + exam_total_marks) > 0 else 0

#         subject_statistics[subject] = {
#             'CA': ca_marks,
#             'MIDTERM': midterm_marks,
#             'EXAM': exam_marks,
#             'total_score': total_marks,
#         }

#     subject_count_statistics = len(subject_statistics)
#     total_marks_obtained = sum([stats['total_score'] for stats in subject_statistics.values()])
    
#     final_average = total_marks_obtained / subject_count_statistics if subject_count_statistics > 0 else 0
#     final_grade = calculate_grade(final_average, student.user.school)

#     # Badge assignment based on the final grade
#     badge_type, description = None, None
#     if final_grade == 'A':
#         badge_type, description = 'Gold', 'Award for achieving a final grade of A'
#     elif final_grade == 'B':
#         badge_type, description = 'Silver', 'Award for achieving a final grade of B'
#     elif final_grade == 'C':
#         badge_type, description = 'Bronze', 'Award for achieving a final grade of C'
    
#     # Fetch existing badges (if applicable, based on your logic)
#     badges = Badge.objects.filter(student=student, session=session, term=term)

#     # Get the current month and year
#     current_month = now().month
#     current_year = now().year

#     # Update or create download statistics for the school
#     try:
#         download_stats, created = BadgeDownloadStats.objects.get_or_create(
#             school=student.user.school,  # Assuming `school` is linked to the user
#             month=current_month,
#             year=current_year,
#         )
#         download_stats.download_count += 1  # Increment download count
#         download_stats.save()
#     except IntegrityError:
#         # Handle case where duplicates exist in the database
#         download_stats = BadgeDownloadStats.objects.filter(
#             school=student.user.school,
#             month=current_month,
#             year=current_year,
#         ).first()  # Get the first record

#         if download_stats:
#             download_stats.download_count += 1
#             download_stats.save()

#     # Prepare context for PDF generation
#     context = {
#         'student': student,
#         'badges': badges,
#         'session': session,
#         'term': term,
#         'final_grade': final_grade,
#         'badge_type': badge_type,
#         'description': description,
#     }

#     # Render the PDF
#     template_path = 'student/dashboard/badge_pdf.html'
#     template = get_template(template_path)
#     html = template.render(context)

#     # Generate PDF response
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{student.first_name}_badges_{session}_{term}.pdf"'
#     result = BytesIO()
#     pdf = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=result)

#     if pdf.err:
#         return HttpResponse(f'Error generating PDF: {pdf.err}', status=500)

#     response.write(result.getvalue())
#     return response

# @login_required
# def badge_pdf_view(request, session, term):
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)

#     # ).distinct()
#     results = Result.objects.filter(
#         student=student,
#         result_class=student.student_class,
#         session=session,
#         term=term,
#     ).select_related('student').distinct()

#     subject_statistics = {}

 
#     for result in results:
#         subject = result.exam.course_name
#         # Calculate marks for CA, MIDTERM, and EXAM
#         ca_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='CA').aggregate(Sum('marks'))['marks__sum'] or 0
#         midterm_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session ,student=student, exam_type__name='MIDTERM').aggregate(Sum('marks'))['marks__sum'] or 0
#         exam_marks = Result.objects.filter(exam__course_name=subject,term=term,session=session, student=student, exam_type__name='EXAM').aggregate(Sum('marks'))['marks__sum'] or 0

#         ca_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='CA'
#         ).values('total_marks').first()
#         ca_total_marks = ca_total_marks['total_marks'] if ca_total_marks else 0  # Total possible marks for CA exam
#         # print(ca_total_marks, 'ca_total_marks11')
       
#         midterm_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='MIDTERM'
#             ).values('total_marks').first()

#         midterm_total_marks = midterm_total_marks['total_marks'] if midterm_total_marks else 0  # Total possible marks for MIDTERM exam
#         # print(midterm_total_marks, 'midterm_total_marks')

#         exam_total_marks = Course.objects.filter(
#         term=term,
#         session=session,
#         exam_type__name='EXAM'
#         ).values('total_marks').first()

#         exam_total_marks = exam_total_marks['total_marks'] if exam_total_marks else 0  # Total possible marks for EXAM

#         if not midterm_marks and not exam_marks:
#             # Only CA marks are present
#             if ca_total_marks > 0:  # Check if ca_total_marks is greater than zero
#                 total_marks = (ca_marks / ca_total_marks) * 100
#             else:
#                 total_marks = 0  # Set to 0 or handle as needed if ca_total_marks is zero

#         elif not exam_marks:
#             # Only CA marks and midterm marks are present
#             c_m = midterm_marks + ca_marks
#             t_c_m = ca_total_marks + midterm_total_marks
            
#             if t_c_m > 0:  # Check if the total of CA and midterm marks is greater than zero
#                 total_marks = round((c_m / t_c_m) * 100, 1)
#             else:
#                 total_marks = 0  # Set to 0 or handle as needed if both totals are zero

#         else:
#             # All marks are present: CA, midterm, and exam
#             total_marks = ca_total_marks + midterm_total_marks + exam_total_marks
            
#             if total_marks > 0:  # Check if the total marks are greater than zero
#                 total_marks = (
#                     (ca_marks / ca_total_marks) * 100 * (ca_total_marks / total_marks) +
#                     (midterm_marks / midterm_total_marks) * 100 * (midterm_total_marks / total_marks) +
#                     (exam_marks / exam_total_marks) * 100 * (exam_total_marks / total_marks)
#                 )
#             else:
#                 total_marks = 0  # Set to 0 or handle as needed if all total marks are zero

        
#         subject_statistics[subject] = {
#             'CA': ca_marks,
#             'MIDTERM': midterm_marks,
#             'EXAM': exam_marks,
#             'total_score': total_marks,
#         }

#         # Calculate the count of subjects from various dictionaries
#         subject_count_statistics = len(subject_statistics)
#         subject_inf = subject_statistics
#         # Initialize the total marks obtained  
#         total_marks_obtaine = 0
#         # Loop through the subjects in subject_inf and add the total score for each subject
#         for student_subjects, stats in subject_inf.items():
#             # print(stats, 'stats')
#             total_marks_obtaine += stats['total_score']  # Add the 'total_score' for each subject
      
#     final_average = total_marks_obtaine / subject_count_statistics if subject_count_statistics > 0 else 0
    
#     final_grade = calculate_grade(final_average, student.user.school)
#     # print(final_grade, 'fgrade')
#     # Assign badge based on final grade
#     badge_type = None
#     description = None
#     if final_grade == 'A':
#         badge_type = 'Gold'
#         description = 'Award for achieving a final grade of A'
#     elif final_grade == 'B':
#         badge_type = 'Silver'
#         description = 'Award for achieving a final grade of B'
#     elif final_grade == 'C':
#         badge_type = 'Bronze'
#         description = 'Award for achieving a final grade of C'
#     else:
#         badge_type = 'None'
#         description = 'No badge awarded'
    
#     # Fetch badges for the student for the specific session and term
    
#     badges = Badge.objects.filter(student=student, session=session, term=term)


#     context = {
#         'student': student,
#         'badges': badges,
#         'session': session,
#         'term': term,
#         'final_grade':final_grade,
#         'badge_type':badge_type,
#         'description':description,
#     }
    
#     # Load the template
#     template_path = 'student/dashboard/badge_pdf.html'
#     template = get_template(template_path)
#     html = template.render(context)
    
#     # Generate PDF
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{student.first_name}_badges_{session}_{term}.pdf"'
#     result = BytesIO()
#     pdf = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=result)
    
#     if pdf.err:
#         return HttpResponse(f'Error generating PDF: {pdf.err}', status=500)
    
#     response.write(result.getvalue())
#     return response



import calendar
import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns  # Use seaborn for better visuals
from django.conf import settings
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import BadgeDownloadStats


# Set seaborn style for better-looking plots
sns.set(style="whitegrid")


import calendar
import os
import plotly.graph_objects as go
from django.conf import settings
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import BadgeDownloadStats




@login_required
def download_statistics_view(request):
    statistics = (
        BadgeDownloadStats.objects
        .values('school__school_name', 'month', 'year')
        .annotate(total_downloads=Sum('download_count'))
        .order_by('school__school_name', 'year', 'month')
    )

    # Convert month numbers to month names
    for stat in statistics:
        stat['month_name'] = calendar.month_abbr[stat['month']]

    # Organize data for plotting
    data = {}
    for stat in statistics:
        school = stat['school__school_name']
        month_name = stat['month_name']
        year = stat['year']
        downloads = stat['total_downloads']

        if school not in data:
            data[school] = {}
        if year not in data[school]:
            data[school][year] = {}
        data[school][year][month_name] = downloads

    # Prepare a list to hold plot HTML for each school-year combination
    plot_urls = []

    # Generate a plot for each school and year
    for school, years in data.items():
        for year, months in years.items():
            months_sorted = list(months.keys())
            downloads_sorted = [months[month] for month in months_sorted]

            # Create a Plotly figure
            fig = go.Figure()

            # Add bars with reduced width
            fig.add_trace(go.Bar(
                x=months_sorted,
                y=downloads_sorted,
                name='Downloads',
                marker_color='blue',
                text=downloads_sorted,
                textposition='auto',
                width=0.2  # Set the bar width here (default is 0.8)
            ))

            # Add line connecting the tops of the bars
            fig.add_trace(go.Scatter(
                x=months_sorted,
                y=downloads_sorted,
                mode='lines+markers',
                name='Trend',
                line=dict(color='red', width=1),
                marker=dict(size=8)
            ))

            # Update layout
            fig.update_layout(
                title=f'Badge Download Statistics for {school} in {year}',
                xaxis_title='Month',
                yaxis_title='Download Count',
                template='plotly_white',
                showlegend=True
            )

            # Generate HTML for the plot and append to plot_urls
            plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            plot_urls.append({
                'school': school,
                'year': year,
                'plot_html': plot_html
            })

    context = {
        'statistics': statistics,
        'plot_urls': plot_urls,
    }

    return render(request, 'student/dashboard/badge_download_stats.html', context)


from student.models import ExamStatistics

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
import plotly.graph_objs as go
from .models import Result

@login_required
def exams_conducted_statistics_view(request):
    # Aggregate the total exams conducted by each school
    statistics = (
        Result.objects.select_related('session','term').values('student__user__school__school_name', 'session__name', 'term__name')  # Group by school, session, and term
        .annotate(total_exams_conducted=Count('exam'))
        .order_by('student__user__school__school_name', 'session', 'term')
    )

    # Prepare data for plotting
    school_exam_data = {}
    for stat in statistics:
        school_name = stat['student__user__school__school_name']
        session_term = f"{stat['session__name']}_{stat['term__name']}"
        if school_name not in school_exam_data:
            school_exam_data[school_name] = {}
        school_exam_data[school_name][session_term] = stat['total_exams_conducted']

    plot_urls = []

    # Generate a plot for each school
    for school, sessions in school_exam_data.items():
        session_terms = list(sessions.keys())
        total_exams = list(sessions.values())

        # Create a Plotly figure
        fig = go.Figure()

        # Add bars for total exams conducted
        fig.add_trace(go.Bar(
            x=session_terms,
            y=total_exams,
            name='Total Exams Conducted',
            marker_color='blue',
            text=total_exams,
            textposition='auto',
            width=0.2,  # Set the bar width here (default is 0.8)
            marker=dict(
                line=dict(color='black', width=1)  # Optional: Add a border to the bars
            )
        ))

        # Add a line connecting the tops of the bars
        fig.add_trace(go.Scatter(
            x=session_terms,
            y=total_exams,
            mode='lines+markers',  # Line with markers on each point
            line=dict(color='red', width=2),  # Customize the line color and width
            name='Trend Line'
        ))

        # Update layout
        fig.update_layout(
            title=f'Exams Conducted Statistics for {school}',
            xaxis_title='Session and Term',
            yaxis_title='Number of Exams',
            template='plotly_white',
            showlegend=True
        )

        # Generate HTML for the plot and append to plot_urls
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        plot_urls.append({
            'school': school,
            'plot_html': plot_html
        })

    context = {
        'statistics': statistics,
        'plot_urls': plot_urls,
    }

    return render(request, 'student/dashboard/exams_conducted_stats.html', context)


# real code
# @login_required
# def generate_report_card(request):
#     # Get the currently logged-in user's profile
#     student = Profile.objects.select_related('user', 'user__school').get(user=request.user)
#     newusers = NewUser.objects.get(id=request.user.id)
    
#     # Fetch results related to the student and the associated exam details
#     # results = Result.objects.filter(student=student).select_related('exam')

#     # Calculate total marks obtained and percentage
#     total_marks_obtained = sum(result.marks for result in results)
#     total_max_marks = sum(result.exam.total_marks for result in results)
#     percentage = (total_marks_obtained / total_max_marks) * 100 if total_max_marks > 0 else 0
    
#     # Access additional student information from the Profile and NewUser models
#     student_name = f"{student.first_name} {student.last_name}"
#     student_gender = newusers.gender
#     student_admission_no = newusers.admission_no
#     print(student_admission_no, 'oooo')
#     student_class = student.user.student_class  # Access the class from NewUser model
#     student_school = student.user.school  # Access the school from NewUser model

#     # Check if the student has a profile picture
#     profile_picture_url = student.user.pro_img.url if student.user.pro_img and hasattr(student.user.pro_img, 'url') else None
    
#     # Calculate grade based on percentage
#     grade = calculate_grade(percentage, student_school)

#     # School information
#     school_motto = student_school.school_motto if student_school else None
#     school_address = student_school.school_address if student_school else None

#     # Calculate the average marks obtained
#     num_exams = results.count()
#     average_marks_obtained = total_marks_obtained / num_exams if num_exams > 0 else 0

#     # Count of students in the same class
#     student_class_count = NewUser.objects.filter(student_class=student_class).count()
#     total_marks_overall_average = total_max_marks/student_class_count
#     # print(total_marks_overall_average, 'uuu')
#     # Grading system from the database
#     grading_system = {
#         'A': f"{student_school.A_min}-{student_school.A_max}",
#         'B': f"{student_school.B_min}-{student_school.B_max}",
#         'C': f"{student_school.C_min}-{student_school.C_max}",
#         'P': f"{student_school.P_min}-{student_school.P_max}",
#         'F': f"{student_school.F_min}-{student_school.F_max}",
#     }
#     # Comments based on grade
#     grade_comments = {
#         'A': student_school.A_comment,
#         'B': student_school.B_comment,
#         'C': student_school.C_comment,
#         'P': student_school.P_comment,
#         'F': student_school.F_comment
#     }

#     # Fetch teachers who teach the class that matches the student's class
#     teachers = Teacher.objects.filter(
#         classes_taught__name=student_class
#     ).prefetch_related('subjects_taught', 'classes_taught')

#     # Create a list to store teacher information
#     teacher_info = []
#     for teacher in teachers:
#         # Fetch the subjects and classes taught by the teacher
#         teacher_subjects = teacher.subjects_taught.all()
#         teacher_classes = teacher.classes_taught.all()
        
#         # Collect teacher information
#         teacher_info.append({
#             'first_name': teacher.first_name,
#             'last_name': teacher.last_name,
#             'form_teacher_remark': teacher.form_teacher_remark,
#         })

#     subject_grades = {}
#     for result in results:
#         course_name = result.exam.course_name  # Use the course name as the key
#         low = Result.objects.filter(exam__course_name=course_name, student__user__student_class=student_class).aggregate(models.Min('marks'))['marks__min']
#         high = Result.objects.filter(exam__course_name=course_name, student__user__student_class=student_class).aggregate(models.Max('marks'))['marks__max']
#         subject_grades[course_name] = {'low': low, 'high': high}  # Ensure course_name is used as the key
    
#     # class average
#     class_averages = {}
#     # subject_comments
#     subject_comments = {}
#     # Calculate positions
#     positions = {}

#     # Calculate positions and generate comments
#     for result in results:
#         subject = result.exam.course_name
#         all_marks = Result.objects.filter(exam__course_name=subject, student__user__student_class=student_class).values_list('marks', flat=True)
#         sorted_marks = sorted(all_marks, reverse=True)
#         position = sorted_marks.index(result.marks) + 1
#         positions[subject] = position
        
#         grade = calculate_grade(result.marks, student_school)
  
#     # Grading comments
#     subject_comments = {}
#     for result in results:
#         subject = result.exam.course_name
#         # Determine grade and comment for the result
#         grade = calculate_grade(result.marks, student_school)
#         comment = {
#             'A': student_school.A_comment,
#             'B': student_school.B_comment,
#             'C': student_school.C_comment,
#             'P': student_school.P_comment,
#             'F': student_school.F_comment,
#         }.get(grade, 'No comment available')
#         subject_comments[subject] = comment
    
#         # Calculate class averages for each subject
#     class_averages = {}
#     for result in results:
#         subject_name = result.exam.course_name  # Use the subject name as the key
#         avg_marks = Result.objects.filter(
#             exam__course_name=subject_name,
#             student__user__student_class=student_class
#         ).aggregate(Avg('marks'))['marks__avg']
#         class_averages[subject_name] = round(avg_marks, 2) if avg_marks else 0


#         # Set comments based on grades
#         for result in results:
#             if result.exam.course_name == subject:
#                 result_grade = calculate_grade(result.marks, student_school)

#     #   Calculate final position based on total marks
#     all_students_total_marks = Result.objects.filter(student__user__student_class=student_class).values('student').annotate(total_marks=Sum('marks')).order_by('-total_marks')

#     final_position = None
#     for idx, student_total in enumerate(all_students_total_marks, start=1):
#         if student_total['student'] == student.id:
#             final_position = ordinal(idx)
#             break

#     # Calculate the highest average in class
#     student_highest_average = max(class_averages.values(), default=0)
#     student_highest_average = round(student_highest_average, 1)  # Round to 1 decimal place

#     student_lowest_average = min(class_averages.values(), default=0)
#     student_lowest_average = round(student_lowest_average, 1)

#     # Calculate the lowest average for each subject across the class
 

#     # Calculate the lowest average among all subjects
#     overall_lowest_average = min(class_averages.values()) if class_averages else 0
#     overall_lowest_average = round(overall_lowest_average, 1)

#     # Calculate the lowest marks across all subjects in the class
#     subject_low_averages = []
#     for result in results:
#         subject_name = result.exam.course_name
#         lowest_marks = Result.objects.filter(
#             exam__course_name=subject_name,
#             student__user__student_class=student_class
#         ).aggregate(models.Min('marks'))['marks__min']
#         if lowest_marks is not None:
#             subject_low_averages.append(lowest_marks)

#     # Calculate the average of these lowest marks
#     overall_lowest_average = sum(subject_low_averages) / len(subject_low_averages) if subject_low_averages else 0
#     overall_lowest_average = round(overall_lowest_average, 1)

#     print(overall_lowest_average)

#     context = {
#         'student': student,
       
#         'student_name': student_name,
#         'student_gender': student_gender,
#         'student_admission_no':student_admission_no,
#         'student_class': student_class,
#         'student_school': student_school,  # Add school to the context
#         'profile_picture': profile_picture_url,  # Add profile picture URL to the context
#         'results': results,
#         'results_count': results.count(),
#         'total_marks_obtained': total_marks_obtained,
#         'total_max_marks': total_max_marks,
#         'percentage': round(percentage, 2),
#         'grade': grade,  # Add grade to context
#         'school_motto': school_motto,
#         'school_address': school_address,
#         'average_marks_obtained': round(average_marks_obtained, 2), 
#         'student_class_count': student_class_count,
#         'grading_system': grading_system,  # Add grading system to context
#         'teacher_info': teacher_info,  # Pass the list of teacher info to context
#         'subject_grades': subject_grades,
#         'positions': positions,
#         'class_averages': class_averages,
#         'subject_comments': subject_comments, 
#         'final_position': final_position,
#         'student_highest_average': student_highest_average,
#         'student_lowest_average': student_lowest_average,
#         'subject_low_averages':subject_low_averages,

        
        
#     }

#     return render(request, 'student/dashboard/report_card.html', context)


# from pypaystack import Transaction, Customer, Plan

@cache_page(60 * 15)
@csrf_exempt
@require_POST
@transaction.non_atomic_requests(using='db_name')
def paystack_webhook(request):
    # Ensure this is a POST request
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=400)

    # Parse the JSON payload from the request
    try:
        payload = json.loads(request.body)
        # print("payloadttt:", payload)
    except json.JSONDecodeError as e:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)

    # Extract relevant information from the payload
    event = payload.get('event')
    data = payload.get('data')

    # Check the event type
    if event == 'charge.success':
        # Extract information from the data
        verified = True
        reference = data.get('reference')
        paid_amount = data.get('amount') / 100
        first_name = data['customer'].get('first_name')
        last_name = data['customer'].get('last_name')
        email = data['customer'].get('email')

        referrer = payload['data']['metadata']['referrer'].strip()
        # print("Referrer URL:", referrer)
        # print("amount:", paid_amount)

        # Split the referrer URL by '/'
        url_parts = referrer.split('/')
        content_type = url_parts[-3]
        # print("content_type", content_type)
        # print('url:', url_parts[-3])

        # retrieving referral codes
        recode = get_object_or_404(NewUser, email = email)
        recode = recode.phone_number
    

        # Check if the last part of the URL is a numeric "id"
        if url_parts[-2].isdigit():
            id_value = url_parts[-2]
            # print("Extracted ID:", id_value)
        else:
            id_value = None

        
        # print("course printed:", course)
        
        # course_amount = course.price
      
        if content_type == 'course':
            # Assuming id_value is the primary key of the Courses model
            course = get_object_or_404(Courses, pk=id_value)

            # Check if a Payment with the same reference already exists
            # user_newuser = get_object_or_404(NewUser, email=request.user)
            # print("user_newuser", user_newuser)
            user = Profile.objects.get(id=course.id)
            existing_payment = Payment.objects.filter(ref=reference).first()

            if not existing_payment:
                # Create a new Payment only if no existing payment is found
                payment = Payment.objects.create(
                    ref=reference,
                    amount=paid_amount,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    verified=verified,
                    content_type=course,
                    payment_user=user,
                    
                )

                # Set courses for the Payment instance
                # course = get_object_or_404(Courses, pk=id_value)
                if course:
                    payment.courses.set([course])
             
            else:
                # Handle the case where a Payment with the same reference already exists
                # You may want to log, display an error message, or take other actions
                print(f"Payment with reference {reference} already exists.")
                            
            
        # course = get_object_or_404(Courses, pk=id_value)
        elif content_type == 'certificates':
            # Assuming id_value is the primary key of the Course model
            course = get_object_or_404(Course, pk=id_value)

            # Check if a CertificatePayment with the same reference already exists
            existing_cert_payment = CertificatePayment.objects.filter(ref=reference).first()

            if not existing_cert_payment:
                # Create a new CertificatePayment only if no existing payment is found
                cert_payment = CertificatePayment.objects.create(
                    ref=reference,
                    amount=paid_amount,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    verified=verified,
                    content_type=course,
                    f_code=recode,
                )

                # Set courses for the CertificatePayment instance
                # course = get_object_or_404(Course, pk=id_value)
                if course:
                    cert_payment.courses.set([course])
            else:
                # Handle the case where a CertificatePayment with the same reference already exists
                # You may want to log, display an error message, or take other actions
                print(f"CertificatePayment with reference {reference} already exists.")

        else:

            if content_type == 'ebooks':
                course = get_object_or_404(PDFDocument, pk=id_value)

                # Check if a payment with the same reference already exists
                existing_payment = EbooksPayment.objects.filter(ref=reference).first()

                if not existing_payment:
                    # Create a new payment only if no existing payment is found
                    epayment = EbooksPayment.objects.create(
                        ref=reference,
                        amount=paid_amount,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        verified=verified,
                        content_type=course,
                    )

                    if course:
                        epayment.courses.set([course])
                else:
                    # Handle the case where a payment with the same reference already exists
                    # You may want to log, display an error message, or take other actions
                    print(f"Payment with reference {reference} already exists.")

 
            # if content_type == 'ebooks':
            #     course = get_object_or_404(PDFDocument, pk=id_value)
            
            #     epayment = EbooksPayment.objects.create(
            #         ref=reference,
            #         amount=paid_amount,
            #         first_name=first_name,
            #         last_name=last_name,
            #         email=email,
            #         verified=verified,
            #         content_type = course,
                
            #     )
            #     # print("idvalue", id_value)
            #     course = get_object_or_404(PDFDocument, pk=id_value)
            #     # print('pdfcourse', course)
            #     # Add courses to the payment using the 'set()' method
            #     if course:
            #         epayment.courses.set([course])

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Unsupported event type'}, status=400)


# end 
    
# views.py


""" import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ReferrerMentor, WithdrawalRequest

# Define the process_paystack_withdrawal function
def process_paystack_withdrawal(customer_id, amount):
    # Use Paystack API to initiate withdrawal
    # Replace 'your_paystack_secret_key' with your actual Paystack secret key

    paystack_secret_key = settings.PAYSTACK_SECRET_KEY

    withdrawal_url = 'https://api.paystack.co/transfer'
    
    headers = {
        'Authorization': f'Bearer {paystack_secret_key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'source': 'balance',
        'amount': int(amount) * 100,  # Paystack uses amount in kobo (multiply by 100)
        'recipient': customer_id,
    }

    response = requests.post(withdrawal_url, json=payload, headers=headers)
    return response.json()


def withdrawal_request(request):
    if request.method == 'POST':
        referrer = ReferrerMentor.objects.filter(referrer=request.user.id).first()

        if not referrer:
            messages.error(request, 'Referrer not found.')
            return redirect('sms:myprofile')

        if not referrer.can_withdraw():
            messages.error(request, 'Withdrawal request cannot be processed. Check your balance or request status.')
            return redirect('sms:myprofile')

        if not referrer.has_paystack_customer_id():
            messages.error(request, 'Withdrawal request cannot be processed. Paystack integration is not set up for this referrer.')
            return redirect('sms:myprofile')

        amount = request.POST.get('amount')

        # Create withdrawal request
        withdrawal = WithdrawalRequest.objects.create(referrer=referrer, amount=amount, status='pending')
        referrer.withdrawal_request_status = 'pending'
        referrer.save()

        # Process withdrawal using Paystack API
        paystack_response = process_paystack_withdrawal(referrer.paystack_customer_id, amount)

        if paystack_response.get('status') == 'success':
            # Payment was successful
            messages.success(request, 'Withdrawal request submitted successfully.')
        else:
            # Payment failed
            withdrawal.status = 'rejected'
            withdrawal.save()
            messages.error(request, f'Withdrawal request failed: {paystack_response.get("message")}')

        return redirect('sms:myprofile')  # Redirect to the dashboard or wherever is appropriate

    return render(request, 'student/dashboard/withdrawal_form.html')

 """


@cache_page(60 * 15)
def pdf_document_list(request):
    documents = PDFDocument.objects.all()
    return render(request, 'student/dashboard/pdf_document_list.html', {'documents': documents})


@login_required
def take_exams_view(request):
    # course = QMODEL.Course.objects.all()

    # course = Course.objects.select_related('schools', 'course_name').only(
    #     'id', 'schools__name', 'course_name__title'
    # )  
    course = Course.objects.select_related('schools', 'course_name').only(
        'id', 'schools__name', 'course_name__title','session','term', 'exam_type__name'
    )

    current_user = request.user
    # user_profile = get_object_or_404(Profile, user=request.user)
    # user_profile = get_object_or_404(Profile.objects.select_related('user'), user=request.user)
    user_profile = get_object_or_404(
            Profile.objects.select_related('user').only(
                'user__id', 'user__username', 'username', 'first_name', 'last_name'), user=request.user
        )
    # Get the results related to this user
    user_results =Result.objects.filter(student = user_profile).select_related('exam').only(
        'exam__id', 'exam__course_name', 'marks')
    # user_results = Result.objects.filter(student=user_profile)
    # print('user_results',user_results)
    # Optionally, get the related courses for these results
    # user_courses = Course.objects.filter(result__student=user_profile).distinct()


    # user_newuser = get_object_or_404(NewUser, email=request.user)
    user_newuser = get_object_or_404(
            NewUser.objects.select_related('school').only(
                'id', 'email', 'school__id', 'school__name', 'student_class'
            ), 
            email=request.user.email)
    
    if user_newuser is not None:
        school = user_newuser.school
        if school is not None:
            school_name = school.school_name
            # course_pay = school.course_pay
            # course_names = Course.objects.filter(course_pay=course_pay)
        else:
            school_name = "Default School Name"
            # course_names = []
            # course_pay = None
        student_class = user_newuser.student_class
    else:
        school_name = "Default School Name"
        student_class = "Default Class"
        # course_names = []
        # course_pay = None

    sub_grade = None  # Initialize sub_grade with a default value
    subjects = None  # Initialize subjects with a default value
    class_subj = []  # Initialize class_subj with a default value

    # Query the CourseGrade instance associated with the current user
    # course_grade = QMODEL.CourseGrade.objects.filter(students__in=[current_user]).first()
    # course_grade = QMODEL.CourseGrade.objects.filter(students__in=[current_user]).first()
    course_grade = QMODEL.CourseGrade.objects.prefetch_related('subjects').filter(students__in=[current_user]).first()

    if course_grade:
        # If the CourseGrade instance exists, you can access its name and subjects
        sub_grade = course_grade.name
        subjects = course_grade.subjects.all()
        for subject in subjects:
            class_subj.append(subject)
    else:
        print("No CourseGrade instance found for the current user.")

    context = {
        'courses': course,
        'class_subj': class_subj,
        'student_class': student_class,
        'school_name': school_name,
        "sub_grade": sub_grade,
        "subjects": subjects,
        # "course_names": course_names,
        # 'course_pay': course_pay,
        # "grades": QMODEL.CourseGrade.objects.all(),
        'user_results':user_results,
    }
    return render(request, 'student/dashboard/take_exams.html', context=context)


# @login_required
# def take_exams_view(request):
#     course = QMODEL.Course.objects.all()
#     current_user = request.user
#     user_profile = get_object_or_404(Profile, user=request.user)
    
#     # Get the results related to this user
#     user_results = Result.objects.filter(student=user_profile)
#     print('user_results',user_results)
#     # Optionally, get the related courses for these results
#     user_courses = Course.objects.filter(result__student=user_profile).distinct()
#     print(' user_courses', user_courses)

#     user_newuser = get_object_or_404(NewUser, email=request.user)
#     if user_newuser is not None:
#         school = user_newuser.school
#         if school is not None:
#             school_name = school.school_name
#             course_pay = school.course_pay
#             course_names = Course.objects.filter(course_pay=course_pay)
#         else:
#             school_name = "Default School Name"
#             course_names = []
#             course_pay = None
#         student_class = user_newuser.student_class
#     else:
#         school_name = "Default School Name"
#         student_class = "Default Class"
#         course_names = []
#         course_pay = None

#     sub_grade = None  # Initialize sub_grade with a default value
#     subjects = None  # Initialize subjects with a default value
#     class_subj = []  # Initialize class_subj with a default value

#     # Query the CourseGrade instance associated with the current user
#     course_grade = QMODEL.CourseGrade.objects.filter(students__in=[current_user]).first()

#     if course_grade:
#         # If the CourseGrade instance exists, you can access its name and subjects
#         sub_grade = course_grade.name
#         subjects = course_grade.subjects.all()
#         for subject in subjects:
#             class_subj.append(subject)
#     else:
#         print("No CourseGrade instance found for the current user.")

#     context = {
#         'courses': course,
#         'class_subj': class_subj,
#         'student_class': student_class,
#         'school_name': school_name,
#         "sub_grade": sub_grade,
#         "subjects": subjects,
#         "course_names": course_names,
#         'course_pay': course_pay,
#         "grades": QMODEL.CourseGrade.objects.all(),
#         'user_results':user_results,
#     }
#     return render(request, 'student/dashboard/take_exams.html', context=context)






# @login_required
# def start_exams_view(request, pk):
    
#     course = QMODEL.Course.objects.get(id = pk)
#     questions = QMODEL.Question.objects.get_queryset().filter(course = course).order_by('id')
#     q_count = QMODEL.Question.objects.all().filter(course = course).count()
#     paginator = Paginator(questions, 100) # Show 25 contacts per page.
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     context = {
#         'course':course,
#         'questions':questions,
#         'q_count':q_count,
#         'page_obj':page_obj
#     }
#     if request.method == 'POST':
#         pass
#     response = render(request, 'student/dashboard/start_exams.html', context=context)
#     response.set_cookie('course_id', course.id)
#     return response

from datetime import datetime, timedelta

from django.http import HttpResponse
from datetime import datetime, timedelta
from django.core.cache import cache  # Import Django's caching framework
from django.utils import timezone
import random
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def permission_denied_view(request, exception):
    # Redirect the user to the desired page
    return redirect("student:view_result")


@login_required
def start_exams_view(request, pk):

    # course = QMODEL.Course.objects.get(id=pk)
    course = get_object_or_404(
        Course.objects.select_related('course_name').only(
            'id', 'room_name', 'course_name__id', 'exam_type__name','course_name__title', 
            'num_attemps', 'show_questions', 
            'duration_minutes'
        ),
        id=pk
    )
    print(course.schools, 'course.exam_type')
    # num_attemps = course.num_attemps
    # questions = QMODEL.Question.objects.filter(course=course).order_by('id')
    questions = QMODEL.Question.objects.select_related('course').only(
        'id', 'course__id', 'marks', 'question', 'img_quiz', 'option1', 'option2', 
        'option3', 'option4', 'answer'
    ).filter(course=course).order_by('id')

    # result_exists = Result.objects.filter(student=request.user.profile, exam=course).exists()
    result_exists = Result.objects.select_related('student', 'exam').only(
        'student__id', 'student__username','exam_type__name', 'exam__id', 'exam__course_name'
    ).filter(
        student=request.user.profile, 
        exam=course
    ).exists()
    
    # Check if the student has already taken this exam
    if result_exists:
        return redirect('student:view_result')
    
    #     # Get the number of questions to display for the course
    show_questions = course.show_questions
    # Retrieve all questions for the course
    # all_questions = QMODEL.Question.objects.filter(course=course)
    # Count the total number of questions
    total_questions = questions.count()
  
    if total_questions >= show_questions:
        questions = random.sample(list(questions), show_questions)
    else:
        questions = list(questions)

    # Order the selected questions by their primary key for stable pagination
    questions.sort(key=lambda q: q.id)
   
    q_count = len(questions)  # Calculate the count of questions
    # print("q_count", q_count)

    context = {
        'course': course,
        'questions': questions,
        # 'num_attemps':num_attemps,
        # 'result_exists':result_exists,
        'q_count': q_count,
        'page_obj': questions,
        # 'remaining_seconds': remaining_seconds,  # Pass remaining time to template
    }

    if request.method == 'POST':
        # Handle form submission
        pass

    response = render(request, 'student/dashboard/start_exams.html', context=context)
    response.set_cookie('course_id', course.id)
    return response


# @login_required
# def start_exams_view(request, pk):

#     course = QMODEL.Course.objects.get(id=pk)
#     num_attemps = course.num_attemps
#     questions = QMODEL.Question.objects.filter(course=course).order_by('id')
#     q_count = questions.count()
#     paginator = Paginator(questions, 200)  # Show 100 questions per page.
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     student = request.user.profile
#     # Check if the result exists
#     result_exists = Result.objects.filter(student=student, exam=course).exists()
#     # Check if the student has already taken this exam
#     if result_exists:
#         return redirect('student:view_result')
    
#     #     # Get the number of questions to display for the course
#     show_questions = course.show_questions
#     # Retrieve all questions for the course
#     all_questions = QMODEL.Question.objects.filter(course=course)
#     # Count the total number of questions
#     total_questions = all_questions.count()
#     # If there are enough questions, select a random subset
#     # if total_questions >= show_questions:
#     #     # Randomly select indices for the questions
#     #     random_indices = random.sample(range(total_questions), show_questions)
#     #     # Filter questions based on the random indices
#     #     questions = [all_questions[index] for index in random_indices]
#     # else:
#     #     # If there are not enough questions, display all questions
#     #     questions = all_questions
#     if total_questions >= show_questions:
#         questions = random.sample(list(all_questions), show_questions)
#     else:
#         questions = list(all_questions)

#     # Order the selected questions by their primary key for stable pagination
#     questions.sort(key=lambda q: q.id)
#     # print("quest", questions)
#     # Shuffle the list of selected questions
#     # random.shuffle(questions)

#     q_count = len(questions)  # Calculate the count of questions
#     # print("q_count", q_count)

#     # Calculate quiz end time
#     quiz_duration = course.duration_minutes
#     quiz_start_time = timezone.now()
#     quiz_end_time = quiz_start_time + timedelta(minutes=quiz_duration)
#     # Store the quiz end time in cache
#     cache.set(f'quiz_end_time_{course.id}', quiz_end_time, timeout=None)
#     # Calculate remaining time until the end of the quiz
#     remaining_time = quiz_end_time - timezone.now()
#     remaining_seconds = max(int(remaining_time.total_seconds()), 0)

#     context = {
#         'course': course,
#         'questions': questions,
#         'num_attemps':num_attemps,
#         'result_exists':result_exists,
#         'q_count': q_count,
#         'page_obj': questions,
#         'remaining_seconds': remaining_seconds,  # Pass remaining time to template
#     }

#     if request.method == 'POST':
#         # Handle form submission
#         pass

#     response = render(request, 'student/dashboard/start_exams.html', context=context)
#     response.set_cookie('course_id', course.id)
#     return response



# end of dashboard view

import json
from django.http import JsonResponse

# example 2

from django.db.models import F

   
@login_required
def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course = QMODEL.Course.objects.get(id=course_id)
        
        total_marks = 0
        questions = QMODEL.Question.objects.filter(course=course).order_by('id')
        
        if request.body:
            json_data = json.loads(request.body)
            for i, question in enumerate(questions, start=1):
                selected_ans = json_data.get(str(i))
                actual_answer = question.answer
                if selected_ans == actual_answer:
                    total_marks += question.marks
        
        student = Profile.objects.get(user_id=request.user.id)

        try:
            # Create a new result, or raise IntegrityError if it already exists
            QMODEL.Result.objects.create(
                marks=total_marks,
                exam=course,
                session=course.session,
                term=course.term,
                exam_type=course.exam_type,
                student=student,
                result_class=student.student_class
            )
            return JsonResponse({'success': True, 'message': 'Marks calculated and saved successfully.'})
        
        except IntegrityError:
            # If the result already exists, return an appropriate response
            return JsonResponse({'success': False, 'error': 'Result already exists.'})
    
    else:
        return JsonResponse({'success': False, 'error': 'Course ID not found.'})
    
# @login_required
# def calculate_marks_view(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course = QMODEL.Course.objects.get(id=course_id)

#         total_marks = 0
#         questions = QMODEL.Question.objects.filter(course=course).order_by('id')
        
#         if request.body:
#             json_data = json.loads(request.body)
#             for i, question in enumerate(questions, start=1):
#                 selected_ans = json_data.get(str(i))
#                 actual_answer = question.answer
#                 if selected_ans == actual_answer:
#                     total_marks += question.marks
        
#         student = Profile.objects.get(user_id=request.user.id)
        
#         # Check if the result already exists
#         # existing_result = QMODEL.Result.objects.filter(exam=course, student=student, marks=total_marks).exists()
#         # result_class, session, term, exam_type
#         existing_result = QMODEL.Result.objects.filter(exam=course, student=student,
#                                                        session = course.session,
#                                                         term = course.term, 
#                                                         result_class =student.student_class,
#                                                         exam_type = course.exam_type,
#                                                        marks=total_marks).exists()
        
#         if not existing_result:
#             # Create a new result only if it doesn't exist
#            existing_result = QMODEL.Result.objects.create(
#                marks=total_marks, 
#                exam=course,
#                term = course.term,
#                exam_type = course.exam_type,
#                session = course.session,
#                student=student, 
#                result_class=student.student_class
#                )
        
#         # Return a JSON response indicating the result of the operation
#         return JsonResponse({'success': True, 'message': 'Marks calculated successfully.'})
    
#     else:
#         return JsonResponse({'success': False, 'error': 'Course ID not found.'})


# @login_required
# def calculate_marks_view(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course = QMODEL.Course.objects.get(id=course_id)
        
#         total_marks = 0
#         questions = QMODEL.Question.objects.filter(course=course).order_by('id')
        
#         if request.body:
#             json_data = json.loads(request.body)
#             for i, question in enumerate(questions, start=1):
#                 selected_ans = json_data.get(str(i))
#                 # print("answers" + str(i), selected_ans)
#                 actual_answer = question.answer
#                 if selected_ans == actual_answer:
#                     total_marks += question.marks
        
#         student = Profile.objects.get(user_id=request.user.id)
#         # result = QMODEL.Result.objects.create(marks=total_marks, exam=course, student=student)
#         existing_result = QMODEL.Result.objects.filter(marks=total_marks, exam=course, student=student).first()
#         if existing_result:
#             # Update the existing result
#             existing_result.marks = total_marks
#             existing_result.save()
#         else:
#             # Create a new result
#             result = QMODEL.Result.objects.create(marks=total_marks, exam=course, student=student)

#         # Redirect to the view_result URL
#         return JsonResponse({'success': True, 'message': 'Marks calculated successfully.'})
    
#     else:
#         return JsonResponse({'success': False, 'error': 'Course ID not found.'})



@cache_page(60 * 15)
@login_required
def exam_warning_view(request):
    qcourses = Course.objects.order_by('id')

    
    context = {
        'courses':qcourses
        }

    return render(request,'student/dashboard/examwarning.html', context = context)

# @login_required
# def view_result_view(request):
#     qcourses = Course.objects.order_by('id')

    
#     context = {
#         'courses':qcourses
#         }

#     return render(request,'student/dashboard/view_result.html', context = context)

@cache_page(60 * 15)
@login_required
def view_result_view(request):
    qcourses = Course.objects.order_by('id')
    context = {
        'courses': qcourses
    }
    return render(request, 'student/dashboard/view_result.html', context)

# @login_required
# def view_result_ajax(request):
#     qcourses = Course.objects.order_by('id').values(
#         'id', 'room_name', 'course_name__title', 'question_number', 
#         'course_pay', 'total_marks', 'num_attemps', 'pass_mark', 
#         'show_questions', 'duration_minutes', 'created', 'updated'
#     )
#     return JsonResponse(list(qcourses), safe=False)


from django.db.models import Count

# @cache_page(60 * 15)
# @login_required
# def check_marks_view(request,pk):
#     course=QMODEL.Course.objects.get(id=pk)
#     student = Profile.objects.get_queryset().order_by('id')
 
#     context = {
#         'results':student,
#         'course':course,
#         'st':request.user,
        
#     }
#     return render(request,'student/check_marks.html', context)


# def verify_certificate(request, certificate_code):
#     certificate = get_object_or_404(Certificate, code=certificate_code, user=request.user)
#     # Perform any additional verification logic here

#     context = {
#         'certificate': certificate,
#     }
#     return render(request, 'student/verify_certificate.html', context)


# download pdf id view
# @login_required
# def pdf_id_view(request, *args, **kwargs):

#     course=QMODEL.Course.objects.all()
#     student = Profile.objects.get(user_id=request.user.id)
#     date = datetime.now()
#     logo = Logo.objects.all() 
#     sign = Signature.objects.all()  # Corrected import
#     design = Designcert.objects.all()
#     pk = kwargs.get('pk')
#     posts = get_list_or_404(course, pk= pk)
#     user_profile =  Profile.objects.filter(user_id = request.user)

#     template_path = 'student/dashboard/certificatepdf.html'

#     students =QMODEL.Student.objects.all()
#     # List to store school names
#     # school_student = get_object_or_404(QMODEL.Student, user=request.user.profile)
#     # Now you can get the associated school for this student
#     user_newuser = get_object_or_404(NewUser, email=request.user)
#     # if user_newuser.school:
#     #     context['school_name'] = user_newuser.school.school_name

#     associated_school =user_newuser.school
#     # Check if there is an associated school
#     if associated_school:
#         school_name = associated_school.school_name
#         principal_name = associated_school.name
#         portfolio = associated_school.portfolio
#         school_logo = associated_school.logo
#         school_sign = associated_school.principal_signature
#         student_name = student.first_name

#         print('principal_name', principal_name)
#         print('portfolio', portfolio)
#         print('school_name',school_name)
#         print('school_logo',school_logo)
#         print('school_sign',school_sign)
#         print('student_name', student_name)
#         student
#     else:
#         print("No associated school for this student.")

 

#     context = {
#         'results': posts,
#         'student':student,
#         'date':date,
#         'course':posts,
#         'logo':logo,
#         'sign':sign,
#         'design':design,
#         # school
#         'school_name':school_name,
#         'school_logo':school_logo,
#         'school_sign':school_sign,
#         'principal_name':principal_name,
#         'portfolio':portfolio,
        
#         }
    
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'
#     # find the template and render it.
#     template = get_template(template_path)
#     html = template.render(context)

#     # create a pdf
#     pisa_status = pisa.CreatePDF(
#        html, dest=response)
#     # if error then show some funny view
#     if pisa_status.err:
#        return HttpResponse('We had some errors <pre>' + html + '</pre>')
   
   
#     return response
    
# @login_required
# def pdf_id_view(request, *args, **kwargs):
#     course = QMODEL.Course.objects.all()
#     student = Profile.objects.get(user_id=request.user.id)
#     date = datetime.now()
#     logo = Logo.objects.all()
#     sign = Signature.objects.all()
#     design = Designcert.objects.all()
#     pk = kwargs.get('pk')
#     posts = get_list_or_404(course, pk=pk)
#     user_profile = Profile.objects.filter(user_id=request.user)

#     template_path = 'student/dashboard/certificatepdf_testing.html'

#     # students = QMODEL.Student.objects.all()

#     # Initialize variables with default values
#     school_name = ''
#     principal_name = ''
#     portfolio = ''
#     school_logo = ''
#     school_sign = ''
#     # student_name = student.first_name

#     # Now you can get the associated school for this student
#     user_newuser = get_object_or_404(NewUser, email=request.user)

#     associated_school = user_newuser.school

#     # Check if there is an associated school
#     if associated_school:
#         school_name = associated_school.school_name
#         principal_name = associated_school.name
#         portfolio = associated_school.portfolio
#         school_logo = associated_school.logo
#         school_sign = associated_school.principal_signature

#     context = {
#         'results': posts,
#         'student': student,
#         'date': date,
#         'course': posts,
#         'logo': logo,
#         'sign': sign,
#         'design': design,
#         # school
#         'school_name': school_name,
#         'school_logo': school_logo,
#         'school_sign': school_sign,
#         'principal_name': principal_name,
#         'portfolio': portfolio,
#     }

#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'

#     # find the template and render it.
#     template = get_template(template_path)
#     html = template.render(context)

#     # create a pdf
#     pisa_status = pisa.CreatePDF(html, dest=response)
    
#     # if error then show some funny view
#     if pisa_status.err:
#         return HttpResponse('We had some errors <pre>' + html + '</pre>')

#     return response
