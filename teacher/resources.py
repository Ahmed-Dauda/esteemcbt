# myapp/resources.py

from import_export import resources
from quiz.models import Question

from django import forms


class QuestionResource(resources.ModelResource):
    class Meta:
        model = Question
