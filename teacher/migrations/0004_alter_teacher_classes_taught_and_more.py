# Generated by Django 5.0.6 on 2024-10-15 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0005_alter_course_unique_together'),
        ('sms', '0001_initial'),
        ('teacher', '0003_alter_teacher_subjects_taught'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='classes_taught',
            field=models.ManyToManyField(blank=True, null=True, related_name='teachers', to='quiz.coursegrade'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='subjects_taught',
            field=models.ManyToManyField(blank=True, null=True, related_name='teachers', to='sms.courses'),
        ),
    ]
