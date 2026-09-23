from django import forms
from .models import FinanceRecord
from django.contrib.auth import get_user_model
NewUser = get_user_model()
from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()


class FinanceRecordForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=NewUser.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={'required': 'Please select a student.'},
    )

    class Meta:
        model = FinanceRecord
        fields = [
            'student',
            'initial_total_deposit',
            'session',
            'term',
            'week_start',
            'school_shop', 'caps', 'haircut', 'others',
            'note',
        ]
        widgets = {
            'week_start': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d',
            ),
        }

    # 👇 NEW: mobile-friendly number inputs
    NUMERIC_FIELDS = [
        'initial_total_deposit',
        'school_shop', 'caps', 'haircut', 'others',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['week_start'].input_formats = ['%Y-%m-%d']

        # Add mobile-friendly attributes to numeric fields
        for name in self.NUMERIC_FIELDS:
            if name in self.fields:
                self.fields[name].widget.attrs.update({
                    'class':       'form-control money-input',
                    'inputmode':   'decimal',   # numeric keypad on mobile
                    'step':        '0.1',
                    'min':         '0',
                    'autocomplete': 'off',
                    'placeholder': '0',
                })

        # Bigger tap target for selects
        for name in ('session', 'term'):
            if name in self.fields:
                self.fields[name].widget.attrs['class'] = 'form-control'

        # Note field gets a slightly taller box
        if 'note' in self.fields:
            self.fields['note'].widget.attrs.update({
                'class': 'form-control',
                'rows': 3,
            })

    def clean_student(self):
        student = self.cleaned_data.get('student')
        if not student:
            raise forms.ValidationError("Please select a student.")
        return student