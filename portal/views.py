import io
import re
# from tkinter import Image
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum
import requests
from portal.models import Result_Portal
import school
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
from reportlab.lib.units import inch, mm

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

from django.http import JsonResponse

def download_class_report(request):
    result_class = request.GET.get('result_class')
    session_id   = request.GET.get('session_id')
    term_id      = request.GET.get('term_id')

    if not all([result_class, session_id, term_id]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    from .tasks import generate_class_report_pdf_task
    task = generate_class_report_pdf_task.delay(result_class, int(session_id), int(term_id))

    return JsonResponse({
        'status': 'processing',
        'task_id': task.id,
        'status_url': request.build_absolute_uri(f'/check-pdf-status/{task.id}/'),
        'download_url': request.build_absolute_uri(f'/download-pdf/{task.id}/'),
    })


#individual report card PDF generation
def download_term_report_pdf(request, student_id, session_id, term_id):
    from collections import defaultdict
    from reportlab.lib.units import mm

    # ── Fetch results ─────────────────────────────────────────────
    results = Result_Portal.objects.filter(
        student_id=student_id,
        session_id=session_id,
        term_id=term_id
    ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('subject__title')

    if not results.exists():
        return HttpResponse("No results found.", status=404)

    student    = results.first().student
    school     = results.first().schools
    session    = results.first().session
    term       = results.first().term
    is_midterm = getattr(term, 'is_midterm', False)

    # ── Clean result_class ────────────────────────────────────────
    raw_class     = getattr(results.first(), 'result_class', '')
    display_class = raw_class.strip().split()[0]

    # ── Class stats ───────────────────────────────────────────────
    all_results = Result_Portal.objects.filter(
        result_class=raw_class,
        session_id=session_id,
        term_id=term_id
    ).select_related('subject')

    student_total   = sum(
        float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
        for r in results
    )
    num_subjects    = results.count()
    student_average = round(student_total / num_subjects, 2) if num_subjects else 0

    class_totals = {}
    for r in all_results:
        sid   = r.student_id
        score = float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
        class_totals[sid] = class_totals.get(sid, 0) + score

    sorted_totals    = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)
    position         = next((i + 1 for i, (sid, _) in enumerate(sorted_totals) if sid == student_id), None)
    total_students   = len(class_totals)
    class_average    = round(sum(class_totals.values()) / len(class_totals), 2) if class_totals else 0
    highest_in_class = round(max(class_totals.values(), default=0), 2)
    lowest_in_class  = round(min(class_totals.values(), default=0), 2)
    final_grade      = results[0].grade_letter if results else ''

    # ── Subject scores map (avoid N+1) ───────────────────────────
    subject_scores_map = defaultdict(list)
    for r in all_results:
        score = float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
        subject_scores_map[r.subject_id].append((r.student_id, score))

    # ── PDF Setup ─────────────────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.username}_term_report.pdf"'

    W, H   = A4
    MARGIN = 5 * mm
    INNER  = W - 2 * MARGIN

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        topMargin=8, bottomMargin=8,
        leftMargin=MARGIN, rightMargin=MARGIN
    )

    BLUE  = colors.HexColor("#1a4e8c")
    LBLUE = colors.HexColor("#d0e4f7")
    LGREY = colors.HexColor("#f2f2f2")

    S = {
        "report_title": ParagraphStyle("rt", fontSize=9,  fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, spaceAfter=4),
        "section_hd":   ParagraphStyle("sh", fontSize=8,  fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, spaceAfter=0),
        "cell_normal":  ParagraphStyle("cn", fontSize=7.5, fontName="Helvetica",
                                       alignment=TA_LEFT,   leading=10),
        "cell_center":  ParagraphStyle("cc", fontSize=7,   fontName="Helvetica",
                                       alignment=TA_CENTER, leading=9),
        "cell_hdr":     ParagraphStyle("ch", fontSize=7,   fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, leading=9),
        "small":        ParagraphStyle("sm", fontSize=6.5, fontName="Helvetica",
                                       alignment=TA_LEFT,   leading=9),
        "comment":      ParagraphStyle("co", fontSize=8,   fontName="Helvetica",
                                       alignment=TA_LEFT,   leading=11, spaceAfter=3),
        "label":        ParagraphStyle("lb", fontSize=8,   fontName="Helvetica-Bold",
                                       alignment=TA_LEFT,   leading=10),
    }

    def hr_line(thickness=0.5, color=BLUE):
        return HRFlowable(width="100%", thickness=thickness, color=color,
                          spaceAfter=3, spaceBefore=3)

    def section_header(text):
        tbl = Table([[Paragraph(text, S["section_hd"])]], colWidths=[INNER])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LBLUE),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("BOX",           (0,0), (-1,-1), 0.5, BLUE),
        ]))
        return tbl

    def ordinal(n):
        if n is None: return "N/A"
        suffix = {1:"st", 2:"nd", 3:"rd"}.get(n if n < 20 else n % 10, "th")
        return f"{n}{suffix}"

    def ic(label, value):
        return Paragraph(f"<b>{label}:</b> {value}", S["cell_normal"])

    def trait_table(title, traits, width):
        hdr  = [[Paragraph(f"<b>{title}</b>", S["cell_hdr"]),
                 Paragraph("<b>Rating</b>",    S["cell_hdr"])]]
        rows = [[Paragraph(t, S["cell_normal"]), Paragraph(str(v), S["cell_center"])]
                for t, v in traits]
        tbl  = Table(hdr + rows, colWidths=[width * 0.75, width * 0.25])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  LBLUE),
            ("GRID",          (0,0), (-1,-1), 0.4, colors.grey),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGREY]),
        ]))
        return tbl

    max_ca   = float(school.max_ca_score)      if school and school.max_ca_score      else 10.0
    max_mid  = float(school.max_midterm_score) if school and school.max_midterm_score  else 20.0
    max_exam = float(school.max_exam_score)    if school and school.max_exam_score     else 70.0

    elements = []

    # ── 1. School Header ──────────────────────────────────────────
    logo_img = None
    if school and getattr(school, 'logo', None):
        try:
            logo_data = io.BytesIO(requests.get(school.logo.url).content)
            logo_img  = RLImage(logo_data, width=70, height=70)
        except Exception:
            pass

    school_name_str    = school.school_name    if school else "School Name"
    school_motto_str   = school.school_motto   if school else ""
    school_address_str = school.school_address if school else ""

    school_details = [
        Paragraph(f"<b>{school_name_str}</b>",
                  ParagraphStyle("SN2", fontSize=13, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Spacer(1, 4),
        Paragraph(f"<i>{school_motto_str}</i>",
                  ParagraphStyle("SM2", fontSize=9, fontName="Helvetica-Oblique", alignment=TA_CENTER)),
        Spacer(1, 4),
        Paragraph(school_address_str,
                  ParagraphStyle("SA2", fontSize=7.5, fontName="Helvetica", alignment=TA_CENTER)),
    ]

    if logo_img:
        header_tbl = Table(
            [[logo_img, school_details, logo_img]],
            colWidths=[70, INNER - 140, 70]
        )
    else:
        header_tbl = Table([[school_details]], colWidths=[INNER])

    header_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    elements.append(header_tbl)
    elements.append(hr_line(thickness=1.5))

    elements.append(Paragraph(
        f"<b>REPORT SHEET FOR {term.name}, {session.name} ACADEMIC SESSION</b>",
        S["report_title"]
    ))
    elements.append(hr_line(thickness=0.5))
    elements.append(Spacer(1, 4))

    # ── 2. Student Info Grid ──────────────────────────────────────
    col3      = INNER / 3
    info_data = [
        [ic("Name",             f"{student.first_name} {student.last_name}"),
         ic("Gender",           getattr(student, 'gender', 'N/A') or 'N/A'),
         ic("Class",            display_class)],
        [ic("No. in Class",     total_students),
         ic("Total Score",      student_total),
         ic("Class Average",    class_average)],
        [ic("Highest In Class", highest_in_class),
         ic("Lowest In Class",  lowest_in_class),
         ic("Final Grade",      final_grade)],
        [ic("Final Average",    student_average),
         ic("POSITION",         ordinal(position)),
         ic("Next Term Begins", getattr(school, 'next_term_date', 'N/A') if school else 'N/A')],
    ]
    info_tbl = Table(info_data, colWidths=[col3, col3, col3])
    info_tbl.setStyle(TableStyle([
        ("GRID",          (0,0), (-1,-1), 0.4, colors.grey),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, LGREY]),
    ]))
    elements += [info_tbl, Spacer(1, 6)]

    # ── 3. Subject Table ──────────────────────────────────────────
    elements.append(section_header("Subjects"))
    elements.append(Spacer(1, 2))

    if is_midterm:
        hdr_row = [Paragraph(h, S["cell_hdr"]) for h in [
            "Subjects",
            f"CA<br/>({int(max_ca)})",
            f"Midterm<br/>Exams<br/>({int(max_mid)})",
            "Total",
            "Per<br/>(%)",
            "Low.<br/>In<br/>Class",
            "High.<br/>In<br/>Class",
            "Class<br/>Average",
            "POS",
            "Out<br/>Of",
            "Grade",
            "Remark",
        ]]
    else:
        hdr_row = [Paragraph(h, S["cell_hdr"]) for h in [
            "Subjects",
            f"CA<br/>({int(max_ca)})",
            f"Midterm<br/>Exams<br/>({int(max_mid)})",
            f"Exams<br/>({int(max_exam)})",
            "Total",
            "Low.<br/>In<br/>Class",
            "High.<br/>In<br/>Class",
            "Class<br/>Average",
            "POS",
            "Out<br/>Of",
            "Grade",
            "Remark",
        ]]

    subj_data = [hdr_row]

    for r in results:
        ca    = float(r.ca_score      or 0)
        mid   = float(r.midterm_score or 0)
        exam  = float(r.exam_score    or 0)
        total = ca + mid + exam

        if is_midterm:
            midterm_total = ca + mid
            max_total     = max_ca + max_mid
            percentage    = round((midterm_total / max_total) * 100) if max_total else 0
        else:
            midterm_total = total
            percentage    = 0

        words       = r.subject.title.split()
        clean_title = ' '.join(
            w for w in words
            if not any(w.upper().startswith(p) for p in ['JSS', 'SS'])
        ).strip()

        s_entries = subject_scores_map[r.subject_id]
        s_scores  = [sc for _, sc in s_entries]
        s_count   = len(s_scores)
        s_avg     = round(sum(s_scores) / s_count, 2) if s_count else 0
        s_high    = max(s_scores, default=0)
        s_low     = min(s_scores, default=0)
        s_sorted  = sorted(s_entries, key=lambda x: x[1], reverse=True)
        s_pos     = next((i + 1 for i, (sid_, _) in enumerate(s_sorted) if sid_ == student_id), None)

        remark_style = ParagraphStyle(
            "rs", fontSize=7, fontName="Helvetica", alignment=TA_LEFT, leading=9,
            textColor=colors.HexColor("#c00000")
            if r.remark and r.remark.lower() == "fail" else colors.black
        )

        if is_midterm:
            subj_data.append([
                Paragraph(clean_title,                S["cell_normal"]),
                Paragraph(str(ca),                    S["cell_center"]),
                Paragraph(str(mid),                   S["cell_center"]),
                Paragraph(str(midterm_total),         S["cell_center"]),
                Paragraph(f"{percentage}%",           S["cell_center"]),
                Paragraph(str(s_low),                 S["cell_center"]),
                Paragraph(str(s_high),                S["cell_center"]),
                Paragraph(str(s_avg),                 S["cell_center"]),
                Paragraph(ordinal(s_pos),             S["cell_center"]),
                Paragraph(str(s_count),               S["cell_center"]),
                Paragraph(f"<b>{r.grade_letter}</b>", S["cell_center"]),
                Paragraph(r.remark or "",             remark_style),
            ])
        else:
            subj_data.append([
                Paragraph(clean_title,                S["cell_normal"]),
                Paragraph(str(ca),                    S["cell_center"]),
                Paragraph(str(mid),                   S["cell_center"]),
                Paragraph(str(exam),                  S["cell_center"]),
                Paragraph(str(total),                 S["cell_center"]),
                Paragraph(str(s_low),                 S["cell_center"]),
                Paragraph(str(s_high),                S["cell_center"]),
                Paragraph(str(s_avg),                 S["cell_center"]),
                Paragraph(ordinal(s_pos),             S["cell_center"]),
                Paragraph(str(s_count),               S["cell_center"]),
                Paragraph(f"<b>{r.grade_letter}</b>", S["cell_center"]),
                Paragraph(r.remark or "",             remark_style),
            ])

    if is_midterm:
        col_fracs = [0.18, 0.06, 0.10, 0.07, 0.07, 0.06, 0.06, 0.09, 0.06, 0.05, 0.06, 0.07]
    else:
        col_fracs = [0.18, 0.05, 0.09, 0.07, 0.06, 0.06, 0.06, 0.09, 0.06, 0.05, 0.06, 0.07]

    col_widths = [INNER * f for f in col_fracs]
    col_widths[-1] = INNER - sum(col_widths[:-1])

    subj_tbl = Table(subj_data, colWidths=col_widths, repeatRows=1)
    subj_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  LBLUE),
        ("GRID",          (0,0),  (-1,-1), 0.4, colors.grey),
        ("FONTSIZE",      (0,0),  (-1,-1), 7),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),  (-1,-1), 3),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 3),
        ("ROWBACKGROUNDS",(0,1),  (-1,-1), [colors.white, LGREY]),
    ]))
    elements += [subj_tbl, Spacer(1, 4)]

    grade_details = (
        getattr(school, 'grade_details', None) or
        "F = 0-45 | E8 = 45-50 | D7 = 50-55 | C6 = 55-60 | C5 = 60-65 | "
        "C4 = 65-70 | B3 = 70-75 | B2 = 75-91 | A1 = 91-100"
    )
    elements.append(Paragraph(
        f"<b>Grade Details:</b> {grade_details} | No. of Subjects: {num_subjects}",
        S["small"]
    ))
    elements.append(Spacer(1, 6))

    # ── 4 & 5: Only for non-midterm ───────────────────────────────
    if not is_midterm:
        # ── 4. Psychomotor & Affective ────────────────────────────
        behavior = StudentBehaviorRecord.objects.filter(
            student_id=student_id,
            session_id=session_id,
            term_id=term_id
        ).first()

        elements.append(section_header("Psychomotor & Affective Traits"))
        elements.append(Spacer(1, 2))

        half = INNER / 2

        if behavior:
            psycho_traits = [
                ("HANDWRITING",        behavior.handwriting),
                ("GAMES",              behavior.games),
                ("SPORTS",             behavior.sports),
                ("DRAWING & PAINTING", behavior.drawing_painting),
                ("CRAFTS",             behavior.crafts),
            ]
            affective_traits = [
                ("PUNCTUALITY",               behavior.punctuality),
                ("ATTENDANCE",                behavior.attendance),
                ("RELIABILITY",               behavior.reliability),
                ("NEATNESS",                  behavior.neatness),
                ("POLITENESS",                behavior.politeness),
                ("HONESTY",                   behavior.honesty),
                ("RELATIONSHIP WITH STUDENTS",behavior.relationship_with_students),
                ("SELF CONTROL",              behavior.self_control),
                ("ATTENTIVENESS",             behavior.attentiveness),
                ("PERSEVERANCE",              behavior.perseverance),
            ]
        else:
            psycho_traits    = [("HANDWRITING",""), ("GAMES",""), ("SPORTS",""),
                                ("DRAWING & PAINTING",""), ("CRAFTS","")]
            affective_traits = [("PUNCTUALITY",""), ("ATTENDANCE",""), ("RELIABILITY",""),
                                ("NEATNESS",""), ("POLITENESS",""), ("HONESTY",""),
                                ("RELATIONSHIP WITH STUDENTS",""), ("SELF CONTROL",""),
                                ("ATTENTIVENESS",""), ("PERSEVERANCE","")]

        side_tbl = Table(
            [[trait_table("Default Psychomotor Rating",      psycho_traits,    half),
              trait_table("Default Affective Traits Rating", affective_traits, half)]],
            colWidths=[half, half]
        )
        side_tbl.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ]))
        elements += [side_tbl, Spacer(1, 6)]

        # ── 5. Comments & Signatures ──────────────────────────────
        elements.append(section_header("Remarks & Signatures"))
        elements.append(Spacer(1, 3))

        form_teacher_name = "N/A"
        if behavior:
            teachers = behavior.form_teacher.all()
            if teachers.exists():
                form_teacher_name = ", ".join(
                    f"{t.first_name} {t.last_name}".strip() for t in teachers
                )

        form_comment      = (behavior.form_teacher_comment if behavior else "") or ""
        principal_comment = (behavior.principal_comment    if behavior else "") or ""

        comments_data = [
            [Paragraph(f"<b>Form Teacher:</b> {form_teacher_name}", S["label"]), ""],
            [Paragraph("<b>Form Teacher Comment:</b>", S["label"]), ""],
            [Paragraph(form_comment      or "No comment.", S["comment"]), ""],
            [Paragraph("<b>PRINCIPAL'S REMARK:</b>",    S["label"]), ""],
            [Paragraph(principal_comment or "No remark.", S["comment"]), ""],
            [
                Paragraph("<b>Form Teacher SIGNATURE:</b> _______________________", S["label"]),
                Paragraph("<b>PRINCIPAL'S SIGNATURE:</b> _______________________",  S["label"]),
            ],
        ]

        if school and getattr(school, 'teacher_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
                sig_img  = RLImage(sig_data, width=100, height=40)
                comments_data[5][0] = sig_img
            except Exception:
                pass

        if school and getattr(school, 'principal_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                sig_img  = RLImage(sig_data, width=100, height=40)
                comments_data[5][1] = sig_img
            except Exception:
                pass

        comment_tbl = Table(comments_data, colWidths=[INNER * 0.6, INNER * 0.4])
        comment_tbl.setStyle(TableStyle([
            ("GRID",          (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("SPAN",          (0,0), (1,0)),
            ("SPAN",          (0,1), (1,1)),
            ("SPAN",          (0,2), (1,2)),
            ("SPAN",          (0,3), (1,3)),
            ("SPAN",          (0,4), (1,4)),
            ("BACKGROUND",    (0,0), (-1,0),  LGREY),
            ("BACKGROUND",    (0,3), (-1,3),  LGREY),
        ]))
        elements.append(comment_tbl)

    # ── Principal signature + form teacher always shows for midterm
    if is_midterm:
        elements.append(Spacer(1, 10))
        elements.append(section_header("Principal's Signature"))
        elements.append(Spacer(1, 6))

        behavior = StudentBehaviorRecord.objects.filter(
            student_id=student_id,
            session_id=session_id,
            term_id=term_id
        ).first()

        form_teacher_name = "N/A"
        if behavior:
            teachers = behavior.form_teacher.all()
            if teachers.exists():
                form_teacher_name = ", ".join(
                    f"{t.first_name} {t.last_name}".strip() for t in teachers
                )

        elements.append(Paragraph(
            f"<b>Form Teacher:</b> {form_teacher_name}",
            S["label"]
        ))
        elements.append(Spacer(1, 6))

        if school and getattr(school, 'principal_signature', None):
            try:
                sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                sig_img  = RLImage(sig_data, width=100, height=40)
                elements.append(sig_img)
            except Exception:
                elements.append(Paragraph(
                    "<b>PRINCIPAL'S SIGNATURE:</b> _______________________",
                    S["label"]
                ))
        else:
            elements.append(Paragraph(
                "<b>PRINCIPAL'S SIGNATURE:</b> _______________________",
                S["label"]
            ))

    doc.build(elements)
    return response

    

#per student
# def download_term_report_pdf(request, student_id, session_id, term_id):
#     # --- Fetch results ---
#     results = Result_Portal.objects.filter(
#         student_id=student_id,
#         session_id=session_id,
#         term_id=term_id
#     ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('subject__title')

#     if not results.exists():
#         return HttpResponse("No results found.", status=404)

#     student = results.first().student
#     school = results.first().schools
#     session = results.first().session
#     term = results.first().term
    
    
#     raw_class = getattr(results.first(), 'result_class', '')
#     print(f"RAW CLASS REPR: {repr(raw_class)}")

#     match = re.match(r'^((?:JSS|SS)\\s*\\d+)', raw_class.strip(), re.IGNORECASE)
#     print(f"MATCH RESULT: {match}")

#     result_class = match.group(1).strip() if match else raw_class.strip()
#     print(f"FINAL result_class: '{result_class}'")

#      # Get school max scores from the first result
   
#     # --- Class stats ---
#     all_results = Result_Portal.objects.filter(
#         result_class=result_class,
#         session_id=session_id,
#         term_id=term_id
#     )

#     student_total = sum(
#         float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
#         for r in results
#     )
#     num_subjects = len(results)
#     student_average = round(student_total / num_subjects, 2) if num_subjects else 0

#     class_totals = {}
#     for r in all_results:
#         sid = r.student_id
#         total_score = float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
#         class_totals[sid] = class_totals.get(sid, 0) + total_score

#     sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)
#     position = next((i + 1 for i, (sid, _) in enumerate(sorted_totals) if sid == student_id), None)
#     total_students = len(class_totals)
#     class_average = round(sum(class_totals.values()) / len(class_totals), 2) if class_totals else 0
#     highest_in_class = max(class_totals.values(), default=0)
#     lowest_in_class = min(class_totals.values(), default=0)
#     final_grade = results[0].grade_letter if results else ''

#     # --- PDF Setup ---
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{student.username}_term_report.pdf"'
#     doc = SimpleDocTemplate(response, pagesize=A4, topMargin=25, leftMargin=25, rightMargin=25, bottomMargin=30)

#     styles = getSampleStyleSheet()
#     style_left = styles["Normal"]
#     style_left.alignment = TA_LEFT
#     style_center = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)

#     elements = []

#     # --- Header Section (Logo + Flex Layout) ---
#     logo_img = None
#     if school and getattr(school, 'logo', None):
#         try:
#             logo_data = io.BytesIO(requests.get(school.logo.url).content)
#             logo_img = RLImage(logo_data, width=80, height=80)
#         except Exception:
#             pass

#     school_name = f"<b>{getattr(school, 'school_name', 'Best Academy, Abuja')}</b>"
#     school_motto = f"<i>{getattr(school, 'school_motto', 'Motto: Knowledge for Excellence')}</i>"
#     school_address = f"{getattr(school, 'school_address', 'Tunga')}"

#     school_details = [
#             Paragraph(school_name, ParagraphStyle(name='SchoolName', fontSize=14, alignment=TA_LEFT)),
#             Spacer(1, 8),  # 4 points of vertical space
#             Paragraph(school_motto, ParagraphStyle(name='SchoolMotto', fontSize=10, alignment=TA_LEFT)),
#             Spacer(1, 8),  # 2 points of vertical space
#             Paragraph(school_address, ParagraphStyle(name='SchoolAddress', fontSize=9, alignment=TA_LEFT))
#         ]

#     header_table = Table([[logo_img if logo_img else "", school_details]], colWidths=[90, 400])
#     header_table.setStyle(TableStyle([
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('LEFTPADDING', (0, 0), (-1, -1), 5),
#         ('RIGHTPADDING', (0, 0), (-1, -1), 5),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
#         ('TOPPADDING', (0, 0), (-1, -1), 0),
#     ]))
#     elements.append(header_table)
#     elements.append(Spacer(1, 10))

    
#     hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
#     elements.append(hr)

#     # --- Title ---
#     elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
#     elements.append(Spacer(1, 10))

#     # --- Student Info (Grid Table) ---

#     student_info_data = [
#         [f"Name: {student.first_name} {student.last_name}", f"Class: {result_class}", f"Term: {term.name}"],
#         [f"Session: {session.name}", f"No. in Class: {total_students}", f"Position: {position} of {total_students}"],
#         [f"Total Score: {student_total}", f"Average Score: {student_average}", f"Class Average: {class_average}"],
#         [f"Highest in Class: {highest_in_class}", f"Lowest in Class: {lowest_in_class}", f"Final Grade: {final_grade}"],
#     ]
#     student_table = Table(student_info_data, colWidths=[180, 180, 180])
#     student_table.setStyle(TableStyle([
#         ('GRID', (0, 0), (-1, -1), 0.6, colors.grey),
#         ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     elements += [student_table, Spacer(1, 15)]

#     max_ca = school.max_ca_score if school else 10
#     max_mid = school.max_midterm_score if school else 30
#     max_exam = school.max_exam_score if school else 60

#     # --- Subject Table (with Grid) ---
#     header_style = ParagraphStyle(name='HeaderStyle', fontName='Helvetica-Bold', fontSize=7, alignment=1)

#     # Use f-strings to insert actual max values
#     headers = [
#         "Subject",
#         f"CA<br/>({max_ca})",
#         f"Midterm<br/>({max_mid})",
#         f"Exam<br/>({max_exam})",
#         "Total",
#         "Per (%)",
#         "Grade",
#         "Class<br/>Ave",
#         "POS",
#         "Out<br/>Of",
#         "High<br/>In<br/>Class",
#         "Low<br/>In<br/>Class",
#         "Remark"
#     ]

#     table_data = [[Paragraph(h, header_style) for h in headers]]



#     for r in results:
#         ca = float(r.ca_score or 0)
#         mid = float(r.midterm_score or 0)
#         exam = float(r.exam_score or 0)
#         total = ca + mid + exam
#         max_total = sum([10 if ca > 0 else 0, 30 if mid > 0 else 0, 60 if exam > 0 else 0])
#         percentage = round((total / max_total) * 100) if max_total else 0

#         subject_results = all_results.filter(subject=r.subject)
#         class_avg = round(sum(
#             float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#             for s in subject_results
#         ) / len(subject_results), 2) if subject_results else 0
#         high_in_class = max([
#             float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#             for s in subject_results
#         ], default=0)
#         low_in_class = min([
#             float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#             for s in subject_results
#         ], default=0)
#         pos_sorted = sorted([
#             (s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
#             for s in subject_results
#         ], key=lambda x: x[1], reverse=True)
#         pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == student_id), None)

#         row = [
#             r.subject.title, str(ca), str(mid), str(exam), str(total),
#             f"{percentage}", r.grade_letter, str(class_avg), str(pos),
#             str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark
#         ]
#         table_data.append([Paragraph(str(x), style_center) for x in row])

#     page_width = A4[0] - doc.leftMargin - doc.rightMargin
#     col_fractions = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
#     col_widths = [page_width * frac for frac in col_fractions]

#     result_table = Table(table_data, colWidths=col_widths)
#     result_table.setStyle(TableStyle([
#         ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 6),
#         ('FONTSIZE', (0, 1), (-1, -1), 6),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     elements += [result_table, Spacer(1, 15)]

#     elements.append(Paragraph(f"<b>Number of Subjects:</b> {num_subjects}", style_left))
#     elements.append(Spacer(1, 5))  # optional spacing after


#     # --- Grading Scale ---
#     grading_text = "<b>GRADING SCALE</b>: A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39"
#     elements.append(Paragraph(grading_text, style_left))
#     # elements.append(Paragraph("<b>GRADING SCALE</b>":"A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39", style_left))
#     elements.append(Spacer(1, 15))

#     elements.append(hr)
     
#     # --- Fetch behavior for 3rd term ---
#     if term.name.lower().strip() in ["3rd term","3rd-term","3rd_term","3rd" ,"third term",'third-term','third_term',"third"]:
#         behavior = StudentBehaviorRecord.objects.filter(
#             student_id=student_id,
#             session_id=session_id,
#             term_id=term_id
#         ).first()

#         if behavior:
#             # --- Psychomotor Table ---
#             psychomotor_data = [["Default Psychomotor", "Rating"]]
#             psychomotor_data += [
#                 ["Handwriting", behavior.handwriting],
#                 ["Games", behavior.games],
#                 ["Sports", behavior.sports],
#                 ["Drawing & Painting", behavior.drawing_painting],
#                 ["Crafts", behavior.crafts]
#             ]
#             psychomotor_table = Table(
#                 psychomotor_data,
#                 colWidths=[120, 40],
#                 rowHeights=[15] + [12]*5  # header = 15, body = 12
#             )
#             psychomotor_table.setStyle(TableStyle([
#                 ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#                 ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
#                 ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
#                 ('FONTSIZE', (0,0), (-1,0), 8),
#                 ('FONTSIZE', (0,1), (-1,-1), 7),
#                 ('ALIGN', (1,1), (-1,-1), 'CENTER'),
#                 ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
#             ]))

#             # --- Affective Table ---
#             affective_data = [["Default Affective Traits", "Rating"]]
#             affective_data += [
#                 ["Punctuality", behavior.punctuality],
#                 ["Attendance", behavior.attendance],
#                 ["Reliability", behavior.reliability],
#                 ["Neatness", behavior.neatness],
#                 ["Politeness", behavior.politeness],
#                 ["Honesty", behavior.honesty],
#                 ["Relationship w/ Students", behavior.relationship_with_students],
#                 ["Self Control", behavior.self_control],
#                 ["Attentiveness", behavior.attentiveness],
#                 ["Perseverance", behavior.perseverance]
#             ]
#             affective_table = Table(
#                 affective_data,
#                 colWidths=[150, 40],
#                 rowHeights=[15] + [12]*10  # header = 15, body = 12
#             )
#             affective_table.setStyle(TableStyle([
#                 ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#                 ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
#                 ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
#                 ('FONTSIZE', (0,0), (-1,0), 8),
#                 ('FONTSIZE', (0,1), (-1,-1), 7),
#                 ('ALIGN', (1,1), (-1,-1), 'CENTER'),
#                 ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
#             ]))

#             # --- Scale Table ---
#             scale_data = [["SCALE"]]
#             scale_data += [["5 - Excellent"], ["4 - Good"], ["3 - Fair"], ["2 - Poor"], ["1 - Very Poor"]]
#             scale_table = Table(
#                 scale_data,
#                 colWidths=[100],
#                 rowHeights=[15] + [12]*5  # header = 15, body = 12
#             )
#             scale_table.setStyle(TableStyle([
#                 ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#                 ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
#                 ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
#                 ('FONTSIZE', (0,0), (-1,0), 8),
#                 ('FONTSIZE', (0,1), (-1,-1), 7),
#                 ('ALIGN', (0,1), (-1,-1), 'CENTER'),
#                 ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
#             ]))

#             # --- Combine tables horizontally ---
#             combined = Table([[psychomotor_table, affective_table, scale_table]], colWidths=[160, 200, 120])
#             combined.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))

#             elements.append(combined)
#             elements.append(Spacer(1, 10))  # tighter spacing
    
#             elements.append(hr)

#     # --- Comments & Signatures ---
#     if school and getattr(school, 'teacher_signature', None):
#         try:
#             sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
#             sig_img = RLImage(sig_data, width=100, height=40)
#             elements.append(sig_img)
#         except Exception:
#             pass

#         elements.append(Spacer(1, 10))

#         if behavior:
#             # append form teacher and principal comments
#             elements.append(Spacer(1, 10))
#             elements.append(Paragraph(f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}", style_left))
#             elements.append(Paragraph(f"<b>Form Teacher Comment:</b> {behavior.form_teacher_comment}", style_left))
#             elements.append(Spacer(1, 5))
#             elements.append(Paragraph(f"<b>Principal's Remark:</b> {behavior.principal_comment}", style_left))

#             elements.append(hr)

#     if school and getattr(school, 'principal_signature', None):
#             try:
#                 sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
#                 sig_img = RLImage(sig_data, width=100, height=40)
#                 elements.append(sig_img)
#             except Exception:
#                 pass
    
#     doc.build(elements)
#     return response


def class_report_list(request):
    reports = Result_Portal.objects.values(
        'result_class',
        'session_id',
        'session__name',
        'term_id',
        'term__name',
        'schools__school_name',
    ).distinct().order_by('result_class', 'session__name', 'term__name')

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


# def download_class_reports_pdf(request, result_class, session_id, term_id):

#     # --- Fetch all results ---
#     all_results = Result_Portal.objects.filter(
#         result_class=result_class,
#         session_id=session_id,
#         term_id=term_id
#     ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('student__username', 'subject__title')

#     if not all_results.exists():
#         return HttpResponse("No results found for this class.", status=404)

#     # --- Group by student ---
#     students = {}
#     for res in all_results:
#         sid = res.student_id
#         if sid not in students:
#             students[sid] = {
#                 'student': res.student,
#                 'records': [],
#                 'school': res.schools,
#                 'session': res.session,
#                 'term': res.term
#             }
#         students[sid]['records'].append(res)

#     # --- Compute totals for ranking ---
#     class_totals = {}
#     for res in all_results:
#         sid = res.student_id
#         total = float(res.ca_score or 0) + float(res.midterm_score or 0) + float(res.exam_score or 0)
#         class_totals[sid] = class_totals.get(sid, 0) + total
#     sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)

#     # --- PDF Setup ---
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="class_{result_class}_term_reports.pdf"'
#     doc = SimpleDocTemplate(response, pagesize=A4, topMargin=25, leftMargin=25, rightMargin=25, bottomMargin=30)

#     styles = getSampleStyleSheet()
#     style_left = styles["Normal"]
#     style_left.alignment = TA_LEFT
#     style_center = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)

#     elements = []

#     # --- Generate report for each student ---
#     for sid, data in students.items():
#         student = data['student']
#         records = data['records']
#         school = data['school']
#         session = data['session']
#         term = data['term']

#         # --- Student stats ---
#         num_subjects = len(records)
#         student_total = sum(
#             float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
#             for r in records
#         )
#         student_average = round(student_total / num_subjects, 2) if num_subjects else 0
#         total_students = len(class_totals)
#         class_average = round(sum(class_totals.values()) / len(class_totals), 2)
#         position = next((i + 1 for i, (stud_id, _) in enumerate(sorted_totals) if stud_id == sid), None)
#         highest_in_class = max(class_totals.values(), default=0)
#         lowest_in_class = min(class_totals.values(), default=0)
#         final_grade = records[0].grade_letter if records else ""

#         # --- Header Section (Logo + School Info in Flex Layout) ---
#         logo_img = None
#         if school and getattr(school, 'logo', None):
#             try:
#                 logo_data = io.BytesIO(requests.get(school.logo.url).content)
#                 logo_img = RLImage(logo_data, width=80, height=80)
#             except Exception:
#                 pass

#         # School details
#         school_name = f"<b>{school.school_name or 'Best Academy, Abuja'}</b>"
#         school_motto = f"<i>{school.school_motto or 'Motto: Knowledge for Excellence'}</i>"
#         school_address = f"{school.school_address or 'Tunga'}"

#         school_details = [
#             Paragraph(school_name, ParagraphStyle(name='SchoolName', fontSize=14, alignment=TA_LEFT)),
#             Spacer(1, 8),  # 4 points of vertical space
#             Paragraph(school_motto, ParagraphStyle(name='SchoolMotto', fontSize=10, alignment=TA_LEFT)),
#             Spacer(1, 8),  # 2 points of vertical space
#             Paragraph(school_address, ParagraphStyle(name='SchoolAddress', fontSize=9, alignment=TA_LEFT))
#         ]


#         # Simulate flexbox with table (Logo | School Info)
#         header_table = Table(
#             [[logo_img if logo_img else "", school_details]],
#             colWidths=[90, 400]
#         )
#         header_table.setStyle(TableStyle([
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ('LEFTPADDING', (0, 0), (-1, -1), 5),
#             ('RIGHTPADDING', (0, 0), (-1, -1), 5),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
#             ('TOPPADDING', (0, 0), (-1, -1), 0),
#         ]))
#         elements.append(header_table)
#         elements.append(Spacer(1, 10))

#         hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
#         elements.append(hr)


#         # --- Title ---
#         elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
#         elements.append(Spacer(1, 10))

#         # --- Student Info (with Grid Borders) ---
#         full_name = f"{student.first_name or ''} {student.last_name or ''}".strip()

#         student_info_data = [
#             [f"Name: {student.first_name} {student.last_name}", f"Class: {result_class}", f"Term: {term.name}"],
#             [f"Session: {session.name}", f"No. in Class: {total_students}", f"Position: {position} of {total_students}"],
#             [f"Total Score: {student_total}", f"Average Score: {student_average}", f"Class Average: {class_average}"],
#             [f"Highest in Class: {highest_in_class}", f"Lowest in Class: {lowest_in_class}", f"Final Grade: {final_grade}"],
#         ]

#         student_table = Table(student_info_data, colWidths=[180, 180, 180])
#         student_table.setStyle(TableStyle([
#             ('GRID', (0, 0), (-1, -1), 0.6, colors.grey),
#             ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
#             ('FONTSIZE', (0, 0), (-1, -1), 10),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ]))
#         elements += [student_table, Spacer(1, 15)]

#         max_ca = school.max_ca_score if school else 10
#         max_mid = school.max_midterm_score if school else 30
#         max_exam = school.max_exam_score if school else 60

#         # --- Subject Table (with Grid) ---
#         header_style = ParagraphStyle(name='HeaderStyle', fontName='Helvetica-Bold', fontSize=7, alignment=1)
#         # Use f-strings to insert actual max values
#         headers = [
#             "Subject",
#             f"CA<br/>({max_ca})",
#             f"Midterm<br/>({max_mid})",
#             f"Exam<br/>({max_exam})",
#             "Total",
#             "Per (%)",
#             "Grade",
#             "Class<br/>Ave",
#             "POS",
#             "Out<br/>Of",
#             "High<br/>In<br/>Class",
#             "Low<br/>In<br/>Class",
#             "Remark"
#         ]

#         table_data = [[Paragraph(h, header_style) for h in headers]]

#         for r in records:
#             ca = float(r.ca_score or 0)
#             mid = float(r.midterm_score or 0)
#             exam = float(r.exam_score or 0)
#             total = ca + mid + exam
#             max_total = sum([10 if ca > 0 else 0, 30 if mid > 0 else 0, 60 if exam > 0 else 0])
#             percentage = round((total / max_total) * 100) if max_total else 0

#             subject_results = all_results.filter(subject=r.subject)
#             class_avg = round(sum(
#                 float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#                 for s in subject_results
#             ) / len(subject_results), 2) if subject_results else 0
#             high_in_class = max([
#                 float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#                 for s in subject_results
#             ], default=0)
#             low_in_class = min([
#                 float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#                 for s in subject_results
#             ], default=0)
#             pos_sorted = sorted([
#                 (s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
#                 for s in subject_results
#             ], key=lambda x: x[1], reverse=True)
#             pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == sid), None)

#             row = [
#                 r.subject.title, str(ca), str(mid), str(exam), str(total),
#                 f"{percentage}", r.grade_letter, str(class_avg), str(pos),
#                 str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark
#             ]
#             table_data.append([Paragraph(str(x), style_center) for x in row])

#         page_width = A4[0] - doc.leftMargin - doc.rightMargin
#         col_fractions = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
#         col_widths = [page_width * frac for frac in col_fractions]

#         result_table = Table(table_data, colWidths=col_widths)
#         result_table.setStyle(TableStyle([
#             ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
#             ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 6),
#             ('FONTSIZE', (0, 1), (-1, -1), 6),
#             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ]))
#         elements += [result_table, Spacer(1, 15)]

#         # --- Grading Scale ---
#         elements.append(Paragraph("<b>GRADING SCALE</b>", style_left))
#         elements.append(Spacer(1, 4))
#         elements.append(Paragraph("A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39", style_left))
#         elements.append(Spacer(1, 15))

#         behavior = StudentBehaviorRecord.objects.filter(
           
#             session_id=session_id,
#             term_id=term_id
#         ).first()

#         elements.append(hr)

#         # ── Behavior / Form Teacher ────────────────────────────────────────
#         if behavior:
#             elements.append(Spacer(1, 10))
#             if behavior.form_teacher and behavior.form_teacher.user:
#                 elements.append(Paragraph(
#                     f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}",
#                     style_left
#                 ))
#             else:
#                 elements.append(Paragraph("<b>Form Teacher:</b> N/A", style_left))
#         elements.append(hr)
        
#         elements.append(hr)

#         # --- Comments & Signatures ---
#         if school and getattr(school, 'teacher_signature', None):
#             try:
#                 sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
#                 sig_img = RLImage(sig_data, width=100, height=40)
#                 elements.append(sig_img)
#             except Exception:
#                 pass

#         elements.append(Spacer(1, 10))

#         if school and getattr(school, 'principal_signature', None):
#             try:
#                 sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
#                 sig_img = RLImage(sig_data, width=100, height=40)
#                 elements.append(sig_img)
#             except Exception:
#                 pass

#         elements.append(PageBreak())

#     doc.build(elements)
#     return response


# def download_class_reports_pdf(request, result_class, session_id, term_id):
#     import re

#     # Clean class name from URL e.g. "SS2 Best Academy, Abuja" -> "SS2"
#     import re
#     display_class = result_class.strip().split()[0]  # e.g. "SS2"
#     print(f"DB query class: '{result_class}' | Display class: '{display_class}'")

#     # --- Fetch all results ---
#     all_results = Result_Portal.objects.filter(
#         result_class=result_class,
#         session_id=session_id,
#         term_id=term_id
#     ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('student__username', 'subject__title')

#     if not all_results.exists():
#         return HttpResponse("No results found for this class.", status=404)

#     # --- Group by student ---
#     students = {}
#     for res in all_results:
#         sid = res.student_id
#         if sid not in students:
#             students[sid] = {
#                 'student': res.student,
#                 'records': [],
#                 'school': res.schools,
#                 'session': res.session,
#                 'term': res.term
#             }
#         students[sid]['records'].append(res)

#     # --- Compute totals for ranking ---
#     class_totals = {}
#     for res in all_results:
#         sid = res.student_id
#         total = float(res.ca_score or 0) + float(res.midterm_score or 0) + float(res.exam_score or 0)
#         class_totals[sid] = class_totals.get(sid, 0) + total
#     sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)

#     # --- PDF Setup ---
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="class_{display_class}_term_reports.pdf"'
#     doc = SimpleDocTemplate(response, pagesize=A4, topMargin=25, leftMargin=25, rightMargin=25, bottomMargin=30)

#     styles = getSampleStyleSheet()
#     style_left = styles["Normal"]
#     style_left.alignment = TA_LEFT
#     style_center = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)

#     elements = []

#     # --- Generate report for each student ---
#     for sid, data in students.items():
#         student = data['student']
#         records = data['records']
#         school  = data['school']
#         session = data['session']
#         term    = data['term']

#         # --- Student stats ---
#         num_subjects   = len(records)
#         student_total  = sum(
#             float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
#             for r in records
#         )
#         student_average  = round(student_total / num_subjects, 2) if num_subjects else 0
#         total_students   = len(class_totals)
#         class_average    = round(sum(class_totals.values()) / len(class_totals), 2)
#         position         = next((i + 1 for i, (stud_id, _) in enumerate(sorted_totals) if stud_id == sid), None)
#         highest_in_class = max(class_totals.values(), default=0)
#         lowest_in_class  = min(class_totals.values(), default=0)
#         final_grade      = records[0].grade_letter if records else ""

#         # --- Header Section ---
#         logo_img = None
#         if school and getattr(school, 'logo', None):
#             try:
#                 logo_data = io.BytesIO(requests.get(school.logo.url).content)
#                 logo_img  = RLImage(logo_data, width=80, height=80)
#             except Exception:
#                 pass

#         school_name    = f"<b>{school.school_name or 'Best Academy, Abuja'}</b>"
#         school_motto   = f"<i>{school.school_motto or 'Motto: Knowledge for Excellence'}</i>"
#         school_address = f"{school.school_address or 'Tunga'}"

#         school_details = [
#             Paragraph(school_name,    ParagraphStyle(name='SchoolName',    fontSize=14, alignment=TA_LEFT)),
#             Spacer(1, 8),
#             Paragraph(school_motto,   ParagraphStyle(name='SchoolMotto',   fontSize=10, alignment=TA_LEFT)),
#             Spacer(1, 8),
#             Paragraph(school_address, ParagraphStyle(name='SchoolAddress', fontSize=9,  alignment=TA_LEFT)),
#         ]

#         header_table = Table(
#             [[logo_img if logo_img else "", school_details]],
#             colWidths=[90, 400]
#         )
#         header_table.setStyle(TableStyle([
#             ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
#             ('LEFTPADDING',   (0, 0), (-1, -1), 5),
#             ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
#             ('TOPPADDING',    (0, 0), (-1, -1), 0),
#         ]))
#         elements.append(header_table)
#         elements.append(Spacer(1, 10))

#         hr = HRFlowable(width="100%", thickness=0.5, color=colors.blue)
#         elements.append(hr)

#         # --- Title ---
#         elements.append(Paragraph("<b><u>TERM REPORT CARD</u></b>", style_center))
#         elements.append(Spacer(1, 10))

#         # --- Student Info Table ---
#         cell_style = ParagraphStyle(
#             name='CellStyle',
#             fontName='Helvetica',
#             fontSize=9,
#             leading=14,
#             spaceAfter=2,
#             spaceBefore=2,
#         )

#         student_info_data = [
#             [
#                 Paragraph(f"<b>Name:</b> {student.first_name} {student.last_name}", cell_style),
#                 Paragraph(f"<b>Class:</b> {display_class}", cell_style),
#                 Paragraph(f"<b>Term:</b> {term.name}", cell_style),
#             ],
#             [
#                 Paragraph(f"<b>Session:</b> {session.name}", cell_style),
#                 Paragraph(f"<b>No. in Class:</b> {total_students}", cell_style),
#                 Paragraph(f"<b>Position:</b> {position} of {total_students}", cell_style),
#             ],
#             [
#                 Paragraph(f"<b>Total Score:</b> {student_total}", cell_style),
#                 Paragraph(f"<b>Average Score:</b> {student_average}", cell_style),
#                 Paragraph(f"<b>Class Average:</b> {class_average}", cell_style),
#             ],
#             [
#                 Paragraph(f"<b>Highest in Class:</b> {highest_in_class}", cell_style),
#                 Paragraph(f"<b>Lowest in Class:</b> {lowest_in_class}", cell_style),
#                 Paragraph(f"<b>Final Grade:</b> {final_grade}", cell_style),
#             ],
#         ]

#         student_table = Table(student_info_data, colWidths=[180, 180, 180])
#         student_table.setStyle(TableStyle([
#             ('GRID',          (0, 0), (-1, -1), 0.6, colors.grey),
#             ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
#             ('FONTSIZE',      (0, 0), (-1, -1), 9),
#             ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
#             ('TOPPADDING',    (0, 0), (-1, -1), 6),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#             ('LEFTPADDING',   (0, 0), (-1, -1), 8),
#             ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
#         ]))
#         elements += [student_table, Spacer(1, 15)]

#         max_ca   = float(school.max_ca_score)      if school else 10.0
#         max_mid  = float(school.max_midterm_score) if school else 30.0
#         max_exam = float(school.max_exam_score)    if school else 60.0

#         # --- Subject Table ---
#         header_style = ParagraphStyle(
#             name='HeaderStyle', fontName='Helvetica-Bold', fontSize=7, alignment=1
#         )
#         headers = [
#             "Subject",
#             f"CA\\n({max_ca})",
#             f"Midterm\\n({max_mid})",
#             f"Exam\\n({max_exam})",
#             "Total",
#             "Per (%)",
#             "Grade",
#             "Class\\nAve",
#             "POS",
#             "Out\\nOf",
#             "High\\nIn\\nClass",
#             "Low\\nIn\\nClass",
#             "Remark",
#         ]

#         table_data = [[Paragraph(h, header_style) for h in headers]]

#         for r in records:
#             ca    = float(r.ca_score    or 0)
#             mid   = float(r.midterm_score or 0)
#             exam  = float(r.exam_score  or 0)
#             total = ca + mid + exam

#             max_total  = (max_ca if ca > 0 else 0.0) + (max_mid if mid > 0 else 0.0) + (max_exam if exam > 0 else 0.0)
#             percentage = round((total / max_total) * 100) if max_total else 0

#             # Strip JSS/SS prefix from subject title
#             # Remove class suffix like JSS1, SS1, JSS2, SS2 etc.
#             words = r.subject.title.split()
#             clean_words = [
#                 w for w in words
#                 if not any(w.upper().startswith(prefix) for prefix in ['JSS', 'SS'])
#             ]
#             clean_title = ' '.join(clean_words).strip()
#             # print(f"Original: '{r.subject.title}' -> Cleaned: '{clean_title}'")

#             subject_results = all_results.filter(subject=r.subject)
#             subject_scores  = [
#                 float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0)
#                 for s in subject_results
#             ]
#             class_avg    = round(sum(subject_scores) / len(subject_scores), 2) if subject_scores else 0
#             high_in_class = max(subject_scores, default=0)
#             low_in_class  = min(subject_scores, default=0)

#             pos_sorted = sorted(
#                 [(s.student_id, float(s.ca_score or 0) + float(s.midterm_score or 0) + float(s.exam_score or 0))
#                  for s in subject_results],
#                 key=lambda x: x[1], reverse=True
#             )
#             pos = next((i + 1 for i, (sid_, _) in enumerate(pos_sorted) if sid_ == sid), None)

#             row = [
#                 clean_title, str(ca), str(mid), str(exam), str(total),
#                 str(percentage), r.grade_letter, str(class_avg), str(pos),
#                 str(len(subject_results)), str(high_in_class), str(low_in_class), r.remark
#             ]
#             table_data.append([Paragraph(str(x), style_center) for x in row])

#         page_width     = A4[0] - doc.leftMargin - doc.rightMargin
#         col_fractions  = [0.10, 0.05, 0.08, 0.06, 0.07, 0.05, 0.07, 0.05, 0.05, 0.06, 0.06, 0.10, 0.20]
#         col_widths     = [page_width * frac for frac in col_fractions]

#         result_table = Table(table_data, colWidths=col_widths)
#         result_table.setStyle(TableStyle([
#             ('GRID',       (0, 0), (-1, -1), 0.4, colors.lightgrey),
#             ('BACKGROUND', (0, 0), (-1,  0), colors.whitesmoke),
#             ('FONTNAME',   (0, 0), (-1,  0), 'Helvetica-Bold'),
#             ('FONTSIZE',   (0, 0), (-1,  0), 6),
#             ('FONTSIZE',   (0, 1), (-1, -1), 6),
#             ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
#             ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
#         ]))
#         elements += [result_table, Spacer(1, 15)]

#         # --- Grading Scale ---
#         elements.append(Paragraph("<b>GRADING SCALE</b>", style_left))
#         elements.append(Spacer(1, 4))
#         elements.append(Paragraph(
#             "A = 70–100 | B = 60–69 | C = 50–59 | D = 45–49 | E = 40–44 | F = 0–39",
#             style_left
#         ))
#         elements.append(Spacer(1, 15))

#         behavior = StudentBehaviorRecord.objects.filter(
#             session_id=session_id,
#             term_id=term_id
#         ).first()

#         elements.append(hr)

#         # --- Form Teacher ---
#         if behavior:
#             elements.append(Spacer(1, 10))
#             if behavior.form_teacher and behavior.form_teacher.user:
#                 elements.append(Paragraph(
#                     f"<b>Form Teacher:</b> {behavior.form_teacher.user.first_name} {behavior.form_teacher.user.last_name}",
#                     style_left
#                 ))
#             else:
#                 elements.append(Paragraph("<b>Form Teacher:</b> N/A", style_left))
#         elements.append(hr)
#         elements.append(hr)

#         # --- Signatures ---
#         if school and getattr(school, 'teacher_signature', None):
#             try:
#                 sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
#                 sig_img  = RLImage(sig_data, width=100, height=40)
#                 elements.append(sig_img)
#             except Exception:
#                 pass

#         elements.append(Spacer(1, 10))

#         if school and getattr(school, 'principal_signature', None):
#             try:
#                 sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
#                 sig_img  = RLImage(sig_data, width=100, height=40)
#                 elements.append(sig_img)
#             except Exception:
#                 pass

#         elements.append(PageBreak())

#     doc.build(elements)
#     return response


import re
from collections import defaultdict
from reportlab.lib.units import mm
def download_class_reports_pdf(request, result_class, session_id, term_id):
    from collections import defaultdict
    from reportlab.lib.units import mm

    # ── Clean display class ───────────────────────────────────────
    display_class = result_class.strip().split()[0]

    # ── Fetch all results ─────────────────────────────────────────
    all_results = Result_Portal.objects.filter(
        result_class=result_class,
        session_id=session_id,
        term_id=term_id
    ).select_related('student', 'subject', 'schools', 'session', 'term').order_by('student__username', 'subject__title')

    if not all_results.exists():
        return HttpResponse("No results found for this class.", status=404)

    # ── Group by student ──────────────────────────────────────────
    students = {}
    for res in all_results:
        sid = res.student_id
        if sid not in students:
            students[sid] = {
                'student': res.student,
                'records': [],
                'school':  res.schools,
                'session': res.session,
                'term':    res.term,
            }
        students[sid]['records'].append(res)

    # ── Class totals for ranking ──────────────────────────────────
    class_totals = {}
    for res in all_results:
        sid   = res.student_id
        total = float(res.ca_score or 0) + float(res.midterm_score or 0) + float(res.exam_score or 0)
        class_totals[sid] = class_totals.get(sid, 0) + total
    sorted_totals = sorted(class_totals.items(), key=lambda x: x[1], reverse=True)

    # ── Subject scores grouped (avoids N+1) ──────────────────────
    subject_scores_map = defaultdict(list)
    for res in all_results:
        score = float(res.ca_score or 0) + float(res.midterm_score or 0) + float(res.exam_score or 0)
        subject_scores_map[res.subject_id].append((res.student_id, score))

    # ── PDF Setup ─────────────────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="class_{display_class}_term_reports.pdf"'

    W, H   = A4
    MARGIN = 5 * mm
    INNER  = W - 2 * MARGIN

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        topMargin=8, bottomMargin=8,
        leftMargin=MARGIN, rightMargin=MARGIN
    )

    BLUE  = colors.HexColor("#1a4e8c")
    LBLUE = colors.HexColor("#d0e4f7")
    LGREY = colors.HexColor("#f2f2f2")

    S = {
        "report_title": ParagraphStyle("rt", fontSize=9,  fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, spaceAfter=4),
        "section_hd":   ParagraphStyle("sh", fontSize=8,  fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, spaceAfter=0),
        "cell_normal":  ParagraphStyle("cn", fontSize=7.5, fontName="Helvetica",
                                       alignment=TA_LEFT,   leading=10),
        "cell_center":  ParagraphStyle("cc", fontSize=7,   fontName="Helvetica",
                                       alignment=TA_CENTER, leading=9),
        "cell_hdr":     ParagraphStyle("ch", fontSize=7,   fontName="Helvetica-Bold",
                                       alignment=TA_CENTER, leading=9),
        "small":        ParagraphStyle("sm", fontSize=6.5, fontName="Helvetica",
                                       alignment=TA_LEFT,   leading=9),
        "comment":      ParagraphStyle("co", fontSize=8,   fontName="Helvetica",
                                       alignment=TA_LEFT,   leading=11, spaceAfter=3),
        "label":        ParagraphStyle("lb", fontSize=8,   fontName="Helvetica-Bold",
                                       alignment=TA_LEFT,   leading=10),
    }

    def hr_line(thickness=0.5, color=BLUE):
        return HRFlowable(width="100%", thickness=thickness, color=color,
                          spaceAfter=3, spaceBefore=3)

    def section_header(text):
        tbl = Table([[Paragraph(text, S["section_hd"])]], colWidths=[INNER])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LBLUE),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("BOX",           (0,0), (-1,-1), 0.5, BLUE),
        ]))
        return tbl

    def ordinal(n):
        if n is None: return "N/A"
        suffix = {1:"st", 2:"nd", 3:"rd"}.get(n if n < 20 else n % 10, "th")
        return f"{n}{suffix}"

    def trait_table(title, traits, width):
        hdr  = [[Paragraph(f"<b>{title}</b>", S["cell_hdr"]),
                 Paragraph("<b>Rating</b>",    S["cell_hdr"])]]
        rows = [[Paragraph(t, S["cell_normal"]), Paragraph(str(v), S["cell_center"])]
                for t, v in traits]
        tbl  = Table(hdr + rows, colWidths=[width * 0.75, width * 0.25])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  LBLUE),
            ("GRID",          (0,0), (-1,-1), 0.4, colors.grey),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, LGREY]),
        ]))
        return tbl

    elements = []

    # ════════════════════════════════════════════════════════════
    # Per-student loop
    # ════════════════════════════════════════════════════════════
    for sid, data in students.items():
        student    = data['student']
        records    = data['records']
        school     = data['school']
        session    = data['session']
        term       = data['term']
        is_midterm = getattr(term, 'is_midterm', False)

        # ── Stats ─────────────────────────────────────────────
        num_subjects     = len(records)
        student_total    = sum(
            float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
            for r in records
        )
        student_average  = round(student_total / num_subjects, 2) if num_subjects else 0
        total_students   = len(class_totals)
        class_average    = round(sum(class_totals.values()) / len(class_totals), 2) if class_totals else 0
        position         = next((i + 1 for i, (stud_id, _) in enumerate(sorted_totals) if stud_id == sid), None)
        highest_in_class = round(max(class_totals.values(), default=0), 2)
        lowest_in_class  = round(min(class_totals.values(), default=0), 2)
        final_grade      = records[0].grade_letter if records else ""
        final_average    = student_average

        max_ca   = float(school.max_ca_score)      if school and school.max_ca_score      else 10.0
        max_mid  = float(school.max_midterm_score) if school and school.max_midterm_score  else 20.0
        max_exam = float(school.max_exam_score)    if school and school.max_exam_score     else 70.0

        # ── 1. School Header ──────────────────────────────────
        logo_img = None
        if school and getattr(school, 'logo', None):
            try:
                logo_data = io.BytesIO(requests.get(school.logo.url).content)
                logo_img  = RLImage(logo_data, width=70, height=70)
            except Exception:
                pass

        school_name_str    = school.school_name    if school else "School Name"
        school_motto_str   = school.school_motto   if school else ""
        school_address_str = school.school_address if school else ""

        school_details = [
            Paragraph(f"<b>{school_name_str}</b>",
                      ParagraphStyle("SN2", fontSize=13, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Spacer(1, 4),
            Paragraph(f"<i>{school_motto_str}</i>",
                      ParagraphStyle("SM2", fontSize=9, fontName="Helvetica-Oblique", alignment=TA_CENTER)),
            Spacer(1, 4),
            Paragraph(school_address_str,
                      ParagraphStyle("SA2", fontSize=7.5, fontName="Helvetica", alignment=TA_CENTER)),
        ]

        if logo_img:
            header_tbl = Table(
                [[logo_img, school_details, logo_img]],
                colWidths=[70, INNER - 140, 70]
            )
        else:
            header_tbl = Table([[school_details]], colWidths=[INNER])

        header_tbl.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("RIGHTPADDING",  (0,0), (-1,-1), 4),
            ("TOPPADDING",    (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        elements.append(header_tbl)
        elements.append(hr_line(thickness=1.5, color=BLUE))

        elements.append(Paragraph(
            f"<b>REPORT SHEET FOR {term.name}, {session.name} ACADEMIC SESSION</b>",
            S["report_title"]
        ))
        elements.append(hr_line(thickness=0.5))
        elements.append(Spacer(1, 4))

        # ── 2. Student Info Grid ──────────────────────────────
        def ic(label, value):
            return Paragraph(f"<b>{label}:</b> {value}", S["cell_normal"])

        col3      = INNER / 3
        info_data = [
            [ic("Name",             f"{student.first_name} {student.last_name}"),
             ic("Gender",           getattr(student, 'gender', 'N/A') or 'N/A'),
             ic("Class",            display_class)],
            [ic("No. in Class",     total_students),
             ic("Total Score",      student_total),
             ic("Class Average",    class_average)],
            [ic("Highest In Class", highest_in_class),
             ic("Lowest In Class",  lowest_in_class),
             ic("Final Grade",      final_grade)],
            [ic("Final Average",    final_average),
             ic("POSITION",         ordinal(position)),
             ic("Next Term Begins", getattr(school, 'next_term_date', 'N/A') if school else 'N/A')],
        ]
        info_tbl = Table(info_data, colWidths=[col3, col3, col3])
        info_tbl.setStyle(TableStyle([
            ("GRID",          (0,0), (-1,-1), 0.4, colors.grey),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 5),
            ("RIGHTPADDING",  (0,0), (-1,-1), 5),
            ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, LGREY]),
        ]))
        elements += [info_tbl, Spacer(1, 6)]

        # ── 3. Subject Table ──────────────────────────────────
        elements.append(section_header("Subjects"))
        elements.append(Spacer(1, 2))

        if is_midterm:
            hdr_row = [Paragraph(h, S["cell_hdr"]) for h in [
                "Subjects",
                f"CA<br/>({int(max_ca)})",
                f"Midterm<br/>Exams<br/>({int(max_mid)})",
                "Total",
                "Per<br/>(%)",
                "Low.<br/>In<br/>Class",
                "High.<br/>In<br/>Class",
                "Class<br/>Average",
                "POS",
                "Out<br/>Of",
                "Grade",
                "Remark",
            ]]
        else:
            hdr_row = [Paragraph(h, S["cell_hdr"]) for h in [
                "Subjects",
                f"CA<br/>({int(max_ca)})",
                f"Midterm<br/>Exams<br/>({int(max_mid)})",
                f"Exams<br/>({int(max_exam)})",
                "Total",
                "Low.<br/>In<br/>Class",
                "High.<br/>In<br/>Class",
                "Class<br/>Average",
                "POS",
                "Out<br/>Of",
                "Grade",
                "Remark",
            ]]

        subj_data = [hdr_row]

        for r in records:
            ca    = float(r.ca_score      or 0)
            mid   = float(r.midterm_score or 0)
            exam  = float(r.exam_score    or 0)
            total = ca + mid + exam

            if is_midterm:
                midterm_total = ca + mid
                max_total     = max_ca + max_mid
                percentage    = round((midterm_total / max_total) * 100) if max_total else 0
            else:
                midterm_total = total
                percentage    = 0

            words       = r.subject.title.split()
            clean_title = ' '.join(
                w for w in words
                if not any(w.upper().startswith(p) for p in ['JSS', 'SS'])
            ).strip()

            s_entries = subject_scores_map[r.subject_id]
            s_scores  = [sc for _, sc in s_entries]
            s_count   = len(s_scores)
            s_avg     = round(sum(s_scores) / s_count, 2) if s_count else 0
            s_high    = max(s_scores, default=0)
            s_low     = min(s_scores, default=0)
            s_sorted  = sorted(s_entries, key=lambda x: x[1], reverse=True)
            s_pos     = next((i + 1 for i, (sid_, _) in enumerate(s_sorted) if sid_ == sid), None)

            remark_style = ParagraphStyle(
                "rs", fontSize=7, fontName="Helvetica", alignment=TA_LEFT, leading=9,
                textColor=colors.HexColor("#c00000")
                if r.remark and r.remark.lower() == "fail" else colors.black
            )

            if is_midterm:
                subj_data.append([
                    Paragraph(clean_title,                S["cell_normal"]),
                    Paragraph(str(ca),                    S["cell_center"]),
                    Paragraph(str(mid),                   S["cell_center"]),
                    Paragraph(str(midterm_total),         S["cell_center"]),
                    Paragraph(f"{percentage}%",           S["cell_center"]),
                    Paragraph(str(s_low),                 S["cell_center"]),
                    Paragraph(str(s_high),                S["cell_center"]),
                    Paragraph(str(s_avg),                 S["cell_center"]),
                    Paragraph(ordinal(s_pos),             S["cell_center"]),
                    Paragraph(str(s_count),               S["cell_center"]),
                    Paragraph(f"<b>{r.grade_letter}</b>", S["cell_center"]),
                    Paragraph(r.remark or "",             remark_style),
                ])
            else:
                subj_data.append([
                    Paragraph(clean_title,                S["cell_normal"]),
                    Paragraph(str(ca),                    S["cell_center"]),
                    Paragraph(str(mid),                   S["cell_center"]),
                    Paragraph(str(exam),                  S["cell_center"]),
                    Paragraph(str(total),                 S["cell_center"]),
                    Paragraph(str(s_low),                 S["cell_center"]),
                    Paragraph(str(s_high),                S["cell_center"]),
                    Paragraph(str(s_avg),                 S["cell_center"]),
                    Paragraph(ordinal(s_pos),             S["cell_center"]),
                    Paragraph(str(s_count),               S["cell_center"]),
                    Paragraph(f"<b>{r.grade_letter}</b>", S["cell_center"]),
                    Paragraph(r.remark or "",             remark_style),
                ])

        if is_midterm:
            col_fracs = [0.18, 0.06, 0.10, 0.07, 0.07, 0.06, 0.06, 0.09, 0.06, 0.05, 0.06, 0.07]
        else:
            col_fracs = [0.18, 0.05, 0.09, 0.07, 0.06, 0.06, 0.06, 0.09, 0.06, 0.05, 0.06, 0.07]

        col_widths = [INNER * f for f in col_fracs]
        col_widths[-1] = INNER - sum(col_widths[:-1])

        subj_tbl = Table(subj_data, colWidths=col_widths, repeatRows=1)
        subj_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),  (-1,0),  LBLUE),
            ("GRID",          (0,0),  (-1,-1), 0.4, colors.grey),
            ("FONTSIZE",      (0,0),  (-1,-1), 7),
            ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),  (-1,-1), 3),
            ("BOTTOMPADDING", (0,0),  (-1,-1), 3),
            ("ROWBACKGROUNDS",(0,1),  (-1,-1), [colors.white, LGREY]),
        ]))
        elements += [subj_tbl, Spacer(1, 4)]

        grade_details = (
            getattr(school, 'grade_details', None) or
            "F = 0-45 | E8 = 45-50 | D7 = 50-55 | C6 = 55-60 | C5 = 60-65 | "
            "C4 = 65-70 | B3 = 70-75 | B2 = 75-91 | A1 = 91-100"
        )
        elements.append(Paragraph(
            f"<b>Grade Details:</b> {grade_details} | No. of Subjects: {num_subjects}",
            S["small"]
        ))
        elements.append(Spacer(1, 6))

        # ── 4 & 5: Only for non-midterm ───────────────────────
        if not is_midterm:
            # ── 4. Psychomotor & Affective ────────────────────
            elements.append(section_header("Psychomotor & Affective Traits"))
            elements.append(Spacer(1, 2))

            behavior = StudentBehaviorRecord.objects.filter(
                student=student,
                session_id=session_id,
                term_id=term_id
            ).first()

            half = INNER / 2

            if behavior:
                psycho_traits = [
                    ("HANDWRITING",        behavior.handwriting),
                    ("GAMES",              behavior.games),
                    ("SPORTS",             behavior.sports),
                    ("DRAWING & PAINTING", behavior.drawing_painting),
                    ("CRAFTS",             behavior.crafts),
                ]
                affective_traits = [
                    ("PUNCTUALITY",               behavior.punctuality),
                    ("ATTENDANCE",                behavior.attendance),
                    ("RELIABILITY",               behavior.reliability),
                    ("NEATNESS",                  behavior.neatness),
                    ("POLITENESS",                behavior.politeness),
                    ("HONESTY",                   behavior.honesty),
                    ("RELATIONSHIP WITH STUDENTS",behavior.relationship_with_students),
                    ("SELF CONTROL",              behavior.self_control),
                    ("ATTENTIVENESS",             behavior.attentiveness),
                    ("PERSEVERANCE",              behavior.perseverance),
                ]
            else:
                psycho_traits    = [("HANDWRITING",""), ("GAMES",""), ("SPORTS",""),
                                    ("DRAWING & PAINTING",""), ("CRAFTS","")]
                affective_traits = [("PUNCTUALITY",""), ("ATTENDANCE",""), ("RELIABILITY",""),
                                    ("NEATNESS",""), ("POLITENESS",""), ("HONESTY",""),
                                    ("RELATIONSHIP WITH STUDENTS",""), ("SELF CONTROL",""),
                                    ("ATTENTIVENESS",""), ("PERSEVERANCE","")]

            side_tbl = Table(
                [[trait_table("Default Psychomotor Rating",      psycho_traits,    half),
                  trait_table("Default Affective Traits Rating", affective_traits, half)]],
                colWidths=[half, half]
            )
            side_tbl.setStyle(TableStyle([
                ("VALIGN",       (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING",  (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ]))
            elements += [side_tbl, Spacer(1, 6)]

            # ── 5. Comments & Signatures ──────────────────────
            elements.append(section_header("Remarks & Signatures"))
            elements.append(Spacer(1, 3))

            form_teacher_name = "N/A"
            if behavior:
                teachers = behavior.form_teacher.all()
                if teachers.exists():
                    form_teacher_name = ", ".join(
                        f"{t.first_name} {t.last_name}".strip() for t in teachers
                    )

            form_comment      = (behavior.form_teacher_comment if behavior else "") or ""
            principal_comment = (behavior.principal_comment    if behavior else "") or ""

            comments_data = [
                [Paragraph(f"<b>Form Teacher:</b> {form_teacher_name}", S["label"]), ""],
                [Paragraph("<b>Form Teacher Comment:</b>", S["label"]), ""],
                [Paragraph(form_comment      or "No comment.", S["comment"]), ""],
                [Paragraph("<b>PRINCIPAL'S REMARK:</b>",    S["label"]), ""],
                [Paragraph(principal_comment or "No remark.", S["comment"]), ""],
                [
                    Paragraph("<b>Form Teacher SIGNATURE:</b> _______________________", S["label"]),
                    Paragraph("<b>PRINCIPAL'S SIGNATURE:</b> _______________________",  S["label"]),
                ],
            ]

            if school and getattr(school, 'teacher_signature', None):
                try:
                    sig_data = io.BytesIO(requests.get(school.teacher_signature.url).content)
                    sig_img  = RLImage(sig_data, width=100, height=40)
                    comments_data[5][0] = sig_img
                except Exception:
                    pass

            if school and getattr(school, 'principal_signature', None):
                try:
                    sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                    sig_img  = RLImage(sig_data, width=100, height=40)
                    comments_data[5][1] = sig_img
                except Exception:
                    pass

            comment_tbl = Table(comments_data, colWidths=[INNER * 0.6, INNER * 0.4])
            comment_tbl.setStyle(TableStyle([
                ("GRID",          (0,0), (-1,-1), 0.3, colors.lightgrey),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("LEFTPADDING",   (0,0), (-1,-1), 6),
                ("SPAN",          (0,0), (1,0)),
                ("SPAN",          (0,1), (1,1)),
                ("SPAN",          (0,2), (1,2)),
                ("SPAN",          (0,3), (1,3)),
                ("SPAN",          (0,4), (1,4)),
                ("BACKGROUND",    (0,0), (-1,0),  LGREY),
                ("BACKGROUND",    (0,3), (-1,3),  LGREY),
            ]))
            elements.append(comment_tbl)

        # ── Principal signature always shows for midterm ──────
        if is_midterm:
            elements.append(Spacer(1, 10))
            elements.append(section_header("Principal's Signature"))
            elements.append(Spacer(1, 6))
            if school and getattr(school, 'principal_signature', None):
                try:
                    sig_data = io.BytesIO(requests.get(school.principal_signature.url).content)
                    sig_img  = RLImage(sig_data, width=100, height=40)
                    elements.append(sig_img)
                except Exception:
                    elements.append(Paragraph(
                        "<b>PRINCIPAL'S SIGNATURE:</b> _______________________",
                        S["label"]
                    ))
            else:
                elements.append(Paragraph(
                    "<b>PRINCIPAL'S SIGNATURE:</b> _______________________",
                    S["label"]
                ))

        elements.append(PageBreak())

    doc.build(elements)
    return response


from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# from .tasks import generate_class_pdf_task


# @csrf_exempt
# def trigger_class_pdf(request, result_class, session_id, term_id):
#     task = generate_class_pdf_task.delay(result_class, session_id, term_id)
#     return JsonResponse({"task_id": task.id}, status=202)


def class_pdf_status(request, task_id):
    result = AsyncResult(task_id)

    if result.state == "PENDING":
        return JsonResponse({"state": "PENDING", "percent": 0, "step": "Waiting in queue..."})

    elif result.state == "PROGRESS":
        meta = result.info or {}
        return JsonResponse({
            "state": "PROGRESS",
            "percent": meta.get("percent", 0),
            "step": meta.get("step", "Processing..."),
        })

    elif result.state == "SUCCESS":
        return JsonResponse({
            "state": "SUCCESS",
            "download_url": result.result.get("download_url"),
            "filename": result.result.get("filename"),
        })

    else:
        return JsonResponse({"state": "FAILURE", "error": str(result.info)}, status=500)
    


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
    Uses bulk_update/bulk_create for maximum performance across multiple schools/teachers.
    """
    teacher = _get_teacher_for_request(request.user)

    # ── Fetch objects ──────────────────────────────────────────────────────
    class_obj  = get_object_or_404(CourseGrade, id=class_id)
    course_obj = get_object_or_404(Courses, id=subject_id)
    session    = get_object_or_404(Session, id=session_id)
    term       = get_object_or_404(Term, id=term_id)

    # ── Students ───────────────────────────────────────────────────────────
    students = list(class_obj.students.all().order_by('id'))

    # ── School max scores ──────────────────────────────────────────────────
    school      = getattr(class_obj, 'schools', None)
    max_ca      = Decimal(str(getattr(school, 'max_ca_score',      '10.0') or '10.0'))
    max_midterm = Decimal(str(getattr(school, 'max_midterm_score', '30.0') or '30.0'))
    max_exam    = Decimal(str(getattr(school, 'max_exam_score',    '60.0') or '60.0'))

    # ── Formset ────────────────────────────────────────────────────────────
    ResultFormset = formset_factory(ResultRowForm, extra=0)

    # ── Context shared across GET and POST ─────────────────────────────────
    base_context = {
        "class_obj":   class_obj,
        "subject_obj": course_obj,
        "session":     session,
        "term":        term,
        "max_ca":      max_ca,
        "max_midterm": max_midterm,
        "max_exam":    max_exam,
    }

    # ── POST: Save results ─────────────────────────────────────────────────
    if request.method == "POST":
        formset = ResultFormset(request.POST)

        if formset.is_valid():
            to_update = []
            to_create = []

            with transaction.atomic():
                # ✅ select_for_update INSIDE atomic block
                existing_results = Result_Portal.objects.filter(
                    student_id__in=[s.id for s in students],
                    subject=course_obj,
                    session=session,
                    term=term,
                    result_class=class_obj.name
                ).select_for_update()

                existing_by_student = {r.student_id: r for r in existing_results}

                for form in formset:
                    cd = form.cleaned_data
                    student_id = cd.get('student_id')
                    if not student_id:
                        continue

                    # Cap scores at school maximums
                    ca    = min(Decimal(str(cd.get('ca_score')      or 0)), max_ca)
                    mid   = min(Decimal(str(cd.get('midterm_score') or 0)), max_midterm)
                    exam  = min(Decimal(str(cd.get('exam_score')    or 0)), max_exam)
                    total = ca + mid + exam

                    existing = existing_by_student.get(int(student_id))

                    if existing:
                        existing.ca_score      = ca
                        existing.midterm_score = mid
                        existing.exam_score    = exam
                        existing.total_score   = total
                        to_update.append(existing)
                    else:
                        to_create.append(Result_Portal(
                            student_id=student_id,
                            subject=course_obj,
                            term=term,
                            session=session,
                            result_class=class_obj.name,
                            schools=school,
                            ca_score=ca,
                            midterm_score=mid,
                            exam_score=exam,
                            total_score=total,
                        ))

                # ── 2 queries total regardless of class size ───────────────
                if to_update:
                    Result_Portal.objects.bulk_update(
                        to_update,
                        ['ca_score', 'midterm_score', 'exam_score', 'total_score']
                    )
                if to_create:
                    Result_Portal.objects.bulk_create(
                        to_create,
                        update_conflicts=True,
                        update_fields=['ca_score', 'midterm_score', 'exam_score', 'total_score'],
                        unique_fields=['student_id', 'subject_id', 'term_id', 'session_id'],
                    )

            messages.success(request, "All results have been saved successfully!")
            return redirect(reverse('portal:enter_results', kwargs={
                'class_id':    class_id,
                'subject_id':  subject_id,
                'session_id':  session_id,
                'term_id':     term_id,
            }))

        else:
            # Invalid formset — return with errors
            forms_with_students = list(zip(formset.forms, students))
            return render(request, "portal/enter_results.html", {
                **base_context,
                "formset":             formset,
                "forms_with_students": forms_with_students,
            })

    # ── GET: Display formset ───────────────────────────────────────────────
    # ✅ No select_for_update on GET — just a plain read
    existing_results = Result_Portal.objects.filter(
        student_id__in=[s.id for s in students],
        subject=course_obj,
        session=session,
        term=term,
        result_class=class_obj.name
    )

    existing_by_student = {r.student_id: r for r in existing_results}

    initial_data = [
        {
            'student_id':         s.id,
            'existing_result_id': existing_by_student[s.id].id if s.id in existing_by_student else '',
            'ca_score':           existing_by_student[s.id].ca_score      if s.id in existing_by_student else Decimal('0.00'),
            'midterm_score':      existing_by_student[s.id].midterm_score if s.id in existing_by_student else Decimal('0.00'),
            'exam_score':         existing_by_student[s.id].exam_score    if s.id in existing_by_student else Decimal('0.00'),
        }
        for s in students
    ]

    formset = ResultFormset(initial=initial_data)
    forms_with_students = list(zip(formset.forms, students))

    return render(request, "portal/enter_results.html", {
        **base_context,
        "formset":             formset,
        "forms_with_students": forms_with_students,
    })

#working codes
# @require_reportcard_subscription
# @login_required
# def enter_results_for_class_subject(request, class_id, subject_id, session_id, term_id):
#     """
#     Render table of students for a class/subject and handle POST to save all results.
#     Uses update_or_create to save results safely.
#     """
#     teacher = _get_teacher_for_request(request.user)
#     # Fetch class, course, session, term
#     class_obj = get_object_or_404(CourseGrade, id=class_id)
#     course_obj = get_object_or_404(Courses, id=subject_id)
#     session = get_object_or_404(Session, id=session_id)
#     term = get_object_or_404(Term, id=term_id)

#     # Fetch all students for this class
#     students = class_obj.students.all().order_by('id')

#     # School max scores
#     school = getattr(class_obj, 'schools', None)
#     max_ca = getattr(school, 'max_ca_score', Decimal('10.0')) if school else Decimal('10.0')
#     max_midterm = getattr(school, 'max_midterm_score', Decimal('30.0')) if school else Decimal('30.0')
#     max_exam = getattr(school, 'max_exam_score', Decimal('60.0')) if school else Decimal('60.0')

#     # Formset
#     ResultFormset = formset_factory(ResultRowForm, extra=0)

#     # GET: prepare initial data
#     existing_results = Result_Portal.objects.filter(
#         student_id__in=students.values_list('id', flat=True),
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

#     if request.method == "POST":
#         formset = ResultFormset(request.POST)
#         if formset.is_valid():
#             with transaction.atomic():
#                 for form in formset:
#                     student_id = form.cleaned_data.get('student_id')
#                     ca = min(Decimal(form.cleaned_data.get('ca_score') or 0), max_ca)
#                     mid = min(Decimal(form.cleaned_data.get('midterm_score') or 0), max_midterm)
#                     exam = min(Decimal(form.cleaned_data.get('exam_score') or 0), max_exam)
#                     total = ca + mid + exam

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

#             # Add success message
#             messages.success(request, "All results have been saved successfully!")

#             # Redirect to same page to show message
#             return redirect(reverse('portal:enter_results', kwargs={
#                 'class_id': class_id,
#                 'subject_id': subject_id,
#                 'session_id': session_id,
#                 'term_id': term_id
#             }))
#         else:
#             # Formset invalid: show errors
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
#     else:
#         # GET: display formset
#         formset = ResultFormset(initial=initial_data)
#         forms_with_students = zip(formset.forms, students)
#         return render(request, "portal/enter_results.html", {
#             "formset": formset,
#             "forms_with_students": forms_with_students,
#             "class_obj": class_obj,
#             "subject_obj": course_obj,
#             "session": session,
#             "term": term,
#             "max_ca": max_ca,
#             "max_midterm": max_midterm,
#             "max_exam": max_exam,
#         })


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
@login_required(login_url='teacher:teacher_login')
def generate_form_teacher_comment(request, student_id):
    student = get_object_or_404(NewUser, id=student_id)

    session_id = request.GET.get("session")
    term_id    = request.GET.get("term")
    class_id   = request.GET.get("class")

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

    def score_label(val):
        """Convert numeric score to descriptive label using 1-5 scale."""
        try:
            v = int(val)
        except (TypeError, ValueError):
            return "not assessed"
        if v == 5: return "excellent"
        if v == 4: return "good"
        if v == 3: return "fair"
        if v == 2: return "poor"
        if v == 1: return "very poor"
        return "not assessed"

    if behavior_record:
        hw           = request.GET.get("handwriting",  behavior_record.handwriting)
        games        = request.GET.get("games",         behavior_record.games)
        sports       = request.GET.get("sports",        behavior_record.sports)
        drawing      = request.GET.get("drawing",       behavior_record.drawing_painting)
        crafts       = request.GET.get("crafts",        behavior_record.crafts)
        punctuality  = request.GET.get("punctuality",   behavior_record.punctuality)
        attendance   = request.GET.get("attendance",    behavior_record.attendance)
        reliability  = request.GET.get("reliability",   behavior_record.reliability)
        neatness     = request.GET.get("neatness",      behavior_record.neatness)
        politeness   = request.GET.get("politeness",    behavior_record.politeness)
        honesty      = request.GET.get("honesty",       behavior_record.honesty)
        relationship = request.GET.get("relationship",  behavior_record.relationship_with_students)
        self_control = request.GET.get("self_control",  behavior_record.self_control)
        attentive    = request.GET.get("attentive",     behavior_record.attentiveness)
        perseverance = request.GET.get("perseverance",  behavior_record.perseverance)

        # Build rich behavior summary with labels
        behavior_summary = (
            f"Psychomotor Skills (Scale: 1=Very Poor, 2=Poor, 3=Fair, 4=Good, 5=Excellent):\n"
            f"  - Handwriting: {hw}/5 ({score_label(hw)})\n"
            f"  - Games: {games}/5 ({score_label(games)})\n"
            f"  - Sports: {sports}/5 ({score_label(sports)})\n"
            f"  - Drawing/Painting: {drawing}/5 ({score_label(drawing)})\n"
            f"  - Crafts: {crafts}/5 ({score_label(crafts)})\n\n"
            f"Affective/Social Traits (Scale: 1=Very Poor, 2=Poor, 3=Fair, 4=Good, 5=Excellent):\n"
            f"  - Punctuality: {punctuality}/5 ({score_label(punctuality)})\n"
            f"  - Attendance: {attendance}/5 ({score_label(attendance)})\n"
            f"  - Reliability: {reliability}/5 ({score_label(reliability)})\n"
            f"  - Neatness: {neatness}/5 ({score_label(neatness)})\n"
            f"  - Politeness: {politeness}/5 ({score_label(politeness)})\n"
            f"  - Honesty: {honesty}/5 ({score_label(honesty)})\n"
            f"  - Relationship with Students: {relationship}/5 ({score_label(relationship)})\n"
            f"  - Self-Control: {self_control}/5 ({score_label(self_control)})\n"
            f"  - Attentiveness: {attentive}/5 ({score_label(attentive)})\n"
            f"  - Perseverance: {perseverance}/5 ({score_label(perseverance)})"
        )
    else:
        behavior_summary = "No behavior records available for this term."

    # ---- GET RESULTS ----
    results = Result_Portal.objects.filter(
        student=student,
        session_id=int(session_id),
        term_id=int(term_id)
    ).select_related("subject").order_by('-total_score')

    if not results.exists():
        return JsonResponse({"comment": "No results found for this student."})

    # Build subject summary with performance labels
    strong_subjects  = []
    weak_subjects    = []
    subject_lines    = []

    for r in results:
        try:
            score = float(r.total_score)
        except (TypeError, ValueError):
            score = 0

        subject_lines.append(
            f"  - {r.subject.title}: {r.total_score}/100 (Grade: {r.grade_letter})"
        )
        if score >= 70:
            strong_subjects.append(r.subject.title)
        elif score < 50:
            weak_subjects.append(r.subject.title)

    subject_scores_text = "\n".join(subject_lines)

    # Compute overall average
    total_scores = []
    for r in results:
        try:
            total_scores.append(float(r.total_score))
        except (TypeError, ValueError):
            pass
    avg = round(sum(total_scores) / len(total_scores), 1) if total_scores else 0

    if avg >= 75:
        overall_performance = "outstanding"
    elif avg >= 60:
        overall_performance = "commendable"
    elif avg >= 50:
        overall_performance = "satisfactory"
    else:
        overall_performance = "below expectation"

    strong_text = ", ".join(strong_subjects[:3]) if strong_subjects else "none highlighted"
    weak_text   = ", ".join(weak_subjects[:2])   if weak_subjects   else "none highlighted"

    first_name = student.first_name

    prompt = f"""
Below is a real Nigerian school teacher's end-of-term report card comment. Study the tone carefully:

EXAMPLE 1:
"Amaka has performed admirably this term, particularly in English Language and Biology where she scored above 80. She is a focused and reliable student who participates well in class. However, her performance in Mathematics requires more attention and consistent practice. I urge her to seek help early next term and approach difficult topics with the same confidence she shows in her strong subjects."

EXAMPLE 2:
"Chukwuemeka showed improvement in his overall conduct this term and his honesty and neatness have been noted. His scores in Civic Education and Christian Religious Studies are commendable. He is encouraged to work harder in Physics and Chemistry, as his current scores suggest he needs to revise more thoroughly. With greater effort and focus, I am confident he will perform better next term."

EXAMPLE 3:
"Fatima has been a diligent and punctual student throughout this term. Her performance in Islamic Studies and English Language is praiseworthy. She should, however, pay closer attention to her work in Further Mathematics and seek clarification whenever she encounters difficulty. I encourage her to maintain her good attitude and put in more effort to round off her academic performance."

Now write a similar comment for the student below. Write EXACTLY like a real teacher filling a report card — direct, honest, specific, and grounded. Do NOT use flowery or motivational-speaker language. Do NOT say things like "your potential shines brightly" or "every small step is a victory". Sound like a teacher, not a life coach.

Student: {student.first_name} {student.last_name}
Class Average: {avg}/100 ({overall_performance})
Strong subjects: {strong_text}
Weak subjects: {weak_text}

Subject Scores:
{subject_scores_text}

Behaviour:
{behavior_summary}

Rules:
- Use the student's first name ({first_name}) once naturally
- Maximum 3 sentences only, one paragraph, no bullet points
- Mention at least one specific subject by name
- Mention one behaviour trait if it stands out (good or poor)
- End with a clear, direct encouragement for next term
- Do NOT start with "I am pleased", "It is with pleasure", or "This term has been a journey"
- Sound like a real Nigerian secondary school teacher writing by hand on a report card
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a highly experienced school form teacher with 15 years of experience "
                        "writing thoughtful, personalized, and encouraging end-of-term student report comments. "
                        "Your comments are warm, specific, honest, and motivating. "
                        "You never write generic or templated comments — every student feels seen."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,   # slight creativity for variety across students
            max_tokens=150,
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

@login_required
def principal_dashboard(request):
    if not getattr(request.user, "is_principal", False):
        return HttpResponseForbidden("Access denied")

    school = request.user.school

    sessions = Session.objects.filter(school=school).order_by('name')
    terms    = Term.objects.filter(school=school).order_by('name')
    classes  = CourseGrade.objects.filter(schools=school).distinct()

    selected_session_id = request.GET.get("session")
    selected_term_id    = request.GET.get("term")
    selected_class_id   = request.GET.get("class")

    selected_session = Session.objects.filter(id=selected_session_id, school=school).first() if selected_session_id else None
    selected_term    = Term.objects.filter(id=selected_term_id, school=school).first() if selected_term_id else None
    selected_class   = CourseGrade.objects.filter(id=selected_class_id, schools=school).first() if selected_class_id else None

    records = []

    if selected_session and selected_term and selected_class:
        # ── 1. Bulk create missing behavior records in one query ──
        students = list(selected_class.students.all())
        existing = set(
            StudentBehaviorRecord.objects.filter(
                student__in=students,
                school=school,
                session=selected_session,
                term=selected_term,
            ).values_list('student_id', flat=True)
        )

        StudentBehaviorRecord.objects.bulk_create([
            StudentBehaviorRecord(
                student=student,
                school=school,
                session=selected_session,
                term=selected_term,
                form_teacher=selected_class.form_teacher,
            )
            for student in students
            if student.id not in existing
        ], ignore_conflicts=True)

        # ── 2. Fetch all records in one query ─────────────────────
        records = list(
            StudentBehaviorRecord.objects.filter(
                student__course_grades=selected_class,
                session=selected_session,
                term=selected_term,
            ).select_related('student')
        )

        # ── 3. Fetch ALL results for all students in ONE query ────
        student_ids = [r.student_id for r in records]

        all_results = Result_Portal.objects.filter(
            student_id__in=student_ids,
            session=selected_session,
            term=selected_term,
            result_class=selected_class.name,
        ).select_related('subject').order_by('subject__title')

        # ── 4. Group results by student_id in Python ──────────────
        from collections import defaultdict
        results_by_student = defaultdict(list)
        for result in all_results:
            results_by_student[result.student_id].append(result)

        # ── 5. Attach computed data to each record ────────────────
        for record in records:
            student_results = results_by_student[record.student_id]

            total_score   = sum(
                float(r.ca_score or 0) + float(r.midterm_score or 0) + float(r.exam_score or 0)
                for r in student_results
            )
            num_subjects  = len(student_results)
            average_score = round(total_score / num_subjects, 2) if num_subjects else 0
            final_grade   = student_results[0].grade_letter if student_results else ''
            remarks       = {r.subject.title: r.remark for r in student_results}

            record.results         = student_results
            record.total_score     = total_score
            record.average_score   = average_score
            record.final_grade     = final_grade
            record.subject_remarks = remarks

        # ── 6. Handle POST ────────────────────────────────────────
        if request.method == "POST":
            to_update = []
            for record in records:
                new_comment = request.POST.get(f"comment_{record.student_id}")
                if new_comment is not None:
                    record.principal_comment = new_comment
                    to_update.append(record)

            if to_update:
                StudentBehaviorRecord.objects.bulk_update(to_update, ['principal_comment'])

            messages.success(request, "Principal comments saved successfully.")
            return redirect(
                request.path +
                f"?session={selected_session.id}&term={selected_term.id}&class={selected_class.id}"
            )

    context = {
        "classes":          classes,
        "sessions":         sessions,
        "terms":            terms,
        "selected_session": selected_session,
        "selected_term":    selected_term,
        "selected_class":   selected_class,
        "records":          records,
    }

    return render(request, "portal/principal_dashboard.html", context)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def generate_principal_comment(request, student_id):
    session_id = request.GET.get("session")
    term_id    = request.GET.get("term")
    class_id   = request.GET.get("class")

    if not (session_id and term_id and class_id):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        student = NewUser.objects.get(id=student_id)
    except NewUser.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    results = Result_Portal.objects.filter(
        student=student,
        session_id=session_id,
        term_id=term_id
    ).select_related("subject").order_by('-total_score')

    if not results.exists():
        return JsonResponse({"comment": "No results found for this student."})

    # ---- Build subject summary ----
    strong_subjects = []
    weak_subjects   = []
    result_lines    = []
    total_scores    = []

    for r in results:
        try:
            score = float(r.total_score)
        except (TypeError, ValueError):
            score = 0
        total_scores.append(score)
        result_lines.append(f"  - {r.subject.title}: {r.total_score}/100 (Grade: {r.grade_letter})")
        if score >= 70:
            strong_subjects.append(r.subject.title)
        elif score < 50:
            weak_subjects.append(r.subject.title)

    result_text  = "\n".join(result_lines)
    avg          = round(sum(total_scores) / len(total_scores), 1) if total_scores else 0
    strong_text  = ", ".join(strong_subjects[:3]) if strong_subjects else "none"
    weak_text    = ", ".join(weak_subjects[:2])   if weak_subjects   else "none"
    first_name   = student.first_name

    if avg >= 75:
        overall = "outstanding"
    elif avg >= 60:
        overall = "commendable"
    elif avg >= 50:
        overall = "satisfactory"
    else:
        overall = "below expectation"

    prompt = f"""
Write a principal report card comment exactly like these examples — very short, concise, no full sentences:

EXAMPLE 1:
"Outstanding performance; excellent in Mathematics and Civic Education; improve Chemistry and Physics. Good conduct. Keep it up."

EXAMPLE 2:
"Satisfactory result; strong in English and Home Economics; needs improvement in Physics and Biology. Fair character traits. More effort needed next term."

EXAMPLE 3:
"Commendable academic performance; notable in Further Mathematics and Economics; work harder in French. Excellent behaviour. Maintain the standard."

Now write one for this student in the exact same style.

Student: {student.first_name} {student.last_name}
Overall: {avg}/100 ({overall})
Strong: {strong_text}
Weak: {weak_text}
Results:
{result_text}

Rules:
- Max 2 short sentences or phrase-style clauses separated by semicolons
- Mention 1-2 strong subjects and 1 weak subject by name
- Add one word on character/behaviour (e.g. "Good conduct", "Excellent traits", "Fair behaviour")
- End with one short closing phrase (e.g. "Keep excelling.", "More effort needed.", "Maintain this standard.")
- NO full paragraphs, NO "I am pleased", NO motivational language
- Be brutally concise like a principal stamping a report card
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Nigerian secondary school principal with 20 years of experience "
                        "writing end-of-term report card comments. Your comments are direct, professional, "
                        "specific and grounded. You never use motivational speaker language. "
                        "You write the way a real principal writes — firm, honest, and encouraging."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=80,
            temperature=0.5,
        )
        ai_comment = resp.choices[0].message.content.strip().strip('"').replace('"', '')
    except Exception as e:
        return JsonResponse({"comment": f"Error generating comment: {str(e)}"})

    return JsonResponse({"comment": ai_comment})


# ── Generate ALL principal comments sequentially ──────────────────────────
@csrf_exempt
def generate_all_principal_comments(request):
    session_id = request.GET.get("session")
    term_id    = request.GET.get("term")
    class_id   = request.GET.get("class")

    if not (session_id and term_id and class_id):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        class_obj = CourseGrade.objects.get(id=class_id)
    except CourseGrade.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    students = class_obj.students.all().order_by('id')
    comments = {}

    for student in students:
        results = Result_Portal.objects.filter(
            student=student,
            session_id=session_id,
            term_id=term_id
        ).select_related("subject").order_by('-total_score')

        if not results.exists():
            comments[str(student.id)] = "No results found for this student."
            continue

        # Build subject summary
        strong_subjects = []
        weak_subjects   = []
        result_lines    = []
        total_scores    = []

        for r in results:
            try:
                score = float(r.total_score)
            except (TypeError, ValueError):
                score = 0
            total_scores.append(score)
            result_lines.append(f"  - {r.subject.title}: {r.total_score}/100 (Grade: {r.grade_letter})")
            if score >= 70:
                strong_subjects.append(r.subject.title)
            elif score < 50:
                weak_subjects.append(r.subject.title)

        result_text = "\n".join(result_lines)
        avg         = round(sum(total_scores) / len(total_scores), 1) if total_scores else 0
        strong_text = ", ".join(strong_subjects[:3]) if strong_subjects else "none"
        weak_text   = ", ".join(weak_subjects[:2])   if weak_subjects   else "none"
        first_name  = student.first_name

        if avg >= 75:
            overall = "outstanding"
        elif avg >= 60:
            overall = "commendable"
        elif avg >= 50:
            overall = "satisfactory"
        else:
            overall = "below expectation"

        prompt = f"""
Write a principal report card comment exactly like these examples — very short, concise, no full sentences, no flowery language:

EXAMPLE 1:
"Outstanding performance; excellent in Mathematics and Civic Education; improve Chemistry and Physics. Good conduct. Keep it up."

EXAMPLE 2:
"Satisfactory result; strong in English and Home Economics; needs improvement in Physics and Biology. Fair character traits. More effort needed next term."

EXAMPLE 3:
"Commendable academic performance; notable in Further Mathematics and Economics; work harder in French. Excellent behaviour. Maintain the standard."

Now write one for this student in the exact same style.

Student: {student.first_name} {student.last_name}
Overall: {avg}/100 ({overall})
Strong: {strong_text}
Weak: {weak_text}
Results: {result_text}

Rules:
- Max 2 short sentences or phrase-style clauses separated by semicolons
- Mention 1-2 strong subjects and 1 weak subject by name
- Add one word on character/behaviour (e.g. "Good conduct", "Excellent traits", "Fair behaviour")
- End with one short closing phrase (e.g. "Keep excelling.", "More effort needed.", "Maintain this standard.")
- NO full paragraphs, NO "I am pleased", NO motivational language
- Be brutally concise like a principal stamping a report card
"""

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Nigerian secondary school principal writing end-of-term "
                            "report card comments. Be direct, professional, specific and grounded. "
                            "Never use motivational speaker language."
                        )
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=80,
                temperature=0.5,
            )
            comments[str(student.id)] = resp.choices[0].message.content.strip().strip('"').replace('"', '')
        except Exception as e:
            comments[str(student.id)] = f"Error: {str(e)}"

    return JsonResponse({"status": "success", "comments": comments})


# ── Generate ALL principal comments sequentially ──────────────────────────
@csrf_exempt
def generate_principal_comment(request, student_id):
    session_id = request.GET.get("session")
    term_id    = request.GET.get("term")
    class_id   = request.GET.get("class")

    if not (session_id and term_id and class_id):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        student = NewUser.objects.get(id=student_id)
    except NewUser.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    results = Result_Portal.objects.filter(
        student=student,
        session_id=session_id,
        term_id=term_id
    ).select_related("subject").order_by('-total_score')

    if not results.exists():
        return JsonResponse({"comment": "No results found for this student."})

    # ---- Build subject summary ----
    strong_subjects = []
    weak_subjects   = []
    result_lines    = []
    total_scores    = []

    for r in results:
        try:
            score = float(r.total_score)
        except (TypeError, ValueError):
            score = 0
        total_scores.append(score)
        result_lines.append(f"  - {r.subject.title}: {r.total_score}/100 (Grade: {r.grade_letter})")
        if score >= 70:
            strong_subjects.append(r.subject.title)
        elif score < 50:
            weak_subjects.append(r.subject.title)

    result_text  = "\n".join(result_lines)
    avg          = round(sum(total_scores) / len(total_scores), 1) if total_scores else 0
    strong_text  = ", ".join(strong_subjects[:3]) if strong_subjects else "none"
    weak_text    = ", ".join(weak_subjects[:2])   if weak_subjects   else "none"
    first_name   = student.first_name

    if avg >= 75:
        overall = "outstanding"
    elif avg >= 60:
        overall = "commendable"
    elif avg >= 50:
        overall = "satisfactory"
    else:
        overall = "below expectation"

    prompt = f"""
Write a principal report card comment exactly like these examples — very short, concise, no full sentences:

EXAMPLE 1:
"Outstanding performance; excellent in Mathematics and Civic Education; improve Chemistry and Physics. Good conduct. Keep it up."

EXAMPLE 2:
"Satisfactory result; strong in English and Home Economics; needs improvement in Physics and Biology. Fair character traits. More effort needed next term."

EXAMPLE 3:
"Commendable academic performance; notable in Further Mathematics and Economics; work harder in French. Excellent behaviour. Maintain the standard."

Now write one for this student in the exact same style.

Student: {student.first_name} {student.last_name}
Overall: {avg}/100 ({overall})
Strong: {strong_text}
Weak: {weak_text}
Results:
{result_text}

Rules:
- Max 2 short sentences or phrase-style clauses separated by semicolons
- Mention 1-2 strong subjects and 1 weak subject by name
- Add one word on character/behaviour (e.g. "Good conduct", "Excellent traits", "Fair behaviour")
- End with one short closing phrase (e.g. "Keep excelling.", "More effort needed.", "Maintain this standard.")
- NO full paragraphs, NO "I am pleased", NO motivational language
- Be brutally concise like a principal stamping a report card
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Nigerian secondary school principal with 20 years of experience "
                        "writing end-of-term report card comments. Your comments are direct, professional, "
                        "specific and grounded. You never use motivational speaker language. "
                        "You write the way a real principal writes — firm, honest, and encouraging."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=80,
            temperature=0.5,
        )
        ai_comment = resp.choices[0].message.content.strip()
    except Exception as e:
        return JsonResponse({"comment": f"Error generating comment: {str(e)}"})

    return JsonResponse({"comment": ai_comment})


# ── Generate ALL principal comments sequentially ──────────────────────────
@csrf_exempt
def generate_all_principal_comments(request):
    session_id = request.GET.get("session")
    term_id    = request.GET.get("term")
    class_id   = request.GET.get("class")

    if not (session_id and term_id and class_id):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        class_obj = CourseGrade.objects.get(id=class_id)
    except CourseGrade.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    students = class_obj.students.all().order_by('id')
    comments = {}

    for student in students:
        results = Result_Portal.objects.filter(
            student=student,
            session_id=session_id,
            term_id=term_id
        ).select_related("subject").order_by('-total_score')

        if not results.exists():
            comments[str(student.id)] = "No results found for this student."
            continue

        # Build subject summary
        strong_subjects = []
        weak_subjects   = []
        result_lines    = []
        total_scores    = []

        for r in results:
            try:
                score = float(r.total_score)
            except (TypeError, ValueError):
                score = 0
            total_scores.append(score)
            result_lines.append(f"  - {r.subject.title}: {r.total_score}/100 (Grade: {r.grade_letter})")
            if score >= 70:
                strong_subjects.append(r.subject.title)
            elif score < 50:
                weak_subjects.append(r.subject.title)

        result_text = "\n".join(result_lines)
        avg         = round(sum(total_scores) / len(total_scores), 1) if total_scores else 0
        strong_text = ", ".join(strong_subjects[:3]) if strong_subjects else "none"
        weak_text   = ", ".join(weak_subjects[:2])   if weak_subjects   else "none"
        first_name  = student.first_name

        if avg >= 75:
            overall = "outstanding"
        elif avg >= 60:
            overall = "commendable"
        elif avg >= 50:
            overall = "satisfactory"
        else:
            overall = "below expectation"

        prompt = f"""
Write a principal report card comment exactly like these examples — very short, concise, no full sentences, no flowery language:

EXAMPLE 1:
"Outstanding performance; excellent in Mathematics and Civic Education; improve Chemistry and Physics. Good conduct. Keep it up."

EXAMPLE 2:
"Satisfactory result; strong in English and Home Economics; needs improvement in Physics and Biology. Fair character traits. More effort needed next term."

EXAMPLE 3:
"Commendable academic performance; notable in Further Mathematics and Economics; work harder in French. Excellent behaviour. Maintain the standard."

Now write one for this student in the exact same style.

Student: {student.first_name} {student.last_name}
Overall: {avg}/100 ({overall})
Strong: {strong_text}
Weak: {weak_text}
Results: {result_text}

Rules:
- Max 2 short sentences or phrase-style clauses separated by semicolons
- Mention 1-2 strong subjects and 1 weak subject by name
- Add one word on character/behaviour (e.g. "Good conduct", "Excellent traits", "Fair behaviour")
- End with one short closing phrase (e.g. "Keep excelling.", "More effort needed.", "Maintain this standard.")
- NO full paragraphs, NO "I am pleased", NO motivational language
- Be brutally concise like a principal stamping a report card
"""

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Nigerian secondary school principal writing end-of-term "
                            "report card comments. Be direct, professional, specific and grounded. "
                            "Never use motivational speaker language."
                        )
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=80,
                temperature=0.5,
            )
            comments[str(student.id)] = resp.choices[0].message.content.strip()
        except Exception as e:
            comments[str(student.id)] = f"Error: {str(e)}"

    return JsonResponse({"status": "success", "comments": comments})

    


# from celery.result import AsyncResult
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .tasks import generate_comments_task


# @csrf_exempt
# def generate_all_principal_comments(request):
#     session_id = request.GET.get("session")
#     term_id = request.GET.get("term")
#     class_id = request.GET.get("class")

#     if not (session_id and term_id and class_id):
#         return JsonResponse({"error": "Missing parameters"}, status=400)

#     # Fire task in background
#     task = generate_comments_task.delay(session_id, term_id, class_id)
#     return JsonResponse({"task_id": task.id}, status=202)


# def get_comment_task_status(request, task_id):
#     """Poll this endpoint to check progress and retrieve comments."""
#     result = AsyncResult(task_id)

#     if result.state == "PENDING":
#         return JsonResponse({"state": "PENDING", "progress": 0})

#     elif result.state == "PROGRESS":
#         meta = result.info
#         return JsonResponse({
#             "state": "PROGRESS",
#             "current": meta.get("current", 0),
#             "total": meta.get("total", 1),
#             "comments": meta.get("comments", {}),
#         })

#     elif result.state == "SUCCESS":
#         return JsonResponse({
#             "state": "SUCCESS",
#             "comments": result.result.get("comments", {}),
#         })

#     else:  # FAILURE
#         return JsonResponse({"state": "FAILURE", "error": str(result.info)}, status=500)


# from celery.result import AsyncResult
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .tasks import generate_comments_task

# @csrf_exempt
# def generate_all_principal_comments(request):
#     session_id = request.GET.get("session")
#     term_id = request.GET.get("term")
#     class_id = request.GET.get("class")

#     if not (session_id and term_id and class_id):
#         return JsonResponse({"error": "Missing parameters"}, status=400)

#     # Fire task in background
#     task = generate_comments_task.delay(session_id, term_id, class_id)
#     return JsonResponse({"task_id": task.id}, status=202)


# def get_comment_task_status(request, task_id):
#     """Poll this endpoint to check progress and retrieve comments."""
#     result = AsyncResult(task_id)

#     if result.state == "PENDING":
#         return JsonResponse({"state": "PENDING", "progress": 0})

#     elif result.state == "PROGRESS":
#         meta = result.info
#         return JsonResponse({
#             "state": "PROGRESS",
#             "current": meta.get("current", 0),
#             "total": meta.get("total", 1),
#             "comments": meta.get("comments", {}),
#         })

#     elif result.state == "SUCCESS":
#         return JsonResponse({
#             "state": "SUCCESS",
#             "comments": result.result.get("comments", {}),
#         })

#     else:  # FAILURE
#         return JsonResponse({"state": "FAILURE", "error": str(result.info)}, status=500)
    

#real view
# @csrf_exempt
# def generate_all_principal_comments(request):
#     """
#     Generate AI principal comments using OpenAI GPT for all students
#     in a given session, term, and class.
#     """

#     session_id = request.GET.get("session")
#     term_id = request.GET.get("term")
#     class_id = request.GET.get("class")

#     if not (session_id and term_id and class_id):
#         return JsonResponse({"error": "Missing parameters: session, term, or class"}, status=400)

#     # Fetch students in the class
#     students = NewUser.objects.filter(course_grades__id=class_id).distinct()

#     # Fetch all results for the students in this session and term
#     results = Result_Portal.objects.filter(
#         session_id=session_id,
#         term_id=term_id,
#         student__in=students
#     ).select_related("subject", "student", "schools")

#     output_comments = {}

#     for student in students:
#         student_results = results.filter(student=student)

#         strong_subjects = []
#         weak_subjects = []
#         result_lines = []

#         for r in student_results:
#             # Determine strong/weak subjects
#             if r.total_score >= 70:
#                 strong_subjects.append(r.subject.title)
#             elif r.total_score < 45:
#                 weak_subjects.append(r.subject.title)

#             result_lines.append(
#                 f"{r.subject.title}: Total={r.total_score}, Grade={r.grade_letter or '-'}, Remark={r.remark or '-'}"
#             )

#         result_text = "\n".join(result_lines) if result_lines else "No results yet."

#         prompt = f"""
# You are a school principal. Write a brief, professional report card comment for this student.

# Student: {student.first_name} {student.last_name}
# Results:
# {result_text}

# Strong subjects: {', '.join(strong_subjects) if strong_subjects else 'None'}
# Weak subjects: {', '.join(weak_subjects) if weak_subjects else 'None'}

# Rules:
# - 1–2 sentences only
# - No salutations, sign-offs, or names
# - Mention strengths, weaknesses, and encouragement
# - Formal and concise tone
# """

#         try:
#             resp = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You generate curriculum-aligned principal comments with high precision."},
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=1800,
#                 temperature=0.4,
#             )

#             # Correct access to the message content
#             ai_comment = resp.choices[0].message.content.strip()

#         except Exception as e:
#             ai_comment = f"Error generating comment: {str(e)}"

#         output_comments[student.id] = ai_comment

#     return JsonResponse({"comments": output_comments}, status=200)



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

