from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from sms.models import Session, Term
from users.models import NewUser
from .access import get_release
from .models import ReportCardAccess, ReportCardRelease


def is_examiner(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.is_staff
        or getattr(user, 'is_principal', False)
    )


examiner_required = user_passes_test(is_examiner, login_url='/login/')


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@login_required
@examiner_required
def report_card_control(request):
    school = request.user.school

    sessions = Session.objects.filter(school=school).order_by('-id') if school else Session.objects.none()
    terms    = Term.objects.all().order_by('id')

    session_id = request.GET.get('session') or (sessions.first().pk if sessions.exists() else None)
    term_id    = request.GET.get('term')    or (terms.first().pk    if terms.exists()    else None)
    sel_class  = request.GET.get('class', '')

    session = Session.objects.filter(pk=session_id).first()
    term    = Term.objects.filter(pk=term_id).first()

    # Classes offered by this school
    classes = list(
        NewUser.objects
        .filter(school=school, is_staff=False)
        .exclude(student_class__isnull=True).exclude(student_class='')
        .values_list('student_class', flat=True)
        .distinct().order_by('student_class')
    )

    # Subscription gate — examiner cannot release if school hasn't paid
    sub = getattr(school, 'subscription', None) if school else None
    sub_ok = bool(sub and sub.is_report_card_valid())
    sub_reason = ''
    if not sub_ok:
        sub_reason = (
            'Report card service is inactive for this school. '
            'Renew the subscription before releasing cards.'
        )

    class_rows = []
    if school and session and term:
        school_release = get_release(school, session, term, '')
        class_rows.append({
            'label': 'ALL CLASSES',
            'value': '',
            'release': school_release,
            'is_open': bool(school_release and school_release.is_released),
            'count': NewUser.objects.filter(school=school, is_staff=False).count(),
        })
        for c in classes:
            rel = get_release(school, session, term, c)
            class_rows.append({
                'label': c,
                'value': c,
                'release': rel,
                'is_open': bool(rel and rel.is_released),
                'count': NewUser.objects.filter(
                    school=school, student_class=c, is_staff=False
                ).count(),
            })

    # Students of the selected class
    students = []
    if school and session and term and sel_class:
        qs = (NewUser.objects
              .filter(school=school, student_class=sel_class, is_staff=False)
              .order_by('last_name', 'first_name'))
        access_map = {
            a.student_id: a
            for a in ReportCardAccess.objects.filter(
                student__in=qs, session=session, term=term
            )
        }
        class_release = get_release(school, session, term, sel_class)
        class_open = bool(class_release and class_release.is_released)

        for s in qs:
            a = access_map.get(s.pk)
            students.append({
                'obj': s,
                'access': a,
                'individually_open': bool(a and a.is_unlocked),
                'class_open': class_open,
                'is_open': bool(a and a.is_unlocked) or class_open,
            })

    return render(request, 'portal/examiner/report_card_control.html', {
        'sessions': sessions, 'terms': terms,
        'session': session, 'term': term,
        'class_rows': class_rows,
        'students': students,
        'sel_class': sel_class,
        'sub_ok': sub_ok,
        'sub_reason': sub_reason,
    })


# --------------------------------------------------------------------------
# Bulk toggle
# --------------------------------------------------------------------------
@require_POST
@login_required
@examiner_required
def toggle_class_release(request):
    school  = request.user.school
    session = get_object_or_404(Session, pk=request.POST['session'])
    term    = get_object_or_404(Term, pk=request.POST['term'])
    student_class = request.POST.get('student_class', '')
    open_it = request.POST.get('state') == 'open'

    # Subscription gate
    sub = getattr(school, 'subscription', None)
    if open_it and (sub is None or not sub.is_report_card_valid()):
        messages.error(request, 'Cannot release: report card subscription is inactive.')
        return redirect(
            f"{request.POST.get('next', '/portal/examiner/report-cards/')}"
            f"?session={session.pk}&term={term.pk}&class={student_class}"
        )

    release, _ = ReportCardRelease.objects.get_or_create(
        school=school, session=session, term=term, student_class=student_class,
        defaults={'released_by': request.user},
    )
    release.is_released = open_it
    release.released_by = request.user
    release.save()

    label = student_class or 'ALL CLASSES'
    messages.success(
        request,
        f"Report cards for {label} — {session} {term} "
        f"{'RELEASED' if open_it else 'LOCKED'}."
    )
    return redirect(
        f"{request.POST.get('next', '/portal/examiner/report-cards/')}"
        f"?session={session.pk}&term={term.pk}&class={student_class}"
    )


# --------------------------------------------------------------------------
# One-by-one toggle
# --------------------------------------------------------------------------
@require_POST
@login_required
@examiner_required
def toggle_student_access(request):
    student = get_object_or_404(
        NewUser, pk=request.POST['student_id'], school=request.user.school
    )
    session = get_object_or_404(Session, pk=request.POST['session'])
    term    = get_object_or_404(Term, pk=request.POST['term'])
    open_it = request.POST.get('state') == 'open'

    if open_it:
        sub = getattr(request.user.school, 'subscription', None)
        if sub is None or not sub.is_report_card_valid():
            messages.error(request, 'Cannot unlock: report card subscription is inactive.')
            return redirect(
                f"{request.POST.get('next', '/portal/examiner/report-cards/')}"
                f"?session={session.pk}&term={term.pk}&class={student.student_class}"
            )

    access, _ = ReportCardAccess.objects.get_or_create(
        student=student, session=session, term=term
    )
    access.is_unlocked = open_it
    access.reason = request.POST.get('reason', 'paid' if open_it else 'manual')
    access.unlocked_by = request.user
    access.unlocked_at = timezone.now() if open_it else None
    access.save()

    messages.success(
        request,
        f"{student.display_name} — report card "
        f"{'UNLOCKED' if open_it else 'LOCKED'} for {session} {term}."
    )
    return redirect(
        f"{request.POST.get('next', '/portal/examiner/report-cards/')}"
        f"?session={session.pk}&term={term.pk}&class={student.student_class}"
    )