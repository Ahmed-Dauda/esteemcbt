from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.contrib.auth import get_user_model

from .models import FinanceRecord, Session, Term
from quiz.models import School

User = get_user_model()


# ----------------------------------------------------------------------
# Widget that scopes the lookup by the row's "school" value
# ----------------------------------------------------------------------

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.contrib.auth import get_user_model
from .models import FinanceRecord
from sms.models import Session, Term
from student.models import School   # or wherever your School model lives


User = get_user_model()


import logging
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.contrib.auth import get_user_model

from .models import FinanceRecord
from sms.models import Session, Term
from student.models import School   # adjust import path if needed

User = get_user_model()
logger = logging.getLogger('finance.import')


# ------------------------------------------------------------------
# Widgets
# ------------------------------------------------------------------
class SchoolScopedFKWidget(ForeignKeyWidget):
    """FK widget scoped to the row's school, whitespace/case tolerant."""
    def get_queryset(self, value, row, *args, **kwargs):
        qs = super().get_queryset(value, row, *args, **kwargs)
        school_name = (row.get('school') or '').strip()
        if school_name:
            qs = qs.filter(school__school_name__iexact=school_name)
        return qs

    def clean(self, value, row=None, *args, **kwargs):
        if value is None or value == '':
            return None
        value = str(value).strip()
        qs = self.get_queryset(value, row, *args, **kwargs)

        obj = qs.filter(**{self.field: value}).first()
        if obj is None:
            obj = qs.filter(**{f"{self.field}__iexact": value}).first()
        if obj is None:
            raise ValueError(
                f"No {self.model.__name__} with {self.field}={value!r} "
                f"for school {row.get('school')!r}."
            )
        return obj


class ScopedAutoCreateUserWidget(ForeignKeyWidget):
    """
    Accountant-provided username from the file.
      - exists under this school        -> use it
      - doesn't exist anywhere          -> create under this school
      - exists under a DIFFERENT school -> reject with clear error
    """
    def clean(self, value, row=None, **kwargs):
        if not value or not str(value).strip():
            return None
        username = str(value).strip()

        request = kwargs.get('request')
        school = getattr(request.user, 'school', None) if request else None
        if school is None:
            raise ValueError(f"Cannot resolve {username!r}: importer has no school.")

        # 1. Exists under THIS school? Use it (re-import case)
        obj = (
            User.objects.filter(school=school, username=username).first()
            or User.objects.filter(school=school, username__iexact=username).first()
        )
        if obj is not None:
            return obj

        # 2. Exists globally under a DIFFERENT school? Reject.
        conflict = User.objects.filter(username__iexact=username).first()
        if conflict is not None:
            raise ValueError(
                f"Username {username!r} already exists under "
                f"{conflict.school!r}. Please choose a different username."
            )

        # 3. Create it under this school
        names = (row.get('names') or '').strip()
        parts = names.split(None, 1)
        first_name = parts[0] if parts else ''
        last_name  = parts[1] if len(parts) > 1 else ''

        slug = ''.join(c for c in school.school_name.lower() if c.isalnum()) or 'school'
        email = f"{username.lower()}@{slug}.local"
        if User.objects.filter(email=email).exists():
            email = f"{username.lower()}+{school.id}@{slug}.local"

        new_user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            student_class=row.get('student_class') or 'NA',
            school=school,
            is_active=False,
        )
        logger.info("Auto-created user %r under school %r", username, school)
        return new_user


