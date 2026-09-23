# Create your views here.
from .models import FinanceRecord, School, Session, Term
import tablib
from django.views.decorators.http import require_POST
from urllib.parse import urlencode
from django.db import transaction
from urllib.parse import urlencode
from django.http import FileResponse
from .pdf import build_deposit_receipt_pdf, build_student_statement_pdf, build_family_statement_pdf, build_class_statements_pdf
from datetime import date, timedelta
from django.db.models import Sum, Count, Max, Q
from django.db.models.functions import Coalesce
from django.db import transaction
from django.db.models import Max
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timedelta
from datetime import date, datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Q
from django.utils.html import escape
from .forms import UploadFileForm, FinanceRecordForm
from datetime import timedelta
from django.db import models
from django.http import FileResponse
from .pdf import build_student_statement_pdf
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
from django.db.models import Max
from .forms import FinanceRecordForm
from .pdf import build_student_statement_pdf, build_family_statement_pdf

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .models import FinanceRecord, Session

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def accountant_required(view_func):
    """Allow only superusers and users with is_accountant=True."""
    @wraps(view_func)
    @login_required(login_url='teacher:teacher_login')
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or getattr(user, 'is_accountant', False)):
            raise PermissionDenied("Only the accounts department can access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


class AccountantRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'teacher:teacher_login'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (
            u.is_superuser or getattr(u, 'is_accountant', False)
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Only the accounts department can access this page.")
        return super().handle_no_permission()
    

class AccountantRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'teacher:teacher_login'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (
            u.is_superuser or getattr(u, 'is_accountant', False)
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Only the accounts department can access this page.")
        return super().handle_no_permission()


@login_required(login_url='teacher:teacher_login')
def finance_record_export_view(request):
    # ---- Filters (mirror finance_record_view) ----
    session_filter = request.GET.get('session') or None
    term_filter    = request.GET.get('term')    or None
    class_filter   = request.GET.get('class')   or None
    school_filter  = request.GET.get('school')  or None

    # ---- Base queryset, scoped to the user's school if they have one ----
    qs = FinanceRecord.objects.all()

    user_school = getattr(request.user, 'school', None)
    if user_school is not None:
        qs = qs.filter(school=user_school)
    elif school_filter:
        qs = qs.filter(school_id=school_filter)

    # ---- Apply the visible filters ----
    if session_filter:
        qs = qs.filter(session_id=session_filter)
    if term_filter:
        qs = qs.filter(term_id=term_filter)
    if class_filter:
        qs = qs.filter(student_class=class_filter)

    # ---- Export only the filtered rows ----
    resource = FinanceRecordResource()
    dataset = resource.export(qs)

    # ---- Format (xlsx by default, csv optional) ----
    fmt = (request.GET.get('format') or 'xlsx').lower()
    if fmt == 'csv':
        data = dataset.csv
        content_type = 'text/csv'
        filename = 'finance_records.csv'
    else:
        data = dataset.xlsx
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = 'finance_records.xlsx'

    response = HttpResponse(data, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


from django.views.decorators.http import require_POST
from django.contrib import messages


@login_required(login_url='teacher:teacher_login')
@require_POST
def finance_record_bulk_delete_view(request):
    """
    Delete the specific records the user selected via checkboxes.
    Only accepts POST. Only deletes records the user has access to.
    """
    # ---- Collect selected IDs (JS posts as `ids_csv`) ----
    ids = request.POST.getlist('ids')

    if not ids:
        raw = request.POST.get('ids_csv', '')
        ids = [x.strip() for x in raw.split(',') if x.strip()]

    # ---- Preserve filters so the redirect lands back on the same view ----
    post_school  = request.POST.get('school',  '')
    post_session = request.POST.get('session', '')
    post_term    = request.POST.get('term',    '')
    post_class   = request.POST.get('class',   '')

    back_url = reverse('finance:finance_record_view')
    if any((post_school, post_session, post_term, post_class)):
        back_url = f"{back_url}?{urlencode({chr(115)+chr(99)+chr(104)+chr(111)+chr(111)+chr(108): post_school, 'session': post_session, 'term': post_term, 'class': post_class})}"

    if not ids:
        messages.error(request, "No rows selected.")
        return redirect(back_url)

    # ---- Scope to the user's school — never trust client IDs ----
    qs = FinanceRecord.objects.filter(sn__in=ids)

    user_school = getattr(request.user, 'school', None)
    if user_school is not None:
        qs = qs.filter(school=user_school)

    requested_count = len(ids)
    count = qs.count()

    if count == 0:
        messages.warning(
            request,
            "No matching records found — they may have already been deleted "
            "or belong to a different school.",
        )
        return redirect(back_url)

    # ---- Perform the delete inside a transaction ----
    with transaction.atomic():
        qs.delete()

    # ---- Feedback ----
    if count < requested_count:
        messages.warning(
            request,
            f"Deleted {count} record(s). "
            f"{requested_count - count} were skipped (out of scope or already gone).",
        )
    else:
        messages.success(request, f"Deleted {count} record(s).")

    return redirect(back_url)


@accountant_required
def finance_record_import_view(request):
    user_school = request.user.school
    if user_school is None:
        return HttpResponse("No school assigned to your account.", status=403)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            resource = FinanceRecordResource()
            dataset = tablib.Dataset()
            new_records = request.FILES['file'].read()

            try:
                dataset.load(new_records, format='xlsx')
            except Exception as e:
                return render(request, 'finance/import_records.html', {
                    'form': form,
                    'errors': [('File error', str(e))],
                })

            # ---------- Dry run ----------
            result = resource.import_data(
                dataset,
                dry_run=True,
                raise_errors=False,
                request=request,
            )

            has_problems = (
                result.has_errors()
                or result.has_validation_errors()
            )

            if has_problems:
                return render(request, 'finance/import_records.html', {
                    'form': form,
                    'errors': result.row_errors(),
                    'validation_errors': result.invalid_rows,
                })

            # ---------- Real import ----------
            result = resource.import_data(
                dataset,
                dry_run=False,
                raise_errors=True,
                request=request,
            )

            # 👇 Stay on this page — show success, reset the form
            messages.success(
                request,
                f"Imported {result.total_rows} finance record(s)."
            )
            form = UploadFileForm()
            return render(request, 'finance/import_records.html', {
                'form': form,
                'imported_count': result.total_rows,
            })

    else:
        form = UploadFileForm()

    return render(request, 'finance/import_records.html', {'form': form})

      

     
  
from teacher.models import Teacher


def _finance_records_datatable(request, base_qs):
    """
    Serve a single DataTables AJAX page from the given queryset.
    Implements the DataTables server-side protocol:
      https://datatables.net/manual/server-side
    """
    draw   = int(request.GET.get('draw', 1))
    start  = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 25))

    # Cap page size so a malicious client can't ask for everything
    if length > 500 or length < 1:
        length = 25

    # Total before the search box filters anything
    records_total = base_qs.count()

    # ---- Global search (DataTables search box) ----
    search = (request.GET.get('search[value]') or '').strip()
    filtered = base_qs

    if search:
        search_lower = search.lower()

        # ---- Text search across real columns ----
        text_q = (
            Q(names__icontains=search) |
            Q(student_class__icontains=search) |
            Q(school__school_name__icontains=search) |
            Q(session__name__icontains=search) |
            Q(term__name__icontains=search)
        )

        # ---- Status search — accepts prefixes as short as 2 chars ----
        # keyword    → stored value
        STATUS_KEYWORDS = [
            ('exhausted', 'exhausted'),
            ('owing',     'exhausted'),     # synonym
            ('available', 'remaining'),
            ('remaining', 'remaining'),
            ('paid',      'remaining'),     # synonym
            ('exh',       'exhausted'),     # short forms
            ('ava',       'remaining'),
            ('rem',       'remaining'),
            ('owi',       'exhausted'),
            ('pai',       'remaining'),
        ]

        status_q = None

        # Match any keyword whose START begins with what the user typed
        if len(search_lower) >= 2:
            for keyword, stored_value in STATUS_KEYWORDS:
                if keyword.startswith(search_lower):
                    status_q = Q(status=stored_value)
                    break

        if status_q is not None:
            filtered = filtered.filter(text_q | status_q)
        else:
            filtered = filtered.filter(text_q)

    records_filtered = filtered.count()

    # ---- Ordering ----
    # Indices match the <th> order in finance_record_list.html.
    # NOTE: column 0 is the selection checkbox, so real data starts at index 1.
    ORDERABLE = {
        '1':  'names',
        '2':  'week_start',
        '3':  'initial_total_deposit',
        '4':  'total_deposit',
        '5':  'school_shop',
        '6':  'caps',
        '7':  'haircut',
        '8':  'others',
        '9':  'total_expense',
        '10': 'current_balance',
        '11': 'balance_brought_forward',
        # 0 (checkbox), 12 (status), 13 (receipt), 14 (edit), 15 (delete) are not sortable
    }
    order_col = request.GET.get('order[0][column]')
    order_dir = (request.GET.get('order[0][dir]') or 'asc').lower()

    if order_col in ORDERABLE:
        col = ORDERABLE[order_col]
        if order_dir == 'desc':
            col = '-' + col
        filtered = filtered.order_by(col)
    else:
        filtered = filtered.order_by('sn')

    # ---- Page ----
    page = filtered[start:start + length]

    # ---- Rows ----
    data = []
    for r in page:
        # ---- Status pill ----
        if r.status == 'exhausted':
            status_html = (
                '<span style="color:#c0392b;font-weight:bold;">'
                '<i class="fas fa-times-circle"></i></span>'
            )
        else:
            status_html = (
                '<span style="color:#27ae60;font-weight:bold;">'
                '<i class="fas fa-check-circle"></i></span>'
            )

        # ---- Edit / Delete ----
        edit_url   = reverse('finance:record_edit',   args=[r.pk])
        delete_url = reverse('finance:record_delete', args=[r.pk])

        edit_html = (
            f'<a href="{edit_url}" class="btn btn-primary" '
            f'style="padding:4px 10px;font-size:12px;">'
            f'<i class="fas fa-edit"></i></a>'
        )
        delete_html = (
            f'<a href="{delete_url}" class="btn btn-danger" '
            f'style="padding:4px 10px;font-size:12px;" '
            f'onclick="return confirm(\'Delete this record?\');">'
            f'<i class="fas fa-trash"></i></a>'
        )

        # ---- Receipt — only if this record has a deposit ----
        if r.initial_total_deposit and r.initial_total_deposit > 0:
            receipt_url = reverse('finance:record_receipt', args=[r.pk])
            receipt_html = (
                f'<a href="{receipt_url}" target="_blank" '
                f'style="background:#17a2b8;color:white;padding:4px 10px;'
                f'border-radius:4px;text-decoration:none;font-size:12px;" '
                f'title="Print Receipt">'
                f'<i class="fas fa-receipt"></i></a>'
            )
        else:
            receipt_html = '<span style="color:#ccc;">—</span>'

        data.append({
            'id':                      r.pk,   # ← used by the checkbox column
            'names':                   escape(r.names.title()) if r.names else '',
            'week_start':              r.week_start.strftime('%d %b %Y') if r.week_start else '—',
            'initial_total_deposit':   str(r.initial_total_deposit or 0),
            'total_deposit':           str(r.total_deposit or 0),
            'school_shop':             str(r.school_shop or 0),
            'caps':                    str(r.caps or 0),
            'haircut':                 str(r.haircut or 0),
            'others':                  str(r.others or 0),
            'total_expense':           str(r.total_expense or 0),
            'current_balance':         str(r.current_balance or 0),
            'balance_brought_forward': str(r.balance_brought_forward or 0),
            'status':                  status_html,
            'receipt':                 receipt_html,
            'edit':                    edit_html,
            'delete':                  delete_html,
        })

    return JsonResponse({
        'draw':            draw,
        'recordsTotal':    records_total,
        'recordsFiltered': records_filtered,
        'data':            data,
    })




@accountant_required
def finance_record_view(request):
    user_school = request.user.school

    if user_school is None:
        return render(request, 'finance/finance_record_list.html', {
            'user_school':     None,
            'finance_school':  None,
            'records':         [],
            'schools':         [],
            'sessions':        [],
            'terms':           [],
            'classes':         [],
            'school_filter':   None,
            'session_filter':  None,
            'term_filter':     None,
            'class_filter':    None,
            'default_session': None,
            'default_term':    None,
        })

    # ---- Sessions (cached) ----
    sessions = cache.get(f'fin_sessions_{user_school.id}')
    if sessions is None:
        sessions = list(Session.objects.filter(school=user_school)
                        .only('id', 'name').order_by('name'))
        cache.set(f'fin_sessions_{user_school.id}', sessions, 300)

    # ---- Terms (cached) ----
    terms = cache.get(f'fin_terms_{user_school.id}')
    if terms is None:
        terms = list(Term.objects.filter(school=user_school)
                     .only('id', 'name', 'order').order_by('order'))
        cache.set(f'fin_terms_{user_school.id}', terms, 300)

    # ---- Defaults from last activity ----
    latest = (FinanceRecord.objects
              .filter(school=user_school)
              .order_by('-sn')
              .values('session_id', 'term_id')
              .first())

    if latest and latest['session_id'] and latest['term_id']:
        default_session = str(latest['session_id'])
        default_term    = str(latest['term_id'])
    else:
        newest_session  = sessions[-1] if sessions else None
        first_term      = terms[0]     if terms    else None
        default_session = str(newest_session.id) if newest_session else None
        default_term    = str(first_term.id)     if first_term     else None

    # ---- Filter params ----
    session_param = request.GET.get('session')
    term_param    = request.GET.get('term')
    class_filter  = request.GET.get('class') or None
    school_filter = request.GET.get('school')

    session_filter = default_session if session_param is None else (session_param or None)
    term_filter    = default_term    if term_param    is None else (term_param    or None)

    # ---- Distinct classes — scoped to current session + term ----
    classes_qs = FinanceRecord.objects.filter(school=user_school)
    if session_filter:
        classes_qs = classes_qs.filter(session_id=session_filter)
    if term_filter:
        classes_qs = classes_qs.filter(term_id=term_filter)

    classes = list(
        classes_qs
        .exclude(student_class__isnull=True)
        .exclude(student_class='')
        .exclude(student_class='NA')
        .values_list('student_class', flat=True)
        .distinct()
        .order_by('student_class')
    )

    # ---- Base queryset ----
    records = (FinanceRecord.objects
               .filter(school=user_school)
               .select_related('school', 'session', 'term', 'student'))

    if school_filter:
        records = records.filter(school_id=school_filter)
    if session_filter:
        records = records.filter(session_id=session_filter)
    if term_filter:
        records = records.filter(term_id=term_filter)
    if class_filter:
        records = records.filter(student_class=class_filter)

    # ---- Branch: DataTables AJAX vs. page render ----
    if request.GET.get('draw'):
        return _finance_records_datatable(request, records)

    records = records.order_by('sn')

    finance_school = getattr(user_school, 'school_name', None) or str(user_school)

    context = {
        'user_school':     user_school,
        'finance_school':  finance_school,
        'records':         records,
        'schools':         School.objects.filter(id=user_school.id),
        'sessions':        sessions,
        'terms':           terms,
        'classes':         classes,
        'school_filter':   school_filter,
        'session_filter':  session_filter,
        'term_filter':     term_filter,
        'class_filter':    class_filter,
        'default_session': default_session,
        'default_term':    default_term,
    }

    return render(request, 'finance/finance_record_list.html', context)




class FinanceRecordUpdateView(AccountantRequiredMixin, UpdateView):
    model = FinanceRecord
    form_class = FinanceRecordForm
    template_name = 'finance/edit_record_form.html'
    # success_url = reverse_lazy('finance:finance_record_view')  ← remove this

    def get_success_url(self):
        # Stay on the same edit page
        return reverse('finance:record_edit', args=[self.object.pk])

    def get_queryset(self):
        return (FinanceRecord.objects
                .filter(school=self.request.user.school)
                .select_related('school', 'session', 'term', 'student'))

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_school = self.request.user.school

        # ---- Sessions ----
        session_qs = Session.objects.all()
        if user_school is not None:
            session_qs = session_qs.filter(school=user_school)
        form.fields['session'].queryset = session_qs.distinct().order_by('name')

        # ---- Terms ----
        term_qs = Term.objects.all()
        if user_school is not None:
            term_qs = term_qs.filter(school=user_school)
        form.fields['term'].queryset = term_qs.distinct().order_by('order')

        # ---- Students ----
        from django.contrib.auth import get_user_model
        User = get_user_model()
        student_qs = User.objects.filter(school=user_school)
        form.fields['student'].queryset = student_qs.distinct().order_by(
            'first_name', 'last_name'
        )

        return form

    def form_valid(self, form):
        student    = form.cleaned_data.get('student')
        session    = form.cleaned_data.get('session')
        term       = form.cleaned_data.get('term')
        week_start = form.cleaned_data.get('week_start')
        confirm    = self.request.POST.get('confirm_duplicate') == '1'

        if student and session and term and week_start and not confirm:
            existing = (FinanceRecord.objects
                        .filter(student=student,
                                session=session,
                                term=term,
                                week_start=week_start)
                        .exclude(pk=self.object.pk)  # 👈 exclude self
                        .first())

            if existing:
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        duplicate_warning=True,
                        existing_record=existing,
                    )
                )
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Finance record updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user_school'] = self.request.user.school
        return ctx



