from django.db import models

# Create your models here.
from quiz.models import School, Session, Term

from django.db import models
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from django.core.exceptions import ObjectDoesNotExist

from django.core.exceptions import ObjectDoesNotExist

from django.db import models
from django.core.exceptions import ValidationError

from decimal import Decimal

from decimal import Decimal

from django.db import models
from decimal import Decimal

from django.db import models
from decimal import Decimal


class FinanceRecord(models.Model):
    STATUS_CHOICES = [
        ('exhausted', 'Exhausted'),
        ('remaining', 'Remaining'),
    ]
    
    sn = models.AutoField(primary_key=True)
    names = models.CharField(max_length=100)
    student_class = models.CharField(max_length=100, default='NA', blank=True, null=True)
    initial_total_deposit = models.DecimalField(max_digits=10, decimal_places=1)
    total_deposit = models.DecimalField(max_digits=10, decimal_places=1)
    # initial_total_deposit = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    # total_deposit = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='financerecord', blank=True, null=True, db_index=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    school_shop = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    caps = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    haircut = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    others = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    total_expense = models.DecimalField(max_digits=10, decimal_places=1, editable=False, default=0)
    current_balance = models.DecimalField(max_digits=10, decimal_places=1, editable=False, default=0)
    balance_brought_forward = models.DecimalField(max_digits=10, decimal_places=1, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='remaining', db_index=True)

    def save(self, *args, **kwargs):
        # Ensure all relevant fields have default values if they are None
        self.initial_total_deposit = self.initial_total_deposit or Decimal('0')
        self.total_deposit = self.total_deposit or Decimal('0')
        self.total_expense = (
            (self.school_shop or Decimal('0')) +
            (self.caps or Decimal('0')) +
            (self.haircut or Decimal('0')) +
            (self.others or Decimal('0'))
        )

        # Adjust total_deposit if initial_total_deposit has been changed
        if self.pk:
            # Fetch the previous instance to compare initial_total_deposit
            previous_record = FinanceRecord.objects.get(pk=self.pk)
            previous_initial_total_deposit = previous_record.initial_total_deposit or Decimal('0')
            
            # Calculate difference and adjust total_deposit
            difference = self.initial_total_deposit - previous_initial_total_deposit
            self.total_deposit += difference

        # Calculate current balance as total_deposit - total_expense
        self.current_balance = self.total_deposit - self.total_expense

        # Add balance_brought_forward to total_deposit only on first save
        if not self.pk:
            if self.session and self.term:
                previous_record = self._get_previous_record()
                if previous_record:
                    self.total_deposit += previous_record.current_balance

        # Set balance_brought_forward for the current record
        self.balance_brought_forward = self.current_balance

        # Update status based on current_balance
        self.status = 'exhausted' if self.current_balance <= 0 else 'remaining'

        super().save(*args, **kwargs)

    def _get_previous_record(self):
        term_order = ['FIRST', 'SECOND', 'THIRD']
        current_term_index = term_order.index(self.term.name)

        if current_term_index > 0:
            previous_term_name = term_order[current_term_index - 1]
            return FinanceRecord.objects.filter(
                names=self.names,
                school=self.school,
                session=self.session,
                term__name=previous_term_name
            ).order_by('-pk').first()
        else:
            previous_session_name = self._get_previous_session_name(self.session.name)
            if previous_session_name:
                return FinanceRecord.objects.filter(
                    names=self.names,
                    school=self.school,
                    session__name=previous_session_name,
                    term__name='THIRD'
                ).order_by('-pk').first()
        return None

    def _get_previous_session_name(self, current_session_name):
        try:
            start_year, end_year = map(int, current_session_name.split('-'))
            previous_start_year = start_year - 1
            previous_end_year = end_year - 1
            return f"{previous_start_year}-{previous_end_year}"
        except (ValueError, TypeError):
            return None

    def __str__(self):
        return f"{self.sn} - {self.names}"


# class FinanceRecord(models.Model):
#     STATUS_CHOICES = [
#         ('exhausted', 'Exhausted'),
#         ('remaining', 'Remaining'),
#     ]
    
