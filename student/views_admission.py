"""Front-end views for the admission-letter workflow (staff only)."""
from datetime import date, timezone
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from datetime import date, timedelta
import re
from .services.admission_letter_config import (
    SESSION_NAME, LETTER_ISSUING_SCHOOL, CLASS_LABELS, DEFAULT_RESUME_DATE,
    PAYMENT_WINDOW_DAYS, ACCEPTANCE_WINDOW_DAYS,
    DEPOSIT_AMOUNT_WORDS, DEPOSIT_AMOUNT_DISPLAY,
    DEFAULT_PRINCIPAL_NAME,
)

from users.models import Profile
from quiz.models import School
from .models import AdmissionLetter
from .services.admission_letter import generate_admission_letter_pdf
from .services.admission_letter_candidates import _student_in_school, find_candidates
from .services.admission_letter_config import (
    SESSION_NAME, LETTER_ISSUING_SCHOOL, CLASS_LABELS, DEFAULT_RESUME_DATE,
    PAYMENT_WINDOW_DAYS,
    DEPOSIT_AMOUNT_WORDS, DEPOSIT_AMOUNT_DISPLAY,
    DEFAULT_PRINCIPAL_NAME,
)

from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and user.is_staff):
            return redirect_to_login(request.get_full_path(), '/admin/login/')

        # Superusers can work on any school
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        school = getattr(request, 'school', None) or getattr(user, 'school', None)
        if school is None or getattr(user, 'school_id', None) != school.id:
            raise PermissionDenied("You don't have access to this school.")

        return view_func(request, *args, **kwargs)
    return _wrapped


ALL_CLASSES = ['JSS1', 'JSS2', 'JSS3', 'SS1', 'SS2']


def _get_letter_template(sch):
    if sch is None:
        return None
    tpl, _ = LetterTemplate.objects.get_or_create(school=sch)
    return tpl



from django.conf import settings

def _issuing_school_and_resume(request):
    sch = getattr(request, 'school', None)               # subdomain (production)

    if sch is None and request.user.is_authenticated:
        sch = getattr(request.user, 'school', None)      # the logged-in user's own school

    if sch is None and settings.DEBUG:                   # local dev last resort
        from quiz.models import School
        sch = School.objects.filter(
            school_name=getattr(settings, 'DEV_DEFAULT_SCHOOL', '')).first()

    if not sch:
        return None, None
    return sch, getattr(sch, 'next_term_date', None)


def _build_or_get_letter(profile, class_key, avg, scores, thr, sch, resume, force=False):
    letter, created = AdmissionLetter.objects.get_or_create(
        student=profile,
        defaults={
            'session': None,
            'school': sch,
            'class_offered': CLASS_LABELS[class_key],
            'subject_scores': {k: str(v.get('pct', v)) if isinstance(v, dict) else str(v)
            for k, v in scores.items()},
            'average_score': avg,
            'pass_threshold': thr,
            'resume_date': resume,
        },
    )

    if letter.pdf_file and not force:
        return letter, False

    # Delete old file so Django writes the new one under the SAME name
    if letter.pdf_file:
        try:
            letter.pdf_file.delete(save=False)
        except Exception:
            pass

    # ── Student name — from the NewUser, not the Profile ─────────────
    user = getattr(profile, 'user', None)
    if user:
        student_name = (f"{user.first_name or ''} {user.last_name or ''}").strip() \
                       or user.display_name
    else:
        student_name = str(profile)

    # ── Letter template (shared constants for this school) ──────────
    letter_template = _get_letter_template(sch)

    # ── Dates ────────────────────────────────────────────────────────
    letter_date = date.today()   # always the date the PDF is printed
    # fff
    payment_deadline = letter_date + timedelta(days=PAYMENT_WINDOW_DAYS)
    acceptance_deadline = payment_deadline + timedelta(days=ACCEPTANCE_WINDOW_DAYS)

    # Resume date always comes from the School model (School.next_term_date).
    resume_date = resume

    buf = generate_admission_letter_pdf(
        student_name=student_name,
        class_offered=class_key,
        guardian_title=profile.guardian_title or '',
        guardian_name=profile.guardian_name or '',
        guardian_address=profile.guardian_address or '',
        school=sch,
        resume_date=resume_date,
        letter_date=letter_date,
        payment_deadline=payment_deadline,
        acceptance_deadline=acceptance_deadline,
        letter_template=letter_template,
        override_student_name=letter.override_student_name,
        override_guardian_name=letter.override_guardian_name,
        override_guardian_address=letter.override_guardian_address,
        override_principal_name=letter.override_principal_name,
        override_deposit_words=letter.override_deposit_words,
        override_deposit_display=letter.override_deposit_display,
        override_intro=letter.override_intro,
        override_deposit_para=letter.override_deposit_para,
        override_notes_text=letter.override_notes_text,
        extra_note=letter.extra_note,
    )

    letter.pdf_file.save(
        f"admission_{profile.id}_{class_key}_{int(time.time())}.pdf",
        ContentFile(buf.read()), save=True)
    return letter, True


