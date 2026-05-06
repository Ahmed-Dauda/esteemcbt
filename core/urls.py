from django.urls import path
from .views import home

app_name = "core"

# core/urls.py
urlpatterns = [
    path('', home, name='farmer_home'),
    path('analyze/', home, name='analyze'),  # future expansion
]