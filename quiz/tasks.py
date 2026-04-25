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

# print("OPENAI_API_KEY:",settings.OPENAI_API_KEY)  # Debug print to verify the key is loaded

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


import unicodedata
import re


#last working codes

# @shared_task(bind=True, max_retries=3, default_retry_delay=5)
# def generate_ai_questions_task(
#     self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
# ):
#     """
#     Celery task to generate AI questions for a school-specific course.
#     Generates questions in batches without repetition by passing previously
#     generated questions as context to each subsequent batch.
#     """
#     job = GenerationJob.objects.get(job_id=job_id)
#     job.status = "processing"
#     job.save()

#     try:
#         # ----------------------------
#         # Fetch school-specific course
#         # ----------------------------
#         course_obj = Course.objects.filter(id=course_id).first()
#         if not course_obj:
#             exc = ValueError(f"Course {course_id} not found")
#             raise self.retry(exc=exc)

#         # ----------------------------
#         # Fetch global course title
#         # ----------------------------
#         global_course = course_obj.course_name
#         course_title_raw = global_course.title if global_course else ""
#         print("RAW course title:", repr(course_title_raw))

#         # ----------------------------
#         # Clean course title for keyword detection
#         # ----------------------------
#         def clean_course_title_letters(title):
#             title = unicodedata.normalize("NFKC", title or "")
#             title = re.sub(r'[^a-zA-Z]', '', title)
#             return title.lower()

#         course_title_clean = clean_course_title_letters(course_title_raw)
#         print("CLEANED course title:", repr(course_title_clean))

#         # ----------------------------
#         # Save learning objectives to school-specific course
#         # ----------------------------
#         course_obj.learning_objectives = learning_objectives
#         course_obj.save()

#         # ----------------------------
#         # Detect subjects
#         # ----------------------------
#         math_keywords = ["math", "mathematics", "maths"]
#         physics_keywords = ["physics", "physic", "phy"]
#         chem_keywords = ["chemistry", "chem"]

#         is_math = any(k in course_title_clean for k in math_keywords)
#         is_physics = any(k in course_title_clean for k in physics_keywords)
#         is_chemistry = any(k in course_title_clean for k in chem_keywords)

#         print("IS MATH:", is_math)
#         print("IS PHYSICS:", is_physics)
#         print("IS CHEMISTRY:", is_chemistry)

#         # ----------------------------
#         # Batch settings
#         # ----------------------------
#         BATCH_SIZE = 10
#         total_questions = int(num_questions)
#         batches = math.ceil(total_questions / BATCH_SIZE)
#         all_questions = []

#         # Tracks question stems already generated to deduplicate across batches
#         generated_question_texts = []

#         for b in range(batches):
#             batch_count = min(BATCH_SIZE, total_questions - (b * BATCH_SIZE))

#             # ----------------------------
#             # Subject-specific instructions
#             # ----------------------------
#             math_instruction = ""
#             physics_instruction = ""
#             chem_instruction = ""

#             if is_math:
#                 math_instruction = """
#             Make sure Both questions and options should be formatted as valid MathML format strictly. 
#             - NO LaTeX
#             - NO ^ symbol
#             - Use MathML for all mathematical expressions
#             - Use proper MathML tags for superscripts, subscripts, fractions, roots, etc
#             """

#             if is_physics:
#                 physics_instruction = """
#            PHYSICS FORMATTING RULES:
#             - Prefer INLINE equations.
#             - Use standard physics formulas, e.g., v = u + at, s = ut + 1/2 at², v² = u² + 2as.
#             - Use proper superscripts and subscripts only with Unicode characters (e.g., ², ³, subscript numbers like H₂).
#             - NO LaTeX.
#             - NO ^ symbol at all.
#             - Use MathML ONLY when absolutely necessary.
#             - Options must be realistic and physically correct.
#             """

#             if is_chemistry:
#                 chem_instruction = """
#             CHEMISTRY FORMATTING RULES:
#             - Use plain text
#             - Chemical formulas like H2O, NaCl, CO2
#             - DO NOT use MathML
#             """

#             # ----------------------------
#             # Build anti-repetition context
#             # Inject previously generated question stems so the model
#             # knows what has already been asked and avoids duplicating them.
#             # ----------------------------
#             already_asked_block = ""
#             if generated_question_texts:
#                 already_asked_list = "\n".join(
#                     f"- {q}" for q in generated_question_texts
#                 )
#                 already_asked_block = f"""
# ALREADY GENERATED QUESTIONS (DO NOT REPEAT OR REPHRASE THESE):
# {already_asked_list}

