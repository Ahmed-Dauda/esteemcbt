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
from quiz.models import Course

# In your models.py

# Add at the top if not already present
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ExamAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('quiz.Course', on_delete=models.CASCADE)

    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    remaining_seconds = models.IntegerField(default=0)

    # THIS IS THE IMPORTANT PART
    saved_answers = models.JSONField(default=dict, blank=True, null=True)
    tab_switch_count = models.PositiveIntegerField(default=0)
    is_submitted = models.BooleanField(default=False)
    resume_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    # In your models.py (where ExamAttempt is defined)

    blur_count = models.PositiveIntegerField(default=0)
    screenshot_count = models.PositiveIntegerField(default=0)

    class Meta:
        
        indexes = [
            # Fast lookup of active attempts by student (most frequent)
            models.Index(fields=['student', 'is_submitted'], name='idx_attempt_student_active'),
            # Fast lookup by resume_code (when resuming after power loss)
            models.Index(fields=['resume_code'], name='idx_attempt_resume_code'),
            # For dashboard/reporting: filter by course and submission status
            models.Index(fields=['course', 'is_submitted'], name='idx_attempt_course_active'),
            # For time‑based queries (e.g., cleanup old attempts)
            models.Index(fields=['start_time'], name='idx_attempt_start_time'),
            # Composite index for the unique_together fields (PostgreSQL uses it automatically, but explicit helps)
            models.Index(fields=['student', 'course', 'is_submitted'], name='idx_attempt_unique_key'),
        ]


