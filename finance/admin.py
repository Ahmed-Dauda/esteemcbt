from django.contrib import admin
from django.utils.html import format_html

from import_export.admin import ImportExportModelAdmin

from .models import FinanceRecord
from .resources import FinanceRecordResource


@admin.register(FinanceRecord)
class FinanceRecordAdmin(ImportExportModelAdmin):
    resource_class = FinanceRecordResource

    list_display = (
        'sn',
        'names',
        'student',
        'student_class',
        'school',
        'session',
        'term',
        'week_start',
        'initial_total_deposit',
        'total_deposit',
        'school_shop',
        'caps',
        'haircut',
        'others',
        'total_expense',
        'current_balance',
        'balance_brought_forward',
        'get_status_color',
        'created_by',
        'updated_at',
    )

    list_filter = (
        'status',
        'school',
        'session',
        'term',
        'week_start',
    )

    search_fields = (
        'names',
        'student__first_name',
        'student__last_name',
        'student__admission_no',
        'student_class',
    )

    autocomplete_fields = ('student', 'school', 'session', 'term')
    list_select_related = ('student', 'school', 'session', 'term')

    date_hierarchy = 'week_start'
    ordering = ('-sn',)
    list_per_page = 50
    save_on_top = True

    readonly_fields = (
        'total_deposit',
        'total_expense',
        'balance_brought_forward',
        'current_balance',
        'status',
        'created_by',
        'updated_by',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Student', {
            'fields': ('student', 'names', 'student_class', 'school')
        }),
        ('Scope', {
            'fields': ('session', 'term', 'week_start')
        }),
        ('Money In', {
            'fields': ('initial_total_deposit',)
        }),
        ('Money Out', {
            'fields': ('school_shop', 'caps', 'haircut', 'others')
        }),
        ('Computed (read-only)', {
            'fields': (
                'total_deposit',
                'total_expense',
                'balance_brought_forward',
                'current_balance',
                'status',
            ),
            'classes': ('collapse',),
        }),
        ('Notes', {
            'fields': ('note',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status', ordering='status')
    def get_status_color(self, obj):
        if obj.status == 'exhausted':
            return format_html(
                '<span style="color:#c0392b;font-weight:bold;">{}</span>',
                obj.status.capitalize(),
            )
        return format_html(
            '<span style="color:#27ae60;font-weight:bold;">{}</span>',
            obj.status.capitalize(),
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)        