from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# ==============================
#  GRADING SYSTEM CONFIGURATION
# ==============================

GRADE_SCALE = [
    (70, 'A', 'Excellent'),
    (60, 'B', 'Very Good'),
    (50, 'C', 'Good'),
    (45, 'D', 'Fair'),
    (40, 'E', 'Pass'),
    (0,  'F', 'Fail'),
]


def get_grade(mark):
    """
    Return (grade_letter, remark) based on the mark.
    """
    try:
        mark = float(mark)
    except (TypeError, ValueError):
        return 'F', 'Invalid'

    for threshold, grade, remark in GRADE_SCALE:
        if mark >= threshold:
            return grade, remark
    return 'F', 'Fail'


def round_decimal(value, places=2):
    """
    Safely round a number to given decimal places.
    """
    try:
        q = Decimal(10) ** -places
        return Decimal(value).quantize(q, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal(0).quantize(Decimal(10) ** -places)


# ==============================
#  PDF RENDERING HELPER
# ==============================
def render_to_pdf(template_src, context_dict=None, filename="result.pdf"):
    """
    Convert Django HTML template to PDF using xhtml2pdf.
    Returns an HttpResponse containing the generated PDF.
    """
    if context_dict is None:
        context_dict = {}

    try:
        template = get_template(template_src)
        html = template.render(context_dict).encode("UTF-8")
    except Exception as e:
        return HttpResponse(f"Error rendering template: {e}", status=500)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        return HttpResponse("Error rendering PDF document.", status=400)
