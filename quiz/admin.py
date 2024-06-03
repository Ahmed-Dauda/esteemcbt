import profile
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields,resources
from import_export.widgets import ForeignKeyWidget
from users.models import Profile
from quiz.models import (
    Question, Course, Result,School,
     
   
    )
# Register your models here.

# admin.site.register(Course)
# admin.site.register(Group)
# admin.site.register(List_Subjects)
# admin.site.register(Subjects)
# admin.site.register(School)
# admin.site.register(TopicsAssessment)
# admin.site.register(QuestionAssessment)

class SchoolAdmin(admin.ModelAdmin):

    list_display = ['school_name','course_pay','customer','created', 'updated']
    search_fields = ['course_pay', 'schools__name']  # Add search field for course name

admin.site.register(School, SchoolAdmin)

from django.contrib import admin

class CourseAdmin(admin.ModelAdmin):
    list_display = ['get_school_name', 'show_questions', 'course_name', 'question_number', 'total_marks', 'num_attemps', 'duration_minutes','created']
    search_fields = ['course_name', 'schools__name']  # Add search field for course name

    def get_school_name(self, obj):
        return obj.schools.school_name if obj.schools else "Unknown School"
    get_school_name.short_description = 'School Name'

admin.site.register(Course, CourseAdmin)

# class CourseAdmin(admin.ModelAdmin):
#     list_display = ['get_school_name', 'show_questions','course_name', 'question_number', 'total_marks', 'pass_mark', 'duration_minutes', 'created', 'updated']
#     search_fields = ['course_name', 'schools__name']  # Add search field for course name

#     def get_school_name(self, obj):
#         return obj.schools.school_name if obj.schools else "Unknown School"
#     get_school_name.short_description = 'School Name'

# admin.site.register(Course, CourseAdmin)


from .models import CourseGrade

class CourseGradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_students_emails', 'get_subject_names']
    search_fields = ['name', 'students__email', 'subjects__name']

    def get_students_emails(self, obj):
        return '\n'.join(str(student.email) for student in obj.students.all())
    get_students_emails.short_description = 'Student Emails'

    def get_subject_names(self, obj):
        return '\n'.join(str(subject) for subject in obj.subjects.all())
    get_subject_names.short_description = 'Subject Names'

admin.site.register(CourseGrade, CourseGradeAdmin)

# class CourseGradeAdmin(admin.ModelAdmin):
#     list_display = ['name','email', 'get_subject_names']
#     search_fields = ['name', 'subjects__name']

#     def get_subject_names(self, obj):
#         return '\n'.join(str(subject) for subject in obj.subjects.all())
#     get_subject_names.short_description = 'Subject Names'

# admin.site.register(CourseGrade, CourseGradeAdmin)

# def promote_students(modeladmin, request, queryset):
#     # Assuming queryset contains students to be promoted
#     print("Queryset:", queryset)  # Print the queryset to check its contents
#     for student in queryset:
#         print("Promoting student:", student.name)  # Print the name of each student being promoted
#         student.promote_to_next_grade()  # You need to define this method in your Student model
#         print("Student promoted successfully.")  # Print a message after promoting each student

# promote_students.short_description = "Promote selected students"




# class SubjectsAdmin(admin.ModelAdmin):
#     list_display = ['get_school_name', 'get_course_names', 'question_number', 'total_marks', 'pass_mark', 'duration_minutes', 'created', 'updated']
#     search_fields = ['course_name__name']  # Add search field for course name

#     def get_school_name(self, obj):
#         return obj.schools.school_name if obj.schools else "Unknown School"
#     get_school_name.short_description = 'School Name'

#     def get_course_names(self, obj):
#         if obj.course_name:
#             return obj.course_name.name
#         else:
#             return "No course assigned"
#     get_course_names.short_description = 'Course Names'

# admin.site.register(Subjects, SubjectsAdmin)


# class SubjectsAdmin(admin.ModelAdmin):
#     list_display = ['get_school_name', 'get_course_names', 'question_number', 'total_marks', 'pass_mark', 'duration_minutes', 'created', 'updated']
    
#     def get_school_name(self, obj):
#         return obj.schools.school_name if obj.schools else "Unknown School"
#     get_school_name.short_description = 'School Name'

#     def get_course_names(self, obj):
#         return '\n'.join(str(course) for course in obj.course_name.all())
#     get_course_names.short_description = 'Course Names'

# admin.site.register(Subjects, SubjectsAdmin)


# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display = ['name', 'email', 'group', 'school']   # Include 'name' field in the list display
#     search_fields = ['name', 'email', 'group__name', 'school__school_name'] 

#     # Optionally, customize the admin change form to display additional information or controls
#     def change_view(self, request, object_id, form_url='', extra_context=None):
#         extra_context = extra_context or {}
#         # Add additional context variables here if needed
#         return super().change_view(request, object_id, form_url, extra_context=extra_context)
    

# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display = ('name', 'grade')

# admin.site.register(Group)

# from django.contrib import admin


# class GroupAdmin(admin.ModelAdmin):
#     list_display = ['name', 'display_subjects']  # Define fields to display in the list

#     def display_subjects(self, obj):
#         """
#         Custom method to display subjects associated with the group.
#         """
#         subject_names = '\n'.join(str(subject) for subject in obj.subjects.all())
#         return subject_names if subject_names else "-"  # Return subject names or "-" if no subjects

