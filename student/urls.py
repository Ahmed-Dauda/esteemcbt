from django.urls import path
from sms.views import update_referrer_mentor

from . import views


app_name = 'student'

urlpatterns = [
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    # path('withdrawal/', views.withdrawal_request, name='withdrawal_request'),
    # URL for updating a referrer mentor
    path('referrer_mentor_detail/<int:pk>/', update_referrer_mentor, name='referrer_mentor_detail'),
   
    
    # path('question-list/', views.question_list_view, name='question-list'),
    # path('question-form/', views.question_form_view, name='question-form'),      
    # path('verify/<str:id>/', views.verify,name='verify'),
    # path('docverify/<str:id>/', views.docverify,name='docverify'),
    
    # path('student/verify/<str:id>/', views.verify_payment, name='verify_payment'),
  
    # path('process', views.process,name='process'),
    # new url subject_view_result
   
    path('take-exam', views.take_exams_view,name='take-exam'),
    path('start-exam/<pk>/', views.start_exams_view,name='start-exam'),
    # path('subject-start-exams/<pk>/', views.subject_start_exams,name='subject-start-exams'),
    path('calculate_marks', views.calculate_marks_view,name='calculate_marks'),
    path('view_result', views.view_result_view,name='view_result'),
    path('exam_warning', views.exam_warning_view,name='exam_warning'),
    # path('subject_view_result', views.subject_view_result,name='subject_view_result'),

    # selling pdf segment
    # path('upload_pdf/', views.upload_pdf_document, name='upload_pdf_document'),
    path('pdf_document_list/', views.pdf_document_list, name='pdf_document_list'),
    path('pdf-gallery/', views.pdf_document_list, name='pdf_gallery'),
    # path('pdf_document_detail/<str:pk>/', views.pdf_document_detail, name='pdf_document_detail'),
    # end

    path('pdf/<pk>/', views.pdf_id_view,name='pdf'),
    # path('check_marks/<pk>/', views.check_marks_view,name='check_marks'),
    # path('verify/', views.verify_cert, name='verify_cert'),

    path('verify/<str:certificate_code>/', views.verify_certificate, name='verify_certificate'),
    
   
]




