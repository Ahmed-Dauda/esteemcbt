import json
import os
import traceback
from io import BytesIO, StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from openai import OpenAI
from django.core.cache import cache
import pickle
import math
import numpy as np
import pandas as pd
import re
import requests
import cloudinary.uploader
from datetime import datetime

# Add these for Word export functionality
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Add at the top of views.py with other imports
from .models import (
    Chapter, ChatMessage, Project, Section, Reference, Dataset,
    DEFAULT_CHAPTERS, DEFAULT_SECTIONS,
)

from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from users.models import NewUser

from functools import wraps
from django.shortcuts import redirect
from django.conf import settings


from functools import wraps
from django.shortcuts import redirect

def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/research/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_custom
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None

    if request.method == 'POST':
        email      = request.POST.get('email', '').strip().lower()
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        if not all([email, username, first_name, password1, password2]):
            error = 'All fields are required.'
        elif password1 != password2:
            error = 'Passwords do not match.'
        elif len(password1) < 8:
            error = 'Password must be at least 8 characters.'
        elif NewUser.objects.filter(email=email).exists():
            error = 'An account with this email already exists.'
        elif NewUser.objects.filter(username=username).exists():
            error = 'This username is already taken.'
        else:
            user = NewUser.objects.create(
                email      = email,
                username   = username,
                first_name = first_name,
                password   = make_password(password1),
                is_active  = True,
            )
            login(request, user)
            return redirect('home')

    return render(request, 'research/signup.html', {'error': error})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            error = 'Both fields are required.'
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next') or 'home'
                return redirect(next_url)
            else:
                error = 'Invalid username or password.'

    return render(request, 'research/login.html', {
        'error': error,
        'next': request.GET.get('next', ''),
    })


from django.conf import settings
client = OpenAI(api_key=getattr(settings, "OPENAI_API_KEY", None))
MODEL  = "gpt-4o-mini"


# ─────────────────────────────────────────────────────────────────────────────
# STATISTICAL HELPER FUNCTIONS (No scipy - pure numpy)
# ─────────────────────────────────────────────────────────────────────────────

def ttest_ind(data1, data2):
    """Independent t-test using numpy only"""
    data1, data2 = np.array(data1), np.array(data2)
    n1, n2 = len(data1), len(data2)
    
    if n1 < 2 or n2 < 2:
        raise ValueError("Each group must have at least 2 observations")
    
    mean1, mean2 = np.mean(data1), np.mean(data2)
    var1, var2 = np.var(data1, ddof=1), np.var(data2, ddof=1)
    
    # Welch's t-test (doesn't assume equal variance)
    se = np.sqrt(var1/n1 + var2/n2)
    t_stat = (mean1 - mean2) / se if se > 0 else 0
    
    # Degrees of freedom (Welch-Satterthwaite)
    df_num = (var1/n1 + var2/n2)**2
    df_den = (var1**2/(n1**2*(n1-1))) + (var2**2/(n2**2*(n2-1)))
    df = df_num / df_den if df_den > 0 else n1 + n2 - 2
    
    # Approximate p-value (normal approximation for large df)
    from math import erf
    p_value = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / np.sqrt(2))))
    p_value = min(max(p_value, 0.0001), 0.9999)
    
    return t_stat, p_value, df


def linregress(x, y):
    """Linear regression using numpy only"""
    x, y = np.array(x), np.array(y)
    n = len(x)
    
    if n < 3:
        raise ValueError("Need at least 3 data points for regression")
    
    x_mean, y_mean = np.mean(x), np.mean(y)
    xx = x - x_mean
    yy = y - y_mean
    
    slope = np.sum(xx * yy) / np.sum(xx**2) if np.sum(xx**2) != 0 else 0
    intercept = y_mean - slope * x_mean
    
    # R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - y_mean)**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    r_value = np.sqrt(r_squared) if slope >= 0 else -np.sqrt(r_squared)
    
    # Standard error and p-value
    if n > 2 and np.sum(xx**2) != 0:
        std_err = np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum(xx**2))
        t_stat = slope / std_err if std_err != 0 else 0
        from math import erf
        p_value = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / np.sqrt(2))))
        p_value = min(max(p_value, 0.0001), 0.9999)
    else:
        std_err, p_value = 0, 1.0
    
    return slope, intercept, r_value, p_value, std_err


def pearsonr(x, y):
    """Pearson correlation using numpy only"""
    x, y = np.array(x), np.array(y)
    n = len(x)
    
    if n < 3:
        raise ValueError("Need at least 3 data points for correlation")
    
    corr_matrix = np.corrcoef(x, y)
    r_value = corr_matrix[0, 1]
    
    # Approximate p-value
    if n > 2 and abs(r_value) < 1:
        t_stat = r_value * np.sqrt((n - 2) / (1 - r_value**2)) if r_value**2 < 1 else 0
        from math import erf
        p_value = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / np.sqrt(2))))
        p_value = min(max(p_value, 0.0001), 0.9999)
    else:
        p_value = 1.0
    
    return r_value, p_value


def chi2_contingency(observed):
    """Chi-square test using numpy only"""
    observed = np.array(observed, dtype=float)
    total = np.sum(observed)
    
    # Expected frequencies
    row_sums = np.sum(observed, axis=1)
    col_sums = np.sum(observed, axis=0)
    expected = np.outer(row_sums, col_sums) / total if total > 0 else observed
    
    # Chi-square statistic
    chi2 = np.sum((observed - expected)**2 / np.maximum(expected, 1e-10))
    
    # Degrees of freedom
    dof = (observed.shape[0] - 1) * (observed.shape[1] - 1)
    
    # Approximate p-value
    from math import exp
    p_value = exp(-chi2 / 2) if chi2 > 0 else 1.0
    p_value = min(max(p_value, 0.0001), 0.9999)
    
    return chi2, p_value, dof, expected


def f_oneway(*args):
    """One-way ANOVA using numpy only"""
    args = [np.array(arg, dtype=float) for arg in args]
    
    # Remove NaN values
    args = [arg[~np.isnan(arg)] for arg in args]
    
    k = len(args)
    n_total = sum(len(arg) for arg in args)
    grand_mean = np.mean(np.concatenate(args))
    
    # Between-group sum of squares
    ss_between = sum(len(arg) * (np.mean(arg) - grand_mean)**2 for arg in args)
    
    # Within-group sum of squares
    ss_within = sum(sum((val - np.mean(arg))**2 for val in arg) for arg in args)
    
    df_between = k - 1
    df_within = n_total - k
    
    if df_within == 0:
        raise ValueError("Insufficient degrees of freedom")
    
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within
    
    f_stat = ms_between / ms_within if ms_within > 0 else 0
    
    # Approximate p-value
    from math import exp
    p_value = exp(-f_stat / 2) if f_stat > 0 else 1.0
    p_value = min(max(p_value, 0.0001), 0.9999)
    
    return f_stat, p_value


