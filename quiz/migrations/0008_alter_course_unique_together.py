# Generated by Django 5.0.6 on 2024-11-07 19:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0007_result_is_locked'),
        ('sms', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('course_name', 'session', 'term', 'schools', 'exam_type')},
        ),
    ]