from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from debug_toolbar.toolbar import debug_toolbar_urls
from django.http import HttpResponse, JsonResponse

def home(request):
    return HttpResponse("""
        <h1>Welcome to Esteem CBT School System</h1>
        <p>Your Django app is successfully deployed on Hetzner via Coolify!</p>
        <h2>Available Portals:</h2>
        <ul>
            <li><a href='/admin/'>Admin Panel</a></li>
            <li><a href='/student/'>Student Portal</a></li>
            <li><a href='/teacher/'>Teacher Portal</a></li>
            <li><a href='/quiz/'>Quiz Section</a></li>
            <li><a href='/portal/'>Main Portal</a></li>
            <li><a href='/health/'>Health Check</a></li>
        </ul>
        <hr>
        <p><small>Esteem CBT - School Management System</small></p>
    """)

def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [  
    path('', home, name='home'),  # This handles the root URL
    path('admin/', admin.site.urls),
    path('', include('sms.urls')),
    path('health/', health_check, name='health_check'),
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
    path('farmer/', include('core.urls'))
] + debug_toolbar_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)