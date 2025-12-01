import io
# from tkinter import Image
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum
import requests
from portal.models import Result_Portal
from sms.models import Term, Session, ExamType
from users.models import NewUser
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
from .models import Result_Portal,StudentBehaviorRecord


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

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.http import HttpResponse
import io
import requests
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.flowables import HRFlowable


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
            Spacer(1, 8),  # 4 points of vertical space
            Paragraph(school_motto, ParagraphStyle(name='SchoolMotto', fontSize=10, alignment=TA_LEFT)),
            Spacer(1, 8),  # 2 points of vertical space
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

    
    hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
    elements.append(hr)

    # --- Title ---
    elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
    elements.append(Spacer(1, 10))

    # --- Student Info (Grid Table) ---
    student_info_data = [
        [f"Name: {student.first_name} {student.last_name}", f"Class: {result_class}", f"Term: {term.name}"],
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
        "Per (%)",
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
            f"{percentage}", r.grade_letter, str(class_avg), str(pos),
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

    elements.append(Paragraph(f"<b>Number of Subjects:</b> {num_subjects}", style_left))
    elements.append(Spacer(1, 5))  # optional spacing after


    # --- Grading Scale ---
    grading_text = "<b>GRADING SCALE</b>: A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39"
    elements.append(Paragraph(grading_text, style_left))
    # elements.append(Paragraph("<b>GRADING SCALE</b>":"A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39", style_left))
    elements.append(Spacer(1, 15))

    elements.append(hr)
     
    # --- Fetch behavior for 3rd term ---
    if term.name.lower().strip() in ["3rd term","3rd-term","3rd_term","3rd" ,"third term",'third-term','third_term',"third"]:
        behavior = StudentBehaviorRecord.objects.filter(
            student_id=student_id,
            session_id=session_id,
            term_id=term_id
        ).first()

        if behavior:
            # --- Psychomotor Table ---
            psychomotor_data = [["Default Psychomotor", "Rating"]]
            psychomotor_data += [
                ["Handwriting", behavior.handwriting],
                ["Games", behavior.games],
                ["Sports", behavior.sports],
                ["Drawing & Painting", behavior.drawing_painting],
                ["Crafts", behavior.crafts]
            ]
            psychomotor_table = Table(
                psychomotor_data,
                colWidths=[120, 40],
                rowHeights=[15] + [12]*5  # header = 15, body = 12
            )
            psychomotor_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('ALIGN', (1,1), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))

            # --- Affective Table ---
            affective_data = [["Default Affective Traits", "Rating"]]
            affective_data += [
                ["Punctuality", behavior.punctuality],
                ["Attendance", behavior.attendance],
                ["Reliability", behavior.reliability],
                ["Neatness", behavior.neatness],
                ["Politeness", behavior.politeness],
                ["Honesty", behavior.honesty],
                ["Relationship w/ Students", behavior.relationship_with_students],
                ["Self Control", behavior.self_control],
                ["Attentiveness", behavior.attentiveness],
                ["Perseverance", behavior.perseverance]
            ]
            affective_table = Table(
                affective_data,
                colWidths=[150, 40],
                rowHeights=[15] + [12]*10  # header = 15, body = 12
            )
            affective_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('ALIGN', (1,1), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))

            # --- Scale Table ---
            scale_data = [["SCALE"]]
            scale_data += [["5 - Excellent"], ["4 - Good"], ["3 - Fair"], ["2 - Poor"], ["1 - Very Poor"]]
            scale_table = Table(
                scale_data,
                colWidths=[100],
                rowHeights=[15] + [12]*5  # header = 15, body = 12
            )
            scale_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('ALIGN', (0,1), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))

            # --- Combine tables horizontally ---
            combined = Table([[psychomotor_table, affective_table, scale_table]], colWidths=[160, 200, 120])
            combined.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))

            elements.append(combined)
            elements.append(Spacer(1, 10))  # tighter spacing
    
            elements.append(hr)

    # --- Comments & Signatures ---
    if school and getattr(school, 'teacher_signature', None):
        try:
            sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
            sig_img = RLImage(sig_data, width=100, height=40)
            elements.append(sig_img)
        except Exception:
            pass

        elements.append(Spacer(1, 10))

        if behavior:
            # append form teacher and principal comments
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}", style_left))
            elements.append(Paragraph(f"<b>Form Teacher Comment:</b> {behavior.form_teacher_comment}", style_left))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"<b>Principal's Remark:</b> {behavior.principal_comment}", style_left))

            elements.append(hr)

    if school and getattr(school, 'principal_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                sig_img = RLImage(sig_data, width=100, height=40)
                elements.append(sig_img)
            except Exception:
                pass
    
    doc.build(elements)
    return response


def class_report_list(request):
    # Fetch distinct combinations
    reports = Result_Portal.objects.values(
        'result_class',
        'session_id',
        'session__name',
        'term_id',
        'term__name'
    ).distinct()

    return render(request, 'portal/class_report_list.html', {
        'reports': reports
    })


def class_report_detail(request, result_class, session_id, term_id):
    # Fetch session and term objects
    session = get_object_or_404(Session, id=session_id)
    term = get_object_or_404(Term, id=term_id)

    # Filter results using case-insensitive match
    results = Result_Portal.objects.filter(
        result_class__iexact=result_class.strip(),
        session=session,
        term=term
    ).select_related('student', 'subject', 'schools').order_by('student__username', 'subject__title')

    if not results.exists():
        # If no results, return a friendly message
        context = {
            'students': {},
            'result_class': result_class,
            'session': session,
            'term': term,
            'max_ca': 10,
            'max_mid': 30,
            'max_exam': 60,
            'message': "No results found for this class for the selected session and term."
        }
        return render(request, 'portal/class_report_detail.html', context)

    # Safe: results exist
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

    context = {
        'students': students,
        'result_class': results.first().result_class,
        'session': session,
        'term': term,
        'max_ca': max_ca,
        'max_mid': max_mid,
        'max_exam': max_exam,
        'message': None
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
            Spacer(1, 8),  # 4 points of vertical space
            Paragraph(school_motto, ParagraphStyle(name='SchoolMotto', fontSize=10, alignment=TA_LEFT)),
            Spacer(1, 8),  # 2 points of vertical space
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

        hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
        elements.append(hr)


        # --- Title ---
        elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
        elements.append(Spacer(1, 10))

        # --- Student Info (with Grid Borders) ---
        full_name = f"{student.first_name or ''} {student.last_name or ''}".strip()

        student_info_data = [
            [f"Name: {student.first_name} {student.last_name}", f"Class: {result_class}", f"Term: {term.name}"],
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
            "Per (%)",
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
                f"{percentage}", r.grade_letter, str(class_avg), str(pos),
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

        behavior = StudentBehaviorRecord.objects.filter(
           
            session_id=session_id,
            term_id=term_id
        ).first()

        elements.append(hr)

        if behavior:
            # append form teacher and principal comments
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}", style_left))

        
        elements.append(hr)

        # --- Comments & Signatures ---
        if school and getattr(school, 'teacher_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
                sig_img = RLImage(sig_data, width=100, height=40)
                elements.append(sig_img)
            except Exception:
                pass

        elements.append(Spacer(1, 10))

        if school and getattr(school, 'principal_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                sig_img = RLImage(sig_data, width=100, height=40)
                elements.append(sig_img)
            except Exception:
                pass

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


from django.contrib import messages

@require_reportcard_subscription
@login_required
def enter_results_for_class_subject(request, class_id, subject_id, session_id, term_id):
    """
    Render table of students for a class/subject and handle POST to save all results.
    Uses update_or_create to save results safely.
    """
    teacher = _get_teacher_for_request(request.user)
    # Fetch class, course, session, term
    class_obj = get_object_or_404(CourseGrade, id=class_id)
    course_obj = get_object_or_404(Courses, id=subject_id)
    session = get_object_or_404(Session, id=session_id)
    term = get_object_or_404(Term, id=term_id)

    # Fetch all students for this class
    students = class_obj.students.all().order_by('id')

    # School max scores
    school = getattr(class_obj, 'schools', None)
    max_ca = getattr(school, 'max_ca_score', Decimal('10.0')) if school else Decimal('10.0')
    max_midterm = getattr(school, 'max_midterm_score', Decimal('30.0')) if school else Decimal('30.0')
    max_exam = getattr(school, 'max_exam_score', Decimal('60.0')) if school else Decimal('60.0')

    # Formset
    ResultFormset = formset_factory(ResultRowForm, extra=0)

    # GET: prepare initial data
    existing_results = Result_Portal.objects.filter(
        student_id__in=students.values_list('id', flat=True),
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

    if request.method == "POST":
        formset = ResultFormset(request.POST)
        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    student_id = form.cleaned_data.get('student_id')
                    ca = min(Decimal(form.cleaned_data.get('ca_score') or 0), max_ca)
                    mid = min(Decimal(form.cleaned_data.get('midterm_score') or 0), max_midterm)
                    exam = min(Decimal(form.cleaned_data.get('exam_score') or 0), max_exam)
                    total = ca + mid + exam

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

            # Add success message
            messages.success(request, "All results have been saved successfully!")

            # Redirect to same page to show message
            return redirect(reverse('portal:enter_results', kwargs={
                'class_id': class_id,
                'subject_id': subject_id,
                'session_id': session_id,
                'term_id': term_id
            }))
        else:
            # Formset invalid: show errors
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
    else:
        # GET: display formset
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


# @require_reportcard_subscription
# @login_required
# def enter_results_for_class_subject(request, class_id, subject_id, session_id, term_id):
#     """
#     Render table of students for a class/subject and handle POST to save all results.
#     Safely creates or updates Result_Portal entries using update_or_create.
#     Enforces school-specific max scores for CA, Midterm, and Exam.
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

#     # Fetch students in the class
#     students = class_obj.students.all().order_by('id')

#     # School max score parameters
#     school = getattr(class_obj, 'schools', None)
#     max_ca = getattr(school, 'max_ca_score', Decimal('10.0')) if school else Decimal('10.0')
#     max_midterm = getattr(school, 'max_midterm_score', Decimal('30.0')) if school else Decimal('30.0')
#     max_exam = getattr(school, 'max_exam_score', Decimal('60.0')) if school else Decimal('60.0')

#     # Formset for bulk entry
#     ResultFormset = formset_factory(ResultRowForm, extra=0)

#     if request.method == "POST":
#         formset = ResultFormset(request.POST)
#         if formset.is_valid():
#             with transaction.atomic():
#                 for form in formset:
#                     student_id = int(form.cleaned_data["student_id"])
#                     ca = min(Decimal(form.cleaned_data.get("ca_score") or 0), max_ca)
#                     mid = min(Decimal(form.cleaned_data.get("midterm_score") or 0), max_midterm)
#                     exam = min(Decimal(form.cleaned_data.get("exam_score") or 0), max_exam)
#                     total = ca + mid + exam

#                     # Safely create or update result
#                     Result_Portal.objects.update_or_create(
#                         student_id=student_id,
#                         subject=course_obj,
#                         term=term,
#                         session=session,
#                         result_class=class_obj.name,
#                         defaults={
#                             'schools': school,
#                             'ca_score': ca,
#                             'midterm_score': mid,
#                             'exam_score': exam,
#                             'total_score': total
#                         }
#                     )

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
#                 "max_ca": max_ca,
#                 "max_midterm": max_midterm,
#                 "max_exam": max_exam,
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
#         "max_ca": max_ca,
#         "max_midterm": max_midterm,
#         "max_exam": max_exam,
#     })


# portal/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from teacher.models import Teacher
from quiz.models import CourseGrade
from portal.models import StudentBehaviorRecord
from portal.forms import StudentBehaviorRecordForm
from django.contrib import messages


# @login_required
# def form_teacher_dashboard(request):
#     teacher = get_object_or_404(Teacher, user=request.user)

#     classes = CourseGrade.objects.filter(
#         form_teacher=teacher,
#         is_active=True
#     ).select_related('session', 'term').prefetch_related('students')

#     return render(request, "portal/form_teacher_dashboard.html", {
#         "classes": classes,
#     })

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from django.conf import settings

# client = OpenAI(api_key="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")


client = OpenAI(api_key=settings.OPENAI_API_KEY)


@login_required(login_url='teacher:teacher_login')
def form_teacher_dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    school = teacher.school

    # ---- FILTER OPTIONS ----
    sessions = Session.objects.filter(school=school)
    terms = Term.objects.filter(school=school)

    # ✅ Only classes associated with this teacher
    classes = teacher.classes_taught.all()

    # ---- SELECTED FILTERS ----
    selected_session_id = request.GET.get("session")
    selected_term_id = request.GET.get("term")
    selected_class_id = request.GET.get("class")

    selected_session = sessions.filter(id=selected_session_id).first() if selected_session_id else None
    selected_term = terms.filter(id=selected_term_id).first() if selected_term_id else None
    selected_class = classes.filter(id=selected_class_id).first() if selected_class_id else None

    records = []

    if selected_session and selected_term and selected_class:
        # ---- LOAD RECORDS ----
        records = StudentBehaviorRecord.objects.filter(
            session=selected_session,
            term=selected_term,
            student__course_grades=selected_class
        ).select_related("student").distinct()

        # ---- HANDLE SAVE (POST) ----
        if request.method == "POST":
            for r in records:
                # Comment
                comment_field = f"comment_{r.student.id}"
                new_comment = request.POST.get(comment_field)
                if new_comment is not None:
                    r.form_teacher_comment = new_comment

                # Psychomotor
                r.handwriting = request.POST.get(f"handwriting_{r.student.id}", 0)
                r.games = request.POST.get(f"games_{r.student.id}", 0)
                r.sports = request.POST.get(f"sports_{r.student.id}", 0)
                r.drawing_painting = request.POST.get(f"drawing_{r.student.id}", 0)
                r.crafts = request.POST.get(f"crafts_{r.student.id}", 0)

                # Affective
                r.punctuality = request.POST.get(f"punctuality_{r.student.id}", 0)
                r.attendance = request.POST.get(f"attendance_{r.student.id}", 0)
                r.reliability = request.POST.get(f"reliability_{r.student.id}", 0)
                r.neatness = request.POST.get(f"neatness_{r.student.id}", 0)
                r.politeness = request.POST.get(f"politeness_{r.student.id}", 0)
                r.honesty = request.POST.get(f"honesty_{r.student.id}", 0)
                r.relationship_with_students = request.POST.get(f"relationship_{r.student.id}", 0)
                r.self_control = request.POST.get(f"self_control_{r.student.id}", 0)
                r.attentiveness = request.POST.get(f"attentive_{r.student.id}", 0)
                r.perseverance = request.POST.get(f"perseverance_{r.student.id}", 0)

                r.save()

            messages.success(request, "Comments and scores saved successfully.")
            return redirect(
                f"{request.path}?session={selected_session.id}&term={selected_term.id}&class={selected_class.id}"
            )

        # ---- ATTACH RESULT DETAILS ----
        for r in records:
            student_results = Result_Portal.objects.filter(
                student=r.student,
                session=selected_session,
                term=selected_term,
            ).select_related("subject")

            r.results = student_results
            if student_results.exists():
                total = sum(float(x.total_score or 0) for x in student_results)
                avg = total / student_results.count()
                r.total_score = total
                r.average_score = round(avg, 2)
                r.final_grade = student_results.first().grade_letter
            else:
                r.total_score = None
                r.average_score = None
                r.final_grade = None

    context = {
        "sessions": sessions,
        "terms": terms,
        "classes": classes,   # only teacher classes
        "records": records,
        "selected_session": selected_session.id if selected_session else "",
        "selected_term": selected_term.id if selected_term else "",
        "selected_class": selected_class.id if selected_class else "",
    }

    return render(request, "portal/form_teacher_dashboard.html", context)


# -----------------------------
# AI COMMENT (single student)
# -----------------------------

@login_required
@login_required(login_url='teacher:teacher_login')
def generate_form_teacher_comment(request, student_id):
    student = get_object_or_404(NewUser, id=student_id)

    session_id = request.GET.get("session")
    term_id = request.GET.get("term")
    class_id = request.GET.get("class")

    # ---- VALIDATE FILTERS ----
    if not session_id or not session_id.isdigit():
        return JsonResponse({"comment": "Invalid session ID."})

    if not term_id or not term_id.isdigit():
        return JsonResponse({"comment": "Invalid term ID."})

    if not class_id or not class_id.isdigit():
        return JsonResponse({"comment": "Invalid class ID."})

    # ---- GET BEHAVIOR RECORD ----
    behavior_record = StudentBehaviorRecord.objects.filter(
        student=student,
        session_id=int(session_id),
        term_id=int(term_id),
        student__course_grades__id=int(class_id)
    ).first()

    # If behavior record exists, pull latest values
    if behavior_record:
        hw = request.GET.get(f"handwriting_{student.id}", behavior_record.handwriting)
        games = request.GET.get(f"games_{student.id}", behavior_record.games)
        sports = request.GET.get(f"sports_{student.id}", behavior_record.sports)
        drawing = request.GET.get(f"drawing_{student.id}", behavior_record.drawing_painting)
        crafts = request.GET.get(f"crafts_{student.id}", behavior_record.crafts)

        punctuality = request.GET.get(f"punctuality_{student.id}", behavior_record.punctuality)
        attendance = request.GET.get(f"attendance_{student.id}", behavior_record.attendance)
        reliability = request.GET.get(f"reliability_{student.id}", behavior_record.reliability)
        neatness = request.GET.get(f"neatness_{student.id}", behavior_record.neatness)
        politeness = request.GET.get(f"politeness_{student.id}", behavior_record.politeness)
        honesty = request.GET.get(f"honesty_{student.id}", behavior_record.honesty)
        relationship = request.GET.get(f"relationship_{student.id}", behavior_record.relationship_with_students)
        self_control = request.GET.get(f"self_control_{student.id}", behavior_record.self_control)
        attentive = request.GET.get(f"attentive_{student.id}", behavior_record.attentiveness)
        perseverance = request.GET.get(f"perseverance_{student.id}", behavior_record.perseverance)

        behavior_summary = (
            f"Psychomotor - H/W: {hw}, Games: {games}, Sports: {sports}, Drawing: {drawing}, Crafts: {crafts}\n"
            f"Affective - Punctuality: {punctuality}, Attendance: {attendance}, Reliability: {reliability}, "
            f"Neatness: {neatness}, Politeness: {politeness}, Honesty: {honesty}, Relationship: {relationship}, "
            f"Self-Control: {self_control}, Attentive: {attentive}, Perseverance: {perseverance}"
        )
    else:
        behavior_summary = "No behavior records yet."

    # ---- GET RESULTS ----
    results = Result_Portal.objects.filter(
        student=student,
        session_id=int(session_id),
        term_id=int(term_id)
    ).select_related("subject")

    if not results.exists():
        return JsonResponse({"comment": "No results found for this student."})

    # Build subject summary
    subject_scores_text = "\n".join(
        f"{r.subject.title}: Total={r.total_score}, Grade={r.grade_letter}"
        for r in results
    )

    prompt = f"""
You are a school form teacher. Write a short, clear, honest comment for this student.

Student: {student.first_name} {student.last_name}

Scores:
{subject_scores_text}

Behavior:
{behavior_summary}

Make the comment 2–3 sentences. Highlight strengths, mention one improvement.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful school teacher assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        comment = response.choices[0].message.content.strip()
        return JsonResponse({"comment": comment})

    except Exception as e:
        return JsonResponse({"comment": f"Error generating comment: {str(e)}"})
                    


@login_required
def edit_student_behavior(request, student_id, term_id, session_id):

    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(NewUser, id=student_id)
    term = get_object_or_404(Term, id=term_id)
    session = get_object_or_404(Session, id=session_id)

    # Fetch or create behavior record automatically
    record, created = StudentBehaviorRecord.objects.get_or_create(
        student=student,
        term=term,
        session=session,
        defaults={
            "form_teacher": teacher,
            "handwriting": 3,
            "games": 3,
            "sports": 3,
            "drawing_painting": 3,
            "crafts": 3,
            "punctuality": 3,
            "attendance": 3,
            "reliability": 3,
            "neatness": 3,
            "politeness": 3,
            "honesty": 3,
            "relationship_with_students": 3,
            "self_control": 3,
            "attentiveness": 3,
            "perseverance": 3,
        }
    )

    if request.method == "POST":
        # Psychomotor fields
        record.handwriting = request.POST.get("handwriting")
        record.games = request.POST.get("games")
        record.sports = request.POST.get("sports")
        record.drawing_painting = request.POST.get("drawing_painting")
        record.crafts = request.POST.get("crafts")

        # Affective fields
        record.punctuality = request.POST.get("punctuality")
        record.attendance = request.POST.get("attendance")
        record.reliability = request.POST.get("reliability")
        record.neatness = request.POST.get("neatness")
        record.politeness = request.POST.get("politeness")
        record.honesty = request.POST.get("honesty")
        record.relationship_with_students = request.POST.get("relationship_with_students")
        record.self_control = request.POST.get("self_control")
        record.attentiveness = request.POST.get("attentiveness")
        record.perseverance = request.POST.get("perseverance")

        # Comment field
        record.form_teacher_comment = request.POST.get("form_teacher_comment")

        record.form_teacher = teacher  # ensure ownership
        record.save()

        messages.success(request, "Behavior record updated successfully.")
        return redirect("portal:form_teacher_dashboard")

    return render(request, "portal/edit_student_behavior.html", {
        "record": record,
        "student": student,
        "term": term,
        "session": session,
    })

from django.http import HttpResponseForbidden
from django.db.models import Prefetch

from django.http import JsonResponse

from django.http import JsonResponse

@login_required
def principal_dashboard(request):
    # Only principals allowed
    if not getattr(request.user, "is_principal", False):
        return HttpResponseForbidden("Access denied")

    school = request.user.school
    classes = CourseGrade.objects.filter(schools=school)
    sessions = Session.objects.all()
    terms = Term.objects.all()

    selected_session_id = request.GET.get("session")
    selected_term_id = request.GET.get("term")
    selected_class_id = request.GET.get("class")

    selected_session = Session.objects.filter(id=selected_session_id).first() if selected_session_id else None
    selected_term = Term.objects.filter(id=selected_term_id).first() if selected_term_id else None
    selected_class = CourseGrade.objects.filter(id=selected_class_id).first() if selected_class_id else None

    records = []

    if selected_session and selected_term and selected_class:
        # Ensure all StudentBehaviorRecords exist
        for student in selected_class.students.all():
            StudentBehaviorRecord.objects.get_or_create(
                student=student,
                school=school,
                session=selected_session,
                term=selected_term,
                defaults={'form_teacher': selected_class.form_teacher}
            )

        # Fetch behavior records
        records = StudentBehaviorRecord.objects.filter(
            student__course_grades=selected_class,
            session=selected_session,
            term=selected_term
        ).select_related('student')

        # Attach results and calculate totals, grades, and remarks
        for record in records:
            results = Result_Portal.objects.filter(
                student=record.student,
                session=selected_session,
                term=selected_term,
                schools=school
            ).select_related('subject')

            # Compute total, average, grade per student
            total_score = sum(float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
                              for r in results)
            num_subjects = len(results)
            average_score = round(total_score / num_subjects, 2) if num_subjects else 0
            final_grade = results[0].grade_letter if results else ''
            remarks = {r.subject.title: r.remark for r in results}

            # Attach to record for template
            record.results = results
            record.total_score = total_score
            record.average_score = average_score
            record.final_grade = final_grade
            record.subject_remarks = remarks

        # Handle POST to save principal comments
        if request.method == "POST":
            for record in records:
                comment_field = f"comment_{record.student.id}"
                new_comment = request.POST.get(comment_field)
                if new_comment is not None:
                    record.principal_comment = new_comment
                    record.save()
            messages.success(request, "Principal comments saved successfully.")
            # Redirect to refresh GET params
            return redirect(request.path + f"?session={selected_session.id}&term={selected_term.id}&class={selected_class.id}")

    context = {
        "classes": classes,
        "sessions": sessions,
        "terms": terms,
        "selected_session": selected_session,
        "selected_term": selected_term,
        "selected_class": selected_class,
        "records": records,
    }

    return render(request, "portal/principal_dashboard.html", context)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



@csrf_exempt
def generate_principal_comment(request, student_id):
    session_id = request.GET.get("session")
    term_id = request.GET.get("term")
    class_id = request.GET.get("class")

    if not (session_id and term_id and class_id):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    from portal.models import NewUser, Result_Portal

    try:
        student = NewUser.objects.get(id=student_id)
    except NewUser.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    results = Result_Portal.objects.filter(
        student=student,
        session_id=session_id,
        term_id=term_id
    ).select_related("subject")

    result_lines = [
        f"{r.subject.title}: Total={r.total_score}, Grade={r.grade_letter}, Remark={r.remark}"
        for r in results
    ]

    result_text = "\n".join(result_lines) if result_lines else "No results yet."

    prompt = f"""
    You are an expert school principal.
    Based on the following student's performance, write a detailed, professional principal comment.
    
    Student: {student.first_name} {student.last_name}
    Results:
    {result_text}

    The comment must:
    - Highlight strong subjects
    - Highlight weak subjects
    - Mention overall performance
    - Be encouraging and actionable
    - Be 2–3 sentences long
    """

    # Call OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate principal comments with high precision."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1800,
            temperature=0.4,
        )
        ai_comment = resp.choices[0].message.content.strip()  # ✅ Correct
    except Exception as e:
        return JsonResponse({"comment": f"Error generating comment: {str(e)}"})

    return JsonResponse({"comment": ai_comment})
    


@csrf_exempt
def generate_all_principal_comments(request):
    """
    Generate AI principal comments using OpenAI GPT for all students
    in a given session, term, and class.
    """

    session_id = request.GET.get("session")
    term_id = request.GET.get("term")
    class_id = request.GET.get("class")

    if not (session_id and term_id and class_id):
        return JsonResponse({"error": "Missing parameters: session, term, or class"}, status=400)

    # Fetch students in the class
    students = NewUser.objects.filter(course_grades__id=class_id).distinct()

    # Fetch all results for the students in this session and term
    results = Result_Portal.objects.filter(
        session_id=session_id,
        term_id=term_id,
        student__in=students
    ).select_related("subject", "student", "schools")

    output_comments = {}

    for student in students:
        student_results = results.filter(student=student)

        strong_subjects = []
        weak_subjects = []
        result_lines = []

        for r in student_results:
            # Determine strong/weak subjects
            if r.total_score >= 70:
                strong_subjects.append(r.subject.title)
            elif r.total_score < 45:
                weak_subjects.append(r.subject.title)

            result_lines.append(
                f"{r.subject.title}: Total={r.total_score}, Grade={r.grade_letter or '-'}, Remark={r.remark or '-'}"
            )

        result_text = "\n".join(result_lines) if result_lines else "No results yet."

        prompt = f"""
You are an expert school principal. Based on the following student's performance, write a professional principal comment.

Student: {student.first_name} {student.last_name}
Results:
{result_text}

Strong subjects: {', '.join(strong_subjects) if strong_subjects else 'None'}
Weak subjects: {', '.join(weak_subjects) if weak_subjects else 'None'}

The comment must:
- Highlight strong subjects
- Highlight weak subjects
- Mention overall performance
- Be encouraging and actionable
- Be 2–3 sentences long
"""

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate curriculum-aligned principal comments with high precision."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1800,
                temperature=0.4,
            )

            # Correct access to the message content
            ai_comment = resp.choices[0].message.content.strip()

        except Exception as e:
            ai_comment = f"Error generating comment: {str(e)}"

        output_comments[student.id] = ai_comment

    return JsonResponse({"comments": output_comments}, status=200)


@login_required
@login_required(login_url='teacher:teacher_login')
def principal_edit_behavior(request, record_id):
    # Only superuser or principal can access
    if not request.user.is_superuser and not getattr(request.user, "is_principal", False):
        return HttpResponseForbidden("Access denied")

    record = get_object_or_404(StudentBehaviorRecord, id=record_id)

    if request.method == "POST":
        comment = request.POST.get("principal_comment", "").strip()
        record.principal_comment = comment
        record.save()
        messages.success(request, "Principal remark updated successfully.")

        # Redirect back to dashboard, keep class selection if available
        class_id = record.student.course_grades.first().id if record.student.course_grades.exists() else None
        if class_id:
            return redirect(f"/portal/principal-dashboard/?class={class_id}")
        return redirect("portal:principal_dashboard")

    context = {
        "record": record
    }
    return render(request, "portal/principal_edit_behavior.html", context)


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