# You MUST generate completely different questions that explore OTHER angles,
# examples, or sub-topics within the same learning objectives.
# """

#             prompt = f"""
# You are a professional assessment specialist.

# Generate {batch_count} multiple-choice questions strictly based on the learning objectives below.
# Each question MUST be unique — do NOT repeat or closely rephrase any question already generated.
# Vary the question style: use scenario-based, definition-based, example-identification,
# fill-in-the-blank style, and application questions to ensure diversity.

# Course: {course_title_raw}

# Learning Objectives:
# {learning_objectives}

# {already_asked_block}

# {math_instruction}
# {physics_instruction}
# {chem_instruction}

# Difficulty Level: {difficulty}

# Rules:
# - Questions must strictly match the learning objectives
# - Be clear and unambiguous
# - Each question MUST have exactly four options (A–D)
# - ONLY ONE correct answer per question
# - Do NOT number the questions
# - Vary question phrasing and structure across all questions

# Return ONLY text in this EXACT format:

# Question: <question text>
# A. <option>
# B. <option>
# C. <option>
# D. <option>
# Answer: <A|B|C|D>
# """

#             # ----------------------------
#             # Call AI API
#             # ----------------------------
#             resp = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": (
#                             "You generate curriculum-aligned exam questions with extreme formatting accuracy. "
#                             "You never repeat or rephrase questions that have already been generated. "
#                             "You vary question styles and explore different aspects of each learning objective."
#                         ),
#                     },
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=3500,
#                 temperature=0.3,  # Raised from 0 to encourage variety while staying on-topic
#             )

#             output = resp.choices[0].message.content

#             # ----------------------------
#             # HARD GUARD: reject LaTeX in Math subjects
#             # ----------------------------
#             if is_math and ("\\(" in output or "\\[" in output):
#                 raise ValueError("LaTeX detected in Mathematics output. Expected MathML only.")

#             parsed = parse_ai_output(output)

#             # ----------------------------
#             # Deduplicate within this batch and against prior batches.
#             # Compares lowercased, stripped question text for fuzzy safety.
#             # ----------------------------
#             seen_normalized = set(q.strip().lower() for q in generated_question_texts)
#             unique_parsed = []
#             for q in parsed:
#                 # Extract the question stem — adjust key name to match your parse_ai_output structure
#                 q_text = q.get("question", "").strip().lower()
#                 if q_text and q_text not in seen_normalized:
#                     unique_parsed.append(q)
#                     seen_normalized.add(q_text)
#                     # Store original-casing stem for the prompt context in next batch
#                     generated_question_texts.append(q.get("question", "").strip())
#                 else:
#                     print(f"[Dedup] Skipped duplicate question: {q_text[:80]}...")

#             all_questions.extend(unique_parsed)

#             # Update job progress
#             job.result = {"partial_count": len(all_questions)}
#             job.save()
#             time.sleep(0.5)

#         # ----------------------------
#         # If deduplication caused a shortfall, log it but don't fail
#         # ----------------------------
#         if len(all_questions) < total_questions:
#             print(
#                 f"[Warning] Only {len(all_questions)} unique questions generated "
#                 f"out of {total_questions} requested. "
#                 f"Consider broadening learning objectives."
#             )

#         # ----------------------------
#         # Final job update
#         # ----------------------------
#         job.result = {"questions": all_questions}
#         job.status = "completed"
#         job.save()

#         return {"created": len(all_questions)}

#     except Exception as exc:
#         job.status = "failed"
#         job.error = str(exc)
#         job.save()
#         raise




#working questions generator

# @shared_task(bind=True, max_retries=3, default_retry_delay=5)
# def generate_ai_questions_task(
#     self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
# ):
#     """
#     Celery task to generate AI questions for a school-specific course.

#     - course_id: ID of Course (school-specific)
#     - Uses Course.course_name.title for the global course title
#     """
#     job = GenerationJob.objects.get(job_id=job_id)
#     job.status = "processing"
#     job.save()

#     try:
#         # ----------------------------
#         # Fetch school-specific course
#         # ----------------------------
#         course_obj = Course.objects.filter(id=course_id).first()
#         if not course_obj:
#             exc = ValueError(f"Course {course_id} not found")
#             raise self.retry(exc=exc)

