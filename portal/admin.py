from django.contrib import admin
from .models import Result_Portal, SchoolSubscription

@admin.register(SchoolSubscription)
class SchoolSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "cbt_active",
        "cbt_expiry",
        "report_card_active",
        "report_card_expiry",
        "updated_at",
    )

    list_filter = (
        "cbt_active",
        "report_card_active",
    )

    search_fields = (
        "school__school_name",
        "school__name",
    )

    readonly_fields = ("updated_at",)

    fieldsets = (
        ("School Information", {
            "fields": ("school",)
        }),
        ("CBT Subscription", {
            "fields": ("cbt_active", "cbt_expiry")
        }),
        ("Report Card Subscription", {
            "fields": ("report_card_active", "report_card_expiry")
        }),
        ("System Info", {
            "fields": ("updated_at",),
        }),
    )

# -------------------------
@admin.register(Result_Portal)
class ResultPortalAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade_letter', 'remark', 'term', 'session', 'result_class', 'schools')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'subject__title')
    list_filter = ('term', 'session', 'result_class', 'schools', 'subject')
    autocomplete_fields = ('student', 'subject','term', 'session', 'schools')
    ordering = ('subject__title',)
    readonly_fields = ('grade_letter', 'remark')