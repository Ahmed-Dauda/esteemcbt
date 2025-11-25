from django.contrib import admin

from teacher.models import Teacher
from .models import Result_Portal, SchoolSubscription,StudentBehaviorRecord
from django.contrib import admin


@admin.register(StudentBehaviorRecord)
class StudentBehaviorRecordAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'session',
        'term',
        'handwriting',
        'games',
        'sports',
        'drawing_painting',
        'crafts',
        'punctuality',
        'attendance',
        'reliability',
        'neatness',
        'politeness',
        'honesty',
        'relationship_with_students',
        'self_control',
        'attentiveness',
        'perseverance',
        'get_form_teacher_name',  # <-- callable
        'form_teacher_comment',
        'principal_comment',
    )

    list_filter = ('session', 'term', 'student')
    search_fields = ('student__first_name', 'student__admission_no')

    fieldsets = (
        ('Student Info', {
            'fields': (('student', 'session', 'term'),)
        }),

        ('Psychomotor Skills', {
            'fields': (
                ('handwriting', 'games', 'sports'),
                ('drawing_painting', 'crafts'),
            )
        }),

        ('Affective Traits', {
            'fields': (
                ('punctuality', 'attendance', 'reliability'),
                ('neatness', 'politeness', 'honesty'),
                ('relationship_with_students', 'self_control', 'attentiveness'),
                ('perseverance',),
            )
        }),

        ('Teacher & Principal Comments', {
            'fields': (
                'form_teacher',
                'form_teacher_comment',
                'principal_comment',
            )
        }),
    )

    autocomplete_fields = ('student',)

    # --------------------------
    # Display teacher full name
    # --------------------------
    def get_form_teacher_name(self, obj):
        if obj.form_teacher:
            return f"{obj.form_teacher.first_name} {obj.form_teacher.last_name}"
        return "-"
    get_form_teacher_name.short_description = "Form Teacher Name"

    # ----------------------------------------
    # Prefill form_teacher, session, term fields
    # ----------------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "form_teacher":
            if hasattr(request, "_obj_") and request._obj_:
                student = request._obj_.student
                course = student.course_grades.first()  # assumes one class per student
                if course and course.form_teacher:
                    kwargs['initial'] = course.form_teacher.id
            # Only show staff users (teachers)
            kwargs['queryset'] = Teacher.objects.filter(school=request.user.school)
        if db_field.name == "session":
            if hasattr(request, "_obj_") and request._obj_:
                student = request._obj_.student
                course = student.course_grades.first()
                if course and course.session:
                    kwargs['initial'] = course.session.id
        if db_field.name == "term":
            if hasattr(request, "_obj_") and request._obj_:
                student = request._obj_.student
                course = student.course_grades.first()
                if course and course.term:
                    kwargs['initial'] = course.term.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Store object in request to access in formfield_for_foreignkey
    def get_form(self, request, obj=None, **kwargs):
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)



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
            "fields": ("updated_at",)
        }),
    )




@admin.register(Result_Portal)
class ResultPortalAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade_letter', 'remark', 'term', 'session', 'result_class', 'schools')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'subject__title')
    list_filter = ('term', 'session', 'result_class', 'schools', 'subject')
    autocomplete_fields = ('student', 'subject','term', 'session', 'schools')
    ordering = ('subject__title',)
    readonly_fields = ('grade_letter', 'remark')