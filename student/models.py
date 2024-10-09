from django.contrib import admin
from django.db.models import Count, Q
from django.db.models import Count, Sum
from users.models import NewUser
from quiz import models as QMODEL
import secrets
from django.conf import settings
import uuid
import random
import string
from django.contrib import messages
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from users.models import Profile 
import secrets
from django.db import models
from sms.paystack import Paystack  # Assuming the Paystack class is imported correctly
from django.utils import timezone
from sms.models import Courses
from cloudinary.models import CloudinaryField


# class Question(models.Model):
#     # topic = models.ForeignKey(Topics, on_delete=models.CASCADE)
#     text = models.TextField()

#     def __str__(self):
#         return self.text

# class Choice(models.Model):
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     text = models.CharField(max_length=200)
#     is_correct = models.BooleanField(default=False)

#     def __str__(self):
#         return self.text


def generate_certificate_code():
    code_length = 10
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(code_length))


# class Certificate(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null= True)
#     code = models.CharField(max_length=10, unique=True, default=generate_certificate_code)
#     holder = models.CharField(max_length=255, null= True)
#     issued_date = models.DateField(null= True)

#     # Add any additional fields relevant to the certificate

#     def __str__(self):
#         return self.holder



# class Logo(models.Model):
   
#    logo = CloudinaryField('image', blank=True, null= True)
   
#    def __str__(self):
#         return f"{self.logo}"

# class PartLogo(models.Model):
   
#    logo = CloudinaryField('image', blank=True, null= True)
   
#    def __str__(self):
#         return f"{self.logo}"
   
# class Signature(models.Model):
       
#    sign = CloudinaryField('image', blank=True, null= True)
   
#    def __str__(self):
#         return f"{self.sign}"  

# class Designcert(models.Model):
       
#    design = CloudinaryField('image', blank=True, null= True)
   
#    def __str__(self):
#         return f"{self.design}"  

from quiz.models import School

class ExamStatistics(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    total_exams_conducted = models.PositiveIntegerField(default=0)
    session = models.CharField(max_length=20, blank=True, null=True)
    term = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school} - {self.session} - {self.term} - {self.total_exams_conducted}"
    
from quiz.models import Result, Course

class Badge(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    session = models.CharField(max_length=120, blank=True, null=True)
    term = models.CharField(max_length=120, blank=True, null=True)
    badge_type = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    final_average = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Field for final average
    final_grade = models.CharField(max_length=2, blank=True, null=True)  # Field for final grade (e.g., A, B, C)

    def __str__(self):
        return f"{self.student.first_name} - Session: {self.session}, Term: {self.term}, Badge: {self.description}, Final Grade: {self.final_grade}"


from django.utils import timezone
from django.conf import settings

class BadgeDownloadStats(models.Model):
    school = models.ForeignKey('quiz.School', on_delete=models.CASCADE, blank=True, null=True)  # Replace 'yourapp' with your actual app name
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, blank=True, null=True)
    month = models.PositiveIntegerField( blank=True, null=True)  # Store the month (1-12)
    year = models.PositiveIntegerField( blank=True, null=True)  # Store the year
    download_count = models.PositiveIntegerField(default=0)  # Track download count for the month

    class Meta:
        unique_together = ('school', 'badge', 'month', 'year')  # Prevent duplicate entries for same month/year
        ordering = ['year', 'month']

    def __str__(self):
        return f"{self.school} - {self.badge} ({self.month}/{self.year})"


class Clubs(models.Model):
    title = models.CharField(max_length=200)
    desc = models.TextField()
    img_ebook = CloudinaryField('Clubs images', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, default='500', max_length=225, blank=True, null=True)
    # pdf_file = models.FileField(upload_to='pdf_documents/')  
    pdf_url = models.URLField(blank=True, null=True)  # Add the URL field for Google Drive PDF link
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"{self.title}"


class PDFGallery(models.Model):
    title = models.CharField(max_length=200)
    desc = models.TextField()
    img_ebook = CloudinaryField('gallery images', blank=True, null=True)
    pdf_url = models.URLField(blank=True, null=True)  # Add the URL field for Google Drive PDF link
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"{self.title}"



