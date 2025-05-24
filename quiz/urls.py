from django.urls import path
from . import views


       
app_name = 'quiz'

urlpatterns = [
    path('examiner/courses/', views.examiner_course_list, name='examiner_course_list'),
    path('examiner/courses/<int:course_id>/questions/', views.examiner_course_questions, name='examiner_course_questions'),  # <-- Add this line
    # path('examiner/questions/', views.examiner_question_list, name='examiner_question_list'),
    path('examiner/questions/<int:pk>/edit/', views.examiner_question_edit, name='examiner_question_edit'),
    path('examiner/questions/<int:pk>/delete/', views.examiner_question_delete, name='examiner_question_delete'),
    
    path('success/', views.success_page_view, name='success_page'),  # Add this line
    path('move_group/', views.move_group, name='move_group'),
   
]




