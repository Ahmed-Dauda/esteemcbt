# Generated by Django 5.0.6 on 2024-11-11 18:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0008_alter_course_unique_together'),
        ('sms', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('course_name', 'session', 'term', 'schools')},
        ),
    ]