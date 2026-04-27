# forms.py
from django import forms
from .models import Dataset

class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.rsplit('.', 1)[-1].lower()
            if ext not in ['csv', 'xlsx', 'xls']:
                raise forms.ValidationError("Only CSV and Excel files are allowed.")
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError("File size must be under 10MB.")
        return file