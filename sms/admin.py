from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
from quiz.models import CourseGrade 

from sms.models import (
    Categories, Courses,
  Gallery, 
    FrequentlyAskQuestions, CourseFrequentlyAskQuestions,
    # CourseLearnerReviews, 
 
    CourseLearnerReviews,Session, Term)

from quiz.models import ExamType

admin.site.site_header = 'Esteem dashboard'
admin.site.site_title = 'Esteem super admin dashboard'
# admin.site.register(Courses)
admin.site.register(FrequentlyAskQuestions)
admin.site.register(Session)
admin.site.register(Term)

class ExamTypeAdmin(admin.ModelAdmin):

    list_display = ['name','description']
    search_fields = ['name']  # Add search field for course name

admin.site.register(ExamType, ExamTypeAdmin)

# admin.py

# admin.py
from django.contrib import admin
from .models import AboutUs, Awards


@admin.register(Awards)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_preview')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content Preview'


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_preview')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content Preview'


from .models import CarouselImage, FrontPageVideo

class FrontPageVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video', 'created', 'updated')


admin.site.register(FrontPageVideo, FrontPageVideoAdmin)


class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ['image_carousel', 'caption']

admin.site.register(CarouselImage, CarouselImageAdmin)

class CoursesResource(resources.ModelResource):
    courses = fields.Field(
        column_name='categories',
        attribute='categories',
        widget=ForeignKeyWidget(Categories, 'name')
    )

    class Meta:
        model = Courses
        prepopulated_fields = {"slug": ("course_name",)}


@admin.register(Courses)
class CoursesAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = [
        'title', 'created_by', 'session', 'term',
        'exam_type', 'display_subjects_school', 'created'
    ]
    list_filter = ['title']
    search_fields = ['title']
    ordering = ['id']
    resource_class = CoursesResource

    def display_subjects_school(self, obj):
        return ", ".join([str(school) for school in obj.schools.all()])
    
    display_subjects_school.short_description = 'School'

    def created_by(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return "Unknown"
    
    created_by.short_description = 'Created By'

    # 🔒 Safe delete for a single course
    def delete_model(self, request, obj):
        for grade in CourseGrade.objects.filter(subjects=obj):
            grade.subjects.remove(obj)
        obj.delete()

    # 🔒 Safe delete for multiple selected courses
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            for grade in CourseGrade.objects.filter(subjects=obj):
                grade.subjects.remove(obj)
            obj.delete()


# class CoursesResource(resources.ModelResource):
    
#     courses = fields.Field(
#         column_name= 'categories',
#         attribute='categories',
#         widget=ForeignKeyWidget(Categories,'name') )
    
#     class Meta:
#         model = Courses
#         prepopulated_fields = {"slug": ("course_name",)}
#         # fields = ('title',)

# class CoursesAdmin(ImportExportModelAdmin, ExportActionMixin):
#     list_display = ['title', 'created_by', 'session', 'term', 'exam_type', 'display_subjects_school', 'created']
#     list_filter = ['title']
#     search_fields = ['title']
#     ordering = ['id']
    
#     resource_class = CoursesResource

#     def display_subjects_school(self, obj):
#         return ", ".join([str(course) for course in obj.schools.all()])
    
#     display_subjects_school.short_description = 'School'

#     def created_by(self, obj):
#         return f"{obj.created_by.first_name} {obj.created_by.last_name}" if obj.created_by else "Unknown"

#     created_by.short_description = 'Created By'

# admin.site.register(Courses, CoursesAdmin)


# class CoursesAdmin(ImportExportModelAdmin, ExportActionMixin):

#     list_display = ['title', 'created_by','session','term','exam_type','display_subjects_school', 'created']
#     list_filter =  ['title']
#     search_fields = ['title']
#     ordering = ['id']
    
#     resource_class = CoursesResource
#     def display_subjects_school(self, obj):
#         return ", ".join([str(course) for course in obj.schools.all()])

#     display_subjects_school.short_description = 'School'

# admin.site.register(Courses, CoursesAdmin)


