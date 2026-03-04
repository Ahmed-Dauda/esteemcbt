import asyncio
from celery import shared_task
from openai import AsyncOpenAI
from django.conf import settings
from .models import NewUser, Result_Portal
import asyncio
import io
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from celery import shared_task
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, HRFlowable, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from .models import Result_Portal, StudentBehaviorRecord
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)



def build_student_pdf_data(sid, data, all_results_dict, class_totals, sorted_totals):
    """
    Pure function — builds one student's element list.
    Runs in a thread pool for parallelism.
    Returns (sid, elements_list)
    """
    student = data['student']
    records = data['records']
    school = data['school']
    session = data['session']
    term = data['term']
    behavior = data.get('behavior')

    styles = getSampleStyleSheet()
    style_left = styles["Normal"]
    style_left.alignment = TA_LEFT
    style_center = ParagraphStyle(name=f"Center_{sid}", parent=styles["Normal"], alignment=TA_CENTER)

    elements = []

    # ── Stats ──────────────────────────────────────────────────────────────
    num_subjects = len(records)
    student_total = class_totals.get(sid, 0)
    student_average = round(student_total / num_subjects, 2) if num_subjects else 0
    total_students = len(class_totals)
    class_average = round(sum(class_totals.values()) / total_students, 2) if total_students else 0
    position = next((i + 1 for i, (stud_id, _) in enumerate(sorted_totals) if stud_id == sid), None)
    highest_in_class = max(class_totals.values(), default=0)
    lowest_in_class = min(class_totals.values(), default=0)
    final_grade = records[0].grade_letter if records else ""

    # ── Logo ───────────────────────────────────────────────────────────────
    logo_img = None
    if school and getattr(school, 'logo', None):
        try:
            logo_data = io.BytesIO(requests.get(school.logo.url, timeout=5).content)
            logo_img = RLImage(logo_data, width=80, height=80)
        except Exception:
            pass

    school_name = f"<b>{getattr(school, 'school_name', 'Best Academy')}</b>"
    school_motto = f"<i>{getattr(school, 'school_motto', '')}</i>"
    school_address = getattr(school, 'school_address', '')

    school_details = [
        Paragraph(school_name, ParagraphStyle(name=f'SN_{sid}', fontSize=14, alignment=TA_LEFT)),
        Spacer(1, 8),
        Paragraph(school_motto, ParagraphStyle(name=f'SM_{sid}', fontSize=10, alignment=TA_LEFT)),
        Spacer(1, 8),
        Paragraph(school_address, ParagraphStyle(name=f'SA_{sid}', fontSize=9, alignment=TA_LEFT)),
    ]

    header_table = Table([[logo_img or "", school_details]], colWidths=[90, 400])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
    elements.append(hr)
    elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
    elements.append(Spacer(1, 10))

    # ── Student Info ───────────────────────────────────────────────────────
    student_info_data = [
        [f"Name: {student.first_name} {student.last_name}", f"Class: {data['result_class']}", f"Term: {term.name}"],
        [f"Session: {session.name}", f"No. in Class: {total_students}", f"Position: {position} of {total_students}"],
        [f"Total Score: {student_total}", f"Average Score: {student_average}", f"Class Average: {class_average}"],
        [f"Highest in Class: {highest_in_class}", f"Lowest in Class: {lowest_in_class}", f"Final Grade: {final_grade}"],
    ]
    student_table = Table(student_info_data, colWidths=[180, 180, 180])
    student_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.6, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements += [student_table, Spacer(1, 15)]

    # ── Subject Table ──────────────────────────────────────────────────────

    max_ca = float(getattr(school, 'max_ca_score', 10) or 10)
    max_mid = float(getattr(school, 'max_midterm_score', 30) or 30)
    max_exam = float(getattr(school, 'max_exam_score', 60) or 60)

    header_style = ParagraphStyle(name=f'HS_{sid}', fontName='Helvetica-Bold', fontSize=7, alignment=1)
    headers = [
        "Subject", f"CA\n({max_ca})", f"Midterm\n({max_mid})",
        f"Exam\n({max_exam})", "Total", "Per (%)", "Grade",
        "Class\nAve", "POS", "Out\nOf", "High\nIn\nClass", "Low\nIn\nClass", "Remark"
    ]
    table_data = [[Paragraph(h, header_style) for h in headers]]

    for r in records:
        ca = float(r.ca_score or 0)
        mid = float(r.midterm_score or 0)
        exam = float(r.exam_score or 0)
        total = ca + mid + exam
        max_total = max_ca + max_mid + max_exam
        percentage = round((total / max_total) * 100) if max_total else 0

        # Use pre-fetched subject results from dict
        subject_results = all_results_dict.get(r.subject_id, [])
        subject_totals = [
            float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
            for s in subject_results
        ]
        class_avg = round(sum(subject_totals) / len(subject_totals), 2) if subject_totals else 0
        high_in_class = max(subject_totals, default=0)
        low_in_class = min(subject_totals, default=0)
        pos_sorted = sorted(
            [(s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
             for s in subject_results],
            key=lambda x: x[1], reverse=True
        )
        pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == sid), None)

        row = [
            r.subject.title, str(ca), str(mid), str(exam), str(total),
            str(percentage), r.grade_letter, str(class_avg), str(pos),
            str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark or ''
        ]
        table_data.append([Paragraph(str(x), style_center) for x in row])

    col_fractions = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
    page_width = A4[0] - 50  # approx margins
    col_widths = [page_width * f for f in col_fractions]

    result_table = Table(table_data, colWidths=col_widths)
    result_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements += [result_table, Spacer(1, 15)]

    # ── Grading Scale ──────────────────────────────────────────────────────
    elements.append(Paragraph("<b>GRADING SCALE</b>", style_left))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39", style_left))
    elements.append(Spacer(1, 15))
    elements.append(hr)

    # ── Behavior / Comments ────────────────────────────────────────────────
    if behavior:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}",
            style_left
        ))
    elements.append(hr)

    # ── Signatures ─────────────────────────────────────────────────────────
    for sig_field in ['teacher_signature', 'principal_signature']:
        if school and getattr(school, sig_field, None):
            try:
                sig_data = io.BytesIO(requests.get(getattr(school, sig_field).url, timeout=5).content)
                elements.append(RLImage(sig_data, width=100, height=40))
            except Exception:
                pass

    elements.append(Spacer(1, 10))
    elements.append(PageBreak())

    return sid, elements

