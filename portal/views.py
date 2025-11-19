import io
from tkinter import Image
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum
import requests
from portal.models import Result_Portal
from sms.models import Term, Session, ExamType
from .utils import render_to_pdf
from .decorators import require_cbt_subscription, require_reportcard_subscription

from django.shortcuts import render
from portal.models import Result_Portal
from django.db.models import Avg, Sum

from django.db.models import F

from itertools import groupby
from operator import itemgetter

from reportlab.platypus import Image as RLImage  # <-- make sure this is reportlab's Image


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse

from .models import School, SchoolSubscription
from .forms import SubscriptionForm
from .decorators import require_feature


def superadmin_required(view):
    return user_passes_test(lambda u: u.is_superuser)(view)


@superadmin_required
def subscription_list(request):
    schools = School.objects.all().order_by("school_name")
    return render(request, "portal/subscription_list.html", {"schools": schools})

from django.shortcuts import render, get_object_or_404
from .models import SchoolSubscription
def subscription_detail(request, school_id):
    school = get_object_or_404(School, id=school_id)

    subscription, created = SchoolSubscription.objects.get_or_create(school=school)

    return render(request, "portal/subscription_detail.html", {
        "school": school,
        "subscription": subscription,
    })

@superadmin_required
def subscription_edit(request, school_id):
    school = get_object_or_404(School, id=school_id)
    subscription = school.subscription

    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect("portal:subscription_list")
    else:
        form = SubscriptionForm(instance=subscription)

    return render(request, "portal/subscription_edit.html", {
        "form": form,
        "school": school
    })


def payment_required(request):
    return render(request, "portal/payment_required.html")


@require_reportcard_subscription
def report_card_list(request):
    # Fetch all results, ordered by class and student
    all_results = Result_Portal.objects.select_related(
        'student', 'session', 'term'
    ).order_by('result_class', 'student__username')

    # Keep track of unique combinations to avoid duplicates
    seen = set()
    reports = []

    for res in all_results:
        key = (res.student_id, res.result_class, res.session_id, res.term_id)
        if key not in seen:
            seen.add(key)
            reports.append({
                'student': res.student,
                'result_class': res.result_class,
                'session': res.session,
                'term': res.term
            })

    context = {
        'reports': reports
    }
    return render(request, 'portal/report_card_list.html', context)

@require_reportcard_subscription
def my_report_cards(request):
    """
    Display all report cards for the logged-in student.
    """
    user = request.user

    # Fetch distinct term/class/session combinations for this student
    reports = (
        Result_Portal.objects.filter(student=user)
        .select_related('student', 'session', 'term')
        .values('result_class', 'session__id', 'term__id')
        .distinct()
    )

    # Prepare report objects for the template
    report_list = []
    for r in reports:
        report_list.append({
            'student': user,
            'result_class': r['result_class'],
            'session': Session.objects.get(id=r['session__id']),
            'term': Term.objects.get(id=r['term__id'])
        })

    context = {'reports': report_list}
    return render(request, 'portal/report_card_list.html', context)


from django.shortcuts import render
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import Result_Portal

EXAM_TYPES = ['CA', 'Mid-Term', 'Exam']


def report_card_detail(request, student_id, session_id, term_id):
    # Fetch all results for the student in this session & term
    results = Result_Portal.objects.filter(
        student_id=student_id,
        session_id=session_id,
        term_id=term_id
    ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('subject__title')

    if not results.exists():
        return HttpResponse("No results found.", status=404)

    student = results.first().student
    session = results.first().session
    term = results.first().term
    result_class = getattr(results.first(), 'result_class', '')

    # Get school max scores from the first result
    school = results.first().schools
    max_ca = school.max_ca_score if school else 10
    max_mid = school.max_midterm_score if school else 30
    max_exam = school.max_exam_score if school else 60

    # Total and average per student (normalized in model)
    student_total = sum([float(res.total_score) for res in results])
    student_average = round(student_total / len(results), 2) if results else 0

    # Class total, average, and position
    all_students_results = Result_Portal.objects.filter(
        result_class=result_class,
        session_id=session_id,
        term_id=term_id
    ).select_related('student')

    class_totals = {}
    for res in all_students_results:
        sid = res.student_id
        class_totals[sid] = class_totals.get(sid, 0) + float(res.total_score or 0)

    class_average = round(sum(class_totals.values()) / len(class_totals), 2) if class_totals else 0
    sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)
    position = next((i + 1 for i, (sid, total) in enumerate(sorted_totals) if sid == student_id), None)
    total_students = len(class_totals)

    context = {
        'student': student,
        'results': results,
        'result_class': result_class,
        'session': session,
        'term': term,
        'student_total': student_total,
        'student_average': student_average,
        'class_average': class_average,
        'position': position,
        'total_students': total_students,
        'max_ca': max_ca,
        'max_mid': max_mid,
        'max_exam': max_exam,
    }

    return render(request, 'portal/report_card_detail.html', context)


