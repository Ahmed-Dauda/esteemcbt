import json
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from openai import OpenAI

from .models import (
    Chapter, ChatMessage, Project, Section,
    DEFAULT_CHAPTERS, DEFAULT_SECTIONS,
)

from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from users.models import NewUser


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

    # FIX 1: Save content from JSON body (sent by saveSection() JS) OR form POST
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
    project_pk = section.chapter.project.pk
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
    """
    FIX 2: Build history BEFORE saving the new user message, so it
    contains only prior turns. Then append the new message manually.
    This prevents the user message from appearing twice in the prompt.

    FIX 3: Return a proper error JSON (not a 502 with an HTML traceback)
    so the frontend can display a helpful message.
    """
    data       = json.loads(request.body)
    user_msg   = data.get("message", "").strip()
    section_id = data.get("section_id")
    # Live editor text sent from frontend — overrides DB content for context
    current_text = data.get("current_text", "").strip()

    if not user_msg:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)
    if not section_id:
        return JsonResponse({"error": "section_id is required."}, status=400)

    section = get_object_or_404(
        Section, pk=section_id, chapter__project__owner=request.user
    )
    project = section.chapter.project

    # If frontend sent live editor content, use it for context
    if current_text:
        section.content = current_text  # temp override, not saved to DB

    # ── Build history from PREVIOUS messages only (last 19 turns) ──────────
    prior_history = list(
        section.chat_messages
        .order_by("created_at")
        .values("role", "content")
    )[-19:]  # leave room for the new user message below

    # ── Append the new user message to the prompt list ─────────────────────
    messages_for_openai = prior_history + [{"role": "user", "content": user_msg}]

    system = _build_context(project, section)

    try:
        reply = _call_openai(system, messages_for_openai)
    except Exception as exc:
        # FIX 3: Return JSON so the JS can show it gracefully
        return JsonResponse(
            {"error": f"AI error: {str(exc)}"},
            status=502,
        )

    # ── Persist both turns AFTER a successful AI call ──────────────────────
    ChatMessage.objects.create(section=section, role="user",      content=user_msg)
    ChatMessage.objects.create(section=section, role="assistant", content=reply)

    return JsonResponse({"reply": reply})


# ─────────────────────────────────────────────────────────────────────────────
# OTHER TOOLS  — FIX 4: added @login_required to the shared helper
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


# FIX 4: _tool_endpoint is not a view so decorators don't apply here —
# auth is enforced on every caller above instead.
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