@accountant_required
def finance_bulk_add_view(request):
    """
    Bulk-add one week's records for an entire class.
    Optimized: O(1) queries regardless of class size.
    """
    user_school = request.user.school
    if user_school is None:
        raise PermissionDenied("No school assigned.")

    session_id   = request.GET.get('session')   or request.POST.get('session')
    term_id      = request.GET.get('term')      or request.POST.get('term')
    class_filter = request.GET.get('class')     or request.POST.get('class')

    if not (session_id and term_id and class_filter):
        messages.error(request, "Please pick a session, term, and class first.")
        return redirect('finance:finance_summary')

    # ---- 1 query: students in this class ----
    from django.contrib.auth import get_user_model
    User = get_user_model()
    students = list(
        User.objects
        .filter(school=user_school, student_class=class_filter)
        .only('id', 'first_name', 'last_name', 'student_class')
        .order_by('first_name', 'last_name')
    )

    if not students:
        messages.warning(request, f"No students found in class {class_filter}.")
        return redirect('finance:finance_summary')

    student_ids = [s.id for s in students]

    # ---- 2 queries: latest record per student ----
    # Query A: highest sn per student
    latest_sns = dict(
        FinanceRecord.objects
        .filter(student_id__in=student_ids)
        .values_list('student_id')
        .annotate(latest=Max('sn'))
        .values_list('student_id', 'latest')
    )

    # Query B: fetch those records (for balance + week_start)
    latest_per_student = {}
    if latest_sns:
        for r in (FinanceRecord.objects
                  .filter(sn__in=latest_sns.values())
                  .only('sn', 'student_id', 'current_balance', 'week_start')):
            latest_per_student[r.student_id] = r

    # ==================================================================
    # POST — bulk insert
    # ==================================================================
    if request.method == 'POST':
        week_start_str = request.POST.get('week_start') or ''
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid week start date.")
            return redirect(
                f"{reverse('finance:finance_bulk_add')}"
                f"?session={session_id}&term={term_id}&class={class_filter}"
            )

        # ---- Parse all rows in memory (no queries) ----
        rows = []
        skipped_no_activity = 0
        skipped_duplicate   = 0

        for s in students:
            def _num(key):
                raw = request.POST.get(f'student_{s.id}_{key}') or '0'
                try:
                    return Decimal(raw)
                except (InvalidOperation, ValueError):
                    return Decimal('0')

            deposit = _num('deposit')
            shop    = _num('shop')
            caps    = _num('caps')
            haircut = _num('haircut')
            others  = _num('others')

            # Skip students with no activity
            if deposit == 0 and shop == 0 and caps == 0 and haircut == 0 and others == 0:
                skipped_no_activity += 1
                continue

            # Skip if a record already exists for this student + week
            # (protects against double-submits and re-running the form)
            existing = (FinanceRecord.objects
                        .filter(student=s,
                                session_id=session_id,
                                term_id=term_id,
                                week_start=week_start)
                        .exists())
            if existing:
                skipped_duplicate += 1
                continue

            rows.append((s, deposit, shop, caps, haircut, others))

        if not rows:
            messages.warning(
                request,
                f"Nothing to save. Skipped {skipped_no_activity} with no activity, "
                f"{skipped_duplicate} duplicates."
            )
            return redirect(
                f"{reverse('finance:finance_bulk_add')}"
                f"?session={session_id}&term={term_id}&class={class_filter}"
            )

        # ---- 1 query: starting sn ----
        next_sn = (FinanceRecord.objects.aggregate(m=Max('sn'))['m'] or 0)

        # ---- Build all FinanceRecord objects in Python ----
        to_create = []
        for s, deposit, shop, caps, haircut, others in rows:
            next_sn += 1

            last = latest_per_student.get(s.id)
            bbf  = last.current_balance if last else Decimal('0')

            total_expense   = shop + caps + haircut + others
            total_deposit   = deposit + bbf
            current_balance = total_deposit - total_expense
            status          = 'exhausted' if current_balance <= 0 else 'remaining'
            full_name       = f"{s.first_name or ''} {s.last_name or ''}".strip()

            to_create.append(FinanceRecord(
                sn                    = next_sn,
                student               = s,
                names                 = full_name,
                student_class         = s.student_class or class_filter,
                school                = user_school,
                session_id            = session_id,
                term_id               = term_id,
                week_start            = week_start,
                initial_total_deposit = deposit,
                school_shop           = shop,
                caps                  = caps,
                haircut               = haircut,
                others                = others,
                total_expense         = total_expense,
                total_deposit         = total_deposit,
                balance_brought_forward = bbf,
                current_balance       = current_balance,
                status                = status,
                created_by            = request.user,   # 👈 add
                updated_by            = request.user,   # 👈 add
            ))

        # ---- 1 batched INSERT (not N) ----
        with transaction.atomic():
            FinanceRecord.objects.bulk_create(to_create, batch_size=200)

        messages.success(
            request,
            f"Saved {len(to_create)} record(s) for {class_filter} "
            f"(week of {week_start}). "
            f"Skipped {skipped_no_activity} empty, {skipped_duplicate} duplicate."
        )
        return redirect(
            f"{reverse('finance:finance_bulk_add')}"
            f"?session={session_id}&term={term_id}&class={class_filter}"
        )

    # ==================================================================
    # GET — show the grid
    # ==================================================================
    student_rows = []
    for s in students:
        last = latest_per_student.get(s.id)
        student_rows.append({
            'student':   s,
            'balance':   last.current_balance if last else Decimal('0'),
            'last_week': last.week_start if last else None,
        })

    # Default week start: last class record + 7, else this Monday
    latest_class = (FinanceRecord.objects
                    .filter(school=user_school,
                            session_id=session_id,
                            term_id=term_id,
                            student_class=class_filter)
                    .order_by('-week_start')
                    .values_list('week_start', flat=True)
                    .first())

    if latest_class:
        default_week_start = latest_class + timedelta(days=7)
    else:
        today = date.today()
        default_week_start = today - timedelta(days=today.weekday())

    context = {
        'user_school':        user_school,
        'session':            Session.objects.filter(pk=session_id).first(),
        'term':               Term.objects.filter(pk=term_id).first(),
        'class_filter':       class_filter,
        'student_rows':       student_rows,
        'default_week_start': default_week_start,
        'session_id':         session_id,
        'term_id':            term_id,
    }
    return render(request, 'finance/bulk_add_form.html', context)


        
