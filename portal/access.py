from .models import (
    ReportCardAccess, ReportCardRelease, SchoolSubscription,
)


def get_release(school, session, term, student_class):
    if school is None:
        return None
    qs = ReportCardRelease.objects.filter(school=school, session=session, term=term)
    specific = qs.filter(student_class=student_class).first()
    return specific or qs.filter(student_class='').first()


def can_view_report_card(student, session, term):
    """
    Precedence:
      1. School subscription must be active for report cards.
      2. Individual unlock  -> always wins.
      3. Class / school-wide release.
    """
    school = getattr(student, 'school', None)

    # 1. School must have paid for the report card module
    sub = getattr(school, 'subscription', None)
    if sub is None or not sub.is_report_card_valid():
        return False, 'Your school\'s report card service is currently inactive.'

    # 2. Individual unlock
    access = ReportCardAccess.objects.filter(
        student=student, session=session, term=term
    ).first()
    if access and access.is_unlocked:
        return True, access.get_reason_display()

    # 3. Bulk release
    release = get_release(school, session, term, student.student_class)
    if release and release.is_released:
        return True, release.note or 'Released by the school'

    return False, 'Report card for this term has not been released yet.'