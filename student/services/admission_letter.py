import re
import io, os, tempfile
from datetime import date, timedelta

import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                HRFlowable, Table, TableStyle)

import io, os, tempfile
from datetime import date, timedelta

import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                HRFlowable, Table, TableStyle)

from .admission_letter_config import (
    DEFAULT_INTRO_TEMPLATE, DEFAULT_DEPOSIT_TEMPLATE, DEFAULT_NOTES_TEMPLATE,
    DEFAULT_CLOSING_LINE, DEFAULT_SIGNATURE_TITLE,
)
from .admission_letter_config import (
    DEPOSIT_AMOUNT_DISPLAY, DEPOSIT_AMOUNT_WORDS,
    BANK_NAME, BANK_BRANCH_HINT, BANK_ACCOUNT, BANK_ACCOUNT_NAME,
    PAYMENT_WINDOW_DAYS, ACCEPTANCE_WINDOW_DAYS,
    ACCEPTANCE_EMAIL_1, ACCEPTANCE_EMAIL_2,
    CLASS_LABELS, SESSION_NAME,
    LETTERHEAD_SCHOOL_LINE, DEFAULT_PRINCIPAL_NAME,
)


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        s = 'th'
    else:
        s = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{s}"


def _fmt_date(d: date) -> str:
    return f"{_ordinal(d.day)} {d.strftime('%B, %Y')}"


class _SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def _fill(text, **vars):
    """Safely fill {placeholders} in user-edited text. Unknown keys are left as-is."""
    if not text:
        return text
    try:
        return text.format_map(_SafeDict(**vars))
    except Exception:
        return text
    
def _cloudinary_to_tempfile(field):
    if not field:
        return None, lambda: None
    try:
        url = field.url
    except Exception:
        return None, lambda: None
    if 'res.cloudinary.com' in url and '/upload/' in url and '/f_' not in url:
        url = url.replace('/upload/', '/upload/f_png/')
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200 or not r.content:
            return None, lambda: None
        from PIL import Image as PILImage
        from io import BytesIO
        img = PILImage.open(BytesIO(r.content))
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(tmp.name, format='PNG')
        tmp.close()
        return tmp.name, lambda: (os.path.exists(tmp.name) and os.unlink(tmp.name))
    except Exception:
        return None, lambda: None


def _build_letterhead(story, school):
    logo_path, logo_clean = _cloudinary_to_tempfile(getattr(school, 'logo', None))

    school_title = (getattr(school, 'name', None)
                    or getattr(school, 'school_name', None)
                    or LETTERHEAD_SCHOOL_LINE)

    name_style = ParagraphStyle('SchoolName', fontName='Times-Bold', fontSize=16,
                                leading=18, alignment=TA_LEFT,
                                textColor=colors.HexColor('#1a6a3a'),
                                spaceAfter=1)
    motto_style = ParagraphStyle('Motto', fontName='Times-Italic', fontSize=10,
                                 leading=12, alignment=TA_LEFT,
                                 textColor=colors.HexColor('#555555'),
                                 spaceAfter=1)
    addr_style = ParagraphStyle('SchoolAddr', fontName='Times-Roman', fontSize=9.5,
                                leading=11.5, alignment=TA_LEFT,
                                textColor=colors.HexColor('#333333'))

    text_block = [Paragraph(school_title.upper(), name_style)]
    motto = getattr(school, 'school_motto', None)
    if motto:
        text_block.append(Paragraph(motto, motto_style))
    address = getattr(school, 'school_address', None)
    if address:
        text_block.append(Paragraph(address, addr_style))

    if logo_path:
        try:
            left_cell = Image(logo_path, width=1.15 * inch, height=1.15 * inch)
        except Exception:
            left_cell = Paragraph('', addr_style)
    else:
        left_cell = Paragraph('', addr_style)

    right_cell = text_block if len(text_block) > 1 else text_block[0]

    table = Table(
        [[left_cell, right_cell]],
        colWidths=[1.3 * inch, None],
        hAlign='LEFT',
    )
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(table)
    story.append(HRFlowable(width='100%', thickness=0.8,
                            color=colors.HexColor('#1a6a3a'),
                            spaceBefore=5, spaceAfter=9))

    return logo_clean




