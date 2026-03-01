import asyncio
from celery import shared_task
from openai import AsyncOpenAI
from django.conf import settings
from .models import NewUser, Result_Portal

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def fetch_comment(student_name, result_text, strong, weak, student_id, semaphore):
    prompt = f"""
You are a school principal. Write a brief, professional report card comment for this student.

Student: {student_name}
Results:
{result_text}

Strong subjects: {', '.join(strong) if strong else 'None'}
Weak subjects: {', '.join(weak) if weak else 'None'}

Rules:
- 1–2 sentences only
- No salutations, sign-offs, or names
- Mention strengths, weaknesses, and encouragement
- Formal and concise tone
"""
    async with semaphore:
        try:
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate concise principal report card comments."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.4,
            )
            return student_id, resp.choices[0].message.content.strip()
        except Exception as e:
            return student_id, f"Error: {str(e)}"


async def generate_all_async(student_data):
    """
    student_data: list of dicts with all data pre-extracted — no DB calls here
    """
    semaphore = asyncio.Semaphore(20)
    tasks = [
        fetch_comment(
            s["name"],
            s["result_text"],
            s["strong"],
            s["weak"],
            s["id"],
            semaphore
        )
        for s in student_data
    ]
    return dict(await asyncio.gather(*tasks))


@shared_task(bind=True)
def generate_comments_task(self, session_id, term_id, class_id):
    # ── Pull everything from DB here (sync context, safe) ──────────────────
    students = list(NewUser.objects.filter(course_grades__id=class_id).distinct())
    results = list(
        Result_Portal.objects.filter(
            session_id=session_id,
            term_id=term_id,
            student__in=students
        ).select_related("subject", "student", "schools")  # ← add schools here
    )

    self.update_state(state="PROGRESS", meta={"current": 0, "total": len(students)})

    # ── Pre-extract ALL data into plain dicts before async context ──────────
    # This avoids any lazy DB access inside async (which causes the error)
    student_data = []
    for student in students:
        student_results = [r for r in results if r.student_id == student.id]

        strong, weak, lines = [], [], []
        for r in student_results:
            total = r.total_score or 0

            # Access grade_letter and remark HERE (sync, safe) not inside async
            try:
                grade = r.grade_letter or '-'
            except Exception:
                grade = '-'

            try:
                remark = r.remark or '-'
            except Exception:
                remark = '-'

            if total >= 70:
                strong.append(r.subject.title)
            elif total < 45:
                weak.append(r.subject.title)

            lines.append(f"{r.subject.title}: Total={total}, Grade={grade}, Remark={remark}")

        student_data.append({
            "id": str(student.id),
            "name": f"{student.first_name} {student.last_name}",
            "result_text": "\n".join(lines) if lines else "No results yet.",
            "strong": strong,
            "weak": weak,
        })

    # ── Now safe to run async — no DB calls will happen inside ─────────────
    comments = asyncio.run(generate_all_async(student_data))

    return {"current": len(students), "total": len(students), "comments": comments}