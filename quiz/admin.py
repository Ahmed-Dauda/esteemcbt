
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
from .models import CourseGrade
from quiz.forms import CourseGradeForm
from django.contrib import admin
from quiz.models import StudentAnswer

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('result', 'question', 'selected_answer', 'is_correct', 'submitted_at')
    list_filter = ('is_correct', 'submitted_at')
    search_fields = ('result__student__user__email', 'question__question')
    
    def get_queryset(self, request):
        # Use select_related to avoid N+1 issues
        qs = super().get_queryset(request)
        return qs.select_related('result__student__user', 'question')
    
  
class SchoolAdmin(admin.ModelAdmin):

    list_display = ['school_name','course_pay','customer','created', 'updated']
    search_fields = ['course_pay', 'schools__name']  # Add search field for course name

admin.site.register(School, SchoolAdmin)

from quiz.models import CourseGrade, Course

@admin.action(description="Delete unused Placeholder Title courses")
def delete_unused_placeholder_courses(modeladmin, request, queryset):
    placeholder_courses = Course.objects.filter(course_name="Placeholder Title")

    deleted_count = 0
    for course in placeholder_courses:
        if not course.course_grade.exists():  # Use reverse relation
            course.delete()
            deleted_count += 1

    modeladmin.message_user(request, f"Deleted {deleted_count} unused Placeholder Title course(s).")


class CourseAdmin(admin.ModelAdmin):    
    list_display = ['get_school_name', 'show_questions', 'course_name', 'session','term','exam_type','question_number', 'total_marks', 'num_attemps', 'duration_minutes', 'created']
    search_fields = ['course_name__title', 'schools__school_name','term__name', 'exam_type__name']  # Add search field for course name and school name
    autocomplete_fields = ['schools']
    actions = [delete_unused_placeholder_courses]
    
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('schools', 'course_name')

    def get_school_name(self, obj):
        return obj.schools.school_name if obj.schools else "Enable Exam"
    get_school_name.short_description = 'School Name'

admin.site.register(Course, CourseAdmin)


#real codes

class CourseGradeAdmin(admin.ModelAdmin):
    form = CourseGradeForm  # ✅ This must be a ModelForm
    list_display = ['name', 'schools', 'get_students_details', 'get_subject_names', 'is_active']
    search_fields = ['name', 'schools__school_name', 'students__email', 'students__first_name', 'students__last_name']
    list_filter = ['schools', 'is_active', 'subjects']
    
    # filter_horizontal = ('students', 'subjects')
    autocomplete_fields = ['students', 'subjects']

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


# class CourseGradeAdmin(admin.ModelAdmin):
#     form = CourseGradeForm
#     autocomplete_fields = ['students', 'subjects']
#     list_display = ['name', 'schools', 'get_students_details', 'get_subject_names', 'is_active']
#     search_fields = ['name', 'schools__school_name','students__email', 'students__first_name', 'students__last_name']
#     list_filter = ['schools', 'is_active', 'subjects']
#     filter_horizontal = ('students', 'subjects')

#     def get_students_details(self, obj):
#         return ", ".join([f"{s.first_name} {s.last_name}" for s in obj.students.all()])
#     get_students_details.short_description = "Students"

#     def get_subject_names(self, obj):
#         return ", ".join([s.title for s in obj.subjects.all()])
#     get_subject_names.short_description = "Subjects"

#     class Media:
#         css = {
#             'all': ('sms/css/admin_custom.css',)  # Load the custom CSS file
#         }

#     def get_students_details(self, obj):
#         return '\n'.join(
#             f"({student.school})-({student.first_name}-{student.last_name}, {student.student_class})"
#             for student in obj.students.all()
#         )
#     get_students_details.short_description = 'Student Details'

#     def get_subject_names(self, obj): 
#         return '\n'.join(str(subject) for subject in obj.subjects.all())
#     get_subject_names.short_description = 'Subject Names'

# admin.site.register(CourseGrade, CourseGradeAdmin)


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
             
            'id', 'exam_course_name','result_class', 'session__name', 'term__name', 
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
    list_filter = ['exam', 'student', 'exam_type', 'session', 'term', 'created']
    search_fields = ['student__first_name', 'student__last_name', 'exam__course_name__title', 'created']
    ordering = ['exam__course_name']
 
admin.site.register(Result, ResultAdmin)




# working with options like option 1, option 2, etc. 