def shapiro(data):
    """Simple normality test (skewness/kurtosis based)"""
    data = np.array(data, dtype=float)
    data = data[~np.isnan(data)]
    n = len(data)
    
    if n < 4:
        raise ValueError("Need at least 4 data points")
    
    # Calculate skewness and kurtosis
    skewness = np.mean(((data - np.mean(data)) / np.std(data, ddof=1))**3)
    kurtosis = np.mean(((data - np.mean(data)) / np.std(data, ddof=1))**4) - 3
    
    # Jarque-Bera test approximation
    jb_stat = n * (skewness**2 / 6 + kurtosis**2 / 24)
    
    from math import exp
    p_value = exp(-jb_stat / 2) if jb_stat > 0 else 1.0
    p_value = min(max(p_value, 0.0001), 0.9999)
    
    # Rough normality score (higher = more normal)
    w_stat = 1 - min(abs(skewness) / 2, 1) * 0.3 - min(abs(kurtosis) / 7, 1) * 0.3
    w_stat = max(0.7, min(0.99, w_stat))
    
    return w_stat, p_value


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_context(project: Project, section: Section) -> str:
    return (
        f"You are an academic writing assistant for a Nigerian university research project.\n"
        f"Project title: \"{project.title}\"\n"
        f"Chapter: {section.chapter.number} – {section.chapter.title}\n"
        f"Section: {section.number} {section.title}\n\n"
        f"Current section content:\n{section.content or '(empty)'}\n\n"
        "Respond in clear, academic English suitable for an undergraduate dissertation. "
        "Be concise and helpful."
    )


def _call_openai(system: str, messages: list) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, *messages],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# PROJECT VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required_custom
def home(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, "research/home.html", {"projects": projects})


@login_required_custom
def create_project(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if not title:
            return render(request, "research/create_project.html",
                          {"error": "Title is required."})

        project = Project.objects.create(owner=request.user, title=title)

        for number, chapter_title, subtitle in DEFAULT_CHAPTERS:
            chapter = Chapter.objects.create(
                project=project,
                number=number,
                title=chapter_title,
                subtitle=subtitle,
                is_open=(number == 1),
            )
            for order, section_title in enumerate(
                DEFAULT_SECTIONS.get(number, []), start=1
            ):
                Section.objects.create(
                    chapter=chapter,
                    title=section_title,
                    order=order,
                )

        first_section = (
            Section.objects.filter(chapter__project=project)
            .order_by("chapter__number", "order")
            .first()
        )
        return redirect("section_detail", pk=first_section.pk)

    return render(request, "research/create_project.html")


@login_required_custom
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    first_section = (
        Section.objects.filter(chapter__project=project)
        .order_by("chapter__number", "order")
        .first()
    )
    if first_section:
        return redirect("section_detail", pk=first_section.pk)
    return redirect("home")


@login_required_custom
def section_detail(request, pk):
    section = get_object_or_404(
        Section, pk=pk, chapter__project__owner=request.user
    )
    project        = section.chapter.project
    active_chapter = section.chapter

    if request.method == "POST":
        content_type = request.content_type or ""
        if "application/json" in content_type:
            data    = json.loads(request.body)
            content = data.get("content", "").strip()
        else:
            content = request.POST.get("content", "").strip()

        section.content = content
        section.save(update_fields=["content", "updated_at"])
        return JsonResponse({"status": "ok"})

    chapters = project.chapters.prefetch_related("sections").all()
    for ch in chapters:
        ch.is_open = (ch.pk == active_chapter.pk)

    chat_history = section.chat_messages.order_by("created_at").all()

    return render(request, "research/project_studio.html", {
        "project":           project,
        "chapters":          chapters,
        "active_chapter":    active_chapter,
        "active_section":    section,
        "active_section_id": section.pk,
        "chat_history":      chat_history,
    })


# ─────────────────────────────────────────────────────────────────────────────
# SECTION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@login_required_custom
@require_POST
def add_section(request):
    data       = json.loads(request.body)
    chapter_id = data.get("chapter_id")
    title      = data.get("title", "").strip()

    if not chapter_id or not title:
        return JsonResponse({"error": "chapter_id and title are required."}, status=400)

    chapter = get_object_or_404(Chapter, pk=chapter_id, project__owner=request.user)
    order   = chapter.sections.count() + 1
    section = Section.objects.create(chapter=chapter, title=title, order=order)

    return JsonResponse({
        "id":     section.pk,
        "title":  section.title,
        "number": section.number,
        "order":  section.order,
    })


@login_required_custom
@require_POST
def edit_section_title(request, pk):
    section = get_object_or_404(Section, pk=pk, chapter__project__owner=request.user)
    data    = json.loads(request.body)
    title   = data.get("title", "").strip()
    if not title:
        return JsonResponse({"error": "Title cannot be empty."}, status=400)
    section.title = title
    section.save(update_fields=["title"])
    return JsonResponse({"title": section.title})


@login_required_custom
@require_POST
def delete_section(request, pk):
    section    = get_object_or_404(Section, pk=pk, chapter__project__owner=request.user)
    chapter_pk = section.chapter.pk
    section.delete()
    next_section = Section.objects.filter(chapter__pk=chapter_pk).first()
    redirect_url = (
        f"/research/section/{next_section.pk}/"
        if next_section
        else f"/research/project/{section.chapter.project.pk}/"
    )
    return JsonResponse({"redirect": redirect_url})


@login_required_custom
@require_POST
def reorder_sections(request):
    data  = json.loads(request.body)
    order = data.get("order", [])
    for idx, section_id in enumerate(order, start=1):
        Section.objects.filter(
            pk=section_id, chapter__project__owner=request.user
        ).update(order=idx)
    return JsonResponse({"status": "ok"})


# ─────────────────────────────────────────────────────────────────────────────
# AI ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

QUICK_ACTION_PROMPTS = {
    "improve":   "Rewrite and improve the current section content. Make it more academically rigorous, well-structured, and professional. Return only the improved text.",
    "detailed":  "Expand the current section content with more depth, examples, and supporting details. Return only the expanded text.",
    "simplify":  "Rewrite the current section content in simpler, clearer language while maintaining academic tone. Return only the simplified text.",
    "context":   "Rewrite or expand the section content to include relevant Nigerian context, statistics, and examples. Return only the updated text.",
    "citations": "Add 3–5 relevant academic in-text citations (APA format) to the section content and append a 'References' list at the end. Return the updated text with citations.",
}


@login_required_custom
@require_POST
def ai_action(request):
    data       = json.loads(request.body)
    action     = data.get("action", "")
    section_id = data.get("section_id")

    if action not in QUICK_ACTION_PROMPTS:
        return JsonResponse({"error": "Unknown action."}, status=400)
    if not section_id:
        return JsonResponse({"error": "section_id is required."}, status=400)

    section = get_object_or_404(Section, pk=section_id, chapter__project__owner=request.user)
    project = section.chapter.project

    system      = _build_context(project, section)
    user_prompt = QUICK_ACTION_PROMPTS[action]

    try:
        result = _call_openai(system, [{"role": "user", "content": user_prompt}])
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    section.content = result
    section.save(update_fields=["content", "updated_at"])

    return JsonResponse({"result": result})


@login_required_custom
@require_POST
def chat(request):
    data       = json.loads(request.body)
    user_msg   = data.get("message", "").strip()
    section_id = data.get("section_id")
    current_text = data.get("current_text", "").strip()

    if not user_msg:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)
    if not section_id:
        return JsonResponse({"error": "section_id is required."}, status=400)

    section = get_object_or_404(
        Section, pk=section_id, chapter__project__owner=request.user
    )
    project = section.chapter.project

    if current_text:
        section.content = current_text

    prior_history = list(
        section.chat_messages
        .order_by("created_at")
        .values("role", "content")
    )[-19:]

    messages_for_openai = prior_history + [{"role": "user", "content": user_msg}]

    system = _build_context(project, section)

    try:
        reply = _call_openai(system, messages_for_openai)
    except Exception as exc:
        return JsonResponse(
            {"error": f"AI error: {str(exc)}"},
            status=502,
        )

    ChatMessage.objects.create(section=section, role="user",      content=user_msg)
    ChatMessage.objects.create(section=section, role="assistant", content=reply)

    return JsonResponse({"reply": reply})


