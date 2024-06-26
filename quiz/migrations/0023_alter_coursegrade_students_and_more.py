# Generated by Django 4.1 on 2024-04-02 11:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sms', '0002_initial'),
        ('quiz', '0022_remove_coursegrade_email_coursegrade_students_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursegrade',
            name='students',
            field=models.ManyToManyField(blank=True, related_name='course_grades', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='coursegrade',
            name='subjects',
            field=models.ManyToManyField(blank=True, related_name='course_grade', to='sms.courses'),
        ),
    ]
