from email.policy import default
from django.contrib.auth.models import AbstractBaseUser, AbstractUser,    BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.urls import reverse
import uuid
import random
import string
from cloudinary.models import CloudinaryField

from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save


# from quiz.models import School

# from quiz.models import School
# from django.contrib.auth import get_user_model
# User = get_user_model()

# from sms.models import Topics  # Update this import



class CustomUserManager(BaseUserManager):

  def create_user(self, email, password, is_staff, is_superuser, **extra_fields):
    if not email:
        raise ValueError('Users must have an email address')
    now = timezone.now()
    email = self.normalize_email(email)
    user = self.model(
        email=email,
        is_staff=is_staff, 
        is_active=True,
        is_superuser=is_superuser, 
        last_login=now,
        date_joined=now, 
        **extra_fields
    )
    user.set_password(password)
    user.save(using=self._db)
    return user
  
  class Meta:
        db_table = 'auth_user'
          
      
  def create_superuser(self, email, password, **extra_fields):
    user=self.create_user(email, password, True, True, **extra_fields)
    user.save(using=self._db)
    return user


gender_choice = [
  ('Male', 'Male'),
  ('Female', 'Female')
]


class NewUser(AbstractBaseUser, PermissionsMixin):
    email           = models.EmailField(max_length=254, unique=True, db_index=True)
    username        = models.CharField(max_length=35, blank=True, db_index=True)
    school          = models.ForeignKey(
                        'quiz.School', 
                        on_delete=models.SET_NULL, 
                        blank=True, 
                        null=True, 
                        db_index=True
                     )
    student_class   = models.CharField(max_length=254, null=True, blank=True, db_index=True)
    phone_number    = models.CharField(max_length=254, blank=True)
    first_name      = models.CharField(max_length=254, null=True, blank=True, db_index=True)
    last_name       = models.CharField(max_length=254, null=True, blank=True, db_index=True)
    admission_no    = models.CharField(max_length=254, null=True, blank=True, db_index=True)
    countries       = models.CharField(max_length=254, blank=True, null=True)
    pro_img         = CloudinaryField(
                        'profile_photos', 
                        blank=True, 
                        null=True, 
                        default='https://i.ibb.co/cx34WCc/logo.png'
                     )
    gender          = models.CharField(choices=gender_choice, max_length=225, blank=True, null=True)
    is_staff        = models.BooleanField(default=False)
    is_superuser    = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=True)
    is_principal    = models.BooleanField(default=False)
    last_login      = models.DateTimeField(null=True, blank=True)
    date_joined     = models.DateTimeField(auto_now_add=True, db_index=True)

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = []

    objects         = CustomUserManager()

    def __str__(self):
        return f'({self.school}) - ({self.first_name}, {self.last_name}, {self.student_class})'

    class Meta:
        db_table = 'auth_user'
        indexes = [
            models.Index(fields=['school', 'student_class']),          # fast filtering by school + class
            models.Index(fields=['school', 'student_class', 'username']),  # for unique lookups per class
            models.Index(fields=['email', 'username']),               # login lookups
            models.Index(fields=['first_name', 'last_name']),         # search by name
        ]