class Directors(models.Model):
    title = models.CharField(max_length=200)
    desc = models.TextField()
    img_ebook = CloudinaryField('directors images', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"{self.title}"


class Management(models.Model):
    title = models.CharField(max_length=200)
    desc = models.TextField()
    img_ebook = CloudinaryField('management images', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"{self.title}"


class PDFDocument(models.Model):
    title = models.CharField(max_length=200)
    desc = models.TextField()
    img_ebook = CloudinaryField('Ebook images', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, default='500', max_length=225, blank=True, null=True)
    # pdf_file = models.FileField(upload_to='pdf_documents/')  
    pdf_url = models.URLField(blank=True, null=True)  # Add the URL field for Google Drive PDF link
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"{self.title}"



class EbooksPayment(models.Model):
    payment_user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    courses = models.ManyToManyField(PDFDocument, related_name='ebooks')
    amount = models.PositiveBigIntegerField(null=True)
    ref = models.CharField(max_length=250, null=True)
    first_name = models.CharField(max_length=250, null=True)
    last_name = models.CharField(max_length=200, null=True)
    content_type = models.CharField(max_length=200, null=True)
    email = models.EmailField(null=True)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        # Get a comma-separated list of course titles
        # course_titles = ', '.join(course.title for course in self.courses.all())
        return f"{self.payment_user} - {self.content_type} Payment - Amount: {self.amount}"

from quiz.models import Result, Course

class CertificatePayment(models.Model):
    payment_user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    courses = models.ManyToManyField(Course,related_name='certificates',blank=True)
    amount = models.PositiveBigIntegerField(null=True)
    # user_association = models.ForeignKey(NewUser, on_delete=models.CASCADE, null=True)
    # referral_code = models.CharField(max_length=250, null=True, blank=True)
    ref = models.CharField(max_length=250, null=True)
    f_code = models.CharField(max_length=200, null=True, blank=True)
    first_name = models.CharField(max_length=250, null=True)
    last_name = models.CharField(max_length=200, null=True)
    content_type = models.CharField(max_length=200, null=True)
    email = models.EmailField(null=True)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    # def __str__(self):
    #     return self.content_type

    def __str__(self):
        
    # Get a comma-separated list of course titles
        course_t = ', '.join(course.course_name.title for course in self.courses.all())
        return f"{self.payment_user} - {self.content_type} Payment - Amount: {self.amount} - Courses: {course_t}"



class DocPayment(models.Model):
    payment_user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    pdfdocument = models.ManyToManyField(PDFDocument, related_name='docpayments')
    amount = models.PositiveBigIntegerField(null=True)
    ref = models.CharField(max_length=250, null=True)
    first_name = models.CharField(max_length=250, null=True)
    last_name = models.CharField(max_length=200, null=True)
    email = models.EmailField(null=True)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):

        # Get a comma-separated list of course titles
        course_titles = ', '.join(course.title for course in self.pdfdocument.all())
        return f"{self.payment_user} {self.amount} {course_titles}"



class Payment(models.Model):
    payment_user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    courses = models.ManyToManyField(Courses, related_name='payments', blank=True)
    amount = models.PositiveBigIntegerField(null=True)
    ref = models.CharField(max_length=250, null=True)
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    content_type = models.CharField(max_length=200, null=True)
    # referral_code = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        # Get a comma-separated list of course titles
        course_titles = ', '.join(course.title for course in self.courses.all())
        return f"{self.payment_user} - {self.content_type} Payment - Amount: {self.amount} - Courses: {course_titles}"


from django.urls import reverse
from django import forms

class ReferrerMentor(models.Model):
    name = models.CharField(max_length=20, blank=True, null=True)
    courses = models.ManyToManyField(Courses, related_name='referrercourses', blank=True)
    referrer_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    # referrer_code = models.CharField(max_length=20, blank=True, null=True)
    # paystack_customer_id = models.CharField(max_length=255, blank=True, null=True)
    referrer = models.ForeignKey(NewUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_users')
    referred_students = models.ManyToManyField(NewUser, related_name='referrer_profiles', blank=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    bank = models.CharField(max_length=50, blank=True, null=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def get_referral_url(self):
        return reverse('referral_signup', args=[str(self.referrer_code)])
    
    @property
    def count_of_students_referred(self):
        phone_numbers = NewUser.objects.filter(phone_number=self.referrer_code)
        return phone_numbers.count()
    
    @property
    def referred_students_count(self):
        return self.referred_students.count()
    
    @property
    def referred_students_phone_numbers(self):
        return self.referred_students.values_list('phone_number', flat=True)
    

    @property
    def f_code_count(self):
        return CertificatePayment.objects.filter(f_code=self.referrer_code).count()

    @property
    def total_amount(self):
        return CertificatePayment.objects.filter(f_code=self.referrer_code).aggregate(Sum('amount'))['amount__sum']

    @property
    def related_payments(self):
        return CertificatePayment.objects.filter(f_code=self.referrer_code)
    
    def __str__(self):
        return f'Referrer Profile for {self.name}'

@receiver(pre_save, sender=ReferrerMentor)
def generate_referrer_code(sender, instance, **kwargs):
    if not instance.referrer_code:
        # Generate a unique code using uuid
        unique_identifier = str(uuid.uuid4().hex)[:10]
        instance.referrer_code = f"cta{unique_identifier}"


# models.py

# class WithdrawalRequest(models.Model):
#     referrer = models.ForeignKey(ReferrerMentor, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Rejected')], default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Image {self.amount}"



class AdvertisementImage(models.Model):
    # img_ebook = CloudinaryField('Ebook images', blank=True, null=True)
    image =CloudinaryField('advertisement_images', blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Image {self.id}"
