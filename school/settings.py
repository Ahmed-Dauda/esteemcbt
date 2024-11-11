
from pathlib import Path
from django.conf import settings
from django.contrib.auth import SESSION_KEY

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-f1btf-a@a!84mjii=$tgdel4$+w5gtmbw3o%7$8n4w+2rntpns'

# Read SECRET_KEY from an environment variable

import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'cg#p$g+j9tax!#a3cup@1$8obt2_+&k3q+pmu)5%asj6yjpkag')



# SECURITY WARNING: don't run with debug turned on in production!
# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = os.environ.get('DJANGO_DEBUG', '') != 'False'


ALLOWED_HOSTS = ['*']
# ALLOWED_HOSTS = ['codethinkers.herokuapp.com','codethinkerslms.com','www.codethinkerslms.com','codethinkers.org','www.codethinkers.org', '127.0.0.1']
# ALLOWED_HOSTS = ['ctsaalms.herokuapp.com','codethinkers.org' ,'127.0.0.1']

# wyswyg = ['grappelli', 'filebrowser']
INSTALLED_APPS = [
  
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # make sure sites is included
    'users',
    'sms',
    'student',
    'quiz',
    'teacher',
    'sweetify',
    'widget_tweaks',
    'hitcount',
    'crispy_forms',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'cloudinary',
    
    'embed_video',
    'xhtml2pdf',
    'tinymce',
    'django_social_share',
    'import_export',
    'django_mathjax',
    "debug_toolbar",
    
    
    
    
# the social providers
    # 'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.twitter',
]

MATHJAX_ENABLED=True

BASE_URL = 'https://codethinkers.org'

AUTH_USER_MODEL = 'users.NewUser'
# Application definition
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # existing backend
    'allauth.account.auth_backends.AuthenticationBackend',
)

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

SOCIAL_AUTH_GOOGLE_KEY = '571775719816-thu9u968v8gpmcuie9ojlb4u0ahig94t.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_SECRET = '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'

# settings.py

# Specify BigAutoField as the default auto field for all models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SOCIAL_AUTH_FACEBOOK_KEY = '416474800140748'
# SOCIAL_AUTH_FACEBOOK_SECRET = '4763331e29fc3703c82ba85f645fe5af'

# django import and export setting
IMPORT_EXPORT_CHUNK_SIZE = 1000 # speed import and export
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = True # you must have permission b4 export
IMPORT_EXPORT_IMPORT_PERMISSION_CODE = True # you must have permission b4 import
IMPORT_EXPORT_IMPORT_PERMISSION_CODE
IMPORT_EXPORT_SKIP_ADMIN_LOG = True # speed import and export
IMPORT_EXPORT_USE_TRANSACTIONS = True  # import won’t import only part of the data set.

# allauth settings

SITE_ID = 2

# SOCIALACCOUNT_EMAIL_VERIFIATION = False
# ACCOUNT_AUTHENTICATION_METHOD ='username_email'
# ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
# ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# ACCOUNT_USER_MODEL_USERNAME_FIELD = 'user_name'
# ACCOUNT_SESSION_REMEMBER = True

# ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_LOGIN_ON_PASSWORD_RESET = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_FORMS = {'signup': 'users.forms.SimpleSignupForm'}



SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        }
    }
}

# unused url
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': SOCIAL_AUTH_GOOGLE_KEY ,
            'secret': SOCIAL_AUTH_GOOGLE_SECRET,
            'key': ''
        }
    }
}

# cloudinary settings
# cloud_name = 'ds5l3gqr6'
# api_key = '671667183251344'
# api_secret = 'P5WKA1qweMmd1i4TkU2W_ZY9ZuA'
# secure = True
CLOUDINARY_URL = 'CLOUDINARY_URL=cloudinary://671667183251344:P5WKA1qweMmd1i4TkU2W_ZY9ZuA@ds5l3gqr6'