#         # ----------------------------
#         # Fetch global course title
#         # ----------------------------
#         global_course = course_obj.course_name  # Courses instance
#         course_title_raw = global_course.title if global_course else ""
#         print("RAW course title:", repr(course_title_raw))

#         # ----------------------------
#         # Clean course title for keyword detection
#         # ----------------------------
#         def clean_course_title_letters(title):
#             title = unicodedata.normalize("NFKC", title or "")
#             title = re.sub(r'[^a-zA-Z]', '', title)
#             return title.lower()

#         course_title_clean = clean_course_title_letters(course_title_raw)
#         print("CLEANED course title:", repr(course_title_clean))

#         # ----------------------------
#         # Save learning objectives to school-specific course
#         # ----------------------------
#         course_obj.learning_objectives = learning_objectives
#         course_obj.save()

#         # ----------------------------
#         # Detect subjects
#         # ----------------------------
#         math_keywords = ["math", "mathematics", "maths"]
#         physics_keywords = ["physics", "physic", "phy"]
#         chem_keywords = ["chemistry", "chem"]

#         is_math = any(k in course_title_clean for k in math_keywords)
#         is_physics = any(k in course_title_clean for k in physics_keywords)
#         is_chemistry = any(k in course_title_clean for k in chem_keywords)

#         print("IS MATH:", is_math)
#         print("IS PHYSICS:", is_physics)
#         print("IS CHEMISTRY:", is_chemistry)

#         # ----------------------------
#         # Batch settings
#         # ----------------------------
#         BATCH_SIZE = 10
#         total_questions = int(num_questions)
#         batches = math.ceil(total_questions / BATCH_SIZE)
#         all_questions = []

#         for b in range(batches):
#             batch_count = min(BATCH_SIZE, total_questions - (b * BATCH_SIZE))

#             # ----------------------------
#             # Subject-specific instructions
#             # ----------------------------
#             math_instruction = ""
#             physics_instruction = ""
#             chem_instruction = ""

#             if is_math:
#                 math_instruction = """
#             Make sure Both questions and options should be formatted as valid MathML format strictly. 
#             - NO LaTeX
#             - NO ^ symbol
#             - Use MathML for all mathematical expressions
#             - Use proper MathML tags for superscripts, subscripts, fractions, roots, etc
#             """

#             if is_physics:
#                 physics_instruction = """
#            PHYSICS FORMATTING RULES:
#             - Prefer INLINE equations.
#             - Use standard physics formulas, e.g., v = u + at, s = ut + 1/2 at², v² = u² + 2as.
#             - Use proper superscripts and subscripts only with Unicode characters (e.g., ², ³, subscript numbers like H₂).
#             - NO LaTeX.
#             - NO ^ symbol at all.
#             - Use MathML ONLY when absolutely necessary.
#             - Options must be realistic and physically correct.
#             """

#             if is_chemistry:
#                 chem_instruction = """
#             CHEMISTRY FORMATTING RULES:
#             - Use plain text
#             - Chemical formulas like H2O, NaCl, CO2
#             - DO NOT use MathML
#             """

#             prompt = f"""
# You are a professional assessment specialist.

# Generate {batch_count} multiple-choice questions strictly based on the learning objectives below.

# Course: {course_title_raw}

# Learning Objectives:
# {learning_objectives}

# {math_instruction}
# {physics_instruction}
# {chem_instruction}

# Difficulty Level: {difficulty}

# Rules:
# - Questions must strictly match the learning objectives
# - Be clear and unambiguous
# - Each question MUST have exactly four options (A–D)
# - ONLY ONE correct answer per question

# Return ONLY text in this EXACT format:

# Question: <question text>
# A. <option>
# B. <option>
# C. <option>
# D. <option>
# Answer: <A|B|C|D>
# """

#             # ----------------------------
#             # Call AI API
#             # ----------------------------
#             resp = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You generate curriculum-aligned exam questions with extreme formatting accuracy."},
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=2200,
#                 temperature=0,
#             )

#             output = resp.choices[0].message.content

#             # ----------------------------
#             # HARD GUARD: reject LaTeX in Math subjects
#             # ----------------------------
#             if is_math and ("\\(" in output or "\\[" in output):
#                 raise ValueError("LaTeX detected in Mathematics output. Expected MathML only.")

