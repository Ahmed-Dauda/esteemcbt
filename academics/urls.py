from django.urls import path
from . import views
from .views import StudentAutocompleteView

app_name = 'academics'  

urlpatterns = [
   path('student-autocomplete/', StudentAutocompleteView.as_view(), name='student-autocomplete'),
    path('student-search/', views.student_search, name='student_search'),
    path('add/', views.add_conduct, name='add_conduct'),
    path('list/', views.list_conducts, name='list_conducts'),
    path('conducts/edit/<int:pk>/', views.edit_conduct, name='edit_conduct'),
    path('conducts/delete/<int:pk>/', views.delete_conduct, name='delete_conduct'),

]
