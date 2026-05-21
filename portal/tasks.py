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


