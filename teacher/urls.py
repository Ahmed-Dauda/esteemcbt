from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

app_name = 'teacher'

urlpatterns = [

    path('teacher-signup/', views.teacher_signup_view, name='teacher_signup'),
    path('teacher_login/', views.teacher_login_view, name='teacher_login'),
    path('teacher_logout/', views.teacher_logout_view, name='teacher_logout'),\
    # path('login-section/', views.login_section_view, name='login_section-view'),
    path('teacher-dashboard', views.teacher_dashboard_view,name='teacher-dashboard'),
    path('student-dashboard', views.student_dashboard_view,name='student-dashboard'),
    path('add-question/', views.add_question_view, name='add_question'),
    # Add more URLs as needed
    # path('teacherlogin', LoginView.as_view(template_name='teacher/teacherlogin.html'),name='teacherlogin'),
    path('import/', views.import_data, name='import_data'),
    path('export/', views.export_data, name='export_data'),
    path('view-questions/', views.view_questions, name='view_questions'),
    path('edit/<int:question_id>/', views.edit_question, name='edit_question'),
    path('delete-question/<int:question_id>/', views.delete_question_view, name='delete_question'),
    path('teacher-results/', views.teacher_results_view, name='teacher_results'),
    path('export-results-csv/', views.export_results_csv, name='export_results_csv'),
]
