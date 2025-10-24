from asyncio import constants
from tokenize import group
from unittest import result
from sweetify.views import SweetifySuccessMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import forms
from django.db import models
from django.utils.decorators import method_decorator
from django.db.models import fields
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from student.models import ReferrerMentor
from django.conf import settings
from django.http import JsonResponse
from django.core.paginator import Paginator
import uuid
from django.http import FileResponse
from hitcount.utils import  get_hitcount_model
from hitcount.views import HitCountMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.core.paginator import Paginator    
from django.db.models import Count
import numpy as np
from django.contrib.auth import logout
from django.db.models import Max, Subquery, OuterRef
# from .forms import BlogcommentForm
from django.contrib.auth.decorators import login_required
# password reset import
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
# from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib import messages #import messages
from student.models import PDFDocument, PDFGallery, Directors, Management
# end password reset import.
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from hitcount.views import HitCountDetailView
# from django.contrib.auth import get_user_model
# User = get_user_model()
# cloudinary import libraries
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.views.generic import ListView
from django.http import JsonResponse
from django.core.paginator import Paginator
from profile import Profile as NewProfile
from student.models import EbooksPayment, PDFDocument, Payment, CertificatePayment
from quiz import models as QMODEL
from quiz.models import Result, Course
from users.models import NewUser, Profile
# from users.forms import SimpleSignupForm
from sms.forms import PaymentForm
from student.models import Clubs
from django.views.decorators.cache import cache_page
from django.views.generic import ListView
from .models import AboutUs, Awards
from student.models import AdvertisementImage
from .models import Courses, CarouselImage, FrontPageVideo
from student.models import PDFDocument
from django.views.generic import DetailView
from django.urls import reverse_lazy
from django.views import View
from django.http import Http404
import logging
from student.models import ReferrerMentor
from student.forms import ReferrerMentorUpdateForm
# views.py




from sms.models import (Categories, Courses, 
                        Gallery,
                          FrequentlyAskQuestions,
                          CourseFrequentlyAskQuestions,
                          CourseLearnerReviews, Session, Term, ExamType,
                        )



class Categorieslistview(LoginRequiredMixin, ListView):
    model = Categories
    template_name = 'sms/home.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
   
    def get_queryset(self):
        return Categories.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = NewUser.objects.all().count()
        context['category'] = Categories.objects.count()
        context['courses'] = Courses.objects.all().count()
        context['user'] = NewUser.objects.get_queryset().order_by('id')
        
        return context
    


# dashboard view
class Category(LoginRequiredMixin, ListView):
    model = Categories
    template_name = 'sms/dashboard/index.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
   
    def get_queryset(self):
        return Categories.objects.all()



class Table(LoginRequiredMixin, ListView):
    model = Categories
    template_name = 'sms/dashboard/tables.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
   
    def get_queryset(self):
        return Categories.objects.all()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = NewUser.objects.all().count()

        return context
    


   
@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class AwardView(ListView):
    model = Awards
    template_name = 'sms/dashboard/awards.html'
    context_object_name = 'awards_list'
    paginate_by = 10  # Number of awards per page

    def get_queryset(self):
        return Awards.objects.only('title', 'img_about_us', 'content')  # Only fetch necessary fields
    


@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class AboutUsView(ListView):
    model = AboutUs
    template_name = 'sms/dashboard/about_us.html'
    context_object_name = 'about_us_list'

    def get_queryset(self):
        return AboutUs.objects.only('title', 'img_about_us', 'content')  # Only fetch necessary fields
    

# class AboutUsView(ListView):
#     model = AboutUs
#     template_name = 'sms/dashboard/about_us.html'
#     context_object_name = 'about_us_list'


