from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('api/generate-chapter4-ai/', views.generate_chapter4_ai, name='generate_chapter4_ai'),
    path('api/regression-analysis/', views.regression_analysis, name='regression_analysis'),
path('api/reliability-analysis/', views.reliability_analysis, name='reliability_analysis'),
    # Add to urlpatterns
    path('api/get-chart-data/', views.get_chart_data, name='get_chart_data'),
path('api/descriptive-analysis/', views.descriptive_analysis, name='descriptive_analysis'),
path('api/exploratory-analysis/', views.exploratory_analysis, name='exploratory_analysis'),
path('api/confirmatory-analysis/', views.confirmatory_analysis, name='confirmatory_analysis'),
path('api/generate-chapter-intro/', views.generate_chapter_intro, name='generate_chapter_intro'),
path('api/generate-chapter-summary/', views.generate_chapter_summary, name='generate_chapter_summary'),
path('api/save-chapter4/', views.save_chapter4, name='save_chapter4'),


# EDA and Chart endpoints
path('api/modify-chart/', views.modify_chart, name='modify_chart'),
path('api/generate-eda/', views.generate_eda, name='generate_eda'),
path('api/analyze-missing-values/', views.analyze_missing_values, name='analyze_missing_values'),
path('api/analyze-outliers/', views.analyze_outliers, name='analyze_outliers'),
path('api/generate-chart/', views.generate_chart, name='generate_chart'),
path('api/create-chart-from-prompt/', views.create_chart_from_prompt, name='create_chart_from_prompt'),
path('api/get-data-insights/', views.get_data_insights, name='get_data_insights'),
path('api/statistical-test/', views.statistical_test, name='statistical_test'),


    # Add these to your urlpatterns
path('api/ai-statistical-analysis/', views.ai_statistical_analysis, name='ai_statistical_analysis'),
path('api/statistical-chat/', views.statistical_chat, name='statistical_chat'),

    path('api/rename-column/<int:dataset_id>/', views.rename_column, name='rename_column'),
path('api/clean-dataset/<int:dataset_id>/', views.clean_dataset, name='clean_dataset'),
path('api/transform-dataset/<int:dataset_id>/', views.transform_dataset, name='transform_dataset'),
path('api/ai-assist-dataset/<int:dataset_id>/', views.ai_assist_dataset, name='ai_assist_dataset'),

    # ── Auth ─────────────────────────────────────────────────────────────────
    path('signup/',  views.signup,     name='signup'),
    path('login/',   views.login_view, name='login'),
    path('logout/',  auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # ── Project ───────────────────────────────────────────────────────────────
    path('',                   views.home,           name='home'),
    path('project/new/',       views.create_project, name='create_project'),
    path('project/<int:pk>/',  views.project_detail, name='project_detail'),

    # ── Editor ────────────────────────────────────────────────────────────────
    path('section/<int:pk>/',          views.section_detail,     name='section_detail'),
    path('section/add/',               views.add_section,        name='add_section'),
    path('section/<int:pk>/rename/',   views.edit_section_title, name='edit_section_title'),
    path('section/<int:pk>/delete/',   views.delete_section,     name='delete_section'),
    path('sections/reorder/',          views.reorder_sections,   name='reorder_sections'),

    # ── AI endpoints ──────────────────────────────────────────────────────────
    path('api/data-analysis-chat/', views.data_analysis_chat, name='data_analysis_chat'),
    path('api/ai-action/',             views.ai_action,       name='ai_action'),
    path('api/chat/',                  views.chat,            name='chat'),
    path('api/tools/improve-writing/', views.improve_writing, name='improve_writing'),
    path('api/tools/humanize/',        views.humanize_text,   name='humanize_text'),
    path('api/tools/grammar/',         views.check_grammar,   name='check_grammar'),

    # ── Exports ───────────────────────────────────────────────────────────────
    path('chapter/<int:pk>/export/word/', views.export_chapter_word, name='export_chapter_word'),
    path('project/<int:pk>/export/word/', views.export_word,         name='export_word'),
    path('project/<int:pk>/export/pdf/',  views.export_pdf,          name='export_pdf'),
    path('project/<int:pk>/export/ppt/',  views.export_ppt,          name='export_ppt'),

    # ── Defense & Build ───────────────────────────────────────────────────────
    path('project/<int:pk>/defense/', views.defense_prep,  name='defense_prep'),
    path('project/<int:pk>/build/',   views.build_project, name='build_project'),

    # ── Data Analysis ─────────────────────────────────────────────────────────
    path('project/<int:pk>/data-analysis/',  views.data_analysis_page, name='data_analysis'),
    path('project/<int:pk>/upload-dataset/', views.upload_dataset,     name='upload_dataset'),
    path('api/load-dataset/<int:pk>/',       views.load_dataset,       name='load_dataset'),
    path('api/delete-dataset/<int:pk>/',     views.delete_dataset,     name='delete_dataset'),
    path('api/export-dataset/<int:pk>/',     views.export_dataset_csv, name='export_dataset_csv'),
    path('api/generate-chapter4/',           views.generate_chapter4,  name='generate_chapter4'),
    path('api/apply-chapter4/',              views.apply_chapter4,     name='apply_chapter4'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
