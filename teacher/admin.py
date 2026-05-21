from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Teacher, SampleCodes, ColumnLock

admin.site.register(SampleCodes)
admin.site.register(ColumnLock)


from .models import TeacherCourseObjective

@admin.register(TeacherCourseObjective)
class TeacherCourseObjectiveAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'course', 'updated_at')
    list_filter = ('course', 'updated_at')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'course__course_name')
    readonly_fields = ('updated_at',)


class AdminTeacher(admin.ModelAdmin):
    list_display = ['id','first_name', 'last_name', 'email', 'username', 'display_subjects_taught', 'display_classes_taught', 'school']
    search_fields = ['first_name', 'last_name', 'school__school_name']
    list_filter = ['school']
    filter_horizontal = ['classes_taught', 'subjects_taught']
    ordering = ['first_name', 'last_name']


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
