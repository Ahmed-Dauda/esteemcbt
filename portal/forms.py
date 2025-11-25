# reports/forms.py
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError

# We'll use these models from your project
from sms.models import Courses, Session, Term  # adjust import paths if different
from .models import Result_Portal  # if Result_Portal lives in same app; else adjust
from decimal import Decimal
from django import forms
from decimal import Decimal
from django import forms
from .models import SchoolSubscription

# portal/forms.py
from django import forms
from portal.models import StudentBehaviorRecord

class StudentBehaviorRecordForm(forms.ModelForm):
    class Meta:
        model = StudentBehaviorRecord
        fields = ['form_teacher_comment', 'principal_comment']
        widgets = {
            'form_teacher_comment': forms.Textarea(attrs={'rows': 3}),
            'principal_comment': forms.Textarea(attrs={'rows': 3}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = SchoolSubscription
        fields = [
            "cbt_active", "cbt_expiry",
            "report_card_active", "report_card_expiry",
        ]
        widgets = {
            "cbt_expiry": forms.DateInput(attrs={"type": "date"}),
            "report_card_expiry": forms.DateInput(attrs={"type": "date"}),
        }


class ResultRowForm(forms.Form):
    """
    Single-row form for one student with school max validation.
    """
    student_id = forms.IntegerField(widget=forms.HiddenInput)
    existing_result_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    ca_score = forms.DecimalField(max_digits=5, decimal_places=2, required=False, min_value=0)
    midterm_score = forms.DecimalField(max_digits=5, decimal_places=2, required=False, min_value=0)
    exam_score = forms.DecimalField(max_digits=5, decimal_places=2, required=False, min_value=0)

    def __init__(self, *args, **kwargs):
        # Accept school max parameters
        self.max_ca = kwargs.pop('max_ca', Decimal('10.00'))
        self.max_midterm = kwargs.pop('max_midterm', Decimal('30.00'))
        self.max_exam = kwargs.pop('max_exam', Decimal('60.00'))
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()

        # Ensure scores are not None
        for field in ("ca_score", "midterm_score", "exam_score"):
            if cleaned.get(field) in (None, ""):
                cleaned[field] = Decimal("0.00")

        # Validate against school max
        if cleaned["ca_score"] > self.max_ca:
            self.add_error("ca_score", f"CA score cannot exceed {self.max_ca}")
        if cleaned["midterm_score"] > self.max_midterm:
            self.add_error("midterm_score", f"Midterm score cannot exceed {self.max_midterm}")
        if cleaned["exam_score"] > self.max_exam:
            self.add_error("exam_score", f"Exam score cannot exceed {self.max_exam}")

        return cleaned

