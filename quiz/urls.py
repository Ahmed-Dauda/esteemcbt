from django.urls import path

from . import views


        
app_name = 'quiz'

urlpatterns = [
    # path('students/', views.students_list, name='students_list'),
    # path('create_group/', views.create_group, name='create_group'),
    #  path('promote/<from_grade>/<to_grade>/', views.promote_students, name='promote_students'),
    # path('move_group/<str:from_group_name>/<str:to_group_name>/', views.move_group, name='move_group'),
    path('move_group/', views.move_group, name='move_group'),
    # path('add_student/', views.add_student, name='add_student'),
    # path('add_student_success/', views.add_student_success, name='add_student_success'),
    # path('promote/', views.promote_students, name='promote_students'),
    path('success/', views.success_page, name='success_page'),
    path('take-exam', views.take_exams_view,name='take-exam'),
    path('start-exam/<pk>/', views.start_exams_view,name='start-exam'),
    path('calculate_marks', views.calculate_marks_view,name='calculate_marks'),
    path('view_result', views.view_result_view,name='view_result'),
    # path('register-student/', views.register_student, name='register_student'),
    # path('school-dashboard/<pk>/', views.school_dashboard, name='school_dashboard'),
   
]




