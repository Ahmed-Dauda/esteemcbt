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
from student.models import Signature
from datetime import datetime
from django.http import JsonResponse, HttpResponseForbidden
from .models import Payment, Profile, CertificatePayment, EbooksPayment
from .models import Certificate
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
from student.models import Logo, Designcert
from quiz.models import Result, Course
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders


# from pypaystack import Transaction, Customer, Plan



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
        print("payloadttt:", payload)
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
        print("Referrer URL:", referrer)
        print("amount:", paid_amount)

        # Split the referrer URL by '/'
        url_parts = referrer.split('/')
        content_type = url_parts[-3]
        print("content_type", content_type)
        print('url:', url_parts[-3])

        # retrieving referral codes
        recode = get_object_or_404(NewUser, email = email)
        recode = recode.phone_number
    

        # Check if the last part of the URL is a numeric "id"
        if url_parts[-2].isdigit():
            id_value = url_parts[-2]
            print("Extracted ID:", id_value)
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
# def withdrawal_request(request):
#     if request.method == 'POST':
#         referrer = ReferrerMentor.objects.filter(referrer=request.user.id).first()

#         if referrer and referrer.can_withdraw() and referrer.has_paystack_customer_id():
#             amount = request.POST.get('amount')

#             # Create withdrawal request
#             withdrawal = WithdrawalRequest.objects.create(referrer=referrer, amount=amount, status='pending')
#             referrer.withdrawal_request_status = 'pending'
#             referrer.save()

#             # Process withdrawal using Paystack API
#             paystack_response = process_paystack_withdrawal(referrer.paystack_customer_id, amount)

#             if paystack_response.get('status') == 'success':
#                 # Payment was successful
#                 messages.success(request, 'Withdrawal request submitted successfully.')
#             else:
#                 # Payment failed
#                 withdrawal.status = 'rejected'
#                 withdrawal.save()
#                 messages.error(request, f'Withdrawal request failed: {paystack_response.get("message")}')

#         else:
#             messages.error(request, 'Withdrawal request cannot be processed. Check your balance, request status, or Paystack integration.')

#         return redirect('sms:myprofile')  # Redirect to the dashboard or wherever is appropriate

#     return render(request, 'student/dashboard/withdrawal_form.html')


# def process_paystack_withdrawal(customer_id, amount):
#     # Use Paystack API to initiate withdrawal
#     # Replace 'your_paystack_secret_key' with your actual Paystack secret key
#     paystack_secret_key = settings.PAYSTACK_PUBLIC_KEY
#     withdrawal_url = 'https://api.paystack.co/transfer'
    
#     headers = {
#         'Authorization': f'Bearer {paystack_secret_key}',
#         'Content-Type': 'application/json',
#     }

#     payload = {
#         'source': 'balance',
#         'amount': int(amount) * 100,  # Paystack uses amount in kobo (multiply by 100)
#         'recipient': customer_id,
#     }

#     response = requests.post(withdrawal_url, json=payload, headers=headers)
#     return response.json()


# def withdrawal_request(request):
#     if request.method == 'POST':
#         # Assuming there's only one ReferrerMentor per user, if not, adjust accordingly
#         referrer = ReferrerMentor.objects.filter(referrer=request.user.id).first()

#         if referrer and referrer.can_withdraw():
#             amount = request.POST.get('amount')
#             withdrawal = WithdrawalRequest.objects.create(referrer=referrer, amount=amount, status='pending')
#             referrer.withdrawal_request_status = 'pending'
#             referrer.save()
#             messages.success(request, 'Withdrawal request submitted successfully.')
#         else:
#             messages.error(request, 'Withdrawal request cannot be processed. Check your balance or request status.')

#         return redirect('sms:myprofile')  # Redirect to the dashboard or wherever is appropriate

#     return render(request, 'student/dashboard/withdrawal_form.html')



def pdf_document_list(request):
    documents = PDFDocument.objects.all()
    return render(request, 'student/dashboard/pdf_document_list.html', {'documents': documents})





# def docverify(request, id):

#     secret_key = settings.PAYSTACK_SECRET_KEY
#     api_url = f'https://api.paystack.co/transaction/verify/{id}'
#     headers = {
#         'Authorization': f'Bearer {secret_key}',
#     }

#     response = requests.get(api_url, headers=headers)