#     sn = models.AutoField(primary_key=True)
#     names = models.CharField(max_length=100)
#     student_class = models.CharField(max_length=100, default='NA', blank=True, null=True)
#     total_deposit = models.DecimalField(max_digits=10, decimal_places=2)
#     initial_total_deposit = models.DecimalField(max_digits=10, decimal_places=2, editable=True, blank=True, null=True)
#     school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='financerecord', blank=True, null=True)
#     session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
#     term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True)
#     school_shop = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     caps = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     haircut = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     others = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     total_expense = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     current_balance = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     balance_brought_forward = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     note = models.TextField(blank=True, null=True)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='remaining')

#     def save(self, *args, **kwargs):
#         # Calculate total_expense based on individual expenses
#         self.total_expense = (
#             (self.school_shop or 0) +
#             (self.caps or 0) +
#             (self.haircut or 0) +
#             (self.others or 0)
#         )

#         # Calculate current_balance as the difference between total_deposit and total_expense
#         self.current_balance = self.total_deposit - self.total_expense

#         # Store the initial_total_deposit (before balance_brought_forward is added)
#         if not self.initial_total_deposit:
#             self.initial_total_deposit = self.total_deposit

#         # Determine the previous record for balance_brought_forward
#         if self.session and self.term and self.names:
#             # Get the previous term or previous session’s last term balance to add to total_deposit
#             previous_record = self._get_previous_record()

#             if previous_record:
#                 # Add the previous balance_brought_forward to the current total_deposit
#                 self.total_deposit += previous_record.current_balance

#         # Set the balance_brought_forward for the current record
#         self.balance_brought_forward = self.current_balance

#         # Update status based on current_balance
#         if self.current_balance <= 0:
#             self.status = 'exhausted'
#         else:
#             self.status = 'remaining'

#         super().save(*args, **kwargs)

#     def _get_previous_record(self):
#         """Helper function to get the previous term's or session's record."""
#         # Define term ordering to get the previous term
#         term_order = ['FIRST', 'SECOND', 'THIRD']
#         current_term_index = term_order.index(self.term.name)

#         if current_term_index > 0:
#             # If not the first term, get the previous term within the same session
#             previous_term_name = term_order[current_term_index - 1]
#             return FinanceRecord.objects.filter(
#                 names=self.names,
#                 school=self.school,
#                 session=self.session,
#                 term__name=previous_term_name
#             ).order_by('-pk').first()
#         else:
#             # If the first term, get the last term of the previous session
#             previous_session_name = self._get_previous_session_name(self.session.name)
#             if previous_session_name:
#                 return FinanceRecord.objects.filter(
#                     names=self.names,
#                     school=self.school,
#                     session__name=previous_session_name,
#                     term__name='THIRD'
#                 ).order_by('-pk').first()
#         return None

#     def _get_previous_session_name(self, current_session_name):
#         """Helper function to find the previous session name based on the current session."""
#         try:
#             start_year, end_year = map(int, current_session_name.split('-'))
#             previous_start_year = start_year - 1
#             previous_end_year = end_year - 1
#             return f"{previous_start_year}-{previous_end_year}"
#         except (ValueError, TypeError):
#             return None

#     def __str__(self):
#         return f"{self.sn} - {self.names}"



# class FinanceRecord(models.Model):
#     STATUS_CHOICES = [
#         ('exhausted', 'Exhausted'),
#         ('remaining', 'Remaining'),
#     ]
    
#     sn = models.AutoField(primary_key=True)
#     names = models.CharField(max_length=100)
#     student_class = models.CharField(max_length=100, default='NA', blank=True, null=True)
#     total_deposit = models.DecimalField(max_digits=10, decimal_places=2)
#     school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='financerecord', blank=True, null=True)
#     session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
#     term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True)
#     school_shop = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     caps = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     haircut = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     others = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
#     total_expense = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     current_balance = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     balance_brought_forward = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     note = models.TextField(blank=True, null=True)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='remaining')

#     def save(self, *args, **kwargs):
#         # Calculate total_expense based on individual expenses
#         self.total_expense = (
#             (self.school_shop or 0) +
#             (self.caps or 0) +
#             (self.haircut or 0) +
#             (self.others or 0)
#         )

