import imp
from django.contrib import admin
from student.models import (Payment,PDFDocument,Clubs,
                            PDFGallery,Directors, Management,
                            DocPayment, CertificatePayment, 
                            EbooksPayment, ReferrerMentor,Badge
                            )

# from student.models import Cart,CartItem, Order, OrderItem
from django.db.models import Sum
from import_export.admin import ImportExportModelAdmin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
from django.contrib import admin
from users.models import NewUser
# from .models import  Question, Choice
from django.db.models import Q 
from .models import Payment
from django.utils.html import format_html
from .models import AdvertisementImage
from student.models import BadgeDownloadStats

from django.contrib import admin
from .models import ExamAttempt, ExamEventLog

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'course',
        'start_time',
        'end_time',
        'is_submitted',
        'resume_code',
        "tab_switch_count"
    )

    list_filter = (
        'is_submitted',
        'start_time',
        'course',
        
    )

    search_fields = (
        'student__username',
        'student__email',
        'course__course_name__title',
        'resume_code'
    )

    readonly_fields = (
        'start_time',
        'resume_code',
        'saved_answers',
    )

    fieldsets = (
        ('Exam Session', {
            'fields': (
                'student',
                'course',
                'start_time',
                'end_time',
                'remaining_seconds',
                'saved_answers'
            )
        }),
        ('Status', {
            'fields': (
                'is_submitted',
                'resume_code'
            )
        }),
    )

@admin.register(ExamEventLog)
class ExamEventLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'event_type', 'timestamp')
    list_filter = ('event_type', 'timestamp', 'course')
    search_fields = ('student__username', 'student__email', 'course__course_name__title', 'details')
    readonly_fields = ('timestamp',)
    fieldsets = (
        ('Event Info', {
            'fields': ('student', 'course', 'event_type', 'details')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

admin.site.register(PDFDocument)
admin.site.register(PDFGallery)
admin.site.register(Directors)
admin.site.register(Management)
admin.site.register(Clubs)
# admin.site.register(WithdrawalRequest)


class BadgeDownloadStatsAdmin(admin.ModelAdmin):
    list_display = ('school', 'month', 'year', 'download_count')  # Show these fields in the list view
    list_filter = ('school', 'year', 'month')  # Enable filtering by school, year, and month
    search_fields = ('school__name',)  # Enable search by school name

admin.site.register(BadgeDownloadStats, BadgeDownloadStatsAdmin)


# class BadgeAdmin(admin.ModelAdmin):
#     list_display = ('id','student','final_average' ,'final_grade','badge_type','description','session', 'term')

# admin.site.register(Badge, BadgeAdmin)

class BadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'term', 'badge_type')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['badge_stats'] = Badge.objects.all().count()
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Badge, BadgeAdmin)

class AdvertisementImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'desc')

admin.site.register(AdvertisementImage, AdvertisementImageAdmin)



# admin.site.register(Payment)


