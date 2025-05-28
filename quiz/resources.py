from import_export import resources, fields
from import_export.widgets import ManyToManyWidget
from .models import CourseGrade, Course

class CourseGradeResource(resources.ModelResource):
    subjects = fields.Field(
        column_name='subjects',
        attribute='subjects',
        widget=ManyToManyWidget(Course, field='id')  # You can use 'id' or 'course_name__title' for better readability
    )

    class Meta:
        model = CourseGrade
        fields = ('id', 'name', 'subjects', 'is_active')
