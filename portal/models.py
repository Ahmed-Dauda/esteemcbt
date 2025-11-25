from django.db import models
from django.utils import timezone
from decimal import Decimal
from quiz.models import School
from sms.models import Courses, Session, Term
from teacher.models import Teacher
from users.models import NewUser


from django.utils import timezone

class SchoolSubscription(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="subscription")

    cbt_active = models.BooleanField(default=False)
    report_card_active = models.BooleanField(default=False)

    cbt_expiry = models.DateField(null=True, blank=True)
    report_card_expiry = models.DateField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription for {self.school.school_name}"

    def is_cbt_valid(self):
        today = timezone.localdate()
        return self.cbt_active and (self.cbt_expiry is None or self.cbt_expiry >= today)

    def is_report_card_valid(self):
        today = timezone.localdate()
        return self.report_card_active and (self.report_card_expiry is None or self.report_card_expiry >= today)


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=School)
def create_school_subscription(sender, instance, created, **kwargs):
    if created:
        SchoolSubscription.objects.create(school=instance)


class Result_Portal(models.Model):
    student = models.ForeignKey(
        NewUser, on_delete=models.CASCADE, related_name="results", db_index=True
    )
    subject = models.ForeignKey(
        Courses, on_delete=models.CASCADE, db_index=True
    )
    schools = models.ForeignKey(
        School, on_delete=models.SET_NULL, related_name='portalschool',
        blank=True, null=True, db_index=True
    )

    result_class = models.CharField(max_length=300, blank=True, null=True, db_index=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, db_index=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, db_index=True)

    # --- Score Fields ---
    ca_score = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    midterm_score = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    exam_score = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    total_score = models.DecimalField(max_digits=5, decimal_places=0, default=0, editable=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'term', 'session']),
            models.Index(fields=['student', 'subject', 'term', 'session']),
            models.Index(fields=['result_class', 'session', 'term']),
            models.Index(fields=['subject', 'session', 'term']),
        ]
        unique_together = ('student', 'subject', 'term', 'session')
        ordering = ['subject__title']

    def __str__(self):
        return f"{self.student.username} - {self.subject.title} ({self.term.name}, {self.session.name})"

    # --- Properties to get max marks from school ---
    @property
    def MAX_CA(self):
        return self.schools.max_ca_score if self.schools and self.schools.max_ca_score is not None else Decimal('10')

    @property
    def MAX_MIDTERM(self):
        return self.schools.max_midterm_score if self.schools and self.schools.max_midterm_score is not None else Decimal('30')

    @property
    def MAX_EXAM(self):
        return self.schools.max_exam_score if self.schools and self.schools.max_exam_score is not None else Decimal('60')

    def save(self, *args, **kwargs):
        """Compute normalized total_score and auto-fill result_class from student profile if missing."""

        # --- Auto-fill result_class from student's profile ---
        if not self.result_class and hasattr(self.student, 'student_class'):
            self.result_class = self.student.student_class

        # --- Total Score Calculation ---
        ca = float(self.ca_score or 0)
        mid = float(self.midterm_score or 0)
        exam = float(self.exam_score or 0)

        total_raw = 0
        total_max = 0

        if ca > 0:
            total_raw += ca
            total_max += float(self.MAX_CA)
        if mid > 0:
            total_raw += mid
            total_max += float(self.MAX_MIDTERM)
        if exam > 0:
            total_raw += exam
            total_max += float(self.MAX_EXAM)

        if total_max > 0:
            normalized_total = (total_raw / total_max) * 100
            self.total_score = Decimal(normalized_total).quantize(Decimal('0.01'))
        else:
            self.total_score = Decimal('0.0')

        super().save(*args, **kwargs)

    # --- Grade Calculation using School Grading System ---
    @property
    def grade_letter(self):
        """Return the grade letter based on normalized total_score using school's grading system."""
        if self.total_score is None or not self.schools:
            return None

        score = float(self.total_score)
        school = self.schools

        if school.A_min <= score <= school.A_max:
            return 'A'
        elif school.B_min <= score <= school.B_max:
            return 'B'
        elif school.C_min <= score <= school.C_max:
            return 'C'
        elif school.P_min <= score <= school.P_max:
            return 'P'
        elif school.F_min <= score <= school.F_max:
            return 'F'
        return None

    @property
    def remark(self):
        """Return remark corresponding to the grade letter based on school's comments."""
        letter = self.grade_letter
        if letter is None or not self.schools:
            return None

        school = self.schools

        return {
            'A': school.A_comment,
            'B': school.B_comment,
            'C': school.C_comment,
            'P': school.P_comment,
            'F': school.F_comment,
        }.get(letter, 'N/A')