#     if response.status_code == 200:
#         data = response.json()  # Parse the JSON response
#         reference = data['data']['reference']
#         amount = data['data']['amount'] / 100
#         email = data['data']['customer']['email']
#         status = data['data']['status']
#         first_name = request.user.profile.first_name
#         last_name = request.user.profile.last_name

#         referrer = data['data']['metadata']['referrer'].strip()
#         print("Referrer URL:", referrer)

#         # Split the referrer URL by '/'
#         url_parts = referrer.split('/')
#         print('u', url_parts)

#         # Check if the last part of the URL is a numeric "id"
#         if url_parts[-2].isdigit():
#             id_value = url_parts[-2]
#             print("Extracted ID:", id_value)
#         else:
#             id_value = None

#         course = get_object_or_404(PDFDocument, pk=id_value)


#         if status == 'success':
#             verified = True

#             # Create the Payment object
#             payment = DocPayment.objects.create(
#                 ref=reference,
#                 first_name=first_name,
#                 last_name=last_name,
#                 payment_user=request.user.profile,
#                 amount=amount,
#                 email=email,
#                 verified=verified
#             )

#             # Add courses to the payment using the 'set()' method
#             if course:
#                 payment.pdfdocument.set([course])

#         data = JsonResponse({'reference': reference})
#     else:
#         data = JsonResponse({'error': 'Payment verification failed.'}, status=400)

#     print('ver', data)
#     return data



# dashboard view
@login_required
def take_exams_view(request):
    course = QMODEL.Course.objects.all()

    # print("no",course)
    current_user = request.user
    print('current user', current_user)

    user_newuser = get_object_or_404(NewUser, email=request.user)
    if user_newuser is not None:
        school_name = user_newuser.school.school_name
        student_class = user_newuser.student_class
        school_name = school_name
        # Fetch the courses associated with the user's school
        school = user_newuser.school
        course_pay = user_newuser.school.course_pay
        course_names = Course.objects.filter(course_pay=course_pay)
        # print("course_names:", course_names)
    else:
        school_name = "Default School Name"
        student_class = "Default Class"    
        print("school_name:", school_name )
        print("student_class", student_class)

    sub_grade = None  # Initialize sub_grade with a default value
    subjects = None  # Initialize subjects with a default value

    # Query the CourseGrade instance associated with the current user
    course_grade = QMODEL.CourseGrade.objects.filter(students__in=[current_user]).first()

    
    if course_grade:
        # If the CourseGrade instance exists, you can access its name and subjects
        sub_grade = course_grade.name
        subjects = course_grade.subjects.all()
        print("Name:", sub_grade)
        print("Subjects:")
        for subject in subjects:
            print(subject)
    else:
       
        print("No CourseGrade instance found for the current user.")
        # Filter out courses that are not in the CourseGrade subjects
  

    context = {
        'courses': course,
        'student_class': student_class,
        'school_name': school_name,
        "sub_grade": sub_grade,
        "subjects": subjects,
        "course_names":course_names,
        'course_pay':course_pay,
        "grades": QMODEL.CourseGrade.objects.all()
    }
    return render(request, 'student/dashboard/take_exams.html', context=context)



# dashboard view
# @login_required
# def subject_take_exams(request):

#     # course = QMODEL.Subjects.objects.all()
#     # # Query all subjects along with their related schools
#     # subjects_with_schools = QMODEL.Subjects.objects.all().prefetch_related('schools')
#     # schools = QMODEL.School.objects.all()
#     # print("sch",schools)
#     # user_newuser = get_object_or_404(NewUser, email=request.user)
#     # if user_newuser.school:
#     #     school_name = user_newuser.school.school_name

#     # Retrieve the current user's group
#     user = request.user
#     # student = get_object_or_404(QMODEL.Student, email=user)
#     # group = student.group
#     # print("User's group:", group)

#     # group_subjects = student.group.subjects
#     # print("User's subjects:", group_subjects)
#     # subject_list = "\n".join(str(subject) for subject in groupw)
#     # print(subject_list)

#     # group_list = group.split(", ")  # Split the string by comma and space

#     # for subject in group_list:
#     #     print('grou',subject)

#     # print("student_school:", student.school)
#     # user_school = student.school
#     # # Retrieve subjects associated with the student
#     # # Query all Subjects objects
#     # subjects = QMODEL.Subjects.objects.all()

#     # Iterate through each Subjects object and retrieve the associated school and course names

#     # groups = QMODEL.Group.objects.all()
#     # Query subjects associated with the user's group
#     # student = QMODEL.Student.objects.filter(group=group).distinct()
#     # # print("student name:", student)
  
