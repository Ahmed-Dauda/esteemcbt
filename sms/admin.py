from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
  

from sms.models import (
    Categories, Courses, Topics, 
    Comment, Blog, Blogcomment,Alert, Gallery, 
    FrequentlyAskQuestions, Partners, CourseFrequentlyAskQuestions, Skillyouwillgain, 
    # CourseLearnerReviews, 
    Whatyouwilllearn, 
    CareerOpportunities, Whatyouwillbuild, 
    AboutCourseOwner, 
    CourseLearnerReviews,
    CompletedTopics
    )


admin.site.register(Gallery)
admin.site.register(FrequentlyAskQuestions)
admin.site.register(Partners)
admin.site.register(CourseFrequentlyAskQuestions)
admin.site.register(Skillyouwillgain)
admin.site.register(CourseLearnerReviews)
admin.site.register(Whatyouwilllearn)
admin.site.register(CareerOpportunities)
admin.site.register(Whatyouwillbuild)
admin.site.register(CompletedTopics)
admin.site.register(AboutCourseOwner)

# class ArticleAdminResource(resources.ModelResource):
    
#     class Meta:
#         model = Gallery
        # fields = ('title',)



class ArticleAdminResource(resources.ModelResource):
    
    class Meta:
        model = Blog
        # fields = ('title',)
               
class ArticleAdminAdmin(ImportExportModelAdmin):
    
    prepopulated_fields = {"slug": ("title",)}
    list_display = ['id', 'title', 'desc', 'created']
    list_filter =  ['title']
    search_fields = ['author__user','title']
    ordering = ['id']
    
    resource_class = ArticleAdminResource

admin.site.register(Blog, ArticleAdminAdmin)



class FeedbackcommentResource(resources.ModelResource):
    
    class Meta:
        model = Comment
        # fields = ('title',)
               
class FeedbackcommentResourceAdmin(ImportExportModelAdmin):
    list_display = ['id', 'title', 'desc', 'created']
    list_filter =  ['title']
    search_fields= ['title']
    ordering = ['id']
    
    resource_class = FeedbackcommentResource

admin.site.register(Comment, FeedbackcommentResourceAdmin)


class CategoriesResource(resources.ModelResource):
    
    class Meta:
        model = Categories
        # fields = ('title',)
               
class CategoriesAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name', 'desc', 'created']
    list_filter =  ['name']
    search_fields= ['name', 'desc']
    ordering = ['id']
    
    resource_class = CategoriesResource

admin.site.register(Categories, CategoriesAdmin)


class CategoriesResource(resources.ModelResource):
    
    courses = fields.Field(
        column_name= 'categories',
        attribute='categories',
        widget=ForeignKeyWidget(Categories,'name') )
    
    class Meta:
        model = Courses
        prepopulated_fields = {"slug": ("course_name",)}
        # fields = ('title',)
               
class CoursesAdmin(ImportExportModelAdmin):

    list_display = ['id', 'categories','title','display_subjects_school', 'desc', 'created']
    list_filter =  ['categories','title']
    search_fields = ['categories__name','title']
    ordering = ['id']
    
    resource_class = CategoriesResource
    def display_subjects_school(self, obj):
        return ", ".join([str(course) for course in obj.schools.all()])

    display_subjects_school.short_description = 'School'

admin.site.register(Courses, CoursesAdmin)



class blogcommentResource(resources.ModelResource):
    
    class Meta:
        model = Blogcomment
        # fields = ('title',)
               
class blogcommentAdmin(ImportExportModelAdmin):
    list_display = ['id','post','name' ,'content']
     # prepopulated_fields = {"slug": ("title",)}
    list_filter =  ['post','created','name']
    search_fields= ['post','name']
    ordering = ['id']
    
    resource_class = blogcommentResource

admin.site.register(Blogcomment, blogcommentAdmin)
    

class TopicsResource(resources.ModelResource):
    
    courses = fields.Field(
        column_name= 'courses',
        attribute='courses',
        widget=ForeignKeyWidget(Courses,'title') )
    
    class Meta:
        model = Topics
        # fields = ('title',)

class TopicsAdmin(ImportExportModelAdmin):
    list_display = ['id', 'categories', 'courses','title', 'desc', 'img_topic', 'video', 'topics_url', 'created', 'updated']
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ['categories', 'courses', 'created']
    search_fields = ['id', 'title', 'created', 'categories__name', 'courses__title']  # Use double underscore for related fields
    ordering = ['id']
    resource_class = TopicsResource

admin.site.register(Topics, TopicsAdmin)



class AlertAdmin(ImportExportModelAdmin):
    list_display = ['id','title','content','created']

    list_filter =  ['title','content','created']
    search_fields= ['id','title','content','created']
    ordering = ['id']

admin.site.register(Alert, AlertAdmin)