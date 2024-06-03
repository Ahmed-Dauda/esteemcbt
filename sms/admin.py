from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
  

from sms.models import (
    Categories, Courses,
  Gallery, 
    FrequentlyAskQuestions, CourseFrequentlyAskQuestions,
    # CourseLearnerReviews, 
 
    CourseLearnerReviews,

    )

admin.site.site_header = 'Esteem super admin dashboard'
admin.site.site_title = 'Esteem super admin dashboard'
# admin.site.register(Courses)
admin.site.register(FrequentlyAskQuestions)

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


# class ArticleAdminResource(resources.ModelResource):
    
#     class Meta:
#         model = Blog
#         # fields = ('title',)
               
# class ArticleAdminAdmin(ImportExportModelAdmin):
    
#     prepopulated_fields = {"slug": ("title",)}
#     list_display = ['id', 'title', 'desc', 'created']
#     list_filter =  ['title']
#     search_fields = ['author__user','title']
#     ordering = ['id']
    
#     resource_class = ArticleAdminResource

# admin.site.register(Blog, ArticleAdminAdmin)



# class FeedbackcommentResource(resources.ModelResource):
    
#     class Meta:
#         model = Comment
#         # fields = ('title',)
               
# class FeedbackcommentResourceAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'title', 'desc', 'created']
#     list_filter =  ['title']
#     search_fields= ['title']
#     ordering = ['id']
    
#     resource_class = FeedbackcommentResource

# admin.site.register(Comment, FeedbackcommentResourceAdmin)


# class CategoriesResource(resources.ModelResource):
    
#     class Meta:
#         model = Categories
#         # fields = ('title',)
               
# class CategoriesAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'name', 'desc', 'created']
#     list_filter =  ['name']
#     search_fields= ['name', 'desc']
#     ordering = ['id']
    
#     resource_class = CategoriesResource

# admin.site.register(Categories, CategoriesAdmin)


class CoursesResource(resources.ModelResource):
    
    courses = fields.Field(
        column_name= 'categories',
        attribute='categories',
        widget=ForeignKeyWidget(Categories,'name') )
    
    class Meta:
        model = Courses
        prepopulated_fields = {"slug": ("course_name",)}
        # fields = ('title',)
               
class CoursesAdmin(ImportExportModelAdmin):

    list_display = ['id','title','display_subjects_school', 'created']
    list_filter =  ['title']
    search_fields = ['title']
    ordering = ['id']
    
    resource_class = CoursesResource
    def display_subjects_school(self, obj):
        return ", ".join([str(course) for course in obj.schools.all()])

    display_subjects_school.short_description = 'School'

admin.site.register(Courses, CoursesAdmin)



# class blogcommentResource(resources.ModelResource):
    
#     class Meta:
#         model = Blogcomment
#         # fields = ('title',)
               
# class blogcommentAdmin(ImportExportModelAdmin):
#     list_display = ['id','post','name' ,'content']
#      # prepopulated_fields = {"slug": ("title",)}
#     list_filter =  ['post','created','name']
#     search_fields= ['post','name']
#     ordering = ['id']
    
#     resource_class = blogcommentResource

# admin.site.register(Blogcomment, blogcommentAdmin)
    

# class TopicsResource(resources.ModelResource):
    
#     courses = fields.Field(
#         column_name= 'courses',
#         attribute='courses',
#         widget=ForeignKeyWidget(Courses,'title') )
    
#     class Meta:
#         model = Topics
#         # fields = ('title',)

# class TopicsAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'categories', 'courses','title', 'desc', 'img_topic', 'video', 'topics_url', 'created', 'updated']
#     prepopulated_fields = {"slug": ("title",)}
#     list_filter = ['categories', 'courses', 'created']
#     search_fields = ['id', 'title', 'created', 'categories__name', 'courses__title']  # Use double underscore for related fields
#     ordering = ['id']
#     resource_class = TopicsResource

# admin.site.register(Topics, TopicsAdmin)



# class AlertAdmin(ImportExportModelAdmin):
#     list_display = ['id','title','content','created']

#     list_filter =  ['title','content','created']
#     search_fields= ['id','title','content','created']
#     ordering = ['id']

# admin.site.register(Alert, AlertAdmin)