class FinanceRecordDeleteView(AccountantRequiredMixin, DeleteView):
    model = FinanceRecord
    template_name = 'finance/record_confirm_delete.html'
    success_url = reverse_lazy('finance:finance_record_view')

    def get_queryset(self):
        # MUST be same school as the logged-in accountant
        return FinanceRecord.objects.filter(school=self.request.user.school)
    



class FinanceRecordCreateView(AccountantRequiredMixin, CreateView):
    model = FinanceRecord
    form_class = FinanceRecordForm
    template_name = 'finance/add_record_form.html'

    def get_success_url(self):
        # Stay on the same add-page after saving
        return reverse('finance:finance_record_add')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_school = self.request.user.school

        # ---- Sessions ----
        session_qs = Session.objects.all()
        if user_school is not None:
            session_qs = session_qs.filter(school=user_school)
        form.fields['session'].queryset = session_qs.distinct().order_by('name')

        # ---- Terms ----
        term_qs = Term.objects.all()
        if user_school is not None:
            term_qs = term_qs.filter(school=user_school)
        form.fields['term'].queryset = term_qs.distinct().order_by('order')

        # ---- Students (NewUser) — restrict to this school ----
        from django.contrib.auth import get_user_model
        User = get_user_model()
        student_qs = User.objects.filter(school=user_school)
        form.fields['student'].queryset = student_qs.distinct().order_by(
            'first_name', 'last_name'
        )

        return form

    def get_initial(self):
        """
        Pre-fill the form with sensible defaults:
          - With ?student=X&session=Y&term=Z   → that student + BBF from their last week
          - With &next=1                        → also pre-fill week_start = last week + 7
          - Without any params                  → last saved session/term, this Monday
        """
        initial = super().get_initial()
        user        = self.request.user
        user_school = user.school

        student_id = self.request.GET.get('student')
        session_id = self.request.GET.get('session')
        term_id    = self.request.GET.get('term')
        next_week  = self.request.GET.get('next') == '1'

        # --------------------------------------------------------------
        # Case 1: arrived from "Add Next Week" (param-carrying link)
        # --------------------------------------------------------------
        if student_id and session_id and term_id:
            last = (FinanceRecord.objects
                    .filter(student_id=student_id,
                            session_id=session_id,
                            term_id=term_id)
                    .order_by('-week_start', '-sn')
                    .first())

            if last:
                initial['student'] = last.student_id
                initial['session'] = last.session_id
                initial['term']    = last.term_id
                initial['balance_brought_forward'] = last.current_balance

                if next_week and last.week_start:
                    initial['week_start'] = last.week_start + timedelta(days=7)
                return initial

        # --------------------------------------------------------------
        # Case 2: opened the form fresh (no params)
        # --------------------------------------------------------------
        latest = (FinanceRecord.objects
                  .filter(school=user_school)
                  .order_by('-sn')
                  .first())

        # Session default
        if latest and latest.session_id:
            initial['session'] = latest.session_id
        else:
            newest_session = (Session.objects
                              .filter(school=user_school)
                              .order_by('name')
                              .last())
            if newest_session:
                initial['session'] = newest_session.id

        # Term default
        if latest and latest.term_id:
            initial['term'] = latest.term_id
        else:
            first_term = (Term.objects
                          .filter(school=user_school)
                          .order_by('order')
                          .first())
            if first_term:
                initial['term'] = first_term.id

        # Week start default
        if latest and latest.week_start:
            initial['week_start'] = latest.week_start + timedelta(days=7)
        else:
            today  = date.today()
            monday = today - timedelta(days=today.weekday())
            initial['week_start'] = monday

        return initial

    def form_valid(self, form):
        # ---- Duplicate-week check ----
        student    = form.cleaned_data.get('student')
        session    = form.cleaned_data.get('session')
        term       = form.cleaned_data.get('term')
        week_start = form.cleaned_data.get('week_start')
        confirm    = self.request.POST.get('confirm_duplicate') == '1'

        if student and session and term and week_start and not confirm:
            existing = (FinanceRecord.objects
                        .filter(student=student,
                                session=session,
                                term=term,
                                week_start=week_start)
                        .first())

            if existing:
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        duplicate_warning=True,
                        existing_record=existing,
                    )
                )

        # ---- Normal save path ----
        form.instance.school = self.request.user.school

        if student:
            full_name = f"{student.first_name or ''} {student.last_name or ''}".strip()
            form.instance.names = full_name or form.cleaned_data.get('names') or ''
            form.instance.student_class = (
                student.student_class
                or form.cleaned_data.get('student_class')
                or 'NA'
            )

        # ---- Audit trail ----
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        # ---- Save + success message ----
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Record for “{form.instance.names}” — week of {form.instance.week_start} saved."
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user_school'] = self.request.user.school
        return ctx

    

