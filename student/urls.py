from django.urls import path
from . import views
# from sms.views import update_referrer_mentor

from django.urls import re_path

app_name = 'student'

urlpatterns = [
    path('exams-conducted-statistics/', views.exams_conducted_statistics_view, name='exams_conducted_statistics'),
    path('download-statistics/', views.download_statistics_view, name='download_statistics'),
    path('badge-list/', views.badge_list_view, name='badge_list_view'),
    path('badge-details/<str:session>/<str:term>/',  views.badge_details_view, name='badge_details_view'),
    path('badge-pdf/<str:session>/<str:term>/', views.badge_pdf_view, name='badge_pdf_view'),

    path('award-badges/<str:session>/<str:term>/', views.award_student_badges, name='award_student_badges'),
    path('leaderboard/<str:session>/<str:term>/', views.leaderboard, name='leaderboard'),
    path('leaderboard-list/', views.leaderboard_list, name='leaderboard_list'),
    
    path('report-card/<str:session>/<str:term>/', views.generate_report_card, name='generate_report_card'),
    path('report-cards/', views.report_card_list, name='report_card_list'), 
    # path('report-card/<str:session>/<str:term>/', views.generate_report_card, name='generate_report_card'),
   
    # path('report-card/', views.generate_report_card, name='generate_report_card'),
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('take-exam', views.take_exams_view,name='take-exam'),
    path('start-exam/<pk>/', views.start_exams_view,name='start-exam'),
    # path('subject-start-exams/<pk>/', views.subject_start_exams,name='subject-start-exams'),
    path('calculate_marks', views.calculate_marks_view,name='calculate_marks'),
    path('view_result', views.view_result_view,name='view_result'),
    #  path('view-result/ajax/', views.view_result_ajax, name='view_result_ajax'),
    path('exam_warning', views.exam_warning_view,name='exam_warning'),
    # path('subject_view_result', views.subject_view_result,name='subject_view_result'),

    # selling pdf segment
    # path('upload_pdf/', views.upload_pdf_document, name='upload_pdf_document'),
    path('pdf_document_list/', views.pdf_document_list, name='pdf_document_list'),
    path('pdf-gallery/', views.pdf_document_list, name='pdf_gallery'),
    # path('pdf_document_detail/<str:pk>/', views.pdf_document_detail, name='pdf_document_detail'),
    # end

]




