# Register your models here.
from django.contrib import admin
from .models import FinanceRecord
from django.utils.html import format_html

from import_export import resources
from .models import FinanceRecord
from import_export import resources, fields


            
# class FinanceRecordResource(resources.ModelResource):
#     is_update = fields.Field(attribute='is_update', readonly=True)

#     class Meta:
#         model = FinanceRecord
#         fields = [
#             'sn', 'names', 'student_class', 'initial_total_deposit', 'total_deposit', 'school__name', 
#             'session__name', 'term__name', 'school_shop', 'caps', 'haircut', 'others', 
#             'total_expense', 'current_balance', 'balance_brought_forward', 'note', 'status', 'is_update'
#         ]
#         import_id_fields = ('sn',)
    
#     def before_import_row(self, row, **kwargs):
#         """Check if the record exists in the database."""
#         try:
#             # Check if a record with the given sn exists
#             existing_record = FinanceRecord.objects.get(sn=row['sn'])
#             row['is_update'] = True
#         except FinanceRecord.DoesNotExist:
#             row['is_update'] = False


# class FinanceRecordResource(resources.ModelResource):
#     class Meta:
#         model = FinanceRecord
#         fields = [
#             'sn', 'names', 'student_class', 'initial_total_deposit', 'total_deposit', 'school__name', 
#             'session__name', 'term__name', 'school_shop', 'caps', 'haircut', 'others', 
#             'total_expense', 'current_balance', 'balance_brought_forward', 'note', 'status'
#         ]
#         import_id_fields = ('sn',)

# end of FinanceRecordResource


class FinanceRecordAdmin(admin.ModelAdmin):  
    list_display = ('names','student_class','session','term', 'school','initial_total_deposit','total_deposit','school_shop','caps','haircut','others', 'total_expense', 'current_balance','balance_brought_forward','get_status_color')
  
    def get_status_color(self, obj):
        # Using format_html to safely render HTML
        if obj.status == 'exhausted':
            return format_html('<span style="color: red;">{}</span>', obj.status.capitalize())
        return format_html('<span style="color: green;">{}</span>', obj.status.capitalize())

    # Optional: Customizing filtering and searching
    list_filter = ('status',)
    search_fields = ('names',)

admin.site.register(FinanceRecord, FinanceRecordAdmin)