class StudentBehaviorRecord(models.Model):
    student = models.ForeignKey(NewUser, on_delete=models.CASCADE, db_index=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, db_index=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, db_index=True)

    # Use string reference to Teacher to avoid load order issues
    form_teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'form_teacher_role': 'form_teacher'},
        related_name='behavior_records'
    )
    form_teacher_comment = models.TextField(blank=True, null=True)
    principal_comment = models.TextField(blank=True, null=True)

    # Psychomotor
    handwriting = models.IntegerField(default=0)
    games = models.IntegerField(default=0)
    sports = models.IntegerField(default=0)
    drawing_painting = models.IntegerField(default=0)
    crafts = models.IntegerField(default=0)

    # Affective
    punctuality = models.IntegerField(default=0)
    attendance = models.IntegerField(default=0)
    reliability = models.IntegerField(default=0)
    neatness = models.IntegerField(default=0)
    politeness = models.IntegerField(default=0)
    honesty = models.IntegerField(default=0)
    relationship_with_students = models.IntegerField(default=0)
    self_control = models.IntegerField(default=0)
    attentiveness = models.IntegerField(default=0)
    perseverance = models.IntegerField(default=0)

    class Meta:
        unique_together = ('student', 'term', 'session')

    def __str__(self):
        return f"{self.student} - {self.term} - {self.session}"




# from django.db import models
# from django.utils import timezone
# from decimal import Decimal
# from quiz.models import School
# from sms.models import Courses, Session, Term
# from users.models import NewUser


# class Result_Portal(models.Model):
#     student = models.ForeignKey(
#         NewUser, on_delete=models.CASCADE, related_name="results", db_index=True
#     )
#     subject = models.ForeignKey(
#         Courses, on_delete=models.CASCADE, db_index=True
#     )
#     schools = models.ForeignKey(
#         School, on_delete=models.SET_NULL, related_name='portalschool',
#         blank=True, null=True, db_index=True
#     )

#     result_class = models.CharField(max_length=300, blank=True, null=True, db_index=True)
#     term = models.ForeignKey(Term, on_delete=models.CASCADE, db_index=True)
#     session = models.ForeignKey(Session, on_delete=models.CASCADE, db_index=True)

#     # --- Score Fields ---
#     ca_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
#     midterm_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
#     exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
#     total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, editable=False)
#     created_at = models.DateTimeField(default=timezone.now)

#     class Meta:
#         indexes = [
#             models.Index(fields=['student', 'term', 'session']),
#             models.Index(fields=['student', 'subject', 'term', 'session']),
#             models.Index(fields=['result_class', 'session', 'term']),
#             models.Index(fields=['subject', 'session', 'term']),
#         ]
#         unique_together = ('student', 'subject', 'term', 'session')
#         ordering = ['subject__title']

#     def __str__(self):
#         return f"{self.student.username} - {self.subject.title} ({self.term.name}, {self.session.name})"

#     # --- Properties to get max marks from school ---
#     @property
#     def MAX_CA(self):
#         return self.schools.max_ca_score if self.schools and self.schools.max_ca_score is not None else Decimal('10.00')

#     @property
#     def MAX_MIDTERM(self):
#         return self.schools.max_midterm_score if self.schools and self.schools.max_midterm_score is not None else Decimal('30.00')

#     @property
#     def MAX_EXAM(self):
#         return self.schools.max_exam_score if self.schools and self.schools.max_exam_score is not None else Decimal('60.00')

#     def save(self, *args, **kwargs):
#         """Compute normalized total_score out of 100 based on school max values."""
#         ca = float(self.ca_score or 0)
#         mid = float(self.midterm_score or 0)
#         exam = float(self.exam_score or 0)

#         total_raw = 0
#         total_max = 0

#         if ca > 0:
#             total_raw += ca
#             total_max += float(self.MAX_CA)
#         if mid > 0:
#             total_raw += mid
#             total_max += float(self.MAX_MIDTERM)
#         if exam > 0:
#             total_raw += exam
#             total_max += float(self.MAX_EXAM)

#         if total_max > 0:
#             normalized_total = (total_raw / total_max) * 100
#             self.total_score = Decimal(normalized_total).quantize(Decimal('0.01'))
#         else:
#             self.total_score = Decimal('0.00')

#         super().save(*args, **kwargs)

#     # --- Grade Calculation ---
#     @property
#     def grade_letter(self):
#         """Return the grade letter based on normalized total_score (out of 100)."""
#         if self.total_score is None:
#             return None
#         score = float(self.total_score)
#         if score >= 70:
#             return 'A'
#         elif score >= 60:
#             return 'B'
#         elif score >= 50:
#             return 'C'
#         elif score >= 45:
#             return 'D'
#         elif score >= 40:
#             return 'E'
#         return 'F'

#     @property
#     def remark(self):
#         """Return remark corresponding to the grade letter."""
#         letter = self.grade_letter
#         if letter is None:
#             return None
#         return {
#             'A': 'Excellent',
#             'B': 'Very Good',
#             'C': 'Good',
#             'D': 'Fair',
#             'E': 'Pass',
#             'F': 'Fail',
#         }.get(letter, 'N/A')