class Profile(models.Model):

    PAYMENT_CHOICES = [('Premium', 'PREMIUM'), ('Free', 'FREE'), ('Sponsored', 'SPONSORED')]
    gender_choice = [('Male', 'MALE'), ('Female', 'FEMALE')]

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, unique=True, related_name='profile', blank=True, null=True, db_index=True)
    username = models.CharField(max_length=225, blank=True, null=True, db_index=True)
    schools = models.ForeignKey('quiz.School', related_name='profile_school', on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    student_course = models.ForeignKey('sms.Courses', on_delete=models.SET_NULL, related_name='students', null=True, db_index=True)
    first_name = models.CharField(max_length=225, blank=True, null=True, db_index=True)
    last_name = models.CharField(max_length=225, blank=True, null=True, db_index=True)
    student_class = models.CharField(max_length=254, null=True, blank=True, db_index=True)
    status_type = models.CharField(choices=PAYMENT_CHOICES, default='Free', max_length=225, db_index=True)
    gender = models.CharField(choices=gender_choice, max_length=225, blank=True, null=True)
    admission_no = models.CharField(max_length=254, null=True, blank=True, db_index=True)
    phone_number = models.CharField(max_length=225, blank=True, null=True, db_index=True)
    countries = models.CharField(max_length=225, blank=True, null=True, db_index=True)
    pro_img = models.CharField(max_length=225, blank=True, null=True)
    bio = models.TextField(max_length=600, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ['first_name','last_name'] 

    def get_absolute_url(self):
        return reverse('sms:userprofileupdateform', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f'{self.first_name or "No First Name"} {self.last_name or "No Last Name"}'.strip()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def userprofile_receiver(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure the profile is updated with the user fields
        profile = instance.profile
        profile.username = instance.username
        profile.first_name = instance.first_name
        profile.last_name = instance.last_name
        profile.student_class = instance.student_class
        profile.admission_no = instance.admission_no  
        profile.schools = instance.school
        profile.phone_number = instance.phone_number
        profile.countries = instance.countries
        
        profile.save()

post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)

# class Profile(models.Model):
    
#     PAYMENT_CHOICES = [
#     ('Premium','PREMIUM'),
#     ('Free', 'FREE'),
#     ('Sponsored', 'SPONSORED'),
  
#     ]

#     user = models.OneToOneField(NewUser, on_delete=models.CASCADE, unique=True, related_name='profile')
#     # school = models.ForeignKey('quiz.School', on_delete=models.SET_NULL, blank=True, null=True)
#     username = models.CharField(max_length=225, blank=True)
#     # referral_code = models.CharField(max_length=225, blank=True, null=True)
#     completed_topics = models.ManyToManyField('sms.Topics', blank=True)
#     student_course = models.ForeignKey('sms.Courses', on_delete=models.SET_NULL, related_name='students', null=True)
#     # courses =models.ForeignKey(Courses,blank=False ,default=1, on_delete=models.SET_NULL, related_name='coursesoooo', null= True)
#     first_name = models.CharField(max_length=225, blank=True, null=True)
#     last_name = models.CharField(max_length=225, blank=True, null=True)
#     status_type = models.CharField (choices = PAYMENT_CHOICES, default='Free' ,max_length=225)
#     gender = models.CharField(choices=gender_choice, max_length=225, blank=True, null=True)
#     phone_number = models.CharField(max_length=225, blank=True, null=True)
#     countries = models.CharField(max_length=225, blank=True, null=True)
#     pro_img = models.ImageField(upload_to='profile', blank=True, null=True)
#     bio = models.TextField(max_length=600, blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     updated = models.DateTimeField(auto_now=True, blank=True, null=True)

#     def get_absolute_url(self):
#         return reverse('sms:userprofileupdateform', kwargs={'pk': self.pk})
#     def __str__(self):
#       return f'{self.first_name} {self.last_name}'

# @receiver(post_save, sender=get_user_model())
# def userprofile_receiver(sender, instance, created, *args, **kwargs):
#     if created:
#         Profile.objects.create(
#             user=instance,
#             username=instance.username,
#             first_name=instance.first_name,
#             last_name=instance.last_name,
#             countries=instance.countries,
#             # referral_code=instance.referral_code,
#             # school=instance.school,
#         )

# post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)


# def userprofile_receiver(sender, instance, created, *args, **kwargs):
#     if created:
#         profile = Profile.objects.create(user=instance, 
#                                          username=instance.username, 
#                                          first_name =instance.first_name, 
#                                          last_name =instance.last_name,
#                                          countries =instance.countries,
#                                          referral_code =instance.referral_code
#                                          )