# Generated by Django 5.0.6 on 2025-06-03 10:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0003_courses_created_by'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='courses',
            options={'ordering': ['title'], 'verbose_name': 'subject', 'verbose_name_plural': 'subjects'},
        ),
    ]