from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model


from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model


@accountant_required
def student_search_api(request):
    User = get_user_model()
    user_school = request.user.school
    q   = (request.GET.get('q') or '').strip()
    sid = request.GET.get('id')

    qs = User.objects.filter(school=user_school)

    if sid:
        qs = qs.filter(id=sid)
    elif q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(admission_no__icontains=q) |
            Q(username__icontains=q) |
            Q(email__icontains=q)
        )
    else:
        qs = qs.none()

    qs = qs.order_by('first_name', 'last_name')[:20]

    results = []
    for u in qs:
        name = f"{u.first_name or ''} {u.last_name or ''}".strip() \
               or u.username or u.email
        label = name
        if u.student_class:
            label += f" — {u.student_class}"
        if u.admission_no:
            label += f" ({u.admission_no})"
        results.append({'id': u.id, 'text': label})

    return JsonResponse({'results': results})



@accountant_required
def finance_summary_view(request):
    user_school = request.user.school
    if user_school is None:
        return render(request, 'finance/finance_summary.html', {
            'sessions':    Session.objects.none(),
            'terms':       Term.objects.none(),
            'rows':        [],
            'exhausted':   [],
            'families':    [],
            'classes':     [],
            'stats':       None,
            'class_stats': [],
        })

    session_filter = request.GET.get('session')
    term_filter    = request.GET.get('term')
    class_filter   = request.GET.get('class') or None

    rows = []
    exhausted = []
    families = []
    stats = None
    class_stats = []

    # Distinct classes for the dropdown (school-wide)
    classes = list(
        FinanceRecord.objects
        .filter(school=user_school)
        .exclude(student_class__isnull=True)
        .exclude(student_class='')
        .exclude(student_class='NA')
        .values_list('student_class', flat=True)
        .distinct()
        .order_by('student_class')
    )

    if session_filter and term_filter:
        qs = (FinanceRecord.objects
              .filter(school=user_school,
                      session_id=session_filter,
                      term_id=term_filter)
              .select_related('student', 'session', 'term')
              .order_by('names', 'week_start', 'sn'))

        groups = {}
        for r in qs:
            key = r.student_id or (r.names, r.student_class)
            groups.setdefault(key, []).append(r)

        for key, records in groups.items():
            first = records[0]
            last  = records[-1]
            row = {
                'student_id':    first.student_id,
                'names':         first.names,
                'student_class': first.student_class,
                'opening':       first.balance_brought_forward or 0,
                'deposits':      sum((r.initial_total_deposit or 0) for r in records),
                'expenses':      sum((r.total_expense        or 0) for r in records),
                'closing':       last.current_balance or 0,
                'status':        last.status,
                'weeks':         len(records),
                'session_id':    first.session_id,
                'term_id':       first.term_id,
            }
            rows.append(row)
            if last.status == 'exhausted':
                exhausted.append(row)

        # Apply class filter
        if class_filter:
            rows      = [r for r in rows      if r['student_class'] == class_filter]
            exhausted = [r for r in exhausted if r['student_class'] == class_filter]

        rows.sort(key=lambda x: (x['names'] or '').lower())

        # Sort exhausted by most negative first
        exhausted.sort(key=lambda x: float(x['closing'] or 0))

        # Families (respect class filter if set)
        fam_set = set()
        for r in qs:
            if class_filter and r.student_class != class_filter:
                continue
            if r.student and r.student.last_name:
                fam_set.add(r.student.last_name)
        families = sorted(fam_set)

        # ================================================================
        # Statistics — overall
        # ================================================================
        total_students  = len(rows)
        exhausted_count = len(exhausted)
        available_count = total_students - exhausted_count
        total_classes   = len(set(r['student_class'] for r in rows if r['student_class']))

        total_opening   = sum((r['opening']  or 0) for r in rows)
        total_deposits  = sum((r['deposits'] or 0) for r in rows)
        total_expenses  = sum((r['expenses'] or 0) for r in rows)
        total_closing   = sum((r['closing']  or 0) for r in rows)

        stats = {
            'total_students': total_students,
            'total_classes':  total_classes,
            'exhausted':      exhausted_count,
            'available':      available_count,
            'total_opening':  total_opening,
            'total_deposits': total_deposits,
            'total_expenses': total_expenses,
            'total_closing':  total_closing,
        }

        # ================================================================
        # Statistics — per class
        # ================================================================
        class_map = {}
        for r in rows:
            cls = r['student_class'] or '—'
            if cls not in class_map:
                class_map[cls] = {
                    'name':      cls,
                    'students':  0,
                    'exhausted': 0,
                    'deposits':  0,
                    'expenses':  0,
                    'closing':   0,
                }
            class_map[cls]['students'] += 1
            class_map[cls]['deposits'] += (r['deposits'] or 0)
            class_map[cls]['expenses'] += (r['expenses'] or 0)
            class_map[cls]['closing']  += (r['closing']  or 0)
            if r['status'] == 'exhausted':
                class_map[cls]['exhausted'] += 1

        class_stats = sorted(class_map.values(), key=lambda x: x['name'])

    else:
        # School-wide exhausted view (no session + term selected)
        latest_ids = (FinanceRecord.objects
                      .filter(school=user_school, student__isnull=False)
                      .values('student_id')
                      .annotate(latest_sn=models.Max('sn'))
                      .values_list('latest_sn', flat=True))

        latest_records = (FinanceRecord.objects
                          .filter(sn__in=list(latest_ids),
                                  status='exhausted')
                          .select_related('student', 'session', 'term')
                          .order_by('names'))

        for r in latest_records:
            if class_filter and r.student_class != class_filter:
                continue
            exhausted.append({
                'student_id':    r.student_id,
                'names':         r.names,
                'student_class': r.student_class,
                'closing':       r.current_balance,
                'session':       r.session.name if r.session else '—',
                'term':          r.term.name    if r.term    else '—',
                'session_id':    r.session_id,
                'term_id':       r.term_id,
                'weeks':         None,
            })

        exhausted.sort(key=lambda x: float(x['closing'] or 0))

    context = {
        'user_school':    user_school,
        'sessions':       Session.objects.filter(school=user_school).order_by('name'),
        'terms':          Term.objects.filter(school=user_school).order_by('order'),
        'session_filter': session_filter,
        'term_filter':    term_filter,
        'class_filter':   class_filter,
        'classes':        classes,
        'rows':           rows,
        'exhausted':      exhausted,
        'families':       families,
        'stats':          stats,
        'class_stats':    class_stats,
    }
    return render(request, 'finance/finance_summary.html', context)

    