# ─────────────────────────────────────────────────────────────────────────────
# OTHER TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@login_required_custom
@require_POST
def improve_writing(request):
    return _tool_endpoint(
        request,
        "Rewrite the text to be more polished, clear, and academically appropriate. "
        "Return only the rewritten text.",
    )


@login_required_custom
@require_POST
def humanize_text(request):
    return _tool_endpoint(
        request,
        "Rewrite the text so it sounds more natural and human-authored, "
        "removing robotic or repetitive phrasing. Return only the rewritten text.",
    )


@login_required_custom
@require_POST
def check_grammar(request):
    return _tool_endpoint(
        request,
        "Correct all grammatical, spelling, and punctuation errors in the text. "
        "Return only the corrected text with no explanations.",
    )


def _tool_endpoint(request, prompt: str):
    data        = json.loads(request.body)
    section_id  = data.get("section_id")
    custom_text = data.get("text", "")

    section = get_object_or_404(
        Section, pk=section_id, chapter__project__owner=request.user
    )
    project = section.chapter.project

    system   = _build_context(project, section)
    content  = custom_text or section.content or ""
    messages = [{"role": "user", "content": f"{prompt}\n\nText:\n{content}"}]

    try:
        result = _call_openai(system, messages)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"result": result})


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

def _style_document(doc: Document, project_title: str):
    """Apply consistent academic styles to a new Document."""
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    h1 = doc.styles['Heading 1']
    h1.font.name = 'Times New Roman'
    h1.font.size = Pt(14)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0x1a, 0x56, 0xdb)

    h2 = doc.styles['Heading 2']
    h2.font.name = 'Times New Roman'
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

    title_para = doc.add_heading(project_title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.runs[0].font.size = Pt(18)
    title_para.runs[0].font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    doc.add_paragraph()


def _add_chapter(doc: Document, chapter: Chapter):
    """Add one chapter (heading + all sections) to the document."""
    doc.add_heading(f"Chapter {chapter.number}: {chapter.title}", level=1)

    for section in chapter.sections.order_by('order'):
        doc.add_heading(f"{section.number} {section.title}", level=2)

        content = (section.content or '').strip()
        if content:
            paragraphs = re.split(r'\n{2,}', content)
            for para_text in paragraphs:
                para_text = para_text.strip()
                if para_text:
                    p = doc.add_paragraph(para_text)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.space_after = Pt(6)
        else:
            p = doc.add_paragraph('[No content yet]')
            p.runs[0].font.italic = True
            p.runs[0].font.color.rgb = RGBColor(0x9c, 0xa3, 0xaf)

    doc.add_paragraph()


def _build_response(doc: Document, filename: str) -> HttpResponse:
    """Serialise the document and return as a file-download response."""
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required_custom
def export_word(request, pk):
    """Export the FULL project as a single .docx file."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)

    doc = Document()
    _style_document(doc, project.title)

    for chapter in project.chapters.prefetch_related('sections').order_by('number'):
        _add_chapter(doc, chapter)

    safe_title = re.sub(r'[^\w\s-]', '', project.title)[:60].strip()
    filename = f"{safe_title}.docx"
    return _build_response(doc, filename)


@login_required_custom
def export_chapter_word(request, pk):
    """Export a SINGLE chapter as a .docx file."""
    chapter = get_object_or_404(
        Chapter, pk=pk, project__owner=request.user
    )
    project = chapter.project

    doc = Document()
    _style_document(doc, project.title)
    _add_chapter(doc, chapter)

    safe_title = re.sub(r'[^\w\s-]', '', project.title)[:40].strip()
    filename = f"{safe_title} - Chapter {chapter.number}.docx"
    return _build_response(doc, filename)


@login_required_custom
def export_pdf(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    raise NotImplementedError("PDF export not yet implemented.")


@login_required_custom
def export_ppt(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    raise NotImplementedError("PPT export not yet implemented.")


@login_required_custom
def defense_prep(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)

    all_content = []
    for chapter in project.chapters.prefetch_related("sections").all():
        for section in chapter.sections.all():
            if section.content:
                all_content.append(f"### {section.number} {section.title}\n{section.content}")

    full_text = "\n\n".join(all_content) or "No content yet."

    system = (
        f"You are an academic defense coach for a Nigerian university project.\n"
        f"Project: \"{project.title}\"\n\n"
        "Based on the project content provided, generate 10 likely defense questions "
        "and suggested answers. Format as:\n"
        "Q1: ...\nA1: ...\n\nQ2: ...\nA2: ..."
    )
    try:
        result = _call_openai(
            system,
            [{"role": "user", "content": f"Project content:\n\n{full_text}"}],
        )
    except Exception as exc:
        result = f"Error: {exc}"

    return render(request, "research/defense_prep.html", {
        "project": project,
        "qa":      result,
    })


@login_required_custom
@require_POST
def build_project(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    updated = []

    for chapter in project.chapters.prefetch_related("sections").all():
        for section in chapter.sections.filter(content=""):
            system = _build_context(project, section)
            prompt = (
                f"Write a comprehensive academic content for section "
                f"\"{section.number} {section.title}\" of the project "
                f"\"{project.title}\". "
                "Use formal academic language suitable for a Nigerian undergraduate dissertation. "
                "The content should be 4–8 paragraphs long."
            )
            try:
                content = _call_openai(system, [{"role": "user", "content": prompt}])
                section.content = content
                section.save(update_fields=["content", "updated_at"])
                updated.append({"id": section.pk, "title": section.title})
            except Exception as exc:
                updated.append({"id": section.pk, "error": str(exc)})

    return JsonResponse({"updated": updated})


def add_reference(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        year = request.POST.get("year")
        source = request.POST.get("source")

        Reference.objects.create(
            project=project,
            title=title,
            author=author,
            year=year,
            source=source
        )

    return redirect("project_detail", pk=pk)


# ─────────────────────────────────────────────────────────────────────────────
# DATASET HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _download_cloudinary_file(cloudinary_field) -> io.BytesIO:
    """Download a Cloudinary file and return as BytesIO buffer."""
    url = cloudinary_field.url
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return io.BytesIO(response.content)


def _read_file(cloudinary_field_or_upload, filename: str = "") -> pd.DataFrame:
    """
    Read CSV or Excel from either:
    - A Cloudinary field (existing dataset)
    - A Django uploaded file (new upload)
    """
    name = filename or getattr(cloudinary_field_or_upload, "name", "") or ""
    name = name.lower()

    if hasattr(cloudinary_field_or_upload, "url"):
        buf = _download_cloudinary_file(cloudinary_field_or_upload)
        if name.endswith(".csv") or "csv" in name:
            return pd.read_csv(buf)
        else:
            return pd.read_excel(buf)

    if name.endswith(".csv"):
        return pd.read_csv(cloudinary_field_or_upload)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(cloudinary_field_or_upload)

    raise ValueError("Unsupported file type. Use CSV or XLSX.")


def _analyse_df(df: pd.DataFrame) -> dict:
    """Build the analysis dict that the template/JS consumes."""
    df = df.fillna("—")
    columns = list(df.columns)
    total_rows = len(df)
    total_cols = len(columns)
    preview = df.head(10).to_dict(orient="records")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    main_col = numeric_cols[0] if numeric_cols else None

    stats = {}
    charts = []

    if main_col:
        series = df[main_col]
        stats["mean_label"] = main_col
        stats["mean"] = float(series.mean())
        stats["max"] = float(series.max())
        stats["min"] = float(series.min())

        stats["extra"] = {
            "Standard Deviation": round(float(series.std()), 2),
            "Median": round(float(series.median()), 2),
            "Mode": float(series.mode().iloc[0]) if not series.mode().empty else "—",
        }

        bins = [0, 49, 59, 69, 79, 100]
        labels = ["0-49", "50-59", "60-69", "70-79", "80-100"]
        try:
            cut = pd.cut(series, bins=bins, labels=labels, right=True)
            dist = cut.value_counts().reindex(labels, fill_value=0).to_dict()
            stats["distribution"] = {str(k): int(v) for k, v in dist.items()}

            pass_count = int((series >= 50).sum())
            fail_count = int((series < 50).sum())
            stats["extra"]["Pass Percentage"] = f"{round(pass_count/total_rows*100, 2)}%"
            stats["extra"]["Fail Percentage"] = f"{round(fail_count/total_rows*100, 2)}%"

            charts.append({
                "title": f"{main_col} Distribution",
                "type": "bar",
                "labels": list(dist.keys()),
                "data": [int(v) for v in dist.values()],
                "dataset_label": "Number of Records",
            })
        except Exception:
            pass

    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    if cat_cols:
        cat_col = cat_cols[0]
        cat_dist = df[cat_col].value_counts().head(6).to_dict()
        stats.setdefault("distribution", {str(k): int(v) for k, v in cat_dist.items()})

        charts.append({
            "title": f"{cat_col} Distribution",
            "type": "pie",
            "labels": [str(k) for k in cat_dist.keys()],
            "data": [int(v) for v in cat_dist.values()],
            "dataset_label": cat_col,
        })

    if main_col and len(cat_cols) >= 1:
        grp = df.groupby(cat_cols[0])[main_col].mean().head(6)
        charts.append({
            "title": f"Avg {main_col} by {cat_cols[0]}",
            "type": "bar",
            "labels": [str(k) for k in grp.index],
            "data": [round(float(v), 2) for v in grp.values],
            "dataset_label": f"Avg {main_col}",
        })

    if main_col and len(columns) >= 1:
        id_col = columns[0]
        top10 = df.nlargest(10, main_col)[[id_col, main_col]].reset_index(drop=True)
        charts.append({
            "title": f"Top 10 by {main_col}",
            "type": "bar",
            "labels": [str(r[id_col]) for _, r in top10.iterrows()],
            "data": [float(r[main_col]) for _, r in top10.iterrows()],
            "dataset_label": main_col,
        })

    return {
        "columns": columns,
        "preview": preview,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "count_label": columns[0] if columns else "Records",
        "stats": stats,
        "charts": charts,
    }


def _get_working_df(user_id, dataset_id):
    cache_key = f"working_df_{user_id}_{dataset_id}"
    df_json = cache.get(cache_key)

    if df_json is not None:
        return pd.read_json(StringIO(df_json), orient="split")

    try:
        dataset = get_object_or_404(Dataset, pk=dataset_id, project__owner_id=user_id)
        df = _read_file(dataset.file, filename=dataset.name)
        df_json = df.to_json(orient="split", date_format="iso")
        cache.set(cache_key, df_json, timeout=3600)
        return df
    except Exception as e:
        return None


def _save_working_df(user_id, dataset_id, df):
    cache_key = f'working_df_{user_id}_{dataset_id}'
    df_json = df.to_json(orient="split", date_format="iso")
    cache.set(cache_key, df_json, timeout=3600)


def _get_chapter4(project: Project) -> Chapter:
    """Return Chapter 4 (Data Analysis) for this project."""
    return Chapter.objects.get(project=project, number=4)


def convert_to_native(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    return obj


# ============================================================================
# DATA ANALYSIS VIEWS
# ============================================================================

@login_required
def data_analysis_page(request, pk):
    """GET /research/project/<pk>/data-analysis/"""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    datasets = Dataset.objects.filter(project=project).order_by("-uploaded_at")

    try:
        ch4 = _get_chapter4(project)
        ch4_first = ch4.sections.order_by("order").first()
        ch4_first_pk = ch4_first.pk if ch4_first else 0
    except Chapter.DoesNotExist:
        ch4_first_pk = 0

    initial_analysis = None
    initial_dataset_id = None
    ds_id = request.GET.get("dataset")
    if ds_id:
        try:
            ds = Dataset.objects.get(pk=ds_id, project=project)
            df = _read_file(ds.file)
            initial_analysis = _analyse_df(df)
            initial_dataset_id = ds.pk
        except Exception:
            pass

    return render(request, "research/data_analysis.html", {
        "project": project,
        "datasets": datasets,
        "chapter4_first_section_pk": ch4_first_pk,
        "initial_analysis": json.dumps(initial_analysis) if initial_analysis else None,
        "initial_dataset_id": initial_dataset_id,
    })


@login_required
@require_POST
def upload_dataset(request, pk):
    """Upload a CSV/Excel file, store in Cloudinary, and immediately analyse it."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    file = request.FILES.get("file")

    if not file:
        return JsonResponse({"error": "No file provided."}, status=400)

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        return JsonResponse({"error": "Only CSV and Excel files are allowed."}, status=400)

    if file.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "File must be under 10 MB."}, status=400)

    try:
        file_content = file.read()

        if ext == ".csv":
            try:
                df = pd.read_csv(StringIO(file_content.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_csv(StringIO(file_content.decode("latin-1")))
        else:
            df = pd.read_excel(BytesIO(file_content))

        clean_file = InMemoryUploadedFile(
            file=BytesIO(file_content),
            field_name="file",
            name=file.name,
            content_type=file.content_type,
            size=len(file_content),
            charset=None,
        )

        dataset = Dataset.objects.create(
            project=project,
            file=clean_file,
            name=file.name,
        )

        df_json = df.to_json(orient="split", date_format="iso")
        cache_key = f"working_df_{request.user.id}_{dataset.pk}"
        cache.set(cache_key, df_json, timeout=3600)

        analysis = _analyse_df(df)

        return JsonResponse({
            "dataset_id": dataset.pk,
            "analysis": analysis,
            "redirect_url": f"/research/project/{pk}/data-analysis/?dataset={dataset.pk}",
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"Upload failed: {str(e)}"}, status=500)


@login_required
@require_GET
def load_dataset(request, pk):
    """Load existing dataset — from cache first, Cloudinary fallback."""
    ds = get_object_or_404(Dataset, pk=pk, project__owner=request.user)

    df = _get_working_df(request.user.id, ds.pk)

    if df is None:
        try:
            df = _read_file(ds.file, filename=ds.name)
            df_json = df.to_json(orient="split", date_format="iso")
            cache_key = f"working_df_{request.user.id}_{ds.pk}"
            cache.set(cache_key, df_json, timeout=3600)
        except Exception as e:
            return JsonResponse({"error": f"Could not load dataset: {str(e)}"}, status=500)

    analysis = _analyse_df(df)
    return JsonResponse({"analysis": analysis, "dataset_id": ds.pk})


@login_required
@require_POST
def delete_dataset(request, pk):
    """POST /research/api/delete-dataset/<pk>/"""
    ds = get_object_or_404(Dataset, pk=pk, project__owner=request.user)
    ds.file.delete(save=False)
    ds.delete()
    return JsonResponse({"ok": True})


@login_required
def export_dataset_csv(request, pk):
    """GET /research/api/export-dataset/<pk>/"""
    ds = get_object_or_404(Dataset, pk=pk, project__owner=request.user)
    try:
        df = _read_file(ds.file)
    except Exception as e:
        return HttpResponse(f"Error reading file: {e}", status=500)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{ds.name}"'
    df.to_csv(response, index=False)
    return response


@login_required
@require_POST
def rename_column(request, dataset_id):
    """Rename a column in the cached DataFrame."""
    data = json.loads(request.body)
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        return JsonResponse({'error': 'Missing old/new column names'}, status=400)
    
    df = _get_working_df(request.user.id, dataset_id)
    if df is None:
        return JsonResponse({'error': 'Dataset not found'}, status=404)
    
    if old_name not in df.columns:
        return JsonResponse({'error': f'Column "{old_name}" not found'}, status=400)
    
    df.rename(columns={old_name: new_name}, inplace=True)
    _save_working_df(request.user.id, dataset_id, df)
    analysis = _analyse_df(df)
    return JsonResponse({'success': True, 'analysis': analysis})


@login_required
@require_POST
def clean_dataset(request, dataset_id):
    """Handle missing values: drop rows or fill numeric medians."""
    data = json.loads(request.body)
    method = data.get('method')
    df = _get_working_df(request.user.id, dataset_id)
    
    if df is None:
        return JsonResponse({'error': 'Dataset not found'}, status=404)

    original_len = len(df)
    if method == 'drop_rows':
        df_clean = df.dropna()
        rows_removed = original_len - len(df_clean)
    elif method == 'fill_median':
        df_clean = df.copy()
        numeric_cols = df_clean.select_dtypes(include='number').columns
        for col in numeric_cols:
            df_clean[col].fillna(df_clean[col].median(), inplace=True)
        rows_removed = 0
    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)

    _save_working_df(request.user.id, dataset_id, df_clean)
    analysis = _analyse_df(df_clean)
    return JsonResponse({'success': True, 'analysis': analysis, 'rows_removed': rows_removed})


@login_required
@require_POST
def transform_dataset(request, dataset_id):
    """Apply transformation: filter or add_column."""
    data = json.loads(request.body)
    operation = data.get('operation')
    df = _get_working_df(request.user.id, dataset_id)
    
    if df is None:
        return JsonResponse({'error': 'Dataset not found'}, status=404)

    try:
        if operation == 'filter':
            col = data.get('column')
            op = data.get('operator')
            val = float(data.get('value'))
            query_str = f"`{col}` {op} {val}"
            df = df.query(query_str)
        elif operation == 'add_column':
            new_col = data.get('new_column')
            expr = data.get('expression')
            allowed = {col: df[col] for col in df.columns}
            allowed['np'] = np
            result = eval(expr, {"__builtins__": {}}, allowed)
            df[new_col] = result
        else:
            return JsonResponse({'error': 'Unsupported operation'}, status=400)
        
        _save_working_df(request.user.id, dataset_id, df)
        analysis = _analyse_df(df)
        return JsonResponse({'success': True, 'analysis': analysis})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def ai_assist_dataset(request, dataset_id):
    """Use AI to generate pandas code to manipulate DataFrame."""
    data = json.loads(request.body)
    instruction = data.get('instruction')
    
    if not instruction:
        return JsonResponse({'error': 'No instruction provided'}, status=400)

    try:
        df = _get_working_df(request.user.id, dataset_id)
        if df is None:
            return JsonResponse({'error': 'Dataset not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Could not load dataset: {str(e)}'}, status=400)

    df_info = f"DataFrame has {df.shape[0]} rows, {df.shape[1]} columns: {', '.join(df.columns)}. First row: {df.iloc[0].to_dict() if len(df) > 0 else 'empty'}"

    system = (
        "You are a data manipulation assistant. Return ONLY valid Python code that modifies the DataFrame variable 'df'.\n"
        "Do not include any explanation, markdown, or backticks. Use df = df[...] style.\n"
        "Example: 'remove rows where age < 18' -> df = df[df['age'] >= 18]\n"
        "Available libraries: pandas as pd, numpy as np. Built-in functions len, min, max, sum, int, float, str are allowed.\n"
        "The code will be executed in a restricted environment. Only modify 'df' and use pandas/numpy operations."
    )
    user = f"Current dataset info: {df_info}\n\nInstruction: {instruction}\n\nReturn only Python code:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        code = response.choices[0].message.content.strip()
        
        if code.startswith('```'):
            code = code.split('```')[1]
            if code.startswith('python'):
                code = code[6:]
            code = code.strip()

        allowed_builtins = {
            'len': len, 'min': min, 'max': max, 'sum': sum, 'abs': abs,
            'round': round, 'int': int, 'float': float, 'str': str, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'range': range,
            'enumerate': enumerate, 'zip': zip, 'True': True, 'False': False, 'None': None,
        }
        local_vars = {'df': df, 'pd': pd, 'np': np}
        exec(code, {"__builtins__": allowed_builtins}, local_vars)
        df = local_vars['df']

        _save_working_df(request.user.id, dataset_id, df)
        analysis = _analyse_df(df)

        return JsonResponse({'success': True, 'analysis': analysis, 'code': code})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': f'AI transformation failed: {str(e)}'}, status=500)


@login_required
@require_POST
def generate_chapter4(request):
    """Generate Chapter 4 using OpenAI."""
    data = json.loads(request.body)
    project = get_object_or_404(Project, pk=data["project_id"], owner=request.user)
    analysis = data.get("analysis", {})

    stats = analysis.get("stats", {})
    charts = analysis.get("charts", [])

    summary = (
        f"Dataset: {analysis.get('total_rows',0)} records, "
        f"{analysis.get('total_cols',0)} columns.\n"
        f"Columns: {', '.join(analysis.get('columns',[]))}\n"
        f"Mean: {stats.get('mean','N/A')}, Max: {stats.get('max','N/A')}, "
        f"Min: {stats.get('min','N/A')}\n"
    )
    if stats.get("distribution"):
        summary += "Distribution: " + ", ".join(
            f"{k}: {v}" for k, v in stats["distribution"].items()
        ) + "\n"
    if stats.get("extra"):
        summary += "Extra stats: " + ", ".join(
            f"{k}: {v}" for k, v in stats["extra"].items()
        ) + "\n"
    if charts:
        summary += "Charts generated: " + ", ".join(c["title"] for c in charts) + "\n"

    system = (
        f"You are an academic writing assistant for a Nigerian university dissertation.\n"
        f"Project: \"{project.title}\"\n"
        "Write Chapter 4: Data Presentation, Analysis and Interpretation.\n"
        "Use formal academic language. Structure with sections:\n"
        "4.1 Introduction\n4.2 Data Presentation\n4.3 Data Analysis\n"
        "4.4 Interpretation of Results\n4.5 Summary\n"
        "Each section should be 2-3 paragraphs."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Dataset summary:\n{summary}\n\nWrite the full Chapter 4."},
            ],
            max_tokens=2000,
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=502)

    return JsonResponse({"content": content})


