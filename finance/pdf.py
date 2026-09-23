from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)


BRAND = colors.HexColor('#4676EF')
LIGHT = colors.HexColor('#f0f0f0')
RED   = colors.HexColor('#c0392b')
GREEN = colors.HexColor('#27ae60')


def build_family_statement_pdf(
    *,
    school_name,
    family_name,
    session_name,
    term_name,
    students_data,   # list of dicts: {student_name, student_class, admission_no, records}
):
    """
    One PDF for a whole family:
      - Cover page: summary of every child + family total
      - One page per child: their weekly ledger
    """
    from reportlab.platypus import PageBreak
    from datetime import date as _date

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm,  bottomMargin=1.5 * cm,
        title=f"Family Statement - {family_name}",
    )

    styles = getSampleStyleSheet()
    h_title = ParagraphStyle('f_title', parent=styles['Title'],
                             textColor=BRAND, fontSize=18, spaceAfter=6)
    h_sub   = ParagraphStyle('f_sub',   parent=styles['Normal'],
                             fontSize=11, textColor=colors.HexColor('#555'))
    h_meta  = ParagraphStyle('f_meta',  parent=styles['Normal'],
                             fontSize=10, leading=14)
    h_head  = ParagraphStyle('f_head',  parent=styles['Heading2'],
                             textColor=BRAND, fontSize=13, spaceAfter=6)

    story = []

    # ============================================================
    # COVER PAGE
    # ============================================================
    story.append(Paragraph(school_name or "School", h_title))
    story.append(Paragraph("Family Account Statement", h_sub))
    story.append(Spacer(1, 14))

    meta = [
        [Paragraph("<b>Family:</b>",  h_meta), Paragraph(family_name or "—",  h_meta)],
        [Paragraph("<b>Session:</b>", h_meta), Paragraph(session_name or "—", h_meta)],
        [Paragraph("<b>Term:</b>",    h_meta), Paragraph(term_name or "—",    h_meta)],
    ]
    meta_tbl = Table(meta, colWidths=[3 * cm, 8 * cm])
    meta_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Children Summary", h_head))

    sum_data = [["Student", "Class", "Adm. No",
                 "Opening", "Deposits", "Expenses", "Closing"]]
    grand_open = grand_dep = grand_exp = grand_close = 0.0

    for student_entry in students_data:
        recs = student_entry.get('records') or []
        if not recs:
            continue

        opening  = float(recs[0].balance_brought_forward or 0)
        closing  = float(recs[-1].current_balance or 0)
        deposits = sum(float(x.initial_total_deposit or 0) for x in recs)
        expenses = sum(float(x.total_expense or 0) for x in recs)

        grand_open  += opening
        grand_dep   += deposits
        grand_exp   += expenses
        grand_close += closing

        sum_data.append([
            student_entry.get('student_name', '—'),
            student_entry.get('student_class', '—'),
            student_entry.get('admission_no', '—'),
            f"{opening:,.1f}",
            f"{deposits:,.1f}",
            f"{expenses:,.1f}",
            f"{closing:,.1f}",
        ])

    sum_data.append([
        "FAMILY TOTAL", "", "",
        f"{grand_open:,.1f}",
        f"{grand_dep:,.1f}",
        f"{grand_exp:,.1f}",
        f"{grand_close:,.1f}",
    ])

    sum_tbl = Table(
        sum_data,
        colWidths=[4.5 * cm, 3 * cm, 2 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm],
    )
    sum_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 9),
        ('FONTSIZE',   (0, 1), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.4, colors.grey),
        ('ALIGN',      (3, 1), (-1, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dfe6f5')),
        ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        f"Generated on {_date.today().strftime('%d %b %Y')}",
        h_sub,
    ))

    # ============================================================
    # ONE PAGE PER CHILD
    # ============================================================
    total_children = len(students_data)

    for idx, student_entry in enumerate(students_data, start=1):
        story.append(PageBreak())

        student_name = student_entry.get('student_name', '—')
        student_class = student_entry.get('student_class', '—')
        admission_no  = student_entry.get('admission_no', '—')
        recs          = student_entry.get('records') or []

        story.append(Paragraph(school_name or "School", h_title))
        story.append(Paragraph(
            f"Student Statement — {student_name} "
            f"<font color='#888' size='10'>({idx} of {total_children})</font>",
            h_sub,
        ))
        story.append(Spacer(1, 10))

        # ---- Student meta ----
        meta = [
            [Paragraph("<b>Student:</b>", h_meta),  Paragraph(student_name, h_meta),
             Paragraph("<b>Class:</b>",   h_meta),  Paragraph(student_class, h_meta)],
            [Paragraph("<b>Adm. No:</b>", h_meta),  Paragraph(admission_no, h_meta),
             Paragraph("<b>Session:</b>", h_meta),  Paragraph(session_name or '—', h_meta)],
            [Paragraph("<b>Term:</b>",    h_meta),  Paragraph(term_name or '—', h_meta),
             Paragraph("", h_meta),                 Paragraph("", h_meta)],
        ]
        meta_tbl = Table(meta, colWidths=[2.5 * cm, 6 * cm, 2.5 * cm, 6 * cm])
        meta_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_tbl)
        story.append(Spacer(1, 12))

        # ---- Ledger table ----
        header = ["Week", "BBF", "Deposit", "Cum. Dep.",
                  "Shop", "Caps", "Haircut", "Others",
                  "Total Exp", "Balance", "Status"]
        data = [header]

        total_dep = total_exp = 0.0
        for rec in recs:
            total_dep += float(rec.initial_total_deposit or 0)
            total_exp += float(rec.total_expense or 0)
            week = rec.week_start.strftime("%d %b %y") if rec.week_start else "—"
            data.append([
                week,
                f"{float(rec.balance_brought_forward or 0):,.1f}",
                f"{float(rec.initial_total_deposit or 0):,.1f}",
                f"{float(rec.total_deposit or 0):,.1f}",
                f"{float(rec.school_shop or 0):,.1f}",
                f"{float(rec.caps or 0):,.1f}",
                f"{float(rec.haircut or 0):,.1f}",
                f"{float(rec.others or 0):,.1f}",
                f"{float(rec.total_expense or 0):,.1f}",
                f"{float(rec.current_balance or 0):,.1f}",
                "Exhausted" if rec.status == 'exhausted' else "Available",
            ])

        if recs:
            closing = float(recs[-1].current_balance or 0)
        else:
            closing = 0.0

        data.append(["TOTAL", "", f"{total_dep:,.1f}", "", "", "", "", "",
                     f"{total_exp:,.1f}", f"{closing:,.1f}", ""])

        col_widths = [1.7 * cm, 1.5 * cm, 1.6 * cm, 1.7 * cm,
                      1.4 * cm, 1.3 * cm, 1.5 * cm, 1.4 * cm,
                      1.6 * cm, 1.7 * cm, 2.1 * cm]
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, 0), 8),
            ('FONTSIZE',   (0, 1), (-1, -1), 8),
            ('GRID',       (0, 0), (-1, -1), 0.35, colors.grey),
            ('ALIGN',      (1, 1), (-2, -1), 'RIGHT'),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            *[('BACKGROUND', (0, i), (-1, i), LIGHT)
              for i in range(2, len(data), 2)],
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dfe6f5')),
            ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(tbl)

    doc.build(story)
    buf.seek(0)
    return buf


