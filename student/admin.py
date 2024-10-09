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