@accountant_required
def finance_student_view(request):
    """
    Show every weekly row for ONE student in ONE session + term.
    """
    user_school    = request.user.school
    student_id     = request.GET.get('student')
    session_filter = request.GET.get('session')
    term_filter    = request.GET.get('term')

    records = FinanceRecord.objects.none()
    student = None
    record_class = None

    if student_id and session_filter and term_filter:
        records = (FinanceRecord.objects
                   .filter(school=user_school,
                           student_id=student_id,
                           session_id=session_filter,
                           term_id=term_filter)
                   .select_related('student', 'session', 'term', 'school')
                   .order_by('week_start', 'sn'))

        # Get the student object once for the header
        from django.contrib.auth import get_user_model
        User = get_user_model()
        student = User.objects.filter(pk=student_id, school=user_school).first()

        # 👇 Historical class — what the record says, not what the user has now
        first_record = records.first()
        if first_record and first_record.student_class:
            record_class = first_record.student_class

    # Compute totals for the footer
    total_deposits = sum(r.initial_total_deposit for r in records) if records else 0
    total_expenses = sum(r.total_expense for r in records) if records else 0
    closing        = records.last().current_balance if records else 0
    opening        = records.first().balance_brought_forward if records else 0

    context = {
        'user_school':    user_school,
        'student':        student,
        'student_id':     student_id,
        'record_class':   record_class,      # 👈 new
        'session_filter': session_filter,
        'term_filter':    term_filter,
        'records':        records,
        'total_deposits': total_deposits,
        'total_expenses': total_expenses,
        'opening':        opening,
        'closing':        closing,
    }
    return render(request, 'finance/student_statement.html', context)



