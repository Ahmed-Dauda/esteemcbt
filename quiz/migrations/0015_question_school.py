# Generated by Django 5.0.6 on 2025-05-26 22:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0014_alter_course_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.school'),
        ),
    ]