@login_required_custom
def export_word(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    raise NotImplementedError("Word export not yet implemented.")


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


"""
Drop these into your research/views.py.
Replace the old export_word / export_pdf / export_ppt stubs.

pip install python-docx
"""

import io
import re

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from .models import Project, Chapter


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _style_document(doc: Document, project_title: str):
    """Apply consistent academic styles to a new Document."""
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    # Heading 1  →  Chapter heading
    h1 = doc.styles['Heading 1']
    h1.font.name = 'Times New Roman'
    h1.font.size = Pt(14)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0x1a, 0x56, 0xdb)   # blue

    # Heading 2  →  Section heading
    h2 = doc.styles['Heading 2']
    h2.font.name = 'Times New Roman'
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0x11, 0x18, 0x27)   # near-black

    # Cover title
    title_para = doc.add_heading(project_title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.runs[0].font.size = Pt(18)
    title_para.runs[0].font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    doc.add_paragraph()   # spacer


def _add_chapter(doc: Document, chapter: Chapter):
    """Add one chapter (heading + all sections) to the document."""
    doc.add_heading(f"Chapter {chapter.number}: {chapter.title}", level=1)

    for section in chapter.sections.order_by('order'):
        doc.add_heading(f"{section.number} {section.title}", level=2)

        content = (section.content or '').strip()
        if content:
            # Split on double newlines → paragraphs
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

    doc.add_paragraph()   # spacer between chapters


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


# ─────────────────────────────────────────────────────────────────────────────
# VIEWS
# ─────────────────────────────────────────────────────────────────────────────

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




@property
def word_count(self):
    return len(self.content.split()) if self.content else 0


@property
def page_count(self):
    return round(self.word_count / 250) or 0  # ~250 words per page


@property
def completion_pct(self):
    sections = Section.objects.filter(chapter__project=self)
    total = sections.count()
    filled = sections.exclude(content='').count()
    return round((filled / total * 100)) if total else 0

from .models import Project, Reference
from django.shortcuts import get_object_or_404, redirect

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

from .models import Dataset

# views.py
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Dataset, Project
from .forms import DatasetUploadForm

# views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

import pandas as pd
import cloudinary.uploader
from django.core.files.uploadedfile import InMemoryUploadedFile

@require_POST
def upload_dataset(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    uploaded_file = request.FILES.get('file')

    if not uploaded_file:
        return JsonResponse({'error': 'No file provided.'}, status=400)

    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ['csv', 'xlsx', 'xls']:
        return JsonResponse({'error': 'Only CSV and Excel files are allowed.'}, status=400)

    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'File must be under 10MB.'}, status=400)

    try:
        # Optionally test-read the file (optional) – but reset file pointer
        if ext == 'csv':
            import pandas as pd
            pd.read_csv(uploaded_file)  # test read
        else:
            import pandas as pd
            pd.read_excel(uploaded_file)
        uploaded_file.seek(0)  # important: reset file pointer after pandas read

        # Create dataset – CloudinaryField will auto-upload to cloud
        dataset = Dataset.objects.create(
            project=project,
            file=uploaded_file,
            name=uploaded_file.name,
        )
        # ❌ REMOVED: dataset.row_count = len(df)  (field doesn't exist)
        # ❌ REMOVED: dataset.column_count = len(df.columns)
        # ✅ No extra save needed – just return success

        return JsonResponse({
            'success': True,
            'dataset_id': dataset.id,
            'redirect_url': f'/research/projects/{project_id}/datasets/{dataset.id}/',
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)
    

import requests
from io import BytesIO

def dataset_detail(request, project_id, dataset_id):
    project = get_object_or_404(Project, id=project_id)
    dataset = get_object_or_404(Dataset, id=dataset_id, project=project)

    preview = None
    stats = None
    error = None

    try:
        # Download file from Cloudinary URL into memory
        response = requests.get(dataset.file.url)
        response.raise_for_status()
        file_data = BytesIO(response.content)

        # Read with pandas based on extension
        if dataset.file.url.endswith('.csv'):
            df = pd.read_csv(file_data)
        else:
            df = pd.read_excel(file_data)

        preview = df.head(10).to_html(classes='table table-sm table-bordered', index=False)
        stats = df.describe().to_html(classes='table table-sm table-bordered')

    except Exception as e:
        error = str(e)

    return render(request, 'research/dataset_detail.html', {
        'project': project,
        'dataset': dataset,
        'preview': preview,
        'stats': stats,
        'error': error,
    })


# views.py – add these imports at the top if missing
import json
import numpy as np
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseBadRequest

# ----------------------------------------------------------------------
# 1. AI analysis of dataset
# ----------------------------------------------------------------------
@login_required_custom
@require_POST
def analyze_dataset_ai(request, project_id, dataset_id):
    """Send dataset preview + stats to AI, return analysis text."""
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    dataset = get_object_or_404(Dataset, id=dataset_id, project=project)
    data = json.loads(request.body)
    section_id = data.get('section_id')
    
    try:
        # Reload dataframe for full preview (not just first 10)
        response = requests.get(dataset.file.url)
        response.raise_for_status()
        file_data = BytesIO(response.content)
        ext = dataset.file.url.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file_data)
        else:
            df = pd.read_excel(file_data)
        
        # Prepare preview (first 20 rows) and basic statistics
        preview_text = df.head(20).to_string()
        stats_text = df.describe().to_string()
        
        system_prompt = (
            "You are a data analysis assistant for a Nigerian university research project. "
            "Write a concise, academic paragraph (4–6 sentences) interpreting the dataset below. "
            "Comment on the number of rows, columns, key statistics, and any noticeable patterns or issues. "
            "Do not use markdown or bullet points – write plain English prose."
        )
        user_prompt = f"""Dataset preview (first 20 rows):
{preview_text}

Descriptive statistics:
{stats_text}

Write an analysis paragraph suitable for a 'Data Presentation' section of a dissertation."""
        
        analysis = _call_openai(system_prompt, [{"role": "user", "content": user_prompt}])
        
        # Optionally save the text into a section
        if section_id:
            section = get_object_or_404(Section, pk=section_id, chapter__project__owner=request.user)
            section.content = analysis
            section.save(update_fields=['content'])
        
        return JsonResponse({'success': True, 'analysis': analysis, 'section_id': section_id})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ----------------------------------------------------------------------
