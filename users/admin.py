

# Register your models heres.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import Profile, NewUser

from quiz.models import Course, Question, Result

# from django.contrib.auth import get_user_model
# User = get_user_model()


from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

from .models import NewUser


# ----------------------------------------------------------------------
# Import / Export resource
# ----------------------------------------------------------------------
class NewUserResource(resources.ModelResource):
    class Meta:
        model = NewUser
        fields = (
            'id', 'email', 'username', 'phone_number',
            'first_name', 'last_name',
            'student_class', 'school', 'countries', 'gender',
            'is_staff', 'is_superuser', 'is_active',
            'is_principal', 'is_accountant',
            'last_login', 'date_joined',
        )
        export_order = fields
        import_id_fields = ('email',)   # email is unique -> safe natural key
        # pro_img is intentionally omitted (CloudinaryField, not import-friendly)


# ----------------------------------------------------------------------
# Custom role filter
# ----------------------------------------------------------------------
class RoleFilter(SimpleListFilter):
    title = _('role')
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return (
            ('principal',  _('Principals')),
            ('accountant', _('Accountants')),
            ('staff',      _('Staff')),
            ('superuser',  _('Superusers')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'principal':
            return queryset.filter(is_principal=True)
        if self.value() == 'accountant':
            return queryset.filter(is_accountant=True)
        if self.value() == 'staff':
            return queryset.filter(is_staff=True)
        if self.value() == 'superuser':
            return queryset.filter(is_superuser=True)
        return queryset


# ----------------------------------------------------------------------
# Admin
# ----------------------------------------------------------------------
class NewUserAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = [
        'email', 'username', 'phone_number', 'first_name', 'last_name',
        'student_class', 'school', 'avatar', 'countries',
        'is_staff', 'is_superuser', 'is_active',
        'is_principal', 'is_accountant',
        'last_login', 'date_joined',
    ]
    list_filter = [
        'email', 'username', 'school', 'phone_number',
        'first_name', 'last_login', 'student_class',
        'is_staff', 'is_superuser', 'is_active',
        'is_principal', 'is_accountant',
        RoleFilter,
    ]
    search_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
        'admission_no',           # 👈 new — needed for autocomplete + search
        'school__school_name',
        'student_class',
    ]
    ordering = ['date_joined']
    autocomplete_fields = ['school']
    resource_class = NewUserResource

    # Tick roles directly from the list page
    list_editable = ('is_accountant', 'is_principal', 'is_active')

    @admin.display(description='Photo')
    def avatar(self, obj):
        if obj.pro_img:
            return format_html(
                '<img src="{}" style="height:32px;width:32px;'
                'border-radius:50%;object-fit:cover;" />',
                obj.pro_img.url,
            )
        return '—'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('school')

    def get_actions(self, request):
        actions = super().get_actions(request)
        # The built-in "export_selected_objects" action is automatically available
        return actions


admin.site.register(NewUser, NewUserAdmin)




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