#     context = {
#         # 'courses':course,
#         # 'group':group,
#         # 'user_school':user_school,
#         # 'subjects':subjects,
#         # 'schools':schools,
#         # 'groups':groups,
#         # # "school_exam":school_name,
#         # "exam_subject":course_names,
#         # 'group_subjects':group_subjects
#     }
#     return render(request, 'student/dashboard/subject_take_exams.html', context=context)



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



# @login_required
# def subject_start_exams(request, pk):
#     # course = QMODEL.Subjects.objects.get(id=pk)
#     course_name = pk  # If pk is the name itself, no need for pk.name
#     course = get_object_or_404(QMODEL.Subjects, course_name=course_name)
#     questions = QMODEL.Subject_Question.objects.filter(course=course).order_by('id')
#     q_count = questions.count()
#     paginator = Paginator(questions, 200)  # Show 100 questions per page.
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
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
#         'q_count': q_count,
#         'page_obj': page_obj,
#         'remaining_seconds': remaining_seconds,  # Pass remaining time to template
#     }

#     if request.method == 'POST':
#         # Handle form submission
#         pass

#     response = render(request, 'student/dashboard/subject_start_exams.html', context=context)
#     response.set_cookie('course_id', course.id)
#     return response

import random

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def permission_denied_view(request, exception):
    # Redirect the user to the desired page
    return redirect("student:view_result")


@login_required
def start_exams_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    num_attemps = course.num_attemps
    
    questions = QMODEL.Question.objects.filter(course=course).order_by('id')
    q_count = questions.count()
    paginator = Paginator(questions, 200)  # Show 100 questions per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    student = request.user.profile
    # Check if the result exists
    result_exists = Result.objects.filter(student=student, exam=course).exists()
    # Check if the student has already taken this exam
    if result_exists:
        # If the student has already taken the exam, raise PermissionDenied
        return redirect("student:view_result")

    
    # Calculate quiz end time
    quiz_duration = course.duration_minutes
    quiz_start_time = timezone.now()
    quiz_end_time = quiz_start_time + timedelta(minutes=quiz_duration)
    
    # Store the quiz end time in cache
    cache.set(f'quiz_end_time_{course.id}', quiz_end_time, timeout=None)

    # Calculate remaining time until the end of the quiz
    remaining_time = quiz_end_time - timezone.now()
    remaining_seconds = max(int(remaining_time.total_seconds()), 0)

    context = {
        'course': course,
        'questions': questions,
        'num_attemps':num_attemps,
        'result_exists':result_exists,
        'q_count': q_count,
        'page_obj': page_obj,
        'remaining_seconds': remaining_seconds,  # Pass remaining time to template
    }

    if request.method == 'POST':
        # Handle form submission
        pass

    response = render(request, 'student/dashboard/start_exams.html', context=context)
    response.set_cookie('course_id', course.id)
    return response


# complate 
# @login_required
# def start_exams_view(request, pk):
#     course = Course.objects.get(id=pk)
#     num_attemps = course.num_attemps

#     user_newuser = get_object_or_404(NewUser, email=request.user)
#     if user_newuser is not None:
#         school_name = user_newuser.school.school_name
#         students_class = user_newuser.student_class
#         print("student class:", students_class )
#         school_name = school_name
#         # Fetch the courses associated with the user's school
#         school = user_newuser.school
#         course_pay = user_newuser.school.course_pay
#         course_names = Course.objects.filter(course_pay=course_pay)
#         # print("course_names:", course_names)
#     else:
#         school_name = "Default School Name"
#         student_class = "Default Class"    
#         print("school_name:", school_name )
    
#     # print("attemp", course.course_name)
#     student = request.user.profile
#     # Check if the result exists
#     result_exists = Result.objects.filter(student=student, exam=course).exists()
#     # Check if the student has already taken this exam
#     if result_exists:
#         # If the student has already taken the exam, raise PermissionDenied
#         return redirect("student:view_result")

#     # Get the number of questions to display for the course
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

#     # Shuffle the list of selected questions
#     # random.shuffle(questions)

#     q_count = len(questions)  # Calculate the count of questions

#     paginator = Paginator(questions, 200)  # Show 100 questions per page.
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
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
#         'student_class':students_class,
#         'num_attemps':num_attemps,
#         'questions': questions,
#         'q_count': q_count,
#         'page_obj': page_obj,
#         'pk': pk,
#         'result_exists':result_exists,
#         'remaining_seconds': remaining_seconds,  # Pass remaining time to template
#     }

