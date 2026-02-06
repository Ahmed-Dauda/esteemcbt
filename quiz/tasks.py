# quiz/tasks.py
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
from users.models import Profile
from datetime import timedelta, timezone

client = OpenAI(api_key=settings.OPENAI_API_KEY)

import django.utils.timezone as dj_timezone  # ✅ Use fully qualified name

from celery import shared_task
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from quiz.models import StudentExamSession

# @shared_task
# def cleanup_old_exam_sessions():
#     cutoff = make_aware(datetime.utcnow() - timedelta(minutes=1))

#     deleted_count, _ = StudentExamSession.objects.filter(
#         created_at__lt=cutoff
#     ).delete()

#     return f"Deleted {deleted_count} old exam sessions"


  
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


# @shared_task(bind=True)
# def generate_ai_questions_task(
#     self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
# ):
#     print("\n🔥🔥🔥 CELERY TASK STARTED 🔥🔥🔥")
#     print("Job ID:", job_id)
#     print("Course ID:", course_id)
#     print("Num Questions:", num_questions)
#     print("Difficulty:", difficulty)
#     print("Learning Objectives:", learning_objectives)

#     # Debug OpenAI key
#     import os
#     openai_key = os.getenv("OPENAI_API_KEY")
#     print("OPENAI KEY PRESENT:", bool(openai_key))
#     if openai_key:
#         print("OPENAI KEY STARTS WITH:", openai_key[:10])  # just first 10 chars, don't print full key

#     job = GenerationJob.objects.get(job_id=job_id)
#     job.status = "processing"
#     job.save()

#     try:
#         # Fetch course object
#         course_obj = Courses.objects.get(id=course_id)
#         course_title = (course_obj.title or "").strip()

#         # Map to Course model and save learning objectives
#         course_detail = Course.objects.filter(course_name=course_obj).first()
#         if course_detail:
#             course_detail.learning_objectives = learning_objectives
#             course_detail.save()

#         # Batch settings
#         BATCH_SIZE = 10
#         total_questions = int(num_questions)
#         batches = math.ceil(total_questions / BATCH_SIZE)
#         all_questions = []

#         for b in range(batches):
#             batch_count = min(BATCH_SIZE, total_questions - (b * BATCH_SIZE))

#             prompt = f"""
# You are a professional assessment specialist.

# Generate {batch_count} multiple-choice questions strictly based on the learning objectives below:

# Course: {course_title}

# Learning Objectives:
# {learning_objectives}

# Difficulty Level: {difficulty}

# Each question MUST:
# - Match the learning objectives
# - Be clear and unambiguous
# - Have 4 options (A–D)
# - Include one correct answer only

# Return ONLY text in this strict format:

# Question: <question text>
# A. <option>
# B. <option>
# C. <option>
# D. <option>
# Answer: <A|B|C|D>
# """
#             print("Calling OpenAI API…")  # <-- log before call
#             resp = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You generate curriculum-aligned exam questions with high precision."
#                     },
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=1800,
#                 temperature=0,
#             )

#             output = resp.choices[0].message.content
#             print("RAW AI OUTPUT:\n", output)

#             parsed = parse_ai_output(output)
#             all_questions.extend(parsed)
#             print("Parsed questions batch:", parsed)

#             # Update job progress
#             job.result = {"partial_count": len(all_questions)}
#             job.save()
#             time.sleep(0.5)

#         # Final job update
#         job.result = {"questions": all_questions}
#         job.status = "completed"
#         job.save()

#         return {"created": len(all_questions)}

#     except Exception as exc:
#         print("🔥🔥🔥 TASK ERROR 🔥🔥🔥")
#         print(exc)
#         job.status = "failed"
#         job.error = str(exc)
#         job.save()
#         raise

