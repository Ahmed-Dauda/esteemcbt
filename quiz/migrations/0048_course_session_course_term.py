# Generated by Django 5.0.6 on 2024-09-05 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0047_course_exam_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='session',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='term',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]