def _matches(profile, q):
    """Case-insensitive match on first name, last name, admission no, or ID."""
    if not q:
        return True
    ql = q.lower().strip()
    return (
        ql in (profile.first_name or '').lower()
        or ql in (profile.last_name or '').lower()
        or ql in (profile.admission_no or '').lower()
        or ql == str(profile.id)
    )


@staff_required
def admission_letters_list(request):
    sch, resume = _issuing_school_and_resume(request)
    if not sch:
        messages.error(request, "No school found for this domain.")
        return redirect('/')

    tpl = _get_letter_template(sch)
    q = request.GET.get('q', '').strip()
    class_filter = request.GET.get('class', '').strip()

    passed, failed, missing = find_candidates(school=sch, session_name=tpl.session_name)

    # Newest first (new registrations get higher IDs)
    passed.sort(key=lambda t: t[0].id, reverse=True)
    failed.sort(key=lambda t: t[0].id, reverse=True)
    missing.sort(key=lambda t: t[0].id, reverse=True)

    total_passed = len(passed)
    total_failed = len(failed)
    total_missing = len(missing)

    if q:
        passed = [t for t in passed if _matches(t[0], q)]
        failed = [t for t in failed if _matches(t[0], q)]
        missing = [t for t in missing if _matches(t[0], q)]

    if class_filter:
        passed = [t for t in passed if t[1] == class_filter]
        failed = [t for t in failed if t[1] == class_filter]
        missing = [t for t in missing if t[1] == class_filter]

    rows = []
    for profile, class_key, avg, scores, thr in passed:
        letter = AdmissionLetter.objects.filter(
            student=profile,
            school=sch,
            class_offered=CLASS_LABELS[class_key],
        ).first()
        rows.append({
            'profile': profile,
            'class_key': class_key,
            'class_label': CLASS_LABELS[class_key],
            'avg': avg,
            'threshold': thr,
            'scores': scores,
            'letter': letter,
            'has_letter': bool(letter and letter.pdf_file),
            'has_guardian': bool(profile.guardian_name and profile.guardian_address),
        })

    ctx = {
        'title': 'Admission Letters',
        'rows': rows,
        'failed': failed,
        'missing': missing,
        'has_school': bool(sch),
        'session_name': tpl.session_name,
        'issuing_school': sch.school_name,
        'q': q,
        'class_filter': class_filter,
        'classes': ALL_CLASSES,
        'total_passed': total_passed,
        'total_failed': total_failed,
        'total_missing': total_missing,
        'filtered': bool(q or class_filter),
    }
    return render(request, 'student/dashboard/list.html', ctx)



@staff_required
def regenerate_letter_and_open(request, profile_id):
    """Rebuild the PDF from the saved overrides, then open it."""
    sch, resume = _issuing_school_and_resume(request)
    if not sch:
        messages.error(request, "No school found for this domain.")
        return redirect('student:admission_letters_list')

    profile = get_object_or_404(Profile.objects.select_related('user'), id=profile_id)
    if not _student_in_school(profile, sch):
        raise Http404("Student not found for this school.")

    tpl = _get_letter_template(sch)

    passed, _, _ = find_candidates(
        school=sch, session_name=tpl.session_name, student_id=profile_id)
    if not passed:
        messages.error(request, f"{profile} is not in the passing list.")
        return redirect('student:admission_letters_list')

    _, class_key, avg, scores, thr = passed[0]
    letter, _ = _build_or_get_letter(
        profile, class_key, avg, scores, thr, sch, resume, force=True)
    return HttpResponseRedirect(letter.pdf_file.url)