@accountant_required
def student_statement_pdf(request):
    user_school    = request.user.school
    student_id     = request.GET.get('student')
    session_filter = request.GET.get('session')
    term_filter    = request.GET.get('term')

    if not (student_id and session_filter and term_filter):
        raise PermissionDenied("Missing parameters.")

    records = list(
        FinanceRecord.objects
        .filter(school=user_school,
                student_id=student_id,
                session_id=session_filter,
                term_id=term_filter)
        .select_related('student', 'session', 'term', 'school')
        .order_by('week_start', 'sn')
    )

    from django.contrib.auth import get_user_model
    User = get_user_model()
    student = User.objects.filter(pk=student_id, school=user_school).first()

    if not student or not records:
        raise PermissionDenied("No records found for this student.")

    student_name = f"{student.first_name or ''} {student.last_name or ''}".strip() or "Student"

    # 👇 Use historical class from the record
    record_class = records[0].student_class or student.student_class or "—"

    buf = build_student_statement_pdf(
        school_name     = str(user_school),
        student_name    = student_name,
        student_class   = record_class,          # 👈 was student.student_class
        admission_no    = student.admission_no or "—",
        session_name    = str(records[0].session) if records[0].session else "—",
        term_name       = str(records[0].term)    if records[0].term    else "—",
        records         = records,
    )

    safe_name = student_name.replace(" ", "_").replace("/", "-")
    filename  = f"statement_{safe_name}_{session_filter}_{term_filter}.pdf"

    return FileResponse(
        buf,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf',
    )