def generate_admission_letter_pdf(
    *, student_name, class_offered,
    guardian_title, guardian_name, guardian_address,
    school, resume_date,
    letter_date=None,
    payment_deadline=None,
    acceptance_deadline=None,
    letter_template=None,
    override_student_name=None,
    override_guardian_name=None,
    override_guardian_address=None,
    override_principal_name=None,
    override_deposit_words=None,
    override_deposit_display=None,
    override_intro=None,
    override_deposit_para=None,
    override_notes_text=None,
    extra_note=None,
) -> io.BytesIO:
    # ── 1. Resolve template text (fall back to built-in defaults) ─────
    if letter_template:
        default_intro       = letter_template.get_intro()
        default_deposit     = letter_template.get_deposit()
        default_notes_text  = letter_template.get_notes()
        default_extra       = letter_template.get_extra()
        closing_line        = letter_template.get_closing()
        signature_title     = letter_template.get_signature_title()
        letterhead_line     = letter_template.get_letterhead_school_line()
        deposit_words       = letter_template.get_deposit_words()
        deposit_display     = letter_template.get_deposit_display()
        bank_name           = letter_template.get_bank_name()
        bank_branch_hint    = letter_template.get_bank_branch_hint()
        bank_account        = letter_template.get_bank_account()
        bank_account_name   = letter_template.get_bank_account_name()
        accept_email_1      = letter_template.get_acceptance_email_1()
        accept_email_2      = letter_template.get_acceptance_email_2()
        payment_window      = letter_template.payment_window_days or PAYMENT_WINDOW_DAYS
        accept_window       = letter_template.acceptance_window_days or ACCEPTANCE_WINDOW_DAYS
    else:
        default_intro       = DEFAULT_INTRO_TEMPLATE
        default_deposit     = DEFAULT_DEPOSIT_TEMPLATE
        default_notes_text  = DEFAULT_NOTES_TEMPLATE
        default_extra       = ''
        closing_line        = DEFAULT_CLOSING_LINE
        signature_title     = DEFAULT_SIGNATURE_TITLE
        letterhead_line     = LETTERHEAD_SCHOOL_LINE
        deposit_words       = DEPOSIT_AMOUNT_WORDS
        deposit_display     = DEPOSIT_AMOUNT_DISPLAY
        bank_name           = BANK_NAME
        bank_branch_hint    = BANK_BRANCH_HINT
        bank_account        = BANK_ACCOUNT
        bank_account_name   = BANK_ACCOUNT_NAME
        accept_email_1      = ACCEPTANCE_EMAIL_1
        accept_email_2      = ACCEPTANCE_EMAIL_2
        payment_window      = PAYMENT_WINDOW_DAYS
        accept_window       = ACCEPTANCE_WINDOW_DAYS

    # ── 2. Dates ─────────────────────────────────────────────────────
    letter_date = letter_date or date.today()
    if payment_deadline is None:
        payment_deadline = letter_date + timedelta(days=payment_window)
    if acceptance_deadline is None:
        acceptance_deadline = payment_deadline + timedelta(days=accept_window)

    # ── 3. Per-student overrides (short text fields) ─────────────────
    original_student_name = student_name   # name from NewUser
    if override_student_name:
        student_name = override_student_name
    if override_guardian_name:
        guardian_name = override_guardian_name
        guardian_title = ''
    if override_guardian_address:
        guardian_address = override_guardian_address
    if override_deposit_words:
        deposit_words = override_deposit_words
    if override_deposit_display:
        deposit_display = override_deposit_display
    # fff
    class_label = CLASS_LABELS.get(class_offered, class_offered)

    def _swap_name(text):
        # Replace the NewUser name baked into override text with the override name
        if text and original_student_name and original_student_name != student_name:
            return text.replace(original_student_name, student_name)
        return text

    # ── 4. Interpolation context (for TEMPLATE defaults only) ────────
    fill_ctx = dict(
        student_name=student_name,
        letterhead=letterhead_line,
        class_label=class_label,
        session_name=SESSION_NAME,
        deposit_words=deposit_words,
        deposit_display=deposit_display,
        bank_name=bank_name,
        bank_branch_hint=bank_branch_hint,
        bank_account=bank_account,
        bank_account_name=bank_account_name,
        payment_deadline=_fmt_date(payment_deadline),
        acceptance_deadline=_fmt_date(acceptance_deadline),
        resume_date=_fmt_date(resume_date),
        acceptance_email_1=accept_email_1,
        acceptance_email_2=accept_email_2,
    )

    # ── 5. Document setup ───────────────────────────────────────────
        # ── Bold key details ────────────────────────────────────────────
    _bold_terms = [t for t in [
        student_name, class_label, SESSION_NAME,
        deposit_display, deposit_words, bank_account,
        _fmt_date(payment_deadline), _fmt_date(acceptance_deadline),
        _fmt_date(resume_date),
        accept_email_1, accept_email_2,
        "There is no refund of any fees if a student is expelled from the School, except for caution fee",
        "parent forfeits 50% of the fees paid",
        "School fees should always be paid in advance",
    ] if t]
    _bold_re = re.compile(
        '|'.join(re.escape(t) for t in sorted(_bold_terms, key=len, reverse=True)))

    def _bold(html):
        html = html.replace('<b>', '').replace('</b>', '')   # avoid double bold
        return _bold_re.sub(lambda m: f"<b>{m.group(0)}</b>", html)

    # ── 5. Document setup ───────────────────────────────────────────
    # ── Bold key details ────────────────────────────────────────────
    _bold_terms = [t for t in [
        student_name, class_label, SESSION_NAME,
        deposit_display, deposit_words, bank_account,
        _fmt_date(payment_deadline), _fmt_date(acceptance_deadline),
        _fmt_date(resume_date),
        accept_email_1, accept_email_2,
        "There is no refund of any fees if a student is expelled from the School, except for caution fee",
        "parent forfeits 50% of the fees paid",
        "School fees should always be paid in advance",
    ] if t]
    _bold_re = re.compile(
        '|'.join(re.escape(t) for t in sorted(_bold_terms, key=len, reverse=True)))

    def _bold(html):
        html = html.replace('<b>', '').replace('</b>', '')   # avoid double bold
        return _bold_re.sub(lambda m: f"<b>{m.group(0)}</b>", html)


    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title=f"Admission Letter - {student_name}",
        author=getattr(school, 'school_name', 'Esteem Learning Center'),
    )

    base   = getSampleStyleSheet()['BodyText']
    body   = ParagraphStyle('Body', parent=base, fontName='Times-Roman',
                            fontSize=11, leading=13.5, alignment=TA_JUSTIFY,
                            spaceAfter=5)
    date_s = ParagraphStyle('Date', parent=body, alignment=TA_LEFT, spaceAfter=8)
    addr_s = ParagraphStyle('Addr', parent=body, alignment=TA_LEFT, spaceAfter=8)
    head_s = ParagraphStyle('Head', parent=body, fontName='Times-Bold',
                            fontSize=12, alignment=TA_CENTER,
                            spaceBefore=4, spaceAfter=6)
    num_s  = ParagraphStyle('Num', parent=body, leftIndent=17,
                            firstLineIndent=-17, spaceAfter=4)
    sign_s = ParagraphStyle('Sign', parent=body, alignment=TA_LEFT,
                            spaceBefore=8, spaceAfter=2)
    bold_s = ParagraphStyle('Bold', parent=body, fontName='Times-Bold',
                            alignment=TA_LEFT, spaceAfter=0, spaceBefore=2)

    # ── 6. Build story ──────────────────────────────────────────────
    story = []
    logo_clean = _build_letterhead(story, school)

    story.append(Paragraph(_fmt_date(letter_date), date_s))

    salutation = f"{guardian_title} {guardian_name}".strip()
    if salutation:
        story.append(Paragraph(f"<b>{salutation}</b>,", addr_s))
    if guardian_address:
        story.append(Paragraph(guardian_address.replace('\n', '<br/>'), addr_s))

    story.append(Paragraph("Dear Parent/Guardian,", body))
    story.append(Paragraph("CONDITIONAL OFFER OF ADMISSION", head_s))

    # ── Intro paragraph ─────────────────────────────────────────────
    # If the student has an override, print it AS-IS.
    # Otherwise interpolate the shared template.
    if override_intro:
        intro_html = _fill(_swap_name(override_intro), **fill_ctx)
    else:
        intro_html = _fill(default_intro, **fill_ctx)
    story.append(Paragraph(_bold(intro_html), body))

    story.append(Paragraph(
        "Due to the high number of applications received, we request you let us know at the "
        "earliest possible date if you accept the offer by,", body))

    # ── Deposit paragraph ───────────────────────────────────────────
    if override_deposit_para:
        deposit_html = _fill(_swap_name(override_deposit_para), **fill_ctx)
        
    else:
        deposit_html = _fill(default_deposit, **fill_ctx)
    story.append(Paragraph(_bold(deposit_html), body))

    # ── Extra paragraph ─────────────────────────────────────────────
    # extra_note (per-student) — verbatim; default_extra — interpolated
    if extra_note:
        story.append(Paragraph(extra_note, body))
    elif default_extra:
        story.append(Paragraph(_fill(default_extra, **fill_ctx), body))

    # ── Numbered notes ──────────────────────────────────────────────
    if override_notes_text:
        notes = [_fill(_swap_name(line.strip()), **fill_ctx)
                 for line in override_notes_text.splitlines() if line.strip()]
    else:
        notes = [_fill(line.strip(), **fill_ctx)
                 for line in default_notes_text.splitlines()
                 if line.strip()]
    if notes:
        story.append(Paragraph("Please note:", body))
        for i, note in enumerate(notes, 1):
            story.append(Paragraph(f"{i}.&nbsp;&nbsp;{_bold(note)}", num_s))

    # ── Closing ─────────────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(Paragraph(closing_line, head_s))
    story.append(Paragraph("Yours Sincerely,", sign_s))

    # ── Signature image ─────────────────────────────────────────────
    sig_path, sig_clean = _cloudinary_to_tempfile(
        getattr(school, 'principal_signature', None))
    if sig_path:
        try:
            story.append(Spacer(1, 4))
            story.append(Image(sig_path, width=1.3 * inch, height=0.55 * inch,
                               hAlign='LEFT'))
        except Exception:
            pass

    # ── Principal name + signature title ────────────────────────────
    story.append(Spacer(1, 2))
    principal_display = (override_principal_name
                         or getattr(school, 'principal_name', None)
                         or DEFAULT_PRINCIPAL_NAME)
    story.append(Paragraph(principal_display, bold_s))
    story.append(Paragraph(signature_title, body))

    doc.build(story)
    logo_clean()
    sig_clean()
    buf.seek(0)
    return buf