from django.urls import path

from school import settings
from . import views
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [

    # urls.py – add inside urlpatterns
path('projects/<int:project_id>/datasets/<int:dataset_id>/analyze/', views.analyze_dataset_ai, name='analyze_dataset_ai'),
path('datasets/<int:dataset_id>/clean/', views.clean_dataset, name='clean_dataset'),
path('datasets/<int:dataset_id>/rename-column/', views.rename_dataset_column, name='rename_dataset_column'),
path('datasets/<int:dataset_id>/age-distribution/', views.age_distribution_data, name='age_distribution_data'),


# urls.py
path('projects/<int:project_id>/upload-dataset/', views.upload_dataset, name='upload_dataset'),
#     ^^^^^^^^ plural, matches /research/projects/3/upload/

    path('projects/<int:project_id>/datasets/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),

    path("project/<int:pk>/reference/add/", views.add_reference, name="add_reference"),
    path("chapter/<int:pk>/export/word/", views.export_chapter_word, name="export_chapter_word"),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # ── Project ──────────────────────────────────────────────────────────────
    path("",                              views.home,            name="home"),
    path("project/new/",                  views.create_project,  name="create_project"),
    path("project/<int:pk>/",             views.project_detail,  name="project_detail"),

    # ── Editor ───────────────────────────────────────────────────────────────
    path("section/<int:pk>/",             views.section_detail,  name="section_detail"),

    # ── Section management ───────────────────────────────────────────────────
    path("section/add/",                  views.add_section,         name="add_section"),
    path("section/<int:pk>/rename/",      views.edit_section_title,  name="edit_section_title"),
    path("section/<int:pk>/delete/",      views.delete_section,      name="delete_section"),
    path("sections/reorder/",             views.reorder_sections,     name="reorder_sections"),

    # ── AI endpoints ─────────────────────────────────────────────────────────
    path("api/ai-action/",               views.ai_action,       name="ai_action"),
    path("api/chat/",                    views.chat,            name="chat"),

    # ── Other tools ──────────────────────────────────────────────────────────
    path("api/tools/improve-writing/",   views.improve_writing, name="improve_writing"),
    path("api/tools/humanize/",          views.humanize_text,   name="humanize_text"),
    path("api/tools/grammar/",           views.check_grammar,   name="check_grammar"),

    # ── Exports ──────────────────────────────────────────────────────────────
    path("project/<int:pk>/export/word/", views.export_word,   name="export_word"),
    path("project/<int:pk>/export/pdf/",  views.export_pdf,    name="export_pdf"),
    path("project/<int:pk>/export/ppt/",  views.export_ppt,    name="export_ppt"),

    # ── Defense & Build ──────────────────────────────────────────────────────
    path("project/<int:pk>/defense/",     views.defense_prep,  name="defense_prep"),
    path("project/<int:pk>/build/",       views.build_project, name="build_project"),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)