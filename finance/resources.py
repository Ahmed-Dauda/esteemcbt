from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.contrib.auth import get_user_model

from .models import FinanceRecord, Session, Term
from quiz.models import School

User = get_user_model()


# ----------------------------------------------------------------------
# Widget that scopes the lookup by the row's "school" value
# ----------------------------------------------------------------------
class SchoolScopedFKWidget(ForeignKeyWidget):
    """
    ForeignKeyWidget that adds a filter on `school__school_name`
    using the value already present in the row.
    """
    def get_queryset(self, value, row, *args, **kwargs):
        qs = super().get_queryset(value, row, *args, **kwargs)
        school_name = row.get('school')
        if school_name:
            qs = qs.filter(school__school_name=school_name)
        return qs


class FinanceRecordResource(resources.ModelResource):
    student = fields.Field(
        column_name='student',
        attribute='student',
        widget=ForeignKeyWidget(User, field='admission_no'),
    )
    school = fields.Field(
        column_name='school',
        attribute='school',
        widget=ForeignKeyWidget(School, field='school_name'),
    )
    session = fields.Field(
        column_name='session',
        attribute='session',
        widget=SchoolScopedFKWidget(Session, field='name'),   # 👈 scoped
    )
    term = fields.Field(
        column_name='term',
        attribute='term',
        widget=SchoolScopedFKWidget(Term, field='name'),      # 👈 scoped
    )
    week_start = fields.Field(
        column_name='week_start',
        attribute='week_start',
        widget=DateWidget(format='%Y-%m-%d'),
    )

    class Meta:
        model = FinanceRecord
        fields = (
            'sn',
            'student',
            'names',
            'student_class',
            'school',
            'session',
            'term',
            'week_start',
            'initial_total_deposit',
            'school_shop',
            'caps',
            'haircut',
            'others',
            'note',
            'total_deposit',
            'total_expense',
            'balance_brought_forward',
            'current_balance',
            'status',
        )
        export_order = fields
        import_id_fields = ('sn',)
        skip_unchanged = True
        report_skipped = False
  
    # ------------------------------------------------------------------
    # Turn off the save() cascade for the whole import — huge speedup
    # ------------------------------------------------------------------
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        FinanceRecord._skip_cascade = True

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        FinanceRecord._skip_cascade = False

    def before_import_row(self, row, **kwargs):
        """Set school from the logged-in user, so the scoped widget can find terms."""
        request = kwargs.get('request')
        if request and getattr(request.user, 'school', None):
            row['school'] = str(request.user.school)

    def before_save_instance(self, instance, using_transactions, dry_run):
        """Auto-fill names + student_class from the student."""
        if instance.student:
            if not instance.names:
                instance.names = (
                    f"{instance.student.first_name or ''} "
                    f"{instance.student.last_name or ''}"
                ).strip()
            if not instance.student_class or instance.student_class == 'NA':
                instance.student_class = instance.student.student_class or 'NA'