# Generated by Django 5.0.6 on 2024-09-08 19:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0048_course_session_course_term'),
        ('student', '0009_badge_course'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badge',
            name='course',
        ),
        migrations.AddField(
            model_name='badge',
            name='result',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.result'),
        ),
    ]