"""school URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from debug_toolbar.toolbar import debug_toolbar_urls

# from django.contrib.auth import views as auth_views #import this

# django_project/urls.py



urlpatterns = [  
    # path('api/', WSGIMiddleware(fastapi_app)), 

    path('admin/', admin.site.urls),
    path('', include('sms.urls')),
    path('student/', include('student.urls')),
    path('quiz/', include('quiz.urls')),
    path('teacher/', include('teacher.urls')),
    path('users/', include('users.urls')),
    path('finance/', include('finance.urls')),  
    path('accounts/', include('allauth.urls')),
    path('academics/', include('academics.urls')),
    
    # path('verify', include('student.urls')),
 
] + debug_toolbar_urls()


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

