from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
  

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
        column_name= 'categories',
        attribute='categories',
        widget=ForeignKeyWidget(Categories,'name') )
    
    class Meta:
        model = Courses
        prepopulated_fields = {"slug": ("course_name",)}
        # fields = ('title',)


@admin.action(description="Delete all unused Placeholder Title courses")
def delete_unused_placeholder_courses(modeladmin, request, queryset):
    placeholder_courses = Courses.objects.filter(title="Placeholder Title")

    deleted_count = 0
    for course in placeholder_courses:
        # Skip deletion if course is used in CourseGrade
        if not course.coursegrade_set.exists():
            course.delete()
            deleted_count += 1

    modeladmin.message_user(request, f"Deleted {deleted_count} unused Placeholder Title course(s).")


class CoursesAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = ['title', 'created_by', 'session', 'term', 'exam_type', 'display_subjects_school', 'created']
    list_filter = ['title']
    search_fields = ['title']
    ordering = ['title']
    actions = [delete_unused_placeholder_courses]
     
    resource_class = CoursesResource

    def display_subjects_school(self, obj):
        return ", ".join([str(course) for course in obj.schools.all()])
    
    display_subjects_school.short_description = 'School'

    def created_by(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}" if obj.created_by else "Unknown"

    created_by.short_description = 'Created By'

admin.site.register(Courses, CoursesAdmin)


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


