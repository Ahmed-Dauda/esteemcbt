# Register your models here.
from django.contrib import admin
from .models import FinanceRecord
from django.utils.html import format_html
from import_export.widgets import ForeignKeyWidget
from import_export import resources
from .models import FinanceRecord
from import_export import resources, fields

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import FinanceRecord, School, Session, Term

class FinanceRecordResource(resources.ModelResource):
    is_update = fields.Field(readonly=True)  # Tracks if the row is an update or new

    # Fixing ForeignKey fields
    school = fields.Field(
        column_name='school',
        attribute='school',
        widget=ForeignKeyWidget(School, 'school_name')  # Match based on school name
    )
    session = fields.Field(
        column_name='session__name',
        attribute='session',
        widget=ForeignKeyWidget(Session, 'name')  # Match based on session name
    )
    term = fields.Field(
        column_name='term__name',
        attribute='term',
        widget=ForeignKeyWidget(Term, 'name')  # Match based on term name
    )

    class Meta:
        model = FinanceRecord
        fields = [
            'sn', 'names', 'student_class', 'school',  # Use 'school' instead of 'school__school_name'
            'session', 'term',  # Use 'session' and 'term' instead of 'session__name', 'term__name'
            'initial_total_deposit', 'total_deposit',
            'school_shop', 'caps', 'haircut', 'others', 
            'total_expense', 'current_balance', 'balance_brought_forward', 'note', 'status'
        ]
        import_id_fields = ('sn',)
        export_order = fields  # Ensure the order of fields during export

    def before_import_row(self, row, **kwargs):
        """Sets 'is_update' to True if the record exists, otherwise False."""
        try:
            # Check for an existing record with the given 'sn' (serial number)
            FinanceRecord.objects.get(sn=row.get('sn'))
            row['is_update'] = True
        except FinanceRecord.DoesNotExist:
            row['is_update'] = False


# class FinanceRecordResource(resources.ModelResource):
#     is_update = fields.Field(readonly=True)  # Tracks if the row is an update or new

#     class Meta:
#         model = FinanceRecord
#         fields = [
#             'sn', 'names', 'student_class', 'school__school_name',
#             'session__name', 'term__name', 'initial_total_deposit', 'total_deposit',
#             'school_shop', 'caps', 'haircut', 'others', 
#             'total_expense', 'current_balance', 'balance_brought_forward', 'note', 'status'
#         ]
#         import_id_fields = ('sn',)
#         export_order = fields  # Ensure the order of fields during export

#     def before_import_row(self, row, **kwargs):
#         """Sets 'is_update' to True if the record exists, otherwise False."""
#         try:
#             # Check for an existing record with the given 'sn' (serial number)
#             FinanceRecord.objects.get(sn=row.get('sn'))
#             row['is_update'] = True
#         except FinanceRecord.DoesNotExist:
#             row['is_update'] = False