@shared_task(bind=True)
def generate_class_pdf_task(self, result_class, session_id, term_id):
    """
    Celery task: mirrors download_class_reports_pdf exactly,
    but runs in background and uploads to Cloudinary.
    """
    import cloudinary
    import cloudinary.uploader
    from .models import Result_Portal, StudentBehaviorRecord
    from django.conf import settings

    # ── Force Cloudinary config ────────────────────────────────────────────
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME if hasattr(settings, 'CLOUDINARY_CLOUD_NAME') else os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=settings.CLOUDINARY_API_KEY if hasattr(settings, 'CLOUDINARY_API_KEY') else os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=settings.CLOUDINARY_API_SECRET if hasattr(settings, 'CLOUDINARY_API_SECRET') else os.environ.get('CLOUDINARY_API_SECRET'),
        secure=True
    )

    self.update_state(state="PROGRESS", meta={"step": "Fetching data...", "percent": 5})

    # ── Fetch all results ──────────────────────────────────────────────────
    all_results = list(
        Result_Portal.objects.filter(
            result_class=result_class,
            session_id=session_id,
            term_id=term_id
        ).select_related('student', 'subject', 'schools', 'session', 'term')
        .order_by('student__username', 'subject__title')
    )

    if not all_results:
        return {"error": "No results found"}

    # ── Group by student ───────────────────────────────────────────────────
    students = {}
    for res in all_results:
        sid = res.student_id
        if sid not in students:
            students[sid] = {
                'student': res.student,
                'records': [],
                'school': res.schools,
                'session': res.session,
                'term': res.term,
            }
        students[sid]['records'].append(res)

    # ── Compute totals for ranking ─────────────────────────────────────────
    class_totals = {}
    for res in all_results:
        sid = res.student_id
        total = float(res.ca_score or 0) + float(res.midterm_score or 0) + float(res.exam_score or 0)
        class_totals[sid] = class_totals.get(sid, 0) + total
    sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)

    # ── Pre-group subject results (avoids N+1 queries) ─────────────────────
    all_results_dict = {}
    for res in all_results:
        all_results_dict.setdefault(res.subject_id, []).append(res)

    # ── Fetch behavior records ─────────────────────────────────────────────
    behaviors = {
        b.student_id: b
        for b in StudentBehaviorRecord.objects.filter(
            session_id=session_id,
            term_id=term_id
        ).select_related('form_teacher__user')
    }

    self.update_state(state="PROGRESS", meta={"step": "Building PDF...", "percent": 20})

    # ── PDF Setup ──────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=25, leftMargin=25, rightMargin=25, bottomMargin=30
    )

    styles = getSampleStyleSheet()
    style_left = styles["Normal"]
    style_left.alignment = TA_LEFT
    style_center = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)

    elements = []
    total_students = len(students)
    completed = 0

    # ── Generate report for each student ──────────────────────────────────
    for sid, data in students.items():
        student = data['student']
        records = data['records']
        school = data['school']
        session = data['session']
        term = data['term']
        behavior = behaviors.get(sid)

        # ── Student stats ──────────────────────────────────────────────────
        num_subjects = len(records)
        student_total = class_totals.get(sid, 0)
        student_average = round(student_total / num_subjects, 2) if num_subjects else 0
        total_students_count = len(class_totals)
        class_average = round(sum(class_totals.values()) / total_students_count, 2) if total_students_count else 0
        position = next((i + 1 for i, (stud_id, _) in enumerate(sorted_totals) if stud_id == sid), None)
        highest_in_class = max(class_totals.values(), default=0)
        lowest_in_class = min(class_totals.values(), default=0)
        final_grade = records[0].grade_letter if records else ""

        # ── Logo ───────────────────────────────────────────────────────────
        logo_img = None
        if school and getattr(school, 'logo', None):
            try:
                logo_data = io.BytesIO(requests.get(school.logo.url, timeout=5).content)
                logo_img = RLImage(logo_data, width=80, height=80)
            except Exception:
                pass

        school_name    = f"<b>{getattr(school, 'school_name', 'Best Academy, Abuja')}</b>"
        school_motto   = f"<i>{getattr(school, 'school_motto', 'Motto: Knowledge for Excellence')}</i>"
        school_address = getattr(school, 'school_address', 'Tunga')

        school_details = [
            Paragraph(school_name, ParagraphStyle(name=f'SN_{sid}', fontSize=14, alignment=TA_LEFT)),
            Spacer(1, 8),
            Paragraph(school_motto, ParagraphStyle(name=f'SM_{sid}', fontSize=10, alignment=TA_LEFT)),
            Spacer(1, 8),
            Paragraph(school_address, ParagraphStyle(name=f'SA_{sid}', fontSize=9, alignment=TA_LEFT)),
        ]

        header_table = Table([[logo_img or "", school_details]], colWidths=[90, 400])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
        elements.append(hr)

        elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
        elements.append(Spacer(1, 10))

        # ── Student Info ───────────────────────────────────────────────────
        student_info_data = [
            [f"Name: {student.first_name} {student.last_name}", f"Class: {result_class}", f"Term: {term.name}"],
            [f"Session: {session.name}", f"No. in Class: {total_students_count}", f"Position: {position} of {total_students_count}"],
            [f"Total Score: {student_total}", f"Average Score: {student_average}", f"Class Average: {class_average}"],
            [f"Highest in Class: {highest_in_class}", f"Lowest in Class: {lowest_in_class}", f"Final Grade: {final_grade}"],
        ]
        student_table = Table(student_info_data, colWidths=[180, 180, 180])
        student_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.6, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements += [student_table, Spacer(1, 15)]

        # ── Subject Table ──────────────────────────────────────────────────
        max_ca   = float(getattr(school, 'max_ca_score', 10) or 10)
        max_mid  = float(getattr(school, 'max_midterm_score', 30) or 30)
        max_exam = float(getattr(school, 'max_exam_score', 60) or 60)

        header_style = ParagraphStyle(name=f'HS_{sid}', fontName='Helvetica-Bold', fontSize=7, alignment=1)
        headers = [
            "Subject",
            f"CA\n({max_ca})",
            f"Midterm\n({max_mid})",
            f"Exam\n({max_exam})",
            "Total", "Per (%)", "Grade",
            "Class\nAve", "POS", "Out\nOf",
            "High\nIn\nClass", "Low\nIn\nClass", "Remark"
        ]
        table_data = [[Paragraph(h, header_style) for h in headers]]

        for r in records:
            ca   = float(r.ca_score or 0)
            mid  = float(r.midterm_score or 0)
            exam = float(r.exam_score or 0)
            total = ca + mid + exam
            max_total = max_ca + max_mid + max_exam
            percentage = round((total / max_total) * 100) if max_total else 0

            # Use pre-fetched subject results
            subject_results = all_results_dict.get(r.subject_id, [])
            subject_totals = [
                float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
                for s in subject_results
            ]
            class_avg    = round(sum(subject_totals) / len(subject_totals), 2) if subject_totals else 0
            high_in_class = max(subject_totals, default=0)
            low_in_class  = min(subject_totals, default=0)
            pos_sorted = sorted(
                [(s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
                 for s in subject_results],
                key=lambda x: x[1], reverse=True
            )
            pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == sid), None)

            row = [
                r.subject.title, str(ca), str(mid), str(exam), str(total),
                str(percentage), r.grade_letter, str(class_avg), str(pos),
                str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark or ''
            ]
            table_data.append([Paragraph(str(x), style_center) for x in row])

        page_width = A4[0] - doc.leftMargin - doc.rightMargin
        col_fractions = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
        col_widths = [page_width * f for f in col_fractions]

        result_table = Table(table_data, colWidths=col_widths)
        result_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements += [result_table, Spacer(1, 15)]

        # ── Grading Scale ──────────────────────────────────────────────────
        elements.append(Paragraph("<b>GRADING SCALE</b>", style_left))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            "A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39",
            style_left
        ))
        elements.append(Spacer(1, 15))
        elements.append(hr)

        # ── Behavior / Form Teacher ────────────────────────────────────────
        if behavior:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}",
                style_left
            ))
        elements.append(hr)

        # ── Signatures ─────────────────────────────────────────────────────
        for sig_field in ['teacher_signature', 'principal_signature']:
            if school and getattr(school, sig_field, None):
                try:
                    sig_data = io.BytesIO(requests.get(getattr(school, sig_field).url, timeout=5).content)
                    elements.append(RLImage(sig_data, width=100, height=40))
                except Exception:
                    pass

        elements.append(Spacer(1, 10))
        elements.append(PageBreak())

        # ── Update progress ────────────────────────────────────────────────
        completed += 1
        percent = 20 + int((completed / total_students) * 65)
        self.update_state(state="PROGRESS", meta={
            "step": f"Built {completed} of {total_students} student pages...",
            "percent": percent
        })

    # ── Build PDF ──────────────────────────────────────────────────────────
    self.update_state(state="PROGRESS", meta={"step": "Assembling final PDF...", "percent": 88})
    doc.build(elements)

    # ── Upload to Cloudinary ───────────────────────────────────────────────
    filename = f"class_{result_class}_session{session_id}_term{term_id}.pdf"
    self.update_state(state="PROGRESS", meta={"step": "Uploading PDF...", "percent": 92})

    buffer.seek(0)
    try:
        upload_result = cloudinary.uploader.upload(
            buffer,
            resource_type="raw",
            public_id=f"pdfs/{filename}",
            overwrite=True,
            type="upload",
            access_mode="public",
        )
        download_url = upload_result["secure_url"]
        print(f"✅ Cloudinary upload success: {download_url}")

    except Exception as e:
        print(f"❌ Cloudinary upload failed: {str(e)}")
        pdf_dir = os.path.join(settings.MEDIA_ROOT, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        filepath = os.path.join(pdf_dir, filename)
        buffer.seek(0)
        with open(filepath, "wb") as f:
            f.write(buffer.read())
        download_url = f"{settings.MEDIA_URL}pdfs/{filename}"
        print(f"⚠️ Fell back to local: {download_url}")

    self.update_state(state="PROGRESS", meta={"step": "Done!", "percent": 100})

    return {"download_url": download_url, "filename": filename}


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


