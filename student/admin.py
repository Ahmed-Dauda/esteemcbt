import importlib
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



from datetime import date

from django.contrib import admin, messages
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.core.files.base import ContentFile
from django.utils.html import format_html

from .models import AdmissionLetter
from users.models import Profile
from quiz.models import School
from .services.admission_letter import generate_admission_letter_pdf
from .services.admission_letter_candidates import find_candidates
from .services.admission_letter_config import (
    SESSION_NAME, LETTER_ISSUING_SCHOOL, CLASS_LABELS, DEFAULT_RESUME_DATE,
)


@admin.register(AdmissionLetter)
class AdmissionLetterAdmin(admin.ModelAdmin):
    list_display      = ('student', 'class_offered', 'average_score',
                         'pass_threshold', 'pdf_button', 'generated_at', 'is_sent')
    list_filter       = ('class_offered', 'is_sent')
    search_fields     = ('student__first_name', 'student__last_name',
                         'student__admission_no')
    readonly_fields   = ('generated_at', 'subject_scores',
                         'average_score', 'pass_threshold')
    date_hierarchy    = 'generated_at'

    def pdf_button(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" '
                'style="padding:4px 10px;background:#1a6a3a;color:#fff;'
                'border-radius:3px;text-decoration:none;font-weight:bold;">'
                '📄 Open PDF</a>',
                obj.pdf_file.url)
        return '—'
    pdf_button.short_description = 'PDF'

    # ── Custom admin URLs ────────────────────────────────────────────────
    def get_urls(self):
        custom = [
            path('candidates/',
                 self.admin_site.admin_view(self.candidates_view),
                 name='admission_letter_candidates'),
            path('candidates/generate/<int:profile_id>/',
                 self.admin_site.admin_view(self.generate_one),
                 name='admission_letter_generate_one'),
            path('candidates/generate-all/',
                 self.admin_site.admin_view(self.generate_all),
                 name='admission_letter_generate_all'),
        ]
        return custom + super().get_urls()

    # ── Helpers ──────────────────────────────────────────────────────────
    def _get_issuing_school_and_resume(self):
        try:
            sch = School.objects.get(school_name=LETTER_ISSUING_SCHOOL)
        except School.DoesNotExist:
            return None, date(*DEFAULT_RESUME_DATE)
        return sch, (sch.next_term_date or date(*DEFAULT_RESUME_DATE))

    def _build_letter(self, profile, class_key, avg, scores, thr, sch, resume, force=False):
        letter, created = AdmissionLetter.objects.get_or_create(
            student=profile, session=None,
            defaults={
                'school': sch,
                'class_offered': CLASS_LABELS[class_key],
                'subject_scores': {k: str(v) for k, v in scores.items()},
                'average_score': avg,
                'pass_threshold': thr,
                'resume_date': resume,
            })
        if letter.pdf_file and not force:
            return letter, False

        student_name = (f"{profile.first_name or ''} {profile.last_name or ''}").strip() \
                       or (profile.user.display_name if profile.user else str(profile))

        buf = generate_admission_letter_pdf(
            student_name=student_name,
            class_offered=class_key,
            guardian_title=profile.guardian_title or '',
            guardian_name=profile.guardian_name or '',
            guardian_address=profile.guardian_address or '',
            school=sch,
            resume_date=resume,
        )
        letter.pdf_file.save(
            f"admission_{profile.id}_{class_key}.pdf",
            ContentFile(buf.read()), save=True)
        return letter, True

    # ── Views ────────────────────────────────────────────────────────────
    def candidates_view(self, request):
        passed, failed, missing = find_candidates(session_name=SESSION_NAME)
        sch, resume = self._get_issuing_school_and_resume()

        rows = []
        for profile, class_key, avg, scores, thr in passed:
            existing = AdmissionLetter.objects.filter(
                student=profile,
                class_offered=CLASS_LABELS[class_key],
            ).first()
            rows.append({
                'profile': profile,
                'class_key': class_key,
                'class_label': CLASS_LABELS[class_key],
                'avg': avg,
                'threshold': thr,
                'scores': scores,
                'has_letter': bool(existing and existing.pdf_file),
                'letter': existing,
                'generate_url': reverse('admin:admission_letter_generate_one',
                                        args=[profile.id]),
                'has_guardian': bool(profile.guardian_name and profile.guardian_address),
            })

        ctx = {
            **self.admin_site.each_context(request),
            'title': 'Admission Letter Dashboard',
            'rows': rows,
            'failed': failed,
            'missing': missing,
            'has_school': bool(sch),
            'generate_all_url': reverse('admin:admission_letter_generate_all'),
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/student/admission_letter_candidates.html',
            ctx)

    def generate_one(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id)
        passed, _, _ = find_candidates(session_name=SESSION_NAME, student_id=profile_id)
        if not passed:
            messages.error(request, f"{profile} is not in the passing list.")
            return redirect('admin:admission_letter_candidates')

        sch, resume = self._get_issuing_school_and_resume()
        if not sch:
            messages.error(request, f"School '{LETTER_ISSUING_SCHOOL}' not found.")
            return redirect('admin:admission_letter_candidates')

        profile, class_key, avg, scores, thr = passed[0]
        if not (profile.guardian_name and profile.guardian_address):
            messages.warning(request, f"{profile} has no guardian name/address.")
            return redirect('admin:admission_letter_candidates')

        letter, created = self._build_letter(profile, class_key, avg, scores, thr,
                                             sch, resume)
        if created:
            messages.success(request, f"Letter generated for {profile}.")
            return redirect(letter.pdf_file.url)
        messages.info(request, f"{profile} already had a letter.")
        return redirect(letter.pdf_file.url)

    def generate_all(self, request):
        passed, _, _ = find_candidates(session_name=SESSION_NAME)
        if not passed:
            messages.warning(request, "No passing students found.")
            return redirect('admin:admission_letter_candidates')

        sch, resume = self._get_issuing_school_and_resume()
        if not sch:
            messages.error(request, f"School '{LETTER_ISSUING_SCHOOL}' not found.")
            return redirect('admin:admission_letter_candidates')

        ok, skipped, no_guardian = 0, 0, 0
        for profile, class_key, avg, scores, thr in passed:
            if not (profile.guardian_name and profile.guardian_address):
                no_guardian += 1
                continue
            _, created = self._build_letter(profile, class_key, avg, scores, thr,
                                            sch, resume)
            if created:
                ok += 1
            else:
                skipped += 1

        messages.success(
            request,
            f"Done. Generated: {ok}, already existed: {skipped}, "
            f"missing guardian info: {no_guardian}."
        )
        return redirect('admin:admission_letter_candidates')


from .models import LetterTemplate

@admin.register(LetterTemplate)
class LetterTemplateAdmin(admin.ModelAdmin):
    list_display = ('school', 'updated_at')
    readonly_fields = ('updated_at',)
    fieldsets = (
        (None, {'fields': ('school',)}),
        ('Letterhead', {
            'fields': ('letterhead_school_line',)
        }),
        ('Body paragraphs', {
            'fields': ('intro_template', 'deposit_paragraph_template'),
        }),
        ('Numbered notes', {
            'fields': ('notes_template', 'extra_paragraph'),
        }),
        ('Closing', {
            'fields': ('closing_line', 'signature_title'),
        }),
        ('Deposit / bank', {
            'fields': ('deposit_amount_words', 'deposit_amount_display',
                       'bank_name', 'bank_branch_hint',
                       'bank_account', 'bank_account_name'),
        }),
        ('Acceptance emails', {
            'fields': ('acceptance_email_1', 'acceptance_email_2'),
        }),
        ('Windows', {
            'fields': ('payment_window_days', 'acceptance_window_days'),
        }),
    )