#     if request.method == 'POST':
#         # Handle form submission
#         pass

#     response = render(request, 'student/dashboard/start_exams.html', context=context)
#     response.set_cookie('course_id', course.id)
#     return response


# def start_exams_view(request, pk):
#     course = Course.objects.get(id=pk)
#     # Get the number of questions to display for the course
#     show_questions = course.show_questions
#     # Retrieve all questions for the course
#     all_questions = QMODEL.Question.objects.filter(course=course)
#     # Count the total number of questions
#     total_questions = all_questions.count()
    
#     # If there are enough questions, select a random subset
#     if total_questions >= show_questions:
#         # Randomly select indices for the questions
#         random_indices = random.sample(range(total_questions), show_questions)
#         # Filter questions based on the random indices
#         questions = [all_questions[index] for index in random_indices]
#     else:
#         # If there are not enough questions, display all questions
#         questions = all_questions

#     # Shuffle the list of selected questions
#     # random.shuffle(questions)

#     q_count = len(questions)  # Calculate the count of questions

#     paginator = Paginator(questions, 200)  # Show 100 questions per page.
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
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
#         'q_count': q_count,
#         'page_obj': page_obj,
#         'remaining_seconds': remaining_seconds,  # Pass remaining time to template
#     }

#     if request.method == 'POST':
#         # Handle form submission
#         pass

#     response = render(request, 'student/dashboard/start_exams.html', context=context)
#     response.set_cookie('course_id', course.id)
#     return response


# @login_required
# def start_exams_view(request, pk):
#     course = QMODEL.Course.objects.get(id=pk)
#     # Get the number of questions to display for the course
#     show_questions = course.show_questions
#     # Retrieve questions for the course
#     questions = QMODEL.Question.objects.filter(course=course).order_by('id')[:show_questions]
#     print("show q", questions)
#     q_count = questions.count()
#     # questions = QMODEL.Question.objects.filter(course=course).order_by('id')
#     # q_count = questions.count()

#     paginator = Paginator(questions, 200)  # Show 100 questions per page.
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     # Calculate quiz end time
#     quiz_duration = course.duration_minutes
#     quiz_start_time = timezone.now()
#     quiz_end_time = quiz_start_time + timedelta(minutes=quiz_duration)
    
#     # Store the quiz end time in cache
#     cache.set(f'quiz_end_time_{course.id}', quiz_end_time, timeout=None)

#     # Calculate remaining time until the end of the quiz
#     remaining_time = quiz_end_time - timezone.now()
#     remaining_seconds = max(int(remaining_time.total_seconds()), 0)

#     # updating timer

#     # if request.method == 'POST':
#     #     timer_data = request.POST.get('timer_data')
#     #     # Split the timer data into minutes and seconds
#     #     minutes, seconds = timer_data.split(':')
        
#     #     # Convert minutes and seconds to integers
#     #     minutes = int(minutes)
#     #     seconds = int(seconds)
        
#     #     # Calculate the total duration in minutes
#     #     total_minutes = minutes + seconds / 60
#     #     print("total_minutes", total_minutes)
        
#     #     # Update the model with the total duration
#     #     instance.duration_minutes = total_minutes
#     #     instance.save()
        
#     #     return JsonResponse({'status': 'success'})



#     context = {
#         'course': course,
#         'questions': questions,
#         'q_count': q_count,
#         'page_obj': page_obj,
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

# school calculate marks view

# @login_required
# def subject_calculate_marks(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course = QMODEL.Subjects.objects.get(id=course_id)
        
#         total_marks = 0
#         questions = QMODEL.Subject_Question.objects.filter(course=course).order_by('id')
        
#         if request.body:
#             json_data = json.loads(request.body)
#             for i, question in enumerate(questions, start=1):
#                 selected_ans = json_data.get(str(i))
#                 print("answers" + str(i), selected_ans)
#                 actual_answer = question.answer
#                 if selected_ans == actual_answer:
#                     total_marks += question.marks
        
#         student = Profile.objects.get(user_id=request.user.id)
#         result = QMODEL.Subject_Result.objects.create(marks=total_marks, exam=course, student=student)
        
#         # Redirect to the view_result URL
#         return JsonResponse({'success': True, 'message': 'Marks calculated successfully.'})
    
#     else:
#         return JsonResponse({'success': False, 'error': 'Course ID not found.'})