from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import Result_Portal
from .constants import GRADING_SCALE
from reportlab.lib.enums import TA_LEFT

EXAM_COLUMNS = ['CA', 'Mid-Term', 'Exam']  # Table headers

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.http import HttpResponse
import io
import requests
from reportlab.lib.styles import ParagraphStyle


def download_term_report_pdf(request, student_id, session_id, term_id):
    # --- Fetch results ---
    results = Result_Portal.objects.filter(
        student_id=student_id,
        session_id=session_id,
        term_id=term_id
    ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('subject__title')

    if not results.exists():
        return HttpResponse("No results found.", status=404)

    student = results.first().student
    school = results.first().schools
    session = results.first().session
    term = results.first().term
    result_class = getattr(results.first(), 'result_class', '')
    
     # Get school max scores from the first result
   
    # --- Class stats ---
    all_results = Result_Portal.objects.filter(
        result_class=result_class,
        session_id=session_id,
        term_id=term_id
    )

    student_total = sum(
        float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
        for r in results
    )
    num_subjects = len(results)
    student_average = round(student_total / num_subjects, 2) if num_subjects else 0

    class_totals = {}
    for r in all_results:
        sid = r.student_id
        total_score = float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
        class_totals[sid] = class_totals.get(sid, 0) + total_score

    sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)
    position = next((i + 1 for i, (sid, _) in enumerate(sorted_totals) if sid == student_id), None)
    total_students = len(class_totals)
    class_average = round(sum(class_totals.values()) / len(class_totals), 2) if class_totals else 0
    highest_in_class = max(class_totals.values(), default=0)
    lowest_in_class = min(class_totals.values(), default=0)
    final_grade = results[0].grade_letter if results else ''

    # --- PDF Setup ---
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.username}_term_report.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=25, leftMargin=25, rightMargin=25, bottomMargin=30)

    styles = getSampleStyleSheet()
    style_left = styles["Normal"]
    style_left.alignment = TA_LEFT
    style_center = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)

    elements = []

    # --- Header Section (Logo + Flex Layout) ---
    logo_img = None
    if school and getattr(school, 'logo', None):
        try:
            logo_data = io.BytesIO(requests.get(school.logo.url).content)
            logo_img = RLImage(logo_data, width=80, height=80)
        except Exception:
            pass

    school_name = f"<b>{getattr(school, 'school_name', 'Best Academy, Abuja')}</b>"
    school_motto = f"<i>{getattr(school, 'school_motto', 'Motto: Knowledge for Excellence')}</i>"
    school_address = f"{getattr(school, 'school_address', 'Tunga')}"

    school_details = [
        Paragraph(school_name, ParagraphStyle(name='SchoolName', fontSize=14, alignment=TA_LEFT)),
        Paragraph(school_motto, ParagraphStyle(name='SchoolMotto', fontSize=10, alignment=TA_LEFT)),
        Paragraph(school_address, ParagraphStyle(name='SchoolAddress', fontSize=9, alignment=TA_LEFT))
    ]

    header_table = Table([[logo_img if logo_img else "", school_details]], colWidths=[90, 400])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # --- Title ---
    elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
    elements.append(Spacer(1, 10))

    # --- Student Info (Grid Table) ---
    student_info_data = [
        [f"Student Name: {student.username}", f"Class: {result_class}", f"Term: {term.name}"],
        [f"Session: {session.name}", f"No. in Class: {total_students}", f"Position: {position} of {total_students}"],
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

    max_ca = school.max_ca_score if school else 10
    max_mid = school.max_midterm_score if school else 30
    max_exam = school.max_exam_score if school else 60

    # --- Subject Table (with Grid) ---
    header_style = ParagraphStyle(name='HeaderStyle', fontName='Helvetica-Bold', fontSize=7, alignment=1)

    # Use f-strings to insert actual max values
    headers = [
        "Subject",
        f"CA<br/>({max_ca})",
        f"Midterm<br/>({max_mid})",
        f"Exam<br/>({max_exam})",
        "Total",
        "Per<br/>(%)",
        "Grade",
        "Class<br/>Ave",
        "POS",
        "Out<br/>Of",
        "High<br/>In<br/>Class",
        "Low<br/>In<br/>Class",
        "Remark"
    ]

    table_data = [[Paragraph(h, header_style) for h in headers]]



    for r in results:
        ca = float(r.ca_score or 0)
        mid = float(r.midterm_score or 0)
        exam = float(r.exam_score or 0)
        total = ca + mid + exam
        max_total = sum([10 if ca > 0 else 0, 30 if mid > 0 else 0, 60 if exam > 0 else 0])
        percentage = round((total / max_total) * 100) if max_total else 0

        subject_results = all_results.filter(subject=r.subject)
        class_avg = round(sum(
            float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
            for s in subject_results
        ) / len(subject_results), 2) if subject_results else 0
        high_in_class = max([
            float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
            for s in subject_results
        ], default=0)
        low_in_class = min([
            float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
            for s in subject_results
        ], default=0)
        pos_sorted = sorted([
            (s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
            for s in subject_results
        ], key=lambda x: x[1], reverse=True)
        pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == student_id), None)

        row = [
            r.subject.title, str(ca), str(mid), str(exam), str(total),
            f"{percentage}%", r.grade_letter, str(class_avg), str(pos),
            str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark
        ]
        table_data.append([Paragraph(str(x), style_center) for x in row])

    page_width = A4[0] - doc.leftMargin - doc.rightMargin
    col_fractions = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
    col_widths = [page_width * frac for frac in col_fractions]

    result_table = Table(table_data, colWidths=col_widths)
    result_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements += [result_table, Spacer(1, 15)]

    # --- Grading Scale ---
    elements.append(Paragraph("<b>GRADING SCALE</b>", style_left))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39", style_left))
    elements.append(Spacer(1, 15))

    # --- Comments & Signatures ---
    elements.append(Paragraph("<b>Teacher’s Comment:</b> ____________________________________________", style_left))
    elements.append(Spacer(1, 8))
    if school and getattr(school, 'teacher_signature', None):
        try:
            sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
            sig_img = RLImage(sig_data, width=100, height=40)
            elements.append(sig_img)
        except Exception:
            pass

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Principal’s Comment:</b> ____________________________________________", style_left))
    elements.append(Spacer(1, 8))
    if school and getattr(school, 'principal_signature', None):
        try:
            sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
            sig_img = RLImage(sig_data, width=100, height=40)
            elements.append(sig_img)
        except Exception:
            pass

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>End of Report</b>", style_center))

    doc.build(elements)
    return response


