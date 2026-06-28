# quiz/tasks.py
from aiohttp import request
from celery import shared_task, current_task
from openai import OpenAI
from django.conf import settings
from quiz.models import Course, GenerationJob, Question, Result, StudentExamSession
from sms.models import Courses
import re
import math
import time
from django.core.cache import cache
from django.db import transaction, IntegrityError
from student.models import ExamAttempt
from users.models import Profile
from datetime import timedelta, timezone

import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db import IntegrityError
from .models import (
    Course, Profile, Result, Question
)
from student.models import ExamAttempt, ExamEventLog
from django.utils import timezone
from student.models import ExamAttempt

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# print("OPENAI_API_KEY:",settings.OPENAI_API_KEY)  # Debug print to verify the key is loaded

import django.utils.timezone as dj_timezone  # ✅ Use fully qualified name

from celery import shared_task
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from quiz.models import StudentExamSession

  
def parse_ai_output(output):
    """Parse AI text into list of question dicts (question, option1..4, answer)"""
    blocks = re.split(r'\n\s*\n', output.strip())
    parsed = []
    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if len(lines) >= 6:  # tolerant parsing (in case extra blank lines)
            q = lines[0].replace("Question:", "").strip()
            # attempt to extract next 4 as options
            opts = []
            for ln in lines[1:5]:
                # safe split by "A. " or "A. " style
                if '. ' in ln:
                    _, rest = ln.split('. ', 1)
                else:
                    rest = ln
                opts.append(rest.strip())
            answer_letter = lines[5].split(':')[-1].strip().upper()
            mapping = {'A': 'Option1', 'B': 'Option2', 'C': 'Option3', 'D': 'Option4'}
            answer_idx = {'A': 0, 'B': 1, 'C': 2, 'D': 3}.get(answer_letter, 0)
            parsed.append({
                "question": q,
                "option1": opts[0] if len(opts) > 0 else "",
                "option2": opts[1] if len(opts) > 1 else "",
                "option3": opts[2] if len(opts) > 2 else "",
                "option4": opts[3] if len(opts) > 3 else "",
                "answer_letter": answer_letter,
                "answer": ['Option1','Option2','Option3','Option4'][answer_idx]
            })
    return parsed


import unicodedata
import re


import re
import math
import time
import unicodedata

from celery import shared_task
from .models import GenerationJob, Course


