# Generated by Django 5.0.6 on 2024-11-19 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0011_alter_coursegrade_subjects'),
        ('sms', '0002_alter_term_options_term_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursegrade',
            name='subjects',
            field=models.ManyToManyField(related_name='course_grade', to='sms.courses'),
        ),
    ]