# example 2

from django.db.models import F

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
#         # Check if a result already exists for this course and student
#         existing_result = QMODEL.Result.objects.filter(exam=course, student=student).first()
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

# quizapp/tasks.py

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
                # print("answers" + str(i), selected_ans)
                actual_answer = question.answer
                if selected_ans == actual_answer:
                    total_marks += question.marks
        
        student = Profile.objects.get(user_id=request.user.id)
        result = QMODEL.Result.objects.create(marks=total_marks, exam=course, student=student)
        
        # Redirect to the view_result URL
        return JsonResponse({'success': True, 'message': 'Marks calculated successfully.'})
    
    else:
        return JsonResponse({'success': False, 'error': 'Course ID not found.'})


# @login_required
# def calculate_marks_view(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course=QMODEL.Course.objects.get(id=course_id)
        
#         total_marks=0
#         questions=QMODEL.Question.objects.get_queryset().filter(course=course).order_by('id')
#         for i in range(len(questions)):
            
#             # selected_ans = request.COOKIES.get(str(i+1))
#             selected_ans = request.POST.get(str(i+1))
#             print("answers1", selected_ans)
#             actual_answer = questions[i].answer
#             if selected_ans == actual_answer:
#                 total_marks = total_marks + questions[i].marks
#         student = Profile.objects.get(user_id=request.user.id)
#         result = QMODEL.Result()
        
#         result.marks=total_marks 
#         result.exam=course
#         result.student=student
#         # m = QMODEL.Result.objects.aggregate(Max('marks'))
#         # max_q = Result.objects.filter(student_id = OuterRef('student_id'),exam_id = OuterRef('exam_id'),).order_by('-marks').values('id')
#         # max_result = Result.objects.filter(id__in = Subquery(max_q[:1]), exam=course, student=student)
        
#         result.save()
#         # score = 0
#         # for max_value in max_result:
#         #     score = score + max_value.marks
            
#         # if total_marks > score:
            
#         return HttpResponseRedirect('view_result')
#     else:
#         return HttpResponseRedirect('take-exam')
# subject_view_result.html



@login_required
def exam_warning_view(request):
    qcourses = Course.objects.order_by('id')

    
    context = {
        'courses':qcourses
        }

    return render(request,'student/dashboard/examwarning.html', context = context)

@login_required
def view_result_view(request):
    qcourses = Course.objects.order_by('id')

    
    context = {
        'courses':qcourses
        }

    return render(request,'student/dashboard/view_result.html', context = context)


from django.db.models import Count

@login_required
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = Profile.objects.get_queryset().order_by('id')
 
    context = {
        'results':student,
        'course':course,
        'st':request.user,
        
    }
    return render(request,'student/check_marks.html', context)






def verify_certificate(request, certificate_code):
    certificate = get_object_or_404(Certificate, code=certificate_code, user=request.user)
    # Perform any additional verification logic here

    context = {
        'certificate': certificate,
    }
    return render(request, 'student/verify_certificate.html', context)


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
    
@login_required
def pdf_id_view(request, *args, **kwargs):
    course = QMODEL.Course.objects.all()
    student = Profile.objects.get(user_id=request.user.id)
    date = datetime.now()
    logo = Logo.objects.all()
    sign = Signature.objects.all()
    design = Designcert.objects.all()
    pk = kwargs.get('pk')
    posts = get_list_or_404(course, pk=pk)
    user_profile = Profile.objects.filter(user_id=request.user)

    template_path = 'student/dashboard/certificatepdf_testing.html'

    # students = QMODEL.Student.objects.all()

    # Initialize variables with default values
    school_name = ''
    principal_name = ''
    portfolio = ''
    school_logo = ''
    school_sign = ''
    # student_name = student.first_name

    # Now you can get the associated school for this student
    user_newuser = get_object_or_404(NewUser, email=request.user)

    associated_school = user_newuser.school

    # Check if there is an associated school
    if associated_school:
        school_name = associated_school.school_name
        principal_name = associated_school.name
        portfolio = associated_school.portfolio
        school_logo = associated_school.logo
        school_sign = associated_school.principal_signature

    context = {
        'results': posts,
        'student': student,
        'date': date,
        'course': posts,
        'logo': logo,
        'sign': sign,
        'design': design,
        # school
        'school_name': school_name,
        'school_logo': school_logo,
        'school_sign': school_sign,
        'principal_name': principal_name,
        'portfolio': portfolio,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'

    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return response
