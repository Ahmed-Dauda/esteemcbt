from django.urls import path
from .views import (class_statements_pdf, family_statement_pdf, finance_dashboard_view, finance_record_receipt_view, finance_record_view,
                    FinanceRecordUpdateView,
                    FinanceRecordDeleteView, 
                    FinanceRecordCreateView,
                    finance_record_export_view,
                    finance_record_import_view, finance_student_view, finance_summary_view, student_search_api, student_statement_pdf,
                    finance_bulk_add_view,
                    )

app_name = 'finance'
 
urlpatterns = [
    path('finance-records/class/pdf/', class_statements_pdf, name='class_statements_pdf'),
    path('record/<int:pk>/receipt/', finance_record_receipt_view, name='record_receipt'),
path('dashboard/', finance_dashboard_view, name='finance_dashboard'),
    path('bulk-add/', finance_bulk_add_view, name='finance_bulk_add'),
    path('api/students/', student_search_api, name='student_search_api'),
    path('finance-records/family/pdf/', family_statement_pdf, name='family_statement_pdf'),
    path('finance-records/student/pdf/',  student_statement_pdf, name='student_statement_pdf'),
    path('finance-records/student/',  finance_student_view,  name='finance_student_view'),
path('finance-records/summary/', finance_summary_view, name='finance_summary'),
    path('finance_record/export/', finance_record_export_view, name='finance_record_export'),
    path('finance_record/import/', finance_record_import_view, name='finance_record_import'),
    path('finance_record/add/', FinanceRecordCreateView.as_view(), name='finance_record_add'),
    path('record/edit/<int:pk>/', FinanceRecordUpdateView.as_view(), name='record_edit'),
    path('record/delete/<int:pk>/', FinanceRecordDeleteView.as_view(), name='record_delete'),
    path('finance-records/', finance_record_view, name='finance_record_view'),
]