@accountant_required
def family_statement_pdf(request):
    """
    One PDF for all children in a family (matched by last name).
    URL: /finance-records/family/pdf/?family=Hassan&session=4&term=7
    """
    user_school    = request.user.school
    family_name    = request.GET.get('family')
    session_filter = request.GET.get('session')
    term_filter    = request.GET.get('term')

    if not (family_name and session_filter and term_filter):
        raise PermissionDenied("Missing parameters.")

    from django.contrib.auth import get_user_model
    User = get_user_model()

    siblings = (User.objects
                .filter(school=user_school, last_name__iexact=family_name)
                .order_by('first_name'))

    students_data = []
    for s in siblings:
        records = list(
            FinanceRecord.objects
            .filter(school=user_school,
                    student_id=s.id,
                    session_id=session_filter,
                    term_id=term_filter)
            .order_by('week_start', 'sn')
        )
        if records:
            students_data.append({
                'student_name':  f"{s.first_name or ''} {s.last_name or ''}".strip() or "Student",
                'student_class': s.student_class or '—',
                'admission_no':  s.admission_no or '—',
                'records':       records,
            })

    if not students_data:
        raise PermissionDenied("No records found for this family.")

    session_obj = Session.objects.filter(pk=session_filter).first()
    term_obj    = Term.objects.filter(pk=term_filter).first()

    buf = build_family_statement_pdf(
        school_name  = str(user_school),
        family_name  = family_name,
        session_name = str(session_obj) if session_obj else '—',
        term_name    = str(term_obj)    if term_obj    else '—',
        students_data = students_data,
    )

    safe = family_name.replace(' ', '_').replace('/', '-')
    filename = f"family_{safe}_{session_filter}_{term_filter}.pdf"
    return FileResponse(buf, as_attachment=True,
                        filename=filename, content_type='application/pdf')