#             parsed = parse_ai_output(output)
#             all_questions.extend(parsed)

#             # Update job progress
#             job.result = {"partial_count": len(all_questions)}
#             job.save()
#             time.sleep(0.5)

#         # ----------------------------
#         # Final job update
#         # ----------------------------
#         job.result = {"questions": all_questions}
#         job.status = "completed"
#         job.save()

#         return {"created": len(all_questions)}

#     except Exception as exc:
#         job.status = "failed"
#         job.error = str(exc)
#         job.save()
#         raise


import re
import math
import time
import unicodedata

from celery import shared_task
from .models import GenerationJob, Course


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def generate_ai_questions_task(
    self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
):
    """
    Celery task to generate AI questions for a school-specific course.
    Guaranteed to return EXACTLY num_questions unique questions.
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


#working before question number fix
# @shared_task(bind=True, max_retries=3, default_retry_delay=5)
# def generate_ai_questions_task(
#     self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
# ):
#     """
#     Celery task to generate AI questions for a school-specific course.

#     - course_id: ID of Course (school-specific)
#     - Uses Course.course_name.title for the global course title
#     """
#     job = GenerationJob.objects.get(job_id=job_id)
#     job.status = "processing"
#     job.save()

#     try:
#         # ----------------------------
#         # Fetch school-specific course
#         # ----------------------------
#         course_obj = Course.objects.filter(id=course_id).first()
#         if not course_obj:
#             exc = ValueError(f"Course {course_id} not found")
#             raise self.retry(exc=exc)

#         # ----------------------------
#         # Fetch global course title
#         # ----------------------------
#         global_course = course_obj.course_name  # Courses instance
#         course_title_raw = global_course.title if global_course else ""
#         print("RAW course title:", repr(course_title_raw))

#         # ----------------------------
#         # Clean course title for keyword detection
#         # ----------------------------
#         import re
#         def clean_course_title_letters(title):
#             title = unicodedata.normalize("NFKC", title or "")
#             title = re.sub(r'[^a-zA-Z]', '', title)
#             return title.lower()

#         course_title_clean = clean_course_title_letters(course_title_raw)
#         print("CLEANED course title:", repr(course_title_clean))

#         # ----------------------------
#         # Save learning objectives to school-specific course
#         # ----------------------------
#         course_obj.learning_objectives = learning_objectives
#         course_obj.save()

#         # ----------------------------
#         # Detect subjects
#         # ----------------------------
#         math_keywords = ["math", "mathematics", "maths"]
#         physics_keywords = ["physics", "physic", "phy"]
#         chem_keywords = ["chemistry", "chem"]

#         is_math = any(k in course_title_clean for k in math_keywords)
#         is_physics = any(k in course_title_clean for k in physics_keywords)
#         is_chemistry = any(k in course_title_clean for k in chem_keywords)

#         print("IS MATH:", is_math)
#         print("IS PHYSICS:", is_physics)
#         print("IS CHEMISTRY:", is_chemistry)
        

#         # ----------------------------
#         # Batch settings
#         # ----------------------------
#         BATCH_SIZE = 10
#         total_questions = int(num_questions)
#         batches = math.ceil(total_questions / BATCH_SIZE)
#         all_questions = []

#         previous_questions_text = "\n".join(
#             [q["question"] for q in all_questions[:60]]  # limit to avoid token overflow
#         )
                

#         for b in range(batches):
#             batch_count = min(BATCH_SIZE, total_questions - (b * BATCH_SIZE))

#             # ----------------------------
#             # Subject-specific instructions
#             # ----------------------------
#             math_instruction = ""
#             physics_instruction = ""
#             chem_instruction = ""

#             if is_math:

#                 math_instruction = """
#                     Format ALL mathematical expressions using plain Unicode characters only.
#                     No markup. No tags. No LaTeX. No MathML. Just text and Unicode symbols.

#                     ═══════════════════════════════════════════════════
#                     ABSOLUTE FORBIDDEN — never output any of these:
#                     ^ (caret for exponents)          BAD: x^2
#                     LaTeX syntax                     BAD: \\frac{3}{4}, $x^2$, \\sqrt{x}
#                     MathML tags                      BAD: <math>, <mfrac>, <msup>, <mn>, <mi>
#                     HTML math tags                   BAD: <sup>, <sub>
#                     Any angle brackets for math      BAD: <anything>
#                     If you are about to type any of the above — STOP and use Unicode instead.
#                     ═══════════════════════════════════════════════════

