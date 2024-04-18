from . import views
from django.urls import path
from .views import ReferralSignupView, SchoolStudentView, SchoolSignupView
from .views import become_referrer
        
app_name = 'users'

urlpatterns = [
    path('school-signupp/', SchoolSignupView.as_view(), name='school_signup'),
    path('schoolstudentview/', SchoolStudentView, name='schoolstudentview'),
    path('referral-signup/<str:referrer_code>/', ReferralSignupView.as_view(), name='referral_signup'),
    path('become-referrer/', become_referrer, name='become_referrer'),
 
   
]