@staff_required
def generate_letter(request, profile_id):
    """Generate (or regenerate) one student's letter, then open the PDF."""
    sch, resume = _issuing_school_and_resume(request)
    if not sch:
        messages.error(request, "No school found for this domain.")
        return redirect('student:admission_letters_list')

    profile = get_object_or_404(Profile.objects.select_related('user'), id=profile_id)

    tpl = _get_letter_template(sch)

    if request.GET.get('force') == '1':
        AdmissionLetter.objects.filter(student=profile, school=sch).delete()

    passed, _, _ = find_candidates(
        school=sch, session_name=tpl.session_name, student_id=profile_id)
    if not passed:
        messages.error(request, f"{profile} is not in the passing list.")
        return redirect('student:admission_letters_list')

    _, class_key, avg, scores, thr = passed[0]

    if not (profile.guardian_name and profile.guardian_address):
        messages.warning(request, f"{profile} has no guardian name/address. "
                                  f"Add it via admin first.")
        return redirect('student:admission_letters_list')

    letter, created = _build_or_get_letter(
        profile, class_key, avg, scores, thr, sch, resume)
    if created:
        messages.success(request, f"Letter generated for {profile}.")
    return HttpResponseRedirect(letter.pdf_file.url)


@staff_required
def generate_all_letters(request):
    """Generate every missing letter. POST-only to avoid accidental triggers."""
    if request.method != 'POST':
        messages.error(request, "Use the button on the list page.")
        return redirect('student:admission_letters_list')

    sch, resume = _issuing_school_and_resume()
    if not sch:
        messages.error(request, f"School '{LETTER_ISSUING_SCHOOL}' not found.")
        return redirect('student:admission_letters_list')

    passed, _, _ = find_candidates(school=sch, session_name=tpl.session_name)
    ok, existed, no_guardian = 0, 0, 0

    for profile, class_key, avg, scores, thr in passed:
        if not (profile.guardian_name and profile.guardian_address):
            no_guardian += 1
            continue
        _, created = _build_or_get_letter(profile, class_key, avg, scores, thr,
                                          sch, resume)
        if created:
            ok += 1
        else:
            existed += 1

    messages.success(
        request,
        f"Done. Generated: {ok}, already existed: {existed}, "
        f"missing guardian info: {no_guardian}."
    )
    return redirect('student:admission_letters_list')

from django import forms


class AdmissionLetterForm(forms.ModelForm):
    class Meta:
        model = AdmissionLetter
        fields = [
            'letter_date', 'payment_deadline', 'acceptance_deadline',
            'override_student_name',
            'override_guardian_name',
            'override_guardian_address',
            'override_principal_name',
            'override_deposit_words',
            'override_deposit_display',
            'override_intro',
            'override_deposit_para',
            'override_notes_text',
            'extra_note',
        ]
        widgets = {
            'letter_date':         forms.DateInput(attrs={'type': 'date'}),
            'payment_deadline':    forms.DateInput(attrs={'type': 'date'}),
            'acceptance_deadline': forms.DateInput(attrs={'type': 'date'}),
            'override_guardian_address': forms.Textarea(attrs={'rows': 2}),
            'override_intro':         forms.Textarea(attrs={'rows': 4}),
            'override_deposit_para':  forms.Textarea(attrs={'rows': 6}),
            'override_notes_text':    forms.Textarea(attrs={'rows': 8}),
            'extra_note':             forms.Textarea(attrs={'rows': 3}),
        }


import time  # add at top of file if not already present


