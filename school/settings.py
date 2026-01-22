
from pathlib import Path
from django.conf import settings
from django.contrib.auth import SESSION_KEY

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


# SECURITY WARNING: don't run with debug turned on in production!
# SECURITY WARNING: don't run with debug turned on in production!


# ALLOWED_HOSTS = ['*']
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
    'finance',
    'dal',
    'dal_select2',
    'academics',
    'sweetify',
    'widget_tweaks',
    'hitcount',
    'crispy_forms',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'cloudinary',
    'django_select2',
    'embed_video',
    'xhtml2pdf',
    'tinymce',
    'django_social_share',
    'import_export',
    'django_mathjax',
    'portal',


    'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.twitter',
]

MATHJAX_ENABLED=True

BASE_URL = 'https://codethinkers.org'

AUTH_USER_MODEL = 'users.NewUser'
# Application definition
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',                # normal Django login
    'users.backends.UsernameOnlyBackend',                       # custom passwordless backend
    'allauth.account.auth_backends.AuthenticationBackend',       # allauth backend
]

# AUTHENTICATION_BACKENDS = (
#     'django.contrib.auth.backends.ModelBackend', # existing backend
#     'allauth.account.auth_backends.AuthenticationBackend',
# )

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
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
# ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_FORMS = {'signup': 'users.forms.SimpleSignupForm'}
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'



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

# Configure Cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure Cloudinary
# cloudinary.config(
#     cloud_name='dcomiviua',
#     api_key='365524854341134',
#     api_secret='_a3awGtK3hznGaSpvLff2RFTt_I',
#     secure = True
# )


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
import os

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


# EMAIL_BACKED = 'django_smtp_ssl.SSLEmailBackend'
# EMAIL_HOST = 'smtppro.zoho.eu'
# # EMAIL_HOST = 'smtppro.zoho.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False 

# EMAIL_HOST_USER = 'techsupport@esteemlearningcentre.com'
# # EMAIL_HOST_PASSWORD = '0806563624937811Bm.'
# EMAIL_HOST_PASSWORD = 'techSupport@01'
# DEFAULT_FROM_EMAIL = 'techsupport@esteemlearningcentre.com'



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.gzip.GZipMiddleware', 
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
     # Add at the top

    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',

  
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    

]

import os
from celery.schedules import crontab

# Redis config for Celery
CELERY_BROKER_URL = os.environ.get('REDISCLOUD_URL', 'redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL  # Optional if you want result backend


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }

# LOGGING = {
#     'version': 1,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'DEBUG',
#     },
# }


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


WSGI_APPLICATION = 'school.wsgi.application'



# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
PROJECT_PATH =os.path.dirname(os.path.abspath(__file__))

import os

# settings.py
import dj_database_url


# DATABASES = {
#     'default': dj_database_url.config(
#         conn_max_age=0,  # or even 10
#         ssl_require=False
#     )
# }

# DATABASES['default']['CONN_MAX_AGE'] = 0  # For PgBouncer
import dj_database_url
from pathlib import Path

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=0,      # PgBouncer-safe
        ssl_require=False,   # PgBouncer does not support SSL
    )
}

# ✅ Django-level setting (NOT sent to Postgres)
DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True


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


# ADDITIONAL SITEs SECURITY
# HTTPS and secure headers

# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_SSL_REDIRECT = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'

# # HSTS (HTTP Strict Transport Security)
# SECURE_HSTS_SECONDS = 3600  # You can increase to 31536000 (1 year) in production
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# # Cookies and sessions
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SESSION_COOKIE_HTTPONLY = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# # Optional - block embedding your site in iframe entirely
# SECURE_FRAME_DENY = True  # Already handled by X_FRAME_OPTIONS = 'DENY'

# end of new security


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

# STATIC_URL = '/static/'
# MEDIA_URL = '/media/'

# STATIC_ROOT =os.path.join(BASE_DIR, 'static')
# MEDIA_ROOT =os.path.join(BASE_DIR, 'media')
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# ✅ Where Django will collect static files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ✅ Where you manually put static files like robots.txt, custom JS, etc.
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
# ]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Heroku: Update database configuration from $DATABASE_URL.

import environ
import os

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

DEBUG = env("DEBUG")
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]


SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")



#CLOUDINARY SETTINGS
cloudinary.config(
    cloud_name = env("CLOUDINARY_CLOUD_NAME"),
    api_key    = env("CLOUDINARY_API_KEY"),
    api_secret = env("CLOUDINARY_API_SECRET"),
    secure     = True
)
CLOUDINARY_URL = env('CLOUDINARY_URL')
DEFAULT_FILE_STORAGE = env('DEFAULT_FILE_STORAGE')

# ASGI application
ASGI_APPLICATION = 'school.asgi.application'

# import dj_database_url
# Update database configuration from $DATABASE_URL.

# db_from_env = dj_database_url.config(conn_max_age=500)
# DATABASES['default'].update(db_from_env)


# STATIC_ROOT = BASE_DIR / 'staticfiles'

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

# Now you can use:
import os
from pathlib import Path
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
load_dotenv()

# Now you can use:
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# BASE_DIR = Path(__file__).resolve().parent.parent
# load_dotenv(os.path.join(BASE_DIR, ".env"))
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


import ssl
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

if REDIS_URL.startswith("rediss://"):  # Heroku production
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        "ssl": {"cert_reqs": ssl.CERT_NONE}
    }
    CELERY_REDIS_BACKEND_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_NONE
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


# example 5
# BEGIN;
# SET TRANSACTION READ WRITE;

# CREATE TABLE finance_financerecord (
#     sn SERIAL PRIMARY KEY,
#     names VARCHAR(100) NOT NULL,
#     student_class VARCHAR(100) DEFAULT 'NA',
#     initial_total_deposit DECIMAL(10,1) NOT NULL,
#     total_deposit DECIMAL(10,1) NOT NULL,
#     school_id INTEGER REFERENCES quiz_school(id) ON DELETE SET NULL,
#     session_id INTEGER REFERENCES sms_session(id) ON DELETE SET NULL,
#     term_id INTEGER REFERENCES sms_term(id) ON DELETE SET NULL,
#     school_shop DECIMAL(10,1) DEFAULT 0,
#     caps DECIMAL(10,1) DEFAULT 0,
#     haircut DECIMAL(10,1) DEFAULT 0,
#     others DECIMAL(10,1) DEFAULT 0,
#     total_expense DECIMAL(10,1) DEFAULT 0 NOT NULL,
#     current_balance DECIMAL(10,1) DEFAULT 0 NOT NULL,
#     balance_brought_forward DECIMAL(10,1),
#     note TEXT,
#     status VARCHAR(10) DEFAULT 'remaining' CHECK (status IN ('exhausted', 'remaining')),
#     CONSTRAINT finance_record_balance_check CHECK (current_balance >= 0)
# );


# COMMIT;


# step 5
# python manage.py migrate #in the heroku shell

# MIGRATION ISSUES
# migraion issue? solution:step! = python manage.py showmigrations

# # magration issue on heroku, run this commad:
# delete the miration folder and rerun migration again, push

#allauth socialaccount migrations
#if you have issue allauth socialaccount migrations, apply befor users.NewUser migration, them comment the allauth and apply the migrations before uncommenting again


INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]