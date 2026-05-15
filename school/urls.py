from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [  
    path('admin/', admin.site.urls),
    path('', include('sms.urls')),
    path('student/', include('student.urls')),
    path('quiz/', include('quiz.urls')),
    path('teacher/', include('teacher.urls')),
    path('users/', include('users.urls')),
    path('finance/', include('finance.urls')),  
    path('portal/', include('portal.urls')),
    path('accounts/', include('allauth.urls')),
    path('academics/', include('academics.urls')),
    path("research/", include("research.urls")),
    path('reminders/', include('reminders.urls')),
    path('farmer/', include('core.urls')),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)