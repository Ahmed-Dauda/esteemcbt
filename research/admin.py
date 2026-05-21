from django.contrib import admin
from .models import Project, Chapter, Section, ChatMessage


# admin.py
from django.contrib import admin
from .models import Dataset

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display  = ('name', 'project', 'uploaded_at', 'file')
    list_filter   = ('project',)
    search_fields = ('name', 'project__title')
    readonly_fields = ('uploaded_at',)
    ordering      = ('-uploaded_at',)

    
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'word_count', 'created_at']

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['project', 'number', 'title']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'title', 'order', 'updated_at']
    list_filter  = ['chapter__project']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['section', 'role', 'created_at']