@shared_task(bind=True, max_retries=3, default_retry_delay=5, queue='esteemcbt')
def generate_ai_questions_task(
    self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
):
    """
    Celery task to generate AI questions for a school-specific course
    Guaranteed to return EXACTLY num_questions unique questions
    """
    job = GenerationJob.objects.get(job_id=job_id)
    job.status = "processing"
    job.save()

    try:
        # ── Fetch course ──────────────────────────────────────────────────
        course_obj = Course.objects.filter(id=course_id).first()
        if not course_obj:
            raise self.retry(exc=ValueError(f"Course {course_id} not found"))

        # ── Fetch global course title ─────────────────────────────────────
        global_course = course_obj.course_name
        course_title_raw = global_course.title if global_course else ""
        print("RAW course title:", repr(course_title_raw))

        # ── Clean title for keyword detection ─────────────────────────────
        def clean_course_title_letters(title):
            title = unicodedata.normalize("NFKC", title or "")
            title = re.sub(r'[^a-zA-Z]', '', title)
            return title.lower()

        course_title_clean = clean_course_title_letters(course_title_raw)
        print("CLEANED course title:", repr(course_title_clean))

        # ── Save learning objectives ──────────────────────────────────────
        course_obj.learning_objectives = learning_objectives
        course_obj.save()

        # ── Subject detection ─────────────────────────────────────────────
        is_math     = any(k in course_title_clean for k in ["math", "mathematics", "maths"])
        is_physics  = any(k in course_title_clean for k in ["physics", "physic", "phy"])
        is_chemistry= any(k in course_title_clean for k in ["chemistry", "chem"])

        print("IS MATH:", is_math)
        print("IS PHYSICS:", is_physics)
        print("IS CHEMISTRY:", is_chemistry)

        # ── Subject-specific prompt instructions ──────────────────────────
        math_instruction = ""
        physics_instruction = ""
        chem_instruction = ""

        if is_math:
            math_instruction = """
                Format ALL mathematical expressions using plain Unicode characters only.
                No markup. No tags. No LaTeX. No MathML. Just text and Unicode symbols.

                ═══════════════════════════════════════════════════
                ABSOLUTE FORBIDDEN — never output any of these:
                ^ (caret for exponents)          BAD: x^2
                LaTeX syntax                     BAD: \\frac{3}{4}, $x^2$, \\sqrt{x}
                MathML tags                      BAD: <math>, <mfrac>, <msup>, <mn>, <mi>
                HTML math tags                   BAD: <sup>, <sub>
                Any angle brackets for math      BAD: <anything>
                If you are about to type any of the above — STOP and use Unicode instead.
                ═══════════════════════════════════════════════════

                EXPONENTS — use Unicode superscript characters:
                x²  x³  xⁿ  x²⁺¹
                Superscript digits/symbols: ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁺ ⁻ ⁼ ⁽ ⁾ ⁿ

                SUBSCRIPTS — use Unicode subscript characters:
                x₁  x₂  aₙ  H₂O  CO₂
                Subscript digits/symbols: ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉ ₊ ₋ ₌ ₍ ₎

                FRACTIONS — use Unicode fraction symbols:
                ½  ⅓  ⅔  ¼  ¾  ⅕  ⅖  ⅗  ⅘  ⅙  ⅚  ⅛  ⅜  ⅝  ⅞
                For any other fraction write: (numerator)/(denominator)

                ROOTS:
                √x  ∛x  ∜x  √(x + 1)

                OPERATORS:
                ×  ÷  ±  ≠  ≈  ≤  ≥  π  ∞  ∑  ∫  ∈  ∝

                EXAMPLES:
                x² - 6x + 8 = 0
                x = (-b ± √(b² - 4ac)) / (2a)
                f(x) = x² + (1)/(x-1) + √(x + 3)

                OUTPUT CHECKLIST:
                ✓ No ^ anywhere
                ✓ No backslashes
                ✓ No < or > characters used for math
                ✓ No <math>, <mfrac>, <msup> or any XML/HTML tags
                ✓ Exponents use ⁰¹²³⁴⁵⁶⁷⁸⁹ superscript digits
                ✓ Fractions use ½⅓¼¾ or (a)/(b) form
                ✓ Roots use √ ∛ ∜
            """

        if is_physics:
            physics_instruction = """
                PHYSICS FORMATTING RULES:
                - Prefer inline equations.
                - Use standard physics formulas: v = u + at, s = ut + ½at², v² = u² + 2as.
                - Use Unicode superscripts/subscripts only (e.g., ², ³, H₂).
                - NO LaTeX. NO ^ symbol. Use MathML ONLY if absolutely necessary.
                - Options must be physically realistic and correct.
            """

        if is_chemistry:
            chem_instruction = """
                CHEMISTRY FORMATTING RULES:
                - Use plain text.
                - Chemical formulas: H2O, NaCl, CO2.
                - DO NOT use MathML.
            """
        #hh
        # ── Batch settings ────────────────────────────────────────────────
        BATCH_SIZE      = 10
        total_questions = int(num_questions)
        all_questions   = []

        # Normalizer for dedup
        def normalize(q):
            return re.sub(r'\s+', ' ', q.lower().strip())

        seen          = set()
        stale_retries = 0     # consecutive batches that added 0 new questions
        MAX_STALE     = 3     # stop if 3 batches in a row add nothing
        attempt       = 0

        # ── Keep looping until we have EXACTLY total_questions ────────────
        while len(all_questions) < total_questions:
            attempt += 1

            remaining   = total_questions - len(all_questions)
            batch_count = min(BATCH_SIZE, remaining)

            # ── Build previous questions context from latest collected ─────
            # Updated INSIDE loop so each batch avoids what was already made
            previous_questions_text = "\n".join(
                [q["question"] for q in all_questions[-30:]]
            )

            # ── Build prompt ──────────────────────────────────────────────
            prompt = f"""
You are a professional assessment specialist.

Generate EXACTLY {batch_count} multiple-choice questions strictly based on the learning objectives below.
No more, no less — return EXACTLY {batch_count} questions.

Course: {course_title_raw}

Learning Objectives:
{learning_objectives}

{math_instruction}
{physics_instruction}
{chem_instruction}

Difficulty Level: {difficulty}

Rules:
- Questions must strictly match the learning objectives
- Be clear and unambiguous
- Each question MUST have exactly four options (A–D)
- ONLY ONE correct answer per question

Return ONLY text in this EXACT format (repeat exactly {batch_count} times):

Question: <question text>
A. <option>
B. <option>
C. <option>
D. <option>
Answer: <A|B|C|D>

Avoid repeating or rephrasing any of these already-generated questions:
{previous_questions_text}

CRITICAL RULES — NO DUPLICATION:
- Do NOT repeat any question
- Do NOT rephrase an existing question
- Each question must test a DIFFERENT concept or variation
- Avoid same numbers, same structure, or same wording
- If a similar idea is used, change context, values, and structure completely

DIVERSITY REQUIREMENTS — include a mix of:
  • Conceptual questions
  • Word problems
  • Application-based questions
  • Direct computation
Do NOT generate only numeric variations of the same problem.
"""

            # ── Call AI API ───────────────────────────────────────────────
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You generate curriculum-aligned exam questions with extreme formatting accuracy. Always return EXACTLY the number of questions requested."
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2200,
                temperature=0.7,
            )

            output = resp.choices[0].message.content

            print("\n" + "=" * 80)
            print(f"BATCH {attempt + 1} | Requesting {batch_count} | Have {len(all_questions)}/{total_questions}")
            print(output)
            print("=" * 80 + "\n")

            parsed = parse_ai_output(output)

            print(f"Parsed {len(parsed)} questions from batch {attempt + 1}")

            # ── Dedup on the fly — only add truly new questions ───────────
            # ── Dedup on the fly — only add truly new questions ───────────
            added_this_batch = 0
            for q in parsed:
                if "question" not in q:
                    continue
                if len(all_questions) >= total_questions:
                    break  # hard stop — never exceed target

                key = normalize(q["question"])
                if key not in seen:
                    seen.add(key)
                    all_questions.append(q)
                    added_this_batch += 1

            print(f"Attempt {attempt} | Added {added_this_batch} | Total: {len(all_questions)}/{total_questions}")

            # ── Stale guard — stop if topic is exhausted ──────────────────
            if added_this_batch == 0:
                stale_retries += 1
                if stale_retries >= MAX_STALE:
                    print(f"WARNING: 3 consecutive batches added nothing. Stopping at {len(all_questions)}.")
                    break
            else:
                stale_retries = 0  # reset on any progress

            # ── Update job progress ───────────────────────────────────────
            job.result = {"partial_count": len(all_questions)}
            job.save()

            time.sleep(0.5)
            
        # ── Hard trim — guarantee exact count even if somehow over ────────
        all_questions = all_questions[:total_questions]

        print(f"\nFINAL count: {len(all_questions)} (requested: {total_questions})")

        # ── Final job update ──────────────────────────────────────────────
        job.result  = {"questions": all_questions}
        job.status  = "completed"
        job.save()

        return {"created": len(all_questions)}

    except Exception as exc:
        job.status = "failed"
        job.error  = str(exc)
        job.save()
        raise






