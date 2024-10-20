
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
from users.models import Profile
from quiz.models import (Question, Course, Result,School)
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from .models import Question, Course, Session, Term, ExamType  # Import required models
from import_export.fields import Field


class SchoolAdmin(admin.ModelAdmin):

    list_display = ['school_name','course_pay','customer','created', 'updated']
    search_fields = ['course_pay', 'schools__name']  # Add search field for course name

admin.site.register(School, SchoolAdmin)

from django.contrib import admin

from django.db.models import Prefetch

class CourseAdmin(admin.ModelAdmin):
    list_display = ['get_school_name', 'show_questions', 'course_name', 'session','term','exam_type','question_number', 'total_marks', 'num_attemps', 'duration_minutes', 'created']
    search_fields = ['course_name__title', 'schools__school_name', 'exam_type__name']  # Add search field for course name and school name

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
    exam_course_name = fields.Field(
        column_name='exam_course_name',
        attribute='exam__course_name',
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
        fields = (
            'exam', 'student_username', 'marks', 
            'result_class', 'session', 'term', 'exam_type', 
            'created', 'id')
        export_order = ('exam_course_name', 'student_username', 'marks', 'result_class', 'session', 'term', 'exam_type', 'created', 'id')
        
        # fields = (
        #     'id', 'exam', 'result_class', 'session', 'term', 
        #     'exam_type', 'student_username', 'student_first_name', 
        #     'student_last_name', 'marks', 'created'
        # )
        


class ResultAdmin(ImportExportModelAdmin):    
    resource_class = ResultResource
    list_display = ['student', 'exam', 'marks', 'exam_type', 'result_class', 'session', 'term', 'created']
    list_filter = ['exam', 'student', 'exam_type', 'session', 'term']
    search_fields = ['student__first_name', 'student__last_name', 'exam__course_name__title', 'marks']
    ordering = ['id']

admin.site.register(Result, ResultAdmin)

# # ResultResource
# class ResultResource(resources.ModelResource):
#     exam_course_name = fields.Field(
#         column_name='exam',
#         attribute='exam__course_name__title'  
#     )
    
#     student_username = fields.Field(
#         column_name='student_username',
#         attribute='student__user__username',
#     )

#     student_first_name = fields.Field(
#         column_name='student_first_name',
#         attribute='student__first_name',
#     )

#     student_last_name = fields.Field(
#         column_name='student_last_name',
#         attribute='student__last_name',
#     )
    
#     class Meta:
#         model = Result
#         fields = ('id', 'exam_course_name','result_class','session','term','exam_type_name', 'student_username', 'student_first_name', 'student_last_name', 'marks', 'created')

               
# class ResultAdmin(ImportExportModelAdmin):    
#     list_display = ['student', 'exam', 'marks','exam_type', 'result_class', 'session', 'term', 'created']
#     list_filter = ['exam', 'student', 'exam_type']
#     search_fields = ['student__first_name', 'student__last_name', 'exam__course_name__title', 'marks', 'exam_type__name', 'created']
#     ordering = ['id']
#     resource_class = ResultResource

# admin.site.register(Result, ResultAdmin)


# end of ResultResource


# from import_export import resources, fields
# from import_export.widgets import ForeignKeyWidget
# from .models import Question, Course, School, Session, Term, ExamType

# class CustomCourseWidget(ForeignKeyWidget):
#     def clean(self, value, row=None, **kwargs):
#         if 'course' in row and 'session' in row and 'exam_type' in row and 'schools' in row:
#             # Fetch courses that match the course name, session, exam_type, and school
#             courses = self.model.objects.filter(
#                 course_name__title=row['course'],
#                 session__name=row['session'],
#                 exam_type__name=row['exam_type'],
#                 schools__name=row['schools']  # Include school in the filter
#             )

#             if courses.count() == 1:
#                 return courses.first()  # Only one match found
#             elif courses.count() > 1:
#                 # Handle multiple matches
#                 raise ValueError(f"Multiple courses found for course: {row['course']}, session: {row['session']}, exam type: {row['exam_type']}, and school: {row['schools']}. Please ensure uniqueness.")
#             else:
#                 raise ValueError(f"No course found for course: {row['course']}, session: {row['session']}, exam type: {row['exam_type']}, and school: {row['schools']}.")

#         return None  # Handle case when row does not contain expected data


# class QuestionResource(resources.ModelResource):
#     # Exporting the `course` field with the custom widget
#     course = fields.Field(
#         column_name='course',
#         attribute='course',
#         widget=CustomCourseWidget(Course, 'course_name__title')  # Adjust according to your Course model
#     )

#     # Exporting `schools` (Many-to-Many) as comma-separated school names
#     schools = fields.Field(
#         column_name='schools',
#         attribute='schools',
#         widget=ManyToManyWidget(School, separator=', ', field='school_name')
#     )

#     # Exporting `session`, `term`, and `exam_type` as Foreign Keys
#     session = fields.Field(
#         column_name='session',
#         attribute='session',
#         widget=ForeignKeyWidget(Session, 'name')  # Assuming 'name' is the field you want to display for session
#     )

#     term = fields.Field(
#         column_name='term',
#         attribute='term',
#         widget=ForeignKeyWidget(Term, 'name')  # Assuming 'name' is the field you want to display for term
#     )

#     exam_type = fields.Field(
#         column_name='exam_type',
#         attribute='exam_type',
#         widget=ForeignKeyWidget(ExamType, 'name')  # Assuming 'name' is the field you want to display for exam_type
#     )

#     class Meta:
#         model = Question
#         fields = (
#             'course', 'schools', 'session', 'term', 'exam_type', 
#             'marks', 'question', 'img_quiz', 'option1', 'option2', 
#             'option3', 'option4', 'answer', 'created', 'updated', 'id'
#         )

#     def dehydrate_schools(self, question):
#         return ', '.join([school.school_name for school in question.schools.all()])


# class QuestionAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'course', 'schools_list', 'session', 'term', 'exam_type', 'marks', 'question', 'answer']
#     list_filter = ['course', 'schools', 'session', 'term', 'exam_type', 'marks', 'question']
#     search_fields = ['course__course_name__title', 'schools__name', 'session__name', 'term__name', 'exam_type__name', 'marks', 'question']
#     ordering = ['id']
#     resource_class = QuestionResource

#     def get_queryset(self, request):
#         queryset = super().get_queryset(request)
#         queryset = queryset.select_related('course', 'session', 'term', 'exam_type').prefetch_related('schools')
#         return queryset

#     def schools_list(self, obj):
#         return ", ".join([school.school_name for school in obj.schools.all()])

#     schools_list.short_description = 'Schools'

# admin.site.register(Question, QuestionAdmin)


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
   
class QuestionAdmin(ImportExportModelAdmin):
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


# class QuestionResource(resources.ModelResource):
    
#     course = fields.Field(
#         column_name= 'course',
#         attribute='course',
#         widget=ForeignKeyWidget(Course, field='course_name__title'))
    
#     class Meta:
#         model = Question
#         fields = ('course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer', 'created', 'updated', 'id')

# class QuestionAdmin(ImportExportModelAdmin):
#     list_display = ['id','course','marks' ,'question', 'answer']
#     # prepopulated_fields = {"slug": ("title",)}
#     list_filter =  ['course','marks' ,'question']
#     search_fields= ['course__course_name__title','marks' ,'question']
#     ordering = ['id']
    
#     resource_class = QuestionResource

# admin.site.register(Question, QuestionAdmin)