# 2. Clean missing data
# ----------------------------------------------------------------------
@login_required_custom
@require_POST
def clean_dataset(request, dataset_id):
    """Drop rows with NaN or fill numeric columns with median."""
    data = json.loads(request.body)
    method = data.get('method')  # 'drop_rows' or 'fill_median'
    dataset = get_object_or_404(Dataset, id=dataset_id, project__owner=request.user)
    
    try:
        # Download file from Cloudinary
        response = requests.get(dataset.file.url)
        response.raise_for_status()
        file_data = BytesIO(response.content)
        ext = dataset.file.url.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file_data)
        else:
            df = pd.read_excel(file_data)
        
        if method == 'drop_rows':
            df_clean = df.dropna()
            rows_dropped = len(df) - len(df_clean)
        elif method == 'fill_median':
            df_clean = df.copy()
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)
            rows_dropped = 0
        else:
            return JsonResponse({'error': 'Invalid method'}, status=400)
        
        # Save cleaned file back to Cloudinary (overwrite or create new)
        # We'll create a new file name to avoid overwriting original
        new_filename = f"cleaned_{dataset.name}"
        csv_buffer = BytesIO()
        df_clean.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Upload cleaned version to Cloudinary
        upload_result = cloudinary.uploader.upload(
            csv_buffer,
            folder='datasets/cleaned/',
            resource_type='auto',
            public_id=f"cleaned_{dataset.id}_{int(datetime.now().timestamp())}",
            format='csv'
        )
        # Create a new Dataset record for cleaned version
        cleaned_dataset = Dataset.objects.create(
            project=dataset.project,
            name=f"Cleaned ({method}) - {dataset.name}",
            file=upload_result['secure_url'],  # CloudinaryField expects URL or file
            # Note: CloudinaryField can store a URL; you may need to adjust model if using field
        )
        # For simplicity, we'll store the URL in a custom field or replace the file?
        # We'll assume your CloudinaryField can take a URL string (django-cloudinary-storage does).
        # If not, you can use a regular URLField.
        # We'll implement using a new field: cleaned_file (URLField) or just return the URL.
        # To keep it simple, we'll return the URL and let frontend offer download.
        
        return JsonResponse({
            'success': True,
            'cleaned_file_url': upload_result['secure_url'],
            'rows_dropped': rows_dropped,
            'rows_remaining': len(df_clean),
            'preview': df_clean.head(10).to_html(classes='table', index=False),
            'stats': df_clean.describe().to_html(classes='table')
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ----------------------------------------------------------------------
# 3. Rename column
# ----------------------------------------------------------------------
@login_required_custom
@require_POST
def rename_dataset_column(request, dataset_id):
    data = json.loads(request.body)
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        return JsonResponse({'error': 'Both old and new names required'}, status=400)
    
    dataset = get_object_or_404(Dataset, id=dataset_id, project__owner=request.user)
    try:
        response = requests.get(dataset.file.url)
        response.raise_for_status()
        file_data = BytesIO(response.content)
        ext = dataset.file.url.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file_data)
        else:
            df = pd.read_excel(file_data)
        
        if old_name not in df.columns:
            return JsonResponse({'error': f'Column "{old_name}" not found'}, status=400)
        
        df.rename(columns={old_name: new_name}, inplace=True)
        
        # Save renamed file to Cloudinary
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        upload_result = cloudinary.uploader.upload(
            csv_buffer,
            folder='datasets/renamed/',
            resource_type='auto',
            public_id=f"renamed_{dataset.id}_{int(datetime.now().timestamp())}",
            format='csv'
        )
        # Create new Dataset record (optional) or update existing. We'll update original's file?
        # I'll create a new record to preserve original.
        renamed_dataset = Dataset.objects.create(
            project=dataset.project,
            name=f"Renamed ({old_name}→{new_name}) - {dataset.name}",
            file=upload_result['secure_url']
        )
        return JsonResponse({
            'success': True,
            'new_dataset_id': renamed_dataset.id,
            'preview': df.head(10).to_html(classes='table', index=False),
            'stats': df.describe().to_html(classes='table')
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ----------------------------------------------------------------------
# 4. Age distribution data (for Chart.js)
# ----------------------------------------------------------------------
@login_required_custom
@require_GET
def age_distribution_data(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id, project__owner=request.user)
    try:
        response = requests.get(dataset.file.url)
        response.raise_for_status()
        file_data = BytesIO(response.content)
        ext = dataset.file.url.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file_data)
        else:
            df = pd.read_excel(file_data)
        # Assume column name is 'age' (or attempt to find numeric column)
        age_col = None
        for col in df.columns:
            if col.lower() == 'age':
                age_col = col
                break
        if age_col is None:
            # pick first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                age_col = numeric_cols[0]
            else:
                return JsonResponse({'error': 'No numeric column found for age distribution'}, status=400)
        
        # Count frequency of each age (or bin for histogram)
        ages = df[age_col].dropna()
        # For histogram, we'll bin into 5-year intervals
        bins = range(int(ages.min()) - (int(ages.min()) % 5), int(ages.max()) + 6, 5)
        hist, bin_edges = np.histogram(ages, bins=bins)
        labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])-1}" for i in range(len(bin_edges)-1)]
        
        return JsonResponse({
            'success': True,
            'column': age_col,
            'labels': labels,
            'frequencies': hist.tolist(),
            'raw_values': ages.tolist()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    