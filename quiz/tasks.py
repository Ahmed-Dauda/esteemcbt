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

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def generate_ai_questions_task(
    self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
):
    """
    Celery task to generate AI questions for a school-specific course.
    Guarantees exactly num_questions unique questions by retrying any
    batch that returns fewer than expected due to AI inconsistency or deduplication.
    Enforces strict MathML for math subjects — discards and retries any question
    that contains plain math notation.
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
        global_course = course_obj.course_name
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
        # Save learning objectives
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
        # Subject-specific instructions
        # ----------------------------
        math_instruction = ""
        physics_instruction = ""
        chem_instruction = ""

        if is_math:
            math_instruction = """
MATHEMATICS FORMATTING — STRICTLY ENFORCED:
You MUST format ALL mathematical expressions using valid MathML wrapped in <math> tags.
This includes: numbers with operations, fractions, exponents, roots, equations, variables.

CORRECT EXAMPLE:
Question: What is <math><msup><mi>x</mi><mn>2</mn></msup></math> when x = 3?
A. <math><mn>6</mn></math>
B. <math><mn>9</mn></math>
C. <math><mn>12</mn></math>
D. <math><mn>3</mn></math>
Answer: B

RULES:
- Use <math>...</math> for EVERY mathematical expression, no exceptions
- Use <msup> for powers/exponents (NOT ^ symbol)
- Use <mfrac> for fractions
- Use <msqrt> for square roots
- Use <mi> for variables (x, y, n)
- Use <mn> for numbers
- Use <mo> for operators (+, -, ×, ÷, =)
- NEVER use LaTeX (no \\( \\[ $ symbols)
- NEVER use ^ symbol
- NEVER write plain math like x^2 or 2/3
"""

        if is_physics:
            physics_instruction = """
PHYSICS FORMATTING RULES:
- Prefer INLINE equations.
- Use standard physics formulas, e.g., v = u + at, s = ut + 1/2 at², v² = u² + 2as.
- Use proper superscripts and subscripts only with Unicode characters (e.g., ², ³, H₂).
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

        # ----------------------------
        # MathML validator/enforcer
        # Discards questions that contain plain math notation so the
        # retry loop can request replacements.
        # ----------------------------
        def enforce_mathml(questions):
            plain_math_patterns = [
                r'\^',           # x^2
                r'\$',           # LaTeX $
                r'\\\(',         # LaTeX \(
                r'\\\[',         # LaTeX \[
                r'\d+/\d+',      # plain fractions like 2/3
                r'sqrt\(',       # sqrt(
            ]
            clean_questions = []
            for q in questions:
                q_text = q.get("question", "")
                options = [
                    q.get("A", ""), q.get("B", ""),
                    q.get("C", ""), q.get("D", "")
                ]
                all_text = q_text + " ".join(options)
                has_plain_math = any(re.search(p, all_text) for p in plain_math_patterns)
                if has_plain_math:
                    print(f"[MathML Guard] Plain math detected, discarding: {q_text[:80]}...")
                else:
                    clean_questions.append(q)
            return clean_questions

        # ----------------------------
        # Helper: call AI and return parsed unique questions
        # ----------------------------
        def fetch_questions(needed, generated_question_texts, seen_normalized):
            """
            Ask the AI for exactly `needed` questions, deduplicate against
            seen_normalized, enforce MathML for math subjects,
            and return only the new unique clean ones.
            """
            already_asked_block = ""
            if generated_question_texts:
                already_asked_list = "\n".join(
                    f"- {q}" for q in generated_question_texts
                )
                already_asked_block = f"""
ALREADY GENERATED QUESTIONS (DO NOT REPEAT OR REPHRASE THESE):
{already_asked_list}

You MUST generate completely different questions that explore OTHER angles,
examples, or sub-topics within the same learning objectives.
"""

            prompt = f"""
You are a professional assessment specialist.

Generate EXACTLY {needed} multiple-choice questions strictly based on the learning objectives below.
This is very important: your response MUST contain EXACTLY {needed} questions — no more, no less.
Each question MUST be unique — do NOT repeat or closely rephrase any question already generated.
Vary the question style: use scenario-based, definition-based, example-identification,
fill-in-the-blank style, and application questions to ensure diversity.

Course: {course_title_raw}

Learning Objectives:
{learning_objectives}

{already_asked_block}

{math_instruction}
{physics_instruction}
{chem_instruction}

Difficulty Level: {difficulty}

Rules:
- Questions must strictly match the learning objectives
- Be clear and unambiguous
- Each question MUST have exactly four options (A–D)
- ONLY ONE correct answer per question
- Do NOT number the questions
- Vary question phrasing and structure across all questions

Return ONLY text in this EXACT format (repeat exactly {needed} times):

Question: <question text>
A. <option>
B. <option>
C. <option>
D. <option>
Answer: <A|B|C|D>
"""

            # Use gpt-4o for math (better MathML compliance), mini for others
            model = "gpt-4o" if is_math else "gpt-4o-mini"

            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You generate curriculum-aligned exam questions with extreme formatting accuracy. "
                            f"You ALWAYS return EXACTLY the number of questions requested. "
                            "You never repeat or rephrase questions that have already been generated. "
                            "You vary question styles and explore different aspects of each learning objective. "
                            + (
                                "For mathematics, you ALWAYS use MathML (<math> tags) for every expression. "
                                "You NEVER use LaTeX, plain fractions like 2/3, or ^ for exponents."
                                if is_math else ""
                            )
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=3500,
                temperature=0.3,
            )

            output = resp.choices[0].message.content

            # Hard guard: reject LaTeX in Math
            if is_math and ("\\(" in output or "\\[" in output):
                print("[MathML Hard Guard] LaTeX detected in output — discarding entire batch.")
                return []

            parsed = parse_ai_output(output)

            # Deduplicate against already generated questions
            unique_new = []
            for q in parsed:
                q_text = q.get("question", "").strip().lower()
                if q_text and q_text not in seen_normalized:
                    unique_new.append(q)
                    seen_normalized.add(q_text)
                else:
                    print(f"[Dedup] Skipped duplicate: {q_text[:80]}...")

            # Enforce MathML for math subjects
            if is_math:
                unique_new = enforce_mathml(unique_new)

            return unique_new

        # ----------------------------
        # Main generation loop
        # Keeps going until we have exactly total_questions
        # ----------------------------
        BATCH_SIZE = 10
        MAX_BATCH_RETRIES = 5
        total_questions = int(num_questions)

        all_questions = []
        generated_question_texts = []  # original-casing stems for prompt context
        seen_normalized = set()        # lowercased stems for dedup

        while len(all_questions) < total_questions:
            still_needed = total_questions - len(all_questions)
            batch_count = min(BATCH_SIZE, still_needed)

            print(f"[Generator] Have {len(all_questions)}/{total_questions} — requesting {batch_count} more...")

            got_new = []
            attempts = 0

            # Retry this batch until we get enough unique questions or hit cap
            while len(got_new) < batch_count and attempts < MAX_BATCH_RETRIES:
                attempts += 1
                remaining_needed = batch_count - len(got_new)

                new_qs = fetch_questions(
                    needed=remaining_needed,
                    generated_question_texts=generated_question_texts,
                    seen_normalized=seen_normalized,
                )

                for q in new_qs:
                    got_new.append(q)
                    generated_question_texts.append(q.get("question", "").strip())

                if len(got_new) < batch_count:
                    print(
                        f"[Retry] Attempt {attempts}: got {len(got_new)}/{batch_count}. "
                        f"Retrying for {batch_count - len(got_new)} more..."
                    )
                    time.sleep(0.5)

            if len(got_new) < batch_count:
                print(
                    f"[Warning] After {MAX_BATCH_RETRIES} attempts, only got "
                    f"{len(got_new)}/{batch_count} for this batch. "
                    f"Learning objectives may be too narrow."
                )

            all_questions.extend(got_new)

            # Update job progress
            job.result = {"partial_count": len(all_questions)}
            job.save()
            time.sleep(0.5)

        # Trim to exact count in the rare case of overshoot
        all_questions = all_questions[:total_questions]

        print(f"[Generator] Final count: {len(all_questions)}/{total_questions}")

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

#calculate marks celery task


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


