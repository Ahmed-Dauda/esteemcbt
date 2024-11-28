from django.contrib import admin
from .models import ConductCategory, StudentConduct

@admin.register(ConductCategory)
class ConductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(StudentConduct)
class StudentConductAdmin(admin.ModelAdmin):
    autocomplete_fields = ['student']
    list_display = ('student', 'school', 'student_class', 'session', 'term', 'category', 'date', 'score', 'conduct_count')
    list_filter = ('school', 'student_class', 'session', 'term', 'category', 'date')
    search_fields = ('student__first_name', 'student__last_name', 'category__name')
    readonly_fields = ['date']
    
    def conduct_count(self, obj):
        """Display the count of conduct records for the student in the same session and term."""
        return obj.get_conduct_count()
    conduct_count.short_description = 'Conduct Count'