class ExamEventLog(models.Model):
    """
    Audit trail for power outages, resumes, auto‑saves, submissions.
    """
    EVENT_TYPES = [
        ('exam_started', 'Exam Started'),
        ('auto_save', 'Auto Save'),
        ('power_outage', 'Power Outage'),
        ('exam_resumed', 'Exam Resumed'),
        ('exam_submitted', 'Exam Submitted'),
        ('heartbeat', 'Heartbeat'),
    ]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('quiz.Course', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    details = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'timestamp']),
            models.Index(fields=['course', 'event_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.student} - {self.event_type} at {self.timestamp}"
    


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


class AdmissionLetter(models.Model):
    student  = models.ForeignKey('users.Profile', on_delete=models.CASCADE,
                                 related_name='admission_letters')
    school   = models.ForeignKey('quiz.School', on_delete=models.CASCADE,
                                 related_name='admission_letters')
    session  = models.ForeignKey('sms.Session', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='admission_letters')

    class_offered   = models.CharField(max_length=20)
    subject_scores  = models.JSONField(default=dict)
    average_score   = models.DecimalField(max_digits=5, decimal_places=2)
    pass_threshold  = models.DecimalField(max_digits=5, decimal_places=2)

    deposit_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=750000)
    payment_deadline = models.DateField(null=True, blank=True)
        # ── Editable overrides (blank = fall back to auto-generated value) ──
    letter_date          = models.DateField(null=True, blank=True)
    payment_deadline     = models.DateField(null=True, blank=True)
    resume_date          = models.DateField(null=True, blank=True)

    override_student_name   = models.CharField(max_length=255, blank=True, default='')
    override_guardian_name  = models.CharField(max_length=255, blank=True, default='')
    override_guardian_address = models.TextField(blank=True, default='')
    override_principal_name = models.CharField(max_length=255, blank=True, default='')
    override_deposit_words  = models.CharField(max_length=255, blank=True, default='')
    override_deposit_display = models.CharField(max_length=50, blank=True, default='')
    extra_note              = models.TextField(blank=True, default='',
    help_text="Optional paragraph appended above the numbered notes.")
    acceptance_deadline = models.DateField(null=True, blank=True)

    # ── Body overrides (blank = use auto-generated paragraph) ─────────
    override_intro = models.TextField(
        blank=True, default='',
        help_text="Replaces the 'The Management of…' paragraph. "
                  "Available vars: {student_name} {class_label} {session_name}")
    override_deposit_para = models.TextField(
        blank=True, default='',
        help_text="Replaces the 'Paying a deposit…' paragraph. "
                  "Available vars: {deposit_words} {deposit_display} {bank_name} "
                  "{bank_account} {bank_account_name} {payment_deadline} {resume_date}")
    override_notes_text = models.TextField(
        blank=True, default='',
        help_text="Replaces the numbered notes. One note per line — each non-blank "
                  "line becomes a numbered item. Available vars: {payment_deadline} "
                  "{acceptance_deadline} {acceptance_email_1} {acceptance_email_2}")
    

    pdf_file     = models.FileField(upload_to='admission_letters/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    sent_at      = models.DateTimeField(null=True, blank=True)
    is_sent      = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'session')
        indexes = [
            models.Index(fields=['school', 'session']),
            models.Index(fields=['is_sent']),
        ]

    def __str__(self):
        return f"{self.student} → {self.class_offered} ({self.session})"


# ──────────────────────────────────────────────────────────────────────
# Letter template — the constant body of an admission letter, per school.
# Editing this once updates every letter that doesn't override the field.
# ──────────────────────────────────────────────────────────────────────

DEFAULT_INTRO_TEMPLATE = (
    "The Management of {letterhead} is pleased to inform you "
    "that your child/ward <b>{student_name}</b>, having passed our entrance "
    "examination is hereby offered a conditional admission into "
    "<b>{class_label}</b> for the {session_name} academic session."
)

DEFAULT_DEPOSIT_TEMPLATE = (
    "Paying a deposit of {deposit_words} ({deposit_display}) into the school "
    "account at {bank_branch_hint} {bank_name}., {bank_account_name} "
    "(A/C No: {bank_account}) before <b>{payment_deadline}</b>. Returning the "
    "teller showing evidence of payment to the accounts section for issuance "
    "of receipt and other required document. The deposit forms part of the "
    "school fees. You will also be given breakdown of the balance and other "
    "joining instructions. The balance of the fees is expected to be paid "
    "before the child resume for the session on <b>{resume_date}</b>."
)

DEFAULT_NOTES_TEMPLATE = (
    "School fees should always be paid in advance. You are encouraged to pay "
    "for the whole year if you are willing and able to do so.\n"
    "The return of the attached slip plus evidence of payment will reserve a "
    "place for your child. Complete and submit the enclosed acceptance form "
    "to the Admin office. (You may also scan the acceptance form, bank teller "
    "and email them to {acceptance_email_1} or {acceptance_email_2}.) Failure "
    "to do so on or before <b>{acceptance_deadline}</b> will imply that you "
    "do not wish to accept this offer and your child's/ward's space will be "
    "offered to other applicants.\n"
    "In the event of a change of mind two weeks after acceptance and payment "
    "of school fees, parent forfeits 50% of the fees paid.\n"
    "There is no refund of any fees if a student is expelled from the School, "
    "except for caution fee.\n"
    "The School Account Unit will need at least two weeks to process the refund."
)

DEFAULT_CLOSING_LINE  = "ACCEPT OUR CONGRATULATIONS."
DEFAULT_SIGNATURE_TITLE = "Principal"


class LetterTemplate(models.Model):
    """One row per school. Holds the constant body of the letter.

    Placeholders available in intro_template:
      {student_name} {class_label} {session_name} {letterhead}

    Placeholders in deposit_paragraph_template:
      {deposit_words} {deposit_display} {bank_name} {bank_branch_hint}
      {bank_account} {bank_account_name} {payment_deadline} {resume_date}

    Placeholders in notes_template (one note per line):
      {payment_deadline} {acceptance_deadline} {acceptance_email_1}
      {acceptance_email_2} {resume_date}
    """
    school = models.OneToOneField(
        'quiz.School', on_delete=models.CASCADE,
        related_name='letter_template',
        help_text="Which school's letterhead this template applies to.")

    intro_template = models.TextField(
        blank=True, default='',
        help_text="Intro paragraph. Blank = use the built-in default.")
    deposit_paragraph_template = models.TextField(
        blank=True, default='',
        help_text="Deposit paragraph. Blank = use the built-in default.")
    notes_template = models.TextField(
        blank=True, default='',
        help_text="One note per line — becomes the numbered list. "
                  "Blank = use the built-in default.")
    extra_paragraph = models.TextField(
        blank=True, default='',
        help_text="Optional paragraph printed above 'Please note:'. "
                  "Blank = none.")
    closing_line = models.CharField(
        max_length=200, blank=True, default='',
        help_text=f"e.g. '{DEFAULT_CLOSING_LINE}'. Blank = use the default.")
    signature_title = models.CharField(
        max_length=100, blank=True, default='',
        help_text=f"e.g. '{DEFAULT_SIGNATURE_TITLE}'. Blank = use the default.")
        # ── Letterhead / school name used in the body ─────────────────────
    letterhead_school_line = models.CharField(
        max_length=255, blank=True, default='',
        help_text="e.g. 'Esteem Learning Center, The Boys\\' College'. "
                  "Blank = use config default.")

    # ── Deposit / bank details ────────────────────────────────────────
    deposit_amount_words = models.CharField(
        max_length=200, blank=True, default='',
        help_text="e.g. 'Seven Hundred Fifty Thousand Naira only'. Blank = config default.")
    deposit_amount_display = models.CharField(
        max_length=50, blank=True, default='',
        help_text="e.g. 'N750,000'. Blank = config default.")
    bank_name = models.CharField(max_length=100, blank=True, default='')
    bank_branch_hint = models.CharField(max_length=100, blank=True, default='')
    bank_account = models.CharField(max_length=50, blank=True, default='')
    bank_account_name = models.CharField(max_length=200, blank=True, default='')

    # ── Acceptance emails ─────────────────────────────────────────────
    acceptance_email_1 = models.EmailField(blank=True, default='')
    acceptance_email_2 = models.EmailField(blank=True, default='')

    # ── Date windows ──────────────────────────────────────────────────
    payment_window_days = models.PositiveIntegerField(
        default=15, help_text="Days from letter date to payment deadline.")
    acceptance_window_days = models.PositiveIntegerField(
        default=15, help_text="Days from payment deadline to acceptance deadline.")
    pass_thresholds = models.JSONField(default=dict, blank=True)
    session_name = models.CharField(max_length=20, default='2025-2026')
    exam_school = models.ForeignKey(
        'quiz.School', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+',
        help_text="School the entrance exams are attached to. Leave blank to use this school.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Letter Template"
        verbose_name_plural = "Letter Templates"

    def __str__(self):
        return f"Letter template — {self.school.school_name}"

    # Accessors that fall back to the built-in defaults
    def get_intro(self):       return self.intro_template or DEFAULT_INTRO_TEMPLATE
    def get_deposit(self):     return self.deposit_paragraph_template or DEFAULT_DEPOSIT_TEMPLATE
    def get_notes(self):       return self.notes_template or DEFAULT_NOTES_TEMPLATE
    def get_extra(self):       return self.extra_paragraph or ''
    def get_closing(self):     return self.closing_line or DEFAULT_CLOSING_LINE
    def get_signature_title(self): return self.signature_title or DEFAULT_SIGNATURE_TITLE
     
    def get_letterhead_school_line(self):
        from .services.admission_letter_config import LETTERHEAD_SCHOOL_LINE
        return self.letterhead_school_line or LETTERHEAD_SCHOOL_LINE
    def get_deposit_words(self):
        from .services.admission_letter_config import DEPOSIT_AMOUNT_WORDS
        return self.deposit_amount_words or DEPOSIT_AMOUNT_WORDS
    def get_deposit_display(self):
        from .services.admission_letter_config import DEPOSIT_AMOUNT_DISPLAY
        return self.deposit_amount_display or DEPOSIT_AMOUNT_DISPLAY
    def get_bank_name(self):
        from .services.admission_letter_config import BANK_NAME
        return self.bank_name or BANK_NAME
    def get_bank_branch_hint(self):
        from .services.admission_letter_config import BANK_BRANCH_HINT
        return self.bank_branch_hint or BANK_BRANCH_HINT
    def get_bank_account(self):
        from .services.admission_letter_config import BANK_ACCOUNT
        return self.bank_account or BANK_ACCOUNT
    def get_bank_account_name(self):
        from .services.admission_letter_config import BANK_ACCOUNT_NAME
        return self.bank_account_name or BANK_ACCOUNT_NAME
    def get_acceptance_email_1(self):
        from .services.admission_letter_config import ACCEPTANCE_EMAIL_1
        return self.acceptance_email_1 or ACCEPTANCE_EMAIL_1
    def get_acceptance_email_2(self):
        from .services.admission_letter_config import ACCEPTANCE_EMAIL_2
        return self.acceptance_email_2 or ACCEPTANCE_EMAIL_2
            