from decimal import Decimal
from django.db.models import Max
from django.conf import settings
from django.db import models
from django.db.models import F, Q

from quiz.models import School
from sms.models import Session, Term



class FinanceRecord(models.Model):
    STATUS_CHOICES = [
        ('exhausted', 'Exhausted'),
        ('remaining', 'Remaining'),
    ]

    # Class-level flag: when True, save() skips the forward re-cascade.
    # Set to True during bulk import, False afterwards.
    _skip_cascade = False

    # ---- identity ----
    sn            = models.AutoField(primary_key=True)
    student       = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name='finance_records',
                        db_index=True,
                    )
    names         = models.CharField(max_length=100, db_index=True)
    student_class = models.CharField(max_length=100, default='NA',
                                     blank=True, null=True, db_index=True)

    # ---- scope ----
    school  = models.ForeignKey(School,  on_delete=models.SET_NULL,
                                related_name='financerecord',
                                blank=True, null=True, db_index=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL,
                                blank=True, null=True, db_index=True)
    term    = models.ForeignKey(Term,    on_delete=models.SET_NULL,
                                blank=True, null=True, db_index=True)

    # ---- weekly anchor ----
    week_start = models.DateField(
                    null=True, blank=True, db_index=True,
                    help_text="Date this school week started (e.g. Monday).",
                 )

    # ---- money in ----
    initial_total_deposit = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    total_deposit  = models.DecimalField(max_digits=10, decimal_places=1,
                                                default=0, blank=True, null=True, db_index=True)
    # ---- money out ----
    school_shop = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    caps        = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    haircut     = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)
    others      = models.DecimalField(max_digits=10, decimal_places=1, default=0, blank=True, null=True)

    # ---- computed ----
    total_expense           = models.DecimalField(max_digits=10, decimal_places=1, editable=False, default=0)
    current_balance         = models.DecimalField(max_digits=10, decimal_places=1, editable=False, default=0)
    balance_brought_forward = models.DecimalField(max_digits=10, decimal_places=1,
                                                  blank=True, null=True, default=0)
    note                    = models.TextField(blank=True, null=True)
    status                  = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                               default='remaining', db_index=True)
    # ---- audit trail ----
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='finance_created',
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='finance_updated',
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        ordering = ['names', 'session', 'term__order', 'week_start', 'sn']
        indexes = [
        # existing
        models.Index(fields=['school', 'session', 'term', 'names']),
        models.Index(fields=['student', 'session', 'term']),
        models.Index(fields=['school', 'week_start']),

        # ADD THESE
        models.Index(fields=['school', 'status']),               # exhausted alert
        models.Index(fields=['school', 'session', 'term', 'week_start']),  # summary
        models.Index(fields=['-sn']),                            # latest lookup
    ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _d(v):
        return Decimal(str(v or 0))

    def compute_expense(self):
        return (
            self._d(self.school_shop) +
            self._d(self.caps) +
            self._d(self.haircut) +
            self._d(self.others)
        )

    def _siblings_in_session(self):
        """All rows for this student in the same session, chronological."""
        return (FinanceRecord.objects
                .filter(student_id=self.student_id,
                        session_id=self.session_id)
                .order_by('term__order',
                          F('week_start').asc(nulls_first=True),
                          'sn'))

    def _previous_term_record(self):
        """Last row for this student in ANY earlier term of ANY earlier session."""
        if not self.term_id:
            return None
        return (FinanceRecord.objects
                .filter(student_id=self.student_id)
                .exclude(pk=self.pk)
                .filter(
                    Q(session_id__lt=self.session_id) |
                    Q(session_id=self.session_id,
                      term__order__lt=self.term.order)
                )
                .order_by('-session_id', '-term__order', '-week_start', '-sn')
                .first())

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        # Capture force_insert so it doesn't get applied to the SECOND save
        force_insert = kwargs.pop('force_insert', False)

        # ---- Force-assign sn when creating a new row ----
        if self.sn is None:
            max_sn = FinanceRecord.objects.aggregate(m=Max('sn'))['m'] or 0
            self.sn = max_sn + 1

        # 1) expense from raw fields
        self.initial_total_deposit = self._d(self.initial_total_deposit)
        self.total_expense         = self.compute_expense()

        # 2) FIRST save — insert only if we were told to force_insert,
        #    otherwise a normal save (which will UPDATE if pk is set)
        if force_insert:
            super().save(*args, force_insert=True, **kwargs)
        else:
            super().save(*args, **kwargs)

        # 3) if scope is incomplete, skip the ledger math
        if not all([self.student_id, self.school_id, self.session_id, self.term_id]):
            return

        # 4) find the previous row in the SAME term
        prev_qs = self._siblings_in_session().exclude(pk=self.pk)
        if self.week_start:
            prev = prev_qs.filter(term_id=self.term_id,
                                  week_start__lte=self.week_start).last()
        else:
            prev = prev_qs.filter(term_id=self.term_id, sn__lt=self.sn).last()

        # 5) if none, carry forward from previous term (any earlier session)
        if prev is None:
            prev_term_row = self._previous_term_record()
            self.balance_brought_forward = (
                prev_term_row.current_balance if prev_term_row else Decimal('0')
            )
        else:
            self.balance_brought_forward = prev.current_balance

        # 6) totals
        self.total_deposit   = self.initial_total_deposit + self._d(self.balance_brought_forward)
        self.current_balance = self.total_deposit - self.total_expense
        self.status          = 'exhausted' if self.current_balance <= 0 else 'remaining'

        # 7) SECOND save — plain UPDATE (no force_insert)
        super().save(*args, **kwargs)

        # 8) re-cascade everything after this row — unless we're bulk-importing
        if not self._skip_cascade:
            self._recompute_following()

        # 2) save once to get a pk (needed to exclude self later)
        super().save(*args, **kwargs)

        # 3) if scope is incomplete, skip the ledger math
        if not all([self.student_id, self.school_id, self.session_id, self.term_id]):
            return

        # 4) find the previous row in the SAME term
        prev_qs = self._siblings_in_session().exclude(pk=self.pk)
        if self.week_start:
            prev = prev_qs.filter(term_id=self.term_id,
                                  week_start__lte=self.week_start).last()
        else:
            prev = prev_qs.filter(term_id=self.term_id, sn__lt=self.sn).last()

        # 5) if none, carry forward from previous term (any earlier session)
        if prev is None:
            prev_term_row = self._previous_term_record()
            self.balance_brought_forward = (
                prev_term_row.current_balance if prev_term_row else Decimal('0')
            )
        else:
            self.balance_brought_forward = prev.current_balance

        # 6) totals
        self.total_deposit   = self.initial_total_deposit + self._d(self.balance_brought_forward)
        self.current_balance = self.total_deposit - self.total_expense
        self.status          = 'exhausted' if self.current_balance <= 0 else 'remaining'

        super().save(*args, **kwargs)

        # 7) re-cascade everything after this row — unless we're bulk-importing
        if not self._skip_cascade:
            self._recompute_following()

    def _recompute_following(self):
        """Walk forward through all later rows for this student+session and
        rewrite BBF / totals / status. Uses .update() so save() isn't re-fired."""
        running = self.current_balance

        later = (FinanceRecord.objects
                 .filter(student_id=self.student_id, session_id=self.session_id)
                 .exclude(pk=self.pk)
                 .filter(
                     Q(term__order__gt=self.term.order) |
                     Q(term__order=self.term.order,
                       week_start__gt=self.week_start) |
                     Q(term__order=self.term.order,
                       week_start=self.week_start,
                       sn__gt=self.sn)
                 )
                 .order_by('term__order',
                           F('week_start').asc(nulls_first=True),
                           'sn'))

        for row in later:
            expense     = row.compute_expense()
            new_bbf     = running
            new_total   = row._d(row.initial_total_deposit) + new_bbf
            new_balance = new_total - expense
            new_status  = 'exhausted' if new_balance <= 0 else 'remaining'

            FinanceRecord.objects.filter(pk=row.pk).update(
                total_expense           = expense,
                balance_brought_forward = new_bbf,
                total_deposit           = new_total,
                current_balance         = new_balance,
                status                  = new_status,
            )
            running = new_balance

    def __str__(self):
        return f"{self.names} — {self.term} (wk {self.week_start})"
    