@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class ManagementView(ListView):
    models = Management
    template_name = 'sms/dashboard/managements.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True

    def get_queryset(self):
        return Management.objects.only('title','desc','img_ebook')  # Only fetch necessary fields
    
   
    # def get_queryset(self):
    #     # return  Courses.objects.all().select_related('categories').distinct()
    #      return Management.objects.all().order_by('id') 
    
    # def get_context_data(self, **kwargs): 
    #     context = super(ManagementView, self).get_context_data(**kwargs)
    #     context['alert_homes'] = self.get_queryset()
        
    #     return context
    

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class DirectorsView(ListView):
    models = Directors
    template_name = 'sms/dashboard/directors.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True

    def get_queryset(self):
        return Directors.objects.only('title','desc','img_ebook')  # Only fetch necessary fields
    
   
    

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class PDFGalleryView(ListView):
    models = PDFGallery
    template_name = 'sms/dashboard/pdf_gallery.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True

    def get_queryset(self):
        return PDFGallery.objects.only('title','desc','img_ebook', 'pdf_url')  # Only fetch necessary fields
    
   
    # def get_queryset(self):
    #     # return  Courses.objects.all().select_related('categories').distinct()
    #      return PDFGallery.objects.all() 
    
    # def get_context_data(self, **kwargs): 
    #     context = super(PDFGalleryView, self).get_context_data(**kwargs)
    #     context['alert_homes']  = PDFGallery.objects.order_by('-created')
        
    #     return context

from teacher.models import Teacher

def some_view(request):
    # Assuming the user is logged in and has a school attribute
    username = request.user.username
    user_school = request.user.school

    teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught', 'classes_taught').get(username=username)
    teacher_school = teacher.school
    print(teacher.school, 'sc')
    context = {
        'user_school':user_school,
        'teacher_school':teacher_school

    }

    return render(request, 'sms/dashboard/teacherbase.html', context= context)

# @method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class DigitalForm(ListView):
    model = PDFDocument
    template_name = 'sms/dashboard/digital_form.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
   
    def get_queryset(self):
        return PDFDocument.objects.all()
    # def get_queryset(self):
    #     return PDFGallery.objects.only('title','desc','img_ebook','pdf_url')  # Only fetch necessary fields
    
    
    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs)
        # context['alert_homes'] = PDFDocument.objects.order_by('-created')
        context['alert_homes'] = PDFDocument.objects.order_by('-created')
        
        # Cache-Control headers for PDF documents
        for document in context['alert_homes']:
            response = HttpResponse()
            response['Cache-Control'] = 'public, max-age=3600'
            document.cache_control = response['Cache-Control']
        
        return context
    


@method_decorator(cache_page(60 * 40), name='dispatch')  # Cache for 15 minutes
class Homepage(ListView):
    model = Courses
    template_name = 'sms/dashboard/homepage1.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True

    def get_queryset(self):
        return Courses.objects.all() 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add CarouselImage queryset to the context
        context['carousel_images'] = CarouselImage.objects.all()
        context['front_page_videos'] = FrontPageVideo.objects.all()
        context['faqs'] = FrequentlyAskQuestions.objects.all()
        context['alerts'] = PDFDocument.objects.order_by('-created')
        context['alert_count_homes'] = PDFDocument.objects.order_by('-created')[:4].count() 
        context['alert_count'] = PDFDocument.objects.all().count()
        context['advertisement_images'] = AdvertisementImage.objects.all()

        # Cache-Control headers for carousel images
        for image in context['carousel_images']:
            image.cache_control = 'public, max-age=3600'

        return context
    


from student.models import DocPayment

# important
class pdfpaymentconfirmation(HitCountDetailView, LoginRequiredMixin, DetailView):

    models = PDFDocument
    template_name = 'student/dashboard/pdfpaymentconfirmation.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
     
    def get_queryset(self):
        return PDFDocument.objects.all()

    def get_context_data(self,*args , **kwargs ):

        context = super().get_context_data(**kwargs)
        document = get_object_or_404(PDFDocument, pk=self.kwargs['pk'])
        context['document'] = document
        user = self.request.user.profile
        # Query the Payment model to get all payments related to the user and course
        related_payments = DocPayment.objects.filter(payment_user=user, pdfdocument = document)
        # print(related_payments)
        context['related_payments'] = related_payments
        context['refs'] = related_payments.values_list('ref', flat=True)
        
        enrollment_count = related_payments.count()
        # Print or use the enrollment_count as needed
        context['enrollment_count'] = enrollment_count + 100
    
        context['paystack_public_key']  = settings.PAYSTACK_PUBLIC_KEY


        return context


# important