@accountant_required
def finance_dashboard_view(request):
    """
    Landing page for the accounts department.
    Single-page overview: today's activity, exhausted students, quick actions.
    """
    user_school = request.user.school
    if user_school is None:
        return render(request, 'finance/dashboard.html', {
            'user_school': None,
            'today':       date.today(),
        })

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    # --------------------------------------------------------------
    # Today's activity — single aggregate query
    # --------------------------------------------------------------
    today_stats = (FinanceRecord.objects
                   .filter(school=user_school,
                           week_start=today)  # or use created-date if you track it
                   .aggregate(
                       records   = Count('sn'),
                       deposits  = Coalesce(Sum('initial_total_deposit'), Decimal('0')),
                       expenses  = Coalesce(Sum('total_expense'), Decimal('0')),
                   ))

    # If you'd rather show "records saved today regardless of week_start",
    # we'd need a created_at field. For now we use week_start.

    # --------------------------------------------------------------
    # Exhausted students — top 5 by debt (most negative first)
    # --------------------------------------------------------------
    latest_ids = (FinanceRecord.objects
                  .filter(school=user_school, student__isnull=False)
                  .values('student_id')
                  .annotate(latest_sn=Max('sn'))
                  .values_list('latest_sn', flat=True))

    exhausted_qs = (FinanceRecord.objects
                    .filter(sn__in=list(latest_ids), status='exhausted')
                    .select_related('student', 'session', 'term')
                    .order_by('current_balance')[:5])

    exhausted_list = [{
        'student_id':    r.student_id,
        'names':         r.names,
        'student_class': r.student_class,
        'closing':       r.current_balance,
        'session_id':    r.session_id,
        'term_id':       r.term_id,
    } for r in exhausted_qs]

    exhausted_count = (FinanceRecord.objects
                       .filter(sn__in=list(latest_ids), status='exhausted')
                       .count())

    # --------------------------------------------------------------
    # Current term snapshot
    # --------------------------------------------------------------
    latest_record = (FinanceRecord.objects
                     .filter(school=user_school)
                     .order_by('-sn')
                     .select_related('session', 'term')
                     .first())

    current_session = latest_record.session if latest_record else None
    current_term    = latest_record.term    if latest_record else None

    # Students / classes count
    from django.contrib.auth import get_user_model
    User = get_user_model()

    student_count = (User.objects
                     .filter(school=user_school)
                     .exclude(student_class__isnull=True)
                     .exclude(student_class='')
                     .exclude(student_class='NA')
                     .count())

    class_count = (User.objects
                   .filter(school=user_school)
                   .exclude(student_class__isnull=True)
                   .exclude(student_class='')
                   .exclude(student_class='NA')
                   .values('student_class')
                   .distinct()
                   .count())

    # --------------------------------------------------------------
    # Week-at-a-glance: entries created for the current week
    # --------------------------------------------------------------
    week_stats = (FinanceRecord.objects
                  .filter(school=user_school,
                          week_start__gte=monday,
                          week_start__lt=monday + timedelta(days=7))
                  .aggregate(
                      records  = Count('sn'),
                      deposits = Coalesce(Sum('initial_total_deposit'), Decimal('0')),
                      expenses = Coalesce(Sum('total_expense'), Decimal('0')),
                  ))

    context = {
        'user_school':      user_school,
        'today':            today,
        'monday':           monday,

        'today_stats':      today_stats,
        'week_stats':       week_stats,

        'exhausted_list':   exhausted_list,
        'exhausted_count':  exhausted_count,

        'current_session':  current_session,
        'current_term':     current_term,
        'student_count':    student_count,
        'class_count':      class_count,
    }
    return render(request, 'finance/dashboard.html', context)


@accountant_required
def finance_record_receipt_view(request, pk):
    """
    Printable deposit receipt for a single FinanceRecord.
    URL: /finance/record/<pk>/receipt/
    """
    user_school = request.user.school
    if user_school is None:
        raise PermissionDenied("No school assigned.")

    record = (FinanceRecord.objects
              .filter(sn=pk, school=user_school)
              .select_related('student', 'session', 'term', 'school')
              .first())

    if not record:
        raise PermissionDenied("Record not found.")

    # ---- Compute balance-before from BBF ----
    balance_before = record.balance_brought_forward or Decimal('0')
    balance_after  = record.current_balance or Decimal('0')

    # ---- Student info ----
    student_name  = record.names or "—"
    student_class = record.student_class or "—"
    admission_no  = getattr(record.student, 'admission_no', None) or "—"

    # ---- Who received it ----
    received_by = (
        f"{request.user.first_name or ''} {request.user.last_name or ''}".strip()
        or request.user.username
        or request.user.email
        or "—"
    )

    # ---- Optional: mark reprint if ?reprint=1 ----
    is_reprint = request.GET.get('reprint') == '1'

    buf = build_deposit_receipt_pdf(
        school_name    = str(user_school),
        student_name   = student_name,
        student_class  = student_class,
        admission_no   = admission_no,
        amount         = record.initial_total_deposit,
        balance_before = balance_before,
        balance_after  = balance_after,
        received_by    = received_by,
        record_sn      = record.sn,
        week_start     = record.week_start,
        is_reprint     = is_reprint,
    )

    safe_name = student_name.replace(' ', '_').replace('/', '-')
    filename  = f"receipt_{record.sn}_{safe_name}.pdf"
    return FileResponse(buf, as_attachment=True,
                        filename=filename, content_type='application/pdf')


@accountant_required
def class_statements_pdf(request):
    """
    One PDF for an entire class:
      GET /finance/records/class/pdf/?session=X&term=Y&class=JSS2A
    """
    user_school = request.user.school
    if user_school is None:
        raise PermissionDenied("No school assigned.")

    session_id   = request.GET.get('session')
    term_id      = request.GET.get('term')
    class_filter = request.GET.get('class')

    if not (session_id and term_id and class_filter):
        raise PermissionDenied("Missing session, term, or class.")

    from django.contrib.auth import get_user_model
    User = get_user_model()

    students = (User.objects
                .filter(school=user_school, student_class=class_filter)
                .order_by('first_name', 'last_name'))

    students_data = []
    for s in students:
        records = list(
            FinanceRecord.objects
            .filter(school=user_school,
                    student_id=s.id,
                    session_id=session_id,
                    term_id=term_id)
            .select_related('session', 'term')
            .order_by('week_start', 'sn')
        )
        if not records:
            continue

        students_data.append({
            'student_name':  f"{s.first_name or ''} {s.last_name or ''}".strip() or 'Student',
            'student_class': s.student_class or '—',
            'admission_no':  s.admission_no or '—',
            'records':       records,
        })

    if not students_data:
        raise PermissionDenied("No records found for this class.")

    session_obj = Session.objects.filter(pk=session_id).first()
    term_obj    = Term.objects.filter(pk=term_id).first()

    buf = build_class_statements_pdf(
        school_name   = str(user_school),
        class_name    = class_filter,
        session_name  = str(session_obj) if session_obj else '—',
        term_name     = str(term_obj)    if term_obj    else '—',
        students_data = students_data,
    )

    safe_class = class_filter.replace(' ', '_').replace(',', '').replace('/', '-')
    filename   = f"class_{safe_class}_{session_id}_{term_id}.pdf"
    return FileResponse(buf, as_attachment=True,
                        filename=filename, content_type='application/pdf')