# Configure Cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure Cloudinary
cloudinary.config(
    cloud_name='dcomiviua',
    api_key='365524854341134',
    api_secret='_a3awGtK3hznGaSpvLff2RFTt_I',
    secure = True
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# import cloudinary

# cloudinary.config( 
#   cloud_name = "ds5l3gqr6", 
#   api_key ="671667183251344", 
#   api_secret = "P5WKA1qweMmd1i4TkU2W_ZY9ZuA",
#   secure = True
# )
# email settings

# EMAIL_BACKED = 'django.core.mail.backends.smtp.EmailBackend'

# the below email backed is for testing with local server
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# code to unblock zoho account
# https://mail.zoho.com/UnblockMe

EMAIL_BACKED = 'django_smtp_ssl.SSLEmailBackend'
EMAIL_HOST = 'smtppro.zoho.eu'
# EMAIL_HOST = 'smtppro.zoho.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False 
EMAIL_HOST_USER = 'techsupport@esteemlearningcentre.com'
# EMAIL_HOST_PASSWORD = '0806563624937811Bm.'
EMAIL_HOST_PASSWORD = 'techSupport@01'
DEFAULT_FROM_EMAIL = 'techsupport@esteemlearningcentre.com'

# if DEBUG:
#     EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
# else:
#     EMAIL_BACKED = 'django.core.mail.backends.smtp.EmailBackend'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',

  
    'django.middleware.clickjacking.XFrameOptionsMiddleware',


]
CSRF_COOKIE_SECURE=False

ROOT_URLCONF = 'school.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Add any template directories here
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Add any template directories here
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
                
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
                
#             ],
#         },
#     },
# ]

WSGI_APPLICATION = 'school.wsgi.application'



# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
PROJECT_PATH =os.path.dirname(os.path.abspath(__file__))

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(PROJECT_PATH, 'school.sqlite3'),
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Lagos'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# ADDITIONAL SITE SECURITies

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIDERECT = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIES_SECURE = True
SECURE_FRAME_DENY = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIES_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# end of security

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
LOGIN_REDIRECT_URL = 'teacher:student-dashboard'
LOGIN_URL = 'account_login'
LOGOUT_REDIRECT_URL = 'account_login'
ACCOUNT_SIGNUP_REDIRECT_URL= 'account_login'
ACCOUNT_SIGNUP_REDIRECT_URL= 'settings.LOGOUT_URL'
# django hit count 
HITCOUNT_KEEP_HIT_ACTIVE = {'seconds': 2}

HITCOUNT_HITS_PER_IP_LIMIT = 0

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

STATIC_URL = '/static/'
MEDIA_URL = '/media/'


STATIC_ROOT =os.path.join(BASE_DIR, 'static')
MEDIA_ROOT =os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Heroku: Update database configuration from $DATABASE_URL.



import dj_database_url
# Update database configuration from $DATABASE_URL.

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)


# STATIC_ROOT = BASE_DIR / 'staticfiles'
# STATIC_URL = '/static/'

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# for TinyMCE 
# settings.py

# settings.py

TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'width': 700,
    'entity_encoding': "raw",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'plugins': 'link image preview codesample contextmenu table code mathjax',
    'toolbar': 'undo redo | styleselect | bold italic | link image | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | table | codesample | mathjax',
    'theme': 'silver',

    # Additional configuration for MathML
    'extended_valid_elements': 'math[*],mrow[*],mfrac[*],mi[*],mn[*],mo[*]',
    'custom_elements': 'math,mrow,mfrac,mi,mn,mo',
    'content_style': "math, mrow, mfrac, mi, mn, mo",
    'mathjax': {
        'lib': 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-AMS_HTML',
        'symbols': {'mathml': True}
    },
    'init_instance_callback': '''
        function (editor) {
            console.log('Editor is initialized.');

            // Add event listener for MathML elements
            editor.on('click', function(e) {
                if (e.target.nodeName === 'MATH' || e.target.closest('math')) {
                    editor.focus();
                }
            });
        }
    ''',

    # Prevent wrapping text in <p> tags
    'forced_root_block': ' ',  # Use <div> instead of <p>
    'forced_root_block_attrs': {},  # Clears any forced attributes
    'br_in_pre': True,  # Insert <br> tags instead of wrapping in <p> tags

    # Allow all elements and attributes
    'valid_elements': '*[*]',  # Allow all elements
    'valid_children': '+body[style|link|script|iframe|section],+section[div|p],+div[math|mrow|mfrac|mi|mn|mo]',
}


