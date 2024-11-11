

# Register your models heres.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import Profile, NewUser

from quiz.models import Course, Question, Result

# from django.contrib.auth import get_user_model
# User = get_user_model()

from import_export.admin import ImportExportModelAdmin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget


class NewUserResource(resources.ModelResource):
    class Meta:
        model = NewUser
        # fields = ('title',)

class NewUserAdmin(ImportExportModelAdmin):
    list_display = ['id', 'email', 'username', 'phone_number', 'first_name', 'last_name', 'student_class', 'school', 'countries', 'is_staff', 'is_superuser', 'is_active', 'last_login', 'date_joined']
    list_filter = ['email', 'username', 'school', 'phone_number', 'first_name', 'last_login', 'student_class']
    search_fields = ['email', 'username', 'school__school_name', 'phone_number', 'first_name', 'last_login', 'student_class']  # Use school__name to search by school name
    ordering = ['date_joined']
    
    resource_class = NewUserResource

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('school')  # Assuming school is a ForeignKey field in NewUser
        return queryset

admin.site.register(NewUser, NewUserAdmin)

# class NewUserResource(resources.ModelResource):
    
#     class Meta:
#         model = NewUser
#         # fields = ('title',)
               
# class NewUserAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'email', 'username', 'phone_number', 'first_name', 'last_name', 'student_class', 'school', 'countries', 'is_staff', 'is_superuser', 'is_active', 'last_login', 'date_joined']
#     list_filter = ['email', 'username', 'school', 'phone_number', 'first_name', 'last_login', 'student_class']
#     search_fields = ['email', 'username', 'school__school_name', 'phone_number', 'first_name', 'last_login', 'student_class']  # Use school__name to search by school name
#     ordering = ['date_joined']
    
#     resource_class = NewUserResource

# admin.site.register(NewUser, NewUserAdmin)

from import_export.widgets import ForeignKeyWidget

class ProfileResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(NewUser, 'email')
    )
    pro_img = fields.Field(
        column_name='pro_img',
        attribute='pro_img',
         # or FileWidget() if you are dealing with actual file imports
    )

    class Meta:
        model = Profile
        fields = ('id', 'user', 'username', 'first_name', 'last_name', 'gender', 'phone_number', 'countries', 'pro_img', 'bio', 'created', 'updated')
        fields = ('id', 'user', 'username', 'first_name', 'last_name', 'gender', 'phone_number', 'countries', 'pro_img', 'bio', 'created', 'updated')

 
class ProfileAdmin(ImportExportModelAdmin):
    list_display = ['id', 'user_email', 'username','schools', 'first_name', 'last_name','student_class' ,'gender', 'phone_number', 'countries', 'pro_img', 'bio', 'created', 'updated']
    # list_display = ['id', 'user', 'username', 'first_name', 'last_name', 'gender', 'phone_number', 'countries', 'pro_img', 'bio', 'created', 'updated']
    list_filter = ['user', 'username', 'first_name', 'last_name', 'gender']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'username', 'gender']
    ordering = ['created']

    def user_email(self, obj):
        return obj.user.email if obj.user else 'No Email'
    user_email.short_description = 'User Email'
    
    resource_class = ProfileResource

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        return queryset

admin.site.register(Profile, ProfileAdmin)


# class ProfileResource(resources.ModelResource):
    
#     courses = fields.Field(
#         column_name= 'user',
#         attribute='user',
#         widget=ForeignKeyWidget(NewUser,'email') )
    
#     class Meta:
#         model = Profile
#         # fields = ('title',)
               
# class ProfileAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'user','username', 'first_name', 'last_name','gender', 'phone_number', 'countries','pro_img', 'bio', 'created','updated']
#     list_filter =  ['user','username', 'first_name', 'last_name','gender' ]
#     search_fields = ['user__email','user__first_name','user__last_name', 'username', 'gender']
#     ordering = ['created']
    
#     resource_class = ProfileResource

# admin.site.register(Profile, ProfileAdmin)


