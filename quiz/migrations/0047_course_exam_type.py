# Generated by Django 5.0.6 on 2024-09-05 09:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0046_examtype_result_exam_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='exam_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.examtype'),
        ),
    ]