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


@shared_task(bind=True)
def save_exam_result_task(self, course_id, student_id, total_marks):
    course = Course.objects.select_related('schools', 'session', 'term', 'exam_type').get(id=course_id)
    student = Profile.objects.select_related('user').get(id=student_id)

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

        
# client = OpenAI(api_key=settings.OPENAI_API_KEY)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

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
# def generate_ai_questions_task(self, job_id, course_id, num_questions, difficulty, marks):
#     job = GenerationJob.objects.get(job_id=job_id)
#     job.status = "processing"
#     job.save()

#     try:
#         course_obj = Courses.objects.get(id=course_id)
#         course_title = course_obj.title or ""
#         course_detail = Course.objects.filter(course_name=course_obj).first()

#         # Batch to keep token usage and runtime reasonable
#         BATCH_SIZE = 10
#         batches = math.ceil(int(num_questions) / BATCH_SIZE)
#         all_questions = []

#         for b in range(batches):
#             batch_count = min(BATCH_SIZE, int(num_questions) - b * BATCH_SIZE)
#             # build prompt; keep it concise
#             prompt = f"""
# You are an expert in learning assessment.
# Generate {batch_count} {difficulty}-level multiple-choice questions strictly about '{course_title}'.
# Format (no extra text):

# Question: <question text>
# A. <option>
# B. <option>
# C. <option>
# D. <option>
# Answer: <A|B|C|D>
# """
#             resp = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role":"system","content":"You are a helpful assistant that generates professional learning quiz questions."},
#                     {"role":"user","content":prompt},
#                 ],
#                 max_tokens=1200,
#                 temperature=0,
#             )

#             output = resp.choices[0].message.content
#             parsed = parse_ai_output(output)
#             all_questions.extend(parsed)

#             # update job progress (approx)
#             job.result = {"partial_count": len(all_questions)}
#             job.save()

#             # optional small sleep to avoid burst rate issues
#             time.sleep(0.5)

#         # Save resulting questions JSON into job.result
#         job.result = {"questions": all_questions}
#         job.status = "completed"
#         job.save()

#         # Optionally return created count
#         return {"created": len(all_questions)}

#     except Exception as exc:
#         job.status = "failed"
#         job.error = str(exc)
#         job.save()
#         raise

from celery import shared_task
import math
import time

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