@login_required
@require_POST
def apply_chapter4(request):
    """Apply AI-generated Chapter 4 to project sections."""
    data = json.loads(request.body)
    project = get_object_or_404(Project, pk=data["project_id"], owner=request.user)
    content = data.get("content", "").strip()

    if not content:
        return JsonResponse({"error": "No content to apply."}, status=400)

    try:
        ch4 = _get_chapter4(project)
    except Chapter.DoesNotExist:
        return JsonResponse({"error": "Chapter 4 not found."}, status=404)

    sections = ch4.sections.order_by("order")
    parts = re.split(r'\n(?=4\.\d)', content)

    for i, section in enumerate(sections):
        if i < len(parts):
            body_lines = parts[i].split("\n")
            body = "\n".join(body_lines[1:]).strip() if len(body_lines) > 1 else parts[i].strip()
            section.content = body
            section.save(update_fields=["content", "updated_at"])

    first_section = sections.first()
    redirect_url = f"/research/section/{first_section.pk}/" if first_section else f"/research/project/{project.pk}/"

    return JsonResponse({"ok": True, "redirect_url": redirect_url})


@login_required
@require_POST
def data_analysis_chat(request):
    """Chat endpoint for data analysis assistance."""
    data = json.loads(request.body)
    message = data.get('message', '')
    context = data.get('context', '')
    step = data.get('step', '')
    project = get_object_or_404(Project, pk=data['project_id'], owner=request.user)

    system = (
        f"You are a data analysis AI assistant for a Nigerian university research project: \"{project.title}\".\n"
        f"The user is on step: {step}.\n"
        f"Dataset context:\n{context}\n"
        "Give concise, actionable advice to improve their data analysis. "
        "When relevant, provide text they can directly apply to their Chapter 4."
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=502)

    return JsonResponse({"reply": reply})


