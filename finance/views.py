# Create your views here.
from .models import FinanceRecord, School, Session, Term
import tablib
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import FinanceRecord
# from .admin import FinanceRecordResource
from tablib import Dataset
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView, DeleteView,CreateView
from .models import FinanceRecord
# finance/views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from tablib import Dataset
from finance.resources import FinanceRecordResource
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required

from .forms import UploadFileForm

@login_required(login_url='teacher:teacher_login')
def finance_record_export_view(request):
    resource = FinanceRecordResource()
    dataset = resource.export()
    response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="finance_records.xlsx"'
    return response


@login_required(login_url='teacher:teacher_login')
def finance_record_import_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            finance_record_resource = FinanceRecordResource()
            dataset = tablib.Dataset()
            new_records = request.FILES['file'].read()
            dataset.load(new_records, format='xlsx')
                
            # Dry-run the import to check for errors
            result = finance_record_resource.import_data(dataset, dry_run=True)
            if not result.has_errors():
                # Perform the actual import
                finance_record_resource.import_data(dataset, dry_run=False)
                return redirect('finance:finance_record_view')  # Update to your list view URL
            else:
                # Handle errors if any
                errors = result.row_errors()
                return render(request, 'finance/import_records.html', {
                    'form': form, 'errors': errors
                })
    else:
        form = UploadFileForm()
    return render(request, 'finance/import_records.html', {'form': form})
  
 


# def finance_record_import_preview(request):
#     if request.method == "POST":
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = form.cleaned_data['file']
#             dataset = Dataset()
#             imported_data = dataset.load(file.read(), format='xlsx')

#             resource = FinanceRecordResource()
#             preview_data = []
#             for row in imported_data.dict:
#                 resource.before_import_row(row)  # Add 'is_update' field to each row
#                 preview_data.append(row)

#             # Store dataset in session to use in confirm view
#             request.session['import_data'] = preview_data

#             return render(request, 'finance/finance_record_import_preview.html', {
#                 'data': preview_data,
#                 'form': form,
#             })
#     else:
#         form = UploadFileForm()
#     return render(request, 'finance/finance_record_import_preview.html', {'form': form})

# def confirm_import(request):
#     if 'import_data' in request.session:
#         import_data = request.session['import_data']

#         resource = FinanceRecordResource()
#         dataset = Dataset(headers=[field.column_name for field in resource.get_fields()])
#         for row in import_data:
#             dataset.append(row)

#         result = resource.import_data(dataset, dry_run=False)  # Perform actual import

#         # Clear session data after import
#         del request.session['import_data'] 

#         return redirect(reverse_lazy('finance:finance_record_view'))
#     else:
#         return redirect(reverse_lazy('finance:finance_record_import_preview'))
    
  
from teacher.models import Teacher

@login_required(login_url='teacher:teacher_login')
def finance_record_view(request):
    # Get the current user's school for filtering
    # username = request.user.username
    user_school = request.user.school

    # teacher = Teacher.objects.select_related('user', 'school').prefetch_related('subjects_taught', 'classes_taught').get(username=username)
    # teacher_school = teacher.school
    

    # Prefetch related data to reduce database hits
    schools = School.objects.filter(id=user_school.id)
    sessions = Session.objects.all()
    terms = Term.objects.all()
    
    # Retrieve filter parameters from the request
    school_filter = request.GET.get('school')
    session_filter = request.GET.get('session')
    term_filter = request.GET.get('term')

    # Base queryset filtered by the user's school
    records = FinanceRecord.objects.filter(school=user_school).select_related('school', 'session', 'term')
    
    # Apply additional filters based on user input  
    finance_school = FinanceRecord.objects.filter(school_id=user_school.id).values_list('school__school_name', flat=True).first()
    # print(finance_school, 'sc')

 
    if school_filter:
        records = records.filter(school_id=school_filter)
    if session_filter:
        records = records.filter(session_id=session_filter)
    if term_filter:
        records = records.filter(term_id=term_filter)

    # Order records by primary key
    records = records.order_by('pk')

    # Prepare context for the template
    context = {
        'user_school':user_school,
        'finance_school':finance_school,
        'records': records,
        'schools': schools,
        'sessions': sessions,
        'terms': terms,
        'school_filter': school_filter,
        'session_filter': session_filter,
        'term_filter': term_filter,
    }

    return render(request, 'finance/finance_record_list.html', context)



class FinanceRecordUpdateView(UpdateView):
    model = FinanceRecord
    fields = [
        'names', 'student_class', 'initial_total_deposit', 'school', 'session', 'term',
        'school_shop', 'caps', 'haircut', 'others', 'note'
    ]
    template_name = 'finance/edit_record_form.html'
    success_url = reverse_lazy('finance:finance_record_view')  # Redirect to the list view after edit

    def get_queryset(self):
        """
        Optimize the queryset by prefetching related fields.
        """
        return FinanceRecord.objects.select_related('school', 'session', 'term')

    def form_valid(self, form):
        """
        Override form_valid to handle additional logic if needed.
        """
        # Example: Add a custom success message
        messages.success(self.request, "Finance record updated successfully!")
        return super().form_valid(form)
    


class FinanceRecordDeleteView(DeleteView):
    model = FinanceRecord
    template_name = 'finance/record_confirm_delete.html'
    success_url = reverse_lazy('finance:finance_record_view')  # Redirect to the list view after delete

class FinanceRecordCreateView(CreateView):
    model = FinanceRecord
    fields = [
        'names', 'student_class', 'initial_total_deposit', 'total_deposit', 'school', 'session', 'term',
        'school_shop', 'caps', 'haircut', 'others', 'note', 
    ]
    template_name = 'finance/add_record_form.html'
    success_url = reverse_lazy('finance:finance_record_view')  # Redirect to the list view after adding a new record

    def form_valid(self, form):
        # You can add any additional logic before saving the form (if needed)
        return super().form_valid(form)
    
    