def _compute_defaults(profile, letter, sch, resume):
    """Auto values that apply when no override is set."""
    from .models import (
        DEFAULT_INTRO_TEMPLATE, DEFAULT_DEPOSIT_TEMPLATE,
        DEFAULT_NOTES_TEMPLATE, DEFAULT_CLOSING_LINE, DEFAULT_SIGNATURE_TITLE,
    )

    # Student name from NewUser (via profile.user)
    user = getattr(profile, 'user', None)
    if user:
        default_student_name = (f"{user.first_name or ''} {user.last_name or ''}").strip() \
                               or user.display_name
    else:
        default_student_name = str(profile)

    guardian_full = f"{profile.guardian_title or ''} {profile.guardian_name or ''}".strip()

    if letter.generated_at:
        base_date = letter.generated_at.date()
    else:
        base_date = date.today()

    payment_default    = base_date + timedelta(days=PAYMENT_WINDOW_DAYS)
    acceptance_default = payment_default + timedelta(days=ACCEPTANCE_WINDOW_DAYS)

    tpl = _get_letter_template(sch)
    if tpl:
        raw_intro   = tpl.intro_template or DEFAULT_INTRO_TEMPLATE
        raw_deposit = tpl.deposit_paragraph_template or DEFAULT_DEPOSIT_TEMPLATE
        raw_notes   = tpl.notes_template or DEFAULT_NOTES_TEMPLATE
        raw_extra   = tpl.extra_paragraph or ''
    else:
        raw_intro   = DEFAULT_INTRO_TEMPLATE
        raw_deposit = DEFAULT_DEPOSIT_TEMPLATE
        raw_notes   = DEFAULT_NOTES_TEMPLATE
        raw_extra   = ''

    # Resolve placeholders so the form shows exactly what the PDF will print
    intro_default   = _resolve_template_text(raw_intro, profile, letter, sch, resume)
    deposit_default = _resolve_template_text(raw_deposit, profile, letter, sch, resume)
    notes_default   = _resolve_template_text(raw_notes, profile, letter, sch, resume)
    extra_default   = _resolve_template_text(raw_extra, profile, letter, sch, resume)

    return {
        'letter_date':               base_date,
        'payment_deadline':          payment_default,
        'acceptance_deadline':       acceptance_default,
        'override_student_name':     default_student_name,
        'override_guardian_name':    guardian_full,
        'override_guardian_address': profile.guardian_address or '',
        'override_principal_name':   (getattr(sch, 'principal_name', '') or
                                      DEFAULT_PRINCIPAL_NAME),
        'override_deposit_words':    DEPOSIT_AMOUNT_WORDS,
        'override_deposit_display':  DEPOSIT_AMOUNT_DISPLAY,
        'override_intro':            intro_default,
        'override_deposit_para':     deposit_default,
        'override_notes_text':       notes_default,
        'extra_note':                extra_default,
    }





def _save_letter_smart(form, defaults):
    letter = form.save(commit=False)
    for field_name, default_value in defaults.items():
        submitted = getattr(letter, field_name, None)
        if submitted in (None, ''):
            continue
        # Ignore any value that still contains template placeholders —
        # those are template text, not real overrides.
        # if isinstance(submitted, str) and '{' in submitted and '}' in submitted:
        #     setattr(letter, field_name, '')
        #     continue
        # Date fields
        if isinstance(default_value, date):
            if submitted == default_value:
                setattr(letter, field_name, None)
        else:
            if str(submitted).strip() == str(default_value).strip():
                setattr(letter, field_name, '')
    letter.save()
    return letter