def _mark_attempt_submitted(course_id, user_id):
    """
    Helper: close the active ExamAttempt for the given user and course.
    """
    

    ExamAttempt.objects.filter(
        student_id=user_id,      # ✅ user_id param, not request.user.id
        course_id=course_id,
        is_submitted=False,
    ).update(
        end_time=timezone.now(),
        is_submitted=True,
        remaining_seconds=0,  # ✅ reset to zero on submit
    )


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, countdown=5, queue='esteemcbt')
def grade_exam_task(self, course_id, user_id, answers_dict):
    try:
        course = Course.objects.select_related(
            'schools', 'session', 'term', 'exam_type'
        ).get(id=course_id)

        student = Profile.objects.select_related('user').get(user_id=user_id)

    except Course.DoesNotExist:
        return f"Course {course_id} not found."

    except Profile.DoesNotExist:
        return f"Student {user_id} profile not found."

    logger.info(
        f"Grading: user={user_id}, course={course_id}, "
        f"school={course.schools}, student_class={student.student_class}"
    )

    # Prevent duplicate results
    if Result.objects.filter(
        student=student,
        exam=course,
        session=course.session,
        term=course.term,
        exam_type=course.exam_type,
    ).exists():
        _mark_attempt_submitted(course_id, user_id)
        return f"Result for student {user_id} already exists."

    # Load questions
    questions = list(
        Question.objects.filter(course=course).only(
            'id',
            'answer',
            'marks'
        )
    )

    # Calculate score
    total_marks = 0

    for question in questions:
        selected = answers_dict.get(str(question.id))

        if selected and selected == question.answer:
            total_marks += question.marks or 0

    school_name = (
        course.schools.school_name
        if course.schools else "Unknown"
    )

    result_class = (
        student.student_class
        or f"Unassigned-{school_name}"
    )

    try:
        with transaction.atomic():
            Result.objects.create(
                schools=course.schools,
                marks=total_marks,
                exam=course,
                session=course.session,
                term=course.term,
                exam_type=course.exam_type,
                student=student,
                result_class=result_class,
            )

            _mark_attempt_submitted(course_id, user_id)

            ExamEventLog.objects.create(
                student_id=user_id,
                course=course,
                event_type="exam_submitted",
                details={
                    "submission_reason": answers_dict.get(
                        "submissionReason",
                        "manual",
                    )
                },
            )

        # Clear any related caches
        cache.delete(f"user_exam_data:{user_id}")
        cache.delete(f"user_results:{user_id}")
        cache.delete(f"take_exams:{user_id}")  # Safe even if unused

        return (
            f"Graded exam for student {user_id}, "
            f"total marks: {total_marks}"
        )

    except IntegrityError as e:
        logger.error(
            f"IntegrityError for user {user_id}: {e}"
        )

        _mark_attempt_submitted(course_id, user_id)

        return (
            f"Duplicate result detected for "
            f"student {user_id}."
        )

    except Exception as e:
        logger.error(
            f"Exception grading user {user_id}: {e}"
        )

        raise self.retry(
            exc=e,
            countdown=5,
            max_retries=3,
        )
    
