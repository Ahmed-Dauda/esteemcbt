
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
from users.models import Profile
from quiz.models import (Question, Course, Result,School)
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from .models import Question, Course, Session, Term, ExamType  # Import required models
from import_export.fields import Field
from django.db.models import Prefetch


class SchoolAdmin(admin.ModelAdmin):

    list_display = ['school_name','course_pay','customer','created', 'updated']
    search_fields = ['course_pay', 'schools__name']  # Add search field for course name

admin.site.register(School, SchoolAdmin)



class CourseAdmin(admin.ModelAdmin):    
    list_display = ['get_school_name', 'show_questions', 'course_name', 'session','term','exam_type','question_number', 'total_marks', 'num_attemps', 'duration_minutes', 'created']
    search_fields = ['course_name__title', 'schools__school_name','term__name', 'exam_type__name']  # Add search field for course name and school name

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('schools', 'course_name')

    def get_school_name(self, obj):
        return obj.schools.school_name if obj.schools else "Enable Exam"
    get_school_name.short_description = 'School Name'

admin.site.register(Course, CourseAdmin)



from .models import CourseGrade
from quiz.forms import CourseGradeForm

class CourseGradeAdmin(admin.ModelAdmin):
    form = CourseGradeForm
    list_display = ['name','schools', 'get_students_details', 'get_subject_names']
    search_fields = ['name', 'students__email', 'subjects__name']

    class Media:
        css = {
            'all': ('sms/css/admin_custom.css',)  # Load the custom CSS file
        }

    def get_students_details(self, obj):
        return '\n'.join(
            f"({student.school})-({student.first_name}-{student.last_name}, {student.student_class})"
            for student in obj.students.all()
        )
    get_students_details.short_description = 'Student Details'

    def get_subject_names(self, obj): 
        return '\n'.join(str(subject) for subject in obj.subjects.all())
    get_subject_names.short_description = 'Subject Names'

admin.site.register(CourseGrade, CourseGradeAdmin)


# ResultResource
from .models import Result, Course, Profile, ExamType
from import_export import resources, fields, widgets  # Importing widgets


class ResultResource(resources.ModelResource):
    exam__course_name = fields.Field(
        column_name='exam_course_name',
        attribute='exam__course_name__title',
    )
       
    student_username = fields.Field(
        column_name='student_username',
        attribute='student__user__username',
    )

    student_first_name = fields.Field(
        column_name='student_first_name',
        attribute='student__first_name',
    )

    student_last_name = fields.Field(
        column_name='student_last_name',
        attribute='student__last_name',
    )
    
    class Meta:
        model = Result
        # fields = (
        #     'exam', 'student_username', 'marks', 
        #     'result_class', 'session', 'term', 'exam_type', 
        #     'created', 'id')
        # export_order = ('exam_course_name', 'student_username', 'marks', 'result_class', 'session', 'term', 'exam_type', 'created', 'id')
        
        fields = (
             
            'id', 'exam_course_name', 'result_class', 'session__name', 'term__name', 
            'exam_type__name', 'student_username', 'student_first_name', 
            'student_last_name', 'marks', 'created'
        )
        export_order = (
            'exam__course_name',
            'student_username',
            'student_first_name',  # First name of the student
            'student_last_name',  # Last name of the student
             'marks',  # Marks or score
            'result_class',  # Class associated with the result
            'session__name',  # Session name
            'term__name',  # Term name
            'exam_type__name',  # Exam type name
           
            'created',  # Created timestamp
            'id',  # The unique ID of the result (optional to be at the end)
        )
        


class ResultAdmin(ImportExportModelAdmin, ExportActionMixin):    
    resource_class = ResultResource
    list_display = ['student', 'exam','schools', 'marks', 'exam_type', 'result_class', 'session', 'term', 'created']
    list_filter = ['exam', 'student', 'exam_type', 'session', 'term']
    search_fields = ['student__first_name', 'student__last_name', 'exam__course_name__title', 'created']
    ordering = ['id']

admin.site.register(Result, ResultAdmin)



# real codes

class QuestionResource(resources.ModelResource):
    course = fields.Field(
        column_name='course',
        attribute='course',
        widget=ForeignKeyWidget(Course, 'course_name__title')
    )

    class Meta:
        model = Question
        fields = ('course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer', 'created', 'updated', 'id')
   
class QuestionAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = ['course', 'marks', 'question','option1','option2','option3','option4' ,'answer']
    list_filter = ['course', 'marks', 'question']  
    search_fields = ['course__course_name__title', 'marks', 'question']
    ordering = ['id']  
    resource_class = QuestionResource   

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('course')
        return queryset
    
admin.site.register(Question, QuestionAdmin)




