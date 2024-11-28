from django.urls import path
from .views import (finance_record_view,
                    FinanceRecordUpdateView,
                    FinanceRecordDeleteView, 
                    FinanceRecordCreateView,
                    finance_record_export_view,
                    finance_record_import_view,
              
                    )

app_name = 'finance'
 
urlpatterns = [
    # path('finance/finance_record/import-preview/', finance_record_import_preview, name='finance_record_import_preview'),
    # path('finance/finance_record/confirm_import/', confirm_import, name='confirm_import'),

    path('finance_record/export/', finance_record_export_view, name='finance_record_export'),
    path('finance_record/import/', finance_record_import_view, name='finance_record_import'),
    path('finance_record/add/', FinanceRecordCreateView.as_view(), name='finance_record_add'),
    path('record/edit/<int:pk>/', FinanceRecordUpdateView.as_view(), name='record_edit'),
    path('record/delete/<int:pk>/', FinanceRecordDeleteView.as_view(), name='record_delete'),
    path('finance-records/', finance_record_view, name='finance_record_view'),
]