#         # Calculate current_balance as the difference between total_deposit and total_expense
#         self.current_balance = self.total_deposit - self.total_expense

#         # Only add previous balance_brought_forward to total_deposit if the record is being created (not updated)
#         if self.pk is None and self.session and self.term and self.names:
#             previous_record = self._get_previous_record()

#             if previous_record:
#                 # Add the previous balance_brought_forward to the current total_deposit
#                 self.total_deposit += previous_record.current_balance

#         # Set the balance_brought_forward for the current record
#         self.balance_brought_forward = self.current_balance

#         # Update status based on current_balance
#         if self.current_balance <= 0:
#             self.status = 'exhausted'
#         else:
#             self.status = 'remaining'

#         super().save(*args, **kwargs)

#     def _get_previous_record(self):
#         """Helper function to get the previous term's or session's record."""
#         term_order = ['FIRST', 'SECOND', 'THIRD']
#         current_term_index = term_order.index(self.term.name)

#         if current_term_index > 0:
#             # If not the first term, get the previous term within the same session
#             previous_term_name = term_order[current_term_index - 1]
#             return FinanceRecord.objects.filter(
#                 names=self.names,
#                 school=self.school,
#                 session=self.session,
#                 term__name=previous_term_name
#             ).order_by('-pk').first()
#         else:
#             # If the first term, get the last term of the previous session
#             previous_session_name = self._get_previous_session_name(self.session.name)
#             if previous_session_name:
#                 return FinanceRecord.objects.filter(
#                     names=self.names,
#                     school=self.school,
#                     session__name=previous_session_name,
#                     term__name='THIRD'
#                 ).order_by('-pk').first()
#         return None

#     def _get_previous_session_name(self, current_session_name):
#         """Helper function to find the previous session name based on the current session."""
#         try:
#             start_year, end_year = map(int, current_session_name.split('-'))
#             previous_start_year = start_year - 1
#             previous_end_year = end_year - 1
#             return f"{previous_start_year}-{previous_end_year}"
#         except (ValueError, TypeError):
#             return None

#     def __str__(self):
#         return f"{self.sn} - {self.names}"
  

# class FinanceRecord(models.Model):
#     STATUS_CHOICES = [
#         ('exhausted', 'Exhausted'),
#         ('remaining', 'Remaining'),
#     ]
    
#     sn = models.AutoField(primary_key=True)
#     names = models.CharField(max_length=100)
#     student_class = models.CharField(max_length=100, default='NA', blank=True, null=True)
#     total_deposit = models.DecimalField(max_digits=10, decimal_places=2)
#     school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='financerecord', blank=True, null=True)
#     session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)  # ForeignKey to Session model
#     term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True)  # Adding index
#     school_shop = models.DecimalField(max_digits=10, decimal_places=2,default =0, blank=True, null=True)
#     caps = models.DecimalField(max_digits=10, decimal_places=2,default =0, blank=True, null=True)
#     haircut = models.DecimalField(max_digits=10, decimal_places=2,default =0, blank=True, null=True)
#     others = models.DecimalField(max_digits=10, decimal_places=2,default =0, blank=True, null=True)
#     total_expense = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     current_balance = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     balance_brought_forward = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     note = models.TextField(blank=True, null=True)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='remaining')

#     def save(self, *args, **kwargs):
#         # Calculate total_expense based on individual expenses
#         self.total_expense = (
#             (self.school_shop or 0) +
#             (self.caps or 0) +
#             (self.haircut or 0) +
#             (self.others or 0)
#         )
        
#         # Calculate current_balance as the difference between total_deposit and total_expense
#         self.current_balance = self.total_deposit - self.total_expense
#         self.balance_brought_forward = self.total_deposit - self.total_expense

#         # Update status based on current_balance being <= total_deposit
#         if self.current_balance <= 0 or  self.current_balance == self.total_deposit:  # This handles both zero and negative balances
#             self.status = 'exhausted'
#         else:  # If current balance is greater than total_deposit
#             self.status = 'remaining'

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.sn} - {self.names}"

