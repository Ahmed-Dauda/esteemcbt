from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Teacher, SampleCodes

admin.site.register(SampleCodes)

class AdminTeacher(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'username', 'display_subjects_taught', 'display_classes_taught', 'school']
    search_fields = ['first_name', 'last_name', 'school__school_name']
    list_filter = ['school']
    filter_horizontal = ['classes_taught', 'subjects_taught']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('school').prefetch_related('classes_taught', 'subjects_taught')
        return queryset

    def display_classes_taught(self, obj):
        return ", ".join([str(course.name) for course in obj.classes_taught.all()])

    def display_subjects_taught(self, obj):
        return ", ".join([str(course) for course in obj.subjects_taught.all()])

    def display_subjects_school(self, obj):
        return ", ".join([str(course.schools) for course in obj.subjects_taught.all()])

    display_classes_taught.short_description = 'Classes Taught'
    display_subjects_taught.short_description = 'Subjects Taught'
    display_subjects_school.short_description = 'Subject School'

admin.site.register(Teacher, AdminTeacher)

# class AdminTeacher(admin.ModelAdmin):
#     list_display = ['id','first_name', 'last_name', 'email','username','display_subjects_taught','display_classes_taught', 'school']
#     search_fields = ['first_name', 'last_name', 'school__school_name']
#     list_filter = ['school']
#     filter_horizontal = ['classes_taught', 'subjects_taught']

#     def display_classes_taught(self, obj):
#         return ", ".join([str(course.name) for course in obj.classes_taught.all()])

#     def display_subjects_taught(self, obj):
#         return ", ".join([str(course) for course in obj.subjects_taught.all()])

#     def display_subjects_school(self, obj):
#             return ", ".join([str(course.schools) for course in obj.subjects_taught.all()])

#     display_classes_taught.short_description = 'Classes Taught'
#     display_subjects_taught.short_description = 'Subjects Taught'
#     display_subjects_school.short_description = 'Subject School'

# admin.site.register(Teacher, AdminTeacher)