#     display_subjects.short_description = 'Subjects'  # Set column header

# admin.site.register(Group, GroupAdmin)


# subjectQUESTION
# class QuestionSubjectResource(resources.ModelResource):
    
#     course = fields.Field(
#         column_name= 'course',
#         attribute='course',
#         widget=ForeignKeyWidget(Course, field='course_name__title'))
    
#     class Meta:
#         model = Subject_Question
#         # fields = ('title',)
               
# class SubjectQuestionAdmin(ImportExportModelAdmin):
#     list_display = ['id','course','marks' ,'question']
#     # prepopulated_fields = {"slug": ("title",)}
#     list_filter =  ['course','marks' ,'question']
#     search_fields= ['id','course__course_name__title','marks' ,'question']
#     ordering = ['id']
    
#     resource_class = QuestionSubjectResource

# admin.site.register(Subject_Question, SubjectQuestionAdmin)

# END subjectQUESTION


# QuestionAssessment

# class QuestionAssessmentResource(resources.ModelResource):
    
#     course = fields.Field(
#         column_name= 'course',
#         attribute='course',
#         widget=ForeignKeyWidget(Course, field='course_name__title'))
    
#     class Meta:
#         model = QuestionAssessment
#         # fields = ('title',)
               
# class QuestionAssessmentAdmin(ImportExportModelAdmin):
#     list_display = ['id','course','marks' ,'question']
#     # prepopulated_fields = {"slug": ("title",)}
#     list_filter =  ['course','marks' ,'question']
#     search_fields= ['id','course__course_name__title','marks' ,'question']
#     ordering = ['id']
    
#     resource_class = QuestionAssessmentResource

# admin.site.register(QuestionAssessment, QuestionAssessmentAdmin)

# ENDQUESTIONASSESSMENT

# ResultAssessment

# class ResultAssessmentResource(resources.ModelResource):
    
#     courses = fields.Field(
#         column_name= 'student',
#         attribute='student',
#         widget=ForeignKeyWidget(Profile,'username') )
    
#     class Meta:
#         model = Result
#         # fields = ('title',)
  
# class ResultAssessmentAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'student', 'exam', 'marks', 'created']
#     list_filter = ['id', 'student', 'exam', 'marks']
#     search_fields = ['id', 'student__first_name', 'student__last_name', 'exam__course_name__title', 'marks', 'created']
#     ordering = ['id']
#     resource_class = ResultAssessmentResource

# admin.site.register(ResultAssessment, ResultAssessmentAdmin)

# end of ResultAssessment


# SubjectResultResource
# class SubjectResultResource(resources.ModelResource):
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
#         model = Subject_Result
#         fields = ('id', 'exam_course_name', 'student_username', 'student_first_name', 'student_last_name', 'marks', 'created')

               
# class SubjectResultAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'student', 'exam', 'marks', 'created']
#     list_filter = ['id', 'student', 'exam', 'marks']
#     search_fields = ['student__first_name', 'student__last_name', 'exam__course_name__title', 'marks', 'created']
#     ordering = ['id']
#     resource_class = SubjectResultResource

# admin.site.register(Subject_Result, SubjectResultAdmin)

# end of SubjectResultResource

# ResultResource
class ResultResource(resources.ModelResource):
    exam_course_name = fields.Field(
        column_name='exam',
        attribute='exam__course_name__title'  
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
        fields = ('id', 'exam_course_name', 'student_username', 'student_first_name', 'student_last_name', 'marks', 'created')

               
class ResultAdmin(ImportExportModelAdmin):
    list_display = ['id', 'student', 'exam', 'marks', 'created']
    list_filter = ['exam', 'student']
    search_fields = ['student__first_name', 'student__last_name', 'exam__course_name__title', 'marks', 'created']
    ordering = ['id']
    resource_class = ResultResource

admin.site.register(Result, ResultAdmin)

# end of ResultResource
 

# class CertificateResource(resources.ModelResource):
    
#     # course = fields.Field(
#     #     column_name= 'course',
#     #     attribute='course',
#     #     widget=ForeignKeyWidget(Course,'course_name') )
    
#     class Meta:
#         model = Certificate_note
#         # fields = ('title',)
               
# class CertificateAdmin(ImportExportModelAdmin):
#     list_display = ['id','note']
    
#     list_filter =  ['note']
#     search_fields= ['note']
#     ordering = ['id']
    
#     resource_class = CertificateResource

# admin.site.register(Certificate_note, CertificateAdmin)


class QuestionResource(resources.ModelResource):
    
    course = fields.Field(
        column_name= 'course',
        attribute='course',
        widget=ForeignKeyWidget(Course, field='course_name__title'))
    
    class Meta:
        model = Question
        fields = ('course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer', 'created', 'updated', 'id')
       
class QuestionAdmin(ImportExportModelAdmin):
    list_display = ['id','course','marks' ,'question', 'answer']
    # prepopulated_fields = {"slug": ("title",)}
    list_filter =  ['course','marks' ,'question']
    search_fields= ['course__course_name__title','marks' ,'question']
    ordering = ['id']
    
    resource_class = QuestionResource

admin.site.register(Question, QuestionAdmin)



