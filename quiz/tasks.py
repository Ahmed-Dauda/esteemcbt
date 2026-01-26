# quiz/tasks.py
from celery import shared_task, current_task
from openai import OpenAI
from django.conf import settings
from quiz.models import Course, GenerationJob, Question, Result
from sms.models import Courses
import re
import math
import time

from django.db import transaction, IntegrityError
from users.models import Profile


client = OpenAI(api_key=settings.OPENAI_API_KEY)
print("OPENAI KEY STARTS WITH:", settings.OPENAI_API_KEY[:20])
        
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


@shared_task(bind=True)
def generate_ai_questions_task(
    self, job_id, course_id, num_questions, difficulty, marks, learning_objectives
):
    job = GenerationJob.objects.get(job_id=job_id)
    job.status = "processing"
    job.save()

    try:
        # Fetch course object
        course_obj = Courses.objects.get(id=course_id)
        course_title = (course_obj.title or "").strip()

        # Map to Course model and save learning objectives
        course_detail = Course.objects.filter(course_name=course_obj).first()
        if course_detail:
            course_detail.learning_objectives = learning_objectives
            course_detail.save()

        # Batch settings
        BATCH_SIZE = 10
        total_questions = int(num_questions)
        batches = math.ceil(total_questions / BATCH_SIZE)
        all_questions = []

        for b in range(batches):
            batch_count = min(BATCH_SIZE, total_questions - (b * BATCH_SIZE))

            prompt = f"""
You are a professional assessment specialist.

Generate {batch_count} multiple-choice questions strictly based on the learning objectives below:

Course: {course_title}

Learning Objectives:
{learning_objectives}

Difficulty Level: {difficulty}

Each question MUST:
- Match the learning objectives
- Be clear and unambiguous
- Have 4 options (A–D)
- Include one correct answer only

Return ONLY text in this strict format:

Question: <question text>
A. <option>
B. <option>
C. <option>
D. <option>
Answer: <A|B|C|D>
"""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You generate curriculum-aligned exam questions with high precision."
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1800,
                temperature=0,
            )

            output = resp.choices[0].message.content
            parsed = parse_ai_output(output)
            all_questions.extend(parsed)
            

            # Update job progress
            job.result = {"partial_count": len(all_questions)}
            job.save()
            time.sleep(0.5)

        # Final job update
        job.result = {"questions": all_questions}
        job.status = "completed"
        job.save()

        return {"created": len(all_questions)}

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.save()
        raise