class QuestionResource(resources.ModelResource):
    course = fields.Field(
        column_name='course',
        attribute='course',
        widget=ForeignKeyWidget(Course, 'course_name__title')  # Adjust field if needed
    )

    def normalize(self, text):
        """Lowercase and remove all spaces from the string."""
        return ''.join(text.lower().split()) if isinstance(text, str) else ''

    def before_import_row(self, row, **kwargs):
        answer_raw = row.get('answer', '')
        answer_text = self.normalize(answer_raw)

        # Normalize all options
        option_map = {
            'Option1': self.normalize(row.get('option1', '')),
            'Option2': self.normalize(row.get('option2', '')),
            'Option3': self.normalize(row.get('option3', '')),
            'Option4': self.normalize(row.get('option4', '')),
        }

        # Try matching answer to option values
        matched = False
        for opt_key, opt_val in option_map.items():
            if answer_text == opt_val:
                row['answer'] = opt_key
                print(f"✅ Matched answer '{answer_raw}' to {opt_key}")
                matched = True
                break

        # Fallback if answer is already like 'Option1', 'option 1', etc.
        if not matched:
            fallback_map = {
                'option1': 'Option1', 'optionone': 'Option1', 'option 1': 'Option1',
                'option2': 'Option2', 'optiontwo': 'Option2', 'option 2': 'Option2',
                'option3': 'Option3', 'optionthree': 'Option3', 'option 3': 'Option3',
                'option4': 'Option4', 'optionfour': 'Option4', 'option 4': 'Option4',
            }

            if answer_text in fallback_map:
                normalized = fallback_map[answer_text]
                row['answer'] = normalized
                # print(f"🔄 Normalized fallback answer '{answer_raw}' to '{normalized}'")
            else:
                pass
                # print(f"❌ Could not match answer '{answer_raw}' to any option")

    class Meta:
        model = Question
        fields = (
            'course', 'marks', 'question', 'img_quiz',
            'option1', 'option2', 'option3', 'option4',
            'answer', 'created', 'updated', 'id'
        )


class QuestionAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = ['course', 'marks', 'question', 'option1', 'option2', 'option3', 'option4', 'answer']
    list_filter = ['course', 'marks', 'question']
    search_fields = ['course__course_name__title', 'marks', 'question']
    ordering = ['id']
    resource_class = QuestionResource

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')


admin.site.register(Question, QuestionAdmin)


class QuestionResource(resources.ModelResource):
    course = fields.Field(
        column_name='course',
        attribute='course',
        widget=ForeignKeyWidget(Course, 'course_name__title')
    )

    def before_import_row(self, row, **kwargs):
        # Normalize the answer field here before saving
        answer = row.get('answer', '')
        normalized_answer = answer.strip().replace(' ', '').capitalize()
        # If you want to convert 'option1' or 'option 1' => 'Option1'
        # You can do it more explicitly like:
        if answer.lower().replace(' ', '') in ['option1', 'optionone', 'option 1']:
            normalized_answer = 'Option1'
        elif answer.lower().replace(' ', '') in ['option2', 'optiontwo', 'option 2']:
            normalized_answer = 'Option2'
        elif answer.lower().replace(' ', '') in ['option3', 'optionthree', 'option 3']:
            normalized_answer = 'Option3'
        elif answer.lower().replace(' ', '') in ['option4', 'optionfour', 'option 4']:
            normalized_answer = 'Option4'
        else:
            # Default fallback, just capitalize and remove spaces
            normalized_answer = answer.strip().replace(' ', '').capitalize()

        row['answer'] = normalized_answer

        # You can print for debugging:
        print(f"Normalized answer from '{answer}' to '{normalized_answer}'")

    class Meta:
        model = Question
        fields = ('course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer', 'created', 'updated', 'id')

    
# real codes
# class QuestionResource(resources.ModelResource):
#     course = fields.Field(
#         column_name='course',
#         attribute='course',
#         widget=ForeignKeyWidget(Course, 'course_name__title')
#     )

#     class Meta:
#         model = Question
#         fields = ('course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer', 'created', 'updated', 'id')
   
# class QuestionAdmin(ImportExportModelAdmin, ExportActionMixin):
#     list_display = ['course', 'marks', 'question','option1','option2','option3','option4' ,'answer']
#     list_filter = ['course', 'marks', 'question']  
#     search_fields = ['course__course_name__title', 'marks', 'question']
#     ordering = ['id']  
#     resource_class = QuestionResource   

#     def get_queryset(self, request):
#         queryset = super().get_queryset(request)
#         queryset = queryset.select_related('course')
#         return queryset
    
# admin.site.register(Question, QuestionAdmin)




