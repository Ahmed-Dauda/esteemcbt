# Generated by Django 4.1 on 2024-03-29 16:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0010_remove_student_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='student',
            old_name='student_user',
            new_name='email',
        ),
    ]