# @shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, countdown=5)
# def grade_exam_task(self, course_id, user_id, answers_dict):
#     cache_key = f"graded:{course_id}:{user_id}"

#     if cache.get(cache_key):
#         return f"Exam for user {user_id} already graded."

#     try:
#         course = Course.objects.select_related(
#             'schools', 'session', 'term', 'exam_type'
#         ).get(id=course_id)
#         student = Profile.objects.select_related('user').get(user_id=user_id)
#     except Course.DoesNotExist:
#         return f"Course {course_id} not found."
#     except Profile.DoesNotExist:
#         return f"Student {user_id} profile not found."

#     logger.info(
#         f"Grading: user={user_id}, course={course_id}, "
#         f"school={course.schools}, student_class={student.student_class}"
#     )

#     if Result.objects.filter(
#         student=student,
#         exam=course,
#         session=course.session,
#         term=course.term,
#         exam_type=course.exam_type,
#     ).exists():
#         _mark_attempt_submitted(course_id, user_id)
#         cache.set(cache_key, True, timeout=3600)
#         return f"Result for student {user_id} already exists."

#     questions = list(
#         Question.objects.filter(course=course).only('id', 'answer', 'marks')
#     )

#     total_marks = 0
#     for question in questions:
#         selected = answers_dict.get(str(question.id))
#         if selected and selected == question.answer:
#             total_marks += question.marks or 0

#     school_name  = course.schools.school_name if course.schools else 'Unknown'
#     result_class = student.student_class or f"Unassigned-{school_name}"

#     try:
#         with transaction.atomic():
#             Result.objects.create(
#                 schools=course.schools,
#                 marks=total_marks,
#                 exam=course,
#                 session=course.session,
#                 term=course.term,
#                 exam_type=course.exam_type,
#                 student=student,
#                 result_class=result_class,
#             )

#             _mark_attempt_submitted(course_id, user_id)  # ✅ uses user_id param

#             ExamEventLog.objects.create(
#                 student_id=user_id,   # ✅ user_id param, not request.user.id
#                 course=course,
#                 event_type='exam_submitted',
#                 details={'submission_reason': answers_dict.get('submissionReason', 'manual')}
#             )

#         cache.set(cache_key, True, timeout=3600)
#         cache.delete(f"user_exam_data:{user_id}")
#         cache.delete(f"user_results:{user_id}")

#         return f"Graded exam for student {user_id}, total marks: {total_marks}"

#     except IntegrityError as e:
#         logger.error(f"IntegrityError for user {user_id}: {e}")
#         _mark_attempt_submitted(course_id, user_id)
#         cache.set(cache_key, True, timeout=3600)
#         return f"Duplicate result detected for student {user_id}."
#     except Exception as e:
#         logger.error(f"Exception grading user {user_id}: {e}")
#         raise self.retry(exc=e, countdown=5, max_retries=3)
    