@staff_required
def edit_letter(request, profile_id):
    sch, resume = _issuing_school_and_resume(request)
    if not sch:
        messages.error(request, "No school found for this domain.")
        return redirect('student:admission_letters_list')
    # fff
    profile = get_object_or_404(Profile.objects.select_related('user'), id=profile_id)
    if not _student_in_school(profile, sch):
        raise Http404("Student not found for this school.")

    letter_template = _get_letter_template(sch)
    
    letter  = AdmissionLetter.objects.filter(student=profile, school=sch).first()

    if letter is None:
        # ff
        passed, _, _ = find_candidates(
            school=sch, session_name=letter_template.session_name, student_id=profile_id)
        if not passed:
            messages.error(request, f"{profile} is not in the passing list.")
            return redirect('student:admission_letters_list')

        sch, resume = _issuing_school_and_resume(request)
        if not sch:
            messages.error(request, f"School '{LETTER_ISSUING_SCHOOL}' not found.")
            return redirect('student:admission_letters_list')

        _, class_key, avg, scores, thr = passed[0]
        letter, _ = _build_or_get_letter(profile, class_key, avg, scores, thr,
                                         sch, resume, force=True)

    sch, resume = _issuing_school_and_resume(request)
    defaults = _compute_defaults(profile, letter, sch, resume)

    if request.method == 'POST':
        form = AdmissionLetterForm(request.POST, instance=letter)
        if form.is_valid():
            letter = _save_letter_smart(form, defaults)

            # Regenerate the PDF so edits show up immediately
            class_key = next(
                (k for k, v in CLASS_LABELS.items() if v == letter.class_offered), None)
            if class_key:
                letter, _ = _build_or_get_letter(
                    profile, class_key,
                    letter.average_score, letter.subject_scores, letter.pass_threshold,
                    sch, resume, force=True)

            # ── Report what actually got saved as an override ────────
            saved_overrides = []
            for field_name in form.fields:
                v = getattr(letter, field_name, None)
                if v not in (None, '', 0):
                    saved_overrides.append(
                        field_name.replace('override_', '').replace('_', ' '))

            if saved_overrides:
                messages.success(
                    request,
                    f"Saved. Overrides stored for: {', '.join(saved_overrides)}. "
                    f"The PDF has been regenerated.")
            else:
                messages.info(
                    request,
                    "Saved. Nothing was stored as an override — every field still "
                    "follows the shared Letter Template.")

            # Reload the form from DB so fields reflect what was actually saved
            # Recompute defaults from the freshly-saved letter so the form
            # reflects the newest resolved values (e.g. name changes)
            defaults_after = _compute_defaults(profile, letter, sch, resume)
            form = AdmissionLetterForm(instance=letter)
            for field_name, default_value in defaults_after.items():
                if field_name not in form.fields:
                    continue
                if getattr(letter, field_name, None) in (None, ''):
                    form.initial[field_name] = default_value
    else:
        # GET — build a fresh form and pre-fill blanks with template values
        form = AdmissionLetterForm(instance=letter)
        for field_name, default_value in defaults.items():
            if field_name not in form.fields:
                continue
            if getattr(letter, field_name, None) in (None, ''):
                form.initial[field_name] = default_value

    # ff
    # Letter date on the form always shows today (matches the printed PDF)
    today = date.today()
    form.initial['letter_date'] = today
    form.initial['payment_deadline'] = today + timedelta(days=PAYMENT_WINDOW_DAYS)
    form.initial['acceptance_deadline'] = (
        form.initial['payment_deadline'] + timedelta(days=ACCEPTANCE_WINDOW_DAYS))
    # ff
    passed, _, _ = find_candidates(
    school=sch, session_name=letter_template.session_name, student_id=profile_id)

    from .models import (
        DEFAULT_INTRO_TEMPLATE, DEFAULT_DEPOSIT_TEMPLATE,
        DEFAULT_NOTES_TEMPLATE, DEFAULT_CLOSING_LINE, DEFAULT_SIGNATURE_TITLE,
    )
    if letter_template:
        active_intro     = letter_template.intro_template or DEFAULT_INTRO_TEMPLATE
        active_deposit   = letter_template.deposit_paragraph_template or DEFAULT_DEPOSIT_TEMPLATE
        active_notes     = letter_template.notes_template or DEFAULT_NOTES_TEMPLATE
        active_extra     = letter_template.extra_paragraph or ''
        active_closing   = letter_template.closing_line or DEFAULT_CLOSING_LINE
        active_sigtitle  = letter_template.signature_title or DEFAULT_SIGNATURE_TITLE
        template_updated = letter_template.updated_at
    else:
        active_intro     = DEFAULT_INTRO_TEMPLATE
        active_deposit   = DEFAULT_DEPOSIT_TEMPLATE
        active_notes     = DEFAULT_NOTES_TEMPLATE
        active_extra     = ''
        active_closing   = DEFAULT_CLOSING_LINE
        active_sigtitle  = DEFAULT_SIGNATURE_TITLE
        template_updated = None

    # Resume date — always comes from the School (School.next_term_date)
    if getattr(sch, 'next_term_date', None):
        d = sch.next_term_date
        day = d.day
        suffix = ('th' if 10 <= day % 100 <= 20
                  else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th'))
        active_resume_display = f"{day}{suffix} {d.strftime('%B, %Y')}"
    else:
        active_resume_display = ''

    ctx = {
        'title': f'Edit letter — {profile}',
        'profile': profile,
        'letter': letter,
        'form': form,
        'passed': passed[0] if passed else None,
        'has_pdf': bool(letter.pdf_file),
        'pdf_url': letter.pdf_file.url if letter.pdf_file else None,
        'letter_template': letter_template,
        'template_updated': template_updated,
        'active_intro':    active_intro,
        'active_deposit':  active_deposit,
        'active_notes':    active_notes,
        'active_extra':    active_extra,
        'active_closing':  active_closing,
        'active_sigtitle': active_sigtitle,
        'active_resume_display': active_resume_display,
    }
    return render(request, 'student/dashboard/edit.html', ctx)



from django import forms as djforms
from .models import LetterTemplate


class LetterTemplateForm(djforms.ModelForm):
    """Edits both School (letterhead-level) and LetterTemplate (body-level) constants."""

    # School fields
    school_display_name = djforms.CharField(
        label="School name (letterhead)",
        max_length=255,
        help_text="Shown in big text at the top of the PDF.")
    school_motto = djforms.CharField(
        label="Motto", max_length=255, required=False)
    school_address = djforms.CharField(
        label="Address", max_length=355, required=False,
        widget=djforms.Textarea(attrs={'rows': 1}))
    school_next_term_date = djforms.DateField(
        label="Resume date", required=False,
        widget=djforms.DateInput(attrs={'type': 'date'}),
        help_text="Used as the resume date on every letter.")
    principal_name = djforms.CharField(
        label="Principal name", max_length=255, required=False,
        help_text="Shown above the 'Principal' signature title.")

    class Meta:
        model = LetterTemplate
        fields = [
            'letterhead_school_line',
            'deposit_amount_words', 'deposit_amount_display',
            'bank_name', 'bank_branch_hint', 'bank_account', 'bank_account_name',
            'acceptance_email_1', 'acceptance_email_2',
            'payment_window_days', 'acceptance_window_days',
            'intro_template', 'deposit_paragraph_template', 'notes_template',
            'extra_paragraph', 'closing_line', 'signature_title',
        ]
        widgets = {
            'intro_template':           djforms.Textarea(attrs={'rows': 4}),
            'deposit_paragraph_template': djforms.Textarea(attrs={'rows': 6}),
            'notes_template':           djforms.Textarea(attrs={'rows': 10}),
            'extra_paragraph':          djforms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school:
            self.fields['school_display_name'].initial = (
                school.name or school.school_name or '')
            self.fields['school_motto'].initial = school.school_motto or ''
            self.fields['school_address'].initial = school.school_address or ''
            self.fields['school_next_term_date'].initial = school.next_term_date
            self.fields['principal_name'].initial = school.principal_name or ''

    def save(self, commit=True):
        tpl = super().save(commit=commit)
        if self.school:
            self.school.name = self.cleaned_data['school_display_name']
            self.school.school_motto = self.cleaned_data['school_motto']
            self.school.school_address = self.cleaned_data['school_address']
            self.school.next_term_date = self.cleaned_data['school_next_term_date']
            self.school.principal_name = self.cleaned_data['principal_name']
            self.school.save()
        return tpl





@staff_required
def edit_letter_template(request):
    sch, resume = _issuing_school_and_resume(request)
    if not sch:
        messages.error(request, "No school found for this domain.")
        return redirect('student:admission_letters_list')
    
    tpl, _ = LetterTemplate.objects.get_or_create(school=sch)
    # rest unchanged

    if request.method == 'POST':
        form = LetterTemplateForm(request.POST, instance=tpl, school=sch)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Template saved. New letters will use these values. "
                "Existing letters update the next time they're regenerated.")
            form = LetterTemplateForm(instance=tpl, school=sch)
    else:
        form = LetterTemplateForm(instance=tpl, school=sch)

    ctx = {
        'title': f'Letter Template — {sch.school_name}',
        'form': form,
        'school': sch,
        'template': tpl,
    }
    return render(request, 'student/admission_letters/template_edit.html', ctx)


from django import forms as djforms
from .models import LetterTemplate


class LetterTemplateForm(djforms.ModelForm):
    """Edits both School (letterhead-level) and LetterTemplate (body-level) constants."""

    school_display_name = djforms.CharField(
        label="School name (letterhead)", max_length=255,
        help_text="Shown in big text at the top of the PDF.")
    school_motto = djforms.CharField(label="Motto", max_length=255, required=False)
    school_address = djforms.CharField(
        label="Address", max_length=355, required=False,
        widget=djforms.Textarea(attrs={'rows': 1}))
    school_next_term_date = djforms.DateField(
        label="Resume date", required=False,
        widget=djforms.DateInput(attrs={'type': 'date'}),
        help_text="Used as 'the child resume for the session on …'")
    principal_name = djforms.CharField(
        label="Principal name", max_length=255, required=False)

    class Meta:
        model = LetterTemplate
        fields = [
            'letterhead_school_line',
            'deposit_amount_words', 'deposit_amount_display',
            'bank_name', 'bank_branch_hint', 'bank_account', 'bank_account_name',
            'acceptance_email_1', 'acceptance_email_2',
            'payment_window_days', 'acceptance_window_days',
            'intro_template', 'deposit_paragraph_template', 'notes_template',
            'extra_paragraph', 'closing_line', 'signature_title',
        ]
        widgets = {
            'intro_template':             djforms.Textarea(attrs={'rows': 5}),
            'deposit_paragraph_template': djforms.Textarea(attrs={'rows': 7}),
            'notes_template':             djforms.Textarea(attrs={'rows': 12}),
            'extra_paragraph':            djforms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

        # ── School-level fields ──────────────────────────────────────
        if school:
            self.fields['school_display_name'].initial = (
                school.name or school.school_name or '')
            self.fields['school_motto'].initial = school.school_motto or ''
            self.fields['school_address'].initial = school.school_address or ''
            self.fields['school_next_term_date'].initial = school.next_term_date
            self.fields['principal_name'].initial = school.principal_name or ''

        # ── Fallback defaults for the LetterTemplate fields ──────────
        from .services import admission_letter_config as cfg
        from .models import (
            DEFAULT_INTRO_TEMPLATE, DEFAULT_DEPOSIT_TEMPLATE,
            DEFAULT_NOTES_TEMPLATE, DEFAULT_CLOSING_LINE, DEFAULT_SIGNATURE_TITLE,
        )
        self.defaults = {
            'letterhead_school_line':      cfg.LETTERHEAD_SCHOOL_LINE,
            'deposit_amount_words':        cfg.DEPOSIT_AMOUNT_WORDS,
            'deposit_amount_display':      cfg.DEPOSIT_AMOUNT_DISPLAY,
            'bank_name':                   cfg.BANK_NAME,
            'bank_branch_hint':            cfg.BANK_BRANCH_HINT,
            'bank_account':                cfg.BANK_ACCOUNT,
            'bank_account_name':           cfg.BANK_ACCOUNT_NAME,
            'acceptance_email_1':          cfg.ACCEPTANCE_EMAIL_1,
            'acceptance_email_2':          cfg.ACCEPTANCE_EMAIL_2,
            'payment_window_days':         cfg.PAYMENT_WINDOW_DAYS,
            'acceptance_window_days':      cfg.ACCEPTANCE_WINDOW_DAYS,
            'intro_template':              DEFAULT_INTRO_TEMPLATE,
            'deposit_paragraph_template':  DEFAULT_DEPOSIT_TEMPLATE,
            'notes_template':              DEFAULT_NOTES_TEMPLATE,
            'extra_paragraph':             '',
            'closing_line':                DEFAULT_CLOSING_LINE,
            'signature_title':             DEFAULT_SIGNATURE_TITLE,
        }

        # ── Which fields are currently falling back to default? ──────
        self.blank_fields = {}
        if self.instance and self.instance.pk:
            for name in self.defaults:
                if name in self.fields:
                    current = getattr(self.instance, name, None)
                    self.blank_fields[name] = current in (None, '', 0)

        # ── Pre-fill blanks with the effective value ─────────────────
        # ── Pre-fill blanks with the effective value ─────────────────
        # Set on self.initial (not field.initial) — Django's BoundField
        # prefers form-level initial over field-level, and ModelForm
        # already put the empty DB value into self.initial.
        if not self.is_bound:
            for name, default in self.defaults.items():
                if name not in self.fields:
                    continue
                current = getattr(self.instance, name, None) if self.instance.pk else None
                if current in (None, '', 0):
                    self.initial[name] = default

    def save(self, commit=True):
        tpl = super().save(commit=commit)
        if self.school:
            self.school.name = self.cleaned_data['school_display_name']
            self.school.school_motto = self.cleaned_data['school_motto']
            self.school.school_address = self.cleaned_data['school_address']
            self.school.next_term_date = self.cleaned_data['school_next_term_date']
            self.school.principal_name = self.cleaned_data['principal_name']
            self.school.save()
        return tpl
    


@staff_required
def edit_letter_template(request):
    """Edit the shared constants that apply to every letter for the issuing school."""
    sch, resume = _issuing_school_and_resume(request)
    if not sch:
        messages.error(request, f"School '{LETTER_ISSUING_SCHOOL}' not found.")
        return redirect('student:admission_letters_list')

    tpl, _ = LetterTemplate.objects.get_or_create(school=sch)

    if request.method == 'POST':
        form = LetterTemplateForm(request.POST, instance=tpl, school=sch)
        if form.is_valid():
            form.save()
            messages.success(request, "Template saved. Existing letters update on next regeneration.")

            # Optional: regenerate every existing letter right now
            if request.POST.get('regenerate_all') == '1':
                passed, _, _ = find_candidates(school=sch, session_name=tpl.session_name)
                ok, failed_regen = 0, 0
                for profile, class_key, avg, scores, thr in passed:
                    try:
                        _build_or_get_letter(profile, class_key, avg, scores, thr,
                                             sch, resume, force=True)
                        ok += 1
                    except Exception as e:
                        failed_regen += 1
                        messages.warning(request, f"Could not regenerate {profile}: {e}")
                if ok:
                    messages.success(request, f"Regenerated {ok} existing letter(s).")
                if failed_regen:
                    messages.warning(request, f"{failed_regen} letter(s) failed to regenerate.")

            form = LetterTemplateForm(instance=tpl, school=sch)
    else:
        form = LetterTemplateForm(instance=tpl, school=sch)

    ctx = {
        'title': f'Letter Template — {sch.school_name}',
        'form': form,
        'school': sch,
        'template': tpl,
        'blank_fields': form.blank_fields,
    }
    return render(request, 'student/dashboard/template_edit.html', ctx)



def _resolve_template_text(text, profile, letter, sch, resume):
    """Substitute {placeholders} with this student's actual values."""
    from .services.admission_letter import _SafeDict, _fmt_date
    from .services import admission_letter_config as cfg
    if not text:
        return text

    if letter.override_student_name:
        student_name = letter.override_student_name
    else:
        user = getattr(profile, 'user', None)
        student_name = ((f"{user.first_name or ''} {user.last_name or ''}").strip()
                        or user.display_name) if user else str(profile)

    letter_date = (letter.letter_date
                   or (letter.generated_at.date() if letter.generated_at else date.today()))
    payment_deadline = letter.payment_deadline or (
        letter_date + timedelta(days=cfg.PAYMENT_WINDOW_DAYS))
    acceptance_deadline = letter.acceptance_deadline or (
        payment_deadline + timedelta(days=cfg.ACCEPTANCE_WINDOW_DAYS))

    tpl = _get_letter_template(sch)
    if tpl:
        deposit_words     = tpl.get_deposit_words()
        deposit_display   = tpl.get_deposit_display()
        bank_name         = tpl.get_bank_name()
        bank_branch_hint  = tpl.get_bank_branch_hint()
        bank_account      = tpl.get_bank_account()
        bank_account_name = tpl.get_bank_account_name()
        accept_email_1    = tpl.get_acceptance_email_1()
        accept_email_2    = tpl.get_acceptance_email_2()
        letterhead_line   = tpl.get_letterhead_school_line()
    else:
        deposit_words     = cfg.DEPOSIT_AMOUNT_WORDS
        deposit_display   = cfg.DEPOSIT_AMOUNT_DISPLAY
        bank_name         = cfg.BANK_NAME
        bank_branch_hint  = cfg.BANK_BRANCH_HINT
        bank_account      = cfg.BANK_ACCOUNT
        bank_account_name = cfg.BANK_ACCOUNT_NAME
        accept_email_1    = cfg.ACCEPTANCE_EMAIL_1
        accept_email_2    = cfg.ACCEPTANCE_EMAIL_2
        letterhead_line   = cfg.LETTERHEAD_SCHOOL_LINE

    if letter.override_deposit_words:
        deposit_words = letter.override_deposit_words
    if letter.override_deposit_display:
        deposit_display = letter.override_deposit_display

    fill_ctx = dict(
        student_name=student_name,
        letterhead=letterhead_line,
        class_label=letter.class_offered or '',
        session_name=cfg.SESSION_NAME,
        deposit_words=deposit_words,
        deposit_display=deposit_display,
        bank_name=bank_name,
        bank_branch_hint=bank_branch_hint,
        bank_account=bank_account,
        bank_account_name=bank_account_name,
        payment_deadline=_fmt_date(payment_deadline),
        acceptance_deadline=_fmt_date(acceptance_deadline),
        resume_date=_fmt_date(resume),
        acceptance_email_1=accept_email_1,
        acceptance_email_2=accept_email_2,
    )
    try:
        return text.format_map(_SafeDict(**fill_ctx))
    except Exception:
        return text

    