#                     EXPONENTS — use Unicode superscript characters:
#                     x²        (x squared)
#                     x³        (x cubed)
#                     xⁿ        (x to the power n)
#                     x²⁺¹      (compound exponent)
#                     Superscript digits/symbols: ⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁺ ⁻ ⁼ ⁽ ⁾ ⁿ

#                     SUBSCRIPTS — use Unicode subscript characters:
#                     x₁  x₂  aₙ  H₂O  CO₂
#                     Subscript digits/symbols: ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉ ₊ ₋ ₌ ₍ ₎

#                     FRACTIONS — use Unicode fraction symbols:
#                     ½  ⅓  ⅔  ¼  ¾  ⅕  ⅖  ⅗  ⅘  ⅙  ⅚  ⅛  ⅜  ⅝  ⅞
#                     For any other fraction write:  (numerator)/(denominator)
#                     Example: 5/7 → (5)/(7)

#                     ROOTS:
#                     √x        (square root)
#                     ∛x        (cube root)
#                     ∜x        (fourth root)
#                     √(x + 1)  (root of expression — use brackets)

#                     OPERATORS:
#                     ×  multiply
#                     ÷  divide
#                     ±  plus or minus
#                     ≠  not equal
#                     ≈  approximately equal
#                     ≤  less than or equal
#                     ≥  greater than or equal
#                     π  pi
#                     ∞  infinity
#                     ∑  sum
#                     ∫  integral
#                     ∈  element of
#                     ∝  proportional to

#                     EXAMPLES (copy this style exactly):
#                     Quadratic equation  →  x² - 6x + 8 = 0
#                     Quadratic formula   →  x = (-b ± √(b² - 4ac)) / (2a)
#                     Fraction            →  ¾ + ½ = 1¼
#                     Subscript           →  a₁ + a₂ = a₃
#                     Chemistry           →  H₂O + CO₂
#                     Complex exponent    →  2³ = 8
#                     Mixed expression    →  f(x) = x² + (1)/(x-1) + √(x + 3)

#                     OUTPUT CHECKLIST — before writing any math, confirm:
#                     ✓ No ^ anywhere
#                     ✓ No backslashes
#                     ✓ No < or > characters used for math
#                     ✓ No <math>, <mfrac>, <msup> or any XML/HTML tags
#                     ✓ Exponents use ⁰¹²³⁴⁵⁶⁷⁸⁹ superscript digits
#                     ✓ Fractions use ½⅓¼¾ or (a)/(b) form
#                     ✓ Roots use √ ∛ ∜
#                     """


#             if is_physics:
#                 physics_instruction = """
#            PHYSICS FORMATTING RULES:
#             - Prefer INLINE equations.
#             - Use standard physics formulas, e.g., v = u + at, s = ut + 1/2 at², v² = u² + 2as.
#             - Use proper superscripts and subscripts only with Unicode characters (e.g., ², ³, subscript numbers like H₂).
#             - NO LaTeX.
#             - NO ^ symbol at all.
#             - Use MathML ONLY when absolutely necessary.
#             - Options must be realistic and physically correct.
#             """

#             if is_chemistry:
#                 chem_instruction = """
#             CHEMISTRY FORMATTING RULES:
#             - Use plain text
#             - Chemical formulas like H2O, NaCl, CO2
#             - DO NOT use MathML
#             """

#             prompt = f"""
# You are a professional assessment specialist.

# Generate {batch_count} multiple-choice questions strictly based on the learning objectives below.

# Course: {course_title_raw}

# Learning Objectives:
# {learning_objectives}

# {math_instruction}
# {physics_instruction}
# {chem_instruction}

# Difficulty Level: {difficulty}

# Rules:
# - Questions must strictly match the learning objectives
# - Be clear and unambiguous
# - Each question MUST have exactly four options (A–D)
# - ONLY ONE correct answer per question

# Return ONLY text in this EXACT format:

# Question: <question text>
# A. <option>
# B. <option>
# C. <option>
# D. <option>
# Answer: <A|B|C|D>

# Avoid repeating or rephrasing any of these questions:
# {previous_questions_text}