# ============================================================================
# STATISTICAL ANALYSIS VIEWS
# ============================================================================

@login_required
@require_POST
def statistical_test(request):
    """Run statistical tests using built-in functions."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')
    test_type = data.get('test_type')
    params = data.get('parameters', {})

    if not dataset_id or not test_type:
        return JsonResponse({'error': 'Missing dataset ID or test type'}, status=400)

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        result_text = ""
        interpretation = ""
        hypothesis_summary = ""

        if test_type == 'ttest':
            test_var = params.get('test_var')
            group_var = params.get('group_var')

            if not test_var or not group_var:
                return JsonResponse({'error': 'Missing test variable or group variable'}, status=400)

            if test_var not in df.columns or group_var not in df.columns:
                return JsonResponse({'error': 'Column not found'}, status=400)

            groups = df[group_var].dropna().unique()
            if len(groups) != 2:
                return JsonResponse({'error': f'T-test requires exactly 2 groups. Found {len(groups)} groups.'}, status=400)

            group1_data = df[df[group_var] == groups[0]][test_var].dropna().tolist()
            group2_data = df[df[group_var] == groups[1]][test_var].dropna().tolist()

            if len(group1_data) < 2 or len(group2_data) < 2:
                return JsonResponse({'error': 'Each group needs at least 2 data points'}, status=400)

            t_stat, p_value, df_val = ttest_ind(group1_data, group2_data)

            result_text = f"""
            <strong>T-Test Results:</strong><br>
            Group 1 ({groups[0]}): n={len(group1_data)}, Mean={np.mean(group1_data):.3f}<br>
            Group 2 ({groups[1]}): n={len(group2_data)}, Mean={np.mean(group2_data):.3f}<br>
            t-statistic = {t_stat:.3f}, p-value = {p_value:.4f}<br>
            """

            if p_value < 0.05:
                interpretation = f"There is a statistically significant difference between groups (p = {p_value:.4f} < 0.05)."
                hypothesis_summary = "H0: No significant difference. REJECTED. H1: Significant difference. ACCEPTED."
            else:
                interpretation = f"There is no statistically significant difference between groups (p = {p_value:.4f} > 0.05)."
                hypothesis_summary = "H0: No significant difference. NOT REJECTED."

        elif test_type == 'regression':
            dep_var = params.get('dependent')
            indep_vars = params.get('independent', [])
            indep_var = indep_vars[0] if indep_vars else None

            if not dep_var or not indep_var:
                return JsonResponse({'error': 'Missing dependent or independent variable'}, status=400)

            valid_data = df[[dep_var, indep_var]].dropna()
            X = valid_data[indep_var].tolist()
            Y = valid_data[dep_var].tolist()

            slope, intercept, r_value, p_value, std_err = linregress(X, Y)
            r_squared = r_value ** 2

            result_text = f"""
            <strong>Regression Results:</strong><br>
            Equation: {dep_var} = {intercept:.3f} + {slope:.3f} × {indep_var}<br>
            R-squared = {r_squared:.3f} ({r_squared * 100:.1f}% variance explained)<br>
            p-value = {p_value:.4f}<br>
            """

            if p_value < 0.05:
                interpretation = f"The regression model is statistically significant (p = {p_value:.4f} < 0.05)."
                hypothesis_summary = f"H0: {indep_var} does not predict {dep_var}. REJECTED."
            else:
                interpretation = f"The regression model is not statistically significant (p = {p_value:.4f} > 0.05)."
                hypothesis_summary = f"H0: {indep_var} does not predict {dep_var}. NOT REJECTED."

        elif test_type == 'correlation':
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                return JsonResponse({'error': 'Need at least 2 numeric columns'}, status=400)

            col1, col2 = numeric_cols[0], numeric_cols[1]
            valid_data = df[[col1, col2]].dropna()
            r_val, p_val = pearsonr(valid_data[col1].tolist(), valid_data[col2].tolist())

            result_text = f"""
            <strong>Correlation Results:</strong><br>
            {col1} & {col2}: r = {r_val:.3f}, p = {p_val:.4f}<br>
            """

            interpretation = "Correlation analysis reveals the strength and direction of linear relationships between variables."
            hypothesis_summary = "H0: No correlation exists. H1: A significant correlation exists."

        else:
            return JsonResponse({'error': f'Unknown test type: {test_type}'}, status=400)

        return JsonResponse({
            'success': True,
            'result': result_text,
            'interpretation': interpretation,
            'hypothesis_summary': hypothesis_summary
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def descriptive_analysis(request):
    """Generate descriptive statistics for Chapter 4."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')

    if not dataset_id:
        return JsonResponse({'error': 'No dataset ID provided'}, status=400)

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        central_tendency = []
        for col in numeric_cols[:5]:
            series = df[col].dropna()
            if len(series) > 0:
                central_tendency.append({
                    'variable': col,
                    'mean': convert_to_native(series.mean()),
                    'median': convert_to_native(series.median()),
                    'mode': convert_to_native(series.mode().iloc[0]) if not series.mode().empty else 'N/A'
                })

        return JsonResponse({
            'success': True,
            'central_tendency': central_tendency,
            'central_interpretation': "The analysis shows the average (mean), middle (median), and most common (mode) values for each numeric variable."
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# ADDITIONAL REQUIRED VIEWS
# ============================================================================

@login_required
@require_POST
def exploratory_analysis(request):
    """Generate exploratory data analysis for Chapter 4."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')

    if not dataset_id:
        return JsonResponse({'error': 'No dataset ID provided'}, status=400)

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        distributions = []
        for col in numeric_cols[:5]:
            series = df[col].dropna()
            if len(series) > 0:
                skewness = convert_to_native(series.skew())
                distributions.append({
                    'variable': col,
                    'skewness': round(skewness, 2) if skewness else 0,
                })

        return JsonResponse({
            'success': True,
            'distributions': distributions,
            'distribution_summary': "Analysis of data distributions reveals important patterns in the dataset."
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def confirmatory_analysis(request):
    """Perform confirmatory analysis (hypothesis testing) for Chapter 4."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')
    test_type = data.get('test_type')
    params = data.get('parameters', {})

    if not dataset_id or not test_type:
        return JsonResponse({'error': 'Missing dataset ID or test type'}, status=400)

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        result_text = ""
        interpretation = ""
        hypothesis_summary = ""

        if test_type == 'ttest':
            test_var = params.get('test_var')
            group_var = params.get('group_var')

            groups = df[group_var].dropna().unique()
            group1_data = df[df[group_var] == groups[0]][test_var].dropna().tolist()
            group2_data = df[df[group_var] == groups[1]][test_var].dropna().tolist()

            t_stat, p_value, df_val = ttest_ind(group1_data, group2_data)

            result_text = f"T-Test: t = {t_stat:.3f}, p = {p_value:.4f}"

            if p_value < 0.05:
                interpretation = "There is a statistically significant difference between the groups."
                hypothesis_summary = "H0: REJECTED. H1: ACCEPTED."
            else:
                interpretation = "There is no statistically significant difference between the groups."
                hypothesis_summary = "H0: NOT REJECTED."

        elif test_type == 'regression':
            dep_var = params.get('dependent')
            indep_vars = params.get('independent', [])
            indep_var = indep_vars[0] if indep_vars else None

            valid_data = df[[dep_var, indep_var]].dropna()
            slope, intercept, r_value, p_value, std_err = linregress(valid_data[indep_var].tolist(), valid_data[dep_var].tolist())

            result_text = f"Regression: R² = {r_value**2:.3f}, p = {p_value:.4f}"

            if p_value < 0.05:
                interpretation = f"{indep_var} significantly predicts {dep_var}."
                hypothesis_summary = f"H0: REJECTED. {indep_var} predicts {dep_var}."
            else:
                interpretation = f"{indep_var} does not significantly predict {dep_var}."
                hypothesis_summary = f"H0: NOT REJECTED."

        elif test_type == 'correlation':
            var1 = params.get('variable1')
            var2 = params.get('variable2')
            valid_data = df[[var1, var2]].dropna()
            r_value, p_value = pearsonr(valid_data[var1].tolist(), valid_data[var2].tolist())

            result_text = f"Correlation: r = {r_value:.3f}, p = {p_value:.4f}"

            if p_value < 0.05:
                interpretation = f"There is a significant correlation between {var1} and {var2}."
                hypothesis_summary = "H0: REJECTED. Variables are correlated."
            else:
                interpretation = f"There is no significant correlation between {var1} and {var2}."
                hypothesis_summary = "H0: NOT REJECTED."

        else:
            return JsonResponse({'error': f'Unknown test type: {test_type}'}, status=400)

        return JsonResponse({
            'success': True,
            'result': result_text,
            'interpretation': interpretation,
            'hypothesis_summary': hypothesis_summary
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def generate_chapter_intro(request):
    """Generate Chapter 4 introduction using AI."""
    data = json.loads(request.body)
    project_id = data.get('project_id')
    analysis_data = data.get('analysis_data', {})

    try:
        project = get_object_or_404(Project, pk=project_id, owner=request.user)

        system_prompt = "You are an academic writing assistant for a Nigerian university dissertation."
        user_prompt = f"Write an introduction for Chapter 4 of project '{project.title}'."

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        return JsonResponse({'intro': response.choices[0].message.content.strip()})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def generate_chapter_summary(request):
    """Generate Chapter 4 summary using AI."""
    data = json.loads(request.body)
    project_id = data.get('project_id')

    try:
        project = get_object_or_404(Project, pk=project_id, owner=request.user)

        system_prompt = "You are an academic writing assistant."
        user_prompt = f"Write a summary for Chapter 4 of project '{project.title}'."

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        return JsonResponse({'summary': response.choices[0].message.content.strip()})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def save_chapter4(request):
    """Save complete Chapter 4 to project sections."""
    data = json.loads(request.body)
    project_id = data.get('project_id')
    content = data.get('content')

    try:
        project = get_object_or_404(Project, pk=project_id, owner=request.user)
        ch4 = Chapter.objects.get(project=project, number=4)
        first_section = ch4.sections.order_by('order').first()

        if first_section:
            first_section.content = content
            first_section.save()
            return JsonResponse({'redirect_url': f'/research/section/{first_section.pk}/'})

        return JsonResponse({'error': 'No section found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def regression_analysis(request):
    """Perform regression analysis."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')
    dependent_var = data.get('dependent_var')
    independent_vars = data.get('independent_vars', [])

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        indep_var = independent_vars[0] if independent_vars else None
        valid_data = df[[dependent_var, indep_var]].dropna()

        slope, intercept, r_value, p_value, std_err = linregress(
            valid_data[indep_var].tolist(),
            valid_data[dependent_var].tolist()
        )

        return JsonResponse({
            'success': True,
            'r_squared': round(r_value ** 2, 4),
            'p_value': round(p_value, 4),
            'slope': round(slope, 4),
            'intercept': round(intercept, 4)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def reliability_analysis(request):
    """Perform reliability analysis (Cronbach's alpha)."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        scale_cols = numeric_cols[:min(10, len(numeric_cols))]
        scale_data = df[scale_cols].dropna()

        n_items = len(scale_cols)
        item_variances = scale_data.var(axis=0, ddof=1)
        total_variance = scale_data.sum(axis=1).var(ddof=1)
        cronbach_alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance) if n_items > 1 else 0

        return JsonResponse({
            'success': True,
            'overall_alpha': round(cronbach_alpha, 4),
            'n_items': n_items,
            'sample_size': len(scale_data)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def get_chart_data(request):
    """Get data for generating charts."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        means = {col: convert_to_native(df[col].mean()) for col in numeric_cols[:5]}

        return JsonResponse({
            'success': True,
            'means': means,
            'numeric_columns': numeric_cols[:5]
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def generate_chart(request):
    """Generate chart based on selected columns."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')
    x_column = data.get('x_column')
    y_column = data.get('y_column')

    try:
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        if y_column and y_column in df.columns:
            grouped = df.groupby(x_column)[y_column].mean().sort_values(ascending=False).head(20)
            labels = [str(label) for label in grouped.index.tolist()]
            values = grouped.values.tolist()
            dataset_label = f'Average {y_column}'
        else:
            counts = df[x_column].value_counts().head(20)
            labels = [str(label) for label in counts.index.tolist()]
            values = counts.values.tolist()
            dataset_label = 'Count'

        return JsonResponse({
            'success': True,
            'labels': labels,
            'datasets': [{
                'label': dataset_label,
                'data': values,
                'backgroundColor': '#3b82f680',
                'borderColor': '#3b82f6',
                'borderWidth': 1
            }]
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def generate_chapter4_ai(request):
    """Use AI to generate complete Chapter 4 based on the dataset."""
    data = json.loads(request.body)
    dataset_id = data.get('dataset_id')
    project_id = data.get('project_id')

    try:
        project = get_object_or_404(Project, pk=project_id, owner=request.user)
        ds = get_object_or_404(Dataset, pk=dataset_id, project__owner=request.user)
        df = _read_file(ds.file, filename=ds.name)

        system_prompt = "You are an expert academic writer. Generate Chapter 4 for a dissertation."
        user_prompt = f"Project: {project.title}\nDataset has {len(df)} rows and {len(df.columns)} columns."

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )

        return JsonResponse({
            'success': True,
            'chapter_content': response.choices[0].message.content.strip()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# MOCK/PLACEHOLDER FUNCTIONS FOR COMPLETENESS
# ============================================================================

@login_required
@require_POST
def modify_chart(request):
    """Modify chart (placeholder)."""
    return JsonResponse({'success': True, 'message': 'Chart modification not fully implemented'})


@login_required
@require_POST
def generate_eda(request):
    """Generate EDA (placeholder)."""
    return JsonResponse({'charts': []})


@login_required
@require_POST
def analyze_missing_values(request):
    """Analyze missing values (placeholder)."""
    return JsonResponse({'missing_values': []})


@login_required
@require_POST
def analyze_outliers(request):
    """Analyze outliers (placeholder)."""
    return JsonResponse({'outliers': [], 'suggestion': 'No outlier analysis available'})


@login_required
@require_POST
def create_chart_from_prompt(request):
    """Create chart from prompt (placeholder)."""
    return JsonResponse({'success': True, 'message': 'AI chart generation not fully implemented'})


@login_required
@require_POST
def get_data_insights(request):
    """Get data insights (placeholder)."""
    return JsonResponse({'success': True, 'insight': 'Data insights not fully implemented'})


@login_required
@require_POST
def ai_statistical_analysis(request):
    """AI statistical analysis (placeholder)."""
    return JsonResponse({"success": True, "result": "AI statistical analysis not fully implemented"})


@login_required
@require_POST
def statistical_chat(request):
    """Statistical chat (placeholder)."""
    return JsonResponse({"reply": "Statistical chat assistant not fully implemented"})