class gotopdfconfirmpage(HitCountDetailView,LoginRequiredMixin, DetailView):

    models = PDFDocument
    template_name = 'student/dashboard/gotoconfirmationpage.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
     
    def get_queryset(self):
        return PDFDocument.objects.all()

    def get_context_data(self,*args , **kwargs ):

        context = super().get_context_data(**kwargs)
        document = get_object_or_404(PDFDocument, pk=self.kwargs['pk'])
        context['document'] = document
        user = self.request.user.profile
        # Query the Payment model to get all payments related to the user and course
        related_payments = DocPayment.objects.filter(payment_user=user, pdfdocument = document)
        print(related_payments)
        context['related_payments'] = related_payments
        context['refs'] = related_payments.values_list('ref', flat=True)
        
        
        return context



# important

@method_decorator(cache_page(60 * 30), name='dispatch')
class PDFDocumentDetailView(LoginRequiredMixin, DetailView):
    model = Courses
    template_name = 'student/dashboard/pdf_document_detail1.html'  # Update with your actual template name
    def get(self, request, *args, **kwargs):
        document = self.get_object()
        
        user = self.request.user
        course = get_object_or_404(Courses, pk=self.kwargs['pk'])
        # Query the Payment model to get all payments related to the user and document
        related_payments = EbooksPayment.objects.filter(email=user, amount=course.price)
        enrollment_count = related_payments.count()
        # Print or use the enrollment_count as needed
        enrollment_count += 100

        # Check if the request is a download request
        if request.GET.get('download'):
            # Prepare the response using FileResponse
            response = FileResponse(document.pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
            return response
        
        context = {
            'document': document,
            'related_payments': related_payments,
            'enrollment_count': enrollment_count,
        }

        return render(request, self.template_name, context=context)


@method_decorator(cache_page(60 * 15), name='dispatch')
class ClubsListView(ListView):
    model = Clubs
    template_name = 'student/dashboard/clubs_list.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.get_queryset()  # Use self.get_queryset() instead of Clubs.objects.all()
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')
class Clubs(HitCountDetailView,LoginRequiredMixin,DetailView):
    models =  Clubs
    template_name = 'student/dashboard/clubs.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
     
    def get_queryset(self):
        return Clubs.objects.all()

    def get_context_data(self,*args , **kwargs ):
        context = super().get_context_data(**kwargs)
        document = get_object_or_404(Clubs, pk=self.kwargs['pk'])
        course = Clubs.objects.get(pk=self.kwargs["pk"])
        context['document'] = document
        user = self.request.user
        related_payments = EbooksPayment.objects.filter(email=user, content_type=course, amount=course.price)
        # related_payments = Payment.objects.filter(email=user, courses__title=object.title, amount=object.price)
        context['related_payments'] = related_payments
        context['paystack_public_key']  = settings.PAYSTACK_PUBLIC_KEY

        
        return context


@method_decorator(cache_page(60 * 15), name='dispatch')
class GalleryDetailView(HitCountDetailView,DetailView):
    models = PDFGallery
    template_name = 'student/dashboard/gallerydetails.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
     
    def get_queryset(self):
        return PDFGallery.objects.all()


    def get_context_data(self,*args , **kwargs ):
        context = super().get_context_data(**kwargs)
        document = get_object_or_404(PDFGallery, pk=self.kwargs['pk'])
        
        course = PDFGallery.objects.get(pk=self.kwargs["pk"])
        context['document'] = document
      
        user = self.request.user

        return context


@method_decorator(cache_page(60 * 5), name='dispatch')
class Ebooks(HitCountDetailView,DetailView):
    models = PDFDocument
    template_name = 'student/dashboard/ebooks.html'
    success_message = 'TestModel successfully updated!'
    count_hit = True
     
    def get_queryset(self):
        return PDFDocument.objects.all()

    def get_context_data(self,*args , **kwargs ):
        context = super().get_context_data(**kwargs)
        document = get_object_or_404(PDFDocument, pk=self.kwargs['pk'])
        course = PDFDocument.objects.get(pk=self.kwargs["pk"])
        context['document'] = document 
        user = self.request.user
        related_payments = EbooksPayment.objects.filter(email=user, content_type=course, amount=course.price)
        # related_payments = Payment.objects.filter(email=user, courses__title=object.title, amount=object.price)
        context['related_payments'] = related_payments
        # context['paystack_public_key']  = settings.PAYSTACK_PUBLIC_KEY

        
        return context