# CRITICAL RULES — NO DUPLICATION:
# - Do NOT repeat any question
# - Do NOT rephrase an existing question
# - Each question must test a DIFFERENT concept or variation
# - Avoid same numbers, same structure, or same wording
# - If a similar idea is used, change context, values, and structure completely to ensure it's a fresh question that explores a new angle of the learning objectives.

# DIVERSITY REQUIREMENTS:
# - Include a mix of:
#   • conceptual questions
#   • word problems
#   • application-based questions
#   • direct computation
# - Do NOT generate only numeric variations of the same problem

# """

#             # ----------------------------
#             # Call AI API
#             # ----------------------------
#             resp = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You generate curriculum-aligned exam questions with extreme formatting accuracy."},
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=2200,
#                 temperature=0.7,
#             )

#             output = resp.choices[0].message.content

#             print("\n" + "="*80)
#             print("RAW AI OUTPUT START")
#             print(output)
#             print("RAW AI OUTPUT END")
#             print("="*80 + "\n")


#             parsed = parse_ai_output(output)

#             print("\n" + "-"*80)
#             print("PARSED OUTPUT:")
#             for q in parsed:
#                 print(q)
#             print("-"*80 + "\n")

#             all_questions.extend(parsed)

#             # Update job progress
#             job.result = {"partial_count": len(all_questions)}
#             job.save()
#             time.sleep(0.5)

#         # ----------------------------
#         # Final job update
#         # REMOVE DUPLICATES
#         # ----------------------------
#         import re

#         def normalize(q):
#             return re.sub(r'\s+', ' ', q.lower().strip())

#         seen = set()
#         unique_questions = []

#         for q in all_questions:
#             if "question" not in q:
#                 continue

#             key = normalize(q["question"])

#             if key not in seen:
#                 seen.add(key)
#                 unique_questions.append(q)

#         all_questions = unique_questions


#         # ----------------------------
#         # FINAL JOB UPDATE
#         # ----------------------------
#         job.result = {"questions": all_questions}
#         job.status = "completed"
#         job.save()

#         return {"created": len(all_questions)}


#     except Exception as exc:
#         job.status = "failed"
#         job.error = str(exc)
#         job.save()
#         raise


import json
import logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, countdown=5)
def grade_exam_task(self, course_id, user_id, answers_dict):
    cache_key = f"graded:{course_id}:{user_id}"

    if cache.get(cache_key):
        return f"Exam for user {user_id} already graded."

    try:
        course = Course.objects.select_related(
            'schools', 'session', 'term', 'exam_type'
        ).get(id=course_id)
        student = Profile.objects.select_related('user').get(user_id=user_id)
    except Course.DoesNotExist:
        return f"Course {course_id} not found."
    except Profile.DoesNotExist:
        return f"Student {user_id} profile not found."

    # ✅ Log for debugging
    logger.info(
        f"Grading: user={user_id}, course={course_id}, "
        f"school={course.schools}, student_class={student.student_class}"
    )

    # ✅ Reliable duplicate check — no result_class (NULL != NULL in PostgreSQL)
    if Result.objects.filter(
        student=student,
        exam=course,
        session=course.session,
        term=course.term,
        exam_type=course.exam_type,
    ).exists():
        cache.set(cache_key, True, timeout=3600)
        return f"Result for student {user_id} already exists."

    # Fetch all questions in one query
    questions = list(
        Question.objects.filter(course=course).only('id', 'answer', 'marks')
    )

    total_marks = 0
    for question in questions:
        selected = answers_dict.get(str(question.id))
        if selected and selected == question.answer:
            total_marks += question.marks or 0

    # ✅ Never save None as result_class
    school_name = course.schools.school_name if course.schools else 'Unknown'
    result_class = student.student_class or f"Unassigned-{school_name}"

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

        cache.set(cache_key, True, timeout=3600)
        cache.delete(f"user_exam_data:{user_id}")
        cache.delete(f"user_results:{user_id}")

        return f"Graded exam for student {user_id}, total marks: {total_marks}"

    except IntegrityError as e:
        logger.error(f"IntegrityError for user {user_id}: {e}")
        cache.set(cache_key, True, timeout=3600)
        return f"Duplicate result detected for student {user_id}."
    except Exception as e:
        logger.error(f"Exception grading user {user_id}: {e}")
        raise self.retry(exc=e, countdown=5, max_retries=3)