def build_student_statement_pdf(
    *,
    school_name,
    student_name,
    student_class,
    admission_no,
    session_name,
    term_name,
    records,
):
    """
    records: list of FinanceRecord objects, already ordered by week.
    Returns a BytesIO positioned at 0.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Statement - {student_name}",
    )

    styles = getSampleStyleSheet()
    h_title  = ParagraphStyle('title',  parent=styles['Title'],
                              textColor=BRAND, fontSize=16, spaceAfter=4)
    h_sub    = ParagraphStyle('sub',    parent=styles['Normal'],
                              fontSize=10, textColor=colors.HexColor('#555'))
    h_meta   = ParagraphStyle('meta',   parent=styles['Normal'],
                              fontSize=10, leading=14)
    cell_par = ParagraphStyle('cell',   parent=styles['Normal'],
                              fontSize=8, leading=10)

    story = []

    # ---------- Header ----------
    story.append(Paragraph(school_name or "School", h_title))
    story.append(Paragraph("Student Account Statement", h_sub))
    story.append(Spacer(1, 10))

    # ---------- Student meta ----------
    meta_data = [
        [Paragraph("<b>Student:</b>", h_meta), Paragraph(student_name or "—", h_meta),
         Paragraph("<b>Class:</b>", h_meta),   Paragraph(student_class or "—", h_meta)],
        [Paragraph("<b>Admission No:</b>", h_meta), Paragraph(admission_no or "—", h_meta),
         Paragraph("<b>Session:</b>", h_meta), Paragraph(session_name or "—", h_meta)],
        [Paragraph("<b>Term:</b>", h_meta), Paragraph(term_name or "—", h_meta),
         Paragraph("", h_meta), Paragraph("", h_meta)],
    ]
    meta_tbl = Table(meta_data, colWidths=[3.2*cm, 5.5*cm, 3.2*cm, 5.5*cm])
    meta_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 12))

    # ---------- Ledger table ----------
    header = [
        "Week", "BBF", "Deposit", "Cum. Dep.",
        "Shop", "Caps", "Haircut", "Others",
        "Total Exp", "Balance", "Status",
    ]
    data = [header]

    total_dep = 0.0
    total_exp = 0.0
    for r in records:
        total_dep += float(r.initial_total_deposit or 0)
        total_exp += float(r.total_expense or 0)
        week = r.week_start.strftime("%d %b %y") if r.week_start else "—"
        data.append([
            week,
            f"{float(r.balance_brought_forward or 0):,.1f}",
            f"{float(r.initial_total_deposit or 0):,.1f}",
            f"{float(r.total_deposit or 0):,.1f}",
            f"{float(r.school_shop or 0):,.1f}",
            f"{float(r.caps or 0):,.1f}",
            f"{float(r.haircut or 0):,.1f}",
            f"{float(r.others or 0):,.1f}",
            f"{float(r.total_expense or 0):,.1f}",
            f"{float(r.current_balance or 0):,.1f}",
            "Exhausted" if r.status == 'exhausted' else "Available",
        ])

    opening = float(records[0].balance_brought_forward or 0) if records else 0.0
    closing = float(records[-1].current_balance or 0)        if records else 0.0

    # Footer totals
    footer = [
        "TOTAL", "", f"{total_dep:,.1f}", "", "", "", "", "",
        f"{total_exp:,.1f}", f"{closing:,.1f}", "",
    ]
    data.append(footer)

    col_widths = [1.7*cm, 1.5*cm, 1.6*cm, 1.7*cm,
                  1.4*cm, 1.3*cm, 1.5*cm, 1.4*cm,
                  1.6*cm, 1.7*cm, 2.1*cm]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        # header
        ('BACKGROUND', (0, 0), (-1, 0), BRAND),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 8),
        ('ALIGN',      (1, 0), (-1, 0), 'CENTER'),
        # body
        ('FONTSIZE',   (0, 1), (-1, -1), 8),
        ('GRID',       (0, 0), (-1, -1), 0.35, colors.grey),
        ('ALIGN',      (1, 1), (-2, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        # zebra
        *[('BACKGROUND', (0, i), (-1, i), LIGHT)
          for i in range(2, len(data), 2)],
        # footer
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dfe6f5')),
        ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 15))

    # ---------- Summary box ----------
    summary = [
        [Paragraph("<b>Opening Balance</b>", h_meta), Paragraph(f"{opening:,.1f}", h_meta)],
        [Paragraph("<b>Total Deposits</b>", h_meta),  Paragraph(f"{total_dep:,.1f}", h_meta)],
        [Paragraph("<b>Total Expenses</b>", h_meta),  Paragraph(f"{total_exp:,.1f}", h_meta)],
        [Paragraph("<b>Closing Balance</b>", h_meta), Paragraph(f"{closing:,.1f}", h_meta)],
    ]
    sum_tbl = Table(summary, colWidths=[4*cm, 4*cm], hAlign='RIGHT')
    sum_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 3), colors.HexColor('#f8f9fa')),
        ('BOX',        (0, 0), (-1, -1), 0.4, colors.grey),
        ('INNERGRID',  (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('ALIGN',      (1, 0), (1, -1), 'RIGHT'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
    ]))
    story.append(sum_tbl)

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Generated on {__import__('datetime').date.today().strftime('%d %b %Y')}",
        h_sub,
    ))

    doc.build(story)
    buf.seek(0)
    return buf


def build_deposit_receipt_pdf(
    *,
    school_name,
    student_name,
    student_class,
    admission_no,
    amount,
    balance_before,
    balance_after,
    received_by,
    record_sn,
    week_start=None,
    is_reprint=False,
):
    """
    Small thermal/A5-friendly deposit receipt.
    Page size: 80mm wide (standard thermal roll), auto height.
    """
    from reportlab.lib.units import mm

    # 80mm width, ~150mm tall — fits most thermal printers
    page_width  = 80 * mm
    page_height = 150 * mm

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=(page_width, page_height),
        leftMargin=5 * mm,
        rightMargin=5 * mm,
        topMargin=5 * mm,
        bottomMargin=5 * mm,
        title=f"Receipt #{record_sn}",
    )

    styles = getSampleStyleSheet()
    h_school = ParagraphStyle(
        'r_school', parent=styles['Title'],
        textColor=BRAND, fontSize=13, alignment=1, spaceAfter=2,
    )
    h_sub = ParagraphStyle(
        'r_sub', parent=styles['Normal'],
        fontSize=9, alignment=1, textColor=colors.HexColor('#555'),
    )
    h_label = ParagraphStyle(
        'r_label', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#888'),
    )
    h_value = ParagraphStyle(
        'r_value', parent=styles['Normal'],
        fontSize=10, textColor=colors.black,
    )
    h_big = ParagraphStyle(
        'r_big', parent=styles['Normal'],
        fontSize=14, textColor=BRAND, alignment=1,
    )

    story = []

    # ---------- Header ----------
    story.append(Paragraph(school_name or "School", h_school))
    story.append(Paragraph("DEPOSIT RECEIPT", h_sub))
    story.append(Spacer(1, 6))

    if is_reprint:
        story.append(Paragraph(
            "<font color='#c0392b'><b>** REPRINT **</b></font>",
            h_sub,
        ))
        story.append(Spacer(1, 4))

    # ---------- Info rows ----------
    def row(label, value):
        return [
            Paragraph(label, h_label),
            Paragraph(str(value), h_value),
        ]

    info_data = [
        row("Receipt #",    record_sn),
        row("Date",         (week_start.strftime('%d %b %Y') if week_start else '—')),
        row("Student",      student_name),
        row("Class",        student_class),
    ]
    if admission_no and admission_no != '—':
        info_data.append(row("Adm. No", admission_no))

    info_tbl = Table(info_data, colWidths=[20 * mm, 50 * mm])
    info_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING',    (0, 0), (-1, -1), 1),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 8))

    # ---------- Amount box ----------
    amount_tbl = Table(
        [[Paragraph(f"<b>₦{float(amount or 0):,.1f}</b>", h_big)]],
        colWidths=[70 * mm],
    )
    amount_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f6ff')),
        ('BOX',        (0, 0), (-1, -1), 0.6, BRAND),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(amount_tbl)
    story.append(Spacer(1, 8))

    # ---------- Balance breakdown ----------
    balance_data = [
        [Paragraph("Balance Before", h_label),
         Paragraph(f"₦{float(balance_before or 0):,.1f}", h_value)],
        [Paragraph("This Deposit",  h_label),
         Paragraph(f"₦{float(amount or 0):,.1f}", h_value)],
        [Paragraph("<b>New Balance</b>", h_label),
         Paragraph(f"<b>₦{float(balance_after or 0):,.1f}</b>", h_value)],
    ]
    bal_tbl = Table(balance_data, colWidths=[35 * mm, 35 * mm])
    bal_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.grey),
        ('ALIGN',     (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(bal_tbl)
    story.append(Spacer(1, 10))

    # ---------- Footer ----------
    story.append(Paragraph("Received by:", h_label))
    story.append(Spacer(1, 2))
    story.append(Paragraph(received_by or "—", h_value))
    story.append(Spacer(1, 12))

    story.append(Paragraph("_ _ _ _ _ _ _ _ _ _ _ _ _", h_sub))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Signature", h_sub))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Thank you!", h_sub))

    doc.build(story)
    buf.seek(0)
    return buf



def build_class_statements_pdf(
    *,
    school_name,
    class_name,
    session_name,
    term_name,
    students_data,   # list of dicts: {student_name, student_class, admission_no, records}
):
    """
    One PDF for a whole class:
      - Cover page: summary of every student + class total (roll-call sheet)
      - One page per student: standalone statement that prints cleanly on its own
    """
    from reportlab.platypus import PageBreak
    from datetime import date as _date

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm,  bottomMargin=1.5 * cm,
        title=f"Class Statement - {class_name}",
    )

    styles = getSampleStyleSheet()
    h_title = ParagraphStyle('c_title', parent=styles['Title'],
                             textColor=BRAND, fontSize=18, spaceAfter=6)
    h_sub   = ParagraphStyle('c_sub',   parent=styles['Normal'],
                             fontSize=11, textColor=colors.HexColor('#555'))
    h_meta  = ParagraphStyle('c_meta',  parent=styles['Normal'],
                             fontSize=10, leading=14)
    h_head  = ParagraphStyle('c_head',  parent=styles['Heading2'],
                             textColor=BRAND, fontSize=13, spaceAfter=6)
    h_foot  = ParagraphStyle('c_foot',  parent=styles['Normal'],
                             fontSize=8, textColor=colors.HexColor('#888'),
                             alignment=1)

    story = []

    # ============================================================
    # COVER PAGE — class roll-call summary
    # ============================================================
    story.append(Paragraph(school_name or "School", h_title))
    story.append(Paragraph("Class Account Statements", h_sub))
    story.append(Spacer(1, 14))

    meta = [
        [Paragraph("<b>Class:</b>",    h_meta), Paragraph(class_name or "—",   h_meta)],
        [Paragraph("<b>Session:</b>",  h_meta), Paragraph(session_name or "—", h_meta)],
        [Paragraph("<b>Term:</b>",     h_meta), Paragraph(term_name or "—",    h_meta)],
        [Paragraph("<b>Students:</b>", h_meta), Paragraph(str(len(students_data)), h_meta)],
    ]
    meta_tbl = Table(meta, colWidths=[3 * cm, 8 * cm])
    meta_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Class Summary", h_head))

    sum_data = [["Student", "Class", "Adm. No",
                 "Opening", "Deposits", "Expenses", "Closing"]]
    grand_open = grand_dep = grand_exp = grand_close = 0.0

    for entry in students_data:
        recs = entry.get('records') or []
        if not recs:
            continue

        opening  = float(recs[0].balance_brought_forward or 0)
        closing  = float(recs[-1].current_balance or 0)
        deposits = sum(float(x.initial_total_deposit or 0) for x in recs)
        expenses = sum(float(x.total_expense or 0) for x in recs)

        grand_open  += opening
        grand_dep   += deposits
        grand_exp   += expenses
        grand_close += closing

        sum_data.append([
            entry.get('student_name', '—'),
            entry.get('student_class', '—'),
            entry.get('admission_no', '—'),
            f"{opening:,.1f}",
            f"{deposits:,.1f}",
            f"{expenses:,.1f}",
            f"{closing:,.1f}",
        ])

    sum_data.append([
        "CLASS TOTAL", "", "",
        f"{grand_open:,.1f}",
        f"{grand_dep:,.1f}",
        f"{grand_exp:,.1f}",
        f"{grand_close:,.1f}",
    ])

    sum_tbl = Table(
        sum_data,
        colWidths=[4.5 * cm, 3 * cm, 2 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm],
    )
    sum_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 9),
        ('FONTSIZE',   (0, 1), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.4, colors.grey),
        ('ALIGN',      (3, 1), (-1, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dfe6f5')),
        ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        f"Generated on {_date.today().strftime('%d %b %Y')}",
        h_sub,
    ))

    # ============================================================
    # ONE PAGE PER STUDENT — standalone, printable alone
    # ============================================================
    for entry in students_data:
        story.append(PageBreak())

        student_name  = entry.get('student_name', '—')
        student_class = entry.get('student_class', '—')
        admission_no  = entry.get('admission_no', '—')
        recs          = entry.get('records') or []

        # ---- Page header (standalone, no "X of N") ----
        story.append(Paragraph(school_name or "School", h_title))
        story.append(Paragraph("Student Account Statement", h_sub))
        story.append(Spacer(1, 10))

        # ---- Student meta ----
        meta = [
            [Paragraph("<b>Student:</b>", h_meta),  Paragraph(student_name, h_meta),
             Paragraph("<b>Class:</b>",   h_meta),  Paragraph(student_class, h_meta)],
            [Paragraph("<b>Adm. No:</b>", h_meta),  Paragraph(admission_no, h_meta),
             Paragraph("<b>Session:</b>", h_meta),  Paragraph(session_name or '—', h_meta)],
            [Paragraph("<b>Term:</b>",    h_meta),  Paragraph(term_name or '—', h_meta),
             Paragraph("", h_meta),                 Paragraph("", h_meta)],
        ]
        meta_tbl = Table(meta, colWidths=[2.5 * cm, 6 * cm, 2.5 * cm, 6 * cm])
        meta_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_tbl)
        story.append(Spacer(1, 12))

        # ---- Ledger table ----
        header = ["Week", "BBF", "Deposit", "Cum. Dep.",
                  "Shop", "Caps", "Haircut", "Others",
                  "Total Exp", "Balance", "Status"]
        data = [header]

        total_dep = total_exp = 0.0
        for rec in recs:
            total_dep += float(rec.initial_total_deposit or 0)
            total_exp += float(rec.total_expense or 0)
            week = rec.week_start.strftime("%d %b %y") if rec.week_start else "—"
            data.append([
                week,
                f"{float(rec.balance_brought_forward or 0):,.1f}",
                f"{float(rec.initial_total_deposit or 0):,.1f}",
                f"{float(rec.total_deposit or 0):,.1f}",
                f"{float(rec.school_shop or 0):,.1f}",
                f"{float(rec.caps or 0):,.1f}",
                f"{float(rec.haircut or 0):,.1f}",
                f"{float(rec.others or 0):,.1f}",
                f"{float(rec.total_expense or 0):,.1f}",
                f"{float(rec.current_balance or 0):,.1f}",
                "Exhausted" if rec.status == 'exhausted' else "Available",
            ])

        closing = float(recs[-1].current_balance or 0) if recs else 0.0
        data.append(["TOTAL", "", f"{total_dep:,.1f}", "", "", "", "", "",
                     f"{total_exp:,.1f}", f"{closing:,.1f}", ""])

        col_widths = [1.7 * cm, 1.5 * cm, 1.6 * cm, 1.7 * cm,
                      1.4 * cm, 1.3 * cm, 1.5 * cm, 1.4 * cm,
                      1.6 * cm, 1.7 * cm, 2.1 * cm]
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, 0), 8),
            ('FONTSIZE',   (0, 1), (-1, -1), 8),
            ('GRID',       (0, 0), (-1, -1), 0.35, colors.grey),
            ('ALIGN',      (1, 1), (-2, -1), 'RIGHT'),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            *[('BACKGROUND', (0, i), (-1, i), LIGHT)
              for i in range(2, len(data), 2)],
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dfe6f5')),
            ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 10))

        # ---- Summary box at bottom of each page ----
        opening_line = (
            f"<b>Opening:</b> ₦{float(recs[0].balance_brought_forward or 0):,.1f}"
            if recs else "<b>Opening:</b> ₦0"
        )
        summary_data = [[
            Paragraph(opening_line, h_meta),
            Paragraph(f"<b>Total Deposits:</b> ₦{total_dep:,.1f}", h_meta),
            Paragraph(f"<b>Total Expenses:</b> ₦{total_exp:,.1f}", h_meta),
            Paragraph(f"<b>Closing Balance:</b> ₦{closing:,.1f}", h_meta),
        ]]
        summary_tbl = Table(summary_data,
                            colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
        summary_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('BOX',        (0, 0), (-1, -1), 0.4, colors.grey),
            ('INNERGRID',  (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_tbl)

        # ---- Small standalone footer ----
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"{school_name or 'School'} · {class_name} · "
            f"{session_name} · {term_name} · "
            f"Printed on {_date.today().strftime('%d %b %Y')}",
            h_foot,
        ))

    doc.build(story)
    buf.seek(0)
    return buf