"""Shared logic: find entrance-exam passers. Used by admin + management command."""
import re
from decimal import Decimal

from student.models import AdmissionLetter, LetterTemplate, Result

from users.models import Profile
from .admission_letter_config import (
    SESSION_NAME, ENTRANCE_EXAM_SCHOOL, PASS_THRESHOLD,
)

CLASS_PATTERNS = [
    (re.compile(r'\bJSS?\s*1\b', re.I), 'JSS1'),
    (re.compile(r'\bJSS?\s*2\b', re.I), 'JSS2'),
    (re.compile(r'\bJSS?\s*3\b', re.I), 'JSS3'),
    (re.compile(r'\bSS\s*1\b',    re.I), 'SS1'),
    (re.compile(r'\bSS\s*2\b',    re.I), 'SS2'),
]
SUBJECT_PATTERNS = {
    'math':          re.compile(r'\b(MATH|MATHEMATIC)', re.I),
    'english':       re.compile(r'\bENGLISH\b', re.I),
    'basic_science': re.compile(r'\b(SCIENCE|BASIC\s*SCI)', re.I),
}


def detect_class(title):
    for pat, key in CLASS_PATTERNS:
        if pat.search(title):
            return key
    return None


def classify_subject(title):
    for kind, pat in SUBJECT_PATTERNS.items():
        if pat.search(title):
            return kind
    return None


def _student_in_school(profile, sch):
    from quiz.models import Result
    if AdmissionLetter.objects.filter(student=profile, school=sch).exists():
        return True
    return Result.objects.filter(student=profile, schools=sch).exists()


def _resolve_session(session_name):
    from sms.models import Session
    for field in ('name', 'title', 'session_name', 'session', 'label', 'session_title'):
        try:
            return Session.objects.get(**{field: session_name})
        except Exception:
            continue
    return None


def find_candidates(school, session_name, classes=None, student_id=None):
    """Returns (passed, failed, missing).

    passed  = [(profile, class_key, avg, {subject: {...}}, threshold), ...]
    failed  = [(profile, class_key, avg, threshold, {subject: {...}}), ...]
    missing = [(profile, class_key, [missing subject names]), ...]
    """
    session_obj = _resolve_session(session_name)
    if session_obj is None:
        return [], [], []

    qs = (Result.objects
          .filter(schools=school, exam__session=session_obj)
          .select_related('student', 'exam', 'exam__course_name')
          .order_by('-created'))          # newest first, so the newest result wins below

    if student_id:
        qs = qs.filter(student_id=student_id)

    by_student = {}
    for r in qs:
        ck = detect_class(r.exam.course_name.title)
        if ck is None:
            continue
        by_student.setdefault(r.student_id, {}).setdefault(ck, []).append(r)

    tpl = LetterTemplate.objects.filter(school=school).first()
    thresholds = (tpl.pass_thresholds if tpl else None) or {}

    profiles = Profile.objects.select_related('user').in_bulk(by_student.keys())

    passed, failed, missing = [], [], []

    for sid, by_class in by_student.items():
        profile = profiles.get(sid)
        if profile is None:
            continue

        for class_key, rows in by_class.items():
            if classes and class_key not in classes:
                continue

            # One result per subject: the newest one (rows are already newest first)
            picked = {}
            for r in rows:
                key = classify_subject(r.exam.course_name.title) or r.exam.course_name.title.lower()
                if key not in picked:
                    picked[key] = r

            if class_key in ('JSS1', 'JSS2', 'JSS3'):
                need = {'math', 'english', 'basic_science'}
                if not need.issubset(picked):
                    missing.append((profile, class_key, sorted(need - set(picked))))
                    continue

            scores = {}
            for key, r in picked.items():
                total = r.exam.total_marks or 100
                pct = (Decimal(str(r.marks)) / Decimal(str(total)) * 100).quantize(Decimal('0.01'))
                scores[key] = {'marks': r.marks, 'total': total, 'pct': pct}

            if not scores:
                missing.append((profile, class_key, ['all']))
                continue

            pcts = [v['pct'] for v in scores.values()]
            avg = (sum(pcts) / Decimal(len(pcts))).quantize(Decimal('0.01'))
            thr = Decimal(str(thresholds.get(class_key, PASS_THRESHOLD.get(class_key, 50))))

            if avg < thr:
                failed.append((profile, class_key, avg, thr, scores))
            else:
                passed.append((profile, class_key, avg, scores, thr))

    return passed, failed, missing