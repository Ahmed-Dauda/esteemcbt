# Generated by Django 5.0.6 on 2024-09-08 20:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0048_course_session_course_term'),
        ('student', '0010_remove_badge_course_badge_result'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badge',
            name='result',
        ),
        migrations.AddField(
            model_name='badge',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.course'),
        ),
    ]