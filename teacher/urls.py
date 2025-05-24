from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

app_name = 'teacher'

urlpatterns = [

    path('control/<str:result_class>/<str:subject>/<str:session_name>/<str:term_name>/', views.control_view, name='control'),
    path('control-list/', views.control_list_view, name='control-list'),
    path('teachers/edit/<int:pk>/', views.teacher_edit_view, name='teacher_edit'),  # Edit URL
    path('teachers/delete/<int:pk>/', views.teacher_delete_view, name='teacher_delete'), 
    path('teachers/', views.teacher_list_view, name='teacher_list'),
    path('create-course/', views.add_course_view, name='create_course_view'),
    path('exam/delete/<int:course_id>/', views.delete_examiner_exam, name='delete_examiner_exam'),
    path('exam/create/', views.create_examiner_exam, name='create_examiner_exam'),
    path('exam/edit/<int:result_id>/', views.edit_result_view, name='edit_result_view'),
    path('exam/delete/<int:result_id>/', views.delete_result_view, name='delete_result_view'),
    path('exam-list', views.exam_list_view, name='exam_list'),
    path('exam/statistics/<int:course_id>/', views.exam_statistics_view, name='exam_statistics'),
    path('course/edit/<int:course_id>/', views.edit_examiner_exam, name='edit_examiner_exam'),
    path('manage-exam/', views.examiner_start_exam, name='manage_exam'),
    path('examiner-dashboard/', views.examiner_dashboard_view, name='examiner_dashboard'),
    path('coursegrade/edit/<int:pk>/', views.edit_coursegrade_view, name='edit_coursegrade'),
    path('coursegrade/delete/<int:pk>/', views.delete_coursegrade_view, name='delete_coursegrade'),
    path('download-csv/', views.download_csv, name='download_csv'),
    
    path('update-teacher-settings/', views.update_teacher_settings, name='update_teacher_settings'),
    
    path('generate-csv/', views.generate_csv, name='generate_csv'),
    path('teacher-signup/', views.teacher_signup_view, name='teacher_signup'),
    path('teacher_login/', views.teacher_login_view, name='teacher_login'),
    path('teacher_logout/', views.teacher_logout_view, name='teacher_logout'),
    path('student-logout/', views.student_logout_view, name='student-logout'),\
    # path('login-section/', views.login_section_view, name='login_section-view'),
    path('teacher-dashboard', views.teacher_dashboard_view,name='teacher-dashboard'),
    path('subject/edit/<int:course_id>/', views.edit_subjects_view, name='edit_subjects_view'),
    path('subject/delete/<int:course_id>/', views.delete_subject_view, name='delete_subject_view'),


    path('student-dashboard', views.student_dashboard_view,name='student-dashboard'),
    path('add-question/', views.add_question_view, name='add_question'),
    # Add more URLs as needed
    
    # path('teacherlogin', LoginView.as_view(template_name='teacher/teacherlogin.html'),name='teacherlogin'),
    # path('import-word/', views.import_word, name='import-word'),
    # path('questions/', views.view_questions, name='view_questions'),
    # path('questions/subject/<int:subject_id>/', views.subject_questions, name='subject_questions'),
    path('teacher/subjects/', views.teacher_subjects_view, name='teacher_subjects'),
    path('teacher/subject/<int:subject_id>/questions/', views.subject_questions_view, name='subject_questions'),
    path('import/', views.import_data, name='import_data'),
    path('export/', views.export_data, name='export_data'),
    path('view-questions/', views.view_questions, name='view_questions'),
    path('edit/<int:question_id>/', views.edit_question, name='edit_question'),
    path('delete-question/<int:question_id>/', views.delete_question_view, name='delete_question'),
    path('teacher-results/', views.teacher_results_view, name='teacher_results'),
    path('teacher/results/edit/<int:result_id>/',  views.edit_teacher_results_view, name='edit_teacher_results'),
    path('teacher/results/delete/<int:result_id>/', views.delete_teacher_result_view, name='delete_teacher_result'),
    path('export-results-csv/', views.export_results_csv, name='export_results_csv'),
    path('import-results/', views.import_results, name='import-results'),
    path('results/<str:result_class>/<str:subject>/<str:session>/<str:term>/', views.result_column_view, name='result_column_view'),
    
    path('save-results/', views.save_results, name='save-results'),
    path('class-list/', views.class_list_view, name='class-list'),
]  
