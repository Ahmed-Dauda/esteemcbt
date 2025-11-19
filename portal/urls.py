from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
     # superadmin
    path("subscriptions/", views.subscription_list, name="subscription_list"),
    path("subscriptions/<int:school_id>/", views.subscription_edit, name="subscription_edit"),

    # restricted access
    path("payment-required/", views.payment_required, name="payment_required"),

    # examples
    # path("cbt/", views.cbt_dashboard, name="cbt_dashboard"),
    # path("report-card/", views.report_card_dashboard, name="report_card_dashboard"),

    path('reports/', views.class_report_list, name='class_report_list'),
    path('reports/<str:result_class>/<int:session_id>/<int:term_id>/', views.class_report_detail, name='class_report_detail'),
    path('reports/pdf/<str:result_class>/<int:session_id>/<int:term_id>/', views.download_class_reports_pdf, name='download_class_reports_pdf'),
    # class report card
    path('report-cards/', views.report_card_list, name='report_card_list'),
    path('my-report-cards/', views.my_report_cards, name='my_report_cards'),

    # Report card detail for a student in a session and term
    path(
        'report-card/<int:student_id>/<int:session_id>/<int:term_id>/',
        views.report_card_detail,
        name='report_card_detail'
    ),

    # PDF download for full term report
    path(
        'report-card/term/pdf/<int:student_id>/<int:session_id>/<int:term_id>/',
        views.download_term_report_pdf,
        name='download_term_report_pdf'
    ),

    path("enter/", views.load_bulk_entry_page, name="enter_select"),
    path(
        "enter/<int:class_id>/<int:subject_id>/<int:session_id>/<int:term_id>/",
        views.enter_results_for_class_subject,
        name="enter_results",
    ),

]
