from django.db.models.aggregates import Count
from django.shortcuts import render,redirect,reverse
from . import models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from teacher import models as TMODEL
# from student.models import  Student
from users.models import NewUser
from users.models import Profile



# views.py

from django.shortcuts import render, redirect
from allauth.account.views import SignupView
from .forms import SimpleSignupForm, SchoolStudentSignupForm
from django.http import HttpResponse

from allauth.account.utils import perform_login
from allauth.socialaccount import signals
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from allauth.account import app_settings




from django.http import HttpResponse

from django.shortcuts import render, redirect


def SchoolStudentView(request):
    if request.method == 'POST':

        form = SchoolStudentSignupForm(request.POST)
        if form.is_valid():
            form.save(request)
            return redirect('sms:myprofile')  # Redirect to a success page
    else:
        form = SchoolStudentSignupForm()

    return render(request, 'users/school_student.html', {'form': form})

from django.views.generic.edit import CreateView
from .forms import SchoolSignupForm  # Import your form
from quiz.models import School  # Import your model
from django.urls import reverse_lazy

class SchoolSignupView(CreateView):
    template_name = 'users/school_registration.html'
    form_class = SchoolSignupForm
    model = School  # Set the model attribute to specify the model to be used
    success_url = reverse_lazy('sms:myprofile')

    def get_queryset(self):
        # Return an empty queryset
        return School.objects.none()

    def form_valid(self, form):
        # Additional logic before saving the form data (if needed)
        # ...

        # Save the form data to the database
        response = super().form_valid(form)

        # Additional logic after saving the form data (if needed)
        # ...

        return response




        

from allauth.account.views import SignupView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# @method_decorator(login_required, name='dispatch')
# class ReferralSignupView(SignupView):
#     template_name = 'users/referrer.html'  # Replace with your actual template path
#     form_class = SimpleSignupForm

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         referral_code = self.kwargs.get('referrer_code', '')
#         context['form'].fields['phone_number'].initial = referral_code
#         context['referrer_code'] = self.request.resolver_match.kwargs.get('referrer_code', '')
#         return context

#     def form_valid(self, form):
#         response = super().form_valid(form)
#         referral_code = form.cleaned_data.get('phone_number', '')

#         # Perform actions with the referral code, e.g., associate it with the user
#         user = self.request.user  # The user object after signup
#         user.phone_number = referral_code
#         user.save()

#         return response
  

from allauth.account.views import SignupView


# class ReferralSignupView(SignupView):
#     template_name = 'users/referrer.html'
#     form_class = SimpleSignupForm  # Default form class

#     def get_form_class(self):
#         referral_code = self.kwargs.get('referrer_code', None)
#         if referral_code:
#             # If there's a referral code in the URL, use the ReferralSignupForm
#             return SimpleSignupForm
#         else:
#             # Otherwise, use the default form class
#             return super().get_form_class()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         referral_code = self.kwargs.get('referrer_code', '')
#         context['form'].fields['phone_number'].initial = referral_code
#         context['referrer_code'] = referral_code
#         return context

#     def form_valid(self, form):
#         response = super().form_valid(form)
#         referral_code = form.cleaned_data.get('phone_number', '')

#         # Perform actions with the referral code, e.g., associate it with the user
#         user = self.request.user  # The user object after signup
#         user.phone_number = referral_code
#         user.save()

#         return response


class ReferralSignupView(SignupView):
    template_name = 'users/referrer.html'  # Replace with your actual template path
    form_class = SimpleSignupForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral_code = self.kwargs.get('referrer_code', '')
        context['form'].fields['phone_number'].initial = referral_code
        context['referrer_code'] = self.request.resolver_match.kwargs.get('referrer_code', '')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        referral_code = form.cleaned_data.get('phone_number', '')

        # Perform actions with the referral code, e.g., associate it with the user
        user = self.request.user  # The user object after signup
        user.phone_number = referral_code
        user.save()
        
        return response


# users/views.py
from django.shortcuts import render, redirect
from .forms import ReferrerMentorForm

def become_referrer(request):
    if request.method == 'POST':
        form = ReferrerMentorForm(request.POST)
        if form.is_valid():
            # Set the referrer field before saving
            form.instance.referrer = request.user
            form.save()
            return redirect('sms:myprofile')  # Redirect to a success page or another URL
    else:
        # Initialize the form with the referrer field hidden
        form = ReferrerMentorForm(initial={'referrer': request.user.pk})

    return render(request, 'users/become_referrer.html', {'form': form})

# def referral_signup(request, referrer_code):
#     # Your referral logic goes here
#     # You can use the referrer_code to identify the referrer and associate it with the signup process
#     # ...

#     return HttpResponse(f"Referral signup page for referrer {referrer_code}")



def take_exams_view(request):
    course = QMODEL.Course.objects.all()
    context = {
        'courses':course
    }
    return render(request, 'student/take_exams.html', context=context)

def start_exams_view(request, pk):

    course = QMODEL.Course.objects.get(id = pk)
    questions = QMODEL.Question.objects.all().filter(course = course)
    context = {
        'course':course,
        'questions':questions
    }
    if request.method == 'POST':
        pass
    response = render(request, 'student/start_exams.html', context=context)
    response.set_cookie('course_id', course.id)
    return response


def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course=QMODEL.Course.objects.get(id=course_id)
        
        total_marks=0
        questions=QMODEL.Question.objects.all().filter(course=course)
        for i in range(len(questions)):
            
            selected_ans = request.COOKIES.get(str(i+1))
            actual_answer = questions[i].answer
            if selected_ans == actual_answer:
                total_marks = total_marks + questions[i].marks
        student = Profile.objects.filter(user_id=request.user.id)
        result = QMODEL.Result()
        result.marks=total_marks
        result.exam=course
        result.student=student
        result.save()

        return HttpResponseRedirect('view_result')
import itertools
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})


from django.db.models import Count

def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = Profile.objects.filter(user_id=request.user.id)
    res= QMODEL.Result.objects.values_list('marks', flat=True).order_by('-marks').distinct()
    stu= QMODEL.Result.objects.values('student','exam','marks').distinct()
    
    vr = QMODEL.Result.objects.values('marks', 'student').annotate(marks_count = Count('marks')).filter(marks_count__gt = 0)
        

    results= QMODEL.Result.objects.order_by('-marks').filter(exam=course).filter(student=student)[:3]
    context = {
        'results':results,
        'course':course,
        'st':request.user,
        'res':res,
        'stu':stu
    }
    return render(request,'student/check_marks.html', context)
