# from email.policy import default
# from django.contrib.auth.models import AbstractBaseUser, AbstractUser,    BaseUserManager, PermissionsMixin
# from django.db import models
# from django.utils import timezone
# from django.conf import settings
# # from django.contrib.auth import get_user_model
# # User = get_user_model()

# from sms.models import Courses

# from django.db.models.signals import post_save, pre_save


# class CustomUserManager(BaseUserManager):

#   def create_user(self, email, password, is_staff, is_superuser, **extra_fields):
#     if not email:
#         raise ValueError('Users must have an email address')
#     now = timezone.now()
#     email = self.normalize_email(email)
#     user = self.model(
#         email=email,
#         is_staff=is_staff, 
#         is_active=True,
#         is_superuser=is_superuser, 
#         last_login=now,
#         date_joined=now, 
#         **extra_fields
#     )
#     user.set_password(password)
#     user.save(using=self._db)
#     return user
  
#   class Meta:
#         db_table = 'auth_user'
      
#   # def create_user(self, email, password, **extra_fields):
#   #   return self._create_user(email, password, False, False, **extra_fields)

#   def create_superuser(self, email, password, **extra_fields):
#     user=self.create_user(email, password, True, True, **extra_fields)
#     user.save(using=self._db)
#     return user


# class NewUser(AbstractBaseUser, PermissionsMixin):

#     email = models.EmailField(max_length=254, unique=True)
#     username = models.CharField(max_length=35,  blank=True)
#     phone_number = models.CharField(max_length=254, blank= True)
#     first_name = models.CharField(max_length=254, null=True, blank=True)
#     last_name = models.CharField(max_length=254, null=True, blank=True)
#     countries = models.CharField(max_length=254,  blank=True, null=True)
#     is_staff = models.BooleanField(default=False)
#     is_superuser = models.BooleanField(default=False)
#     is_active = models.BooleanField(default=True)
#     last_login = models.DateTimeField(null=True, blank=True)
#     date_joined = models.DateTimeField(auto_now_add=True)
    

#     USERNAME_FIELD = 'email'
#     # USERNAME_FIELD = 'username'
#     EMAIL_FIELD = 'username'
#     REQUIRED_FIELDS = []

#     objects = CustomUserManager()

#     def __str__(self):
#         return f'{self.email}'

 
#     class Meta:
#       db_table = 'auth_user'
     

# gender_choice = [
#   ('Male', 'Male'),
#   ('Female', 'Female')
# ]


# from django.db import models
# from django.conf import settings
# from django.db.models.signals import post_save
# from django.urls import reverse
# import uuid
# import random
# import string




# class Profile(models.Model):
    
#     PAYMENT_CHOICES = [
#     ('Premium','PREMIUM'),
#     ('Free', 'FREE'),
#     ('Sponsored', 'SPONSORED'),
  
#     ]

#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True, related_name='profile')
#     username = models.CharField(max_length=225, blank=True)
#     # referral_code = models.CharField(max_length=224, blank=True)
#     courses =models.ForeignKey(Courses,blank=False ,default=1, on_delete=models.SET_NULL, related_name='coursesoooo', null= True)
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
#         return f'{self.first_name} {self.last_name} profile'


# def userprofile_receiver(sender, instance, created, *args, **kwargs):
#     if created:
#         profile = Profile.objects.create(user=instance, 
#                                          username=instance.username, 
#                                          first_name =instance.first_name, 
#                                          last_name =instance.last_name,
#                                          countries =instance.countries,
#                                         #  referral_code =instance.referral_code
#                                          )

# post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)