# TINYMCE_DEFAULT_CONFIG = {
#     'height': 360,
#     'width': 700,
#     'cleanup_on_startup': True,
#     'custom_undo_redo_levels': 20,
#     'selector': 'textarea',
#     'plugins': 'link image preview codesample contextmenu table code',
#     'toolbar': 'undo redo | styleselect | bold italic | link image | codesample | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | table | code | math',
#     'theme': 'silver',
# }

# TINYMCE_JS_URL = 'https://cdn.tiny.cloud/1/r5ebxl5femg5gy8yvid6alg59ohekm45qlmxptc20qeu5jgw/tinymce/5/tinymce.min.js'

# r5ebxl5femg5gy8yvid6alg59ohekm45qlmxptc20qeu5jgw

TINYMCE_JS_URL = 'https://cdn.tiny.cloud/1/r5ebxl5femg5gy8yvid6alg59ohekm45qlmxptc20qeu5jgw/tinymce/6/tinymce.min.js'
TINYMCE_COMPRESSOR = False

# PAYSTACK_SECRET_KEY = os.environ.get('sk_test_75e53acfea9e04b0c52c3c3c6c46281c844a706a')
# PAYSTACK_PUBLIC_KEY = os.environ.get('pk_test_72337ad2f9419ff6eb3204519bb884067c075ed8')

# test api
PAYSTACK_SECRET_KEY = 'sk_test_75e53acfea9e04b0c52c3c3c6c46281c844a706a'
PAYSTACK_PUBLIC_KEY = 'pk_test_72337ad2f9419ff6eb3204519bb884067c075ed8'

# live api
# PAYSTACK_SECRET_KEY = 'sk_live_ecb915cd648ffcea0578361a08ac369122f02754'
# PAYSTACK_PUBLIC_KEY = 'pk_live_010265c77983e11a700678d34d476b1ce1c48fb1'


# problem of hosting to heroku and solution
# error: failed to push some refs to 'https://git.heroku.com/codethinkers.git'
# git checkout -b master
# git add .
# git commit -m "your commit message"
# git push -u origin master
# git push heroku master

# # solution to django.db.utils.OperationalError: no such table: auth_user
# python manage.py migrate --run-syncdb

# if you have problem withe migrations not applied
# python manage.py showmigrations quiz
# python manage.py migrate quiz 0008_alter_group_subjects --fake

# problem: ValueError: Dependency on app with no migrations: users
# solution

# 1. python manage.py makemigrations users
# 2.  python manage.py migrate users
# 3.  python manage.py createsuperuser

# using ngov to test webhooks

# change the webhook to a test mode in paystack
# login to the ngrov website and copy and paste ngrok config add-authtoken 2SL4rhAyqYBNfeHZvWsCan18Pcz_71B7staheJejM8eL6husJ
# ngrok http 8000 --host-header=rewrite


# migration folder issues

# if table is referencing deleted column, just remove the table from migration folder

# if makemigration is not recognized, do installation of libraries

#ALTER TABLE public.quiz_course DROP COLUMN course_name;
#ALTER TABLE public.quiz_course ADD COLUMN course_name VARCHAR(50) UNIQUE;


# step 1

# begin;
# set transaction read write;
# ALTER TABLE public.quiz_course
# ADD COLUMN course_name VARCHAR(500);
# COMMIT;  

# step 2

# begin;
# set transaction read write;
# ALTER TABLE "public"."quiz_course"
# ALTER COLUMN "course_name" TYPE bigint USING "course_name"::bigint;
# COMMIT;  

# step 3

# inserting relationships

# begin;
# set transaction read write;
# ALTER TABLE "public"."quiz_course"
# ADD CONSTRAINT "quiz_course_course_name_fkey" FOREIGN KEY ("course_name") REFERENCES "public"."sms_courses" ("id");
# COMMIT;  


# step 4
# begin;
# set transaction read write;
# ALTER TABLE "public"."teacher_teacher_subjects_taught" RENAME COLUMN course_id TO courses_id;
# COMMIT; 


# step 5
# python manage.py migrate #in the heroku shell

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]