# ------------------------------------------------------------------
# Resource
# ------------------------------------------------------------------
class FinanceRecordResource(resources.ModelResource):
    student = fields.Field(
        column_name='username',
        attribute='student',
        widget=ScopedAutoCreateUserWidget(User, field='username'),
    )
    school = fields.Field(
        column_name='school',
        attribute='school',
        widget=ForeignKeyWidget(School, field='school_name'),
    )
    session = fields.Field(
        column_name='session',
        attribute='session',
        widget=SchoolScopedFKWidget(Session, field='name'),
    )
    term = fields.Field(
        column_name='term',
        attribute='term',
        widget=SchoolScopedFKWidget(Term, field='name'),
    )
    week_start = fields.Field(
        column_name='week_start',
        attribute='week_start',
        widget=DateWidget(format='%Y-%m-%d'),
    )

    class Meta:
        model = FinanceRecord
        fields = (
            'student',              # exported as "username"
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
            'sn',                   # hidden identity — last column
        )
        export_order = fields
        import_id_fields = ('sn',)  # match by sn when present
        skip_unchanged = True
        report_skipped = False

    # ------------------------------------------------------------------
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        FinanceRecord._skip_cascade = True

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        FinanceRecord._skip_cascade = False

    # ------------------------------------------------------------------
    def before_import_row(self, row, **kwargs):
        from datetime import datetime as _dt, date as _date

        # ---- Normalize header keys IN PLACE (do NOT rebind row) ----
        for k in list(row.keys()):
            cleaned = str(k).strip().lower()
            if k != cleaned:
                row[cleaned] = row.pop(k)

        row_number = kwargs.get('row_number', '?')

        # ---- Normalize sn ----
        sn_val = row.get('sn')
        if sn_val in (None, '', 'None'):
            row.pop('sn', None)
        else:
            try:
                row['sn'] = int(str(sn_val).strip())
            except (ValueError, TypeError):
                row.pop('sn', None)

        # ---- Force importer's school ----
        request = kwargs.get('request')
        importer_school = getattr(request.user, 'school', None) if request else None
        if importer_school:
            row['school'] = importer_school.school_name

        # ---- Whitespace cleanup on text values ----
        for f in ('session', 'term', 'username', 'names', 'student_class'):
            if row.get(f):
                row[f] = str(row[f]).strip()

        # ---- Reject rows with no names AND no username ----
        names    = (row.get('names') or '').strip()
        username = (row.get('username') or '').strip()
        if not names and not username:
            raise ValueError(
                f"Row {row_number}: no 'names' and no 'username'. "
                f"Values: names={row.get('names')!r}, username={row.get('username')!r}"
            )

        # ---- Natural-key fallback ----
        if not row.get('sn') and importer_school:
            week      = row.get('week_start')
            sess_name = (row.get('session') or '').strip()
            term_name = (row.get('term') or '').strip()

            if username and week and sess_name and term_name:
                student = (
                    User.objects.filter(school=importer_school, username=username).first()
                    or User.objects.filter(username=username).first()
                )
                session = (
                    Session.objects.filter(school=importer_school, name__iexact=sess_name).first()
                    or Session.objects.filter(name__iexact=sess_name).first()
                )
                term = (
                    Term.objects.filter(school=importer_school, name__iexact=term_name).first()
                    or Term.objects.filter(name__iexact=term_name).first()
                )

                # Normalize week_start to a date
                week_dt = None
                if isinstance(week, _dt):
                    week_dt = week.date()
                elif isinstance(week, _date):
                    week_dt = week
                elif isinstance(week, str):
                    for fmt in ('%Y-%m-%d', '%d %b %Y', '%d/%m/%Y',
                                '%Y/%m/%d', '%d-%m-%Y', '%m/%d/%Y'):
                        try:
                            week_dt = _dt.strptime(week.strip(), fmt).date()
                            break
                        except ValueError:
                            continue

                logger.info(
                    "Fallback: user=%r week=%r(type %s) session=%r term=%r "
                    "| student=%s session=%s term=%s",
                    username, week, type(week).__name__, sess_name, term_name,
                    student, session, term,
                )

                if student and session and term and week_dt:
                    existing = FinanceRecord.objects.filter(
                        student=student,
                        week_start=week_dt,
                        session=session,
                        term=term,
                    ).first()
                    if existing:
                        row['sn'] = existing.sn
                        logger.info("Fallback MATCH sn=%s — updating", existing.sn)
                    else:
                        logger.info(
                            "Fallback: no match for student=%s week=%s session=%s term=%s",
                            student, week_dt, session, term,
                        )
                        
                    # ------------------------------------------------------------------
    def before_save_instance(self, instance, using_transactions, dry_run):
        # ---- names is NOT NULL — never let it be None/empty ----
        if not instance.names:
            if instance.student:
                full = (
                    f"{instance.student.first_name or ''} "
                    f"{instance.student.last_name or ''}"
                ).strip()
                instance.names = full or instance.student.username or 'Unknown'
            else:
                instance.names = 'Unknown'

        # ---- student_class defaults ----
        if not instance.student_class or instance.student_class == 'NA':
            if instance.student and instance.student.student_class:
                instance.student_class = instance.student.student_class
            else:
                instance.student_class = 'NA'


# class FinanceRecordResource(resources.ModelResource):
#     student = fields.Field(
#         column_name='student',
#         attribute='student',
#         widget=ForeignKeyWidget(User, field='admission_no'),
#     )
#     school = fields.Field(
#         column_name='school',
#         attribute='school',
#         widget=ForeignKeyWidget(School, field='school_name'),
#     )
#     session = fields.Field(
#         column_name='session',
#         attribute='session',
#         widget=ForeignKeyWidget(Session, field='name'),   # 👈 scoped
#     )
#     term = fields.Field(
#         column_name='term',
#         attribute='term',
#         widget=SchoolScopedFKWidget(Term, field='name'),      # 👈 scoped
#     )
#     week_start = fields.Field(
#         column_name='week_start',
#         attribute='week_start',
#         widget=DateWidget(format='%Y-%m-%d'),
#     )

#     class Meta:
#         model = FinanceRecord
#         fields = (
#             'sn',
#             'student',
#             'names',
#             'student_class',
#             'school',
#             'session',
#             'term',
#             'week_start',
#             'initial_total_deposit',
#             'school_shop',
#             'caps',
#             'haircut',
#             'others',
#             'note',
#             'total_deposit',
#             'total_expense',
#             'balance_brought_forward',
#             'current_balance',
#             'status',
#         )
#         export_order = fields
#         import_id_fields = ('sn',)
#         skip_unchanged = True
#         report_skipped = False
  
#     # ------------------------------------------------------------------
#     # Turn off the save() cascade for the whole import — huge speedup
#     # ------------------------------------------------------------------
#     def before_import(self, dataset, using_transactions, dry_run, **kwargs):
#         FinanceRecord._skip_cascade = True

#     def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
#         FinanceRecord._skip_cascade = False

#     def before_import_row(self, row, **kwargs):
#         """Set school from the logged-in user, so the scoped widget can find terms."""
#         request = kwargs.get('request')
#         if request and getattr(request.user, 'school', None):
#             row['school'] = str(request.user.school)

#     def before_save_instance(self, instance, using_transactions, dry_run):
#         """Auto-fill names + student_class from the student."""
#         if instance.student:
#             if not instance.names:
#                 instance.names = (
#                     f"{instance.student.first_name or ''} "
#                     f"{instance.student.last_name or ''}"
#                 ).strip()
#             if not instance.student_class or instance.student_class == 'NA':
#                 instance.student_class = instance.student.student_class or 'NA'