import unicodedata
import re

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def generate_ai_questions_task(
    self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
):
    """
    Celery task to generate AI questions for a school-specific course.

    - course_id: ID of Course (school-specific)
    - Uses Course.course_name.title for the global course title
    """
    job = GenerationJob.objects.get(job_id=job_id)
    job.status = "processing"
    job.save()

    try:
        # ----------------------------
        # Fetch school-specific course
        # ----------------------------
        course_obj = Course.objects.filter(id=course_id).first()
        if not course_obj:
            exc = ValueError(f"Course {course_id} not found")
            raise self.retry(exc=exc)

        # ----------------------------
        # Fetch global course title
        # ----------------------------
        global_course = course_obj.course_name  # Courses instance
        course_title_raw = global_course.title if global_course else ""
        print("RAW course title:", repr(course_title_raw))

        # ----------------------------
        # Clean course title for keyword detection
        # ----------------------------
        def clean_course_title_letters(title):
            title = unicodedata.normalize("NFKC", title or "")
            title = re.sub(r'[^a-zA-Z]', '', title)
            return title.lower()

        course_title_clean = clean_course_title_letters(course_title_raw)
        print("CLEANED course title:", repr(course_title_clean))

        # ----------------------------
        # Save learning objectives to school-specific course
        # ----------------------------
        course_obj.learning_objectives = learning_objectives
        course_obj.save()

        # ----------------------------
        # Detect subjects
        # ----------------------------
        math_keywords = ["math", "mathematics", "maths"]
        physics_keywords = ["physics", "physic", "phy"]
        chem_keywords = ["chemistry", "chem"]

        is_math = any(k in course_title_clean for k in math_keywords)
        is_physics = any(k in course_title_clean for k in physics_keywords)
        is_chemistry = any(k in course_title_clean for k in chem_keywords)

        print("IS MATH:", is_math)
        print("IS PHYSICS:", is_physics)
        print("IS CHEMISTRY:", is_chemistry)

        # ----------------------------
        # Batch settings
        # ----------------------------
        BATCH_SIZE = 10
        total_questions = int(num_questions)
        batches = math.ceil(total_questions / BATCH_SIZE)
        all_questions = []

        for b in range(batches):
            batch_count = min(BATCH_SIZE, total_questions - (b * BATCH_SIZE))

            # ----------------------------
            # Subject-specific instructions
            # ----------------------------
            math_instruction = ""
            physics_instruction = ""
            chem_instruction = ""

            if is_math:
                math_instruction = """
            Make sure Both questions and options should be formatted as valid MathML format strictly. 
            - NO LaTeX
            - NO ^ symbol
            - Use MathML for all mathematical expressions
            - Use proper MathML tags for superscripts, subscripts, fractions, roots, etc
            """

            if is_physics:
                physics_instruction = """
           PHYSICS FORMATTING RULES:
            - Prefer INLINE equations.
            - Use standard physics formulas, e.g., v = u + at, s = ut + 1/2 at², v² = u² + 2as.
            - Use proper superscripts and subscripts only with Unicode characters (e.g., ², ³, subscript numbers like H₂).
            - NO LaTeX.
            - NO ^ symbol at all.
            - Use MathML ONLY when absolutely necessary.
            - Options must be realistic and physically correct.
            """

            if is_chemistry:
                chem_instruction = """
            CHEMISTRY FORMATTING RULES:
            - Use plain text
            - Chemical formulas like H2O, NaCl, CO2
            - DO NOT use MathML
            """

            prompt = f"""
You are a professional assessment specialist.

Generate {batch_count} multiple-choice questions strictly based on the learning objectives below.

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

Return ONLY text in this EXACT format:

Question: <question text>
A. <option>
B. <option>
C. <option>
D. <option>
Answer: <A|B|C|D>
"""

            # ----------------------------
            # Call AI API
            # ----------------------------
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate curriculum-aligned exam questions with extreme formatting accuracy."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2200,
                temperature=0,
            )

            output = resp.choices[0].message.content

            # ----------------------------
            # HARD GUARD: reject LaTeX in Math subjects
            # ----------------------------
            if is_math and ("\\(" in output or "\\[" in output):
                raise ValueError("LaTeX detected in Mathematics output. Expected MathML only.")

            parsed = parse_ai_output(output)
            all_questions.extend(parsed)

            # Update job progress
            job.result = {"partial_count": len(all_questions)}
            job.save()
            time.sleep(0.5)

        # ----------------------------
        # Final job update
        # ----------------------------
        job.result = {"questions": all_questions}
        job.status = "completed"
        job.save()

        return {"created": len(all_questions)}

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.save()
        raise


#calculate marks celery task

import json


@shared_task(bind=True)
def grade_exam_task(self, course_id, user_id, answers_dict):
    """
    Async grading task for a student's exam.
    Caches results in Redis to prevent duplicate grading.
    """
    cache_key = f"graded:{course_id}:{user_id}"
    
    # 1️⃣ Check Redis if already graded
    if cache.get(cache_key):
        return f"Exam for user {user_id} already graded."

    try:
        course = Course.objects.select_related('schools', 'session', 'term', 'exam_type').get(id=course_id)
        student = Profile.objects.select_related('user').get(user_id=user_id)
    except Course.DoesNotExist:
        return f"Course {course_id} not found."
    except Profile.DoesNotExist:
        return f"Student {user_id} profile not found."

    # 2️⃣ Prevent duplicate results in DB
    if Result.objects.filter(
        student=student,
        exam=course,
        session=course.session,
        term=course.term,
        exam_type=course.exam_type,
        result_class=student.student_class
    ).exists():
        cache.set(cache_key, True, timeout=0)  # mark as graded for 1 hour
        return f"Result for student {user_id} already exists."

    # 3️⃣ Calculate total marks
    total_marks = 0
    questions = course.question_set.all()  # assumes related_name='question_set'

    for question in questions:
        qid = str(question.id)
        selected = answers_dict.get(qid)
        if selected and selected == question.answer:
            total_marks += question.marks or 0

    # 4️⃣ Save result in a transaction
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
                result_class=student.student_class
            )
        # 5️⃣ Cache that this student is graded
        cache.set(cache_key, True, timeout=0)  # 1 hour
        return f"Graded exam for student {user_id}, total marks: {total_marks}"

    except IntegrityError:
        cache.set(cache_key, True, timeout=0)
        return f"Duplicate result detected for student {user_id}."
    except Exception as e:
        # Retry if something unexpected happens
        raise self.retry(exc=e, countdown=5, max_retries=3)    