# download per class
@require_reportcard_subscription
def class_report_list(request):
    sessions = Session.objects.all()
    terms = Term.objects.all()
    classes = Result_Portal.objects.values_list('result_class', flat=True).distinct()

    context = {
        'sessions': sessions,
        'terms': terms,
        'classes': classes,
    }
    return render(request, 'portal/class_report_list.html', context)


def class_report_detail(request, result_class, session_id, term_id):
    results = Result_Portal.objects.filter(
        result_class=result_class,
        session_id=session_id,
        term_id=term_id
    ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('student__username', 'subject__title')

    if not results.exists():
        return HttpResponse("No results found for this class.", status=404)

    # Get school max scores from the first result
    school = results.first().schools
    max_ca = school.max_ca_score if school else 10
    max_mid = school.max_midterm_score if school else 30
    max_exam = school.max_exam_score if school else 60
    # Group results by student
    students = {}
    for res in results:
        sid = res.student_id
        if sid not in students:
            students[sid] = {'student': res.student, 'records': []}
        students[sid]['records'].append(res)

    session = results.first().session
    term = results.first().term
    context = {
        'students': students,
        'result_class': result_class,
        'session': session,
        'term': term,
        'max_ca': max_ca,
        'max_mid': max_mid,
        'max_exam': max_exam,
    }
    return render(request, 'portal/class_report_detail.html', context)


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def download_class_reports_pdf(request, result_class, session_id, term_id):

    # --- Fetch all results ---
    all_results = Result_Portal.objects.filter(
        result_class=result_class,
        session_id=session_id,
        term_id=term_id
    ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('student__username', 'subject__title')

    if not all_results.exists():
        return HttpResponse("No results found for this class.", status=404)

    # --- Group by student ---
    students = {}
    for res in all_results:
        sid = res.student_id
        if sid not in students:
            students[sid] = {
                'student': res.student,
                'records': [],
                'school': res.schools,
                'session': res.session,
                'term': res.term
            }
        students[sid]['records'].append(res)

    # --- Compute totals for ranking ---
    class_totals = {}
    for res in all_results:
        sid = res.student_id
        total = float(res.ca_score or 0) + float(res.midterm_score or 0) + float(res.exam_score or 0)
        class_totals[sid] = class_totals.get(sid, 0) + total
    sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)

    # --- PDF Setup ---
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="class_{result_class}_term_reports.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=25, leftMargin=25, rightMargin=25, bottomMargin=30)

    styles = getSampleStyleSheet()
    style_left = styles["Normal"]
    style_left.alignment = TA_LEFT
    style_center = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)

    elements = []

    # --- Generate report for each student ---
    for sid, data in students.items():
        student = data['student']
        records = data['records']
        school = data['school']
        session = data['session']
        term = data['term']

        # --- Student stats ---
        num_subjects = len(records)
        student_total = sum(
            float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
            for r in records
        )
        student_average = round(student_total / num_subjects, 2) if num_subjects else 0
        total_students = len(class_totals)
        class_average = round(sum(class_totals.values()) / len(class_totals), 2)
        position = next((i + 1 for i, (stud_id, _) in enumerate(sorted_totals) if stud_id == sid), None)
        highest_in_class = max(class_totals.values(), default=0)
        lowest_in_class = min(class_totals.values(), default=0)
        final_grade = records[0].grade_letter if records else ""

        # --- Header Section (Logo + School Info in Flex Layout) ---
        logo_img = None
        if school and getattr(school, 'logo', None):
            try:
                logo_data = io.BytesIO(requests.get(school.logo.url).content)
                logo_img = RLImage(logo_data, width=80, height=80)
            except Exception:
                pass

        # School details
        school_name = f"<b>{school.school_name or 'Best Academy, Abuja'}</b>"
        school_motto = f"<i>{school.school_motto or 'Motto: Knowledge for Excellence'}</i>"
        school_address = f"{school.school_address or 'Tunga'}"

        school_details = [
            Paragraph(school_name, ParagraphStyle(name='SchoolName', fontSize=14, alignment=TA_LEFT)),
            Paragraph(school_motto, ParagraphStyle(name='SchoolMotto', fontSize=10, alignment=TA_LEFT)),
            Paragraph(school_address, ParagraphStyle(name='SchoolAddress', fontSize=9, alignment=TA_LEFT))
        ]

        # Simulate flexbox with table (Logo | School Info)
        header_table = Table(
            [[logo_img if logo_img else "", school_details]],
            colWidths=[90, 400]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # --- Title ---
        elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
        elements.append(Spacer(1, 10))

        # --- Student Info (with Grid Borders) ---
        student_info_data = [
            [f"Student Name: {student.username}", f"Class: {result_class}", f"Term: {term.name}"],
            [f"Session: {session.name}", f"No. in Class: {total_students}", f"Position: {position} of {total_students}"],
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

        max_ca = school.max_ca_score if school else 10
        max_mid = school.max_midterm_score if school else 30
        max_exam = school.max_exam_score if school else 60

        # --- Subject Table (with Grid) ---
        header_style = ParagraphStyle(name='HeaderStyle', fontName='Helvetica-Bold', fontSize=7, alignment=1)
        # Use f-strings to insert actual max values
        headers = [
            "Subject",
            f"CA<br/>({max_ca})",
            f"Midterm<br/>({max_mid})",
            f"Exam<br/>({max_exam})",
            "Total",
            "Per<br/>(%)",
            "Grade",
            "Class<br/>Ave",
            "POS",
            "Out<br/>Of",
            "High<br/>In<br/>Class",
            "Low<br/>In<br/>Class",
            "Remark"
        ]

        table_data = [[Paragraph(h, header_style) for h in headers]]

        for r in records:
            ca = float(r.ca_score or 0)
            mid = float(r.midterm_score or 0)
            exam = float(r.exam_score or 0)
            total = ca + mid + exam
            max_total = sum([10 if ca > 0 else 0, 30 if mid > 0 else 0, 60 if exam > 0 else 0])
            percentage = round((total / max_total) * 100) if max_total else 0

            subject_results = all_results.filter(subject=r.subject)
            class_avg = round(sum(
                float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
                for s in subject_results
            ) / len(subject_results), 2) if subject_results else 0
            high_in_class = max([
                float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
                for s in subject_results
            ], default=0)
            low_in_class = min([
                float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
                for s in subject_results
            ], default=0)
            pos_sorted = sorted([
                (s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
                for s in subject_results
            ], key=lambda x: x[1], reverse=True)
            pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == sid), None)

            row = [
                r.subject.title, str(ca), str(mid), str(exam), str(total),
                f"{percentage}%", r.grade_letter, str(class_avg), str(pos),
                str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark
            ]
            table_data.append([Paragraph(str(x), style_center) for x in row])

        page_width = A4[0] - doc.leftMargin - doc.rightMargin
        col_fractions = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
        col_widths = [page_width * frac for frac in col_fractions]

        result_table = Table(table_data, colWidths=col_widths)
        result_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements += [result_table, Spacer(1, 15)]

        # --- Grading Scale ---
        elements.append(Paragraph("<b>GRADING SCALE</b>", style_left))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39", style_left))
        elements.append(Spacer(1, 15))

        # --- Comments & Signatures ---
        elements.append(Paragraph("<b>Teacher’s Comment:</b> ____________________________________________", style_left))
        elements.append(Spacer(1, 8))
        if school and getattr(school, 'teacher_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
                sig_img = RLImage(sig_data, width=100, height=40)
                elements.append(sig_img)
            except Exception:
                pass

        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>Principal’s Comment:</b> ____________________________________________", style_left))
        elements.append(Spacer(1, 8))
        if school and getattr(school, 'principal_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                sig_img = RLImage(sig_data, width=100, height=40)
                elements.append(sig_img)
            except Exception:
                pass

        elements.append(Spacer(1, 20))
        elements.append(Paragraph("<b>End of Report</b>", style_center))
        elements.append(PageBreak())

    doc.build(elements)
    return response



# bulk upload
# reports/views.py
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse
from django.forms import formset_factory

from sms.models import Session, Term, Courses  # adjust imports to your project layout
from quiz.models import Course, School, CourseGrade
from teacher.models import Teacher
from .models import Result_Portal
from .forms import ResultRowForm


RESULT_FIELDS = ['ca_score', 'midterm_score', 'exam_score', 'total_score']


def _get_teacher_for_request(user):
    """Return the Teacher instance for the logged-in user or raise 404."""
    return get_object_or_404(Teacher, user=user)


@require_reportcard_subscription
@login_required
def load_bulk_entry_page(request):
    """
    Landing page where teacher selects class, subject, term, session,
    or if params provided, loads the table immediately.
    """
    teacher = _get_teacher_for_request(request.user)

    # Classes and subjects the teacher teaches
    classes = teacher.classes_taught.all()
    subjects = teacher.subjects_taught.all()

    # Sessions and terms for the teacher's school
    sessions = Session.objects.filter(school=teacher.school)
    terms = Term.objects.filter(school=teacher.school)

    context = {
        "classes": classes,
        "subjects": subjects,
        "sessions": sessions,
        "terms": terms,
    }

    # template will show a form to choose class/subject/term/session
    return render(request, "portal/select_entry_params.html", context)




@require_reportcard_subscription
@login_required
def enter_results_for_class_subject(request, class_id, subject_id, session_id, term_id):
    """
    Render table of students for a class/subject and handle POST to save all results.
    Safely creates or updates Result_Portal entries using update_or_create.
    Enforces school-specific max scores for CA, Midterm, and Exam.
    """
    teacher = _get_teacher_for_request(request.user)

    # Fetch class, course, session, term
    class_obj = get_object_or_404(CourseGrade, id=class_id)
    course_obj = get_object_or_404(Courses, id=subject_id)
    session = get_object_or_404(Session, id=session_id)
    term = get_object_or_404(Term, id=term_id)

    # --- Robust permission checks ---
    teacher_classes = teacher.classes_taught.all()
    teacher_subjects = teacher.subjects_taught.all()

    if not any(c.id == class_obj.id for c in teacher_classes):
        return HttpResponseForbidden("You are not assigned to this class.")

    if not any(s.id == course_obj.id for s in teacher_subjects):
        return HttpResponseForbidden("You are not assigned to this subject.")

    # Fetch students in the class
    students = class_obj.students.all().order_by('id')

    # School max score parameters
    school = getattr(class_obj, 'schools', None)
    max_ca = getattr(school, 'max_ca_score', Decimal('10.0')) if school else Decimal('10.0')
    max_midterm = getattr(school, 'max_midterm_score', Decimal('30.0')) if school else Decimal('30.0')
    max_exam = getattr(school, 'max_exam_score', Decimal('60.0')) if school else Decimal('60.0')

    # Formset for bulk entry
    ResultFormset = formset_factory(ResultRowForm, extra=0)

    if request.method == "POST":
        formset = ResultFormset(request.POST)
        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    student_id = int(form.cleaned_data["student_id"])
                    ca = min(Decimal(form.cleaned_data.get("ca_score") or 0), max_ca)
                    mid = min(Decimal(form.cleaned_data.get("midterm_score") or 0), max_midterm)
                    exam = min(Decimal(form.cleaned_data.get("exam_score") or 0), max_exam)
                    total = ca + mid + exam

                    # Safely create or update result
                    Result_Portal.objects.update_or_create(
                        student_id=student_id,
                        subject=course_obj,
                        term=term,
                        session=session,
                        result_class=class_obj.name,
                        defaults={
                            'schools': school,
                            'ca_score': ca,
                            'midterm_score': mid,
                            'exam_score': exam,
                            'total_score': total
                        }
                    )

            return redirect(reverse('portal:enter_results', kwargs={
                'class_id': class_id,
                'subject_id': subject_id,
                'session_id': session_id,
                'term_id': term_id
            }))
        else:
            forms_with_students = zip(formset.forms, students)
            return render(request, "portal/enter_results.html", {
                "formset": formset,
                "forms_with_students": forms_with_students,
                "class_obj": class_obj,
                "subject_obj": course_obj,
                "session": session,
                "term": term,
                "max_ca": max_ca,
                "max_midterm": max_midterm,
                "max_exam": max_exam,
            })

    # GET: prepare initial data for formset
    existing_results = Result_Portal.objects.filter(
        student_id__in=[s.id for s in students],
        subject=course_obj,
        session=session,
        term=term,
        result_class=class_obj.name
    )
    existing_by_student = {r.student_id: r for r in existing_results}

    initial_data = []
    for s in students:
        existing = existing_by_student.get(s.id)
        initial_data.append({
            'student_id': s.id,
            'existing_result_id': existing.id if existing else '',
            'ca_score': existing.ca_score if existing else Decimal('0.00'),
            'midterm_score': existing.midterm_score if existing else Decimal('0.00'),
            'exam_score': existing.exam_score if existing else Decimal('0.00'),
        })

    formset = ResultFormset(initial=initial_data)
    forms_with_students = zip(formset.forms, students)

    return render(request, "portal/enter_results.html", {
        "formset": formset,
        "forms_with_students": forms_with_students,
        "class_obj": class_obj,
        "subject_obj": course_obj,
        "session": session,
        "term": term,
        "max_ca": max_ca,
        "max_midterm": max_midterm,
        "max_exam": max_exam,
    })



# @login_required
# def enter_results_for_class_subject(request, class_id, subject_id, session_id, term_id):
#     """
#     Render table of students for a class/subject and handle POST to save all results.
#     Safely creates or updates Result_Portal entries using update_or_create.
#     """
#     teacher = _get_teacher_for_request(request.user)

#     # Fetch class, course, session, term
#     class_obj = get_object_or_404(CourseGrade, id=class_id)
#     course_obj = get_object_or_404(Courses, id=subject_id)
#     session = get_object_or_404(Session, id=session_id)
#     term = get_object_or_404(Term, id=term_id)

#     # --- Robust permission checks ---
#     teacher_classes = teacher.classes_taught.all()
#     teacher_subjects = teacher.subjects_taught.all()

#     if not any(c.id == class_obj.id for c in teacher_classes):
#         return HttpResponseForbidden("You are not assigned to this class.")

#     if not any(s.id == course_obj.id for s in teacher_subjects):
#         return HttpResponseForbidden("You are not assigned to this subject.")

#     # Fetch students in the class
#     students = class_obj.students.all().order_by('id')

#     # Formset for bulk entry
#     ResultFormset = formset_factory(ResultRowForm, extra=0)

#     if request.method == "POST":
#         formset = ResultFormset(request.POST)
#         if formset.is_valid():
#             with transaction.atomic():
#                 for form in formset:
#                     student_id = int(form.cleaned_data["student_id"])
#                     ca = Decimal(form.cleaned_data.get("ca_score") or 0)
#                     mid = Decimal(form.cleaned_data.get("midterm_score") or 0)
#                     exam = Decimal(form.cleaned_data.get("exam_score") or 0)
#                     total = ca + mid + exam

#                     # Safely create or update result
#                     Result_Portal.objects.update_or_create(
#                         student_id=student_id,
#                         subject=course_obj,
#                         term=term,
#                         session=session,
#                         result_class=class_obj.name,  # VERY IMPORTANT
#                         defaults={
#                             'schools': getattr(class_obj, 'schools', None),
#                             'ca_score': ca,
#                             'midterm_score': mid,
#                             'exam_score': exam,
#                             'total_score': total
#                         }
#                     )


#             # Redirect to same page
#             return redirect(reverse('portal:enter_results', kwargs={
#                 'class_id': class_id,
#                 'subject_id': subject_id,
#                 'session_id': session_id,
#                 'term_id': term_id
#             }))
#         else:
#             forms_with_students = zip(formset.forms, students)
#             return render(request, "portal/enter_results.html", {
#                 "formset": formset,
#                 "forms_with_students": forms_with_students,
#                 "class_obj": class_obj,
#                 "subject_obj": course_obj,
#                 "session": session,
#                 "term": term,
#             })

#     # GET: prepare initial data for formset
#     existing_results = Result_Portal.objects.filter(
#         student_id__in=[s.id for s in students],
#         subject=course_obj,
#         session=session,
#         term=term,
#         result_class=class_obj.name
#     )
#     existing_by_student = {r.student_id: r for r in existing_results}

#     initial_data = []
#     for s in students:
#         existing = existing_by_student.get(s.id)
#         initial_data.append({
#             'student_id': s.id,
#             'existing_result_id': existing.id if existing else '',
#             'ca_score': existing.ca_score if existing else Decimal('0.00'),
#             'midterm_score': existing.midterm_score if existing else Decimal('0.00'),
#             'exam_score': existing.exam_score if existing else Decimal('0.00'),
#         })

#     formset = ResultFormset(initial=initial_data)
#     forms_with_students = zip(formset.forms, students)

#     return render(request, "portal/enter_results.html", {
#         "formset": formset,
#         "forms_with_students": forms_with_students,
#         "class_obj": class_obj,
#         "subject_obj": course_obj,
#         "session": session,
#         "term": term,
#     })
