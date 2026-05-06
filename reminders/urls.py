from django.urls import path
from . import views

urlpatterns = [
    path('detector/', views.index, name='index'),
    path('analyze/', views.analyze_fraud, name='analyze'),
    path('api/v1/check/', views.analyze_fraud, name='api_check'),
]