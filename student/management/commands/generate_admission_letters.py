import re
from datetime import date
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from quiz.models import School
from users.models import Profile
from student.models import Result, AdmissionLetter
from student.services.admission_letter import generate_admission_letter_pdf
from student.services.admission_letter_config import (
    SESSION_NAME, ENTRANCE_EXAM_SCHOOL, LETTER_ISSUING_SCHOOL,
    PASS_THRESHOLD, CLASS_LABELS, DEFAULT_RESUME_DATE,
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


class Command(BaseCommand):
    help = "Generate conditional admission letters for students who passed entrance exams."

    def add_arguments(self, parser):
        parser.add_argument('--school', default=LETTER_ISSUING_SCHOOL)
        parser.add_argument('--classes', nargs='*')
        parser.add_argument('--session', default=SESSION_NAME)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--student-id', type=int)

    def _resolve_session(self, session_name):
        """Find the Session row regardless of what the name field is called."""
        try:
            from sms.models import Session
        except ImportError:
            return None
        for field in ('name', 'title', 'session_name', 'session', 'label', 'session_title'):
            try:
                return Session.objects.get(**{field: session_name})
            except Exception:
                continue
        return None

    def handle(self, *args, **o):
        dry = o['dry_run']

        session_obj = self._resolve_session(o['session'])
        if session_obj is None:
            self.stderr.write(
                f"[ERROR] Session '{o['session']}' not found. "
                f"Check SESSION_NAME in admission_letter_config.py, or the "
                f"field names on sms.Session."
            )
            return

        try:
            issuing_school = School.objects.get(school_name=o['school'])
        except School.DoesNotExist:
            self.stderr.write(f"[ERROR] School '{o['school']}' not found.")
            return

        resume = issuing_school.next_term_date or date(*DEFAULT_RESUME_DATE)

        qs = (Result.objects
              .filter(exam__schools__school_name=ENTRANCE_EXAM_SCHOOL,
                      exam__session=session_obj)
              .select_related('student', 'exam', 'exam__course_name'))

        if o['student_id']:
            qs = qs.filter(student_id=o['student_id'])

        by_student = {}
        for r in qs:
            ck = detect_class(r.exam.course_name.title)
            if ck is None:
                continue
            by_student.setdefault(r.student_id, {}).setdefault(ck, []).append(r)

        passed, failed, missing = [], [], []

        for sid, by_class in by_student.items():
            try:
                profile = Profile.objects.select_related('user').get(id=sid)
            except Profile.DoesNotExist:
                continue

            for class_key, rows in by_class.items():
                if o['classes'] and class_key not in o['classes']:
                    continue

                if class_key in ('JSS1', 'JSS2', 'JSS3'):
                    picked = {}
                    for r in rows:
                        kind = classify_subject(r.exam.course_name.title)
                        if kind and kind not in picked:
                            picked[kind] = r
                    need = {'math', 'english', 'basic_science'}
                    if not need.issubset(picked):
                        missing.append((profile, class_key, sorted(need - set(picked.keys()))))
                        continue
                    rows = list(picked.values())

                scores = {}
                for r in rows:
                    total = r.exam.total_marks or 100
                    if not total:
                        continue
                    pct = (Decimal(r.marks) / Decimal(total) * 100).quantize(Decimal('0.01'))
                    key = classify_subject(r.exam.course_name.title) or r.exam.course_name.title.lower()
                    scores[key] = pct

                if not scores:
                    missing.append((profile, class_key, ['all']))
                    continue

                avg = (sum(scores.values()) / Decimal(len(scores))).quantize(Decimal('0.01'))
                thr = Decimal(PASS_THRESHOLD[class_key])

                if avg < thr:
                    failed.append((profile, class_key, avg, thr))
                else:
                    passed.append((profile, class_key, avg, scores, thr))

        self.stdout.write("\n=== SUMMARY ===")
        self.stdout.write(f"Passed:  {len(passed)}")
        self.stdout.write(f"Failed:  {len(failed)}")
        self.stdout.write(f"Missing: {len(missing)}\n")

        if missing:
            self.stdout.write("⚠ MANUAL REVIEW (missing subject result):")
            for p, c, subs in missing:
                self.stdout.write(f"  - id={p.id} {p} [{c}] missing {subs}")
        if failed:
            self.stdout.write("\n✗ FAILED:")
            for p, c, avg, thr in failed:
                self.stdout.write(f"  - id={p.id} {p} [{c}] avg={avg} < {thr}")

        if dry:
            self.stdout.write("\n[dry-run] No PDFs generated.\n")
            return

        for profile, class_key, avg, scores, thr in passed:
            if not (profile.guardian_name and profile.guardian_address):
                self.stdout.write(f"[skip] {profile} has no guardian name/address")
                continue

            user = getattr(profile, 'user', None)
            if user:
                student_name = (f"{user.first_name or ''} {user.last_name or ''}").strip() \
                               or user.display_name
            else:
                student_name = str(profile)

            letter, created = AdmissionLetter.objects.get_or_create(
                student=profile, session=session_obj,
                defaults={
                    'school': issuing_school,
                    'class_offered': CLASS_LABELS[class_key],
                    'subject_scores': {k: str(v) for k, v in scores.items()},
                    'average_score': avg,
                    'pass_threshold': thr,
                    'resume_date': resume,
                })

            if not created and letter.pdf_file:
                self.stdout.write(f"[skip] {profile} already has a letter")
                continue

            buf = generate_admission_letter_pdf(
                student_name=student_name,
                class_offered=class_key,
                guardian_title=profile.guardian_title or '',
                guardian_name=profile.guardian_name or '',
                guardian_address=profile.guardian_address or '',
                school=issuing_school,
                resume_date=resume,
            )
            letter.pdf_file.save(
                f"admission_{profile.id}_{class_key}.pdf",
                ContentFile(buf.read()), save=True)
            self.stdout.write(f"[ok] {profile} → {letter.pdf_file.name}")

        self.stdout.write("\nDone.\n")